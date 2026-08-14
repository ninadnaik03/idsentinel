"""Download bounded non-overlapping TAR byte ranges concurrently."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import time
from pathlib import Path


def fetch(url: str, target: Path, start: int, end: int) -> dict[str, object]:
    completed = subprocess.run(
        ["curl.exe", "--fail", "--silent", "--show-error", "--range", f"{start}-{end}", "--output", str(target), url],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(f"Range {start}-{end} failed: {completed.stderr}")
    expected = end - start + 1
    if target.stat().st_size != expected:
        raise RuntimeError(f"Range {start}-{end}: expected {expected}, got {target.stat().st_size}")
    return {"path": str(target.resolve()), "start": start, "end": end, "bytes": expected}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="ftp://smartengines.com/dlc-2021/clips.tar")
    parser.add_argument("--total-bytes", type=int, default=17_768_312_320)
    parser.add_argument("--parts", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--minimum-free-gib", type=float, default=10.0)
    args = parser.parse_args()
    minimum_free = int(args.minimum_free_gib * 1024**3)
    if shutil.disk_usage(args.output.parent).free - args.total_bytes < minimum_free:
        raise SystemExit("Insufficient disk after conservative safety margin")
    args.output.mkdir(parents=True, exist_ok=True)
    size = (args.total_bytes + args.parts - 1) // args.parts
    jobs = []
    for index in range(args.parts):
        start = index * size
        end = min(args.total_bytes - 1, (index + 1) * size - 1)
        jobs.append((args.url, args.output / f"part_{index:02d}.bin", start, end))
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parts) as pool:
        records = list(pool.map(lambda job: fetch(*job), jobs))
    audit = {
        "url": args.url,
        "bytes_downloaded": sum(item["bytes"] for item in records),
        "elapsed_seconds": time.perf_counter() - started,
        "peak_temporary_storage_bytes": sum(item["bytes"] for item in records),
        "minimum_free_bytes": minimum_free,
        "parts": records,
    }
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
