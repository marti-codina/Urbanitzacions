import geopandas as gpd
import pandas as pd
import numpy as np
import os
from shapely.strtree import STRtree

# 1. Load data
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = data

# Load urban areas
urb = gpd.read_file(data + 'Capes PC/Delimitacio_v1.shp', 
                   columns=['NOM', 'MUN_INE', 'CODI', 'TIPUS', 'MUNICIPI', 'COMARCA', 'mapid', 'OBSERVACAIO', 'Area', 'geometry'])

# Load and filter buildings
edificis = gpd.read_file(data + 'fuxed_construccions_p.gpkg')
edificis = edificis[edificis['tipus'] == 'edi'].copy()
edificis['area_edifici'] = edificis.geometry.area
edificis = edificis[edificis['area_edifici'] > 45]  # Filter buildings >45m²

# Load population grid
grid = gpd.read_file(data + "Població/2024/gridpoblacio01012024.shp")

# Ensure consistent CRS
edificis = edificis.to_crs(urb.crs)
grid = grid.to_crs(urb.crs)

# --------------------------------------------------
# OPTIMIZED VERSION OF get_largest_overlap
# --------------------------------------------------
def get_largest_overlap(buildings, grid_cells):
    """Versió optimitzada que evita el problema de 'index_right'"""
    buildings = buildings.reset_index(drop=True)
    grid_cells = grid_cells.reset_index(drop=True)
    
    joins = gpd.sjoin(
        buildings[['id', 'geometry']],
        grid_cells[['ID_QUADTRE', 'geometry']],
        how='inner',
        predicate='intersects'
    )
    
    joins['area'] = joins.apply(
        lambda x: x.geometry.intersection(
            grid_cells.loc[x.index_right, 'geometry']
        ).area,
        axis=1
    )
    
    joins = joins.sort_values('area').drop_duplicates('id', keep='last')
    return joins[['id', 'ID_QUADTRE']]

# --------------------------------------------------
# Demographic attributes mapping
# --------------------------------------------------
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

# --------------------------------------------------
# STEP 1: Calculate population using grid method where possible
# --------------------------------------------------
def calculate_grid_population(urban_area):
    """Calculate population using grid method for a single urban area"""
    # Convert urban_area to GeoDataFrame
    urban_area_gdf = gpd.GeoDataFrame([urban_area], geometry='geometry', crs=urb.crs)
    
    # Find buildings within this urban area
    buildings_in_area = gpd.sjoin(
        edificis[['id', 'geometry']],
        urban_area_gdf[['geometry']],
        how='inner',
        predicate='within'
    )
    
    if len(buildings_in_area) == 0:
        return None
    
    # Find grid cells that intersect with this urban area
    grid_in_area = gpd.sjoin(
        grid,
        urban_area_gdf[['geometry']],
        how='inner',
        predicate='intersects'
    )
    
    if len(grid_in_area) == 0:
        return None
    
    # Assign buildings to grid cells
    building_assignments = get_largest_overlap(
        buildings_in_area[['id', 'geometry']],
        grid_in_area[['ID_QUADTRE', 'geometry']]
    )
    
    # Calculate buildings per grid
    buildings_per_grid = building_assignments.groupby('ID_QUADTRE').size().reset_index(name='num_edificis')
    
    # Merge with demographic data
    grid_with_density = pd.merge(
        grid_in_area,
        buildings_per_grid,
        on='ID_QUADTRE',
        how='left'
    ).fillna({'num_edificis': 1})
    
    # Calculate population per building
    for orig_attr, new_attr in demographic_attrs.items():
        grid_with_density[f'{new_attr}_per_edifici'] = (
            grid_with_density[orig_attr] / grid_with_density['num_edificis']
        )
    
    # Sum population for all buildings in this urban area
    urban_pop = building_assignments.merge(
        grid_with_density[['ID_QUADTRE'] + [f'{new_attr}_per_edifici' for new_attr in demographic_attrs.values()]],
        on='ID_QUADTRE'
    )
    
    return {
        'building_count': len(buildings_in_area),
        **{new_attr: urban_pop[f'{new_attr}_per_edifici'].sum() for new_attr in demographic_attrs.values()}
    }

# --------------------------------------------------
# STEP 2: Process all urban areas with fallback to 2.6 method
# --------------------------------------------------
results = []

for _, urban_area in urb.iterrows():
    # Try grid method first
    grid_result = calculate_grid_population(urban_area)
    
    if grid_result is not None:
        # Use grid method results
        results.append({
            'NOM': urban_area['NOM'],
            'method': 'grid',
            **grid_result
        })
    else:
        # Fall back to 2.6 method
        urban_area_gdf = gpd.GeoDataFrame([urban_area], geometry='geometry', crs=urb.crs)
        buildings_in_area = gpd.sjoin(
            edificis[['id', 'geometry', 'area_edifici']],
            urban_area_gdf[['geometry']],
            how='inner',
            predicate='within'
        )
        
        num_buildings = len(buildings_in_area)
        total_pop = num_buildings * 2.6
        
        results.append({
            'NOM': urban_area['NOM'],
            'method': '2.6',
            'building_count': num_buildings,
            'URB_TOT': total_pop,
            # Other demographic fields will be NaN for 2.6 method
            **{k: np.nan for k in demographic_attrs.values() if k != 'URB_TOT'}
        })

# Convert results to DataFrame
results_df = pd.DataFrame(results)

# Merge with original urban areas
final_result = urb.merge(results_df, on='NOM', how='left')

# Calculate percentage of 65+ population (only for grid method areas)
final_result['URB_%_65'] = np.where(
    final_result['method'] == 'grid',
    (final_result['URB_65+'] / final_result['URB_TOT']) * 100,
    np.nan
)

# Create URB_VELL column (1 if %65+ > 40, 0 otherwise)
final_result['URB_VELL'] = np.where(
    final_result['URB_%_65'] > 40, 1, 0
)

# Fill NA values for 2.6 method areas
final_result['URB_%_65'] = final_result['URB_%_65'].fillna(0)
final_result['URB_VELL'] = final_result['URB_VELL'].fillna(0)

# --------------------------------------------------
# Export results
# --------------------------------------------------
output_path = os.path.join(dataout, "urban_areas_combined_population.shp")
final_result.to_file(output_path)

print(f"Results saved to {output_path}")
print("\nSummary statistics:")
print(f"Areas using grid method: {len(final_result[final_result['method'] == 'grid'])}")
print(f"Areas using 2.6 method: {len(final_result[final_result['method'] == '2.6'])}")
print(f"Total population: {final_result['URB_TOT'].sum():,.0f}")
print(f"Total buildings counted: {final_result['building_count'].sum():,.0f}")