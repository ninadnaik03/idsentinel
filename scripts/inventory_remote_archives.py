"""Inventory the small SIDTD template ZIP through HTTP range requests.

This reads the central directory only; it does not download or extract the 1.27 GB
archive and does not copy source images into the repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from remotezip import RemoteZip

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.m1 import parse_sidtd_template_names, validate_manifest, write_json, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sidtd-url",
        default="http://datasets.cvc.uab.es/SIDTD/templates.zip",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "data")
    parser.add_argument("--seed", type=int, default=20250813)
    args = parser.parse_args()

    with RemoteZip(args.sidtd_url) as archive:
        infos = archive.infolist()
    names = [info.filename for info in infos]
    inventory = {
        "url": args.sidtd_url,
        "entry_count": len(infos),
        "uncompressed_bytes": sum(info.file_size for info in infos),
        "compressed_member_bytes": sum(info.compress_size for info in infos),
        "image_entry_count": sum(name.lower().endswith(".jpg") for name in names),
        "json_entry_count": sum(name.lower().endswith(".json") for name in names),
        "entries": [
            {
                "name": info.filename,
                "size_bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "crc32": f"{info.CRC:08x}",
            }
            for info in infos
        ],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(inventory, args.output_dir / "sidtd_templates_zip_inventory.json")
    records = parse_sidtd_template_names(names, seed=args.seed)
    write_jsonl(records, args.output_dir / "sidtd_protocol_b_manifest.jsonl")
    report = validate_manifest(records)
    write_json(report, args.output_dir / "sidtd_protocol_b_validation.json")
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
