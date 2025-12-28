## Convert to WGS84 for GeoJSON
- first we import the coastline shp and convert to geojson for proper mapping when using api
- The we can set this geojson as the bounding box using STAC_API `intersects`
- using VH mean, VV stddev, and VH/VV ratio