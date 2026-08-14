# Data inventory and provenance

M1 inventory date: 2026-08-13. Source images are not redistributed by this repository. Manifests reference source locations or archive members; split-specific image copies are prohibited.

## License gate

| Dataset | Version | Source | License | Research use | Redistribution |
|---|---|---|---|---|---|
| DLC-2021 | 1.0.2 | https://zenodo.org/records/6586764 and linked parts | CC BY-SA 2.5 Generic | Permitted with attribution and share-alike compliance | Do not redistribute here; any redistribution/derivative distribution must satisfy CC BY-SA 2.5. The bundled license also asks users to attribute Generated Photos in derivative works. |
| SIDTD | v1 | https://tc11.cvc.uab.es/datasets/SIDTD_1 | CC BY-SA 3.0 Unported, as displayed by TC-11 | Permitted with attribution and share-alike compliance | Do not redistribute here; archive members remain remote references. |

Authoritative DLC `license.txt`, `README.md`, and `dlc-2021.csv` are retained under `data/raw/source_metadata/dlc2021/`. The TC-11 catalog license statement is recorded in `artifacts/data/license_audit.json`; no independent license file was exposed next to the SIDTD archive during M1, so downstream users must re-check the catalog at retrieval time.

## Protocol A - primary three-class experiment

Source: DLC-2021 only.

| Mapped class | Original types | Metadata rows | Unique usable identifiers |
|---|---|---:|---:|
| BONA_FIDE | `or` | 290 | 290 |
| PRINT | `cc`, `cg` | 734 | 734 |
| SCREEN | `re` | 400 | 400 |
| **Total** | | **1,424** | **1,424** |

The latest authoritative CSV at Zenodo record 7467028 corrects the earlier duplicate `lva_passport/03.re0003` entry to `lva_passport/03.re0006`; all 1,424 identifiers are unique.

The deterministic group split uses the 80 keys `<document_type>:<specimen_number>` and seed `20250813`:

| Split | Bona fide | Print | Screen | Total |
|---|---:|---:|---:|---:|
| Train | 200 | 505 | 278 | 983 |
| Validation | 49 | 122 | 70 | 241 |
| Test | 41 | 107 | 52 | 200 |

This remains the **full DLC protocol** metadata inventory and is not train-ready locally. M2 instead completed the separately labeled **Protocol A-Reduced** below.

## Protocol A-Reduced - 24-hour reduced DLC reproduction protocol

This DLC-only subset contains 100 BONA_FIDE, 100 PRINT, and 100 SCREEN images. It is not the complete DLC benchmark. BONA_FIDE and PRINT were selectively retrieved from Zenodo; SCREEN annotated midpoint frames were extracted during an early-terminated FTP tar stream. No source archive or dataset images are redistributed through the repository.

| Split | BONA_FIDE | PRINT | SCREEN | Total |
|---|---:|---:|---:|---:|
| Train | 71 | 71 | 72 | 214 |
| Validation | 15 | 15 | 12 | 42 |
| Test | 14 | 14 | 16 | 44 |

The subset covers 80/80/50 unique base documents by class. Exact and pHash-distance-6 audits found no duplicate clusters, and no base document or capture crosses splits. The final train-ready manifest is `artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl`.

## Protocol B - exploratory composite experiment

Source: SIDTD templates only, never merged into Protocol A metrics.

Remote central-directory inventory observed:

- 3,461 archive entries;
- 2,222 JPEG images;
- 1,232 JSON annotations;
- 1,000 bona fide templates;
- 1,222 manipulated templates;
- exactly 1,000 derived `base_document_id` groups after pairing fake filenames to the real template prefix.

| Split | Bona fide | Composite | Total |
|---|---:|---:|---:|
| Train | 700 | 861 | 1,561 |
| Validation | 150 | 179 | 329 |
| Test | 150 | 182 | 332 |

SIDTD fake annotations inspected during M1 explicitly identify manipulation type and `src`; for example, `alb_id_00_fake_6_25` is `Inpaint_and_Rewrite` derived from `alb_id_00.jpg`. The manifest conservatively derives lineage from that same filename prefix for all entries. A future full annotation audit must verify every `src` and `second_src` before training.

## Leakage and duplicate status

- Group leakage tests pass for both generated manifests.
- Protocol A: 80 base groups; no group or capture crosses a split after identifier consolidation.
- Protocol B: 1,000 base groups; real and fake variants of a base remain together.
- Protocol A-Reduced has complete SHA-256/pHash coverage and passes duplicate and lineage leakage assertions.
- The full 1,424-capture DLC metadata protocol and SIDTD Protocol B do not have corpus-wide media hashes; no claim is made that those larger protocols are cleared.

## Storage

- DLC compressed archive parts required by the Zenodo layout: 105,918,680,922 bytes (~105.9 GB decimal), excluding small metadata/baseline files.
- SIDTD full published media endpoints: 107,864,783,192 bytes (~107.9 GB decimal).
- Combined full download: ~213.8 GB, impossible with the observed 48.65 GB free disk.
- DLC FTP offers a 17,768,312,320-byte `clips.tar` with byte ranges. A sequential streaming selector could retain only one frame per clip without retaining the tar, but would still transfer/scan the complete tar.
- SIDTD templates archive: 1,273,966,468 bytes compressed; range inventory avoids local extraction.

Recommended local retained footprint after selective acquisition: 1-3 GB for 1,424 DLC frames, required SIDTD exploratory images only, manifests, hashes, crops, and plots. Temporary peak should be kept below 6 GB by streaming one source at a time and deleting verified transfer fragments.

## Generated artifacts

- `artifacts/data/dlc2021_protocol_a_manifest.jsonl`
- `artifacts/data/dlc2021_protocol_a_validation.json`
- `artifacts/data/sidtd_protocol_b_manifest.jsonl`
- `artifacts/data/sidtd_protocol_b_validation.json`
- `artifacts/data/sidtd_templates_zip_inventory.json`
- `artifacts/data/source_statistics_sample.json`
- `artifacts/data/license_audit.json`
- `artifacts/data/storage_audit.json`

No experiment metrics exist at M1.

M2 preprocessing observations for Protocol A-Reduced are documented in `docs/PORTRAIT_EXTRACTION_AUDIT.md`; these are preprocessing metrics, not classifier results.
