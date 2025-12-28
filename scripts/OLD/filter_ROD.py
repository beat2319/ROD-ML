import rasterio
import rasterio.features
import geopandas as gpd
from shapely.geometry import shape
import numpy as np

# --- CONFIGURATION ---
rod_shp_path = "../data/response/ROD_shp/ROD_by_year/2016_rod/2016ROD.shp"
tree_tif_path = "../data/predictor/tree_cover/treeCover_2015/nlcd_tcc_hawaii_2015_v2021-4.tif"
output_shp_path = "../data/response/ROD_shp/2016ROD_Forested_Only.shp"

# Minimum tree cover % to consider "Forest" (e.g., 20%)
TREE_THRESHOLD = 20 

# 1. Load the ROD Data
rod_gdf = gpd.read_file(rod_shp_path)
print(f"Original ROD Polygons: {len(rod_gdf)}")

# 2. Vectorize the Tree Cover (The Heavy Lifting)
# We turn the Raster pixels > 20% into Polygons
with rasterio.open(tree_tif_path) as src:
    # Read data (optimize by using a window if file is huge, or read 1/10th resolution)
    # For NLCD, reading the whole island usually fits in RAM (approx 1-2GB)
    # If it crashes, we can downsample using `out_shape`
    tree_data = src.read(1)
    
    # Create binary mask (1 = Forest, 0 = Non-Forest)
    mask = (tree_data > TREE_THRESHOLD).astype(np.uint8)
    
    # Extract shapes (Polygonize)
    print("Vectorizing Forest Map (this may take a moment)...")
    results = (
        {'properties': {'raster_val': v}, 'geometry': s}
        for i, (s, v) in enumerate(
            rasterio.features.shapes(mask, mask=mask, transform=src.transform)
        )
    )
    
    # Convert to GeoPandas
    forest_geoms = list(results)
    forest_gdf = gpd.GeoDataFrame.from_features(forest_geoms, crs=src.crs)

# 3. Clean up Forest Polygons
# We only want the polygons where raster_val == 1
forest_gdf = forest_gdf[forest_gdf['raster_val'] == 1]

# 4. The Intersection (The "Filter")
# Ensure CRS matches
if rod_gdf.crs != forest_gdf.crs:
    rod_gdf = rod_gdf.to_crs(forest_gdf.crs)

print("Filtering ROD polygons by Forest Cover...")
# This keeps only the intersection: (ROD AND Forest)
filtered_rod = gpd.overlay(rod_gdf, forest_gdf, how='intersection')

# 5. Save and Finish
print(f"Filtered ROD Polygons: {len(filtered_rod)}")
filtered_rod.to_file(output_shp_path)
print("Done! Use this new shapefile in your patcher.")