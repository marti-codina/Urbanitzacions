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
high_vuln = ['ind', 'ins', 'edu', 'san', 'enu', 'eaf', 'eeo', 'ehí', 'iel', 
             'hcb', 'eso', 'ete', 'tai', 'tec', 'tre', 'tct', 'age', 'com', 'pen']
medium_vuln = ['jac', 'hot', 'bal', 'cam', 'pat']
low_vuln = ['ele', 'fut', 'mcs', 'ten', 'ces', 'esp', 'mon', 'cas']

# 3. Filtrar només edificis vulnerables
edificis_vulnerables = edificis[edificis['tipus'].isin(high_vuln + medium_vuln + low_vuln)].copy()

# 4. Classificar edificis per vulnerabilitat
edificis_vulnerables['vulnerabilitat'] = 'Medium'  # Valor per defecte
edificis_vulnerables.loc[edificis_vulnerables['tipus'].isin(high_vuln), 'vulnerabilitat'] = 'High'
edificis_vulnerables.loc[edificis_vulnerables['tipus'].isin(low_vuln), 'vulnerabilitat'] = 'Low'

# 5. Intersecció edificis-urbanitzacions
buildings_in_urb = gpd.sjoin(
    left_df=edificis_vulnerables[['id', 'tipus', 'vulnerabilitat', 'geometry']].reset_index(drop=True),
    right_df=urb[['NOM', 'geometry']].reset_index(drop=True),
    how='inner',
    predicate='within'
)

# 6. Crear resum per NOM i vulnerabilitat
summary = buildings_in_urb.groupby(['NOM', 'vulnerabilitat']).agg({
    'id': lambda x: ', '.join(map(str, x)),
    'tipus': lambda x: ', '.join(x),
    'vulnerabilitat': 'count'
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

# 8. Calcular total d'edificis
result_data['Total_edificis'] = (
    result_data['High_vuln_count'] + 
    result_data['Medium_vuln_count'] + 
    result_data['Low_vuln_count']
)

# 9. Guardar resultats
output_file = os.path.join(dataout, "Urbanitzacions_Vulnerabilitat_Detallat.shp")
result_data.to_file(output_file)

# 10. Mostrar resum
print("Resum d'edificis per vulnerabilitat:")
print(result_data[['NOM', 'High_vuln_count', 'Medium_vuln_count', 'Low_vuln_count', 'Total_edificis']].head())
print(f"\nFitxer guardat a: {output_file}")