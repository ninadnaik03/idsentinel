# M5 Failure Analysis

M5 failures: 16/44. Categories: `{'PERSISTENT_ACROSS_ALL': 5, 'NEW_EDGE_FAILURE': 7, 'CORRECTED_BY_TEXTURE_ONLY': 4}`.

## `dlc2021:aze_passport/05.or0002:annotated_midpoint`

- `BONA_FIDE` -> `SCREEN`; confidence 0.471654; PERSISTENT_ACROSS_ALL.
- Probabilities: BONA_FIDE=0.372999, PRINT=0.155347, SCREEN=0.471654.
- Padding `False`; edge norm 1.151248; crop `artifacts/data/portrait_crops_reduced/001.jpg`.
- No causal explanation is inferred.

## `dlc2021:aze_passport/07.or0001:annotated_midpoint`

- `BONA_FIDE` -> `SCREEN`; confidence 0.435101; NEW_EDGE_FAILURE.
- Probabilities: BONA_FIDE=0.350811, PRINT=0.214088, SCREEN=0.435101.
- Padding `True`; edge norm 1.112561; crop `artifacts/data/portrait_crops_reduced/002.jpg`.
- No causal explanation is inferred.

## `dlc2021:est_id/00.or0001:annotated_midpoint`

- `BONA_FIDE` -> `SCREEN`; confidence 0.542171; NEW_EDGE_FAILURE.
- Probabilities: BONA_FIDE=0.350265, PRINT=0.107564, SCREEN=0.542171.
- Padding `True`; edge norm 1.093579; crop `artifacts/data/portrait_crops_reduced/004.jpg`.
- No causal explanation is inferred.

## `dlc2021:fin_id/04.or0001:annotated_midpoint`

- `BONA_FIDE` -> `SCREEN`; confidence 0.396567; NEW_EDGE_FAILURE.
- Probabilities: BONA_FIDE=0.352250, PRINT=0.251183, SCREEN=0.396567.
- Padding `False`; edge norm 1.431688; crop `artifacts/data/portrait_crops_reduced/007.jpg`.
- No causal explanation is inferred.

## `dlc2021:grc_passport/05.or0001:annotated_midpoint`

- `BONA_FIDE` -> `SCREEN`; confidence 0.457786; PERSISTENT_ACROSS_ALL.
- Probabilities: BONA_FIDE=0.350063, PRINT=0.192151, SCREEN=0.457786.
- Padding `True`; edge norm 1.184261; crop `artifacts/data/portrait_crops_reduced/009.jpg`.
- No causal explanation is inferred.

## `dlc2021:lva_passport/02.or0001:annotated_midpoint`

- `BONA_FIDE` -> `SCREEN`; confidence 0.368230; CORRECTED_BY_TEXTURE_ONLY.
- Probabilities: BONA_FIDE=0.289967, PRINT=0.341803, SCREEN=0.368230.
- Padding `False`; edge norm 1.237147; crop `artifacts/data/portrait_crops_reduced/010.jpg`.
- No causal explanation is inferred.

## `dlc2021:srb_passport/02.or0001:annotated_midpoint`

- `BONA_FIDE` -> `SCREEN`; confidence 0.446432; CORRECTED_BY_TEXTURE_ONLY.
- Probabilities: BONA_FIDE=0.390020, PRINT=0.163548, SCREEN=0.446432.
- Padding `True`; edge norm 1.101488; crop `artifacts/data/portrait_crops_reduced/012.jpg`.
- No causal explanation is inferred.

## `dlc2021:srb_passport/03.or0001:annotated_midpoint`

- `BONA_FIDE` -> `PRINT`; confidence 0.364296; PERSISTENT_ACROSS_ALL.
- Probabilities: BONA_FIDE=0.288402, PRINT=0.364296, SCREEN=0.347302.
- Padding `False`; edge norm 1.037197; crop `artifacts/data/portrait_crops_reduced/013.jpg`.
- No causal explanation is inferred.

## `dlc2021:aze_passport/05.cg0001:annotated_midpoint`

- `PRINT` -> `SCREEN`; confidence 0.481365; NEW_EDGE_FAILURE.
- Probabilities: BONA_FIDE=0.169894, PRINT=0.348741, SCREEN=0.481365.
- Padding `False`; edge norm 1.223259; crop `artifacts/data/portrait_crops_reduced/014.jpg`.
- No causal explanation is inferred.

## `dlc2021:aze_passport/05.cg0002:annotated_midpoint`

- `PRINT` -> `SCREEN`; confidence 0.411864; PERSISTENT_ACROSS_ALL.
- Probabilities: BONA_FIDE=0.262212, PRINT=0.325924, SCREEN=0.411864.
- Padding `False`; edge norm 1.448711; crop `artifacts/data/portrait_crops_reduced/015.jpg`.
- No causal explanation is inferred.

## `dlc2021:aze_passport/07.cg0001:annotated_midpoint`

- `PRINT` -> `SCREEN`; confidence 0.401547; NEW_EDGE_FAILURE.
- Probabilities: BONA_FIDE=0.251854, PRINT=0.346599, SCREEN=0.401547.
- Padding `True`; edge norm 1.165183; crop `artifacts/data/portrait_crops_reduced/016.jpg`.
- No causal explanation is inferred.

## `dlc2021:aze_passport/07.re0002:annotated_midpoint`

- `SCREEN` -> `BONA_FIDE`; confidence 0.363987; PERSISTENT_ACROSS_ALL.
- Probabilities: BONA_FIDE=0.363987, PRINT=0.287737, SCREEN=0.348276.
- Padding `True`; edge norm 1.236397; crop `artifacts/data/portrait_crops_reduced/031.jpg`.
- No causal explanation is inferred.

## `dlc2021:fin_id/01.re0002:annotated_midpoint`

- `SCREEN` -> `BONA_FIDE`; confidence 0.526603; CORRECTED_BY_TEXTURE_ONLY.
- Probabilities: BONA_FIDE=0.526603, PRINT=0.215004, SCREEN=0.258393.
- Padding `False`; edge norm 1.050502; crop `artifacts/data/portrait_crops_reduced/035.jpg`.
- No causal explanation is inferred.

## `dlc2021:grc_passport/03.re0001:annotated_midpoint`

- `SCREEN` -> `BONA_FIDE`; confidence 0.437913; CORRECTED_BY_TEXTURE_ONLY.
- Probabilities: BONA_FIDE=0.437913, PRINT=0.148852, SCREEN=0.413235.
- Padding `True`; edge norm 1.027295; crop `artifacts/data/portrait_crops_reduced/038.jpg`.
- No causal explanation is inferred.

## `dlc2021:grc_passport/05.re0001:annotated_midpoint`

- `SCREEN` -> `BONA_FIDE`; confidence 0.498923; NEW_EDGE_FAILURE.
- Probabilities: BONA_FIDE=0.498923, PRINT=0.143884, SCREEN=0.357194.
- Padding `True`; edge norm 1.128985; crop `artifacts/data/portrait_crops_reduced/040.jpg`.
- No causal explanation is inferred.

## `dlc2021:grc_passport/05.re0002:annotated_midpoint`

- `SCREEN` -> `BONA_FIDE`; confidence 0.563423; NEW_EDGE_FAILURE.
- Probabilities: BONA_FIDE=0.563423, PRINT=0.128112, SCREEN=0.308465.
- Padding `True`; edge norm 1.072463; crop `artifacts/data/portrait_crops_reduced/041.jpg`.
- No causal explanation is inferred.
