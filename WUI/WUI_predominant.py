import geopandas as gpd

# Carregar les capes
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
URB = gpd.read_file(data + 'RAW_URB_J_25/RAW_URB_J_25.shp')
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

# 3. Trobar per cada urbanització (NOM) el DN amb més àrea
# Primer agrupem per NOM i DN, sumant les àrees
dn_area = intersections.groupby(['NOM', 'DN'])['area_int'].sum().reset_index()

# Ara per cada NOM, trobem el DN amb màxima àrea
dn_dominant = dn_area.loc[dn_area.groupby('NOM')['area_int'].idxmax()]

# 4. Fusionar resultats amb la capa original URB
URB_final = URB.merge(dn_dominant[['NOM', 'DN']], on='NOM', how='left')
URB_final = URB_final.rename(columns={'DN': 'DN_dominant'})

# Mostrar resultats
print(URB_final[['NOM', 'DN_dominant']].head())

# Guardar resultats
URB_final.to_file(data + 'Urb_July/WUI_July_pred.shp')