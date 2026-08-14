# Paper Specification

## Status and source

- Paper: Marko Peterlin and Borut Batagelj, "Multi-Branch Forensic Architecture for ID Card Presentation Attack Detection with Portrait Extraction," ERK 2025, pp. 481-485.
- Audit date: 2026-08-13.
- Scope: Track 1 of the Second Competition on Presentation Attack Detection on ID Cards (IJCB 2025).
- This document reports the paper's statements. It does not describe implemented code or new experimental results.

## Original paper method

### Task definition and classes

The method performs single-model, four-class classification of identity-card presentations:

1. bona fide;
2. print attack;
3. screen attack;
4. composite attack involving facial manipulation.

The pipeline has two stages: context-preserving portrait extraction, followed by a three-branch convolutional classifier.

### Dataset and protocol

- Private Track 1 competition dataset of 12,000 template-generated PVC ID-card images.
- Balanced four-way classes.
- Training: 2,500 images per class (10,000 total).
- Validation: 500 images per class (2,000 total).
- Competition testing used a hidden independent test set; local tables are validation results except the competition leaderboard.
- The paper does not state an identity/group-aware split rule, document-template counts, capture-device distribution, or duplicate policy.

### Portrait preprocessing

Algorithm 1 specifies this fallback sequence:

1. RetinaFace at confidence threshold 0.7.
2. If detected, select the best face based on size and position.
3. Otherwise apply CLAHE and retry RetinaFace.
4. Otherwise run a Haar cascade.
5. Otherwise use template-based region estimation.
6. Crop the original image from the selected bounding box with padding parameter alpha = 0.8.
7. Automatically expand to maintain a minimum 384 x 384 pixel resolution.

The objective is to retain surrounding document context rather than make a tight face crop.

Reported preprocessing figures are 88.3% first-attempt success, 98.7% success with all fallbacks, and 0.23 seconds average processing time per image. The paper does not provide per-fallback counts, confidence intervals, hardware-specific timing details, or the definition of extraction success.

### Backbone branch

- ImageNet-pretrained ConvNeXt from `timm`.
- Early layers frozen to reduce overfitting.
- Final stage fine-tuned.
- Produces high-level semantic features.

The exact ConvNeXt variant, pretrained weight identifier, feature dimension, pooling operation, normalization, and precise freeze boundary are not specified.

### Texture branch

- Adaptive pooling to 32 x 32.
- Lightweight convolutional layers.
- Batch normalization.
- Dimensionality reduction to 64 features.
- Intended to capture halftone patterns and color bleeding; the surrounding discussion also motivates screen moire and RGB subpixel effects.

The number of layers, channels, kernels, strides, padding, activation, pooling after convolutions, and dropout are not specified.

### Edge branch

- Specialized downsampling.
- Edge-detection kernels.
- 32-dimensional output.
- Intended to capture boundary discontinuities associated with composite attacks.

The edge operator, fixed-versus-learned status, channel handling, layer topology, and downsampling schedule are not specified.

### Fusion

The paper gives learnable scalar branch weights:

`F_combined = w1 * F_backbone + w2 * F_texture + w3 * F_edge`

with `w1`, `w2`, and `w3` real-valued learnable scalars.

The paper does not explain how branch vectors of unequal stated dimensions are made add-compatible, does not give the common dimension `d`, and does not specify weight initialization, normalization, constraints, or regularization.

### Classification head

The figure explicitly specifies:

- `d -> 512`, BatchNorm, ReLU;
- `512 -> 256`, BatchNorm, ReLU;
- `256 -> 128`, BatchNorm, ReLU;
- `128 -> 4 logits`.

No dropout is stated. Four logits imply multiclass classification, but the paper does not explicitly name the training loss.

### Class imbalance

The paper caps class weights at 3.0:

`weight_i = min(N / (K * n_i), 3.0)`

where `N` is sample count, `K` is class count, and `n_i` is the count for class `i`. For the balanced paper dataset this formula yields 1.0 for every class.

### Augmentation

The paper lists:

- screen: RGB channel shifts and moire patterns;
- print: noise injection and compression artifacts;
- composite: edge enhancement;
- lighting: brightness and contrast changes.

Probabilities, parameter ranges, ordering, label conditioning, validation transforms, and whether augmentations were applied online are not specified.

### Training configuration

- Framework: PyTorch.
- Input: 384 x 384 pixels.
- Batch size: 32.
- Maximum epochs: 250.
- Early stopping: 15 epochs without improvement.
- Optimizer: AdamW.
- Learning rates:
  - backbone: `5e-7`;
  - forensic branches: `1e-5`;
  - feature weights: `1e-4`;
  - classifier: `5e-6`.
- Scheduler: retain rates while average validation F1 improves; after five consecutive epochs without improvement, reduce by an unspecified constant factor.
- Paper hardware: 16 CPU cores, 128 GB RAM, and two NVIDIA A100 GPUs with 80 GB each.

Unspecified items include AdamW betas, epsilon, weight decay, scheduler factor and minimum learning rate, mixed precision, gradient clipping/accumulation, seed, checkpoint criterion details, distributed-training configuration, data-loader settings, and initialization.

### Evaluation metrics and reported results

The paper separates per-class/average F1 from binary PAD operating metrics. It defines APCER and BPCER after collapsing attacks versus bona fide, and defines EER at the threshold where they are equal. It reports BPCER at APCER 10%, 5%, and 1%, called BP10, BP20, and BP100. Competition ranking uses:

`AVR = 0.2 * BP10 + 0.3 * BP20 + 0.5 * BP100`.

Local validation results reported by the paper:

| Approach | Bona fide F1 | Print F1 | Screen F1 | Composite F1 | Average F1 |
|---|---:|---:|---:|---:|---:|
| With crop | 89.83 | 92.85 | 97.80 | 94.88 | 93.84 |
| Without crop | 83.54 | 84.60 | 98.76 | 98.70 | 91.40 |

| Approach | EER | BP10 | BP20 | BP100 | AVR |
|---|---:|---:|---:|---:|---:|
| With crop | 5.60 | 7.80 | 16.20 | 51.40 | 32.12 |
| Without crop | 8.97 | 25.40 | 45.40 | 75.60 | 56.50 |

These are paper-reported percentages, not IDSentinel results. The paper's hidden-test competition entry ranked sixth and reported EER 26.53 and AVR 71.77, below the Track 1 host baseline. The large validation-to-hidden-test gap is evidence of limited domain generalization and must not be obscured.

### Limitations stated or evidenced by the paper

- Private competition data prevents protocol-matched independent reproduction.
- Testing/refinement time was constrained by the competition.
- The authors identify cross-dataset domain adaptation, attention-based fusion, and broader branch configurations as future work.
- Hidden-test performance was substantially worse than local validation performance.
- The best competition approaches used document-centric detection/segmentation, homography rectification, and large ViT backbones, which outperformed this single-model CNN entry.
- No ablation isolates the texture branch, edge branch, fusion rule, or augmentation contribution.
- No uncertainty estimates, repeated seeds, latency protocol, parameter count, or failure analysis are reported.

## Missing implementation details requiring explicit decisions

1. ConvNeXt variant and pretrained checkpoint.
2. Semantic pooling and feature dimension.
3. Exact freeze boundary and unfreezing policy.
4. Texture branch topology.
5. Edge operator and topology.
6. Add-compatible projection for unequal branch dimensions.
7. Common fusion dimension and scalar-weight parameterization.
8. Loss function (cross entropy is the natural interpretation, not an explicit statement).
9. Face-selection score combining size and position.
10. CLAHE parameters and whether detection uses enhanced pixels only or also crops them.
11. Haar model and parameters.
12. Template-region representation and template selection.
13. Exact alpha = 0.8 crop geometry.
14. Expansion/padding behavior at image borders and for sub-384 images.
15. Image normalization and resizing interpolation.
16. Augmentation probabilities/ranges and leakage controls.
17. AdamW weight decay/betas and scheduler factor.
18. F1 averaging convention used for control decisions.
19. Checkpoint tie breaking and threshold selection.
20. APCER/BPCER score direction, interpolation, and EER numerical method.
21. Random seeds, number of runs, and confidence intervals.
22. Dataset identity grouping and duplicate/leakage protocol.

## Public implementation search

The local repository contained no implementation before M0. Exact-title web searches and GitHub-oriented searches performed on 2026-08-13 found the paper PDF and related datasets, but no public code repository attributable to the authors and no exact public implementation of this architecture. This is a search result, not proof that no implementation exists. If code is later found, it must be reported and treated only as a comparison source unless the user explicitly changes the independent-implementation rule.
