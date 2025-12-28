import os
import math
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import box

def get_grid_gdf(bounds, patch_m, crs):
    """Generates a regular grid of boxes within given bounds."""
    minx, miny, maxx, maxy = bounds
    x_coords = np.arange(math.floor(minx/patch_m)*patch_m, math.ceil(maxx/patch_m)*patch_m, patch_m)
    y_coords = np.arange(math.floor(miny/patch_m)*patch_m, math.ceil(maxy/patch_m)*patch_m, patch_m)
    
    grid_boxes = [box(x, y, x + patch_m, y + patch_m) for x in x_coords for y in y_coords]
    return gpd.GeoDataFrame({'geometry': grid_boxes}, crs=crs)

def validate_canopy(geom, src, threshold=75):
    """Checks if the patch area meets the tree cover percentage."""
    window = from_bounds(*geom.bounds, transform=src.transform)
    # Read the data for this specific window
    data = src.read(1, window=window)
    if data.size == 0:
        return False
    
    # Calculate percentage of pixels above threshold (excluding nodata)
    valid_pixels = data[data != src.nodata]
    if valid_pixels.size == 0:
        return False
    
    coverage = np.mean(valid_pixels >= threshold) * 100
    return coverage >= threshold

def build_yearly_master(rod_month_dir, rod_year_path, tif_path, coastline_path, patch_px=128, res=10):
    patch_m = patch_px * res
    year_label = os.path.basename(rod_month_dir.rstrip('/'))
    all_year_patches = []

    # 1. Load Environmental Masks
    print("Loading Coastline and Canopy Reference...")
    with rasterio.open(tif_path) as src:
        tif_crs = src.crs
        # Load coastline and dissolve to a single geometry for fast intersection checks
        coastline = gpd.read_file(coastline_path).to_crs(tif_crs).union_all()
        
        # 2. Pre-process Yearly ROD for Negative Pool
        print(f"Loading Yearly ROD Reference: {rod_year_path}")
        year_gdf = gpd.read_file(rod_year_path).to_crs(tif_crs)
        
        # Generate grid over the entire year's ROD extent
        y_grid_gdf = get_grid_gdf(year_gdf.total_bounds, patch_m, tif_crs)
        
        # Spatial Join: Identify boxes that contain ANY ROD detections this year
        year_rod_indices = gpd.sjoin(y_grid_gdf, year_gdf, how="inner", predicate="intersects").index.unique()

        # 3. Monthly Processing
        for file in sorted(os.listdir(rod_month_dir)):
            if not file.endswith(".geojson"): continue
            month = file.split('_')[0]
            print(f"\n--- Processing Month: {month} ---")
            
            month_gdf = gpd.read_file(os.path.join(rod_month_dir, file)).to_crs(tif_crs)
            if month_gdf.empty: continue

            # A. POSITIVES: Generate grid over monthly detections
            m_grid_gdf = get_grid_gdf(month_gdf.total_bounds, patch_m, tif_crs)
            pos_candidates = gpd.sjoin(m_grid_gdf, month_gdf, how="inner", predicate="intersects").drop_duplicates(subset=['geometry'])
            
            # Filter Positives by Coastline (Hard Filter)
            pos_on_land = pos_candidates[pos_candidates.geometry.intersects(coastline)].copy()
            pos_on_land['label'] = 1
            pos_on_land['month'] = month

            # B. NEGATIVES: Sample from the healthy pool
            neg_pool = y_grid_gdf[~y_grid_gdf.index.isin(year_rod_indices)].copy()
            
            # Filter Negatives by Coastline first to save on expensive Raster I/O
            neg_on_land = neg_pool[neg_pool.geometry.intersects(coastline)].sample(frac=1)
            
            valid_healthy = []
            target_count = len(pos_on_land)
            
            print(f"Validating canopy for {target_count} negative samples...")
            for _, row in neg_on_land.iterrows():
                if validate_canopy(row.geometry, src, threshold=75):
                    valid_healthy.append(row.geometry)
                if len(valid_healthy) >= target_count:
                    break
            
            if valid_healthy:
                negatives = gpd.GeoDataFrame({'geometry': valid_healthy, 'label': 0}, crs=tif_crs)
                negatives['month'] = month
                all_year_patches.extend([pos_on_land[['geometry', 'label', 'month']], negatives])
                print(f"Final Count: {len(pos_on_land)} POS, {len(negatives)} NEG")

    # 4. Final Export
    if all_year_patches:
        final_gdf = pd.concat(all_year_patches).reset_index(drop=True)
        final_gdf['year'] = year_label
        output_name = f"Master_Dataset_{year_label}.geojson"
        # Exporting in UTM Zone 4N (EPSG:32604) for consistency
        final_gdf.to_crs(epsg=32604).to_file(output_name, driver='GeoJSON')
        print(f"\nSuccess! Total patches generated for {year_label}: {len(final_gdf)}")

if __name__ == "__main__":
    # Ensure these paths are correct for your local environment
    MONTH_DIR = "../../data/response/ROD_Monthly/2024"
    YEAR_FILE = "../../data/response/ROD_Year/2024_ROD.geojson"
    TIF_MAP = "../../data/predictor/tree_cover/treeCover_2021/nlcd_tcc_hawaii_2021_v2021-4.tif"
    COASTLINE = "../../data/location/coastline/Coastline.shp" 
    
    build_yearly_master(MONTH_DIR, YEAR_FILE, TIF_MAP, COASTLINE)