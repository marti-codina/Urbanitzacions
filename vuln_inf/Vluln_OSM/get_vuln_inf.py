import numpy as np 
import pyrosm 
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
import glob 
import sys
from scipy import ndimage, stats, spatial
import sys
from shapely.geometry import box
import pandas as pd
import geopandas as gpd
import os
import glob 
import warnings
from shapely.errors import ShapelyDeprecationWarning
import pdb 
from shapely.validation import make_valid, explain_validity

data = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/"
dataout = data + "Urb_July/VULN/"

osm = pyrosm.OSM(data + "cataluna-latest.osm.pbf")

# 2. Obtenir edificis amb les etiquetes específiques
# Definim els filtres per a cada categoria
amenity_filters = {
    "amenity": ["college", "kindergarten", "research_institute", "school", 
                "university", "clinic", "dentist", "doctors", "hospital", 
                "nursing_home", "social_facility", "fuel"]
}

tourism_filter = {"tourism": True}  # Agafem tots els edificis amb qualsevol etiqueta tourism

industrial_filters = {
    "industrial": ["oil", "wellsite", "fracking", "chemical", 
                   "electrical", "refinery"]
}

leisure_filters = {
    "leisure": ["summer_camp", "fitness_centre", "pitch", "resort", "sports_centre", "sports_hall", "stadium"]
}

areoway_filters = {
    "aeroway" : ["tower"]
}

manmade_filters = {
    "man_made" : ["communications_tower"]
}
generator_filters = {"power" : True }




# Obtenir els edificis per a cada filtre
buildings_amenity = osm.get_buildings(custom_filter=amenity_filters)
buildings_tourism = osm.get_buildings(custom_filter=tourism_filter)
buildings_industrial = osm.get_buildings(custom_filter=industrial_filters)
buildings_leisure = osm.get_buildings(custom_filter=leisure_filters)
buildings_aeroway = osm.get_buildings(custom_filter=areoway_filters)
buildings_manmade = osm.get_buildings(custom_filter=manmade_filters)
buildings_generator = osm.get_buildings(custom_filter=generator_filters)

# 3. Combinar totes les geometries en un sol GeoDataFrame
# Afegim una columna 'category' per identificar el tipus
buildings_amenity['category'] = 'amenity'
buildings_tourism['category'] = 'tourism'
buildings_industrial['category'] = 'industrial'
buildings_leisure['category'] = 'leisure'
buildings_aeroway['category'] = 'aeroway'
buildings_manmade['category'] = 'manmade'
buildings_generator['category'] = 'power'

# Concatenem totes les capes
all_buildings = gpd.GeoDataFrame(
    pd.concat([buildings_amenity, buildings_tourism, buildings_industrial, buildings_leisure, buildings_aeroway, buildings_manmade, buildings_generator], 
              ignore_index=True),
    crs=buildings_amenity.crs
)

# 4. Netejar i preparar les dades
# Eliminem duplicats si n'hi ha
#all_buildings = all_buildings.drop_duplicates(subset=['osm_id'])

# Seleccionem columnes rellevants (opcional)
columns_to_keep = ['name', 'category', 'amenity', 'tourism', 'industrial', 'leisure', 'aeroway', 'man_made', 'generator', 'geometry']
all_buildings = all_buildings[[col for col in columns_to_keep if col in all_buildings.columns]]

# 5. Guardar com a Shapefile
all_buildings.to_file(dataout + "edificis_vuln.gpkg", driver = 'GPKG')