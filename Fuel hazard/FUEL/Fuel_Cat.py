import geopandas as gpd
import pandas as pd
import os
from tqdm import tqdm  # Per a barra de progrés (opcional)

def main():
    # Configuració de paths (verifica que siguin correctes)
    DATA_DIR = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Urb_July/FUEL/'
    OUTPUT_DIR = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Urb_July/'
    
    print("⏳ Carregant dades...")
    try:
        # Carrega les dades amb verificació explícita
        fuel_path = os.path.join(DATA_DIR, 'Fuel_all.geojson')
        urb_path = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/RAW_URB_J_25/CRS_URB_J_25.shp'
        
        if not os.path.exists(fuel_path):
            raise FileNotFoundError(f"No s'ha trobat el fitxer {fuel_path}")
        if not os.path.exists(urb_path):
            raise FileNotFoundError(f"No s'ha trobat el fitxer {urb_path}")
        
        fuel = gpd.read_file(fuel_path)
        urb = gpd.read_file(urb_path)
        
        print("✅ Dades carregades correctament")
        print(f"📊 Polígons de vegetació: {len(fuel)}")
        print(f"🏘️ Urbanitzacions: {len(urb)}")
    except Exception as e:
        print(f"❌ Error en carregar dades: {str(e)}")
        return

    # Verificació de CRS (imprescindible)
    print("\n🔍 Verificant sistemes de coordenades...")
    print(f"CRS vegetació: {fuel.crs}")
    print(f"CRS urbanitzacions: {urb.crs}")
    
    if fuel.crs != urb.crs:
        print("⚠️ CRS diferents, convertint urbanitzacions...")
        urb = urb.to_crs(fuel.crs)
        print(f"➡️ Nou CRS urbanitzacions: {urb.crs}")

    # Verificació de columnes necessàries
    REQUIRED_FUEL_COLS = ['geometry', 'V_A', 'ID', 'ICat']
    REQUIRED_URB_COLS = ['ID', 'geometry', 'Shape_Area']
    
    missing_fuel_cols = [col for col in REQUIRED_FUEL_COLS if col not in fuel.columns]
    missing_urb_cols = [col for col in REQUIRED_URB_COLS if col not in urb.columns]
    
    if missing_fuel_cols:
        print(f"❌ Falten columnes a vegetació: {missing_fuel_cols}")
        return
    if missing_urb_cols:
        print(f"❌ Falten columnes a urbanitzacions: {missing_urb_cols}")
        return
    
    print("✅ Estructura de dades correcta")

    # Processament principal
    print("\n🔧 Calculant interseccions precises...")
    results = []
    
    # Utilitza tqdm per a barra de progrés (opcional)
    for _, urbanitzacio in tqdm(urb.iterrows(), total=len(urb)):
        try:
            # 1. Intersecció precisa
            fuel['intersection'] = fuel.geometry.intersection(urbanitzacio.geometry)
            fuel['intersect_area'] = fuel['intersection'].area
            
            # 2. Filtrar interseccions significatives (>1m²)
            valid = fuel[fuel['intersect_area'] > 1].copy()
            
            if len(valid) == 0:
                results.append({
                    'ID': urbanitzacio['ID'],
                    'ICat_urb': 0,
                    'total_V_A': 0,
                    'NOM': urbanitzacio.get('NOM', '')
                })
                continue
            
            # 3. Càlcul ponderat
            valid['weighted'] = valid['ICat'] * valid['intersect_area']
            total_weight = valid['weighted'].sum()
            total_area = valid['intersect_area'].sum()
            
            results.append({
                'ID': urbanitzacio['ID'],
                'ICat_urb': int(round(total_weight / total_area)),
                'total_V_A': total_area,
                'NOM': urbanitzacio.get('NOM', '')
            })
        except Exception as e:
            print(f"⚠️ Error processant urbanització ID {urbanitzacio['ID']}: {str(e)}")
            continue

    # Verificació de resultats
    if not results:
        print("❌ No s'han generat resultats")
        return
    
    print(f"\n📋 Resultats generats per {len(results)} urbanitzacions")
    
    # Crear DataFrame amb resultats
    result_df = pd.DataFrame(results)
    
    # Fusionar amb dades originals
    final = urb.merge(result_df, on='ID', how='left')
    
    # Guardar resultats
    output_path = os.path.join(OUTPUT_DIR, "FCat_urb.shp")
    try:
        final.to_file(output_path)
        print(f"\n💾 Resultat guardat a: {output_path}")
        
        # Verificació específica per Cal Sendró
        if 'NOM' in final.columns:
            cal_sendro = final[final['NOM'] == 'Cal Sendró']
            if not cal_sendro.empty:
                print("\n🔎 Verificació per Cal Sendró:")
                print(f"Àrea calculada: {cal_sendro['total_V_A'].values[0]:.2f} m²")
                print(f"ICat_urb: {cal_sendro['ICat_urb'].values[0]}")
            else:
                print("\n⚠️ No s'ha trobat Cal Sendró als resultats")
    except Exception as e:
        print(f"❌ Error en guardar resultats: {str(e)}")

if __name__ == "__main__":
    main()
    print("\n🏁 Procés finalitzat")