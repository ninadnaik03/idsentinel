# Source-Confound Audit

## Decision

**BLOCKER: the proposed DLC-2021 + SIDTD four-class construction is rejected as the primary benchmark.**

Answer to the required question:

> Could a classifier predict COMPOSITE primarily by identifying which dataset produced the image?

**Yes.** In the inspected construction, every composite sample would be a SIDTD template while every bona fide/print/screen sample would be a DLC video frame. Dataset identity is therefore deterministically associated with COMPOSITE. More importantly, basic non-semantic statistics visibly separate the sources.

No four-class result from that naive merge may be presented as evidence that the model learned composite boundaries.

## Evidence

### Deterministic source/class relationship

| Dataset | Bona fide | Print | Screen | Composite |
|---|---:|---:|---:|---:|
| DLC-2021 proposed subset | yes | yes | yes | no |
| SIDTD templates | yes | no | no | yes |

Adding SIDTD bona fide controls would make “SIDTD means composite” non-deterministic, but PRINT and SCREEN would still identify DLC, and composite would still identify SIDTD. This reduces but does not control the confound for four-class classification.

### Non-semantic image-statistic sample

Twenty images were selectively decoded via HTTP range reads: five DLC originals, five DLC gray copies, five SIDTD bona fide templates, and five SIDTD manipulated templates.

Observed dimensions/aspect ratios:

- All 10 sampled DLC frames were portrait camera frames at 1080 x 1920 or 2160 x 3840, aspect ratio exactly 0.5625.
- The 10 sampled SIDTD templates were landscape document images with aspect ratios from 1.4147 to 1.6046 and dimensions such as 2167 x 1360, 1327 x 827, and 1134 x 716.
- All samples were JPEG, but DLC sample sizes were roughly 50-249 kB while SIDTD samples were roughly 139 kB-1.86 MB.
- RGB means and standard deviations also differed, although the sample is too small to generalize those distributions.

On this audited sample, the rule `aspect_ratio < 1 => DLC; aspect_ratio > 1 => SIDTD` separates all 20/20 images without semantic content. This is not a trained source classifier and is not a population accuracy estimate; it is direct proof that the proposed raw-input merge contains an obvious source shortcut.

The complete values and archive member names are stored in `artifacts/data/source_statistics_sample.json`.

### Coverage limits

- DLC `or` and `cg` are standalone ZIPs and support range inspection.
- DLC `cc` and `re` are split/multipart ZIPs; Python's ZIP reader cannot access the final segment alone, and full acquisition exceeds practical local storage.
- Corpus-wide source classification, compression-distribution tests, and near-duplicate hashing were therefore not completed.

These limits do not weaken the blocker: the deterministic label/source mapping and 20/20 aspect-ratio separation already invalidate the naive merged benchmark.

## Can SIDTD controls repair the four-class dataset?

SIDTD contains sufficient bona fide controls for a separate experiment: 1,000 real templates accompany 1,222 fake templates, and filenames/annotations connect manipulations to source templates. However:

1. SIDTD bona fide versus SIDTD composite is a different acquisition task from DLC camera-frame PAD.
2. SIDTD templates do not provide matched print and screen classes under the same source pipeline.
3. Combining sources would leave a one-way shortcut: COMPOSITE occurs only in SIDTD.

Conclusion: SIDTD controls make Protocol B scientifically interpretable, but do not make the mixed four-class benchmark clean.

## Can equivalent composite attacks be generated from DLC documents?

Technically, a lineage-preserving generator could manipulate a DLC base document's portrait region and assign the derivative the same `base_document_id`. Scientifically, this was not approved or implemented in M1 because:

- it would create synthetic composites with generator-specific shortcuts;
- the transformation must operate before or consistently across physical capture to match DLC acquisition;
- label leakage and boundary artifacts would require a dedicated validation study;
- generated attacks cannot be represented as real-world composite data.

This is a future dataset-research option, not evidence that a clean four-class protocol currently exists.

## Approved candidate protocols

### Protocol A - primary architecture experiment

- Dataset: DLC-2021 only.
- Classes: BONA_FIDE, PRINT, SCREEN.
- Unique metadata-addressable samples: 1,424 after the authoritative `re0006` metadata correction.
- Base groups: 80.
- Purpose: compare semantic baseline and full multi-branch architecture without dataset source predicting class.
- Status: scientifically recommended; media acquisition and whole-corpus duplicate clearance remain required before training.

### Protocol B - exploratory composite experiment

- Dataset: SIDTD templates only.
- Classes: BONA_FIDE versus COMPOSITE.
- Samples: 1,000 bona fide + 1,222 manipulated.
- Base groups: 1,000, with derivatives grouped with their original.
- Purpose: exploratory within-source manipulation detection.
- Status: separate benchmark only; never merge its metrics with Protocol A.

## Final ruling

The main benchmark is three-class Protocol A. COMPOSITE is retained only in separately labeled Protocol B. A four-class benchmark remains blocked until all classes can be produced under a defensibly matched source/acquisition protocol and a source-only diagnostic fails to predict class-relevant source identity.
