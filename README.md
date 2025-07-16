## Explicació de càlcul de cadascun dels paràmetres:

A continuació es detallen quins fitxers cal executar per calcular els defierents paràmetres de les urbanitzacions. **_Tingues en comte que potser s'hauran de canviar les localitzacions/noms dels fitxers._** 

# WUI Type:
   Fitxer WUI_predominant.py 
   Input: capa polígons urbanitzacions i capa vectorial WUI alcasena
   Outpt: WUI Pilot

   Fitxer WUI_mean no és bo ja que en calcular a la mitjana si per exemple, hi ha categories 2 i 4 dona categoria 3
   
# Fuel hazard Index:
Vegetation type:
Per obtenir el tipus de vegetació e caa urbanitació cal seguir els seguents passos
1) load-usol-category.py (crea una capa per cada categoria de comustible dines els límits de les urbanitzacions)
2) ConcatFuels.py
3) Fuel_Cat.py
  
# Aggregation Index:
Carpeta fragstats, executar els fitxers en l'ordre:
1) Geotiff_class.py
2) re-scale.py
3) batch.py
4) Executar el batch a fragstats
   *Passos*: Obrir fragstats-> file->Open -> MeRODOLOGIA URBANITZACIONS WUI/CAPES GIS/Urb_July/AI/fragastats_ready -> Import batch -> run
   *Nota*: ja hi ha configurat el nom i camí del fotxer de sortida (C:\Users\marti.codina\Nextcloud\2025 - FIRE-SCENE (subcontract)\METODOLOGIA URBANITZACIONS WUI\Capes GIS\Urb_July\AI\URB_AI_results) pestanya analisys parameters -> Automaticaly save results
5) getAI_urb.py


# Topographic complexity:
1) Executar el fitxer TPI

Population:
1) executar Edi_count.py

# Vulnerability:
Dades: Geofabrik (15/07/2025)  
