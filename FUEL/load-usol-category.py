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



print('fuel clc')
indir = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Aggregation_index/data'
outdir = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Aggregation_index/data/usol/'

delimitacio_file = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Capes PC/Delimitacio_v1.shp'  # Assuming this is the boundary file
cobertes_file = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/cobertes-sol-v1r0-2019-2022.gpkg'  # The land cover file

fuelCatTag = []
fuelCatTag.append([234]) #1
fuelCatTag.append([228])#2
fuelCatTag.append([222,224,226,229,346]) #3
fuelCatTag.append([223,227])  #4
fuelCatTag.append([221,225]) #5

# Step 1: Perform the intersection between Delimitacio_v1 and cobertes-sol
print('Loading boundary file...')
boundary = gpd.read_file(delimitacio_file)

print('Loading land cover file...')
land_cover = gpd.read_file(cobertes_file)

print('Performing intersection...')
usol_pilot = gpd.overlay(land_cover, boundary, how='intersection')

# Save the intersected file for future use
usol_pilot.to_file(indir + '/usol_pilot.shp')


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