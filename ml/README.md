# KrishiVeda — Machine Learning

```
ml/
  datasets/      download scripts (data itself is git-ignored)
  training/      training scripts
  models/        trained artefacts (git-ignored): disease_cnn.pt, crop_recommender.joblib
  evaluation/    metrics reports (JSON) and training logs
```

Inference code lives in the backend (`backend/app/services/`) so the API has no dependency on this
folder except the model files. The CNN architecture + preprocessing are defined once in
`backend/app/services/disease_model_arch.py` and imported by the training script.

## 1. Plant disease detection (CNN)

| Item | Value |
|------|-------|
| Dataset | PlantVillage, "without augmentation" release — Mendeley Data doi:10.17632/tywbtsjrjv.1 (Pandian & Gopal), original images Hughes & Salathé (arXiv:1511.08060) |
| Licence | CC0 1.0 (as listed on the Mendeley record) |
| Subset used | up to 250 random images per class (seed 42) → 9,652 images, 39 classes |
| Split | stratified 70 / 15 / 15 → 6,718 train · 1,467 validation · 1,467 test |
| Model | MobileNetV3-Large, ImageNet pre-trained (torchvision), new 39-way linear head |
| Training | 1 epoch head-only (backbone frozen), then full fine-tuning with OneCycle LR (AdamW, label smoothing 0.1), augmentation: random resized crop, flips, rotation ±20°, colour jitter |
| Input | 224×224 RGB, resize short side to 256 then centre crop, ImageNet mean/std |

### Supported crops and classes (38 + "no leaf")

| Crop | Classes |
|------|---------|
| Apple | Apple scab, Black rot, Cedar apple rust, Healthy |
| Blueberry | Healthy |
| Cherry | Powdery mildew, Healthy |
| Maize (Corn) | Gray leaf spot, Common rust, Northern leaf blight, Healthy |
| Grape | Black rot, Esca (black measles), Leaf blight, Healthy |
| Orange | Citrus greening (Huanglongbing) |
| Peach | Bacterial spot, Healthy |
| Bell pepper | Bacterial spot, Healthy |
| Potato | Early blight, Late blight, Healthy |
| Raspberry, Soybean | Healthy |
| Squash | Powdery mildew |
| Strawberry | Leaf scorch, Healthy |
| Tomato | Bacterial spot, Early blight, Late blight, Leaf mould, Septoria leaf spot, Spider mites, Target spot, Mosaic virus, Yellow leaf curl virus, Healthy |
| — | Background without leaves (used to report "no leaf found") |

### Results (held-out test set, 1,467 images, evaluated with the API's own preprocessing)

| Metric | Value |
|--------|-------|
| Test accuracy | **98.23 %** |
| Test macro-F1 | **98.21 %** |
| Best validation accuracy | 98.36 % (after fine-tune epoch 3) |
| Confidence ≥ 60 % (shown as a diagnosis) | 93.0 % of images, **99.12 % accurate** |
| Confidence < 60 % (shown as "not sure") | 7.0 % of images |
| Weakest classes (F1) | Tomato late blight 0.88, Maize gray leaf spot 0.88, Maize northern leaf blight 0.88, Tomato early blight 0.93 |

Training history: head epoch val 88.4 % → fine-tune 92.8 % → 97.4 % → 98.4 %; about 54 min on a laptop CPU.
Full details (per-class scores, confusion matrix) are in `evaluation/disease_model_report.json`.

### Step 2 — fine-tuning on real-field photos (deployed model)

| Item | Value |
|------|-------|
| Field dataset | PlantDoc (Singh et al., CoDS-COMAD 2020), **CC BY 4.0**, 2,342 train / 236 test photos, 27 of our classes |
| Script | `ml/datasets/fetch_plantdoc.py`, `ml/training/finetune_field.py`, `ml/evaluation/evaluate_disease.py` |
| Training | starts from the lab model; PlantVillage train + 85 % of PlantDoc train (×3 oversampled), stronger augmentation, 4 epochs, AdamW + cosine LR; best epoch chosen by mean of lab and field validation accuracy (~95 min on CPU) |

| Test set | Lab-only model | **Lab + field model (deployed)** |
|----------|---------------:|---------------------------------:|
| Lab photos — PlantVillage test (1,467) | 98.23 % | **98.64 %** |
| Real-field photos — PlantDoc test (236) | 29.24 % | **63.56 %** (macro-F1 63.2 %) |
| Field: correct crop identified | 48.7 % | **80.9 %** |
| Field: correct answer in top 3 | 46.6 % | **89.4 %** |
| Field: accuracy when confidence ≥ 70 % | 37.5 % (10 % of photos) | **82.1 %** (50 % of photos) |

Because field photos are harder, the "not sure" threshold was raised from 60 % to **70 %**: half of
field photos get a confident answer (82 % correct) and the rest are flagged for a better photo or an
expert. Weakest field classes: tomato bacterial spot, maize gray leaf spot, tomato mosaic virus,
potato early/late blight. The lab-only model is kept as `ml/models/disease_cnn_lab.pt`.
Report: `evaluation/disease_field_report.json`; baseline: `evaluation/field_eval_lab_model.json`.

The PlantDoc test set is small (236 images, 4–12 per class), so field numbers have a margin of
roughly ±6 %.

### Limitations (read before presenting results)

* Lab accuracy (98.6 %) is much higher than real-field accuracy (63.6 %). Quote both, and treat the
  field number as the realistic one for farmers' phone photos.
* The dataset contains several photos of the same leaf; a random split can put near-duplicates in
  both train and test sets, inflating the score.
* Important Indian crops (wheat, rice, cotton, sugarcane, chilli, mustard …) are **not** covered.
  An image of an unsupported crop will still be mapped to one of the 39 classes — hence the
  confidence threshold and the "not sure" status.
* Only 250 images per class were used to keep CPU training practical; training on the full
  54k-image dataset or field datasets (e.g. PlantDoc) should improve robustness.

## 2. Crop recommendation

| Item | Value |
|------|-------|
| Dataset | Crop Recommendation Dataset, Atharva Ingle (Kaggle), **Apache 2.0** |
| Size | 2,200 rows, 22 crops (100 each), features N, P, K, temperature, humidity, pH, rainfall |
| Model | RandomForestClassifier (300 trees), scikit-learn |
| Evaluation | stratified 20 % hold-out: **accuracy 99.32 %, macro-F1 99.32 %**; 5-fold CV on train: 99.38 % ± 0.55 % |
| Explanation | per-crop 10th–90th percentile ranges from the training data, compared with the farmer's inputs |

Limitation: the dataset was built by *augmenting* Indian rainfall, climate and fertiliser data
(per its description), so the near-perfect score shows the classes are easy to separate in this
dataset — not that recommendations are validated on real farms. Units of N/P/K and the rainfall
period are not precisely documented by the dataset author.

## Re-training

```powershell
.venv\Scripts\python ml\datasets\fetch_crop_dataset.py
.venv\Scripts\python ml\training\train_crop_model.py
.venv\Scripts\python ml\datasets\fetch_plantvillage_subset.py --per-class 250
.venv\Scripts\python ml\training\train_disease_cnn.py --head-epochs 1 --finetune-epochs 3
# Field fine-tuning (writes a candidate; copy it over disease_cnn.pt after checking the report)
.venv\Scripts\python ml\datasets\fetch_plantdoc.py
.venv\Scripts\python ml\training\finetune_field.py --epochs 4
copy ml\models\disease_cnn.pt ml\models\disease_cnn_lab.pt
copy ml\models\disease_cnn_field.pt ml\models\disease_cnn.pt
```
