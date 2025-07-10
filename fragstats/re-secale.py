import os
import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
from tqdm import tqdm  # Per mostrar progrés

def resample_geotiff(input_path, output_path, target_resolution, resampling_method='mode'):
    """Funció per remostrejar un únic fitxer GeoTIFF"""
    with rasterio.open(input_path) as src:
        data = src.read()
        profile = src.profile
        
        scale_factor = target_resolution / src.res[0]
        new_height = int(src.height / scale_factor)
        new_width = int(src.width / scale_factor)
        
        new_transform = rasterio.Affine(
            target_resolution, 0, src.transform[2],
            0, -target_resolution, src.transform[5]
        )
        
        profile.update(
            transform=new_transform,
            height=new_height,
            width=new_width,
            compress='DEFLATE',  # Compressió per estalviar espai
            predictor=2 if data.dtype == np.float32 else 1  # Millor compressió per floats
        )
        
        data_out = np.zeros((src.count, new_height, new_width), dtype=data.dtype)
        
        reproject(
            source=data,
            destination=data_out,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=new_transform,
            dst_crs=src.crs,
            resampling=getattr(Resampling, resampling_method.lower())
        )
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data_out)

def batch_resample(input_folder, output_folder, target_res=10, resampling='mode'):
    """
    Processa tots els fitxers TIFF d'una carpeta
    
    Paràmetres:
    - input_folder: Carpeta amb els fitxers d'entrada (1x1m)
    - output_folder: Carpeta on desar els resultats (10x10m)
    - target_res: Resolució objectiu (10 per 10x10m)
    - resampling: Mètode de remostratge ('average', 'bilinear', 'nearest', etc.)
    """
    # Crear carpeta de sortida si no existeix
    os.makedirs(output_folder, exist_ok=True)
    
    # Llistar tots els fitxers TIFF/GeoTIFF de la carpeta
    tif_files = [f for f in os.listdir(input_folder) 
                if f.lower().endswith(('.tif', '.tiff', '.geotiff'))]
    
    print(f"Trobats {len(tif_files)} fitxers per processar")
    
    # Processar cada fitxer amb barra de progrés
    for filename in tqdm(tif_files, desc="Processant fitxers"):
        input_path = os.path.join(input_folder, filename)
        
        # Crear nom de sortida (afegim '_10m' abans de l'extensió)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_5m{ext}"
        output_path = os.path.join(output_folder, output_filename)
        
        try:
            resample_geotiff(input_path, output_path, target_res, resampling)
        except Exception as e:
            print(f"\nError processant {filename}: {str(e)}")
            continue

# Exemple d'ús
if __name__ == "__main__":
    # Configuració
    INPUT_DIR = r"C:\Users\marti.codina\Nextcloud\2025 - FIRE-SCENE (subcontract)\METODOLOGIA URBANITZACIONS WUI\Capes GIS\Geotiffs_urb_pilot\rasters_URB"  # Modifica això
    OUTPUT_DIR = r"C:\Users\marti.codina\Nextcloud\2025 - FIRE-SCENE (subcontract)\METODOLOGIA URBANITZACIONS WUI\Capes GIS\Geotiffs_urb_pilot\rasters_URB\simpl_5m"               # Modifica això
    TARGET_RESOLUTION = 5                    # 10 metres
    RESAMPLING_METHOD = "mode"             # 'average', 'bilinear', 'nearest', etc.
    
    # Executar el processament per lots
    batch_resample(INPUT_DIR, OUTPUT_DIR, TARGET_RESOLUTION, RESAMPLING_METHOD)
    
    print("Processament completat!")