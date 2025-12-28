import requests
import json

base_url = "https://geodata.hawaii.gov/arcgis/rest/services/Terrestrial/MapServer/1/query"
params = {
    'where': '1=1',
    'outFields': '*',
    'f': 'geojson',
    'outSR': '4326',
    'resultOffset': 0,
    'resultRecordCount': 1000
}

all_features = []
scraping = True

while scraping:
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if 'features' in data:
        all_features.extend(data['features'])
        print(f"Collected {len(all_features)} features...")
    
    # Check if we should keep going
    if data.get('exceededTransferLimit'):
        params['resultOffset'] += 1000
    else:
        scraping = False

# Wrap in a FeatureCollection
geojson_output = {
    "type": "FeatureCollection",
    "features": all_features
}

with open("scraped_data.geojson", "w") as f:
    json.dump(geojson_output, f)