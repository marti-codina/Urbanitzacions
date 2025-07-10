import geopandas as gpd
import osmnx as ox
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point
import networkx as nx
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.ops import linemerge

# Configuración
ox.settings.log_console = True
ox.settings.timeout = 600

# 1. Cargar datos de entrada
data_path = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Capes PC/Delimitacio_v1.shp'
urb = gpd.read_file(data_path).to_crs("EPSG:25831")

def prepare_geometries(gdf):
    """Converteix MultiLineString a LineString i fusiona segments connectats"""
    geometries = []
    for geom in gdf.geometry:
        if geom.geom_type == 'MultiLineString':
            # Fusionem totes les parts connectades
            merged = linemerge(geom)
            if merged.geom_type == 'LineString':
                geometries.append(merged)
            else:  # Si segueix sent MultiLineString, agafem cada part
                geometries.extend(list(merged.geoms))
        else:
            geometries.append(geom)
    return geometries

def build_topological_graph(geometries, buffer_dist=3):
    """Crea un graf topològic considerant proximitat espacial"""
    G = nx.Graph()
    all_points = []
    
    # Pass 1: Extraure tots els punts finals i intermedis rellevants
    for line in geometries:
        points = list(line.coords)
        # Afegim punts cada certa distància per capturar corbes
        if line.length > buffer_dist * 2:
            num_points = int(line.length / buffer_dist) + 1
            points = [line.interpolate(i/num_points).coords[0] for i in range(num_points + 1)]
        all_points.extend(points)
    
    # Pass 2: Agrupar punts propers amb DBSCAN
    coords = np.array(all_points)
    if len(coords) == 0:
        return G
    
    db = DBSCAN(eps=buffer_dist, min_samples=1).fit(coords)
    unique_labels = set(db.labels_)
    
    # Crear diccionari de centres de cluster
    cluster_centers = {
        label: tuple(np.mean(coords[db.labels_ == label], axis=0))
        for label in unique_labels if label != -1
    }
    
    # Pass 3: Reconnectar segments amb els nous nodes
    for line in geometries:
        # Trobar el cluster més proper per a cada extrem
        start = min(cluster_centers.keys(), 
                  key=lambda x: Point(cluster_centers[x]).distance(Point(line.coords[0])))
        end = min(cluster_centers.keys(), 
                key=lambda x: Point(cluster_centers[x]).distance(Point(line.coords[-1])))
        
        # Afegir connexió al graf
        G.add_edge(cluster_centers[start], cluster_centers[end])
    
    return G, cluster_centers

def plot_corrected_diagram(gdf_vies, output_path, buffer_dist=3):
    fig, ax = plt.subplots(figsize=(12, 12), facecolor='white')
    
    # Preparar geometries sense simplificació excessiva
    geometries = prepare_geometries(gdf_vies)
    
    # Construir graf amb connexió espacial
    G, nodes = build_topological_graph(geometries, buffer_dist)
    
    if len(G.edges()) == 0:
        print("No s'han trobat vies vàlides")
        return
    
    # Dibuixar les connexions
    for edge in G.edges():
        x, y = zip(*edge)
        ax.plot(x, y, 'k-', linewidth=1.5, alpha=0.7)
    
    # Identificar nodes correctament
    node_degrees = dict(G.degree())
    
    # Cul-de-sac reals (grau 1 i allunyats d'altres nodes)
    cul_de_sac = [
        node for node, degree in node_degrees.items() 
        if degree == 1 and all(
            Point(node).distance(Point(other)) > buffer_dist * 1.5
            for other in nodes.values() if other != node
        )
    ]
    
    # Interseccions (grau >=3 o canvis bruscos de direcció)
    intersections = [
        node for node, degree in node_degrees.items()
        if degree >= 3 or (
            degree == 2 and len(set(G.neighbors(node))) > 1  # Evita bucles simples
        )
    ]
    
    # Dibuixar elements
    if cul_de_sac:
        x, y = zip(*cul_de_sac)
        ax.scatter(x, y, c='red', s=80, label='Cul-de-sac', zorder=5)
    
    if intersections:
        x, y = zip(*intersections)
        ax.scatter(x, y, c='blue', s=80, label='Intersecció', zorder=5)
    
    # Configuració final
    ax.set_title(f"Diagrama Corregit\nDistància de connexió: {buffer_dist}m", 
                pad=20, fontsize=14)
    ax.legend(title="Elements", loc='upper right')
    ax.axis('equal')
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Diagrama guardat a {output_path}")


# 3. Procesamiento principal
for i, row in urb.iterrows():
    try:
        poly_gdf = gpd.GeoDataFrame(geometry=[row.geometry], crs=urb.crs)
        poly_wgs84 = poly_gdf.to_crs("EPSG:4326").geometry.iloc[0]
        
        gdf_vies = ox.features_from_polygon(
            poly_wgs84,
            tags={'highway': True}
        ).to_crs(urb.crs)
        
        gdf_vies = gdf_vies[gdf_vies.geometry.notna()]
        gdf_vies = gdf_vies[gdf_vies.geometry.type.isin(['LineString', 'MultiLineString'])]
        
        plot_corrected_diagram(gdf_vies, f"Diagrama_{i+1}.png", buffer_dist=3)
        
    except Exception as e:
        print(f"Error en polígon {i+1}: {str(e)}")