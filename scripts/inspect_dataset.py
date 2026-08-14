"""Build metadata manifests and leakage reports without copying source media."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.m1 import parse_dlc_inventory, validate_manifest, write_json, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dlc-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "data")
    parser.add_argument("--seed", type=int, default=20250813)
    args = parser.parse_args()

    records = parse_dlc_inventory(args.dlc_csv, seed=args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(records, args.output_dir / "dlc2021_protocol_a_manifest.jsonl")
    report = validate_manifest(records)
    write_json(report, args.output_dir / "dlc2021_protocol_a_validation.json")
    print(report)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
