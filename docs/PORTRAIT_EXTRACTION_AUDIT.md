# Protocol A-Reduced Portrait Extraction Audit

## Status and scope

**M2 is complete for Protocol A-Reduced. M3 is not approved and has not begun.** This is a 24-hour reduced DLC reproduction protocol, not the full 1,424-capture DLC protocol and not a reproduction of full-dataset paper results.

Protocol A-Reduced contains 300 DLC-2021 images: 100 BONA_FIDE, 100 PRINT, and 100 SCREEN. Selection used no model outputs or visual-quality filtering. BONA_FIDE and PRINT use deterministic group-round-robin requests from the Zenodo member API. SCREEN uses annotated midpoint frames streamed from `clips.tar`, capped at two captures per base document and stopped immediately at 100.

## Leakage and splits

The final set covers 80 BONA_FIDE bases, 80 PRINT bases, and 50 SCREEN bases. The same DLC base may support multiple classes and always has one split. The deterministic group split is:

| Split | BONA_FIDE | PRINT | SCREEN | Total |
|---|---:|---:|---:|---:|
| Train | 71 | 71 | 72 | 214 |
| Validation | 15 | 15 | 12 | 42 |
| Test | 14 | 14 | 16 | 44 |

Unique base counts by class are respectively 56/56/36 in train, 12/12/6 in validation, and 12/12/8 in test. SHA-256 and pHash-distance-6 analysis found zero exact or near-duplicate clusters. Automated assertions found zero duplicate, `base_document_id`, or `capture_id` split violations.

## Pipeline and Haar plausibility rule

The pipeline is RetinaFace `>=0.7`, CLAHE plus RetinaFace, Haar, then template fallback. Detection may inspect CLAHE pixels, but every final 384x384 crop comes from the original pixels. Context expansion uses alpha 0.8 on every face-box side, square adjustment, clipping, and reflect padding.

A Haar candidate is accepted only if its clipped box is at least 24 px per side, aspect ratio is 0.65-1.55, image-area ratio is 0.0005-0.12, its center is within the central 96% of the image, grayscale standard deviation is at least 10, and an OpenCV Haar eye candidate occurs in the upper 75% of its face ROI. Rejected candidates continue to template fallback. Tests cover accepted and rejected Haar behavior. The one accepted SCREEN Haar crop was included in the non-cherry-picked visual audit and is visually plausible.

## Our observed results

| Class | N | RetinaFace first | CLAHE+RetinaFace | Haar | Template | Failure |
|---|---:|---:|---:|---:|---:|---:|
| BONA_FIDE | 100 | 100% | 0% | 0% | 0% | 0% |
| PRINT | 100 | 100% | 0% | 0% | 0% | 0% |
| SCREEN | 100 | 99% | 0% | 1% | 0% | 0% |

| Class | Mean confidence | Median confidence | Mean box ratio | Median box ratio | Padding |
|---|---:|---:|---:|---:|---:|
| BONA_FIDE | 0.9940 | 0.9989 | 0.01363 | 0.01124 | 39% |
| PRINT | 0.9960 | 0.9986 | 0.01180 | 0.01098 | 32% |
| SCREEN | 0.9864 | 0.9996 | 0.01649 | 0.01466 | 61% |

Document-type statistics are recorded in `artifacts/metrics/portrait_extraction_reduced.json`. All 300 outputs are exactly 384x384.

## Shortcut assessment

Fallback stage and failure rate do not form an obvious class shortcut: 299/300 images use first-pass RetinaFace, only one SCREEN uses Haar, and no image fails. Output dimensions are identical. Confidence medians and face-box ratios are also similar, although SCREEN has a moderately larger box ratio.

Padding is the material warning: SCREEN is padded 61% of the time versus 39% BONA_FIDE and 32% PRINT. The pixels introduced by reflect padding could therefore correlate with class. The smallest defensible mitigation is to keep detector/fallback/confidence metadata out of model inputs, retain the same crop algorithm for every class, report this imbalance, and include a validation-only sensitivity check using a slightly tighter context crop or border masking in a later robustness experiment. The primary protocol is usable, but padding-related shortcut behavior must be examined in failure analysis.

## Resource measurements

- Metered acquisition network lower bound: 12,525,344,453 bytes (SCREEN tar stream plus all retained fast-path originals). A short Zenodo attempt ended on HTTP 429 before writing an audit, so its annotation/retry overhead is unmetered; an exact total would be dishonest.
- SCREEN acquisition: 5,927.28 seconds; 12,494,561,792 bytes streamed; 29,960,078 bytes retained.
- Total retained originals: 60,742,739 bytes.
- Crop storage: 16,029,567 bytes.
- Peak temporary storage: 29,960,078 bytes; the tar was never stored.
- Peak extraction RSS: 600,981,504 bytes (~573 MiB).
- Median CPU preprocessing latency: 0.3032 seconds/image.
- p95 CPU preprocessing latency: 0.3979 seconds/image.

The measured implementation is feasible on the 8 GB laptop.

## Artifacts

- Final manifest: `artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl`
- Validation: `artifacts/data/dlc2021_protocol_a_reduced_validation.json`
- Extraction metrics: `artifacts/metrics/portrait_extraction_reduced.json`
- 48-sample visual audit: `artifacts/plots/portrait_extraction_audit_reduced.png`

## Proposed M3 plan — not authorized

After explicit approval only: implement a semantic-only ImageNet-pretrained ConvNeXt-Tiny baseline at 384x384; freeze stem/stages 0-2 and fine-tune the final stage; use three logits, weighted cross entropy, validation macro-F1, and validation-only early stopping; run CPU batch-1 smoke tests locally; train on temporary/free GPU compute; save immutable config, seed, manifest hash, checkpoint, confusion matrix, macro-F1, per-class F1, and failure analysis; then stop before texture/edge/fusion work.
