import geopandas as gpd
from zipfile import ZipFile
import os

kmz_file = "Hakalau Forest National Wildlife Refuge.kmz"
# kml_file = "temp_kml_file.kml"

# Extract KML from KMZ
with ZipFile(kmz_file, 'r') as z:
    for name in z.namelist():
        if name.endswith('.kml'):
            z.extract(name, '.')
            kml_file = name
            break

# Read KML
gdf = gpd.read_file(kml_file)

# Get appropriate UTM zone automatically
gdf_utm = gdf.to_crs(gdf.estimate_utm_crs())

# Save output as GeoJSON in UTM
gdf_utm.to_file("output_utm.geojson", driver="GeoJSON")

print("Converted to UTM:", gdf_utm.crs)
