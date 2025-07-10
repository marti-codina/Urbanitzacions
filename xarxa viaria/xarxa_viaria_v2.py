import geopandas as gpd
import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# Configuració
ox.settings.log_console = True
ox.settings.timeout = 300
ox.settings.default_crs = "EPSG:4326"

# Carrega el fitxer amb múltiples polígons
data_path = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Capes PC/Delimitacio_v1.shp'
urb = gpd.read_file(data_path).to_crs("EPSG:4326")

# Defineix colors per tipus de via (personalitzable)
tipus_vies = {
    'residential': 'gray',
    'secondary': 'orange',
    'primary': 'red',
    'motorway': 'purple',
    'service': 'blue',
    'unclassified': 'green'
}

# Processa cada polígon
for i, polygon in enumerate(urb.geometry):
    try:
        print(f"\nProcessant polígon {i+1}/{len(urb)}...")
        
        # Obtenció de la xarxa
        xarxa = ox.graph_from_polygon(
            polygon,
            network_type='drive',
            simplify=True,
            truncate_by_edge=True,
            custom_filter='["highway"~"residential|secondary|primary|motorway|service|unclassified"]'
        )
        
        if len(xarxa.nodes()) == 0:
            print(f"  No s'han trobat vies per al polígon {i+1}")
            continue
        
        # Classifica les vies per tipus
        gdf_edges = ox.graph_to_gdfs(xarxa, nodes=False)
        gdf_edges['color'] = gdf_edges['highway'].apply(
            lambda x: next((color for tipo, color in tipus_vies.items() if tipo in str(x)), 'black'))
        
        # Visualització
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # Fons: polígon actual
        gpd.GeoSeries([polygon]).plot(ax=ax, color='lightgray', edgecolor='blue', alpha=0.3)
        
        # Dibuixa les vies per tipus (amb colors)
        for tipo, color in tipus_vies.items():
            edges = gdf_edges[gdf_edges['highway'].str.contains(tipo, na=False)]
            if not edges.empty:
                edges.plot(ax=ax, color=color, linewidth=1.5, label=tipo.capitalize())
        
        # Llegenda i títol
        ax.legend(title="Tipus de via")
        ax.set_title(f"Polígon {i+1}: {len(xarxa.nodes())} nodes, {len(xarxa.edges())} arestes")
        plt.tight_layout()
        
        # Guarda el gràfic
        plt.savefig(f"poligon_{i+1}_xarxa.png", dpi=300)
        plt.close()
        print(f"  Gràfic guardat com 'poligon_{i+1}_xarxa.png'")
        
    except Exception as e:
        print(f"  Error en el polígon {i+1}: {str(e)}")

print("\nProcessament completat!")