import pandas as pd
import geopandas as gpd
import numpy as np
import os

data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = data  # pots deixar-ho així si la sortida va al mateix lloc

# Carrega les capes
ai = gpd.read_file(data + 'AI_URB.shp')
veg = gpd.read_file(data + 'urb_FCat.shp')


# Manté les columnes necessàries incloent IAI i ICat
AI_selcet = ai[[ "geometry", "Area", "NOM", "AI", "AI_cat"]]
veg_select = veg[["geometry", "total_veg_", "NOM", "ICat_urb"]]

# Fer el merge de les dues capes
merged = pd.merge(AI_selcet, veg_select, on="NOM", how="left")

merged["veg_%"] = (merged["total_veg_"] / merged["Area"])

# Calcular Fuel_H segons la fórmula [(total_veg_/Area)*(AI+ICat_urb)].round(0)
merged["Fuel_H"] = ( merged["veg_%"] * (merged["AI_cat"] + merged["ICat_urb"])).round(0)

# Convertir a enters
merged["ICat_urb"] = merged["ICat_urb"].astype(int)
merged["Fuel_H"] = merged["Fuel_H"].astype(int)

# Seleccionar només les columnes necessàries per al nou shapefile
FH_URB = merged[["geometry_x", "NOM", "Area", "AI", "AI_cat", "veg_%", "ICat_urb", "Fuel_H"]]

# Renombrar la columna de geometria perquè sigui consistent
FH_URB = FH_URB.rename(columns={"geometry_x": "geometry"})

# Convertir el DataFrame a GeoDataFrame (assegurant-nos que la geometria és vàlida)
FH_URB_gdf = gpd.GeoDataFrame(FH_URB, geometry="geometry")

# Guardar el nou shapefile
output_path = os.path.join(dataout, "FH_URB.shp")
FH_URB_gdf.to_file(output_path)

print(f"Fitxer {output_path} creat amb èxit!")