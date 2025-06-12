import geopandas as gpd
import pandas as pd
import numpy as np
import os

# 1. Load data with original IDs
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = data

urb = gpd.read_file(data + 'Capes PC/Delimitacio_v1.shp')
grid = gpd.read_file(data + "Població/2024/gridpoblacio01012024.shp")
edificis = gpd.read_file(data + 'fuxed_construccions_p.gpkg')

# Verify required columns
assert 'id' in edificis.columns, "Missing 'id' in edificis"
assert 'NOM' in urb.columns, "Missing 'NOM' in urbanitzacions"
assert 'ID_QUADTRE' in grid.columns, "Missing 'ID_QUADTRE' in grid"
assert 'TOTAL' in grid.columns, "Missing 'TOTAL' in grid"

# Ensure consistent CRS
edificis = edificis.to_crs(urb.crs)
grid = grid.to_crs(urb.crs)

# --------------------------------------------------
# STEP 1: Calculate density (people/building) per grid cell
#         (using ALL buildings, not just urban ones)
# --------------------------------------------------

# A. Join ALL buildings with grid
all_buildings_grid = gpd.sjoin(
    left_df=edificis[['id', 'geometry']].reset_index(drop=True),
    right_df=grid[['ID_QUADTRE', 'TOTAL', 'geometry']].reset_index(drop=True),
    how='inner',
    predicate='intersects'
).rename(columns={'index_right': 'grid_idx'})

# B. Count buildings per grid cell
buildings_per_grid = (
    all_buildings_grid.groupby('ID_QUADTRE')
    .size()
    .reset_index(name='total_buildings')
)

# C. Calculate people per building
grid_with_density = grid.merge(
    buildings_per_grid,
    on='ID_QUADTRE',
    how='left'
)
grid_with_density['total_buildings'] = grid_with_density['total_buildings'].fillna(1)
grid_with_density['people_per_building'] = (
    grid_with_density['TOTAL'] / 
    grid_with_density['total_buildings']
)

# --------------------------------------------------
# STEP 2: Calculate urban population
# --------------------------------------------------

# A. Find buildings within urban areas
buildings_in_urb = gpd.sjoin(
    left_df=edificis[['id', 'geometry']].reset_index(drop=True),
    right_df=urb[['NOM', 'geometry']].reset_index(drop=True),
    how='inner',
    predicate='within'
).rename(columns={'index_right': 'urb_idx'})

# B. Join urban buildings with grid
buildings_urb_grid = gpd.sjoin(
    left_df=buildings_in_urb.reset_index(drop=True),
    right_df=grid[['ID_QUADTRE', 'geometry']].reset_index(drop=True),
    how='inner',
    predicate='intersects'
).rename(columns={'index_right': 'grid_idx2'})

# C. Add density information
urban_buildings_with_density = buildings_urb_grid.merge(
    grid_with_density[['ID_QUADTRE', 'people_per_building']],
    on='ID_QUADTRE',
    how='left'
)

# D. Calculate population per urban area
urban_population = (
    urban_buildings_with_density.groupby('NOM')
    .agg(
        building_count=('id', 'count'),
        total_population=('people_per_building', 'sum')
    )
    .reset_index()
)

# E. Merge with original urban areas
urb_with_pop = urb.merge(
    urban_population,
    on='NOM',
    how='left'
).fillna({'building_count': 0, 'total_population': 0})

# --------------------------------------------------
# Save results
# --------------------------------------------------
output_path = os.path.join(dataout, "urban_areas_with_population.shp")
urb_with_pop.to_file(output_path)

print(f"Success! Results saved to {output_path}")
print(f"Total urban population: {urb_with_pop['total_population'].sum():,.0f}")
print(f"Total buildings in urban areas: {urb_with_pop['building_count'].sum():,.0f}")