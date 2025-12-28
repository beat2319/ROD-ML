import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom
from shapely.geometry import box
from shapely.validation import make_valid
import os

# --- 1. CONFIGURATION ---
BASE_GEOJSON_PATH = "../data/response/mapping/fha.geojson"
TARGET_YEAR = 2016
TREE_TIF_PATH = f"../data/location/treeCover_{TARGET_YEAR}/hawaii_{TARGET_YEAR}.tif"
OUTPUT_PATH = f"training_data_{TARGET_YEAR}.geojson"

PROJECT_CRS = "EPSG:32605"

# --- COLUMN MAPPING ---
METADATA_COLS = {
    "severity_score": "PERCENT_AFFECTED_FACTOR", 
    "diagnosis": "DCA",                           
    "damage_type": "DAMAGE_TYPE",                 
    "acres": "ACRES",
    "impact_years": "IMPACT_YEARS"
}

COL_YEAR = "YEAR"

# PARAMETERS
GAP_SIZE = 200      
CONTEXT_SIZE = 2000 
PATCH_SIZE = 256    
RES = 10            

def create_year_zones(base_path, target_year):
    print(f"1. Loading Base Data & Filtering for {target_year}...")
    gdf = gpd.read_file(base_path)
    if gdf.crs.to_string() != PROJECT_CRS:
        gdf = gdf.to_crs(PROJECT_CRS)

    gdf['geometry'] = gdf['geometry'].apply(make_valid)
    gdf = gdf[~gdf.is_empty]

    # Filter: Active disease up to this year
    gdf[COL_YEAR] = gdf[COL_YEAR].astype(int)
    active_rod = gdf[gdf[COL_YEAR] <= target_year].copy()
    
    print(f"   Found {len(active_rod)} cumulative infection sites.")

    # A. POSITIVES
    positives = active_rod.copy()
    positives['class_label'] = 1
    positives['zone_type'] = 'core'

    # B. NEGATIVES
    all_disease_mask = active_rod.geometry.buffer(GAP_SIZE)
    outer_rings = active_rod.geometry.buffer(GAP_SIZE + CONTEXT_SIZE)
    negatives_geom = outer_rings.difference(all_disease_mask)
    
    negatives = gpd.GeoDataFrame(geometry=negatives_geom, crs=PROJECT_CRS)
    negatives['class_label'] = 0
    negatives['zone_type'] = 'context_ring'

    return pd.concat([positives, negatives], ignore_index=True)

def generate_tiles(sampling_map, tif_path, max_overlap=0.20):
    print("2. Generating Tiles & Attaching Metadata...")
    
    # --- OPTIMIZATION: Prioritize Data ---
    # Sort so we process the most severe/largest areas FIRST.
    # If a severe tile overlaps a minor one, the severe one gets created, 
    # and the minor one gets skipped later by the overlap check.
    col_name = METADATA_COLS['severity_score']
    sampling_map[col_name] = pd.to_numeric(sampling_map[col_name], errors='coerce').fillna(0)

    if 'severity_score' in sampling_map.columns:
        sampling_map = sampling_map.sort_values('severity_score', ascending=False)
    
    _ = sampling_map.sindex 
    
    tile_size_m = PATCH_SIZE * RES
    half_tile = tile_size_m / 2
    tiles = []
    
    # Track geometries of tiles we have effectively "saved"
    # Format: list of shapely Polygons
    saved_tile_geoms = []

    with rasterio.open(tif_path) as src:
        tif_crs = src.crs
        
        for idx, row in sampling_map.iterrows():
            # 1. Candidate Generation
            if row['zone_type'] == 'core':
                c = row.geometry.centroid
                candidates = [box(c.x - half_tile, c.y - half_tile, c.x + half_tile, c.y + half_tile)]
            else:
                # Context rings (negatives) are already grid-based (0% overlap usually)
                b = row.geometry.bounds
                x_coords = np.arange(b[0], b[2], tile_size_m)
                y_coords = np.arange(b[1], b[3], tile_size_m)
                candidates = [box(x, y, x + tile_size_m, y + tile_size_m) for x in x_coords for y in y_coords]

            for tile_box in candidates:
                # --- A. SPATIAL DEDUPLICATION (The Fix) ---
                # Check this candidate against all previously saved tiles
                is_duplicate = False
                
                # Simple optimization: Only check last 500 tiles (locality) 
                # or check all if dataset is small (<5000). 
                # For strictness, we check all.
                tile_area = tile_box.area
                
                for existing_geom in saved_tile_geoms:
                    # Quick bounds check to avoid expensive intersection
                    if not tile_box.intersects(existing_geom):
                        continue
                        
                    inter_area = tile_box.intersection(existing_geom).area
                    overlap_ratio = inter_area / tile_area
                    
                    if overlap_ratio > max_overlap:
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    continue

                # --- B. Standard Validity Checks ---
                if not row.geometry.intersects(tile_box): continue
                inter_area = row.geometry.intersection(tile_box).area
                
                keep = False
                if row['class_label'] == 1 and inter_area > 0: keep = True
                elif row['class_label'] == 0 and inter_area > (0.3 * tile_box.area): keep = True
                if not keep: continue

                # try:
                geom_tif = transform_geom(sampling_map.crs, tif_crs, tile_box.__geo_interface__)
                out_img, _ = mask(src, [geom_tif], crop=True, filled=False)
                
                # PROBLEM WAS HERE:
                # if out_img[0].size == 0: continue
                # valid_pixels = out_img[0][out_img[0] > 0].size
                # if valid_pixels == 0: continue 

                # --- FIX ---
                # 1. Check if image is empty (edge of map)
                if out_img[0].size == 0: continue
                
                # 2. Count tree pixels
                valid_pixels = out_img[0][out_img[0] > 0].size
                
                # 3. Calculate Ratio
                tree_ratio = valid_pixels / out_img[0].size
                
                # 4. SAFETY VALVE: If it is a KNOWN DISEASE SITE, keep it 
                # even if the tree cover map is empty (might be dead trees).
                if row['class_label'] == 1:
                    pass # Keep going!
                elif valid_pixels == 0: 
                    continue
                
                if row['class_label'] == 1 or tree_ratio > 0.10:
                    
                    # Calculate Severity (Using the weighted method from before)
                    tile_record = {
                        'geometry': tile_box,
                        'class_label': row['class_label'],
                        'image_year': TARGET_YEAR,
                        'source_id': idx
                    }
                    
                    # --- CORRECTED METADATA AGGREGATION ---
                    if row['class_label'] == 1:
                        # 1. Find ALL disease polygons touching this tile
                        possible_matches_index = list(sampling_map.sindex.intersection(tile_box.bounds))
                        possible_matches = sampling_map.iloc[possible_matches_index]
                        
                        # Filter to exact intersection & strictly positive class
                        precise_matches = possible_matches[
                            (possible_matches.intersects(tile_box)) & 
                            (possible_matches['class_label'] == 1)
                        ].copy()

                        # 2. Calculate "Visual Severity"
                        # Formula: (Sum of (Score * Intersection_Area)) / Total_Tree_Area_In_Tile
                        
                        if not precise_matches.empty:
                            precise_matches['inter_area'] = precise_matches.intersection(tile_box).area
                            
                            # Calculate total tree area in meters squared
                            total_tree_area_m2 = valid_pixels * (RES * RES)
                            
                            if total_tree_area_m2 == 0:
                                total_tree_area_m2 = tile_box.area
                            # Sum of (Severity * Area)
                            severity_mass = (precise_matches[METADATA_COLS['severity_score']] * precise_matches['inter_area']).sum()
                            
                            # Normalized Severity (0-100 scale spread over tree cover)
                            # Cap at 100 just in case of minor projection alignment errors
                            final_severity = min(100, severity_mass / total_tree_area_m2)
                            tile_record['severity_score'] = round(final_severity, 2)
                            
                            # For Categorical fields, pick the dominant one by area
                            dominant = precise_matches.sort_values('inter_area', ascending=False).iloc[0]
                            tile_record['diagnosis'] = dominant.get(METADATA_COLS['diagnosis'], "Unknown")
                            tile_record['damage_type'] = dominant.get(METADATA_COLS['damage_type'], "Unknown")
                            
                            # Stats
                            tile_record['acres'] = precise_matches['inter_area'].sum() / 4046.86 # Convert m2 to acres
                            tile_record['impact_years'] = precise_matches[METADATA_COLS['impact_years']].max()
                        else:
                            # Fallback (should be rare)
                            tile_record['severity_score'] = 0
                            tile_record['diagnosis'] = "Healthy"
                            tile_record['damage_type'] = "None"
                            tile_record['acres'] = 0
                            tile_record['impact_years'] = 0

                    else:
                        # Healthy / Background Logic
                        tile_record['severity_score'] = 0
                        tile_record['diagnosis'] = "Healthy"
                        tile_record['damage_type'] = "None"
                        tile_record['acres'] = 0
                        tile_record['impact_years'] = 0

                    tiles.append(tile_record)
                    saved_tile_geoms.append(tile_box) 

                # except Exception:
                #     continue

    return gpd.GeoDataFrame(tiles, crs=PROJECT_CRS)

# --- EXECUTION ---
if __name__ == "__main__":
    zones = create_year_zones(BASE_GEOJSON_PATH, TARGET_YEAR)
    final_gdf = generate_tiles(zones, TREE_TIF_PATH)
    
    # Balance
    rod = final_gdf[final_gdf['class_label']==1]
    healthy = final_gdf[final_gdf['class_label']==0]
    
    print(f"Generated {len(rod)} positive tiles and {len(healthy)} healthy tiles.")

    if len(rod) > 0:
        target_healthy = len(rod) * 2
        if len(healthy) > target_healthy:
            healthy = healthy.sample(n=target_healthy, random_state=42)
        final_gdf = pd.concat([rod, healthy])

    # Save
    final_gdf = final_gdf.to_crs("EPSG:4326")
    final_gdf.to_file(OUTPUT_PATH, driver="GeoJSON")
    print(f"Done. Saved {len(final_gdf)} tiles.")
    print("Columns:", final_gdf.columns.tolist())