# M3 Failure Analysis

Protocol A-Reduced (300-sample leakage-safe DLC-2021 reduced protocol). These are our observed results, not full-DLC or paper-reported results.

Observed test errors: 18 of 44.

The confusion matrix shows six SCREEN→BONA_FIDE, five BONA_FIDE→PRINT, three BONA_FIDE→SCREEN, three PRINT→BONA_FIDE, and one PRINT→SCREEN errors. These are observed transitions. Any explanation involving glare, blur, texture, display boundaries, or crop context requires human visual review and is not inferred automatically.

Padding diagnostic: padded errors 8/22 (36.4%); non-padded errors 10/22 (45.5%). This descriptive association does not establish causality.

## dlc2021:aze_passport/05.or0001:annotated_midpoint

- Observed: `BONA_FIDE` → `PRINT`; confidence 0.4336.
- Probabilities: `{"BONA_FIDE": 0.29418203234672546, "PRINT": 0.4336118996143341, "SCREEN": 0.2722060978412628}`.
- Base document: `dlc2021:aze_passport:05`; capture: `aze_passport/05.or0001:device=android:condition=artificial light + bright objects`; document type: `aze_passport`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `or/clips/images/aze_passport/05.or0001/000121.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/000.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:aze_passport/05.or0002:annotated_midpoint

- Observed: `BONA_FIDE` → `SCREEN`; confidence 0.3810.
- Probabilities: `{"BONA_FIDE": 0.2631378769874573, "PRINT": 0.35582271218299866, "SCREEN": 0.38103941082954407}`.
- Base document: `dlc2021:aze_passport:05`; capture: `aze_passport/05.or0002:device=iphone:condition=artificial light + bright objects`; document type: `aze_passport`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `or/clips/images/aze_passport/05.or0002/000244.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/001.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:est_id/05.or0001:annotated_midpoint

- Observed: `BONA_FIDE` → `SCREEN`; confidence 0.4518.
- Probabilities: `{"BONA_FIDE": 0.38673466444015503, "PRINT": 0.16144965589046478, "SCREEN": 0.4518156349658966}`.
- Base document: `dlc2021:est_id:05`; capture: `est_id/05.or0001:device=android:condition=artificial light`; document type: `est_id`.
- Padding: `True`; detector stage (analysis only): `retinaface`.
- Source member: `or/clips/images/est_id/05.or0001/000131.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/005.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:grc_passport/03.or0001:annotated_midpoint

- Observed: `BONA_FIDE` → `PRINT`; confidence 0.3364.
- Probabilities: `{"BONA_FIDE": 0.32712432742118835, "PRINT": 0.3364470601081848, "SCREEN": 0.33642861247062683}`.
- Base document: `dlc2021:grc_passport:03`; capture: `grc_passport/03.or0001:device=android:condition=colored light`; document type: `grc_passport`.
- Padding: `True`; detector stage (analysis only): `retinaface`.
- Source member: `or/clips/images/grc_passport/03.or0001/000126.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/008.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:grc_passport/05.or0001:annotated_midpoint

- Observed: `BONA_FIDE` → `PRINT`; confidence 0.5586.
- Probabilities: `{"BONA_FIDE": 0.21002866327762604, "PRINT": 0.5585547685623169, "SCREEN": 0.23141659796237946}`.
- Base document: `dlc2021:grc_passport:05`; capture: `grc_passport/05.or0001:device=android:condition=artificial light + flash`; document type: `grc_passport`.
- Padding: `True`; detector stage (analysis only): `retinaface`.
- Source member: `or/clips/images/grc_passport/05.or0001/000125.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/009.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:lva_passport/02.or0001:annotated_midpoint

- Observed: `BONA_FIDE` → `SCREEN`; confidence 0.5932.
- Probabilities: `{"BONA_FIDE": 0.10251076519489288, "PRINT": 0.30433180928230286, "SCREEN": 0.5931574106216431}`.
- Base document: `dlc2021:lva_passport:02`; capture: `lva_passport/02.or0001:device=android:condition=daylight + alternating shadow`; document type: `lva_passport`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `or/clips/images/lva_passport/02.or0001/000117.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/010.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:srb_passport/02.or0001:annotated_midpoint

- Observed: `BONA_FIDE` → `PRINT`; confidence 0.4049.
- Probabilities: `{"BONA_FIDE": 0.22782103717327118, "PRINT": 0.4049130380153656, "SCREEN": 0.36726588010787964}`.
- Base document: `dlc2021:srb_passport:02`; capture: `srb_passport/02.or0001:device=android:condition=artificial light + flash`; document type: `srb_passport`.
- Padding: `True`; detector stage (analysis only): `retinaface`.
- Source member: `or/clips/images/srb_passport/02.or0001/000121.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/012.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:srb_passport/03.or0001:annotated_midpoint

- Observed: `BONA_FIDE` → `PRINT`; confidence 0.5502.
- Probabilities: `{"BONA_FIDE": 0.20347246527671814, "PRINT": 0.5501930713653564, "SCREEN": 0.2463344782590866}`.
- Base document: `dlc2021:srb_passport:03`; capture: `srb_passport/03.or0001:device=android:condition=colored light`; document type: `srb_passport`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `or/clips/images/srb_passport/03.or0001/000117.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/013.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:aze_passport/05.cg0002:annotated_midpoint

- Observed: `PRINT` → `BONA_FIDE`; confidence 0.4618.
- Probabilities: `{"BONA_FIDE": 0.46175017952919006, "PRINT": 0.14593425393104553, "SCREEN": 0.39231550693511963}`.
- Base document: `dlc2021:aze_passport:05`; capture: `aze_passport/05.cg0002:device=iphone:condition=artificial light + bright objects`; document type: `aze_passport`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `cg/clips/images/aze_passport/05.cg0002/000226.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/015.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:aze_passport/07.cg0002:annotated_midpoint

- Observed: `PRINT` → `SCREEN`; confidence 0.3737.
- Probabilities: `{"BONA_FIDE": 0.27525007724761963, "PRINT": 0.35109856724739075, "SCREEN": 0.3736513555049896}`.
- Base document: `dlc2021:aze_passport:07`; capture: `aze_passport/07.cg0002:device=iphone:condition=artificial light + flash`; document type: `aze_passport`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `cg/clips/images/aze_passport/07.cg0002/000226.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/017.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:fin_id/04.cg0001:annotated_midpoint

- Observed: `PRINT` → `BONA_FIDE`; confidence 0.3729.
- Probabilities: `{"BONA_FIDE": 0.37294700741767883, "PRINT": 0.33416953682899475, "SCREEN": 0.2928834855556488}`.
- Base document: `dlc2021:fin_id:04`; capture: `fin_id/04.cg0001:device=android:condition=artificial light + flash`; document type: `fin_id`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `cg/clips/images/fin_id/04.cg0001/000097.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/021.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:rus_internalpassport/04.cg0001:annotated_midpoint

- Observed: `PRINT` → `BONA_FIDE`; confidence 0.4242.
- Probabilities: `{"BONA_FIDE": 0.42421382665634155, "PRINT": 0.3611619174480438, "SCREEN": 0.2146243005990982}`.
- Base document: `dlc2021:rus_internalpassport:04`; capture: `rus_internalpassport/04.cg0001:device=android:condition=colored light`; document type: `rus_internalpassport`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `cg/clips/images/rus_internalpassport/04.cg0001/000495.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/025.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:aze_passport/05.re0001:annotated_midpoint

- Observed: `SCREEN` → `BONA_FIDE`; confidence 0.4412.
- Probabilities: `{"BONA_FIDE": 0.44124215841293335, "PRINT": 0.30133745074272156, "SCREEN": 0.2574203610420227}`.
- Base document: `dlc2021:aze_passport:05`; capture: `aze_passport/05.re0001:device=iphone:condition=macbook pro`; document type: `aze_passport`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `clips/images/aze_passport/05.re0001/000261.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/028.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:aze_passport/07.re0002:annotated_midpoint

- Observed: `SCREEN` → `BONA_FIDE`; confidence 0.3766.
- Probabilities: `{"BONA_FIDE": 0.37661638855934143, "PRINT": 0.2754618227481842, "SCREEN": 0.34792181849479675}`.
- Base document: `dlc2021:aze_passport:07`; capture: `aze_passport/07.re0002:device=iphone:condition=philips`; document type: `aze_passport`.
- Padding: `True`; detector stage (analysis only): `retinaface`.
- Source member: `clips/images/aze_passport/07.re0002/000235.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/031.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:est_id/00.re0001:annotated_midpoint

- Observed: `SCREEN` → `BONA_FIDE`; confidence 0.4534.
- Probabilities: `{"BONA_FIDE": 0.4534033238887787, "PRINT": 0.17114178836345673, "SCREEN": 0.3754548728466034}`.
- Base document: `dlc2021:est_id:00`; capture: `est_id/00.re0001:device=iphone:condition=lenovo`; document type: `est_id`.
- Padding: `True`; detector stage (analysis only): `retinaface`.
- Source member: `clips/images/est_id/00.re0001/000235.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/032.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:est_id/00.re0002:annotated_midpoint

- Observed: `SCREEN` → `BONA_FIDE`; confidence 0.5948.
- Probabilities: `{"BONA_FIDE": 0.5947547554969788, "PRINT": 0.2275676429271698, "SCREEN": 0.17767758667469025}`.
- Base document: `dlc2021:est_id:00`; capture: `est_id/00.re0002:device=iphone:condition=macbook pro`; document type: `est_id`.
- Padding: `True`; detector stage (analysis only): `retinaface`.
- Source member: `clips/images/est_id/00.re0002/000235.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/033.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:fin_id/01.re0002:annotated_midpoint

- Observed: `SCREEN` → `BONA_FIDE`; confidence 0.3912.
- Probabilities: `{"BONA_FIDE": 0.39119431376457214, "PRINT": 0.32207804918289185, "SCREEN": 0.2867276668548584}`.
- Base document: `dlc2021:fin_id:01`; capture: `fin_id/01.re0002:device=iphone:condition=macbook pro`; document type: `fin_id`.
- Padding: `False`; detector stage (analysis only): `retinaface`.
- Source member: `clips/images/fin_id/01.re0002/000244.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/035.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.

## dlc2021:grc_passport/03.re0001:annotated_midpoint

- Observed: `SCREEN` → `BONA_FIDE`; confidence 0.5000.
- Probabilities: `{"BONA_FIDE": 0.4999619722366333, "PRINT": 0.16709619760513306, "SCREEN": 0.33294177055358887}`.
- Base document: `dlc2021:grc_passport:03`; capture: `grc_passport/03.re0001:device=iphone:condition=hp`; document type: `grc_passport`.
- Padding: `True`; detector stage (analysis only): `retinaface`.
- Source member: `clips/images/grc_passport/03.re0001/000235.jpg`.
- Crop: `artifacts/data/portrait_crops_reduced/038.jpg` (GPU-bundle path; map by sample ID to the frozen local manifest).
- Possible explanation: not assigned automatically; visual interpretation would be speculative.
