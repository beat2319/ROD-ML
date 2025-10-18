## Rapid ‘Ōhi‘a Death ML Project
- Core architecture [[Convolutional Neural Network]]
	- Full UNet for segmentation with keep resolution high
	- Will use resnet18 as CNN architecture
### Publishing
Due April 30th 2026, and deadline January 10th 2026 abstract
 - IEEE 
	 - IGARRS
	 - LETTER
- Remote Sensing of Environment
	- Short Communication (7 pages)
- AIAA 
	- Student Conference 
### Supporting Research 
- [[Pirotti2023-Sentinel-1Response]]
	- Both structural and moisture changes with similarity to ROD
- [[Lin2021-InteroperabilityStudy]]
- [[Xie2025-IntegratingSentinel-1]]
- [[Image Segmentation]]
### Data
| Predictor | 2016 (July)          | 2017 (July)          | ...     | 2024 (July)          |
| --------- | -------------------- | -------------------- | ------- | -------------------- |
| **Raw**   | **2016 (May - Oct)** | **2017 (May - Oct)** | **...** | **2017 (May - Oct)** |


- [Predictor](https://cms.ctahr.hawaii.edu/rod/)
	- collection with [[ohia_results.py]]
	- plotted with originally [[test_map.r]]
	- ![[tmapOhia-death.png]]
- [Raw](https://dataspace.copernicus.eu/explore-data)
	- Layers OSM background as borders
	- Sentinel-1 C-VV and C-VH backscatter values 
	- ![[2025-08-07-00_00_2025-09-07-23_59_Sentinel-1_IW_VV+VH_VH_-_decibel_gamma0.jpg]]
	- 


### [Folder Structure](https://drive.google.com/drive/folders/1C0eY5JS29bLsW9nKfr7IHuCDhcU1VHEy?usp=drive_link)
```bash
├── documentation
├── Predictor_Map
│   ├── GpMessages
│   ├── ImportLog
│   ├── Index
│   │   └── Predictor_Map_index
│   │       ├── Connections
│   │       ├── Predictor_Map
│   │       └── Thumbnail
│   ├── Predictor_Map.gdb
│   └── RasterFunctionTemplates
│       └── Project1
├── SAR_data
├── scripts
└── training_data
    ├── coastline
    └── ROD_shp
        ├── ohia_shp
        └── rod_by_year
            ├── 2016_rod 
            ├── 2017_rod
            ├── 2018_rod
            ├── 2019_rod
            ├── 2020_rod
            ├── 2021_rod
            ├── 2022_rod
            ├── 2023_rod
            └── 2024_rod
```
