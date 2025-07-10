import geopandas as gpd
import osmnx as ox
import matplotlib.pyplot as plt
from shapely.geometry import LineString, MultiLineString, Point, MultiPoint
import networkx as nx
from itertools import combinations
import numpy as np
from sklearn.cluster import DBSCAN

def simplify_and_connect(gdf_vies, buffer_dist=3):
    """Simplifica la geometría y conecta segmentos cercanos"""
    # Simplificar geometrías a segmentos rectos
    gdf_vies['simple_geom'] = gdf_vies['geometry'].apply(
        lambda g: LineString([g.coords[0], g.coords[-1]]) if g.geom_type == 'LineString' else
        LineString([list(g.geoms)[0].coords[0], list(g.geoms)[-1].coords[-1]])
    )
    
    # Extraer todos los puntos extremos
    endpoints = []
    for geom in gdf_vies['simple_geom']:
        endpoints.extend([geom.coords[0], geom.coords[-1]])
    
    # Convertir a array para DBSCAN
    coords = np.array(endpoints)
    
    # Agrupar puntos cercanos (buffer_dist en unidades CRS, metros para EPSG:25831)
    db = DBSCAN(eps=buffer_dist, min_samples=1).fit(coords)
    labels = db.labels_
    
    # Crear diccionario de mapeo de puntos a clusters
    cluster_centers = {}
    for label in set(labels):
        if label != -1:
            cluster_points = coords[labels == label]
            cluster_centers[label] = tuple(np.mean(cluster_points, axis=0))
    
    # Reemplazar coordenadas por sus centros de cluster
    new_coords = [cluster_centers[label] for label in labels]
    
    # Reconstruir geometrías con nodos conectados
    new_geoms = []
    for geom in gdf_vies['simple_geom']:
        start = geom.coords[0]
        end = geom.coords[-1]
        
        # Encontrar los nuevos puntos para este segmento
        start_idx = endpoints.index(start)
        end_idx = endpoints.index(end)
        
        new_start = new_coords[start_idx]
        new_end = new_coords[end_idx]
        
        new_geoms.append(LineString([new_start, new_end]))
    
    gdf_vies['connected_geom'] = new_geoms
    return gdf_vies, cluster_centers.values()

def plot_schematic_diagram(gdf_vies, output_path, buffer_dist=3):
    fig, ax = plt.subplots(figsize=(10, 10), facecolor='white')
    
    # Procesar geometrías y conexiones
    gdf_vies, cluster_points = simplify_and_connect(gdf_vies, buffer_dist)
    
    # Crear grafo
    G = nx.Graph()
    
    # Añadir aristas
    for idx, row in gdf_vies.iterrows():
        geom = row['connected_geom']
        start = (geom.coords[0][0], geom.coords[0][1])
        end = (geom.coords[-1][0], geom.coords[-1][1])
        G.add_edge(start, end)
    
    # Dibujar conexiones
    for edge in G.edges():
        x = [edge[0][0], edge[1][0]]
        y = [edge[0][1], edge[1][1]]
        ax.plot(x, y, 'k-', linewidth=1.5, alpha=0.7)
    
    # Identificar nodos
    node_degrees = dict(G.degree())
    
    # Cul-de-sac (grado 1 y no cerca de otros nodos)
    cul_de_sac = []
    for node, degree in node_degrees.items():
        if degree == 1:
            # Verificar que no está cerca de otros nodos (excepto su conexión)
            is_isolated = True
            connected_node = next(iter(G[node]))
            for other_node in G.nodes():
                if other_node != node and other_node != connected_node:
                    dist = Point(node).distance(Point(other_node))
                    if dist < buffer_dist * 2:  # Umbral más estricto
                        is_isolated = False
                        break
            if is_isolated:
                cul_de_sac.append(node)
    
    if cul_de_sac:
        x, y = zip(*cul_de_sac)
        ax.scatter(x, y, c='red', s=50, label='Cul-de-sac', zorder=5)
    
    # Intersecciones (grado >= 3 o grado 2 con ángulo agudo)
    intersections = []
    for node, degree in node_degrees.items():
        if degree >= 3:
            intersections.append(node)
        elif degree == 2:
            neighbors = list(G.neighbors(node))
            p1 = Point(neighbors[0])
            p2 = Point(node)
            p3 = Point(neighbors[1])
            
            # Calcular ángulo
            v1 = (p1.x - p2.x, p1.y - p2.y)
            v2 = (p3.x - p2.x, p3.y - p2.y)
            dot = v1[0]*v2[0] + v1[1]*v2[1]
            det = v1[0]*v2[1] - v1[1]*v2[0]
            angle = np.abs(np.arctan2(det, dot))
            
            if angle < np.pi/2:  # Ángulo agudo
                intersections.append(node)
    
    if intersections:
        x, y = zip(*intersections)
        ax.scatter(x, y, c='blue', s=50, label='Intersección', zorder=5)
    
    # Circuitos
    try:
        triangles = [c for c in nx.cycle_basis(G) if len(c) == 3]
        for triangle in triangles:
            x, y = zip(*triangle)
            x = list(x) + [x[0]]
            y = list(y) + [y[0]]
            ax.fill(x, y, alpha=0.2, color='green')
    except:
        pass
    
    # Configuración
    ax.set_title(f"Diagrama Esquemático (Buffer: {buffer_dist}m)", pad=20, fontsize=14)
    ax.legend(title="Elementos", frameon=True, facecolor='white')
    ax.axis('equal')
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

# Carga datos y procesamiento (igual que antes)
data_path = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Capes PC/Delimitacio_v1.shp'
urb = gpd.read_file(data_path).to_crs("EPSG:25831")

for i, row in urb.iterrows():
    try:
        print(f"\nPolígon {i+1}/{len(urb)} - Processant...")
        
        poly_gdf = gpd.GeoDataFrame(geometry=[row.geometry], crs=urb.crs)
        poly_wgs84 = poly_gdf.to_crs("EPSG:4326").geometry.iloc[0]
        
        gdf_vies = ox.features_from_polygon(
            poly_wgs84,
            tags={'highway': True}
        ).to_crs(urb.crs)
        
        gdf_vies = gdf_vies[gdf_vies.geometry.notna()]
        gdf_vies = gdf_vies[gdf_vies.geometry.type.isin(['LineString', 'MultiLineString'])]
        
        # Generar diagrama con buffer de conexión de 3 metros
        plot_schematic_diagram(gdf_vies, f"fig_xarxa_viaria/Diagrama_Esquematico_{i+1}.png", buffer_dist=3)
        print(f"Diagrama esquemático {i+1} generado correctamente")
        
    except Exception as e:
        print(f"Error en polígon {i+1}: {str(e)}")