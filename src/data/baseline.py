"""Frozen-manifest dataset and integrity checks for M3."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from src.data.m1 import duplicate_clusters, duplicate_split_violations


CLASS_NAMES = ("BONA_FIDE", "PRINT", "SCREEN")
CLASS_TO_INDEX = {label: index for index, label in enumerate(CLASS_NAMES)}
EXPECTED_SPLITS = {
    "train": {"BONA_FIDE": 71, "PRINT": 71, "SCREEN": 72},
    "validation": {"BONA_FIDE": 15, "PRINT": 15, "SCREEN": 12},
    "test": {"BONA_FIDE": 14, "PRINT": 14, "SCREEN": 16},
}


def load_and_validate_manifest(path: Path) -> tuple[list[dict], dict]:
    raw = path.read_bytes()
    records = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    errors = []
    if len(records) != 300:
        errors.append(f"expected 300 records, found {len(records)}")
    counts = Counter(row["mapped_label"] for row in records)
    if counts != Counter({label: 100 for label in CLASS_NAMES}):
        errors.append(f"class counts differ: {dict(counts)}")
    actual_splits = {split: dict(Counter(row["mapped_label"] for row in records if row["split"] == split)) for split in EXPECTED_SPLITS}
    if actual_splits != EXPECTED_SPLITS:
        errors.append(f"frozen split differs: {actual_splits}")
    for row in records:
        if not Path(row["portrait_crop_path"]).is_file():
            errors.append(f"missing crop: {row['sample_id']}")
    for field in ("base_document_id", "capture_id"):
        mapping = defaultdict(set)
        for row in records:
            mapping[row[field]].add(row["split"])
        errors.extend(f"{field} crosses splits: {key}" for key, splits in mapping.items() if len(splits) > 1)
    clusters = duplicate_clusters(records)
    violations = duplicate_split_violations(records, clusters)
    if violations:
        errors.append(f"duplicate clusters cross splits: {violations}")
    if errors:
        raise RuntimeError("M3 manifest invariant failure:\n" + "\n".join(errors))
    return records, {"manifest_sha256": hashlib.sha256(raw).hexdigest(), "duplicate_clusters": len(clusters), "split_counts": actual_splits}


def image_transform(training: bool):
    return transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))])


class ProtocolAReducedDataset(Dataset):
    def __init__(self, records: list[dict], split: str, training: bool = False) -> None:
        self.records = [row for row in records if row["split"] == split]
        self.transform = image_transform(training)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        row = self.records[index]
        with Image.open(row["portrait_crop_path"]) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, CLASS_TO_INDEX[row["mapped_label"]], index


def training_class_weights(records: list[dict], cap: float = 3.0) -> list[float]:
    counts = Counter(row["mapped_label"] for row in records if row["split"] == "train")
    total, classes = sum(counts.values()), len(CLASS_NAMES)
    return [min(total / (classes * counts[label]), cap) for label in CLASS_NAMES]
