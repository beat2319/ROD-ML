import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# OBJECTID, CREATED_DATE, FEATURE_USER_ID, REGION_ID, HOST_CODE, HOST, DCA_CODE, DCA
# DAMAGE_TYPE_CODE, DAMAGE_TYPE, PERCENT_AFFECTED_CODE, PERCENT_AFFECTED, OBSERVATION_COUNT
# COLLECTION_MODE, AREA_TYPE, PHOTOS, PHOTOLINK, ACRES, NUMBER_OF_TREES_CODE, 
# NUMBER_OF_TREES_COUNT_RANGE, BUFF_DIST, ISLAND, PERCENT_AFFECTED_FACTOR, IMPACT_ACRES
# YEAR, Shape__Area, Shape__Length, geometry

Year = 2024
Month = 12

def convert_datetime(df_in):
    df = df_in.copy()

    df['DATE_TIME'] = pd.to_datetime(df.CREATED_DATE, unit='ms')

    df['MONTH'] = df['DATE_TIME'].dt.month

    return df

def main():
    path = "../../data/response/mapping/fha.geojson"
    
    gdf = gpd.read_file(path)
    new_gdf = gdf.pipe(convert_datetime) 

    # filtered_df = new_gdf[(new_gdf['DATE_TIME'].dt.year == Year) & (new_gdf['DATE_TIME'].dt.month == Month)]
    filtered_df = new_gdf[(new_gdf['DATE_TIME'].dt.year == Year)]

    print(filtered_df.head(1700).transpose())

    filtered_df.to_file(f"../../data/response/ROD_Monthly/{Year}_ROD.geojson", driver="GeoJSON")

if __name__ == '__main__':
    main()

