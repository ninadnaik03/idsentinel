# M5 ConvNeXt + Edge Report

These are our observed Protocol A-Reduced results, not paper results or a full-DLC reproduction.

## Controlled implementation

- Frozen 300-sample GPU manifest SHA-256 `4088bd0b7ad8ad00b7478fe8effde238c3a34b0d3ed3164323a05b779799259d`, identical to M3/M4 provenance.
- Pixels only; no texture branch or acquisition/detector/padding metadata enters the classifier.
- Canonical fixed Sobel-X/Y buffers, luminance grayscale, magnitude `sqrt(gx^2 + gy^2 + 1e-6)`, no per-image normalization; trainable Conv-BN-ReLU 1->16->32, global pool, Linear 32->32.
- Semantic and 32-D edge features project to 256-D, combine through two softmax-normalized learned weights, then classifier 256->512->256->128->3.
- Parameters: 28,329,333 total; 15,981,333 trainable; 12,348,000 frozen.
- Tesla T4; duration 198.77 s; 56 epochs; best epoch 41; no stochastic augmentation.

## Observed results

- Best validation macro-F1: 0.759630.
- Test accuracy 0.636364; macro precision 0.661977; macro recall 0.633929; macro-F1 0.640249.
- BONA_FIDE: precision 0.545455; recall 0.428571; F1 0.480000.
- PRINT: precision 0.916667; recall 0.785714; F1 0.846154.
- SCREEN: precision 0.523810; recall 0.687500; F1 0.594595.
- Confusion matrix: `[[6, 1, 7], [0, 11, 3], [5, 0, 11]]`; failures 16/44.

## M5 versus M3 (primary)

- Accuracy +0.045455; macro-F1 +0.050211.
- BONA_FIDE F1 +0.066207.
- PRINT F1 +0.156499.
- SCREEN F1 -0.072072.

## Observed three-model comparison

| Metric | M3 Semantic | M4 +Texture | M5 +Edge |
|---|---:|---:|---:|
| Accuracy | 0.590909 | 0.681818 | 0.636364 |
| Macro-F1 | 0.590038 | 0.678519 | 0.640249 |
| BONA_FIDE F1 | 0.413793 | 0.480000 | 0.480000 |
| PRINT F1 | 0.689655 | 0.888889 | 0.846154 |
| SCREEN F1 | 0.666667 | 0.666667 | 0.594595 |
| Failures | 18 | 14 | 16 |

M4 is descriptively higher than M5 on this one 44-sample test (accuracy +0.045455 and macro-F1 +0.038269 for M4 relative to M5). This does not establish that texture is objectively superior to edge.

## Learned fusion weights

- Semantic 0.502496; edge 0.497504. These are learned fusion weights, not causal importance.

## M3 failure transitions

- BONA_FIDE->PRINT: CORRECTED=2, CHANGED_TO_DIFFERENT_WRONG_CLASS=2, PERSISTENT=1
- BONA_FIDE->SCREEN: PERSISTENT=2, CORRECTED=1
- PRINT->BONA_FIDE: CHANGED_TO_DIFFERENT_WRONG_CLASS=1, CORRECTED=2
- PRINT->SCREEN: CORRECTED=1
- SCREEN->BONA_FIDE: CORRECTED=3, PERSISTENT=3
- New M5 failures among M3-correct samples: 7.
- Correction overlap across the 18 M3 failures: `{'CORRECTED_BY_BOTH': 7, 'PERSISTENT_ACROSS_ALL': 5, 'CORRECTED_BY_EDGE_ONLY': 2, 'CORRECTED_BY_TEXTURE_ONLY': 4}`.

## Padding and border diagnostics

- Padded: 9/22 (40.91%); M3 36.36%; M4 36.36%.
- Non-padded: 7/22 (31.82%); M3 45.45%; M4 27.27%.
- Padded BONA_FIDE: n=7; mean outer-border Sobel=1.136311; mean central Sobel=0.922886; mean per-sample ratio=1.214227.
- Padded PRINT: n=6; mean outer-border Sobel=0.993905; mean central Sobel=1.138438; mean per-sample ratio=0.851856.
- Padded SCREEN: n=9; mean outer-border Sobel=1.378151; mean central Sobel=1.022595; mean per-sample ratio=1.360511.

These are small descriptive distributions and do not show that reflected padding caused predictions.

## Limitations

- Only 44 test samples and one primary seed; differences have high sampling uncertainty.
- ConvNeXt+Edge also adds projections and a progressive classifier, so this is not a causal edge-only ablation.
- Sobel is applied to ImageNet-normalized inputs; absolute magnitude therefore reflects that fixed normalization.
- Protocol A-Reduced is not the full DLC-2021 corpus.

## Proposed M6 plan (not implemented)

If explicitly approved, M6 should combine the already frozen M5 edge and M4 texture designs with the semantic branch in a three-branch model: 64-D texture and 32-D edge outputs, three independent 256-D projections, three softmax-normalized learned weights, and the same progressive classifier. It should reuse the exact frozen manifest/seed/preprocessing and semantic freeze policy, pass a three-branch CPU gradient/checkpoint gate, then run one validation-selected T4 experiment and one frozen-test evaluation. Compare descriptively with M3, M4, and M5, retain padding/border/failure analyses, and do not add API, frontend, deployment, robustness, unconstrained-weight ablation, or extra seeds unless separately approved.
