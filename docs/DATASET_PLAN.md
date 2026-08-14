# Dataset Plan

## Decision summary

M1 ruling: **do not merge DLC-2021 and SIDTD into a primary four-class benchmark**.

- Protocol A uses DLC-2021 only for BONA_FIDE, PRINT, and SCREEN.
- Protocol B separately uses SIDTD bona fide and synthetic composite templates.
- The raw sources are trivially distinguishable by aspect ratio and acquisition format; details are in `SOURCE_CONFOUND_AUDIT.md`.
- No result may combine Protocol A and Protocol B metrics or present the mixed construction as four-class forensic evidence.

## Candidate audit

### DLC-2021 - primary source for bona fide, print, and screen

- Access: open Zenodo records; large multipart download.
- Scale: 1,424 videos, each at least five seconds; first 50 frames are annotated.
- Clip counts:
  - original laminated (`or`): 290;
  - unlaminated color copy (`cc`): 484;
  - unlaminated gray copy (`cg`): 250;
  - screen recapture (`re`): 400.
- Ten synthetic/mock identity-document types and eight physical examples per type are described by the dataset paper.
- Privacy: mock documents with generated owner photos and artificial personal information.
- Proposed mapping:
  - `or` -> BONA_FIDE;
  - `cc` and `cg` -> PRINT;
  - `re` -> SCREEN.
- Limitation: “original” means the laminated mock-document acquisition, not a government-issued real ID. Print subclasses are unlaminated hard copies. Frames within a video are highly correlated.
- License gate: M1 must download and hash the record's `license.txt` and record its exact terms before any data use. The research article is CC BY, but that alone must not be substituted for the dataset-file license.

### SIDTD - primary source for composite

- Access: public TC-11/CVC download links.
- License displayed by TC-11: Creative Commons Attribution-ShareAlike 3.0 Unported; M1 must preserve the downloaded license and confirm that every selected component is covered.
- Ten European document nationalities based on MIDV-2020.
- Composite techniques: crop-and-replace and inpainting.
- The source reports 191 physically produced counterfeit documents and 7,214 extracted fake clips/frames; MIDV-2020-derived bona fide clips are much more numerous.
- Proposed mapping: forged crop-and-replace/inpainting samples -> COMPOSITE.
- Limitation: these are synthetic/digital manipulations, and the capture process differs from DLC-2021. They must never be described as naturally occurring or real-world composite attacks.

### KID34K - not selected for M1

- The Zenodo record is restricted and has no downloadable files.
- Access requires a request workflow; licensing and exact usable class counts cannot be verified locally at M0.
- It remains a future optional external-validation source if access and license are granted.

### MIDV-2020 - metadata/base-document support, not a PAD class source by itself

- 1,000 unique mock identity documents, 1,000 video clips, 2,000 scans, 1,000 photos, and 72,409 annotated images in total.
- Useful for provenance/group identifiers and for understanding SIDTD lineage.
- It does not independently supply the full print/screen/composite PAD taxonomy required here.

### Other candidates

- Syn-IDPASS: exactly 9,000 images across three countries (3,000 each of bona fide, print, and screen), but access requires a signed license agreement and composite is absent. It is a strong optional replacement/validation set if access is granted.
- FantasyID: publicly described as 786 bona fide and 1,572 manipulated samples, mostly CC BY 4.0; it supports composite manipulation but not the required print/screen taxonomy as separate attack labels. It may become an external composite test set after exact download and license verification.
- FMIDV: 28,000 copy-move forgeries but access is by request and it does not solve the complete four-class PAD problem.

## Superseded M0 estimate

The table below was the pre-inspection M0 estimate and is retained only for audit history. It is not approved:

| Class | Source | Expected samples before QC |
|---|---|---:|
| BONA_FIDE | DLC `or` | 290 |
| PRINT | DLC `cc` + `cg` | 734 |
| SCREEN | DLC `re` | 400 |
| COMPOSITE | SIDTD fake clips, grouped by forged base document | cap at 734 |
| **Total** | mixed | **2,158** |

The composite cap prevents one source from dominating. If fewer than 734 distinct group-safe SIDTD items survive QC, retain all valid groups and use capped class weights; do not oversample before splitting.

Expected post-QC count: approximately **1,900-2,150 images**, depending on corrupt files, missing portrait annotations, license scope, and whether 734 sufficiently independent SIDTD groups exist. This is an estimate, not an observed count.

A secondary scale-up manifest may select up to five temporally separated frames per DLC video only after the one-frame pipeline passes leakage tests. Every frame from a clip/document remains in the same split, and bootstrap resampling operates on the base group. The scale-up ceiling would be about 10,790 images under the same class cap, but it must not be called 10,790 independent samples.

## Split and leakage policy

- Target split: 70% train, 15% validation, 15% test.
- Split unit: strongest available lineage key, not image path.
- DLC group key: physical document identity if derivable; otherwise document type + specimen number, with video ID nested below it.
- SIDTD group key: original MIDV document/base template plus all forged derivatives and capture frames.
- A base document and every derivative must occur in exactly one split.
- Prefer stratified group assignment with deterministic seed and a manifest committed to the repository.
- No test access during model selection, augmentation selection, threshold selection, or early stopping.
- Duplicate checks: exact SHA-256, perceptual hash, and lineage metadata overlap.
- Report both image-level metrics and base-group bootstrap confidence intervals later.

## Source-confound controls

The proposed four-way dataset has a severe structural confound: COMPOSITE comes from SIDTD while the other classes come from DLC-2021. Required controls:

1. Train a source-only classifier or use source prediction diagnostics to quantify dataset separability.
2. Evaluate binary tasks within sources where labels permit.
3. Match resolution/compression distributions without destroying forensic cues.
4. Report per-source and per-document-type performance.
5. Treat four-class results as exploratory if class and source remain inseparable.
6. Do not claim the model learned composite boundaries merely from high composite F1.

## Genuinely supported attack classes

- BONA_FIDE: supported as captures of synthetic/mock laminated documents.
- PRINT: supported as physically captured unlaminated color and grayscale copies.
- SCREEN: supported as physical recaptures from device displays.
- COMPOSITE: supported only as synthetic/digitally generated crop-and-replace or inpainting manipulation, potentially with physical recapture in SIDTD. It is not equivalent to the paper's private competition composite distribution.

## Blockers requiring approval or M1 verification

- **BLOCKER:** exact DLC dataset-file license terms must be read and accepted before download/use.
- **BLOCKER:** SIDTD archives must be inspected to verify exact independent base-document IDs and usable composite counts; 7,214 frames are not 7,214 independent documents.
- **HIGH:** class label is confounded with dataset source for COMPOSITE.
- **HIGH:** access/download footprint is large (DLC part 1 alone is about 33.9 GB; all required parts require substantially more storage).
- **HIGH:** portrait crops may fail or be ill-defined for passport layouts and non-card documents; scope may need restriction to card-shaped ID types.
- **MEDIUM:** one-frame-per-clip selection policy must be deterministic and avoid quality cherry-picking.
- **MEDIUM:** class balance will be imperfect and independent group counts may be small.
- **MEDIUM:** public sources use mock/synthetic identities and do not establish real-world deployment validity.

## Provenance fields required in M1

`sample_id`, `source_dataset`, `source_version`, `source_url`, `license_id`, `archive_sha256`, `base_document_id`, `capture_id`, `frame_index`, `document_type`, `original_label`, `mapped_label`, `is_synthetic_identity`, `is_synthetic_attack`, `split`, and `mapping_rationale`.
