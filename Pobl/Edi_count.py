import geopandas as gpd
import pandas as pd
import os

# 1. Carregar les capes
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = data

# Carregar urbanitzacions
URB = gpd.read_file(data + 'Capes PC/Delimitacio_v1.shp', 
                   columns=['NOM', 'MUN_INE', 'CODI', 'TIPUS', 'MUNICIPI', 'COMARCA', 'mapid', 'OBSERVACAIO', 'Area', 'geometry'])

# Carregar edificis i filtrar
edi = gpd.read_file(data + 'fuxed_construccions_p.gpkg')
edi = edi[edi['tipus'] == 'edi'].copy()

# Calcular àrea dels edificis (important fer-ho abans del spatial join)
edi['area_edifici'] = edi.geometry.area
edi = edi[edi['area_edifici'] > 45]  # Filtrar per àrea >45m²

# Assegurar mateix CRS
if URB.crs != edi.crs:
    edi = edi.to_crs(URB.crs)

# Spatial join
joined = gpd.sjoin(URB, edi, how='left', predicate='intersects')
# Agrupar per polígon URB i comptar edificis
count_edificis = joined.groupby('NOM')['area_edifici'].count().reset_index()
count_edificis = count_edificis.rename(columns={'area_edifici': 'num_edificis'})

# Fusionar el recompte amb la capa original URB
URB_with_count = pd.merge(URB, count_edificis, on='NOM', how='left')

# Omplir NaN amb 0 (per urbanitzacions sense edificis)
URB_with_count['num_edificis'] = URB_with_count['num_edificis'].fillna(0).astype(int)

# Si vols guardar el resultat:
output_path = os.path.join(dataout, 'URB_edificis_count.shp')
URB_with_count.to_file(output_path)

print(f"Nombre d'edificis per urbanització calculat i guardat a {output_path}")
print(URB_with_count[['NOM', 'num_edificis']].head())