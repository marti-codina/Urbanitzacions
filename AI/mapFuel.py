import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Defineix les rutes
indir = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Aggregation_index/data'
outdir = indir + '/usol/'

# Defineix les categories de "fuel" i noms més descriptius
fuelCatTag = {
    1: [221, 225],
    2: [223, 227],
    3: [222, 224, 226, 229, 346],
    4: [228],
    5: [234]
}

# Colors associats a cada categoria
color_dict = {
    1: 'darkgreen',
    2: 'fuchsia',
    3: 'gold',
    4: 'tomato',
    5: 'teal'
}

# Noms descriptius per a la llegenda
legend_labels = {
    1: 'Coníferes',
    2: 'Esclerofiles',
    3: 'caducifolis, matollars',
    4: 'Prats',
    5: 'Zones humides i aiguamolls'
}

# Llegeix el fitxer .shp
clc = gpd.read_file(f"{indir}/usol_pilot.shp")
clc = clc.to_crs("EPSG:25831")

# Crea un GeoDataFrame buit per combinar-ho tot
fuelCat_all = []

# Classifica i exporta
for iv, tags in fuelCatTag.items():
    fuel = clc[clc['nivell_2'].isin(tags)].copy()
    fuel['fuel_cat'] = iv
    fuel.to_file(f'{outdir}/fuelCategory{iv}.geojson', driver='GeoJSON')
    fuelCat_all.append(fuel)

# Concatena totes les categories en un sol GeoDataFrame
fuelCat_all = pd.concat(fuelCat_all)

# Dibuixa el mapa
fig, ax = plt.subplots(figsize=(10, 10))
for iv, color in color_dict.items():
    label = legend_labels.get(iv, f'Categoria {iv}')
    fuelCat_all[fuelCat_all['fuel_cat'] == iv].plot(
        ax=ax, color=color, label=label, linewidth=0.2, edgecolor='black'
    )

ax.set_title("Categories de vegetació a Catalunya (combustible)", fontsize=14)
ax.set_axis_off()
ax.legend(title="Tipus de vegetació", loc='lower left', fontsize=9, title_fontsize=10)
plt.tight_layout()
plt.show()

