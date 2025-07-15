import pandas as pd
import geopandas as gpd
import numpy as np
import os

data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Urb_July/FUEL/'
dataout = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Urb_July/'  # pots deixar-ho així si la sortida va al mateix lloc

# Carrega les capes
fuel = gpd.read_file(data + 'Fuel_all.geojson')
urb_file = gpd.read_file('C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/RAW_URB_J_25/CRS_URB_J_25.shp')

# Assegura't que la columna "nom" existeix
assert "ID" in urb_file.columns, "No existeix la columna 'nom' a urb_file"

fuel['Area_veg'] = fuel.geometry.area
urb_file = urb_file.rename(columns={'Area':'Area_urb'})



# Manté les columnes necessàries incloent IAI i ICat
fuel_selceted = fuel[[ "geometry", "Area_veg", "ID", "ICat"]]


# Unió espacial
fuel_urb = fuel_selceted.sjoin(urb_file[["ID", "geometry", "Shape_Area"]], how='inner', predicate='intersects')

# Càlculs ponderats per les tres variables
fuel_urb["weighted_ICat"] = fuel_urb["ICat"] * fuel_urb["Area_veg"]



# Agregació per ICat
result_ICat = fuel_urb.groupby('index_right').agg(
    ICat_urb=('weighted_ICat', 'sum'),
    total_veg_area=('Area_veg', 'sum')
)
result_ICat['ICat_urb'] = (result_ICat['ICat_urb'] / result_ICat['total_veg_area']).round(0)
result_ICat = result_ICat.reset_index()


# Fusiona amb les dades urbanes
urb_with_avg = urb_file.merge(result_ICat, left_index=True, right_on='index_right', how='left')
urb_with_avg = urb_with_avg.drop(columns=['index_right'])

output_file = os.path.join(dataout, "urb_FCat.shp")
urb_with_avg.to_file(output_file)




print("Shapefile URB_FCat.shp guardat correctament.")


'''
tot_IFH_max = urb_with_avg['IFH_rel'].max()
tot_IFH_min = urb_with_avg['IFH_rel'].min()

if tot_IFH_max == tot_IFH_min:
    urb_with_avg['IFH_rel'] = 0.0
else:
    urb_with_avg['IFH_norm'] = (urb_with_avg['IFH_rel'] - tot_IFH_min) / (tot_IFH_max - tot_IFH_min)

# Classificació de IFH_norm
urb_with_avg['IFH_class'] = 1  # Valor per defecte (baix)
urb_with_avg.loc[(urb_with_avg['IFH_norm'] >= 0.33) & (urb_with_avg['IFH_norm'] < 0.66), 'IFH_class'] = 2  # Mig
urb_with_avg.loc[urb_with_avg['IFH_norm'] >= 0.66, 'IFH_class'] = 3  # Alt


# Desa el resultat
output_file = os.path.join(dataout, "urb_AI.shp")
urb_with_avg.to_file(output_file)
'''