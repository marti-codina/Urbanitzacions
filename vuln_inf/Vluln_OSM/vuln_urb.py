import geopandas as gpd
import pandas as pd
import os


data = "C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/"

vuln = gpd.read_file (data + "Urb_July/VULN/edificis_vuln.gpkg")
urb = gpd.read_file (data + "RAW_URB_J_25/CRS_URB_J_25.gpkg")

