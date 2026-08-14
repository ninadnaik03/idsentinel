"""Create private portable M5 Colab bundle with immutable M3/M4 comparisons."""
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=ROOT/"artifacts/private/m5_colab_bundle.zip"); args=p.parse_args(); staging=ROOT/"artifacts/private/m5_colab_bundle"
    if staging.exists(): shutil.rmtree(staging)
    files=("src","scripts/train_m4_texture.py","scripts/train_m5_edge.py","requirements.txt","artifacts/metrics/m3_baseline_metrics.json","artifacts/metrics/m3_test_predictions.csv","artifacts/metrics/m4_texture_metrics.json","artifacts/metrics/m4_test_predictions.csv")
    for relative in files:
        source,target=ROOT/relative,staging/relative
        if source.is_dir(): shutil.copytree(source,target,ignore=shutil.ignore_patterns("__pycache__"))
        else: target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
    records=[json.loads(x) for x in (ROOT/"artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]; manifest=staging/"artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl"; manifest.parent.mkdir(parents=True,exist_ok=True)
    with manifest.open("w",encoding="utf-8",newline="\n") as stream:
        for i,r in enumerate(records):
            target=staging/"artifacts/data/portrait_crops_reduced"/f"{i:03d}.jpg"; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(r["portrait_crop_path"],target); r["portrait_crop_path"]=(Path("artifacts/data/portrait_crops_reduced")/target.name).as_posix(); stream.write(json.dumps(r,sort_keys=True)+"\n")
    args.output.parent.mkdir(parents=True,exist_ok=True); print(shutil.make_archive(str(args.output.with_suffix("")),"zip",staging)); return 0
if __name__=="__main__": raise SystemExit(main())
