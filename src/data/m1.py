"""M1 metadata, grouping, splitting, and duplicate-audit utilities.

The module deliberately streams records and images. It never copies source images
into split directories and never loads a complete dataset into memory as pixels.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from PIL import Image


SCHEMA_VERSION = "1.0"
DLC_ROW = re.compile(
    r"^(?P<doctype>[^/]+)/(?P<specimen>\d+)\.(?P<kind>cc|cg|or|re)(?P<capture>\d+)$"
)
DLC_LABELS = {"or": "BONA_FIDE", "cc": "PRINT", "cg": "PRINT", "re": "SCREEN"}


@dataclass(frozen=True)
class SampleRecord:
    schema_version: str
    sample_id: str
    source_dataset: str
    source_version: str
    source_url: str
    license_id: str
    base_document_id: str
    capture_id: str
    frame_index: int | None
    document_type: str
    original_label: str
    mapped_label: str
    is_synthetic_identity: bool
    is_synthetic_attack: bool
    split: str
    media_path: str
    media_available: bool
    sampling_rule: str
    mapping_rationale: str


def stable_hash(value: str, seed: int) -> int:
    payload = f"{seed}:{value}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def assign_group_splits(
    group_ids: Sequence[str], seed: int = 20250813, ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)
) -> dict[str, str]:
    if not group_ids:
        return {}
    if not math.isclose(sum(ratios), 1.0, abs_tol=1e-9):
        raise ValueError("Split ratios must sum to one")
    groups = sorted(set(group_ids), key=lambda item: (stable_hash(item, seed), item))
    total = len(groups)
    n_train = round(total * ratios[0])
    n_val = round(total * ratios[1])
    n_train = min(n_train, total)
    n_val = min(n_val, total - n_train)
    labels = ["train"] * n_train + ["validation"] * n_val
    labels += ["test"] * (total - len(labels))
    return dict(zip(groups, labels, strict=True))


def parse_dlc_inventory(csv_path: Path, seed: int = 20250813) -> list[SampleRecord]:
    rows_by_identifier: dict[str, list[tuple[re.Match[str], str, str]]] = defaultdict(list)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, delimiter=";")
        for line_number, row in enumerate(reader, start=1):
            if len(row) != 3:
                raise ValueError(f"Unexpected DLC row {line_number}: {row!r}")
            match = DLC_ROW.fullmatch(row[0].strip())
            if not match:
                raise ValueError(f"Unexpected DLC identifier on row {line_number}: {row[0]!r}")
            rows_by_identifier[row[0].strip()].append((match, row[1].strip(), row[2].strip()))

    # The published CSV contains one duplicated clip identifier with conflicting
    # device metadata. A media item must appear once, so consolidate identifier
    # collisions and preserve all conflicting values in capture_id.
    rows = [values[0] for _, values in sorted(rows_by_identifier.items())]
    group_ids = [f"dlc2021:{m['doctype']}:{m['specimen']}" for m, _, _ in rows]
    split_by_group = assign_group_splits(group_ids, seed=seed)
    records: list[SampleRecord] = []
    for match, device, condition in rows:
        identifier = match.group(0)
        collisions = rows_by_identifier[identifier]
        devices = sorted({item[1] for item in collisions})
        conditions = sorted({item[2] for item in collisions})
        group_id = f"dlc2021:{match['doctype']}:{match['specimen']}"
        original = match["kind"]
        records.append(
            SampleRecord(
                schema_version=SCHEMA_VERSION,
                sample_id=f"dlc2021:{identifier}:annotated_midpoint",
                source_dataset="DLC-2021",
                source_version="1.0.2",
                source_url="https://zenodo.org/records/6586764",
                license_id="CC-BY-SA-2.5",
                base_document_id=group_id,
                capture_id=f"{identifier}:device={'|'.join(devices)}:condition={'|'.join(conditions)}",
                frame_index=25,
                document_type=match["doctype"],
                original_label=original,
                mapped_label=DLC_LABELS[original],
                is_synthetic_identity=True,
                is_synthetic_attack=original != "or",
                split=split_by_group[group_id],
                media_path="",
                media_available=False,
                sampling_rule="25th annotated frame (metadata plan; archive member unresolved)",
                mapping_rationale={
                    "or": "laminated mock original",
                    "cc": "unlaminated color hard copy",
                    "cg": "unlaminated grayscale hard copy",
                    "re": "device-screen recapture",
                }[original],
            )
        )
    return records


def parse_sidtd_template_names(names: Sequence[str], seed: int = 20250813) -> list[SampleRecord]:
    parsed: list[tuple[str, str, str, bool]] = []
    for name in names:
        if not name.lower().endswith(".jpg"):
            continue
        prefix = "templates/Images/"
        if not name.startswith(prefix):
            raise ValueError(f"Unexpected SIDTD template image path: {name}")
        section, filename = name[len(prefix) :].split("/", 1)
        if section not in {"reals", "fakes"}:
            raise ValueError(f"Unexpected SIDTD section: {name}")
        stem = Path(filename).stem
        base_stem = stem.split("_fake_", 1)[0]
        try:
            doctype, specimen = base_stem.rsplit("_", 1)
        except ValueError as error:
            raise ValueError(f"Cannot derive SIDTD lineage: {name}") from error
        if not specimen.isdigit():
            raise ValueError(f"Invalid SIDTD specimen number: {name}")
        parsed.append((name, doctype, specimen, section == "fakes"))
    group_ids = [f"sidtd:{doctype}:{specimen}" for _, doctype, specimen, _ in parsed]
    split_by_group = assign_group_splits(group_ids, seed=seed)
    records: list[SampleRecord] = []
    for name, doctype, specimen, is_fake in parsed:
        group_id = f"sidtd:{doctype}:{specimen}"
        records.append(
            SampleRecord(
                schema_version=SCHEMA_VERSION,
                sample_id="sidtd:" + Path(name).stem,
                source_dataset="SIDTD",
                source_version="1",
                source_url="http://datasets.cvc.uab.es/SIDTD/templates.zip",
                license_id="CC-BY-SA-3.0",
                base_document_id=group_id,
                capture_id="template:" + Path(name).stem,
                frame_index=None,
                document_type=doctype,
                original_label="fake" if is_fake else "real",
                mapped_label="COMPOSITE" if is_fake else "BONA_FIDE",
                is_synthetic_identity=True,
                is_synthetic_attack=is_fake,
                split=split_by_group[group_id],
                media_path=f"remotezip://templates.zip!/{name}",
                media_available=True,
                sampling_rule="all template images; remote archive member reference",
                mapping_rationale=(
                    "SIDTD crop-and-replace/inpainting manipulation"
                    if is_fake
                    else "paired unmanipulated MIDV-2020-derived template"
                ),
            )
        )
    return records


def iter_jsonl(path: Path) -> Iterator[dict[str, object]]:
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_jsonl(records: Iterable[SampleRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(asdict(record), sort_keys=True) + "\n")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest(records: Sequence[SampleRecord]) -> dict[str, object]:
    issues: list[str] = []
    seen_samples: set[str] = set()
    group_splits: dict[str, set[str]] = defaultdict(set)
    capture_splits: dict[str, set[str]] = defaultdict(set)
    for record in records:
        if record.sample_id in seen_samples:
            issues.append(f"duplicate sample_id: {record.sample_id}")
        seen_samples.add(record.sample_id)
        group_splits[record.base_document_id].add(record.split)
        capture_splits[record.capture_id].add(record.split)
    for group, splits in group_splits.items():
        if len(splits) != 1:
            issues.append(f"base_document_id crosses splits: {group} -> {sorted(splits)}")
    for capture, splits in capture_splits.items():
        if len(splits) != 1:
            issues.append(f"capture_id crosses splits: {capture} -> {sorted(splits)}")
    return {
        "valid": not issues,
        "issues": issues,
        "sample_count": len(records),
        "base_document_count": len(group_splits),
        "counts_by_class": dict(sorted(Counter(r.mapped_label for r in records).items())),
        "counts_by_split": dict(sorted(Counter(r.split for r in records).items())),
        "counts_by_split_class": {
            split: dict(sorted(counter.items()))
            for split, counter in sorted(
                (
                    (split, Counter(r.mapped_label for r in records if r.split == split))
                    for split in ("train", "validation", "test")
                )
            )
        },
        "media_available": sum(r.media_available for r in records),
    }


def write_json(payload: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")


def file_inventory(paths: Iterable[Path]) -> Iterator[dict[str, object]]:
    for path in paths:
        stat = path.stat()
        yield {
            "path": str(path.resolve()),
            "size_bytes": stat.st_size,
            "extension": path.suffix.lower(),
            "sha256": sha256_file(path),
        }


def image_fingerprint(path: Path) -> dict[str, object]:
    """Return exact and perceptual identifiers using bounded image memory."""
    with Image.open(path) as image:
        encoding = image.format or "UNKNOWN"
        width, height = image.size
        rgb = image.convert("RGB")
        sample = rgb.copy()
        sample.thumbnail((256, 256))
        pixels = list(sample.getdata())
        means = [sum(pixel[channel] for pixel in pixels) / len(pixels) for channel in range(3)]
        import cv2
        import numpy as np

        gray_array = np.asarray(rgb.convert("L").resize((32, 32)), dtype=np.float32)
        low = cv2.dct(gray_array)[:8, :8]
        median = float(np.median(low[1:]))
        bits = (low > median).reshape(-1)
        phash = sum(int(bit) << index for index, bit in enumerate(bits))
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "phash64": f"{phash:016x}",
        "width": width,
        "height": height,
        "aspect_ratio": width / height,
        "encoding": encoding,
        "file_bytes": path.stat().st_size,
        "rgb_mean": means,
    }


def hamming_hex(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def duplicate_clusters(records: Sequence[dict[str, object]], max_phash_distance: int = 6) -> list[list[int]]:
    """Connected components over exact hashes or near perceptual hashes."""
    parent = list(range(len(records)))

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    exact: dict[str, int] = {}
    for index, record in enumerate(records):
        digest = str(record["sha256"])
        if digest in exact:
            union(index, exact[digest])
        else:
            exact[digest] = index
    for left in range(len(records)):
        for right in range(left + 1, len(records)):
            if hamming_hex(str(records[left]["phash"]), str(records[right]["phash"])) <= max_phash_distance:
                union(left, right)
    clusters: dict[int, list[int]] = defaultdict(list)
    for index in range(len(records)):
        clusters[find(index)].append(index)
    return [items for items in clusters.values() if len(items) > 1]


def duplicate_split_violations(records: Sequence[dict[str, object]], clusters: Sequence[Sequence[int]]) -> list[dict[str, object]]:
    violations = []
    for cluster in clusters:
        splits = sorted({str(records[index]["split"]) for index in cluster})
        if len(splits) > 1:
            violations.append({"indices": list(cluster), "splits": splits})
    return violations
