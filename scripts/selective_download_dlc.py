"""Retrieve exactly one annotated frame per DLC capture via Zenodo container API."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import threading
import time
from pathlib import Path
from urllib.parse import quote

import requests


ARCHIVES = {
    "or": ("6586764", "or.zip"),
    "cg": ("6586764", "cg.zip"),
    "cc": ("6466764", "cc.zip"),
    "re": ("6466770", "re.zip"),
}
thread_state = threading.local()


def session() -> requests.Session:
    if not hasattr(thread_state, "session"):
        thread_state.session = requests.Session()
    return thread_state.session


def fetch(url: str, attempts: int = 10) -> bytes:
    for attempt in range(attempts):
        try:
            response = session().get(url, timeout=120)
            response.raise_for_status()
            return response.content
        except requests.HTTPError as error:
            if attempt + 1 == attempts:
                raise
            retry_after = error.response.headers.get("Retry-After") if error.response is not None else None
            time.sleep(float(retry_after) if retry_after else min(60, 2**attempt))
        except Exception:
            if attempt + 1 == attempts:
                raise
            time.sleep(min(60, 2**attempt))
    raise AssertionError("unreachable")


def retrieve(record: dict, output: Path, minimum_free: int) -> dict[str, object]:
    identifier = record["sample_id"].split(":", 2)[1].rsplit(":", 1)[0]
    doctype, clip = identifier.split("/", 1)
    kind = clip[3:5]
    record_id, archive = ARCHIVES[kind]
    root = f"https://zenodo.org/api/records/{record_id}/files/{archive}/container"
    annotation_member = f"{kind}/clips/annotations/{doctype}/{clip}.json"
    existing = sorted((output / doctype / clip).glob("*.jpg"))
    if existing:
        target = existing[0]
        return {
            "sample_id": record["sample_id"], "source_member": f"{kind}/clips/images/{doctype}/{clip}/{target.name}",
            "annotation_member": annotation_member, "media_path": str(target.resolve()), "selected_frame": target.name,
            "bytes": target.stat().st_size, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes_downloaded": 0,
        }
    annotation_url = f"{root}/{quote(annotation_member, safe='/')}"
    annotation_bytes = fetch(annotation_url)
    payload = json.loads(annotation_bytes)
    names = sorted({item.get("filename") for item in payload.get("_via_img_metadata", {}).values() if item.get("filename")})
    if not names:
        raise RuntimeError(f"No annotated frames in {annotation_member}")
    frame = names[len(names) // 2]
    image_member = f"{kind}/clips/images/{doctype}/{clip}/{frame}"
    image_url = f"{root}/{quote(image_member, safe='/')}"
    image_bytes = fetch(image_url)
    if shutil.disk_usage(output).free < minimum_free:
        raise RuntimeError("Free disk dropped below safety margin")
    target = output / doctype / clip / frame
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(image_bytes)
    return {
        "sample_id": record["sample_id"],
        "source_member": image_member,
        "annotation_member": annotation_member,
        "media_path": str(target.resolve()),
        "selected_frame": frame,
        "bytes": len(image_bytes),
        "sha256": hashlib.sha256(image_bytes).hexdigest(),
        "bytes_downloaded": len(annotation_bytes) + len(image_bytes),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--kinds", default="or,cg,cc,re")
    parser.add_argument("--limit-per-kind", type=int)
    parser.add_argument("--minimum-free-gib", type=float, default=10.0)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    allowed = {item.strip() for item in args.kinds.split(",") if item.strip()}
    filtered = []
    counts = {}
    for record in records:
        identifier = record["sample_id"].split(":", 2)[1].rsplit(":", 1)[0]
        kind = identifier.split(".", 1)[1][:2]
        if kind not in allowed:
            continue
        if args.limit_per_kind is not None and counts.get(kind, 0) >= args.limit_per_kind:
            continue
        counts[kind] = counts.get(kind, 0) + 1
        filtered.append(record)
    records = filtered
    args.output.mkdir(parents=True, exist_ok=True)
    minimum_free = int(args.minimum_free_gib * 1024**3)
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda record: retrieve(record, args.output, minimum_free), records))
    audit = {
        "method": "Zenodo archive-container selective member retrieval",
        "bytes_downloaded": sum(item["bytes_downloaded"] for item in results),
        "elapsed_seconds": time.perf_counter() - started,
        "selected_count": len(results),
        "final_retained_bytes": sum(item["bytes"] for item in results),
        "peak_temporary_storage_bytes": 0,
        "minimum_free_bytes": minimum_free,
        "records": results,
    }
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in audit.items() if key != "records"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
