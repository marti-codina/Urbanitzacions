import sys
import os 
import pandas as pd
import geopandas as gpd
import matplotlib as mpl
import numpy as np
import shapely
import importlib
import matplotlib.colors as colors
from matplotlib import pyplot as plt
from shapely.geometry import Polygon
from fiona.crs import from_epsg

# Homebrewed tools
# Directori d’entrada i sortida
indir = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Urb_July/FUEL/'
dirout = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Urb_July/FUEL/'


print('Load CLC categories and classify by hazard level ...', end='')
sys.stdout.flush()
idxclc = range(1, 6)
fuelCat_all = []
for iv in idxclc:
    fuelCat_ = gpd.read_file(os.path.join(indir, f'fuelCategory{iv}.geojson'))
    fuelCat_['ICat'] = iv
    fuelCat_['rank'] = f'vegetation category {iv}'
    fuelCat_all.append(fuelCat_)

fuelCat_all = pd.concat(fuelCat_all)

    # Classificació segons AI
    #fuelCat_all['IAI'] = -999
    #fuelCat_all.loc[fuelCat_all['AI'] > 0.9, 'IAI'] = 2
    #fuelCat_all.loc[(fuelCat_all['AI'] > 0) & (fuelCat_all['AI'] <= 0.9), 'IAI'] = 1
    #fuelCat_all.loc[fuelCat_all['AI'] <= 0, 'IAI'] = 0

    # Categoria final de perill
    #fuelCat_all['IFH'] = fuelCat_all['ICat'] + fuelCat_all['IAI']
    #fuelCat_all['FH_rank'] = 'hazard category ' + fuelCat_all['IFH'].astype(str)

print(' done')

    # 🔽 Exportació del fitxer vectorial classificat
out_vector_file = os.path.join(dirout, 'Fuel_all.geojson')
fuelCat_all.to_file(out_vector_file, driver='GeoJSON')
print(f'Fitxer vectorial desat a: {out_vector_file}')

    # 🔽 (Opcional) plot si vols mantenir la visualització (això depèn de si tens definits aquests valors globals)
"""
    # Resta del codi per generar el mapa si tens definits:
    #   - xminAll, xmaxAll, yminAll, ymaxAll, landNE, graticule, bordersSelection, crs_here

    # mpl.rcParams[...]  # ja establert

    fig = plt.figure(figsize=(10, 10))
    ax = plt.subplot(111)
    fuelCat_all.plot(ax=ax, column='FH_rank', legend=True, cmap=colors.ListedColormap(list(color_dict.values())), zorder=4)

    ax.set_title('Fire Hazard Categories Area', pad=20)
    fig.savefig(os.path.join(dirout, 'FireHazardCatArea.png'), dpi=400)
    plt.close(fig)
    """
