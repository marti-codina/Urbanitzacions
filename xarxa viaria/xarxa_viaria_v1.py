import geopandas as gpd
import osmnx as ox
import matplotlib.pyplot as plt

# Configuració inicial
ox.settings.log_console = True
ox.settings.timeout = 300
ox.settings.cache_folder = "cache_osmnx"  # Directori específic per a la memòria cau

# Carrega el shapefile
data_path = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Capes PC/Delimitacio_v1.shp'
urb = gpd.read_file(data_path)

# Verifica el CRS i reprojecta si cal
if urb.crs is None:
    urb = urb.set_crs("EPSG:4326", allow_override=True)
elif urb.crs != "EPSG:4326":
    urb = urb.to_crs("EPSG:4326")

# Obtenir el polígon
polygon = urb.geometry.iloc[0]

# Configuració específica per a àrees petites
config = {
    'truncate_by_edge': True,
    'simplify': True,
    'retain_all': False,
    'clean_periphery': True
}

# Obtenir la xarxa viària
try:
    xarxa = ox.graph_from_polygon(polygon, network_type='drive', **config)
    
    # Visualització millorada
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Plot del polígon de fons
    urb.plot(ax=ax, color='lightgray', edgecolor='blue', alpha=0.3)
    
    # Plot de la xarxa
    ox.plot_graph(
        xarxa,
        ax=ax,
        node_color='red',
        node_size=20,
        edge_color='black',
        edge_linewidth=1,
        show=False,
        close=False
    )
    
    # Afegir títol i llegenda
    ax.set_title(f"Xarxa viària de la urbanització\n{len(xarxa.nodes())} nodes, {len(xarxa.edges())} arestes")
    plt.tight_layout()
    plt.show()
    
    # Exportar resultats
    ox.save_graph_geopackage(xarxa, filepath='xarxa_viaria.gpkg')
    print("Exportació completada: xarxa_viaria.gpkg")
    
except Exception as e:
    print(f"Error principal: {e}")
    print("Provant mètode alternatiu...")
    
    # Opció alternativa
    try:
        gdf_vies = ox.features_from_polygon(polygon, tags={'highway': True})
        if not gdf_vies.empty:
            fig, ax = plt.subplots(figsize=(12, 12))
            urb.plot(ax=ax, color='lightgray', edgecolor='blue', alpha=0.3)
            gdf_vies.plot(ax=ax, color='black', linewidth=1)
            ax.set_title("Vies obtingudes amb mètode alternatiu")
            plt.show()
        else:
            print("No s'han trobat vies dins del polígon")
    except Exception as e2:
        print(f"Error alternatiu: {e2}")