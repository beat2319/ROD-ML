import rasterio
from rasterio.features import shapes
import geopandas as gpd

# 1. Load the Raster
# We need to capture the CRS from the source file first
with rasterio.open("../data/location/treeCover_2017/hawaii_2017.tif") as src:
    image = src.read(1)
    mask = image != 0 
    transform = src.transform
    source_crs = src.crs  # Capture the original CRS

    # 2. Polygonize
    results = (
        {'properties': {'raster_val': v}, 'geometry': s}
        for i, (s, v) in enumerate(
            shapes(image, mask=mask, transform=transform)
        )
    )

    # 3. Create GeoDataFrame
    # CRITICAL: Tell GeoPandas what CRS the data is currently in (from the TIF)
    gdf = gpd.GeoDataFrame.from_features(list(results), crs=source_crs)

# 4. Reproject and Save
# Convert to EPSG:4326 (The standard Lat/Lon for GeoJSON)
gdf = gdf.to_crs("EPSG:4326")

gdf.to_file("../data/location/treeCover_2017/hawaii_2017.geojson", driver='GeoJSON')