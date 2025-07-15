import geopandas as gpd


indir = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/RAW_URB_J_25/' 

delim = gpd.read_file(indir +"RAW_URB_J_25.shp")
# Assigna el CRS correcte (substitueix 'EPSG:25831' pel teu CRS si és diferent)
delim = delim.set_crs("EPSG:25831", allow_override=True)

delim.to_file(indir+'CRS_URB_J_25.shp')