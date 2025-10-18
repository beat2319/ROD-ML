from sentinelhub import SHConfig, SentinelHubCatalog

print("Attempting to load default configuration...")
try:
    # Load configuration from the default profile
    config = SHConfig()

    # Check if the Client ID was loaded correctly
    print(f"Loaded Client ID: {config.sh_client_id}")

    # Check if the crucial CDSE URLs are set
    print(f"Loaded Base URL: {config.sh_base_url}")
    print(f"Loaded Token URL: {config.sh_token_url}")

    if not config.sh_client_id or not config.sh_client_secret:
         print("\nERROR: Client ID or Secret not found in config!")
         print("Please run 'sentinelhub.config --sh_client_id YOUR_ID --sh_client_secret YOUR_SECRET ...' again.")
    elif "dataspace.copernicus.eu" not in config.sh_base_url:
         print("\nERROR: sh_base_url does not seem to be set for CDSE!")
         print("Please run 'sentinelhub.config --sh_base_url https://sh.dataspace.copernicus.eu ...' again.")
    else:
        print("\nConfiguration seems loaded correctly. Attempting authentication test...")
        # Try a simple authenticated request: listing available data collections
        catalog = SentinelHubCatalog(config=config)
        collections = catalog.get_collections()

        if collections:
            print("\nSUCCESS! Authentication worked.")
            print("Available collections include:")
            # Print first 5 collection IDs
            for collection in collections[:5]:
                print(f"- {collection['id']}")
            print("...")
        else:
            print("\nAuthentication might have worked, but no collections listed?")

except Exception as e:
    print(f"\nAn error occurred: {e}")
    print("Authentication or API call failed. Check your credentials and configuration.")