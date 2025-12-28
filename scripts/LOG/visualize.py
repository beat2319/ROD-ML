import os
import sys

# Force the PROJ_LIB path to the Anaconda environment's path
conda_prefix = sys.prefix
os.environ['PROJ_LIB'] = os.path.join(conda_prefix, 'share', 'proj')

import geopandas as gpd
import matplotlib.pyplot as plt
import math
import pandas as pd
import rasterio
import rasterio.plot
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.windows import from_bounds
from shapely.geometry import box
import numpy as np

def analyze_month(geojson_path, canopy_tif_path, patch_px=256, res=10, buffer_m=2000):
    # 1. Load ROD data and project to our Master CRS
    gdf = gpd.read_file(geojson_path)
    gdf_utm = gdf.to_crs(epsg=32604)
    minx, miny, maxx, maxy = gdf_utm.total_bounds

    # 2. Grid Math (Snapped to 2560m intervals)
    patch_m = patch_px * res
    s_minx, s_miny = math.floor(minx / patch_m) * patch_m, math.floor(miny / patch_m) * patch_m
    s_maxx, s_maxy = math.ceil(maxx / patch_m) * patch_m, math.ceil(maxy / patch_m) * patch_m

    # 3. Generate Grid
    patches = [box(x, y, x + patch_m, y + patch_m) 
               for x in range(int(s_minx), int(s_maxx), patch_m)
               for y in range(int(s_miny), int(s_maxy), patch_m)]
    grid_gdf = gpd.GeoDataFrame({'geometry': patches}, crs=32604)

    # 4. Filter ROD and Healthy
    rod_patches = gpd.sjoin(grid_gdf, gdf_utm, how="inner", predicate="intersects").drop_duplicates(subset=['geometry']).copy()
    all_forest_patches = grid_gdf[~grid_gdf.index.isin(rod_patches.index)].copy()
    
    sample_size = min(len(rod_patches), len(all_forest_patches))
    healthy_samples = all_forest_patches.sample(n=sample_size)

    # 5. REPROJECTION & PLOTTING
    fig, ax = plt.subplots(figsize=(12, 10))

    with rasterio.open(canopy_tif_path) as src:
        # Define the window bounds in UTM 32604
        win_minx, win_miny = s_minx - buffer_m, s_miny - buffer_m
        win_maxx, win_maxy = s_maxx + buffer_m, s_maxy + buffer_m
        
        # Calculate transform for the reprojected window
        dst_crs = 'EPSG:32604'
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        
        # Clip the data and reproject only the necessary window to save RAM
        # We use a window from the original TIF bounds
        from rasterio.warp import transform_bounds
        orig_left, orig_bottom, orig_right, orig_top = transform_bounds(dst_crs, src.crs, win_minx, win_miny, win_maxx, maxy)
        window = src.window(orig_left, orig_bottom, orig_right, orig_top)
        
        # Read data
        data = src.read(1, window=window)
        src_transform = src.window_transform(window)
        
        # Create an empty array for the reprojected data
        # Downsample to 1024x1024 for MacBook Air performance
        dst_data = np.zeros((1024, 1024), np.float32)
        dst_transform, _, _ = calculate_default_transform(
            src.crs, dst_crs, window.width, window.height, 
            left=orig_left, bottom=orig_bottom, right=orig_right, top=orig_top,
            dst_width=1024, dst_height=1024
        )

        reproject(
            source=data,
            destination=dst_data,
            src_transform=src_transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.bilinear
        )

        # Plot the reprojected background
        rasterio.plot.show(dst_data, transform=dst_transform, ax=ax, cmap='YlGn', alpha=0.7)

    # 6. Plot Vector Overlays (Already in EPSG:32604)
    grid_gdf.boundary.plot(ax=ax, color='black', linewidth=0.3, alpha=0.3)
    rod_patches.boundary.plot(ax=ax, color='red', linewidth=2, label='ROD Patch')
    healthy_samples.boundary.plot(ax=ax, color='blue', linewidth=2, label='Healthy Patch')
    gdf_utm.plot(ax=ax, color='darkred', markersize=5, label='ROD Detection')

    ax.set_title(f"Diagnostic Map (All Projected to EPSG:32604)")
    ax.set_xlim(win_minx, win_maxx)
    ax.set_ylim(win_miny, win_maxy)
    plt.legend(loc='lower right')
    plt.show()

    return pd.concat([rod_patches, healthy_samples])

# --- EXECUTION ---
canopy_tif = "../../data/predictor/tree_cover/treeCover_2015/nlcd_tcc_hawaii_2015_v2021-4.tif"
geojson_file = "../../data/response/ROD_Monthly/2016/1_2016_ROD.geojson"
final = analyze_month(geojson_file, canopy_tif)