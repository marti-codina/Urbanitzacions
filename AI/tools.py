import sys
import os 
import pandas as pd
import geopandas as gpd
import shapely 
import numpy as np 
from matplotlib import pyplot as plt
from shapely.geometry import Polygon
from sklearn.cluster import AgglomerativeClustering
import multiprocessing
import pdb 
import warnings
#warnings.filterwarnings("error")
import pyproj
import importlib 
from rasterio.warp import calculate_default_transform, reproject, Resampling
import socket

#homebrwed
sys.path.append('../data/')
glc = importlib.import_module("load-usol-category")



########################
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

dir_data = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Aggregation_index/data/usol/'


##########################
def my_read_file(filepath):
    if os.path.isfile(filepath.replace('.geojson','.prj')):
        tmp = gpd.read_file(filepath)
        with open(filepath.replace('.geojson','.prj'),'r') as f:
            lines = f.readlines()
        try:
            tmp.set_crs(crs=lines[0], allow_override=True, inplace=True)
        except: 
            pdb.set_trace()
        return tmp
    else:
        return gpd.read_file(filepath)


##########################
##########################
def cpu_count():
    return multiprocessing.cpu_count()


##########################
def dist2FuelCat(indir,fuelCat, indus):
    
    bb = 1.e4 # 10 km
    nbregroup = indus['group'].max() +1
    for ig in range(0, nbregroup):
        #print('group {:d}/{:d} ... '.format(ig,nbregroup),end='\r')
        indus_ = indus.loc[indus['group']==ig]
        #print(indus_.shape)
        xmin, ymin, xmax, ymax = indus_.total_bounds
        
        fuelCat_ = fuelCat.cx[xmin-bb:xmax+bb, ymin-bb:ymax+bb]
        #print('sub fuelCat size', fuelCat_.shape)
        #fuelCat_ = dissolveGeometryWithinBuffer(fuelCat_,20) #only important for osm fuel data
        #print('compute distance')
        dist2fuelCat_ = getDistanceBetweenGdf(indus_,fuelCat_)
        pdb.set_trace()
        #fuelCat_ = None
        

        if ig == 0: 
            dist2fuelCat = dist2fuelCat_
        else:
            dist2fuelCat = pd.concat([dist2fuelCat, dist2fuelCat_])
    #print('done                 ') 
  
    mindist = dist2fuelCat.min(axis=1).sort_index()
    minPolyIdx = dist2fuelCat.idxmin(axis=1).sort_index()

    return mindist, minPolyIdx



##########################
def star_AIpoly(param):
    return AIpoly(*param)

def AIpoly(gdf, ipo, ptdx = 2, dbox = 20., PoverA=0.05):

    poly = gdf[ipo:ipo+1]
    
    minx,miny,maxx,maxy = poly.total_bounds
    xx = np.arange(minx,maxx+ptdx,ptdx)
    yy = np.arange(miny,maxy+ptdx,ptdx)
    ptsy, ptsx = np.meshgrid(yy,xx)
    
    gpts = gpd.GeoDataFrame(crs=poly.crs, geometry=[shapely.geometry.Point(x,y) for x,y in zip(ptsx.flatten(), ptsy.flatten())] )
    
    gpts2 = gpd.sjoin(gpts, poly, predicate = 'within')
    
    if gpts2.shape[0] == 0: 
        return 0 # poylgon was not catched by ptdx resolution, assume it is too small to have effect

    boxminx, boxminy, boxmaxx, boxmaxy = gpts2.total_bounds
    gdf_local = gdf.cx[boxminx-2*dbox:boxmaxx+2*dbox, boxminy-2*dbox:boxmaxy+2*dbox]

    AIpt = []
    for ipt in range(gpts2.shape[0]):
        
        pt = gpts2[ipt:ipt+1]
        
        x_= pt.geometry.iloc[0].coords.xy[0][0]
        y_= pt.geometry.iloc[0].coords.xy[1][0]
        boxx = [x_-dbox/2, x_+dbox/2, x_+dbox/2, x_-dbox/2,x_-dbox/2]
        boxy = [y_-dbox/2, y_-dbox/2, y_+dbox/2, y_+dbox/2,y_-dbox/2]
        box = gpd.GeoDataFrame(crs=poly.crs, geometry=[ shapely.geometry.Polygon(zip(boxx,boxy)) ] )

        gdf_box = gpd.overlay(gdf_local, box, how = 'intersection', keep_geom_type=False)
        
        Abox = (dbox**2)*1.e-4

        A    = gdf_box.area.sum()/1.e4   # total area ha of the selected polygon
        if A > .8*Abox : 
            AIpt.append(1)
            break 
        elif A < .1*Abox : 
            AIpt.append(0)
        else:
            P    = gdf_box.length.sum() * 1.e-3 # total perimeter km of the selected polygon
            #PoverA = 0.05 #max([0.04,P/A])
            A_unit = ptdx**2 * 1.e-4# ha
            S_unit = PoverA * A_unit*1.e4 #  m   square S_unit = 0.04 A_unit
            Pmax = S_unit * ( A /(A_unit) ) * 1.e-3
            Pmin = 2 * np.pi * np.sqrt(1.e4*A/np.pi) / 1.e3
            AIpt.append( 1 - (P-Pmin)/(Pmax-Pmin) ) #Boegart et al 2002 https://sites.bu.edu/cliveg/files/2013/12/jbogaert02.pdf

            #if P>Pmax : print(AIpt[-1], Pmax, P, Pmin, A/Abox, P/A*1.e-1)

            if AIpt[-1] == 1: break

    return max(AIpt)


##########################
def add_AI2gdf(gdf, ptdx=2, dbox=20, PoverA=0.05):
    """
    Calculate Aggregation Index (AI) for polygons (serial mode for small datasets).
    Args:
        gdf (GeoDataFrame): Input geometries
        ptdx (int): Sampling resolution (meters)
        dbox (float): Analysis box size (meters)
        PoverA (float): Perimeter/Area ratio threshold
    """
    results = []
    for ipo in range(gdf.shape[0]):
        # Progress tracking
        progress = 100 * (ipo + 1) / gdf.shape[0]
        print(f"\rProgress: {progress:.1f}%", end="")
        sys.stdout.flush()
        
        # Compute AI for single polygon
        result = star_AIpoly([gdf, ipo, ptdx, dbox, PoverA])
        results.append(result)
    
    gdf['AI'] = results
    print("\nDone!")  # Newline after progress
    return gdf


###########################################################
def reproject_raster(src_band, src_bounds, src_transform, src_crs, dst_crs, resolution=200):
    dst_transform, width, height = calculate_default_transform(
        src_crs,
        dst_crs,
        src_band.shape[1],
        src_band.shape[2],
        *src_bounds,  # unpacks outer boundaries (left, bottom, right, top)
        resolution=resolution
    )
    dst_band = np.zeros([height, width])

    try: 
        return  reproject(
        source=src_band,
        destination=dst_band,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        dst_nodata=-999,
        resampling=Resampling.nearest)
    except:
        pdb.set_trace()


##########################
if __name__ == '__main__':
    gdf = gpd.read_file('./gdf-testCat1.geojson')
    dbox = 200.
    ptdx = 10

    mm_ = add_AI2gdf(gdf, ptdx=ptdx, dbox=dbox)
    plt.hist(mm_['AI'], 20, label=f'{ptdx} m')
    
    plt.legend()
    plt.title('Distribució de l\'índex d\'agregació')
    plt.xlabel('AI')
    plt.ylabel('Freqüència')
    plt.show()

    #indir = '/mnt/dataEstrella/OSM/FuelCategories/'
    #wood = gpd.read_file(indir+'wood.shp')

    #wood_geom = dissolveGeometryWithinBuffer(wood)

    #distancesIntraWood = getDistanceBetweenGdf(wood_geom,wood_geom)
    