# Implementation Plan

## Milestone status

- M0: complete - paper audit and initial feasibility.
- M1: complete - metadata inventory, provenance schema, deterministic grouping/splits, license/storage audits, and source-confound ruling.
- M2: complete for the explicitly approved Protocol A-Reduced (300 DLC-only samples, 100/class). Full DLC remains unacquired.
- M3: complete - semantic-only ConvNeXt-Tiny baseline, local CPU smoke test, free-T4 training, validation-only checkpoint selection, one-time test evaluation, failure analysis, and padding diagnostic.
- M4-M14: not started. M4 is not approved.

## Approved experiment structure

- **Primary experiment available for the sprint:** Protocol A-Reduced, DLC-2021 only; BONA_FIDE, PRINT, SCREEN; 300 acquired captures. Always distinguish it from the 1,424-capture full DLC protocol.
- **Exploratory Protocol B:** SIDTD templates only; BONA_FIDE versus COMPOSITE; 2,222 archive-observed images in 1,000 base-document groups.
- The mixed-source four-class benchmark is blocked and must not be used.

## 24-hour experiment priorities

### Must have

1. Clean semantic ConvNeXt baseline.
2. Full multi-branch IDSentinel.
3. Baseline-versus-full-model comparison.
4. Confusion matrix, macro F1, and per-class F1.
5. Failure analysis.

### Should have if compute permits

6. ConvNeXt + Texture.
7. ConvNeXt + Edge.
8. One bounded robustness experiment.

### Optional

9. Fusion-weight ablation, including unconstrained scalars.
10. Multiple random seeds.
11. Extensive robustness suite.

Scientific correctness takes precedence over completing optional ablations.

## Low-resource-first design

### Local profile

`configs/local.yaml` is for pipeline development and smoke tests:

- CPU;
- batch size 1;
- zero DataLoader workers;
- lazy/on-demand decoding;
- no full-dataset RAM cache;
- at most 64 samples per class for development validation.

Local reductions are never reported as paper-faithful experimental results.

### External GPU profile

`configs/train_gpu.yaml` preserves ConvNeXt-Tiny and 384 x 384 input while using:

- physical batch 8;
- gradient accumulation 4 for effective batch 32;
- mixed precision;
- two DataLoader workers;
- portrait-crop caching only.

Scripts must accept both profiles without code changes. Free/temporary notebook GPU execution is sufficient; paid infrastructure is not required.

## Hardware feasibility after M1

- Observed local RAM constraint: approximately 8 GB. Inventory code streams rows and uses ZIP central directories; image decoding is one image at a time.
- Observed free disk: 52,235,984,896 bytes (48.65 GiB).
- Complete DLC Zenodo archives: 105.9 GB compressed; they do not fit.
- Complete SIDTD media endpoints: 107.9 GB; they do not fit.
- Minimum useful retained subset: one selected DLC frame per unique capture plus manifests/hashes, estimated 1 GB.
- Recommended retained footprint including crops and exploratory SIDTD subset: 3 GB.
- Temporary peak target: at most 6 GB by streaming and deleting verified fragments.
- Estimated preprocessing RAM: under 1.5 GB with one decoder, zero/one worker, and no RetinaFace batch queue; must be measured in M2.
- Portrait extraction should run locally serially, though RetinaFace CPU latency may be several seconds per image; M2 will benchmark 32 samples.
- ConvNeXt-Tiny inference should run locally at batch 1 on CPU, slowly.
- Scientifically useful ConvNeXt training is not realistic on the laptop within 24 hours.
- External GPU is needed for the baseline and full-model training; expected combined must-have runtime is approximately 4-10 hours on a free T4/L4-class GPU, subject to actual I/O and early stopping.

## M2 plan

M2 implements portrait extraction only; no model or training code.

1. Resolve/select actual Protocol A media members. Prefer streaming the 17.77 GB FTP `clips.tar` once and retaining only deterministic annotated midpoint frames; never retain the tar and extracted full corpus together.
2. Verify every selected sample decodes and update `media_path`, dimensions, encoding, and `media_available`.
3. Compute SHA-256 and 64-bit perceptual hashes; cluster near duplicates and fail if a cluster crosses splits.
4. Re-run split/leakage validation and freeze a train-ready Protocol A manifest.
5. Implement RetinaFace threshold 0.7 with serial CPU-safe inference.
6. Implement CLAHE + RetinaFace, Haar, and configurable template fallback.
7. Crop the original image with documented alpha 0.8 geometry and context preservation; resize/pad to 384 x 384.
8. Persist only crops, bounding boxes, detector/confidence, and provenance—not split copies of originals.
9. Generate 32 extraction examples and fallback-stage success counts.
10. Benchmark peak RAM, per-image CPU time, crop storage, and batch-1 inference feasibility.
11. Stop and request approval before M3.

If media cannot be selectively acquired within storage/network constraints, M2 stops at that blocker rather than substituting unverified data.

## Subsequent milestone boundaries

- M3: clean ConvNeXt semantic baseline.
- M4-M6: texture, edge, common-space `d=256` fusion, and full model.
- M7: must-have training/evaluation.
- M8-M10: compute-gated ablations, robustness, branch/failure analysis.
- M11-M12: FastAPI and research UI.
- M13-M14: research audit, README, and deployment.
