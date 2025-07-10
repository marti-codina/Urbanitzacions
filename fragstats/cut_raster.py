import os
import rasterio
from rasterio.windows import Window
import math

# Configuración
input_folder = r"C:\Users\marti.codina\Nextcloud\2025 - FIRE-SCENE (subcontract)\METODOLOGIA URBANITZACIONS WUI\Capes GIS\Geotiffs_urb_pilot"
output_folder = os.path.join(input_folder, "50x50_tiles")  # Carpeta para los resultados
tile_size = 50  # Tamaño del cuadrado en metros

# Crear carpeta de salida si no existe
os.makedirs(output_folder, exist_ok=True)

# Procesar cada archivo GeoTIFF en la carpeta de entrada
for filename in os.listdir(input_folder):
    if filename.startswith("zone_") and filename.endswith(".tif"):
        input_path = os.path.join(input_folder, filename)
        zone_name = os.path.splitext(filename)[0]  # Ej: "zona_1"
        
        with rasterio.open(input_path) as src:
            # Calcular tamaño de píxeles (asumiendo que son iguales en x e y)
            pixel_size_x, pixel_size_y = src.res
            
            # Convertir 20m a píxeles
            tile_width_px = int(round(tile_size / pixel_size_x))
            tile_height_px = int(round(tile_size / pixel_size_y))
            
            # Calcular número de cuadrados en cada dimensión
            num_cols = math.ceil(src.width / tile_width_px)
            num_rows = math.ceil(src.height / tile_height_px)
            
            # Crear cada cuadrado
            for row in range(num_rows):
                for col in range(num_cols):
                    # Definir la ventana (window) para cortar
                    window = Window(
                        col * tile_width_px,
                        row * tile_height_px,
                        min(tile_width_px, src.width - col * tile_width_px),
                        min(tile_height_px, src.height - row * tile_height_px)
                    )
                    
                    # Leer los datos de la ventana
                    data = src.read(window=window)
                    
                    # Calcular las coordenadas de la esquina superior izquierda
                    transform = src.window_transform(window)
                    x_origin = transform[2]
                    y_origin = transform[5]
                    
                    # Crear el perfil del nuevo raster
                    profile = src.profile
                    profile.update({
                        'height': window.height,
                        'width': window.width,
                        'transform': transform
                    })
                    
                    # Nombre del archivo de salida
                    output_filename = f"{zone_name}_{row}_{col}.tif"
                    output_path = os.path.join(output_folder, output_filename)
                    
                    # Guardar el cuadrado
                    with rasterio.open(output_path, 'w', **profile) as dst:
                        dst.write(data)
        
        print(f"Procesado {filename} - generados {num_rows*num_cols} cuadrados de 20x20m")

print("Proceso completado!")