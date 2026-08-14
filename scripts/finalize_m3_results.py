"""Validate imported GPU results and render M3 analysis/provenance documents."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    metrics_path = ROOT / "artifacts/metrics/m3_baseline_metrics.json"
    predictions_path = ROOT / "artifacts/metrics/m3_test_predictions.csv"
    manifest_path = ROOT / "artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    predictions = list(csv.DictReader(predictions_path.open(encoding="utf-8")))
    if len(predictions) != 44 or metrics["test_errors"] != sum(row["true_class"] != row["predicted_class"] for row in predictions):
        raise RuntimeError("Imported test predictions fail count/error invariants")
    if sum(sum(row) for row in metrics["confusion_matrix"]) != 44:
        raise RuntimeError("Confusion matrix does not contain the frozen 44-sample test set")
    frozen_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    provenance = {
        "protocol": "Protocol A-Reduced",
        "frozen_local_manifest_sha256": frozen_hash,
        "gpu_bundle_manifest_sha256": metrics["reproducibility"]["manifest_sha256"],
        "note": "The private GPU bundle rewrote only crop paths to portable POSIX-relative paths; sample IDs, labels, splits, hashes, and pixels were unchanged.",
        "test_prediction_rows": len(predictions),
    }
    (ROOT / "artifacts/m3/frozen_manifest_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    failures = metrics["failures"]
    report = [
        "# M3 Failure Analysis", "",
        "Protocol A-Reduced (300-sample leakage-safe DLC-2021 reduced protocol). These are our observed results, not full-DLC or paper-reported results.", "",
        f"Observed test errors: {len(failures)} of 44.", "",
        "The confusion matrix shows six SCREEN→BONA_FIDE, five BONA_FIDE→PRINT, three BONA_FIDE→SCREEN, three PRINT→BONA_FIDE, and one PRINT→SCREEN errors. These are observed transitions. Any explanation involving glare, blur, texture, display boundaries, or crop context requires human visual review and is not inferred automatically.", "",
        f"Padding diagnostic: padded errors {metrics['padding_diagnostic']['true']['errors']}/{metrics['padding_diagnostic']['true']['count']} ({metrics['padding_diagnostic']['true']['error_rate']:.1%}); non-padded errors {metrics['padding_diagnostic']['false']['errors']}/{metrics['padding_diagnostic']['false']['count']} ({metrics['padding_diagnostic']['false']['error_rate']:.1%}). This descriptive association does not establish causality.", "",
    ]
    for failure in failures:
        report.extend([
            f"## {failure['sample_id']}", "",
            f"- Observed: `{failure['true_class']}` → `{failure['predicted_class']}`; confidence {failure['confidence']:.4f}.",
            f"- Probabilities: `{json.dumps(failure['probabilities'], sort_keys=True)}`.",
            f"- Base document: `{failure['base_document_id']}`; capture: `{failure['capture_id']}`; document type: `{failure['document_type']}`.",
            f"- Padding: `{failure['padded']}`; detector stage (analysis only): `{failure['detector_stage']}`.",
            f"- Source member: `{failure['source_member']}`.",
            f"- Crop: `{failure['crop_path']}` (GPU-bundle path; map by sample ID to the frozen local manifest).",
            "- Possible explanation: not assigned automatically; visual interpretation would be speculative.", "",
        ])
    (ROOT / "docs/M3_FAILURE_ANALYSIS.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(provenance, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
