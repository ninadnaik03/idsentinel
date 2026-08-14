#!/usr/bin/env bash
set -euo pipefail
python -m pip install -q -r requirements.txt
python scripts/train_m4_texture.py --device cuda --batch-size 8 --accumulation 4 --workers 2 --epochs 250 --seed 20250813 --patience 15
zip -qr m4_results.zip artifacts/m4 artifacts/metrics/m4_texture_metrics.json artifacts/metrics/m4_test_predictions.csv artifacts/metrics/m4_vs_m3.json artifacts/plots/m4_confusion_matrix.png artifacts/plots/m4_training_curves.png artifacts/plots/m4_branch_weights.png artifacts/plots/m4_failures.png
