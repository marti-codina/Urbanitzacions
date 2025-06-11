import geopandas as gpd
import tools

if __name__ == '__main__':

    indir = 'C:/Users/marti.codina/Nextcloud/2025 - FIRE-SCENE (subcontract)/METODOLOGIA URBANITZACIONS WUI/Capes GIS/Aggregation_index/data/usol/'
    ptdx = 2   # resolució del mostreig
    dbox = 50. # mida de la caixa d'anàlisi

    idxclc = range(1, 6)
    for iv in idxclc:
        print(f'Calculant AI: fuel cat {iv} ...')
        fuelCat = gpd.read_file(f'{indir}fuelCategory{iv}.geojson')

        fuelCat = tools.add_AI2gdf(fuelCat, ptdx=ptdx, dbox=dbox)

        fuelCat.to_file(f'{indir}fuelCategory{iv}_v2.geojson', driver='GeoJSON')

    print('Fet.')
