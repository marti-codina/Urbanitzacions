import pandas as pd
import geopandas as gpd
import numpy as np
import os

data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = data  # pots deixar-ho així si la sortida va al mateix lloc

# Carrega les capes
AI = gpd.read_file(data + 'Aggregation_index/data/fuelCategory_all_v2.geojson')
urb_file = gpd.read_file(data + 'Capes PC/Delimitacio_v1.shp')

# Assegura't que la columna "nom" existeix
assert "NOM" in urb_file.columns, "No existeix la columna 'nom' a urb_file"

AI['Area_veg'] = AI.geometry.area
urb_file = urb_file.rename(columns={'Area':'Area_urb'})

#print(AI.columns)
#print(urb_file.columns)

# Manté només la geometria i la columna 'nom' per fer la unió espacial
AI_selceted = AI[["IFH", "geometry", "Area_veg", "NOM"]]
AI_urb = AI.sjoin(urb_file[["NOM", "geometry", "Area_urb"]], how='inner', predicate='intersects')
AI_urb["weighted_IFH"] = AI_urb["IFH"]*AI_urb["Area_veg"]

#print(AI_urb.columns)

# Alternative grouping that preserves the index_right
result = AI_urb.groupby('index_right').agg(
    weighted_avg_IFH=('weighted_IFH', 'sum'),
    total_AI_area=('Area_veg', 'sum')
)
result['weighted_avg_IFH'] = result['weighted_avg_IFH'] / result['total_AI_area']
result = result.reset_index()

urb_with_avg = urb_file.merge(result, left_index=True, right_on='index_right', how='left')
urb_with_avg = urb_with_avg.drop(columns=['index_right'])


urb_with_avg['new_index'] = (
    urb_with_avg['weighted_avg_IFH'] / 
    (urb_with_avg['total_AI_area'] / urb_with_avg['Area_urb'])
)

# Desa el resultat
output_file = os.path.join(dataout, "urb_AI_v0.shp")
urb_with_avg.to_file(output_file)

print("Shapefile URB_AI.shp guardat correctament.")