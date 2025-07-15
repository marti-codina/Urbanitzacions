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
dataout = data

osm = pyrosm.OSM(data + "cataluna-latest.osm.pbf")

custom_filter = {}