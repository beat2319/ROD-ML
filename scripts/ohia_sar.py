from sentinelhub import (
    SHConfig,
    SentinelHubCatalog,
    DataCollection,
    BBox,
    CRS
)
from sentinelhub.time_utils import parse_time
from datetime import datetime, timedelta
# No longer need json import for debugging
# import json

# --- Configuration ---
try:
    config = SHConfig()
    if not config.sh_client_id or not config.sh_client_secret:
        print("ERROR: Credentials not found. Run 'sentinelhub.config ...' first.")
        exit()
    if "dataspace.copernicus.eu" not in config.sh_base_url:
         print("ERROR: Configuration not set for CDSE. Run 'sentinelhub.config --sh_base_url ... --sh_token_url ...' first.")
         exit()
    print("Configuration loaded successfully.")
except Exception as e:
    print(f"Error loading configuration: {e}")
    exit()

# --- Define Search Parameters ---
ohia_bbox_coords = [-155.33501, 19.7667, -155.26428, 19.83131]
ohia_bbox = BBox(bbox=ohia_bbox_coords, crs=CRS.WGS84)
print(f"\nSearching within BBox: {ohia_bbox_coords}")

end_date = datetime.now()
start_date = end_date - timedelta(days=90)
time_interval_str = (
    start_date.strftime('%Y-%m-%d'),
    end_date.strftime('%Y-%m-%d')
)
print(f"Searching time range: {time_interval_str[0]} to {time_interval_str[1]}")

# --- Initialize Catalog and Check Collections ---
target_collection_s1 = "sentinel-1-grd"
try:
    catalog = SentinelHubCatalog(config=config)
    print("\nInitialization check passed.")
except Exception as e:
    print(f"\nAn error occurred initializing catalog: {e}")
    exit()

# --- Attempt Search for Sentinel-1 GRD ---
try:
    print(f"\nPerforming catalog search for '{target_collection_s1}'...")
    search_iterator_s1 = catalog.search(
        collection=target_collection_s1,
        bbox=ohia_bbox,
        time=time_interval_str,
    )
    results_s1 = list(search_iterator_s1)
    print(f"\nFound {len(results_s1)} scenes for '{target_collection_s1}'.")

    # --- Print Details of Found S1 Scenes using CORRECT keys ---
    if results_s1:
        print("\n--- Details of Found Sentinel-1 GRD Scenes: ---")
        for idx, item in enumerate(results_s1): # Loop through ALL found scenes
            scene_id = item['id']
            sensing_time = parse_time(item['properties']['datetime']).strftime('%Y-%m-%d %H:%M:%S')
            # Use the keys identified from the previous output
            orbit_dir = item['properties'].get('sat:orbit_state', 'N/A')
            relative_orbit = item['properties'].get('sat:relative_orbit', 'N/A')
            polarization_code = item['properties'].get('s1:polarization', 'N/A') # e.g., DV
            polarization_list = item['properties'].get('sar:polarizations', []) # e.g., ['VV', 'VH']


            print(f"{idx+1}. ID: {scene_id}")
            print(f"   Time: {sensing_time}")
            print(f"   Orbit Direction: {orbit_dir}")
            print(f"   Relative Orbit #: {relative_orbit}")
            print(f"   Polarization Code: {polarization_code}")
            print(f"   Polarizations Available: {polarization_list}")
            print("-" * 25)
    else:
        print("No scenes found for the specified criteria.")

except Exception as e:
    print(f"\nERROR occurred during '{target_collection_s1}' search: {e}")