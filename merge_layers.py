import geopandas as gpd
import os

# 1. Carregar les capes
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = data

# Load data with selected columns
URB = gpd.read_file(data + 'Capes PC/Delimitacio_v1.shp', 
                   columns=['NOM', 'MUN_INE', 'CODI', 'TIPUS', 'MUNICIPI', 'COMARCA', 'mapid', 'OBSERVACAIO', 'Area', 'geometry'])

WUI = gpd.read_file(data + 'WUI_pilot.shp', columns=['NOM', 'DN_URB'])
AI = gpd.read_file(data + 'urb_AI.shp', columns=['NOM', 'new_index']).rename(columns={'new_index':'Hazard_MC'})
POBL = gpd.read_file(data + 'urban_areas_with_population_corrected.shp', 
                    columns=['NOM', 'building_c', 'URB_TOT', 'URB_HOME', 'URB_DONA', 'URB_VELL'])
TPI = gpd.read_file(data + 'URB_TPI.shp', columns=['NOM', 'TPI'])
VULN = gpd.read_file(data + 'Urbanitzacions_Vulnerabilitat_Detallat.shp', columns=['NOM', 'High_vuln_', 'Medium_vul', 'Low_vuln_c', 'Total_edif'])  # Assumint que hi ha un camp 'VULNERAB'

# 2. Fer les unions selectives mantenint la geometria original de URB
capa_final = URB.copy()

# Llista de capes i atributs a fusionar (excloent 'NOM' que s'utilitza per fusionar)
capes_a_fusionar = [
    (WUI, ['DN_URB']), #Bo
    (AI, ['Hazard_MC']), #Bo
    (POBL, ['building_c', 'URB_TOT', 'URB_HOME', 'URB_DONA', 'URB_VELL']),
    (TPI, ['TPI']),
    (VULN, ['High_vuln_', 'Medium_vul', 'Low_vuln_c', 'Total_edif'])
]

for capa, atributs in capes_a_fusionar:
    # Seleccionar només els atributs necessaris (incloent 'NOM' per la fusió)
    cols = ['NOM'] + atributs
    capa_final = capa_final.merge(
        capa[cols],
        on='NOM',
        how='left',  # Conserva totes les entrades de la capa base
        suffixes=('', f'_{capa.iloc[0,:].geometry.type}')  # Sufix identificatiu
    )

# 3. Neteja de columnes potencialment duplicades
# (Mantenim la primera ocurrència de cada columna)
capa_final = capa_final.loc[:,~capa_final.columns.duplicated()]

# 4. Verificació dels resultats
print("Columnes finals:", capa_final.columns.tolist())
print("Nombre d'entrades:", len(capa_final))
print("Geometria conservada?", capa_final.geometry.equals(URB.geometry))  # Hauria de retornar True

# 5. Guardar el resultat
output_path = os.path.join(dataout, "URB_integrated.shp")
capa_final.to_file(output_path)
print(f"\nResultat guardat a: {output_path}")