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

# 3. Filtrar només edificis vulnerables (excloem 'altres')
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

# 6. Crear strings concatenats per ID i tipus
concat_data = buildings_in_urb.groupby(['NOM', 'vulnerabilitat']).agg({
    'id': lambda x: ', '.join(map(str, x)),
    'tipus': lambda x: ', '.join(x)
}).unstack()

# Reorganitzar les columnes
concat_data.columns = [
    'High_vuln_ids', 'High_vuln_tipus',
    'Medium_vuln_ids', 'Medium_vuln_tipus',
    'Low_vuln_ids', 'Low_vuln_tipus'
]

# 7. Comptar edificis per vulnerabilitat
count_data = buildings_in_urb.groupby('NOM')['vulnerabilitat'].value_counts().unstack(fill_value=0)
count_data = count_data.rename(columns={
    'High': 'High_vuln_count',
    'Medium': 'Medium_vuln_count',
    'Low': 'Low_vuln_count'
})

# 8. Fusionar totes les dades
urb_with_vulnerability = urb.merge(
    count_data,
    on='NOM',
    how='left'
).merge(
    concat_data,
    on='NOM',
    how='left'
)

# 9. Omplir valors NaN
for col in ['High_vuln_count', 'Medium_vuln_count', 'Low_vuln_count',
            'High_vuln_ids', 'High_vuln_tipus',
            'Medium_vuln_ids', 'Medium_vuln_tipus',
            'Low_vuln_ids', 'Low_vuln_tipus']:
    if col.endswith('_count'):
        urb_with_vulnerability[col] = urb_with_vulnerability[col].fillna(0).astype(int)
    else:
        urb_with_vulnerability[col] = urb_with_vulnerability[col].fillna('')

# 10. Calcular total
urb_with_vulnerability['Total_edificis'] = (
    urb_with_vulnerability['High_vuln_count'] +
    urb_with_vulnerability['Medium_vuln_count'] +
    urb_with_vulnerability['Low_vuln_count']
)

# 11. Guardar resultats
output_file = os.path.join(dataout, "Urbanitzacions_Vulnerabilitat_Detallat.shp")
urb_with_vulnerability.to_file(output_file)

# 12. Mostrar resum
print("Resum d'edificis per vulnerabilitat:")
print(urb_with_vulnerability[['NOM', 'High_vuln_count', 'Medium_vuln_count', 'Low_vuln_count', 'Total_edificis']].head())
print(f"\nFitxer guardat a: {output_file}")