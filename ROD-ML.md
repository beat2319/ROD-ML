# Rapid ‘Ōhi‘a Death ML Project

## Project Status

- **Goal:** Detect ROD severity using segmentation with Sentinel-1 data
- **Current Blocker:** Waiting on data access (government shutdown)
- **Core Problem:** Small dataset scene size (9)
- **Solution:** Augmentation and Tiling
- **Next Step:** Finalize architecture, and finish configuring server

---

## Data

### Definition

- **Study Area:** 103,616,122.64 $m^2$
- **Pixel Resolution:** 10m x 10m
- **Patch Size:** 256px \* 256px
- **Samples:** ~16 patches per scene
- **Total Dataset (9 scenes):** ~144 unique samples

### Sources

| **[Response](https://www.arcgis.com/home/search.html?q=owner:%22bjtucker%22&restrict=false#content)** | 2016 (July)          | 2017 (July)          | ...     | 2024 (July)          |
| ----------------------------------------------------------------------------------------------------- | -------------------- | -------------------- | ------- | -------------------- |
| **[Predictor](https://dataspace.copernicus.eu/explore-data)**                                         | **2016 (May - Oct)** | **2017 (May - Oct)** | **...** | **2024 (May - Oct)** |

#### Response

- **Multi-class**
  - | 1                 | 2             | 3                 | 4               | 5                  | 6                   |
    | ----------------- | ------------- | ----------------- | --------------- | ------------------ | ------------------- |
    | Very Light (1-3%) | Light (4-10%) | Moderate (11-29%) | Severe (30-50%) | Very Severe (>50%) | Damage Point (100%) |
  - ![[hakalau_ROD_map.pdf#page=1&rect=5,2,781,610|kakalau_ROD_map, p.1]]
- **Binary**
  - ![[2016ROD_HWR.pdf#page=1&rect=3,150,612,656|2016ROD_HWR, p.1]]

#### Predictor

- Sentinel-1 C-VV and C-VH backscatter values
  - ![[2025-08-07-00_00_2025-09-07-23_59_Sentinel-1_IW_VV+VH_VH_-_decibel_gamma0.jpg]]
- Elevation and Rainfall

### Status & Approval

- Project Data Manager
  - [Brian Tucker](chrome://brian.tucker.researcher@hawaii.gov)
    - "The polygon data is fairly general and mostly represents a limited number of individual dead trees within a larger area.  There are also a number of factors regarding time and data collection accuracy that could be challenging for a project like this"
- Map Creator
  - [Robert D. Hauff](chrome://robert.d.hauff@hawaii.gov)
    - "data sharing ... the raw aerial survey data"

### Visualization

```leaflet
id: map
geojson: [[2024ROD.geojson]]
geojson: [[neatogeo_Hakalau Forest National Wildlife Refuge.geojson]]
geojsonColor: red
height: 500px
lat: 19.87
long: -155.34
minZoom: 10
maxZoom: 30
verbose: true
```

---

## Training Methodology

### Data Augmentation & Tiling

- **Strong Augmentation:**
  - Reprojection
    - convert prediction geojson and response to UTM coords
  - Radiometric Calibration
    - (1,0) is_rain
  - Geometric: Cropping, horizontal/vertical mirroring, rotation, resizing
  - Other: Using built-in SOT (Sub-pixel Offset Tracking)
  - Noise: SNR changing the noise
  - radio frequency interference
  - shadowing
  - fading
  - https://www.bellingcat.com/resources/2022/02/11/radar-interference-tracker-a-new-open-source-tool-to-locate-active-military-radar-systems/
- **Tiling:** using overlapping tiles to generate more samples

### Model Architecture

- **Approach:** We will be testing both a binary and multi-class segmentation
- **Pre-Trained Weights:** Leverage transfer learning with SAR-HUB, or Image-Net
  - 3/5 frozen, 2/5 unfrozen layer split for fine tuning
- **Backbone:** ResNet18
  - ![[Pasted image 20251024203704.png]]
- **Segmentation:** U-Net
  - ![[Pasted image 20251024203448.png]]

#### Model 1: Binary Segmentation

- **Goal:** Identify each pixel as either 'unaffected' ($0$) or 'affected' ($1$)
- **Model:** U-Net with pre-trained encoder (ResNet18)
- **Labels:** All 6 affected classes merged into a single affected class
- **Loss Function:** BCE + Dice Loss
  - Binary Cross Entropy for per pixel accuracy
  - Dice Loss for severe imbalance between "affected" and "unaffected"
  - **Alternative:** [Focal Loss](https://www.tensorflow.org/api_docs/python/tf/keras/losses/BinaryFocalCrossentropy) if class imbalance is still severe
- **Visualization:**
  - ![[IMG_6D946CCD2453-1.jpeg]]

#### Model 2: Multi-Class Segmentation

- **Goal:** Classify each pixel into one of seven classes
  - Unaffected ($0$), Very Light ($1$), Light ($2$), Moderate ($3$), Severe ($4$), Very Severe ($5$), or Damage Point ($6$)
- **Model:** U-Net with pre-trained encoder (ResNet18)
- **Labels:** The original multi class masks ($0-6$)
- **Loss Function:** CE + Dice Loss
  - Cross Entropy standard for multi class segmentation
  - Dice for severe class imbalance
- **Visualization:**
  - ![[IMG_045D7484B2E9-1.jpeg]]

### Hyperparameters & Validation

- **Hyperparameters**
  - **Batch Size:** 8 or 16 due to small dataset
  - **Optimizer:** AdamW
  - **Learning Rate:** 1e-4
  - **Epochs:** `200`
- **Validation**
  - 5-fold cross-validation for reliable performance metric

### Compute

- Local: RTX 5090 (32gb VRAM)
  - development
- Cloud: A100 (80gb VRAM)
  - 5-fold cross-validation
  - ![[Pasted image 20251109104310.png]]

---

## Publishing

**Due April 30th 2026, and deadline January 10th 2026 abstract**

- IEEE
  - [IGARRS](https://2026.ieeeigarss.org/important_dates.php)
    - https://2026.ieeeigarss.org/call_for_papers.php
    - 400 -600 abstract (not published) :-(
    - 4 page extended abstract :-)
    - Ask prof and grad student
  - LETTER
- Remote Sensing of Environment
  - Short Communication (7 pages)
- AIAA
  - Student Conference

---

## Folder Structure

```bash
├── data
│   ├── location
│   │   ├── coastline
│   │   └── hakalau_unicorporated community.kmz
│   ├── predictor
│   │   ├── mapping
│   │   └── ROD_shp
│   └── response
│       └── SAR_data
├── documentation
│   ├── Sentinel-1_IW_VV+VH_VH_-_decibel_gamma0.jpg
│   ├── fpls-14-1139232-g015.jpg
│   ├── hakalau_ROD_map.pdf
│   ├── kakalua_community_map.pdf
│   └── tmapOhia-death.png
├── ReadMe.md
├── ROD-ML.md
└── scripts
    ├── converter.py
    ├── ohia_results.py
    ├── ohia_sar.py
    ├── test_config.py
    └── test_map.r
```

---

## Appendix

## Sepidah

- Sepidahs' Project
  - 25million pixels in one scene
  - (600 scene)
  - 16 batch size
  - 768 x 768
- ROD project
  - Simple CNN, Unet, non deep unets with pretrianed ResNet-18
  - small patch size **128** or 256
  - Batch size 8
    -
  - high stride with more overlap between the patches
  - heavy dropout 0.6
  - weight decay
  - augmentation
    - geometry (rotation and scaling and flipping) at least 6 with high rate at least 80% for each
      - input and label
    - brightness and contrast around 50%
      - input
  - accurate labels and balanced
  - alpha earth embeddings as input features
  - purchase more collab if needed
- Pre-prossening
  - Masking and lots of reading on pre-processing
  - atmospheric
  - radiometric
  - train correction
  - reprojection
  - thermal noise reduction
  - if more accurate
    - speckle filtering
- Fight for accuracy

### Zhongying Wangs' Adjustment

- On scope, here’s a streamlined plan that keeps the intent but trims redundancy:
  - Image-level classifier (simple CNN) — optional baseline/filter. Keep this only if you’ll use it to (a) sanity-check labels and (b) cheaply filter obvious negatives before segmentation. Otherwise, we can skip straight to segmentation.
- U-Net segmentation
  - If “affected” is a single class vs. background, one binary U-Net is sufficient (BCE+Dice loss, pretrained encoder, strong augmentation). If you need sub-types (e.g., multiple categories of “affected”), use a multi-class U-Net (CE+Dice).
  - It would be worth trying [focal loss](https://nam10.safelinks.protection.outlook.com/?url=https%3A%2F%2Farxiv.org%2Fpdf%2F1708.02002.pdf&data=05%7C02%7CBenjamin.Atkinson%40colorado.edu%7C672db55c783e448124ee08de1c13b00c%7C3ded8b1b070d462982e4c0b019f46057%7C1%7C0%7C638979068038065295%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&sdata=%2BwEdC8pPdwECGQUWrAnsDJUoSxFTstKoz9V2oCiLKrU%3D&reserved=0 "https://arxiv.org/pdf/1708.02002.pdf") if there is a severe imbalance between positive and negative pairs. TensorFlow has this implementation:[TensorFlow BinaryFocalCrossentropy](https://www.tensorflow.org/api_docs/python/tf/keras/losses/BinaryFocalCrossentropy)

### Research Papers

- [[Pirotti2023-Sentinel-1Response]]
  - Both structural and moisture changes with similarity to ROD
- [[Lin2021-InteroperabilityStudy]]
- [[Xie2025-IntegratingSentinel-1]]
- [[Karimzadeha2025-Performanceand]]
  - While advances in deep learning excel at leveraging spatial information, optimal ways of leveraging geographic location information remain under explored.
- [[Wang2025-High-ResolutionEstimation]]
  - Despite their success, these models (gradient boosting and forrest models) follow a point-to-point estimation approach and do not fully leverage both spatial and temporal information, while using a Long Short-Term Memory (LSTM) network with Attention resulted in a 2.2% improvement in overall RMSE, and a 9.8% reduction in RMSE on high-concentration days.
- [[Perroy2021-SpatialPatterns]]
  - Fenced in areas for explaintion

### In Class Notes

- [[Image Segmentation]]
  - Focus on U-Net
- [[fpls-14-1139232-g015.jpg]]
  - visualization for studying canopy with ml
- [[Convolutional Neural Network]]
  - Deep dive into core architecture

### Labs

- [[Lab 6 - CNN]]
- [[Lab 7 - Image Segmentation]]

### Other Architecture

- CNN-LSTM
  > [!PDF|note] [[Karimzadeha2025-Performanceand.pdf#page=3&selection=51,71,54,4&color=note|Karimzadeha2025-Performanceand, p.3]]
  >
  > > Architectures combining convolutional and recurrent layers, such as CNN-LSTM models [18], have shown improved accuracy by jointly modeling spatial features and temporal dynamics.
- RNN
  > [!PDF|note] [[Karimzadeha2025-Performanceand.pdf#page=4&selection=228,0,231,68&color=note|Karimzadeha2025-Performanceand, p.4]]
  >
  > > Recurrent Neural Networks (RNNs) [32] and Long Short-term Memory networks (LSTMs) [6] belong to this group, and have been successfully adopted in geospatial applications for time-series forecasting, such forecasting the geographic spread of infectious diseases [12] or various remote sensing applications [33]
- Using Location Encoders
  > [!PDF|note] [[Karimzadeha2025-Performanceand.pdf#page=7&selection=10,0,24,22&color=note|Karimzadeha2025-Performanceand, p.7]]
  >
  > > An alternative is to use pretrained location encoders to generate embeddings es for each location s and ingest those embeddings in the predictive task at hand (i.e., the downstream task).

## Pre Trained Models

https://olmoearth.allenai.org/?utm_source=ai2-olmoearth&utm_medium=referral&utm_campaign=olmoearth

## Gap

- what can we do to improve the paper, what can we improve what is our job?
  - How can we fill that gap, explain that gap!!!
  - What methods did they use.
  - 3.7 Impact Factor
  - Read some papers
- Reviewer wants to see that gap, how to improve the related works
  - Easily publish (alpha earth embeddings is the novelty)
    - no foundational embedding
    - this is the first study that uses "..."
  - What is the gap and explain novelty and goal
    - how is what we do different?
      - build out a story
- Read at least 20 papers on the topic and see what is done
  - Is there any paper that has used foundational embeddings
  - What deep learning has been used
  - what loss has been used
