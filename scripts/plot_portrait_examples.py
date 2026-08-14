"""Plot deterministic portrait extraction examples without cherry-picking."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import matplotlib.pyplot as plt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=32)
    args = parser.parse_args()
    all_records = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    labels = ("BONA_FIDE", "PRINT", "SCREEN")
    per_class = args.count // len(labels)
    records = []
    for label in labels:
        candidates = [row for row in all_records if row["mapped_label"] == label]
        fallback = [row for row in candidates if row.get("portrait_detector") in {"haar", "template", "decode_failure"}]
        regular = [row for row in candidates if row not in fallback]
        # Deterministic coverage: include fallback/questionable cases first, then evenly spaced ordinary rows.
        chosen = fallback[: max(2, per_class // 4)]
        remaining = per_class - len(chosen)
        if remaining > 0 and regular:
            indices = [round(i * (len(regular) - 1) / max(1, remaining - 1)) for i in range(remaining)]
            chosen.extend(regular[index] for index in indices)
        records.extend(chosen[:per_class])
    rows = (len(records) + 3) // 4
    figure, axes = plt.subplots(rows, 8, figsize=(20, rows * 3.2), squeeze=False)
    for index, record in enumerate(records):
        row, pair = divmod(index, 4)
        original_axis, crop_axis = axes[row, pair * 2], axes[row, pair * 2 + 1]
        original = cv2.imread(record["media_path"])
        crop = cv2.imread(record["portrait_crop_path"])
        if original is not None:
            x1, y1, x2, y2 = map(int, record["portrait_bbox"])
            cv2.rectangle(original, (x1, y1), (x2, y2), (0, 0, 255), max(2, original.shape[1] // 500))
            scale = min(1.0, 640 / max(original.shape[:2]))
            if scale < 1:
                original = cv2.resize(original, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            original_axis.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
        if crop is not None:
            crop_axis.imshow(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        original_axis.set_title(f"{record['mapped_label']}\n{record['portrait_detector']}", fontsize=8)
        crop_axis.set_title("context crop", fontsize=8)
        original_axis.axis("off")
        crop_axis.axis("off")
    for axis in axes.flat[len(records) * 2 :]:
        axis.axis("off")
    figure.suptitle("IDSentinel Protocol A-Reduced portrait extraction audit", fontsize=14)
    figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=150)
    plt.close(figure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
