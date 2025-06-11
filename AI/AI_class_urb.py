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

# Manté només la geometria i la columna 'nom' per fer la unió espacial
AI_urb = AI.sjoin(urb_file[["NOM", "geometry", "Area"]], how='inner', predicate='intersects')

# Inicialitza les columnes H1-H7
for h in range(1, 8):
    urb_file[f"H{h}"] = 0.0


print(AI_urb.columns)

# Calcula la suma d'àrees per IFH per cada urbanització
for h in range(1, 8):
    summary = AI_urb[AI_urb["IFH"] == h].groupby("NOM_left")["Area"].sum()
    urb_file.loc[urb_file["NOM"].isin(summary.index), f"H{h}"] = urb_file["NOM"].map(summary).fillna(0)

# Calcula la mitjana ponderada H_mitja
weights = np.arange(1, 8)
H_cols = [f"H{h}" for h in weights]

urb_file["sum_Hi*i"] = urb_file[H_cols].multiply(weights, axis=1).sum(axis=1)
urb_file["Tot_A_poli"] = urb_file[H_cols].sum(axis=1)

# Evita divisió per 0
urb_file["H_mitja"] = urb_file["sum_Hi*i"] / urb_file["Tot_A_poli"]
urb_file["H_mitja"] = urb_file["H_mitja"].fillna(0)

# Hazard cobertura: mitjana ponderada ajustada a l'àrea de la urbanització
urb_file["Hazard_cobertura"] = urb_file["H_mitja"] * (urb_file["Tot_A_poli"] / urb_file["Area"])

# Desa el resultat
output_file = os.path.join(dataout, "URB_AI.shp")
urb_file.to_file(output_file)

print("Shapefile URB_AI.shp guardat correctament.")
