import geopandas as gpd
import pandas as pd


file_path = r"C:\Users\beat2319\Downloads\ohia\training_data\ohia_shp\ohia_hawaii.shp"
test_df = gpd.read_file(file_path)
test_df = test_df.set_geometry('geometry')
test_df = test_df.set_geometry('geometry')
input_year = "2024"

def convert_df(df,year):
    filtered_df = df.loc[df['YEAR'] == year]
    return filtered_df

if __name__ == '__main__':
    gdf = gpd.GeoDataFrame(convert_df(test_df,input_year),crs="EPSG:4326")
    gdf.to_file(f"{input_year}ROD.shp", driver='ESRI Shapefile')