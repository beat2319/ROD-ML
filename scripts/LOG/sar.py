import os
import calendar
import numpy as np
import geopandas as gpd
import pystac_client
import planetary_computer as pc
import rasterio
from rasterio import warp
from rasterio.enums import Resampling
from tqdm import tqdm
from scipy.ndimage import gaussian_filter # Added for speckle filtering

def calculate_rvi(vv, vh):
    """Calculates Radar Vegetation Index for Dual-Pol SAR."""
    # Ensure linear power values are clipped to avoid negative artifacts or zero division
    vv = np.clip(vv, 1e-5, None)
    vh = np.clip(vh, 1e-5, None)
    rvi = (4 * vh) / (vv + vh)
    return np.clip(rvi, 0, 1)

def download_rtc_to_ssd(geojson_path, ssd_output_path):
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=pc.sign_inplace,
    )

    gdf = gpd.read_file(geojson_path)
    target_crs = gdf.crs 
    
    print(f"Starting Monthly Median SAR Collection (Speckle-Filtered) for {len(gdf)} patches...")

    for idx, row in tqdm(gdf.iterrows(), total=len(gdf), desc="Processing Patches"):
        month_str = str(row['month']).zfill(2)
        year = str(row['year'])
        label = int(row['label'])
        
        patch_id = f"{year}_{month_str}_{idx}"
        npy_output = os.path.join(ssd_output_path, f"{patch_id}_L{label}.npy")
        tif_output = os.path.join(ssd_output_path, f"{patch_id}_L{label}.tif")

        if os.path.exists(npy_output):
            continue

        last_day = calendar.monthrange(int(year), int(month_str))[1]
        date_range = f"{year}-{month_str}-01T00:00:00Z/{year}-{month_str}-{last_day}T23:59:59Z"
        
        geom_4326 = gdf.iloc[[idx]].to_crs(epsg=4326).geometry.iloc[0].__geo_interface__
        bounds_utm = row.geometry.bounds

        try:
            search = catalog.search(
                filter_lang="cql2-json",
                filter={
                    "op": "and", "args": [
                        {"op": "s_intersects", "args": [{"property": "geometry"}, geom_4326]},
                        {"op": "anyinteracts", "args": [{"property": "datetime"}, date_range]},
                        {"op": "=", "args": [{"property": "collection"}, "sentinel-1-rtc"]}
                    ]
                }
            )
            
            items = list(search.get_items())
            if not items: continue

            month_vv_stack, month_vh_stack = [], []

            for item in items:
                with rasterio.open(item.assets["vv"].href) as src_vv, \
                     rasterio.open(item.assets["vh"].href) as src_vh:
                    
                    l, b, r, t = warp.transform_bounds(target_crs, src_vv.crs, *bounds_utm)
                    win = src_vv.window(l, b, r, t)
                    
                    vv_data = src_vv.read(1, window=win, boundless=True, out_shape=(128, 128), resampling=Resampling.bilinear)
                    vh_data = src_vh.read(1, window=win, boundless=True, out_shape=(128, 128), resampling=Resampling.bilinear)
                    
                    month_vv_stack.append(vv_data)
                    month_vh_stack.append(vh_data)

            if not month_vv_stack: continue

            # --- PRE-PROCESSING BLOCK ---
            
            # 1. Calculate Median (Temporal Denoising)
            median_vv = np.median(np.array(month_vv_stack), axis=0)
            median_vh = np.median(np.array(month_vh_stack), axis=0)
            
            # 2. Apply Speckle Filter (Spatial Denoising)
            # Applying sigma=0.8 on linear data BEFORE RVI or dB conversion
            smooth_vv = gaussian_filter(median_vv, sigma=0.8)
            smooth_vh = gaussian_filter(median_vh, sigma=0.8)

            # 3. Calculate RVI from smoothed data
            rvi = calculate_rvi(smooth_vv, smooth_vh)
            
            # 4. Convert to Decibels (dB) for U-Net Input
            vv_db = 10 * np.log10(np.clip(smooth_vv, 1e-5, None))
            vh_db = 10 * np.log10(np.clip(smooth_vh, 1e-5, None))

            # 5. Save NPY
            final_stack = np.stack([vv_db, vh_db, rvi]).astype(np.float32)
            np.save(npy_output, final_stack)

            # 6. Save TIF for QGIS Validation (Every 100th)
            if idx % 100 == 0:
                transform = rasterio.transform.from_bounds(*bounds_utm, 128, 128)
                with rasterio.open(
                    tif_output, 'w',
                    driver='GTiff',
                    height=128, width=128,
                    count=3,
                    dtype='float32',
                    crs=target_crs,
                    transform=transform
                ) as dst:
                    dst.write(vv_db, 1) 
                    dst.write(vh_db, 2) 
                    dst.write(rvi, 3)   

        except Exception as e:
            print(f"Error at index {idx}: {e}")

if __name__ == "__main__":
    # Point this to your 2024 directory to re-collect with the new filter
    SSD_PATH = "../../data/predictor/rtc/2024"
    GEOJSON = "Master_Dataset_2024.geojson"
    
    if not os.path.exists(SSD_PATH):
        os.makedirs(SSD_PATH, exist_ok=True)
        
    download_rtc_to_ssd(GEOJSON, SSD_PATH)