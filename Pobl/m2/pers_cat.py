import pandas as pd

# 1. Carregar dades
data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/'
EDI = pd.read_csv(data + 'Població/t15681.csv', encoding='utf-8-sig')
POB = pd.read_csv(data + 'Població/t15224.csv', encoding='utf-8-sig')

# 2. Netejar dades
# Per EDI (edificis)

EDI = EDI.rename(columns={EDI.columns[0]: 'comarca'})

# Per POB (població)

POB = POB.rename(columns={POB.columns[0]: 'comarca', 'Valor': 'poblacio'})
POB['comarca'] = POB['comarca'].str.replace('"', '').str.strip()

# 3. Definir intervals fixos (en m²)
intervals = {
    '30': 30,
    '45': 45, 
    '75': 75,
    '105': 105,
    '135': 135,
    '165': 165,
    '180': 180
}

# 4. Calcular superfície mitjana ponderada per comarca
def calcular_mitjana_ponderada(fila):
    total_habitatges = 0
    total_m2 = 0
    
    for col, m2 in intervals.items():
        if col in fila.index:
            num_hab = fila[col]
            total_habitatges += num_hab
            total_m2 += num_hab * m2
    
    return total_m2 / total_habitatges if total_habitatges > 0 else 0

EDI['mitjana_ponderada'] = EDI.apply(calcular_mitjana_ponderada, axis=1)

# 5. Assignar mitjana ponderada a "No hi consta" i calcular area_total
if 'No hi consta' in EDI.columns:
    EDI['area_no_consta'] = EDI['No hi consta'] * EDI['mitjana_ponderada']
    
    # Calcular area_total (sumant tots els intervals coneguts + l'assignat a "No hi consta")
    area_intervals = sum(EDI[col].astype(float) * m2 for col, m2 in intervals.items() if col in EDI.columns)
    EDI['area_total'] = area_intervals + EDI['area_no_consta']
else:
    # Cas que no hi hagi columna "No hi consta"
    EDI['area_total'] = sum(EDI[col].astype(float) * m2 for col, m2 in intervals.items() if col in EDI.columns)

# 6. Fusionar amb població i calcular densitat
resultat = pd.merge(
    EDI[['comarca', 'area_total', 'mitjana_ponderada']],
    POB[['comarca', 'poblacio']],
    on='comarca',
    how='inner'
)

resultat['metre_pers'] = resultat['area_total'] / resultat['poblacio']

# 7. Mostrar resultats
print("Superfície mitjana ponderada per comarca:")
print(resultat[['comarca', 'mitjana_ponderada', 'area_total', 'poblacio', 'metre_pers']]
      .sort_values('metre_pers', ascending=False))

# 8. Guardar resultats
resultat.to_csv(data + 'resultat_densitat_ponderat.csv', index=False, encoding='utf-8-sig')