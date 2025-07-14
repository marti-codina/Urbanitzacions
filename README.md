Explicació de càlcul de cadascun dels paràmetres:

Interfície
   Fitxer WUI_CLASS.py 
   Input: capa polígons urbanitzacions i capa vectorial WUI alcasena
   Outpt: WUI Pilot
   
Fuel hazard Index:
Vegetation type:
Per obtenir el tipus de vegetació e caa urbanitació cal seguir els seguents passos
1) load-usol-category.py (crea una capa per cada categoria de comustible dines els límits de les urbanitzacions)
2) ConcatFuels.py
3) Fuel_Cat.py
  
Aggregation Index:
Carpeta fragstats, executar els fitxers en l'ordre:
1) Geotiff_class.py
2) re-scale.py
3) batch.py
4) Executar el batch a fragstats
5) getAI_urb.py


Topographic complexity
1) Executar el fitxer TPI

Population
   
