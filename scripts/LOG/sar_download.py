import os
import math
import geopandas as gpd
import pandas as pd
import rasterio
from shapely.geometry import box

def get_canopy_tif(rod_year, tif_base):
    """
    Implements the 1-year lag logic for canopy maps.
    Uses 2021 as the ceiling for 2022+ data.
    """
    rod_year_int = int(rod_year)
    target_year = 2021 if rod_year_int >= 2022 else rod_year_int - 1
    
    year_dir = f"treeCover_{target_year}"
    dir_path = os.path.join(tif_base, year_dir)
    
    # Fallback to the current year if the lag directory is missing
    if not os.path.exists(dir_path):
        dir_path = os.path.join(tif_base, f"treeCover_{rod_year_int}")
        
    if os.path.exists(dir_path):
        for f in os.listdir(dir_path):
            if f.endswith(".tif") and "aux" not in f:
                return os.path.join(dir_path, f), target_year
    return None, None

def build_master_list(rod_base, tif_base, patch_px=256, res=10):
    all_patches = []
    patch_m = patch_px * res  # 2560m

    # Filter for directories in the ROD base path
    years = sorted([d for d in os.listdir(rod_base) if os.path.isdir(os.path.join(rod_base, d))])

    for year in years:
        year_path = os.path.join(rod_base, year)
        tif_path, canopy_year = get_canopy_tif(year, tif_base)
        
        if not tif_path:
            print(f"Skipping {year}: No canopy TIF found.")
            continue
        
        with rasterio.open(tif_path) as src:
            tif_crs = src.crs
            nodata = src.nodata
            
            # 1. Aggregation: Load all monthly/split GeoJSONs for this year into one GDF
            # This ensures healthy patches don't conflict with ROD in other files.
            files = [f for f in os.listdir(year_path) if f.endswith(".geojson")]
            if not files:
                continue

            print(f"--- Processing {year} (Using {canopy_year} Canopy) ---")
            year_rod_gdf = pd.concat([
                gpd.read_file(os.path.join(year_path, f)).to_crs(tif_crs) 
                for f in files
            ]).reset_index(drop=True)

            if year_rod_gdf.empty:
                continue

            # 2. Generate snapped grid for the entire year's ROD bounding box
            minx, miny, maxx, maxy = year_rod_gdf.total_bounds
            s_minx = math.floor(minx / patch_m) * patch_m
            s_miny = math.floor(miny / patch_m) * patch_m
            s_maxx = math.ceil(maxx / patch_m) * patch_m
            s_maxy = math.ceil(maxy / patch_m) * patch_m

            patches = [box(x, y, x + patch_m, y + patch_m) 
                       for x in range(int(s_minx), int(s_maxx), patch_m)
                       for y in range(int(s_miny), int(s_maxy), patch_m)]
            grid_gdf = gpd.GeoDataFrame({'geometry': patches}, crs=tif_crs)

            # 3. Extract Positive ROD Patches (Label 1)
            rod_patches = gpd.sjoin(grid_gdf, year_rod_gdf, how="inner", predicate="intersects")
            rod_patches = rod_patches.drop_duplicates(subset=['geometry']).copy()
            rod_patches['label'] = 1

            # 4. Extract Healthy Baseline Patches (Label 0)
            # Filter pool against the AGGREGATED year data to prevent false negatives
            neg_pool = grid_gdf[~grid_gdf.index.isin(rod_patches.index)].copy()
            valid_healthy = []
            shuffled = neg_pool.sample(frac=1)
            
            # Target 1:1 balance per year
            target_count = len(rod_patches)
            
            for _, row in shuffled.iterrows():
                cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
                try:
                    # Sample centroid directly in TIF CRS
                    val = next(src.sample([(cx, cy)]))[0]
                    # Must not be ocean (NoData) and must be dense Ohia (>=75%)
                    if val != nodata and val >= 75: 
                        valid_healthy.append(row.geometry)
                except:
                    continue
                
                if len(valid_healthy) >= target_count:
                    break
            
            # 5. Compile the year batch
            year_batches = []
            if not rod_patches.empty:
                year_batches.append(rod_patches[['geometry', 'label']])
            if valid_healthy:
                h_gdf = gpd.GeoDataFrame({'geometry': valid_healthy, 'label': 0}, crs=tif_crs)
                year_batches.append(h_gdf)
            
            if year_batches:
                final_year = pd.concat(year_batches)
                final_year['rod_year'] = year
                final_year['canopy_year'] = canopy_year
                all_patches.append(final_year)
                print(f"Created {len(rod_patches)} positive and {len(valid_healthy)} negative patches.")

    # Final Export
    if all_patches:
        final_gdf = pd.concat(all_patches).reset_index(drop=True)
        # Export to UTM Zone 4N (EPSG:32604) for standard Hawaii analysis
        output_name = "ROD_Final_Master_List.geojson"
        final_gdf.to_crs(epsg=32604).to_file(output_name, driver='GeoJSON')
        print(f"\nSuccess! Saved {len(final_gdf)} total patches to {output_name}.")
    else:
        print("Error: No patches were generated.")

if __name__ == "__main__":
    # Update these paths based on your gpu server structure
    ROD_DATA_DIR = "../../data/response/ROD_Monthly/"
    CANOPY_DIR = "../../data/predictor/tree_cover/"
    
    build_master_list(
        rod_base=ROD_DATA_DIR, 
        tif_base=CANOPY_DIR, 
        patch_px=256, 
        res=10
    )