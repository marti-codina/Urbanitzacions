import geopandas as gpd
import pandas as pd
import numpy as np
import os
from shapely.strtree import STRtree

# 1. Load data
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = data

urb = gpd.read_file(data + 'Capes PC/Delimitacio_v1.shp')
grid = gpd.read_file(data + "Població/2024/gridpoblacio01012024.shp")
edificis = gpd.read_file(data + 'fuxed_construccions_p.gpkg')

# Filter residential buildings
edificis = edificis[edificis['tipus'] == 'edi'].copy()

# Verify columns
assert 'id' in edificis.columns, "Missing 'id' in edificis"
assert 'NOM' in urb.columns, "Missing 'NOM' in urbanitzacions"
assert 'ID_QUADTRE' in grid.columns, "Missing 'ID_QUADTRE' in grid"

# Demographic attributes and their new names
demographic_attrs = {
    'TOTAL': 'URB_TOT',
    'HOMES': 'URB_HOME',
    'DONES': 'URB_DONA',
    'P_0_14': 'URB_0_14',
    'P_15_64': 'URB_15_64',
    'P_65_I_MES': 'URB_65+',
    'P_ESPANYOL': 'URB_ESP',
    'P_ESTRANGE': 'URB_ESTR',
    'P_NASC_CAT': 'URB_N_CAT',
    'P_NASC_EST': 'URB_N_EST',
    'P_POS_IMPU': 'URB_IMPU'
}

# Ensure consistent CRS
edificis = edificis.to_crs(urb.crs)
grid = grid.to_crs(urb.crs)

# --------------------------------------------------
# OPTIMIZED VERSION OF get_largest_overlap
# --------------------------------------------------
def get_largest_overlap(buildings, grid_cells):
    """Versió optimitzada que evita el problema de 'index_right'"""
    # Reset index to avoid conflicts
    buildings = buildings.reset_index(drop=True)
    grid_cells = grid_cells.reset_index(drop=True)
    
    # Spatial join
    joins = gpd.sjoin(
        buildings[['id', 'geometry']],
        grid_cells[['ID_QUADTRE', 'geometry']],
        how='inner',
        predicate='intersects'
    )
    
    # Calculate intersection areas
    joins['area'] = joins.apply(
        lambda x: x.geometry.intersection(
            grid_cells.loc[x.index_right, 'geometry']
        ).area,
        axis=1
    )
    
    # Keep only largest intersection per building
    joins = joins.sort_values('area').drop_duplicates('id', keep='last')
    
    return joins[['id', 'ID_QUADTRE']]

# --------------------------------------------------
# STEP 1: Calculate density per grid cell
# --------------------------------------------------
building_grid_assignments = get_largest_overlap(
    edificis,
    grid[['ID_QUADTRE', 'geometry']]
)

# Merge with demographic data
grid_with_buildings = pd.merge(
    building_grid_assignments,
    grid[['ID_QUADTRE'] + list(demographic_attrs.keys())],
    on='ID_QUADTRE',
    how='left'
)

# Calculate buildings per grid
buildings_per_grid = grid_with_buildings.groupby('ID_QUADTRE').size().reset_index(name='num_edificis')
grid_with_density = pd.merge(
    grid,
    buildings_per_grid,
    on='ID_QUADTRE',
    how='left'
).fillna({'num_edificis': 1})

# Calculate population per building
for orig_attr, new_attr in demographic_attrs.items():
    grid_with_density[f'{new_attr}_per_edifici'] = (
        grid_with_density[orig_attr] / grid_with_density['num_edificis']
    )

# --------------------------------------------------
# STEP 2: Calculate urban population
# --------------------------------------------------
# Find buildings within urban areas (using 'within')
edificis_in_urb = gpd.sjoin(
    left_df=edificis[['id', 'geometry']],
    right_df=urb[['NOM', 'geometry']],
    how='inner',
    predicate='within'
).drop(columns=['index_right'])  # Eliminem la columna problemàtica

# Assign to grid cells
urban_building_assignments = (
    get_largest_overlap(
        edificis_in_urb[['id', 'geometry']],
        grid[['ID_QUADTRE', 'geometry']]
    )
    .merge(edificis_in_urb[['id', 'NOM']], on='id')  # Mantenim el NOM
)

# Merge with density data
urban_population = (
    urban_building_assignments
    .merge(grid_with_density[['ID_QUADTRE'] + [f'{new_attr}_per_edifici' for new_attr in demographic_attrs.values()]],
           on='ID_QUADTRE')
    .groupby('NOM')
    .agg(
        building_count=('id', 'count'),
        **{f'{new_attr}': (f'{new_attr}_per_edifici', 'sum') for new_attr in demographic_attrs.values()}
    )
    .reset_index()
)

# Calculate percentage of 65+ population
urban_population['URB_%_65'] = (urban_population['URB_65+'] / urban_population['URB_TOT']) * 100

# Merge with original urban areas
urb_with_pop = urb.merge(urban_population, on='NOM', how='left').fillna(0)

# Crear columna URB_VELL (1 si %65+ > 40, 0 altrament)
urb_with_pop['URB_VELL'] = (urb_with_pop['URB_%_65'] > 40).astype(int)
# --------------------------------------------------
# Export results
# --------------------------------------------------
output_path = os.path.join(dataout, "urban_areas_with_population_corrected.shp")
urb_with_pop.to_file(output_path)

print(f"Resultats guardats a {output_path}")
print("\nResum de totals:")
for new_attr in demographic_attrs.values():
    print(f"{new_attr}: {urb_with_pop[new_attr].sum():,.0f}")
print(f"Edificis comptats: {urb_with_pop['building_count'].sum():,.0f}")
print(f"Percentatge mitjà de població 65+: {urb_with_pop['URB_%_65'].mean():.1f}%")