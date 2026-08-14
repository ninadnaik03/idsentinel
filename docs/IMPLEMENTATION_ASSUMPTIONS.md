# Implementation Assumptions

No architectural code exists through M1. The entries below are decisions proposed for later milestones and remain change-controlled.

## Known from paper

- Four classes: bona fide, print, screen, composite.
- RetinaFace threshold 0.7, then CLAHE + RetinaFace, Haar cascade, template estimate.
- Context padding alpha = 0.8 and minimum 384 x 384 crop.
- ImageNet-pretrained ConvNeXt; early layers frozen and final stage fine-tuned.
- Texture input pooled to 32 x 32 and output dimension 64.
- Edge output dimension 32 and use of edge-detection kernels.
- Three learnable scalar branch weights.
- MLP `d -> 512 -> 256 -> 128 -> 4`, with BatchNorm + ReLU after the first three linear layers.
- Input 384 x 384, AdamW, batch size 32, at most 250 epochs, early stopping patience 15.
- Learning rates: backbone `5e-7`, forensic branches `1e-5`, fusion weights `1e-4`, classifier `5e-6`.
- Scheduler reacts after five validation epochs without improvement.
- Class weight formula capped at 3.0.
- Screen, print, composite, and lighting augmentation families listed in `PAPER_SPEC.md`.

## Inferred by us

These are proposed defaults, not paper claims:

1. **Fusion projection:** project each branch to a common `d = 256` space before weighted addition because raw semantic, 64-D texture, and 32-D edge vectors cannot generally be added.
2. **Fusion weights:** initialize three logits to zero and apply softmax, yielding stable equal positive weights summing to one. Unconstrained scalars remain an optional compute-gated ablation.
3. **Backbone:** begin with `convnext_tiny` from `timm` and infer its pooled feature width at runtime. This is the smallest standard ConvNeXt likely to fit the 24-hour budget.
4. **Semantic pooling:** use the model's documented global average pooling before projection.
5. **Freeze policy:** freeze stem and stages 0-2, train stage 3 and final normalization; expose fully frozen and broader fine-tuning modes.
6. **Texture topology:** adaptive average pool to 32 x 32, two small Conv-BN-ReLU blocks, global average pool, linear projection to 64.
7. **Edge topology:** fixed grayscale Sobel x/y kernels, gradient magnitude, lightweight Conv-BN-ReLU processing, global average pool, linear projection to 32.
8. **Loss:** weighted multiclass cross entropy over logits, with no in-model softmax.
9. **Crop pixels:** detection may run on CLAHE-enhanced pixels, but the final crop is taken from the unmodified original image.
10. **Border handling:** expand the desired crop geometrically, clip to image bounds, then reflect-pad where safe (edge-pad otherwise) before resizing to 384 x 384.
11. **Face selection:** use a documented score combining confidence, plausible portrait location for the selected template, and bounding-box area; never silently choose largest face alone.
12. **Validation objective:** macro F1, because the paper says average F1 without defining micro/weighted averaging and the target requires macro F1.
13. **Scheduler:** `ReduceLROnPlateau(mode=max, patience=5, factor=0.5)` on validation macro F1; factor 0.5 is inferred.
14. **Reproducibility:** deterministic seed, immutable split manifest, run config snapshot, Git commit, and environment metadata.
15. **Metrics:** attack probability equals `1 - P(BONA_FIDE)`; threshold selection uses validation only; EER is calculated from the ROC operating point minimizing absolute APCER-BPCER difference with interpolation documented in tests.

## Changed due to data or compute limits

1. Primary Protocol A uses DLC-2021 alone with three classes because the DLC+SIDTD four-class merge is source-confounded.
2. Exploratory Protocol B uses SIDTD alone for paired bona fide-versus-composite evaluation; its metrics are never merged with Protocol A.
3. Use one deterministic frame per DLC capture instead of treating correlated frames as independent samples.
4. Use group-aware 70/15/15 splits rather than the paper's stated fixed train/validation counts.
5. Treat SIDTD composite as synthetic/digital manipulation and label that limitation everywhere.
6. Local development uses CPU, batch 1, no workers, and bounded smoke-test subsets. Scientifically useful training is delegated to temporary/free GPU compute when available.
7. The paper's dual-A100 environment is not a minimum requirement, and no 12/24 GB local GPU is assumed.
8. **M2 rescue protocol:** call the acquired subset "Protocol A-Reduced" or the "24-hour reduced DLC reproduction protocol". It is not the full DLC protocol and its results must not be presented as full-dataset paper reproduction results.
9. **Reduced selection:** prioritize unique `base_document_id` values using deterministic round-robin selection across groups, then balance DLC-only BONA_FIDE/PRINT/SCREEN around the acquired SCREEN count. Existing deterministic group assignments remain immutable.
10. **Bounded acquisition:** stream the source `clips.tar` only until the SCREEN target is reached, retaining only selected annotated frames and never retaining the tar. Keep at most two SCREEN captures per base document during acquisition to avoid concentration in a few lineages.
11. **Haar plausibility:** accept a Haar face only when its clipped box is at least 24 px on each side, has aspect ratio 0.65-1.55, occupies 0.05%-12% of the image, has a center within the central 96% of the image, has grayscale standard deviation at least 10, and contains at least one Haar eye candidate in the upper 75% of the face ROI. Otherwise continue to the deterministic template fallback.

## M3 semantic baseline assumptions

1. Use timm model identifier `convnext_tiny.fb_in22k_ft_in1k_384` when pretrained weights are requested. This provides an ImageNet-pretrained 384-pixel ConvNeXt-Tiny; the paper does not identify its exact checkpoint.
2. Replace the timm classifier with one three-logit linear layer while retaining the model's documented global pooling and final normalization.
3. Freeze `stem` and stages 0-2; train stage 3, final normalization, and the new classifier. The final normalization is treated as part of the trainable final semantic stage.
4. Use no stochastic augmentation in the primary baseline. Horizontal flips make document text physically implausible, and rotations/fills could alter the already-audited border shortcut. Train, validation, and test therefore use only deterministic RGB tensor conversion and ImageNet normalization. Robustness augmentation remains outside M3.
5. Use AdamW defaults except explicit learning rates and weight decay `0.01`, which is an implementation assumption because the paper omits weight decay. Backbone and classifier are separate optimizer groups at `5e-7` and `5e-6`.
6. The fixed seed is `20250813`. Deterministic algorithms are requested where supported. Checkpoint selection and scheduler input use validation macro-F1 only.
7. GPU batches use physical batch 8 and accumulation 4 initially. CUDA out-of-memory recovery may reduce physical batch to 4, 2, or 1 while increasing accumulation to preserve an effective batch of approximately 32; resolution and dataset remain unchanged.

## M4 ConvNeXt + texture assumptions

1. M4 is a single controlled architecture comparison against the immutable M3 baseline. It reuses the exact frozen Protocol A-Reduced manifest, seed, preprocessing, class weighting, validation selection rule, and test set.
2. The semantic feature is timm ConvNeXt-Tiny's pooled, normalized pre-classifier feature. Stem and stages 0-2 remain frozen; stage 3 and final normalization remain trainable exactly as in M3. The M3 classifier is not reused because M4 has its own progressive classifier.
3. The texture branch follows the approved suggested topology without alteration: deterministic adaptive average pooling to 32 x 32, three Conv-BatchNorm-ReLU blocks with widths 16, 32, and 64, then adaptive global average pooling. Its output is exactly 64-D.
4. Semantic and texture features are independently linearly projected to 256-D. Two zero-initialized scalar logits are softmax-normalized before weighted addition, so initial learned fusion weights are 0.5/0.5 and always sum to one.
5. The progressive classifier is `256 -> 512 -> 256 -> 128 -> 3`, with BatchNorm and ReLU after the first three linear layers. This common-space projection and exact classifier realization are our implementation interpretation, not a claimed paper detail.
6. Optimizer groups use the approved M4 learning rates: trainable ConvNeXt backbone `5e-7`, texture branch `1e-5`, projections `1e-5`, fusion logits `1e-4`, and classifier `5e-6`, with the M3 AdamW weight decay `0.01`.
7. The texture branch receives image pixels only. Detector identity, confidence, padding, document/source/device, and acquisition metadata are never model inputs.
8. Learned scalar values are reported only as learned fusion weights, not causal importance.

## M5 ConvNeXt + edge assumptions

1. M5 is one controlled ConvNeXt+Edge comparison using the exact M3/M4 frozen manifest, seed, preprocessing, normalization, train-only class weights, and no-stochastic-augmentation policy.
2. Grayscale is the fixed luminance transform `0.2989 R + 0.5870 G + 0.1140 B` applied to the already normalized model input. Canonical Sobel-X/Y kernels are registered as non-parameter buffers and applied with one-pixel zero padding. Magnitude is `sqrt(gx^2 + gy^2 + 1e-6)` with no per-image normalization.
3. The trainable edge topology follows the approved example exactly: Conv-BN-ReLU `1->16`, Conv-BN-ReLU `16->32`, adaptive global average pooling, and `Linear(32,32)`. Output is exactly 32-D.
4. Semantic and edge features are separately projected to 256-D and fused through two zero-initialized, softmax-normalized scalar logits. The progressive classifier is `256->512->256->128->3` with BatchNorm and ReLU after its first three linear layers.
5. The semantic feature extraction and freeze policy match M4: pooled normalized pre-classifier ConvNeXt output, with stem/stages 0-2 frozen and stage 3/final normalization trainable.
6. Border sensitivity is descriptive only. For padded frozen-test crops, mean Sobel magnitude is measured over the union of the outer 10% rows/columns and separately over the central 80% rectangle; inputs are not modified.
7. Learned scalar values are called learned fusion weights and are not interpreted as causal importance.

## Decisions deferred until M1 evidence

- Whether Protocol A should include passport layouts or be restricted to card-shaped documents after M2 portrait-extraction QA.
- Corpus-wide exact/near-duplicate clearance after selected media acquisition.
- Final train-ready counts after decode and portrait-extraction QC.
- Whether SIDTD `src`/`second_src` fields all agree with filename-derived lineage.
