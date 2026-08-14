"""Finalize Protocol A media records and run serial portrait extraction."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

import cv2
import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.m1 import duplicate_clusters, duplicate_split_violations, image_fingerprint
from src.preprocessing.portrait import HaarDetector, PortraitExtractor, RetinaFaceONNX


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def clip_identifier(source_member: str) -> str:
    parts = Path(source_member.replace("/", "\\")).parts
    images = parts.index("images")
    return f"{parts[images + 1]}/{parts[images + 2]}"


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--acquisition", type=Path, action="append", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--crop-dir", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()

    records = load_jsonl(args.manifest)
    media = {}
    for acquisition_path in args.acquisition:
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        media.update({clip_identifier(item["source_member"]): item for item in acquisition["records"]})
    resolved = []
    for record in records:
        identifier = record["sample_id"].split(":", 2)[1].rsplit(":", 1)[0]
        item = media.get(identifier)
        if item is None:
            continue
        fingerprint = image_fingerprint(Path(item["media_path"]))
        record.update(
            {
                "class": record["mapped_label"],
                "source": record["source_dataset"],
                "media_path": item["media_path"],
                "source_member": item["source_member"],
                "selected_frame": item["selected_frame"],
                "width": fingerprint["width"],
                "height": fingerprint["height"],
                "sha256": fingerprint["sha256"],
                "phash": fingerprint["phash64"],
                "media_available": True,
            }
        )
        resolved.append(record)

    clusters = duplicate_clusters(resolved)
    violations = duplicate_split_violations(resolved, clusters)
    if violations:
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(json.dumps({"status": "blocked_duplicate_leakage", "violations": violations}, indent=2), encoding="utf-8")
        raise SystemExit("Duplicate cluster crosses splits; repair required before extraction")

    retinaface = RetinaFaceONNX(args.model)
    extractor = PortraitExtractor(retinaface, HaarDetector())
    process = psutil.Process()
    peak_rss = process.memory_info().rss
    timings = []
    detector_counts = Counter()
    by_class = defaultdict(list)
    by_document_type = defaultdict(list)
    failures = []
    args.crop_dir.mkdir(parents=True, exist_ok=True)
    for index, record in enumerate(resolved):
        original = cv2.imread(record["media_path"])
        if original is None:
            record.update({"portrait_success": False, "portrait_detector": "decode_failure", "portrait_bbox": None, "portrait_confidence": None})
            failures.append(record["sample_id"])
            row = {"detector": "decode_failure", "confidence": None, "area_ratio": None, "padding": False, "success": False}
            by_class[record["mapped_label"]].append(row)
            by_document_type[record["document_type"]].append(row)
            continue
        started = time.perf_counter()
        result = extractor.extract(original)
        timings.append(time.perf_counter() - started)
        peak_rss = max(peak_rss, process.memory_info().rss)
        detector_counts[result.detector] += 1
        x1, y1, x2, y2 = result.bbox or (0, 0, 0, 0)
        area_ratio = max(0, x2 - x1) * max(0, y2 - y1) / (original.shape[0] * original.shape[1])
        row = {"detector": result.detector, "confidence": result.confidence, "area_ratio": area_ratio, "padding": result.padding_applied, "success": result.success}
        by_class[record["mapped_label"]].append(row)
        by_document_type[record["document_type"]].append(row)
        crop_path = args.crop_dir / record["mapped_label"].lower() / f"{index:05d}.jpg"
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(crop_path), result.crop)
        record.update(
            {
                "portrait_bbox": list(result.bbox) if result.bbox else None,
                "portrait_detector": result.detector,
                "portrait_confidence": result.confidence,
                "portrait_success": result.success,
                "portrait_crop_path": str(crop_path.resolve()),
                "portrait_bbox_area_ratio": area_ratio,
                "portrait_padding_applied": result.padding_applied,
            }
        )

    args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.output_manifest.open("w", encoding="utf-8", newline="\n") as stream:
        for record in resolved:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    def summarize(rows):
        confidences = [row["confidence"] for row in rows if row["confidence"] is not None and row["detector"] != "template"]
        area = [row["area_ratio"] for row in rows if row["area_ratio"] is not None]
        counts = Counter(row["detector"] for row in rows)
        return {
            "count": len(rows),
            "detector_counts": dict(counts),
            "detector_percent": {key: 100 * value / len(rows) for key, value in counts.items()},
            "mean_confidence": statistics.fmean(confidences) if confidences else None,
            "median_confidence": statistics.median(confidences) if confidences else None,
            "mean_bbox_area_ratio": statistics.fmean(area) if area else None,
            "median_bbox_area_ratio": statistics.median(area) if area else None,
            "padding_count": sum(row["padding"] for row in rows),
            "padding_percent": 100 * sum(row["padding"] for row in rows) / len(rows),
            "complete_failure_count": sum(not row["success"] for row in rows),
            "complete_failure_percent": 100 * sum(not row["success"] for row in rows) / len(rows),
        }
    class_stats = {label: summarize(rows) for label, rows in sorted(by_class.items())}
    document_stats = {label: summarize(rows) for label, rows in sorted(by_document_type.items())}
    audit = {
        "status": "complete",
        "resolved_samples": len(resolved),
        "unresolved_samples": len(records) - len(resolved),
        "exact_or_near_duplicate_clusters": len(clusters),
        "duplicate_split_violations": violations,
        "detector_counts": dict(detector_counts),
        "by_class": class_stats,
        "by_document_type": document_stats,
        "median_cpu_seconds": statistics.median(timings) if timings else None,
        "p95_cpu_seconds": percentile(timings, 0.95) if timings else None,
        "peak_rss_bytes": peak_rss,
        "crop_storage_bytes": sum(path.stat().st_size for path in args.crop_dir.rglob("*.jpg")),
        "failures": failures,
    }
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
