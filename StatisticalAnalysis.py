# %% LOADING THE FILES
import rasterio
import geopandas as gpd
import pandas as pd
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import os
import numpy as np

base_dictiornary = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project"
os.chdir(base_dictiornary)

modis_raster_path = base_dictiornary + "\\Files\\MODIS\\ParsedRasterData"
modis_shapefile_path = base_dictiornary + "\\Files\\MODIS\\ParsedShapeFile"
list_raster_modis = os.listdir(modis_raster_path)
list_shapefile_modis = os.listdir(modis_shapefile_path)
list_shapefile_modis = [file for file in list_shapefile_modis if file.endswith(".shp")]

# %% Legend Data
legend = pd.read_csv('E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\Legend\\CLC2018_CLC2018_V2018_20_QGIS.txt', sep=",", header=None)
legend.columns = ["id", "greyscale", "r", "g", "b", "description"]

 # %% RASTER ANALYSIS
statistical_raster_data = {}

analysis_dataframe = pd.DataFrame(columns = ["year", "month", "raster"]) 
for file in list_raster_modis[:3]:
    month = file.split(".")[1][-2:]

    if month not in statistical_raster_data.keys():
        statistical_raster_data[month] = {}

    raster = SatelliteDataService.get_satellite_object_raster(modis_raster_path + "\\" +  file)
    raster_data = raster.read()
    land_cover_classes = np.unique(raster_data[raster_data > 0])

    
    for land_cover_class in land_cover_classes:
        count_land_cover = np.sum(land_cover_class == raster_data)
    
    

# %% SHAPEFILE ANALYSIS