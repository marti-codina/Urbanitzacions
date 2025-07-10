import geopandas as gpd
import pandas as pd
import os

# 1. Carregar les dades
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = data

urb = gpd.read_file(data + 'Capes PC/Delimitacio_v1.shp')
edificis = gpd.read_file(data + 'fuxed_construccions_p.gpkg')

# Verificar columnes necessàries
assert 'NOM' in urb.columns, "Missing 'NOM' in urbanitzacions"
assert 'tipus' in edificis.columns, "Missing 'tipus' in edificis"
assert 'id' in edificis.columns, "Missing 'id' in edificis"

# Assegurar mateix CRS
edificis = edificis.to_crs(urb.crs)

# 2. Definir categories de vulnerabilitat
high_vuln = ['edu', 'san','cam']
medium_vuln = ['ind', 'ins','jac', 'hot', 'bal', 'pat', 'enu', 'eaf', 'eeo', 'ehí', 'iel', 
             'hcb', 'eso', 'ete', 'tai', 'tec', 'tre', 'tct', 'age', 'com']
low_vuln = ['fut', 'mcs', 'ten', 'ces', 'esp', 'mon', 'cas', 'pen']

# 3. Filtrar només edificis vulnerables
edificis_vulnerables = edificis[edificis['tipus'].isin(high_vuln + medium_vuln + low_vuln)].copy()

# 4. Classificar edificis per vulnerabilitat i assignar puntuació
edificis_vulnerables['vulnerabilitat'] = 'Medium'  # Valor per defecte
edificis_vulnerables['puntuacio'] = 2  # Puntuació per defecte (Medium)

edificis_vulnerables.loc[edificis_vulnerables['tipus'].isin(high_vuln), 'vulnerabilitat'] = 'High'
edificis_vulnerables.loc[edificis_vulnerables['tipus'].isin(high_vuln), 'puntuacio'] = 3

edificis_vulnerables.loc[edificis_vulnerables['tipus'].isin(low_vuln), 'vulnerabilitat'] = 'Low'
edificis_vulnerables.loc[edificis_vulnerables['tipus'].isin(low_vuln), 'puntuacio'] = 1

# 5. Intersecció edificis-urbanitzacions
buildings_in_urb = gpd.sjoin(
    left_df=edificis_vulnerables[['id', 'tipus', 'vulnerabilitat', 'puntuacio', 'geometry']].reset_index(drop=True),
    right_df=urb[['NOM', 'geometry']].reset_index(drop=True),
    how='inner',
    predicate='intersects'
)

# 6. Crear resum per NOM i vulnerabilitat
summary = buildings_in_urb.groupby(['NOM', 'vulnerabilitat']).agg({
    'id': lambda x: ', '.join(map(str, x)),
    'tipus': lambda x: ', '.join(x),
    'vulnerabilitat': 'count',
    'puntuacio': 'sum'
}).rename(columns={'vulnerabilitat': 'count'}).reset_index()

# 7. Preparar dades per a cada nivell de vulnerabilitat
vuln_levels = ['High', 'Medium', 'Low']
result_data = urb[['NOM', 'geometry']].copy()

for vuln in vuln_levels:
    # Filtrar per nivell de vulnerabilitat
    temp = summary[summary['vulnerabilitat'] == vuln]
    
    # Afegir columnes de comptatge
    result_data[f'{vuln}_vuln_count'] = result_data['NOM'].map(
        temp.set_index('NOM')['count']).fillna(0).astype(int)
    
    # Afegir columnes de llistes
    result_data[f'{vuln}_vuln_ids'] = result_data['NOM'].map(
        temp.set_index('NOM')['id']).fillna('')
    result_data[f'{vuln}_vuln_tipus'] = result_data['NOM'].map(
        temp.set_index('NOM')['tipus']).fillna('')

# 8. Calcular total d'edificis i puntuació total
result_data['Total_edificis'] = (
    result_data['High_vuln_count'] + 
    result_data['Medium_vuln_count'] + 
    result_data['Low_vuln_count']
)

# Calcular TOT_vuln (suma de puntuacions)
tot_vuln = buildings_in_urb.groupby('NOM')['puntuacio'].sum().reset_index()
result_data['TOT_vuln'] = result_data['NOM'].map(
    tot_vuln.set_index('NOM')['puntuacio']).fillna(0).astype(int)

# 9. Calcular vulnerabilitat normalitzada
tot_vuln_max = result_data['TOT_vuln'].max()
tot_vuln_min = result_data['TOT_vuln'].min()

# Evitar divisió per zero si totes les urbanitzacions tenen el mateix valor
if tot_vuln_max == tot_vuln_min:
    result_data['Vuln_norm'] = 0.0
else:
    result_data['Vuln_norm'] = (result_data['TOT_vuln'] - tot_vuln_min) / (tot_vuln_max - tot_vuln_min)

# 9.1 Crear la columna Vuln_class basada en Vuln_norm
result_data['Vuln_class'] = 1  # Valor per defecte (baix)

result_data.loc[(result_data['Vuln_norm'] >= 0.33) & (result_data['Vuln_norm'] < 0.66), 'Vuln_class'] = 2  # Mig
result_data.loc[result_data['Vuln_norm'] >= 0.66, 'Vuln_class'] = 3  # Alt

# 10. Guardar resultats
output_file = os.path.join(dataout, "URB_VULN_NORM.shp")
result_data.to_file(output_file)

# 11. Mostrar resum
print("Resum d'edificis i vulnerabilitat:")
print(result_data[['NOM', 'High_vuln_count', 'Medium_vuln_count', 'Low_vuln_count', 
                  'Total_edificis', 'TOT_vuln', 'Vuln_norm', 'Vuln_class']].head())
print(f"\nFitxer guardat a: {output_file}")
print(f"\nValors de referència:")
print(f"TOT_vuln màxim: {tot_vuln_max}")
print(f"TOT_vuln mínim: {tot_vuln_min}")