import geopandas as gpd
import pandas as pd

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

# Agregar dades
stats = joined.groupby('NOM').agg(
    num_edificis=('index_right', 'count'),
    area_total_edificis=('area_edifici', 'sum')
).reset_index()

# Fusionar amb original
result = URB.merge(stats, on='NOM', how='left')

# Omplir NaN
result['num_edificis'] = result['num_edificis'].fillna(0)


# Afegir nova columna: divisió de l'àrea total entre 14.566
result['Pobl'] = result['num_edificis'] * 2.6

# Resultat
print(result[['NOM', 'num_edificis', 'Pobl']])

# Guardar resultat
result.to_file(dataout + 'URB_pob.shp')