import pandas as pd
import geopandas as  gpd
import numpy as np
import os
import sys


data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'

AI = gpd.read_file(data + 'Aggregation_index/data/fuelCategory_all_v2.geojson')
urb_file = gpd.read_file(data + 'Capes PC/Delimitacio_v1.shp')

AI_urb = AI.sjoin(urb_file, how='inner', predicate='intersects')

urb_file["H1"] = -1
urb_file["H2"] = -1
urb_file["H3"] = -1
urb_file["H4"] = -1
urb_file["H5"] = -1
urb_file["H6"] = -1
urb_file["H7"] = -1

for irow, row in urb_file.iterrows():
    tpi_sub = AI_urb[AI_urb["index_right"] == irow]
    for h in range(1, 8):
        urb_file.at[irow, f'H{h}'] = tpi_sub[tpi_sub["IFH"] == h]["Area"].sum()

# Calcula numerador i denominador
weights = np.arange(1, 8)  # array([1, 2, 3, 4, 5, 6, 7])
H_cols = [f"H{h}" for h in weights]

# Numerador: suma ponderada
urb_file["numerador"] = urb_file[H_cols].multiply(weights, axis=1).sum(axis=1)

# Denominador: suma total d’àrees
urb_file["denominador"] = urb_file[H_cols].sum(axis=1)

# Mitjana ponderada
urb_file["Hazard_mitja"] = urb_file["numerador"] / urb_file["denominador"]

urb_file["Hazard_cobertura"] =urb_file["Hazard_mitja"]*(urb_file["denominador"]/urb_file["Area"])

output_file= os.path.join(dataout, "URB_AI.shp")
urb_file.to_file(output_file)
print("urb_tpi saved")