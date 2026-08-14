"""Create the private portable M4 Colab bundle."""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=ROOT / "artifacts/private/m4_colab_bundle.zip"); args = parser.parse_args(); staging = ROOT / "artifacts/private/m4_colab_bundle"
    if staging.exists(): shutil.rmtree(staging)
    for relative in ("src", "scripts/train_m4_texture.py", "requirements.txt", "artifacts/metrics/m3_baseline_metrics.json", "artifacts/metrics/m3_test_predictions.csv"):
        source, target = ROOT / relative, staging / relative
        if source.is_dir(): shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
        else: target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    manifest = ROOT / "artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl"; records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    target_manifest = staging / "artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl"; target_manifest.parent.mkdir(parents=True, exist_ok=True)
    with target_manifest.open("w", encoding="utf-8", newline="\n") as stream:
        for index, record in enumerate(records):
            target = staging / "artifacts/data/portrait_crops_reduced" / f"{index:03d}.jpg"; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(record["portrait_crop_path"], target); record["portrait_crop_path"] = (Path("artifacts/data/portrait_crops_reduced") / target.name).as_posix(); stream.write(json.dumps(record, sort_keys=True) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True); print(shutil.make_archive(str(args.output.with_suffix("")), "zip", staging)); return 0
if __name__ == "__main__": raise SystemExit(main())
