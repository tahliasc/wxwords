# Classifier Skill Report

Comparison of the WxWords ResNet50V2 cloud classifier (trained on CCSN, 11 classes) against the native labels of two external ground-based cloud datasets: TJNU GCD (7 broad WMO categories) and WEBCAM aviation (9 operational classes).

The model was trained only on CCSN. These datasets are out-of-sample tests of how well the model generalises to imagery captured by different cameras, in different locations, under different conditions.

## How to read this report

- Each row is a **native dataset class**, with the count of images and the distribution of CCSN predictions the model produced.
- The **Top match** column shows which CCSN class the model picked most often for that native class.
- The **Plausible %** column shows the share of predictions that fall within a human-judged set of acceptable CCSN matches. For example, TJNU class 2 (Altocumulus/Cirrocumulus) maps to Ac or Cc — a prediction of either counts as plausible.
- The **Native class** column shows the dataset's own label, which is taken as ground truth.
- **Limitations:** native datasets have their own labelling biases. WEBCAM 'precip' is a weather state not a cloud genus, so any CCSN mapping is approximate.

---

## TJNU Ground-based Cloud Dataset (19,000 images, 7 classes)

| Native class | n | Ac | As | Cb | Cc | Ci | Cs | Ct | Cu | Ns | Sc | St | Top match | Plausible % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Altocumulus/Cirrocumulus** (2) | 1475 | 25 | · | · | **52** | · | · | · | · | · | · | · | Cc (52%) | 76% |
| **Cirrus/Cirrostratus** (3) | 1906 | · | 20 | · | 18 | **42** | · | · | · | · | · | · | Ci (42%) | 49% |
| **Clear sky** (4) | 3739 | · | · | · | 38 | · | 35 | · | · | · |  | · | Cc (38%) | n/a |
| **Cumulonimbus/Nimbostratus** (6) | 5764 | · | **66** | · | · | · | · | · | · | 25 | · | · | As (66%) | 25% |
| **Cumulus** (1) | 1525 | **42** | · | · | · | · | · | · | 17 | · |  | · | Ac (42%) | 17% |
| **Mixed cloud** (7) | 955 | 16 | 28 | · | 20 | · | · | · | · | 22 | · | · | As (28%) | 100% |
| **Stratocumulus/Stratus/Altostratus** (5) | 3636 | · | **55** | · | · | · | · | · |  | 19 | · | · | As (55%) | 57% |

**Overall plausible-match rate: 35.6%** (6,772 / 19,000 images)

_Values are % of native class's images predicted as each CCSN class. **Bold** ≥40%, plain ≥15%, · means <15% but non-zero. 'Plausible %' is the rate at which the model predicted a class that overlaps the native class's true cloud types._

### TJNU — model confidence distribution

| Top-1 confidence | n | % |
|---|---|---|
| >= 80% | 226 | 1.2% |
| 60-80% | 1,148 | 6.0% |
| 40-60% | 7,102 | 37.4% |
| 20-40% | 9,896 | 52.1% |
| < 20% | 628 | 3.3% |

### TJNU — what the model predicted most

| Predicted CCSN class | n | % |
|---|---|---|
| As | 7,167 | 37.7% |
| Cc | 3,567 | 18.8% |
| Ns | 2,643 | 13.9% |
| Cs | 1,908 | 10.0% |
| Ci | 1,549 | 8.2% |
| Ac | 1,444 | 7.6% |
| Cu | 314 | 1.7% |
| Ct | 231 | 1.2% |
| St | 92 | 0.5% |
| Sc | 57 | 0.3% |
| Cb | 28 | 0.1% |

---

## WEBCAM Aviation Cloud Dataset (15,543 images, 9 classes)

| Native class | n | Ac | As | Cb | Cc | Ci | Cs | Ct | Cu | Ns | Sc | St | Top match | Plausible % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Altocumulus** (ac) | 1974 | · | · | · | 20 | · | 37 | · | · | · | · | · | Cs (37%) | 4% |
| **Cirrus** (ci) | 2263 | · | · | · | · | · | **54** | · | · | · | · | · | Cs (54%) | 10% |
| **Clear sky** (clear) | 2600 | · | · | · | · | · | **62** | · | · | · | · | · | Cs (62%) | n/a |
| **Cumulonimbus** (cb) | 776 | · | · | · | · | · | · | · | 21 | 29 | · | · | Ns (29%) | 11% |
| **Fair-weather Cumulus** (cu) | 2626 | · | · | · | · | · | 28 | · | 16 | 15 | · | · | Cs (28%) | 16% |
| **Obscured / Fog** (obsc) | 1896 | · | 29 | · | · | · | **41** | · |  | 21 | · | · | Cs (41%) | 24% |
| **Precipitation** (precip) | 1028 | · | · | · | · |  | · | · | · | **57** | · | · | Ns (57%) | 58% |
| **Stratus** (st) | 1321 | · | · | · | · | · | · | · |  | **46** | · | 17 | Ns (46%) | 17% |
| **Towering Cumulus** (tcu) | 1059 | · | · | · | · | · | · | · | 24 | 20 | · | · | Cu (24%) | 38% |

**Overall plausible-match rate: 15.9%** (2,469 / 15,543 images)

_Values are % of native class's images predicted as each CCSN class. **Bold** ≥40%, plain ≥15%, · means <15% but non-zero. 'Plausible %' is the rate at which the model predicted a class that overlaps the native class's true cloud types._

### WEBCAM — model confidence distribution

| Top-1 confidence | n | % |
|---|---|---|
| >= 80% | 170 | 1.1% |
| 60-80% | 956 | 6.2% |
| 40-60% | 4,048 | 26.0% |
| 20-40% | 9,204 | 59.2% |
| < 20% | 1,165 | 7.5% |

### WEBCAM — what the model predicted most

| Predicted CCSN class | n | % |
|---|---|---|
| Cs | 5,694 | 36.6% |
| Ns | 3,094 | 19.9% |
| Cc | 1,271 | 8.2% |
| As | 1,266 | 8.1% |
| St | 1,038 | 6.7% |
| Sc | 932 | 6.0% |
| Cu | 859 | 5.5% |
| Ci | 434 | 2.8% |
| Ac | 345 | 2.2% |
| Cb | 326 | 2.1% |
| Ct | 284 | 1.8% |

---

## Observations

This section is auto-generated from the data; treat it as a starting point for analysis, not conclusions.

### TJNU

- ✗ **Cumulus** — 17% plausible. Model's top pick: Ac (outside plausible set).
- ✓ **Altocumulus/Cirrocumulus** — 76% plausible. Model's top pick: Cc (within plausible set).
- ⚠ **Cirrus/Cirrostratus** — 49% plausible. Model's top pick: Ci (within plausible set).
- ⚠ **Stratocumulus/Stratus/Altostratus** — 57% plausible. Model's top pick: As (within plausible set).
- ✗ **Cumulonimbus/Nimbostratus** — 25% plausible. Model's top pick: As (outside plausible set).
- ✓ **Mixed cloud** — 100% plausible. Model's top pick: As (within plausible set).

### WEBCAM

- ✗ **Altocumulus** — 4% plausible. Model's top pick: Cs (outside plausible set).
- ✗ **Cumulonimbus** — 11% plausible. Model's top pick: Ns (outside plausible set).
- ✗ **Cirrus** — 10% plausible. Model's top pick: Cs (outside plausible set).
- ✗ **Fair-weather Cumulus** — 16% plausible. Model's top pick: Cs (outside plausible set).
- ✗ **Obscured / Fog** — 24% plausible. Model's top pick: Cs (outside plausible set).
- ⚠ **Precipitation** — 58% plausible. Model's top pick: Ns (within plausible set).
- ✗ **Stratus** — 17% plausible. Model's top pick: Ns (outside plausible set).
- ⚠ **Towering Cumulus** — 38% plausible. Model's top pick: Cu (within plausible set).

### Takeaways for retraining

- Classes where plausible-match is low indicate either (a) genuine domain shift, (b) class mismatch between the native dataset and CCSN, or (c) under-representation in CCSN's 2,543 training images.
- Adding sorted images from TJNU and WEBCAM into the training set should lift performance on these classes substantially.
- The Clear / Fog / Rainbow classes you've added aren't in CCSN, so this report doesn't measure them — but TJNU class 4 (Clear sky) and WEBCAM 'obsc' contribute ready-labelled images for those classes once sorted.
