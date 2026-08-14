#!/usr/bin/env bash
set -euo pipefail
python -m pip install timm==1.0.24
python scripts/train_baseline.py --device cuda --batch-size 8 --accumulation 4 --workers 2 --epochs 250
