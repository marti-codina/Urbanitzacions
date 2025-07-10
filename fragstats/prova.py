import numpy as np
import rasterio
from rasterio.transform import Affine

# Output file path
output_path = r"C:\Users\marti.codina\Nextcloud\2025 - FIRE-SCENE (subcontract)\METODOLOGIA URBANITZACIONS WUI\Capes GIS\Geotiffs_urb_pilot\20x20_tiles\modified_pattern2.tif"

# Grid parameters
grid_size_m = 20  # 20 meters
mida_graella = 20  # 20x20 cèl·les
celda_mida = 1     # 1 metre per celda

# Creem el patró exacte que has especificat
patro_base = np.array([
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [1, 1, 2, 1, 2, 1, 1, 2, 1, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
], dtype=np.uint8)

# Repetim el patró per omplir 20 files
data = np.vstack([patro_base for _ in range(7)])[:20]  # Assegurem 20 files exactes

# Si necessitem més columnes (per fer 20x20), repetim horitzontalment
if data.shape[1] < 20:
    repeticions = (20 // data.shape[1]) + 1
    data = np.hstack([data for _ in range(repeticions)])[:, :20]

# Transformació geogràfica (exemple UTM 31N)
transform = Affine.translation(0, 20) * Affine.scale(celda_mida, -celda_mida)

# Perfil del GeoTIFF
profile = {
    'driver': 'GTiff',
    'dtype': 'uint8',
    'nodata': None,  # Important per FRAGSTATS
    'width': 20,
    'height': 20,
    'count': 1,
    'crs': 'EPSG:25831',  # Canvia al teu CRS
    'transform': transform,
}

# Escrivim el fitxer
with rasterio.open(output_path, 'w', **profile) as dst:
    dst.write(data, 1)

print("Fitxer generat correctament a:", output_path)
print("Visualització del patró (primera part):")
print(data[:3, :10])  # Mostrem les 3 primeres files i 10 columnes