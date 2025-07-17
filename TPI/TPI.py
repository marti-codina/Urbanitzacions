import geopandas as gpd
import numpy as np
import os

# Input/output paths
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Urb_July/TPI/'
dataout = data  # Using same directory for output
delimitacio_file = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/RAW_URB_J_25/CRS_URB_J_25.shp'  # Assuming this is the boundary file
tpi = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/TPI_class_CAT_vect.shp'  # The land cover file

print('Loading boundary file...')
boundary = gpd.read_file(delimitacio_file)

print('Loading land cover file...')
land_cover = gpd.read_file(tpi)

print('Performing intersection...')
tpi_pilot = gpd.overlay(land_cover, boundary, how='intersection')

# Save the intersected file for future use
tpi_pilot.to_file(data + 'TPI_URB_raw.shp')

# Load data
tpi_file = gpd.read_file(data + 'TPI_PILOT_VECT.shp')
urb_file = gpd.read_file(delimitacio_file).rename(columns={'Shape_Area': 'Area_urb'})
tpi_file['Area_tpi'] = tpi_file.geometry.area

# Spatial join
tpi_urb = tpi_file.sjoin(urb_file, how='inner', predicate='intersects')

# Initialize result columns
for col in ['barranc', 'pedent', 'carena', '% barranc', '% pendent', '% carena', 'TPI']:
    urb_file[col] = -1  # Initialize with -1 (or consider using NaN)

# Calculate areas by category using groupby (more efficient than iterrows)
# More efficient way using groupby + aggregation
area_sums = tpi_urb.groupby(['index_right', 'DN'])['Area_tpi'].sum().unstack()

urb_file['barranc'] = area_sums[[1, 2, 3]].sum(axis=1).reindex(urb_file.index, fill_value=0)
urb_file['pedent'] = area_sums[[6, 7]].sum(axis=1).reindex(urb_file.index, fill_value=0)
urb_file['carena'] = area_sums[[9, 10]].sum(axis=1).reindex(urb_file.index, fill_value=0)

# Calculate percentages (with zero division protection)
urb_file['% barranc'] = (urb_file['barranc'] / urb_file['Area_urb'].replace(0, 1))*100
urb_file['% pendent'] = (urb_file['pedent'] / urb_file['Area_urb'].replace(0, 1))*100
urb_file['% carena'] = (urb_file['carena'] / urb_file['Area_urb'].replace(0, 1))*100

# Calculate TPI index
conditions = [
    ((urb_file['% barranc'] >= 10) & (urb_file['% pendent'] >= 30) & (urb_file['% carena'] >= 20)),
    ((urb_file['% barranc'] >= 10) & (urb_file['% pendent'] >= 30)) |
    ((urb_file['% barranc'] >= 10) & (urb_file['% carena'] >= 20)) |
    ((urb_file['% pendent'] >= 30) & (urb_file['% carena'] >= 20)),
    (urb_file['% barranc'] >= 10) | (urb_file['% pendent'] >= 30) | (urb_file['% carena'] >= 20)
]

choices = [3, 2, 1]
urb_file['TPI'] = np.select(conditions, choices, default=0)

# Save result
output_file = os.path.join(dataout, "URB_TPI.shp")
urb_file.to_file(output_file)
print(f"File saved successfully: {output_file}")