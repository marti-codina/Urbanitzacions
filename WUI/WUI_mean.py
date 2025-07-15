import geopandas as gpd

# Carregar les capes
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
URB = gpd.read_file(data + 'Peri-Urban polygons/FIRE-SCENE_Peri-Urban-polygons_2025_July.shp')
WUI = gpd.read_file(data + 'Vect_WUI_Cat.shp')  # Assegura't que té el camp 'DN'

# Verificar sistemes de coordenades
if URB.crs != WUI.crs:
    WUI = WUI.to_crs(URB.crs)

# 1. Crear interseccions entre URB i WUI
intersections = gpd.overlay(
    URB[['NOM', 'geometry']],
    WUI[['DN', 'geometry']],
    how='intersection',
    keep_geom_type=True
)

# 2. Calcular àrea de cada intersecció
intersections['area_int'] = intersections.geometry.area

# 3. Calcular producte DN*àrea
intersections['dn_area'] = intersections['DN'] * intersections['area_int']

# 4. Agregar per urbanització (NOM)
resultats = intersections.groupby('NOM').agg(
    area_total=('area_int', 'sum'),
    suma_dn_ponderat=('dn_area', 'sum')
).reset_index()

# 5. Calcular DN mitjà ponderat
resultats['DN_mitja'] = (resultats['suma_dn_ponderat'] / resultats['area_total']).round()
resultats["DN_mitja"] = resultats["DN_mitja"].astype(int)

# 6. Fusionar resultats amb la capa original URB
URB_final = URB.merge(resultats[['NOM', 'DN_mitja']], on='NOM', how='left')

# Mostrar resultats
print(URB_final[['NOM', 'DN_mitja']].head())

# Guardar resultats
URB_final.to_file(data + 'Urb_July/WUI_July.shp')