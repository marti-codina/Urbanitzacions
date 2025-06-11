import pandas as pd
import geopandas as  gpd
import numpy as np
import os
import sys


data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'

tpi_file = gpd.read_file(data + 'tpi_file.shp')
urb_file = gpd.read_file(data + 'URB_PILOT.shp')

tpi_urb = tpi_file.sjoin(urb_file, how='inner', predicate='intersects')

urb_file["barranc"] = -1
urb_file["pedent"] = -1
urb_file["carena"] = -1
urb_file["% barranc"] = -1
urb_file["% penendt"] = -1
urb_file["% carena"] = -1

for irow, row in urb_file.iterrows():
    tpi_sub = tpi_urb[tpi_urb["index_right"] == irow]
    urb_file.at[irow, 'barranc'] = tpi_sub[tpi_sub["DN"].isin([1, 2, 3])]["Area"].sum()
    urb_file.at[irow, 'pedent'] = tpi_sub[tpi_sub["DN"].isin([6, 7])]["Area"].sum()
    urb_file.at[irow, 'carena'] = tpi_sub[tpi_sub["DN"].isin([9, 10])]["Area"].sum()
    urb_file.at[irow, '% barranc'] = urb_file.at[irow, 'barranc'] / urb_file.at[irow, 'Area']
    urb_file.at[irow, '% pendent'] = urb_file.at[irow, 'barranc'] / urb_file.at[irow, 'Area']
    urb_file.at[irow, '% carena'] = urb_file.at[irow, 'barranc'] / urb_file.at[irow, 'Area']

# Afegeix columna TPI
urb_file["TPI"] = 0

cond1 = (urb_file["% barranc"] >= 0.1) | (urb_file["% pendent"] >= 0.3) | (urb_file["% carena"] >= 0.2)
cond2 = (
    ((urb_file["% barranc"] >= 0.1) & (urb_file["% pendent"] >= 0.3)) |
    ((urb_file["% barranc"] >= 0.1) & (urb_file["% carena"] >= 0.2)) |
    ((urb_file["% pendent"] >= 0.3) & (urb_file["% carena"] >= 0.2))
)
cond3 = (
    (urb_file["% barranc"] >= 0.1) &
    (urb_file["% pendent"] >= 0.3) &
    (urb_file["% carena"] >= 0.2)
)

urb_file.loc[cond1, "TPI"] = 1
urb_file.loc[cond2, "TPI"] = 2
urb_file.loc[cond3, "TPI"] = 3

no_cond = ~(cond1 | cond2 | cond3)
urb_file.loc[no_cond, "TPI"] = 0

output_file= os.path.join(dataout, "URB_TPI.shp")
print("urb_tpi saved")
