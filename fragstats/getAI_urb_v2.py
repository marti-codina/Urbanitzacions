import os
import rasterio
import chardet
import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd

input_rasters = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Geotiffs_urb_pilot/rasters_URB"
class_file = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Geotiffs_urb_pilot/URB_AI_results.class"  # Fitxer amb LID, adreça i AI
original_shp = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Capes PC/Delimitacio_v1.shp"
output_shp = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/quadrats_AI.shp"

# 1. Detecció de l'encoding del fitxer
# Llista d'encodings a provar
encodings_to_try = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']

def try_read_file(file_path, encodings):
    for encoding in encodings:
        try:
            # Provar amb diferents delimitadors
            for sep in [',', ';', '\t']:
                try:
                    return pd.read_csv(
                        file_path,
                        sep=sep,
                        engine='python',
                        header=0,
                        encoding=encoding
                    )
                except pd.errors.ParserError:
                    continue
        except UnicodeDecodeError:
            continue
    raise ValueError("No s'ha pogut llegir el fitxer amb cap encoding o delimitador provat")

try:
    # Llegir el fitxer
    df = try_read_file(class_file, encodings_to_try)
    
    # Verificar i convertir columnes a string si no ho són
    for col in df.columns:
        if not pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].astype(str)
    
    # Neteja de noms de columnes
    df.columns = df.columns.str.strip()
    
    # Neteja i conversió de valors (amb verificació addicional)
    if 'AI' in df.columns:
        df['AI'] = pd.to_numeric(df['AI'].str.strip() if pd.api.types.is_string_dtype(df['AI']) else df[col], 
                                errors='coerce').fillna(0)
    else:
        raise ValueError("No s'ha trobat la columna 'AI' al fitxer")
    
    # Extracció del nom del fitxer amb verificació
    if 'LID' in df.columns:
        df['nom_fitxer'] = df['LID'].str.strip().apply(os.path.basename)
    else:
        raise ValueError("No s'ha trobat la columna 'LID' al fitxer")
    
    print("\n[DEBUG] Mostra de dades del .class:")
    print(df[['nom_fitxer', 'AI']].head())

except Exception as e:
    print(f"\n[ERROR] Processament del fitxer .class: {e}")
    exit()

    # 2. Lectura del fitxer .class
    # Utilitzem una expressió regular més robusta per al separador
    df = pd.read_csv(
        class_file,
        sep=r',\s*',  # Nota la 'r' per a raw string
        engine='python',
        header=0,
        encoding=file_encoding
    )
    
    # Neteja de noms de columnes
    df.columns = df.columns.str.strip()
    
    # Netegem i convertim valors
    df['AI'] = pd.to_numeric(df['AI'].str.strip(), errors='coerce').fillna(0)
    
    # Extraiem el nom curt del fitxer des de LID
    df['nom_fitxer'] = df['LID'].str.strip().apply(os.path.basename)
    
    print("\n[DEBUG] Mostra de dades del .class:")
    print(df[['nom_fitxer', 'AI']].head())

except Exception as e:
    print(f"\n[ERROR] Processament del fitxer .class: {e}")
    exit()

# 2. Creació del diccionari d'AI (nom fitxer -> AI)
ai_dict = {row['nom_fitxer'].replace('.tif', ''): row['AI'] for _, row in df.iterrows()}
print(f"\n[STATUS] S'han processat {len(ai_dict)} entrades del .class")

# 3. Processament dels rasters per crear shapefile temporal
print("\n[STATUS] Creant shapefile temporal a partir de rasters...")
poligons_temp = []
dades_temp = []

# Crear diccionari AI només si existeix la columna 'nom_fitxer' al DataFrame
if hasattr(df, 'nom_fitxer'):
    ai_dict = dict(zip(
        df['nom_fitxer'].str.replace('.tif', '', case=False), 
        df['AI']
    ))
else:
    print("\n[ERROR] No s'ha trobat la columna 'nom_fitxer' al DataFrame")
    exit()

for filename in os.listdir(input_rasters):
    if filename.lower().endswith('.tif'):
        try:
            nom_base = os.path.splitext(filename)[0]
            ai = ai_dict.get(nom_base, 0.0)
            
            with rasterio.open(os.path.join(input_rasters, filename)) as src:
                bounds = src.bounds
                geometry = Polygon([
                    (bounds.left, bounds.bottom),
                    (bounds.left, bounds.top),
                    (bounds.right, bounds.top),
                    (bounds.right, bounds.bottom)
                ])
                
                dades_temp.append({
                    'nom_raster': nom_base,
                    'AI': ai,
                    'geometry': geometry
                })
        except Exception as e:
            print(f"[WARNING] Error processant {filename}: {e}")

if not dades_temp:
    print("\n[ERROR] No s'han trobat rasters vàlids")
    exit()

# Creem GeoDataFrame temporal amb la mateixa CRS que l'original
gdf_temp = gpd.GeoDataFrame(dades_temp, geometry='geometry', crs="EPSG:25831")

# 4. Lectura del shapefile original
print("\n[STATUS] Llegint shapefile original...")
try:
    gdf_original = gpd.read_file(original_shp)
    print(f"Shapefile original té {len(gdf_original)} entrades")
    
    # Assegurar que tenen la mateixa CRS
    if gdf_original.crs != gdf_temp.crs:
        print("[INFO] Reprojectant shapefile original per coincidir CRS")
        gdf_original = gdf_original.to_crs(gdf_temp.crs)
except Exception as e:
    print(f"\n[ERROR] Error llegint shapefile original: {e}")
    exit()

# 5. Fem la unió espacial directa entre polígons
print("\n[STATUS] Realitzant unió espacial directa...")
try:
    # Unió espacial basada en intersecció de polígons
    gdf_joined = gpd.sjoin(
        gdf_original,
        gdf_temp[['AI', 'geometry']],
        how='left',
        predicate='intersects'
    )
    
    # Netegem duplicats (pot haver-hi múltiples interseccions)
    gdf_joined = gdf_joined.drop_duplicates(subset=gdf_original.columns.tolist())
    
    # Si hi ha valors NaN en AI, els posem a 0
    gdf_joined['AI'] = gdf_joined['AI'].fillna(0)
    
    # Netegem columnes redundants
    if 'index_right' in gdf_joined.columns:
        gdf_joined = gdf_joined.drop(columns=['index_right'])
    
    print(f"\n[SUCCESS] Unió completada. Shapefile resultant té {len(gdf_joined)} entrades")
    
except Exception as e:
    print(f"\n[ERROR] Error en la unió espacial: {e}")
    exit()

# 6. Guardem el resultat
print("\n[STATUS] Guardant resultat...")
try:
    # Eliminem columnes que no necessitem
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