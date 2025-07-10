import geopandas as gpd
import osmnx as ox
import matplotlib.pyplot as plt
from shapely.geometry import LineString

# Configuració
ox.settings.log_console = True
ox.settings.timeout = 600

# Carrega dades
data_path = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Capes PC/Delimitacio_v1.shp'

urb = gpd.read_file(data_path).to_crs("EPSG:25831")

# Paleta de colors millorada
tipus_vies = {
    'motorway|motorway_link': ('#8e44ad', 2.5, 'Autopista'),
    'primary|primary_link': ('#e74c3c', 2.0, 'Principal'),
    'secondary|secondary_link': ('#f39c12', 1.5, 'Secundària'),
    'tertiary|tertiary_link': ('#f1c40f', 1.2, 'Terciària'),
    'residential': ('#95a5a6', 0.8, 'Residencial'),
    'service': ('#3498db', 0.6, 'Servei'),
    'unclassified': ('#2ecc71', 0.8, 'No classificada')  # Verd més viu
}

for i, row in urb.iterrows():
    try:
        print(f"\nPolígon {i+1}/{len(urb)} - Processant...")
        
        # Creem un GeoDataFrame temporal amb el polígon actual
        poly_gdf = gpd.GeoDataFrame(geometry=[row.geometry], crs=urb.crs)
        
        # Conversió a WGS84 per a la consulta
        poly_wgs84 = poly_gdf.to_crs("EPSG:4326").geometry.iloc[0]
        
        # Obtenció de vies
        gdf_vies = ox.features_from_polygon(
            poly_wgs84,
            tags={'highway': True}
        ).to_crs(urb.crs)  # Tornem al CRS original
        
        # Neteja de geometries
        gdf_vies = gdf_vies[gdf_vies.geometry.notna()]
        gdf_vies = gdf_vies[gdf_vies.geometry.type.isin(['LineString', 'MultiLineString'])]
        
        # Preparació del gràfic
        fig, ax = plt.subplots(figsize=(12, 12), facecolor='white')
        poly_gdf.plot(ax=ax, color='#ecf0f1', edgecolor='#bdc3c7')
        
        # Dibuixat per categories
        for pattern, (color, amplada, etiqueta) in tipus_vies.items():
            mask = gdf_vies['highway'].astype(str).str.contains(pattern, na=False)
            if mask.any():
                temp = gdf_vies[mask].copy()
                temp['geometry'] = temp['geometry'].apply(
                    lambda g: g if g.type == 'LineString' else 
                    LineString([p for line in g.geoms for p in line.coords]))
                temp.plot(ax=ax, color=color, linewidth=amplada, label=etiqueta)
        
        # Elements del gràfic
        ax.set_title(f"Distribució viària - Àrea {i+1}", pad=20, fontsize=14)
        ax.legend(title="Llegenda", frameon=True, facecolor='white')
        ax.axis('off')
        
        # Guardar
        plt.savefig(f"fig_xarxa_viaria/Mapa_{i+1}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Mapa {i+1} generat correctament")
        
    except Exception as e:
        print(f"Error en polígon {i+1}: {str(e)}")