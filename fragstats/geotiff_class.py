import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
import os
from rasterio.crs import CRS

# 📁 Fitxers d'entrada
raster_path = "C:/Users/marti.codina/Downloads/cobertes-sol-v1r0-2023.tif"
shapefile_path = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Capes PC/Delimitacio_v1.shp"
output_dir = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Geotiffs_urb_pilot/rasters_URB"

# 🛠️ Crear carpeta si no existeix
os.makedirs(output_dir, exist_ok=True)

# 📂 Carregar shapefile
zones = gpd.read_file(shapefile_path)

# 🟩 Valors considerats vegetació
vegetation_vals = [7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 26]
NODATA = 0  # Valor per als píxels fora dels polígons

# 🔄 Verificar i reprojectar si cal
with rasterio.open(raster_path) as src:
    raster_crs = src.crs
    if zones.crs != raster_crs:
        print(f"⚠️ CRS no coincideixen: Shapefile ({zones.crs}) vs Raster ({raster_crs})")
        zones = zones.to_crs(raster_crs)
        print(f"✅ Shapefile reprojectat a {raster_crs}")

# 🔁 Iterar per cada zona
with rasterio.open(raster_path) as src:
    for idx, row in zones.iterrows():
        geom = [row.geometry]
        nom = str(row['NOM']).strip().replace(" ", "_").replace("/", "-")
        
        try:
            # 🪚 Retallar la zona amb màscara (píxels fora del polígon seran NoData)
            out_image, out_transform = mask(src, geom, crop=True, all_touched=True, nodata=NODATA)
        except ValueError as e:
            print(f"[!] Zona {idx + 1} ({nom}) no conté píxels vàlids: {str(e)}")
            continue

        # 🎯 Reclassificar el raster retallat
        data = out_image[0]  # obtenim la primera banda
        
        # Crear una màscara per als píxels vàlids (dins del polígon)
        valid_mask = (data != NODATA)
        
        # Aplicar la reclassificació només als píxels vàlids
        # Nova versió (assigna 0 als NoData)
        reclassified = np.full_like(data, 0)  # Inicialitzar tot a 0 (nou NoData)
        reclassified[valid_mask] = np.where(np.isin(data[valid_mask], vegetation_vals), 1, 2)

        # ⚙️ Actualitzar metadades
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": reclassified.shape[0],
            "width": reclassified.shape[1],
            "transform": out_transform,
            "count": 1,
            "dtype": "uint8",
            "nodata": 0  # Especificar el valor NoData
        })

        # 🏷️ Nom del fitxer de sortida
        out_path = os.path.join(output_dir, f"{nom}.tif")

        # 💾 Escriure el GeoTIFF reclassificat
        try:
            with rasterio.open(out_path, "w", **out_meta) as dest:
                dest.write(reclassified.astype(np.uint8), 1)
            print(f"[✓] Exportada zona {idx + 1} ({nom}) → {out_path}")
        except Exception as e:
            print(f"[!] Error en escriure {out_path}: {str(e)}")

print("✅ Procés completat!")