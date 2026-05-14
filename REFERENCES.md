# WxWords — References & Attribution

Project documentation covering all datasets, algorithms, APIs, and third-party services
used in the WxWords cloud classification and weather forecast system.

---

## Te Reo Māori Weather Knowledge

### Apanui Skipper's PhD thesis

The kupu huarere (weather words) page is compiled from the appendices of:

> Skipper, A. (2020). *Ko te kawa tūpanapana i ngā hau tūpua a Tāwhiri-Mātea: The
> Validation, Revitalisation and Enhancement of Māori Environmental Knowledge of
> Weather and Climate* [PhD thesis, The University of Waikato]. Research Commons.
> https://researchcommons.waikato.ac.nz/

- **Author:** Apanui Skipper
- **Year:** 2020
- **Institution:** The University of Waikato
- **Copyright:** Apanui Skipper; reproduction requires author permission per the
  Research Commons copyright statement (Copyright Act 1994, NZ).

Content reproduced from the thesis includes the classification tables, weather
indicators, and te reo Māori glossary spanning Hauraki, Te Whānau-a-Apanui, and
Ngāi Tahu kōrero. Each entry retains the original kaikōrero and source attribution
exactly as recorded in the thesis.

---

## Datasets

### CCSN (Cirrus Cumulus Stratus Nimbus) Database

The primary training dataset. 2,543 images across 11 cloud genera classes (Ac, As, Cb,
Cc, Ci, Cs, Ct, Cu, Ns, Sc, St) at 256×256 JPEG.

- **Source:** [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/CADDPD)
- **Mirror:** [Kaggle](https://www.kaggle.com/datasets/mmichelli/cirrus-cumulus-stratus-nimbus-ccsn-database)
- **GitHub:** https://github.com/upuil/CCSN-Database
- **License:** CC0 1.0 Public Domain Dedication
- **Dataset DOI:** [10.7910/DVN/CADDPD](https://doi.org/10.7910/DVN/CADDPD)

**Citation:**

> Zhang, J., Liu, P., Zhang, F., & Song, Q. (2018). CloudNet: Ground-Based Cloud
> Classification With Deep Convolutional Neural Network. *Geophysical Research Letters*,
> 45(16), 8665–8672. DOI: [10.1029/2018GL077787](https://doi.org/10.1029/2018GL077787)

---

### TJNU Ground-based Cloud Dataset (GCD)

Supplementary dataset used to expand training data. 19,000 images across 7 WMO-aligned
cloud categories at 512×512 JPEG, with predefined train/test split (10,000/9,000).
Collected 2019–2020 across nine Chinese provinces.

| Class | Description                               |
|-------|-------------------------------------------|
| 1     | Cumulus                                   |
| 2     | Altocumulus and Cirrocumulus               |
| 3     | Cirrus and Cirrostratus                   |
| 4     | Clear sky (cloudiness ≤ 10%)              |
| 5     | Stratocumulus, Stratus, and Altostratus   |
| 6     | Cumulonimbus and Nimbostratus             |
| 7     | Mixed cloud                               |

- **Source:** https://github.com/shuangliutjnu/TJNU-Ground-based-Cloud-Dataset
- **Download:** [Google Drive](https://drive.google.com/file/d/1dsgoEQLqR3YrOMBC_hOsVEUQC7HuV2fN/view)
- **License:** Custom GCD Agreement — non-commercial research use only; redistribution prohibited
- **Copyright:** Shuang Liu / Tianjin Normal University (TJNU)

**Citation (required):**

> S. Liu, L. Duan, Z. Zhang, X. Cao, and T. S. Durrani, "Ground-Based Remote Sensing
> Cloud Classification via Context Graph Attention Network," *IEEE Transactions on
> Geoscience and Remote Sensing*, vol. 60, pp. 1–11, 2022.
> DOI: [10.1109/TGRS.2021.3063255](https://doi.org/10.1109/TGRS.2021.3063255)

**Note:** TJNU images are grouped into broader categories than our 11-class CCSN scheme.
A model-assisted manual sorting process (`presort_tjnu.py` + `sort_review.html`) is used
to reclassify TJNU images into the granular CCSN classes before merging into the training
set.

---

## Algorithm & Model Architecture

### Ground-based Cloud Classification with Deep Learning

The classification approach and transfer learning methodology are inspired by this
repository.

- **Source:** https://github.com/marcosPlaza/Ground-based-Cloud-Classification-with-Deep-Learning
- **Author:** Marcos Plaza Gonzalez (Master's thesis, supervised by Jordi Vitrià and Gerard Gomez)
- **License:** MIT License (2022)

The project applies transfer learning with ImageNet-pretrained convolutional neural
networks to ground-based cloud images, using the CCSN dataset for fine-tuning.

---

### ResNet50V2 (Backbone Architecture)

The model uses ResNet50V2 as the feature extraction backbone, selected after comparing
MobileNetV2 (43.1% val accuracy), EfficientNetB0 (48.5%), and ResNet50V2 (50.7%) on the
CCSN dataset. ResNet50V2 uses pre-activation residual blocks (batch normalisation and ReLU
before convolution) which improve gradient flow during fine-tuning.

**Original ResNet paper:**

> He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep Residual Learning for Image
> Recognition. *Proceedings of the IEEE Conference on Computer Vision and Pattern
> Recognition (CVPR)*, 770–778.
> DOI: [10.1109/CVPR.2016.90](https://doi.org/10.1109/CVPR.2016.90)
> arXiv: [1512.03385](https://arxiv.org/abs/1512.03385)

**ResNet V2 paper (identity mappings — the variant used):**

> He, K., Zhang, X., Ren, S., & Sun, J. (2016). Identity Mappings in Deep Residual
> Networks. In *Computer Vision — ECCV 2016*, LNCS vol. 9908, pp. 630–645. Springer.
> DOI: [10.1007/978-3-319-46493-0_38](https://doi.org/10.1007/978-3-319-46493-0_38)
> arXiv: [1603.05027](https://arxiv.org/abs/1603.05027)

---

### TensorFlow / TensorFlow.js

Model training uses TensorFlow (Keras API). Browser-based inference uses TensorFlow.js
with the `layers-model` format converted via `tensorflowjs_converter`.

- **TensorFlow:** https://github.com/tensorflow/tensorflow
- **TensorFlow.js:** https://github.com/tensorflow/tfjs
- **License:** Apache License 2.0
- **Copyright:** The TensorFlow Authors / Google LLC

**Citation:**

> Abadi, M., Barham, P., Chen, J., Chen, Z., Davis, A., Dean, J., et al. (2016).
> TensorFlow: A System for Large-Scale Machine Learning. *12th USENIX Symposium on
> Operating Systems Design and Implementation (OSDI 16)*, pp. 265–283.
> arXiv: [1605.08695](https://arxiv.org/abs/1605.08695)

---

## Data Sources (Live)

### MetService NZ — Forecast Data

Today's text forecast for Christchurch, fetched from the MetService public data API.

- **Endpoint:** `https://www.metservice.com/publicData/localForecastchristchurch`
- **Terms:** http://about.metservice.com/api-terms-and-conditions
- **Data policy:** https://about.metservice.com/our-company/about-this-site/data-access-policy/
- **Copyright:** MetService Limited (New Zealand State-Owned Enterprise)
- **Contact:** dataenquiries@metservice.com

**Required attribution:**

> This data was provided by MetService Limited

**Note:** The API response includes a restriction notice. The CORS header
(`Access-Control-Allow-Origin: http://about.metservice.com`) blocks direct browser
requests; a CORS proxy is used as a workaround.

---

### Windy.com — Webcam Image

Live webcam image from Coastal Burwood, Christchurch, used for cloud classification input.

- **Webcam page:** https://www.windy.com/-Webcams/webcams/1672279274
- **Image URL:** `https://imgproxy.windy.com/_/full/plain/current/1672279274/original.jpg`
- **Terms:** https://account.windy.com/agreements/windy-api-webcams-terms-of-use
- **Operator:** Windyty, SE (Prague, Czech Republic)

**Required attribution:**

> Webcams provided by [windy.com](https://windy.com) —
> [add a webcam](https://www.windy.com/webcams/add)

**Restrictions:** No redistribution, no mass downloading, no stretching beyond original
size. Webcam operators retain rights to their content.

---

### corsproxy.io — CORS Proxy

Used as a fallback to bypass MetService CORS restrictions for browser-based API requests.

- **URL:** https://corsproxy.io
- **Terms:** https://corsproxy.io/tos/
- **License:** Proprietary service
- **Note:** Free tier is for development use only; production use requires a paid plan

---

## Training Configuration

| Parameter              | Value                              |
|------------------------|------------------------------------|
| Backbone               | ResNet50V2 (ImageNet pretrained)   |
| Input size             | 224 × 224 × 3                      |
| Preprocessing          | Scale to [-1, 1] (ResNet50V2)      |
| Training phases        | 1) Frozen base  2) Fine-tune top layers |
| Augmentation           | Rotation, flip, zoom, shift, shear |
| Label smoothing        | 0.1                                |
| LR schedule            | Cosine decay                       |
| Training platform      | Google Colab (T4 GPU, free tier)   |
| Output format          | TensorFlow.js layers-model         |
| Target classes (v2)    | 14: Ac, As, Cb, Cc, Ci, Clear, Cs, Ct, Cu, Fog, Ns, Rainbow, Sc, St |

---

## Project Files

| File                    | Purpose                                          |
|-------------------------|--------------------------------------------------|
| `index.html`            | Main website — forecast, webcam, cloud classifier |
| `train_colab.ipynb`     | Colab notebook for GPU training                  |
| `train_compare.py`      | Local multi-backbone comparison script           |
| `train_best.py`         | Extended training with best backbone             |
| `train_model.py`        | Initial single-backbone training script          |
| `presort_tjnu.py`       | Pre-sort TJNU images using trained model         |
| `sort_review.html`      | Manual review UI for TJNU image sorting          |
| `models/tfjs/`          | TF.js model weights for browser inference        |
| `models/class_names.json` | Class label list                               |
| `data/CCSN_v2/`         | CCSN training images (11 + 3 new class folders)  |
| `data/TJNU-GCD/`        | TJNU dataset (19,000 images, 7 classes)          |
