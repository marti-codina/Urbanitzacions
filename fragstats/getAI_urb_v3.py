import os
import rasterio
import chardet
import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd
from difflib import get_close_matches  # Per a matching de noms aproximat

# Configuració de paths
input_rasters = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Geotiffs_urb_pilot/rasters_URB"
class_file = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Geotiffs_urb_pilot/URB_AI_results.class"
original_shp = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Capes PC/Delimitacio_v1.shp"
output_shp = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/quadrats_AI.shp"

# 1. Funció per netejar noms
def clean_name(name):
    return (str(name).lower()
            .replace('_5m', '').replace('.tif', '')
            .replace('_', ' ').replace('-', ' ')
            .strip())

# 2. Lectura i processament del fitxer .class
try:
    # Detecció d'encoding
    def detect_encoding(file_path):
        with open(file_path, 'rb') as f:
            return chardet.detect(f.read())['encoding']
    
    encoding = detect_encoding(class_file)
    print(f"\n[INFO] Encoding detectat: {encoding}")
    
    # Lectura del fitxer
    df = pd.read_csv(class_file, sep=r',\s*', engine='python', encoding=encoding)
    
    # Neteja de dades
    df.columns = df.columns.str.strip()
    df['nom_fitxer'] = df['LID'].str.strip().apply(os.path.basename)
    df['nom_net'] = df['nom_fitxer'].apply(clean_name)
    df['AI'] = pd.to_numeric(df['AI'].str.strip() if pd.api.types.is_string_dtype(df['AI']) else df['AI'], 
                            errors='coerce').fillna(0)
    
    print("\n[DEBUG] Mostra de dades del .class:")
    print(df[['nom_fitxer', 'nom_net', 'AI']].head())

except Exception as e:
    print(f"\n[ERROR] Processament del fitxer .class: {e}")
    exit()

# 3. Crear diccionari d'AI amb noms netejats
ai_dict = {clean_name(row['nom_fitxer']): row['AI'] for _, row in df.iterrows()}
print(f"\n[STATUS] S'han processat {len(ai_dict)} entrades del .class")

# 4. Processament dels rasters
print("\n[STATUS] Creant shapefile temporal a partir de rasters...")
dades_temp = []

for filename in os.listdir(input_rasters):
    if filename.lower().endswith('.tif'):
        try:
            nom_net = clean_name(filename)
            # Matching aproximat per si hi ha petites diferències
            match = get_close_matches(nom_net, ai_dict.keys(), n=1, cutoff=0.8)
            ai = ai_dict[match[0]] if match else 0.0
            
            with rasterio.open(os.path.join(input_rasters, filename)) as src:
                bounds = src.bounds
                geometry = Polygon([
                    (bounds.left, bounds.bottom),
                    (bounds.left, bounds.top),
                    (bounds.right, bounds.top),
                    (bounds.right, bounds.bottom)
                ])
                
                dades_temp.append({
                    'nom_original': filename,
                    'nom_net': nom_net,
                    'AI': ai,
                    'geometry': geometry
                })
        except Exception as e:
            print(f"[WARNING] Error processant {filename}: {e}")

if not dades_temp:
    print("\n[ERROR] No s'han trobat rasters vàlids")
    exit()

gdf_temp = gpd.GeoDataFrame(dades_temp, geometry='geometry', crs="EPSG:25831")

# 5. Processament del shapefile original
print("\n[STATUS] Llegint shapefile original...")
try:
    gdf_original = gpd.read_file(original_shp)
    gdf_original['nom_net'] = gdf_original['NOM'].apply(clean_name)
    
    if gdf_original.crs != gdf_temp.crs:
        gdf_original = gdf_original.to_crs(gdf_temp.crs)
    
    print(f"Shapefile original té {len(gdf_original)} entrades")
except Exception as e:
    print(f"\n[ERROR] Error llegint shapefile original: {e}")
    exit()

# 6. Unió espacial millorada
print("\n[STATUS] Realitzant unió espacial...")
try:
    # Unió espacial
    gdf_joined = gpd.sjoin(gdf_original, gdf_temp[['AI', 'geometry']], how='left', predicate='intersects')
    
    # Neteja de resultats
    gdf_joined['AI'] = gdf_joined['AI'].fillna(0)
    gdf_joined = gdf_joined.drop_duplicates(subset=gdf_original.columns.tolist())
    
    if 'index_right' in gdf_joined.columns:
        gdf_joined = gdf_joined.drop(columns=['index_right'])
    
    print(f"\n[SUCCESS] Unió completada. Shapefile resultant té {len(gdf_joined)} entrades")
except Exception as e:
    print(f"\n[ERROR] Error en la unió espacial: {e}")
    exit()

# 7. Guardar resultats
print("\n[STATUS] Guardant resultat...")
try:
    columns_to_keep = [col for col in gdf_original.columns if col != 'AI'] + ['AI']
    gdf_result = gdf_joined[columns_to_keep]
    gdf_result.to_file(output_shp)
    
    # Estadístiques
    total = len(gdf_result)
    with_ai = len(gdf_result[gdf_result['AI'] > 0])
    
    print("\n[RESULTAT FINAL]")
    print(f"Shapefile generat a: {output_shp}")
    print(f"Polígons processats: {total}")
    print(f"Polígons amb AI>0: {with_ai}")
    print(f"Polígons amb AI=0: {total - with_ai}")
    
    print("\n[DEBUG] Mostra de resultats:")
    print(gdf_result[['NOM', 'AI']].head())
except Exception as e:
    print(f"\n[ERROR] Error guardant shapefile final: {e}")