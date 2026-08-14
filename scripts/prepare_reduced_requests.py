"""Create deterministic, lineage-diverse media requests for Protocol A-Reduced."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def round_robin(records: list[dict], target: int, max_per_base: int) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for record in sorted(records, key=lambda row: row["sample_id"]):
        groups[record["base_document_id"]].append(record)
    selected: list[dict] = []
    for depth in range(max_per_base):
        for base in sorted(groups):
            if depth < len(groups[base]):
                selected.append(groups[base][depth])
                if len(selected) == target:
                    return selected
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--max-per-base", type=int, default=2)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    candidates = [row for row in records if row["original_label"] == args.kind]
    selected = round_robin(candidates, args.target, args.max_per_base)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as stream:
        for record in selected:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps({"kind": args.kind, "selected": len(selected), "unique_bases": len({row['base_document_id'] for row in selected})}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
