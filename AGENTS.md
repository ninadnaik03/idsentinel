# AGENTS.md

## Scope and research integrity

- Preserve the distinction between **Original paper method**, **Our implementation**, and **Our experimental results** in documentation.
- Never fabricate metrics, dataset properties, licenses, or experimental outcomes.
- Never describe this repository as an official reproduction or imply affiliation with the paper authors.
- Keep all descendants of one `base_document_id` in one split.
- Do not use the test set for model selection, threshold selection, or hyperparameter tuning.
- Record inferred choices in `docs/IMPLEMENTATION_ASSUMPTIONS.md` before implementing them.
- Do not manually edit generated result artifacts.

## Current milestone gate

M2 through M5 are complete for **Protocol A-Reduced**. M3/M4/M5 artifacts remain
immutable. Model research is paused. Do not implement M6 or later experiments;
the active milestone is the public research website and safe publication.
