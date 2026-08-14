# M4 SCREEN Error Comparison

The six rows below are exactly the M3 SCREEN->BONA_FIDE errors. Probabilities follow BONA_FIDE, PRINT, SCREEN.

## `dlc2021:aze_passport/05.re0001:annotated_midpoint`

- M3: `BONA_FIDE`; BONA_FIDE=0.441242, PRINT=0.301337, SCREEN=0.257420.
- M4: `BONA_FIDE`; BONA_FIDE=0.507344, PRINT=0.131583, SCREEN=0.361073.
- Outcome: **PRESERVED**.

## `dlc2021:aze_passport/07.re0002:annotated_midpoint`

- M3: `BONA_FIDE`; BONA_FIDE=0.376616, PRINT=0.275462, SCREEN=0.347922.
- M4: `BONA_FIDE`; BONA_FIDE=0.547369, PRINT=0.151794, SCREEN=0.300837.
- Outcome: **PRESERVED**.

## `dlc2021:est_id/00.re0001:annotated_midpoint`

- M3: `BONA_FIDE`; BONA_FIDE=0.453403, PRINT=0.171142, SCREEN=0.375455.
- M4: `SCREEN`; BONA_FIDE=0.281064, PRINT=0.163358, SCREEN=0.555578.
- Outcome: **CORRECTED**.

## `dlc2021:est_id/00.re0002:annotated_midpoint`

- M3: `BONA_FIDE`; BONA_FIDE=0.594755, PRINT=0.227568, SCREEN=0.177678.
- M4: `SCREEN`; BONA_FIDE=0.215369, PRINT=0.161413, SCREEN=0.623218.
- Outcome: **CORRECTED**.

## `dlc2021:fin_id/01.re0002:annotated_midpoint`

- M3: `BONA_FIDE`; BONA_FIDE=0.391194, PRINT=0.322078, SCREEN=0.286728.
- M4: `SCREEN`; BONA_FIDE=0.303312, PRINT=0.174685, SCREEN=0.522002.
- Outcome: **CORRECTED**.

## `dlc2021:grc_passport/03.re0001:annotated_midpoint`

- M3: `BONA_FIDE`; BONA_FIDE=0.499962, PRINT=0.167096, SCREEN=0.332942.
- M4: `SCREEN`; BONA_FIDE=0.287403, PRINT=0.135716, SCREEN=0.576881.
- Outcome: **CORRECTED**.

Summary: 4/6 corrected, 2/6 preserved, 0/6 changed to another wrong class.
