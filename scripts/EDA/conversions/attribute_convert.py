import geopandas as gpd
import pandas as pd

file_path = "/Users/benatkinson/iCloud/Obsidian Vault/Projects/ROD-ML/data/predictor/ROD_shp/ROD_by_year/2024_rod/2024ROD.shp"
test_df = gpd.read_file(file_path)
test_df = test_df.set_geometry('geometry')

#ordered_dict = {'Very Light (1-3%)', 'Light (4-10%)', 'Moderate (11-29%)', 'Severe (30-50%)','Very Severe (>50%)' 'Damage Point (100%)'}
test_df['PERCENT__1'] = pd.Categorical(test_df['PERCENT__1'], ['Very Light (1-3%)', 'Light (4-10%)', 'Moderate (11-29%)', 'Severe (30-50%)','Very Severe (>50%)' 'Damage Point (100%)'])

# print(test_df.T.head)
test_df = test_df.sort_values("PERCENT__1")
test_df.dropna()

if __name__ == '__main__':
    gdf = gpd.GeoDataFrame(test_df,crs="EPSG:4326")
    gdf.to_file("2024_Order_ROD.shp", driver='ESRI Shapefile')