# M3 Semantic Baseline Report

## Scope

This is our reproduced semantic-only ConvNeXt-Tiny implementation and our observed result on **Protocol A-Reduced**, the 300-sample leakage-safe DLC-2021 reduced protocol. It is not the full DLC benchmark and is not directly comparable to paper-reported full-protocol results.

## Implementation

- `convnext_tiny.fb_in22k_ft_in1k_384`, ImageNet-pretrained, 384x384 RGB pixels only.
- Global pooling/final normalization followed by one three-logit linear classifier.
- Stem and stages 0-2 frozen; stage 3, final normalization, and classifier trainable.
- 27,822,435 total parameters; 15,474,435 trainable; 12,348,000 frozen.
- Train-only capped weights: 1.004695 BONA_FIDE, 1.004695 PRINT, 0.990741 SCREEN.
- AdamW groups: `5e-7` trainable backbone and `5e-6` classifier; assumed weight decay 0.01.
- No stochastic augmentation. All splits use RGB tensor conversion and ImageNet normalization.
- Validation macro-F1 checkpointing; early stopping patience 15; plateau scheduler patience 5/factor 0.5.

## Environments

The local CPU smoke test used PyTorch 2.8.0 CPU, timm 1.0.24, batch 1, and zero workers. It passed forward, backward, loss, optimizer, validation metric, and checkpoint round-trip. Peak RSS was 572,510,208 bytes (~546 MiB); one forward pass took 0.553 seconds. Smoke metrics are not experimental results.

The real run used a free Google Colab Tesla T4, PyTorch 2.11.0+cu128, timm 1.0.24, mixed precision, physical batch 8, accumulation 4, and two workers. It completed 50 epochs in 153.68 seconds. The best validation macro-F1 was 0.580522 at epoch 35; test was evaluated once after loading that checkpoint.

## Our observed test result

| Metric | Value |
|---|---:|
| Accuracy | 0.590909 |
| Macro precision | 0.593651 |
| Macro recall | 0.589286 |
| Macro F1 | 0.590038 |
| BONA_FIDE F1 | 0.413793 |
| PRINT F1 | 0.689655 |
| SCREEN F1 | 0.666667 |

Confusion matrix, rows=true and columns=predicted in BONA_FIDE/PRINT/SCREEN order:

```text
[[6, 5, 3],
 [3,10, 1],
 [6, 0,10]]
```

There were 18 errors among 44 test samples. The dominant observed transition was SCREEN→BONA_FIDE (6). See `docs/M3_FAILURE_ANALYSIS.md`; possible visual explanations are not assigned automatically.

## Padding diagnostic

- Padded: 8 errors / 22 samples = 36.36% error rate.
- Non-padded: 10 errors / 22 samples = 45.45% error rate.

Within this small fixed test set, padded samples did not have a higher error rate. This descriptive comparison does not demonstrate that the model did or did not use padding-related pixels, and it does not establish causality.

## Limitations

- Only 300 samples and 44 test cases; estimates have high variance.
- One fixed seed, because M3 follows the 24-hour compute priority.
- The full DLC benchmark was not acquired.
- The reduced class subsets have different base-document coverage.
- Padding prevalence differs by class, and descriptive error rates cannot rule out shortcut use.
- No stochastic augmentation was used; this avoids altering forensic/border cues but may limit generalization.
- The private GPU bundle rewrote crop paths for Linux portability. `artifacts/m3/frozen_manifest_provenance.json` records both hashes and confirms that sample IDs, labels, splits, image hashes, and pixels were unchanged.

## M4 stop gate

M4 has not begun. A proposed M4 would implement only the texture branch and its isolated ConvNeXt+Texture comparison while preserving the M3 baseline and split. Texture, edge, fusion, and full-model work require explicit approval and a clarified M4 boundary.
