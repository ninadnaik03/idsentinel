"""Build and validate the acquired DLC-only Protocol A-Reduced manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.m1 import duplicate_clusters, duplicate_split_violations, image_fingerprint


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def clip_id(member: str) -> str:
    parts = PurePosixPath(member).parts
    index = parts.index("images")
    return f"{parts[index + 1]}/{parts[index + 2]}"


def assign_group_safe_splits(records: list[dict], clusters: list[list[int]]) -> None:
    parent = list(range(len(records)))

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    by_base: dict[str, int] = {}
    for index, row in enumerate(records):
        base = row["base_document_id"]
        if base in by_base:
            union(index, by_base[base])
        else:
            by_base[base] = index
    for cluster in clusters:
        for index in cluster[1:]:
            union(cluster[0], index)
    components: dict[int, list[int]] = defaultdict(list)
    for index in range(len(records)):
        components[find(index)].append(index)
    # Seeded group ordering plus fixed group quotas keeps the intended 70/15/15
    # ratio without ever breaking a lineage or duplicate component.
    ordered = sorted(components.values(), key=lambda items: hashlib.sha256(("idsentinel-reduced-v1|" + "|".join(sorted(records[i]["base_document_id"] for i in items))).encode()).hexdigest())
    group_count = len(ordered)
    train_end = round(0.70 * group_count)
    validation_end = train_end + round(0.15 * group_count)
    for position, component in enumerate(ordered):
        best_split = "train" if position < train_end else ("validation" if position < validation_end else "test")
        for index in component:
            records[index]["split"] = best_split


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-manifest", type=Path, required=True)
    parser.add_argument("--acquisition", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--minimum-per-class", type=int, default=100)
    args = parser.parse_args()
    metadata = {}
    for row in load_jsonl(args.full_manifest):
        identifier = row["sample_id"].split(":", 2)[1].rsplit(":", 1)[0]
        metadata[identifier] = row
    media = []
    acquisition_summaries = []
    for path in args.acquisition:
        payload = json.loads(path.read_text(encoding="utf-8"))
        media.extend(payload["records"])
        acquisition_summaries.append({key: value for key, value in payload.items() if key != "records"})
    records = []
    for item in media:
        identifier = clip_id(item["source_member"])
        if identifier not in metadata:
            raise RuntimeError(f"Acquired member absent from full manifest: {identifier}")
        row = dict(metadata[identifier])
        fingerprint = image_fingerprint(Path(item["media_path"]))
        row.update({
            "protocol": "Protocol A-Reduced",
            "class": row["mapped_label"],
            "media_available": True,
            "media_path": item["media_path"],
            "source_member": item["source_member"],
            "selected_frame": item["selected_frame"],
            "width": fingerprint["width"], "height": fingerprint["height"],
            "encoding": fingerprint["encoding"], "file_bytes": fingerprint["file_bytes"],
            "sha256": fingerprint["sha256"], "phash": fingerprint["phash64"],
        })
        records.append(row)
    sample_ids = [row["sample_id"] for row in records]
    if len(sample_ids) != len(set(sample_ids)):
        raise RuntimeError("Duplicate acquired sample_id")
    counts = Counter(row["mapped_label"] for row in records)
    required = {"BONA_FIDE", "PRINT", "SCREEN"}
    if set(counts) != required or min(counts.values()) < args.minimum_per_class:
        raise RuntimeError(f"M2 completion threshold not met: {dict(counts)}")
    clusters = duplicate_clusters(records)
    assign_group_safe_splits(records, clusters)
    violations = duplicate_split_violations(records, clusters)
    base_splits: dict[str, set[str]] = defaultdict(set)
    capture_splits: dict[str, set[str]] = defaultdict(set)
    for row in records:
        base_splits[row["base_document_id"]].add(row["split"])
        capture_splits[row["capture_id"]].add(row["split"])
    lineage_violations = {base: sorted(splits) for base, splits in base_splits.items() if len(splits) > 1}
    capture_violations = {capture: sorted(splits) for capture, splits in capture_splits.items() if len(splits) > 1}
    if violations or lineage_violations or capture_violations:
        raise RuntimeError("Automated leakage assertions failed")
    exact = [cluster for cluster in clusters if len({records[index]["sha256"] for index in cluster}) == 1]
    records.sort(key=lambda row: (row["split"], row["mapped_label"], row["sample_id"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as stream:
        for row in records:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    split_class = {split: dict(Counter(row["mapped_label"] for row in records if row["split"] == split)) for split in ("train", "validation", "test")}
    bases_split_class = {
        split: {label: len({row["base_document_id"] for row in records if row["split"] == split and row["mapped_label"] == label}) for label in sorted(required)}
        for split in ("train", "validation", "test")
    }
    audit = {
        "protocol": "Protocol A-Reduced", "status": "complete", "sample_count": len(records),
        "counts_by_class": dict(counts), "unique_bases_by_class": {label: len({row["base_document_id"] for row in records if row["mapped_label"] == label}) for label in sorted(required)},
        "counts_by_split_class": split_class, "unique_bases_by_split_class": bases_split_class,
        "exact_duplicate_clusters": len(exact), "exact_or_near_duplicate_clusters": len(clusters),
        "duplicate_split_violations": violations, "base_document_split_violations": lineage_violations,
        "capture_split_violations": capture_violations, "acquisition": acquisition_summaries,
    }
    args.audit.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
