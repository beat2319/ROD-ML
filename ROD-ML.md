# Rapid ‘Ōhi‘a Death ML Project
## Publishing
Due April 30th 2026, and deadline January 10th 2026 abstract
 - IEEE 
	 - [IGARRS](https://2026.ieeeigarss.org/important_dates.php)
		 - 400 -600 abstract (not published) :-(
		 - 4 page extended abstract :-)
		 - Ask prof and grad student
	 - LETTER
- Remote Sensing of Environment
	- Short Communication (7 pages)
- AIAA 
	- Student Conference 
## Core Architecture
**[[Convolutional Neural Network#Diagram|Convolutional Neural Network]]**
![[CNN.svg]]
- Specifically with [[Convolutional Neural Network#Pooling|Pooling]] and [[Convolutional Neural Network#Convolved Layer (Feature Map)|Feature Map]]
### Single Model Approach
- **will be using pre-trained weights**
	- Full U-net for [[Image Segmentation]] to keep resolution high
		 - ![[Pasted image 20251024203448.png]]
	- Resnet18 as CNN architecture
		- ![[Pasted image 20251024203704.png]]
	- ![[PNG image_2.png]]
### Two Model Approach (More Confident)
**will be using pre-trained weights**
- First a binary classification (is_affected) with UNet and resnet18 
- Then an ordinal regression (using grouped percentages) with UNet and resnet18 
- ![[IMG_81272E943973-1.jpeg]]
## Architecture Add Ons & Options
- CNN-LSTM
> [!PDF|note] [[Karimzadeha2025-Performanceand.pdf#page=3&selection=51,71,54,4&color=note|Karimzadeha2025-Performanceand, p.3]]
> > Architectures combining convolutional and recurrent layers, such as CNN-LSTM models [18], have shown improved accuracy by jointly modeling spatial features and temporal dynamics.
> 
> 
- RNN
> [!PDF|note] [[Karimzadeha2025-Performanceand.pdf#page=4&selection=228,0,231,68&color=note|Karimzadeha2025-Performanceand, p.4]]
> > Recurrent Neural Networks (RNNs) [32] and Long Short-term Memory networks (LSTMs) [6] belong to this group, and have been successfully adopted in geospatial applications for time-series forecasting, such forecasting the geographic spread of infectious diseases [12] or various remote sensing applications [33]
> 
> 
- Using Location Encoders
> [!PDF|note] [[Karimzadeha2025-Performanceand.pdf#page=7&selection=10,0,24,22&color=note|Karimzadeha2025-Performanceand, p.7]]
> > An alternative is to use pretrained location encoders to generate embeddings es for each location s and ingest those embeddings in the predictive task at hand (i.e., the downstream task). 
> 
> 
## Supporting Research 
- **Research Papers**
	- [[Pirotti2023-Sentinel-1Response]]
		- Both structural and moisture changes with similarity to ROD
	- [[Lin2021-InteroperabilityStudy]]
	- [[Xie2025-IntegratingSentinel-1]]
	- [[Karimzadeha2025-Performanceand]]
		- While advances in deep learning excel at leveraging spatial information, optimal ways of leveraging geographic location information remain under explored.
	- [[Wang2025-High-ResolutionEstimation]]
		- Despite their success, these models (gradient boosting and forrest models) follow a point-to-point estimation approach and do not fully leverage both spatial and temporal information, while using a Long Short-Term Memory (LSTM) network with Attention resulted in a 2.2% improvement in overall RMSE, and a 9.8% reduction in RMSE on high-concentration days.
- **In Class Notes**
	- [[Image Segmentation]]
		- Focus on U-Net
	- [[fpls-14-1139232-g015.jpg]]
		- visualization for studying canopy with ml 
	- [[Convolutional Neural Network]]
		- Deep dive into core architecture
## Data
#### Visualization
- ![[hakalua_community_map.pdf#page=1&rect=4,4,786,607|kakalua_community_map, p.1]]

| 1                 | 2                     | 3                     | 4                 | 5                  | 6                   |
| ----------------- | --------------------- | --------------------- | ----------------- | ------------------ | ------------------- |
| Very Light (1-3%) | Light         (4-10%) | Moderate     (11-29%) | Severe   (30-50%) | Very Severe (>50%) | Damage Point (100%) |
- ![[hakalau_ROD_map.pdf#page=1&rect=5,2,781,610|kakalau_ROD_map, p.1]]
### Scene Size
- We currently are limited to a scene size of 9 (2016 - 2024)
	- this is not great and we will have to depend on our data being quite accurate 
### Augmentation
- Due to our lack of scenes, but vast dataset, a great option would be to augment our data
	- such as cropping and horizontal/vertical mirroring
	- other data augmentation methods (resizing, *mirroring*, rotation, aspect, *cropping*, and color jitter)
### Dataset
#### Pairing
| Predictor | 2016 (July)          | 2017 (July)          | ...     | 2024 (July)          |
| --------- | -------------------- | -------------------- | ------- | -------------------- |
| **Response**   | **2016 (May - Oct)** | **2017 (May - Oct)** | **...** | **2024 (May - Oct)** |
#### [Predictor](https://www.arcgis.com/home/item.html?id=469e3fdccca846f094e3031fa57a6912)
- collection with [[ohia_results.py]]
- plotted with originally [[test_map.r]]
	- [[tmapOhia-death.png]]
- adapted and mapped out in ARCGIS PRO
	- [[hakalau_ROD_map.pdf]]
#### [Response](https://dataspace.copernicus.eu/explore-data)
- Layers OSM background as borders
- Sentinel-1 C-VV and C-VH backscatter values 
	- ![[2025-08-07-00_00_2025-09-07-23_59_Sentinel-1_IW_VV+VH_VH_-_decibel_gamma0.jpg]]
### Training 
- First, a binary classification U-Net method was employed to identify each sub-area as affected or unaffected. Then, a regression U-Net method was applied to determine the severity level only of the affected area.
- Maybe a pretuned model, that we tweak

### Folder Structure
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

| Vector   | Raster | Database    | Webservice |
| -------- | ------ | ----------- | ---------- |
| .shp     | .tif   | .gdb (esri) | wfs        |
| .geojson | .img   | .gpkg       | wms        |
| .kml     |        |             |            |

Use server connection in ARCGIS via url for db
[remote_sensing](https://earthexplorer.usgs.gov)
