import sys
import os 
#os.environ['USE_PYGEOS'] = '0'
import pandas as pd 
import geopandas as gpd
import numpy as np 
import matplotlib as mpl
import matplotlib.pyplot as plt
import pyrosm
import pyproj


#if __name__ == '__main__':
categories = np.arange(1,6)
colorveg=['blue','green','orange','black','magenta']

print('fuel clc')
indir = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Aggregation_index/data'
outdir = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Aggregation_index/data/usol/'
fuelCatTag = []
fuelCatTag.append([221,225]) #1
fuelCatTag.append([223,227]) #2
fuelCatTag.append([222,224,226,229,346]) #3
fuelCatTag.append([228]) #4
fuelCatTag.append([234]) #5

clc = gpd.read_file(indir+'/usol_pilot.shp')
to_latlon = pyproj.Transformer.from_crs(clc.crs, 'epsg:25831')
lowerCorner = to_latlon.transform(*clc.total_bounds[:2])
upperCorner = to_latlon.transform(*clc.total_bounds[2:])
print('bounding box')
print(lowerCorner[::-1], upperCorner[::-1])
print(clc['nivell_2'].unique())
print(clc['nivell_2'].dtype)

    
for iv in categories:
    print('  fuel cat: {:d}'.format(iv),end='')

    condition =  (pd.Series([False]*len(clc)))
    for tag in fuelCatTag[iv-1]:
        condition |= (clc['nivell_2']==tag)
    fuel = clc[condition]
    print(fuel.shape)
        
    fuel.to_file(outdir+'fuelCategory{:d}.geojson'.format(iv), driver="GeoJSON")