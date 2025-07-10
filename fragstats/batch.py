import os

# Configuració
input_folder = r"C:\Users\marti.codina\Nextcloud\2025 - FIRE-SCENE (subcontract)\METODOLOGIA URBANITZACIONS WUI\Capes GIS\Geotiffs_urb_pilot\rasters_URB\simpl_5m"
output_batch_file = os.path.join(input_folder, "fragstats_batch_5m.fbt")

# Llistar tots els fitxers .tif a la carpeta
tif_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.tif')]

# Obrir el fitxer batch per escriure
with open(output_batch_file, 'w') as txt_file:
    # Escriure capçalera si és necessària (opcional)
    txt_file.write("[FRAGSTATS BATCH]\n")
    txt_file.write("VERSION=4.3\n\n")  # Versió de FRAGSTATS
    
    txt_file.write("[FILES]\n")
    
    for fl in tif_files:
        # Construir el camí complet al fitxer
        pth = os.path.join(input_folder, fl)
        # Construir la línia en el format que espera FRAGSTATS
        outStr = f"{pth}, x, 999, x, x, 1, x, IDF_GeoTIFF\n"
        txt_file.write(outStr)

print(f"Fitxer batch creat correctament a: {output_batch_file}")
print(f"S'han inclòs {len(tif_files)} fitxers GeoTIFF al batch.")