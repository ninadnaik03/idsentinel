"""Stream DLC clips.tar once and retain one deterministic annotated frame per capture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from collections import Counter
from pathlib import Path, PurePosixPath


class CountingReader:
    def __init__(self, stream):
        self.stream = stream
        self.bytes_read = 0

    def read(self, size=-1):
        data = self.stream.read(size)
        self.bytes_read += len(data)
        return data

    def close(self):
        self.stream.close()


class PrefixReader:
    def __init__(self, prefix: bytes, stream):
        self.prefix = bytearray(prefix)
        self.stream = stream

    def read(self, size=-1):
        if size < 0:
            data = bytes(self.prefix) + self.stream.read()
            self.prefix.clear()
            return data
        head = bytes(self.prefix[:size])
        del self.prefix[:size]
        return head + self.stream.read(size - len(head))


def valid_tar_header(block: bytes) -> bool:
    if len(block) != 512 or not block.strip(b"\0"):
        return False
    try:
        stored = int(block[148:156].rstrip(b"\0 ") or b"0", 8)
    except ValueError:
        return False
    computed = sum(block[:148]) + 8 * ord(" ") + sum(block[156:])
    return stored == computed and bool(block[:100].split(b"\0", 1)[0])


def resync_tar_stream(reader: CountingReader) -> PrefixReader:
    while block := reader.read(512):
        if valid_tar_header(block):
            return PrefixReader(block, reader)
    raise RuntimeError("No tar header found after range start")


def annotation_filenames(payload: dict) -> list[str]:
    metadata = payload.get("_via_img_metadata", {})
    names = {value.get("filename") for value in metadata.values() if value.get("filename")}
    return sorted(names)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="ftp://smartengines.com/dlc-2021/clips.tar")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--minimum-free-gib", type=float, default=10.0)
    parser.add_argument("--kind", default="re", help="DLC capture kind to retain (re=SCREEN)")
    parser.add_argument("--target", type=int, default=100)
    parser.add_argument("--max-per-base", type=int, default=2)
    parser.add_argument("--max-seconds", type=int, default=14400)
    parser.add_argument("--start-offset", type=int, default=0, help="512-byte-aligned byte offset for a ranged stream")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    minimum_free = int(args.minimum_free_gib * 1024**3)
    started = time.perf_counter()
    peak_output = 0
    selected_by_clip: dict[str, str] = {}
    retained: list[dict[str, object]] = []
    skipped = 0
    reserved_by_base: Counter[str] = Counter()
    retained_by_base: Counter[str] = Counter()
    stop_reason = "archive_exhausted"
    last_progress = started

    curl_process = None
    if args.url.startswith("ftp://"):
        command = ["curl.exe", "--fail", "--silent", "--show-error", "--max-time", str(args.max_seconds)]
        if args.start_offset:
            if args.start_offset % 512:
                raise ValueError("--start-offset must be divisible by 512")
            command.extend(["--range", f"{args.start_offset}-"])
        command.append(args.url)
        curl_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
        )
        if curl_process.stdout is None:
            raise RuntimeError("curl stdout pipe was not created")
        response = curl_process.stdout
    else:
        response = sys.stdin.buffer if args.url == "-" else urllib.request.urlopen(args.url, timeout=120)
    reader = CountingReader(response)
    try:
        tar_stream = resync_tar_stream(reader) if args.start_offset else reader
        with tarfile.open(fileobj=tar_stream, mode="r|*") as archive:
            for member in archive:
                elapsed = time.perf_counter() - started
                if elapsed >= args.max_seconds:
                    stop_reason = "time_box_reached"
                    break
                if not member.isfile():
                    continue
                path = PurePosixPath(member.name)
                if "annotations" in path.parts and path.suffix.lower() == ".json":
                    stream = archive.extractfile(member)
                    if stream is None:
                        continue
                    payload = json.load(stream)
                    names = annotation_filenames(payload)
                    kind = path.stem[3:5]
                    base = f"{path.parent.name}:{path.stem[:2]}"
                    if names and kind == args.kind and reserved_by_base[base] < args.max_per_base:
                        clip = f"{path.parent.name}/{path.stem}"
                        selected_by_clip[clip] = names[len(names) // 2]
                        reserved_by_base[base] += 1
                    continue
                if "images" not in path.parts or path.suffix.lower() not in {".jpg", ".jpeg"}:
                    continue
                clip = f"{path.parent.parent.name}/{path.parent.name}"
                if selected_by_clip.get(clip) != path.name:
                    skipped += 1
                    continue
                free = shutil.disk_usage(args.output).free
                if free < minimum_free:
                    raise RuntimeError(f"Free disk {free} is below safety margin {minimum_free}")
                source = archive.extractfile(member)
                if source is None:
                    continue
                target = args.output / path.parent.parent.name / path.parent.name / path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                with target.open("wb") as sink:
                    while chunk := source.read(1024 * 1024):
                        digest.update(chunk)
                        sink.write(chunk)
                retained.append(
                    {
                        "source_member": member.name,
                        "media_path": str(target.resolve()),
                        "selected_frame": path.name,
                        "bytes": target.stat().st_size,
                        "sha256": digest.hexdigest(),
                        "base_document_id": f"dlc2021:{path.parent.parent.name}:{path.parent.name[:2]}",
                    }
                )
                retained_by_base[f"{path.parent.parent.name}:{path.parent.name[:2]}"] += 1
                peak_output = max(peak_output, sum(int(item["bytes"]) for item in retained))
                now = time.perf_counter()
                if now - last_progress >= 30:
                    print(json.dumps({"retained": len(retained), "unique_bases": len(retained_by_base), "downloaded_bytes": reader.bytes_read, "elapsed_seconds": now - started}), flush=True)
                    last_progress = now
                if len(retained) >= args.target:
                    stop_reason = "target_reached"
                    break
    finally:
        if args.url != "-":
            reader.close()
        if curl_process is not None:
            if stop_reason in {"target_reached", "time_box_reached"}:
                curl_process.terminate()
            return_code = curl_process.wait(timeout=30)
            if return_code and stop_reason == "archive_exhausted":
                raise RuntimeError(f"curl exited with status {return_code}")

    audit = {
        "url": args.url,
        "start_offset": args.start_offset,
        "bytes_downloaded": reader.bytes_read,
        "elapsed_seconds": time.perf_counter() - started,
        "selected_count": len(retained),
        "annotated_clip_count": len(selected_by_clip),
        "skipped_image_members": skipped,
        "final_retained_bytes": sum(int(item["bytes"]) for item in retained),
        "peak_temporary_storage_bytes": peak_output,
        "minimum_free_bytes": minimum_free,
        "target": args.target,
        "kind": args.kind,
        "max_per_base": args.max_per_base,
        "unique_base_documents": len(retained_by_base),
        "stop_reason": stop_reason,
        "records": retained,
    }
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in audit.items() if key != "records"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
