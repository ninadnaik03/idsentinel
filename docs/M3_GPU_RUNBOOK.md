# M3 Free-GPU Runbook

This runs the semantic-only ConvNeXt-Tiny baseline on Protocol A-Reduced. It does not implement M4.

1. Run `python scripts/package_m3_gpu.py` locally. The resulting private ZIP contains the 300 licensed crops and must not be committed or redistributed.
2. Open a free Google Colab or Kaggle GPU session and upload/extract the ZIP into the session workspace.
3. Run `bash scripts/run_m3_colab.sh` from the extracted directory.
4. Download `artifacts/m3`, `artifacts/metrics`, `artifacts/plots`, and `docs/M3_FAILURE_ANALYSIS.md` before the temporary runtime expires.

The trainer probes CUDA backward memory at 384x384. It tries physical batch 8, then 4, 2, and 1 on out-of-memory and increases gradient accumulation to retain an effective batch of approximately 32. It never changes images, resolution, splits, or class membership.

The test dataset is instantiated only after early stopping and reloading the checkpoint selected by validation macro-F1. Do not rerun test evaluation for model selection.
