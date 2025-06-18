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

# Diccionari de reemplaçament per ICat
reemplacament = {
    1: 5,
    2: 4,
    3: 3,
    4: 2,
    5: 1
}

# Manté les columnes necessàries incloent IAI i ICat
AI_selceted = AI[["IFH", "geometry", "Area_veg", "NOM", "IAI", "ICat"]]

# Aplicar el canvi a ICat
AI_selceted['ICat'] = AI_selceted['ICat'].map(reemplacament)

# Unió espacial
AI_urb = AI_selceted.sjoin(urb_file[["NOM", "geometry", "Area_urb"]], how='inner', predicate='intersects')

# Càlculs ponderats per les tres variables
AI_urb["weighted_IFH"] = AI_urb["IFH"] * AI_urb["Area_veg"]
AI_urb["weighted_IAI"] = AI_urb["IAI"] * AI_urb["Area_veg"]
AI_urb["weighted_ICat"] = AI_urb["ICat"] * AI_urb["Area_veg"]

# Agregació per IFH
result_IFH = AI_urb.groupby('index_right').agg(
    weighted_avg_IFH=('weighted_IFH', 'sum'),
    total_veg_area=('Area_veg', 'sum')
)
result_IFH['weighted_avg_IFH'] = result_IFH['weighted_avg_IFH'] / result_IFH['total_veg_area']
result_IFH = result_IFH.reset_index()

# Agregació per IAI
result_IAI = AI_urb.groupby('index_right').agg(
    weighted_avg_IAI=('weighted_IAI', 'sum'),
    total_veg_area=('Area_veg', 'sum')
)
result_IAI['weighted_avg_IAI'] = result_IAI['weighted_avg_IAI'] / result_IAI['total_veg_area']
result_IAI = result_IAI.reset_index()

# Agregació per ICat
result_ICat = AI_urb.groupby('index_right').agg(
    weighted_avg_ICat=('weighted_ICat', 'sum'),
    total_veg_area=('Area_veg', 'sum')
)
result_ICat['weighted_avg_ICat'] = result_ICat['weighted_avg_ICat'] / result_ICat['total_veg_area']
result_ICat = result_ICat.reset_index()

# Fusiona tots els resultats
result = result_IFH.merge(result_IAI, on=['index_right', 'total_veg_area'], how='left')
result = result.merge(result_ICat, on=['index_right', 'total_veg_area'], how='left')

# Fusiona amb les dades urbanes
urb_with_avg = urb_file.merge(result, left_index=True, right_on='index_right', how='left')
urb_with_avg = urb_with_avg.drop(columns=['index_right'])

# Calcula els nous índexs
urb_with_avg['IFH_urb'] = (
    urb_with_avg['weighted_avg_IFH'] / 
    (urb_with_avg['total_veg_area'] / urb_with_avg['Area_urb'])
)

urb_with_avg['AI_urb'] = urb_with_avg['weighted_avg_IAI']

urb_with_avg['ICat_urb'] = urb_with_avg['weighted_avg_ICat'] 

# Desa el resultat
output_file = os.path.join(dataout, "urb_AI.shp")
urb_with_avg.to_file(output_file)

print("Shapefile URB_AI.shp guardat correctament.")