import pandas as pd
import geopandas as gpd
import os

# 1. Carregar les capes
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
dataout = data

# Load data with selected columns
URB = gpd.read_file(data + 'RAW_URB_J_25/CRS_URB_J_25.shp', 
                   columns=['ID', 'NOM', 'TIPUS', 'CODIMUNI', 'NOMMUNI', 'NOMCOMAR', 'NOMVEGUE', 'NOMPROV', 'INE5','Shape_Area', 'AREA', 'geometry'])

WUI = gpd.read_file(data + 'Urb_July/WUI_July_pred.shp', columns=['ID', 'DN_dominan'])
WUI = WUI.rename(columns={'DN_dominan': 'WUI_type'})  # Primer fem el rename
FH = gpd.read_file(data + 'Urb_July/FH_URB.shp', 
                    columns=['ID', 'total_V_A', 'AI', 'AI_cat', 'veg_%', 'ICat_urb', 'Fuel_H'])
EDI = gpd.read_file(data + 'Urb_July/EDI_URB.shp', columns=['ID', 'num_edific'])

# 2. Fer les unions selectives mantenint la geometria original de URB
capa_final = URB.copy()

# Llista de capes i atributs a fusionar
capes_a_fusionar = [
    (WUI, ['WUI_type']),
    (FH, ['total_V_A', 'AI', 'AI_cat', 'veg_%', 'ICat_urb', 'Fuel_H']),
    (EDI, ['num_edific'])
]

# Verificar que les columnes existeixen abans de fusionar
print("Columnes a WUI:", WUI.columns.tolist())
print("Columnes a FH:", FH.columns.tolist())
print("Columnes a EDI:", EDI.columns.tolist())

for capa, atributs in capes_a_fusionar:
    # Verificar que els atributs existeixen a la capa
    for attr in atributs:
        if attr not in capa.columns:
            raise ValueError(f"L'atribut '{attr}' no existeix a la capa {capa.iloc[0,:].geometry.type}")
    
    # Seleccionar només els atributs necessaris (incloent 'ID' per la fusió)
    cols = ['ID'] + atributs
    capa_final = capa_final.merge(
        capa[cols],
        on='ID',
        how='left',  # Conserva totes les entrades de la capa base
        suffixes=('', f'_{capa.iloc[0,:].geometry.type.lower()}')  # Sufix identificatiu
    )

# 3. Neteja de columnes potencialment duplicades
capa_final = capa_final.loc[:, ~capa_final.columns.duplicated()]

# 4. Verificació dels resultats
print("\nColumnes finals:", capa_final.columns.tolist())
print("Nombre d'entrades:", len(capa_final))
print("Geometria conservada?", capa_final.geometry.equals(URB.geometry))

# 5. Guardar els resultats
# Shapefile
output_shp = os.path.join(dataout, "URB_integrated.shp")
capa_final.to_file(output_shp)
print(f"\nShapefile guardat a: {output_shp}")

# Excel (sense geometria)
output_excel = os.path.join(dataout, "URB_integrated_attributes.xlsx")
pd.DataFrame(capa_final.drop(columns='geometry')).to_excel(output_excel, index=False)
print(f"Excel amb atributs guardat a: {output_excel}")