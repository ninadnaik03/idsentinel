# M4 ConvNeXt + Texture Report

These are our observed results on the frozen 300-sample Protocol A-Reduced experiment, not results from the original paper or the full DLC-2021 corpus.

## Controlled protocol

- Frozen manifest: 300 samples; local SHA-256 `9f435547bf0ac20b0a265a40126c0366ef52a64aaac34a868e4adbe6319a0349`; portable GPU SHA-256 `4088bd0b7ad8ad00b7478fe8effde238c3a34b0d3ed3164323a05b779799259d` (identical to M3 GPU provenance).
- Splits, crop geometry, labels, seed, normalization, class weights, and no-stochastic-augmentation policy are identical to M3.
- The checkpoint was selected only by validation macro-F1. The frozen 44-sample test set was instantiated after checkpoint selection and evaluated once.

## Architecture and training

- ImageNet-pretrained `convnext_tiny.fb_in22k_ft_in1k_384` semantic branch; stem/stages 0-2 frozen, stage 3 and final normalization trainable.
- Pixel-only texture branch: adaptive 32x32 pooling, Conv-BN-ReLU widths 16/32/64, global pooling, 64-D output.
- Both branches project to 256-D and combine through two softmax-normalized learned scalar weights; progressive classifier 256->512->256->128->3.
- Parameters: 28,355,317 total; 16,007,317 trainable; 12,348,000 frozen.
- GPU: Tesla T4; physical batch 8; accumulation 4; duration 154.20 s; 48 epochs; best epoch 33.

## Observed results

- Best validation macro-F1: 0.855067.
- Test accuracy: 0.681818; macro precision: 0.689510; macro recall: 0.678571; macro-F1: 0.678519.
- BONA_FIDE: precision 0.545455; recall 0.428571; F1 0.480000.
- PRINT: precision 0.923077; recall 0.857143; F1 0.888889.
- SCREEN: precision 0.600000; recall 0.750000; F1 0.666667.
- Confusion matrix (rows true, columns predicted; BONA_FIDE, PRINT, SCREEN): `[[6, 1, 7], [1, 12, 1], [4, 0, 12]]`.
- Failures: 14 of 44.

## Delta versus immutable M3

- Accuracy: +0.090909; macro-F1: +0.088480.
- BONA_FIDE F1: +0.066207.
- PRINT F1: +0.199234.
- SCREEN F1: -0.000000.
- Four of the six M3 SCREEN->BONA_FIDE errors were corrected; two persisted. SCREEN F1 was unchanged because other SCREEN errors and prediction tradeoffs offset those corrections.

## Learned fusion weights

- Best-checkpoint semantic weight: 0.503779.
- Best-checkpoint texture weight: 0.496221.

These are learned fusion weights, not proof of causal importance.

## Padding diagnostic

- Padded: 8/22 errors (36.36%); M3 was 36.36%.
- Non-padded: 6/22 errors (27.27%); M3 was 45.45%.

Class x padding counts are stored in the metrics artifact. These small descriptive strata do not establish that padding caused any prediction.

## Limitations

- The test set has only 44 samples and this is one seed, so deltas have high sampling uncertainty.
- This experiment changes more than a single feature extractor relative to M3: it introduces projections and a deeper classifier alongside the texture branch. It tests the approved ConvNeXt+Texture system, not the isolated causal contribution of texture alone.
- The reduced acquisition is not the full DLC-2021 benchmark; no paper-level reproduction claim is justified.
- Learned fusion weights and embedding norms are descriptive and are not causal importance measures.

## Proposed M5 plan (not implemented)

With explicit approval, M5 should run one controlled ConvNeXt+Edge experiment on the same frozen protocol: implement a pixel-only 32-D fixed-gradient/lightweight edge branch, retain the M3 semantic freeze policy, independently project semantic and edge features to 256-D, use two softmax-normalized learned weights and the same progressive classifier, repeat the CPU gradient/checkpoint smoke gate, then run exactly one validation-selected T4 experiment and one frozen-test evaluation. Report M5 vs M3 and class/padding/failure diagnostics. Do not add texture+edge three-branch fusion until a later separately approved milestone.
