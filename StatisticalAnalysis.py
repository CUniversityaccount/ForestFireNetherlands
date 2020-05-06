# %% LOADING THE FILES
import rasterio
import geopandas as gpd
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import os
import numpy as np

base_dictiornary = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project"
os.chdir(base_dictiornary)
list_raster_modis = os.listdir(base_dictiornary + "\\Files\\MODIS\\ParsedRasterData")
list_shapefile_modis = os.listdir(base_dictiornary + "\\Files\\MODIS\\ParsedShapeFile")
list_shapefile_modis = [file for file in list_shapefile_modis if file.endswith(".shp")]

# %% RASTER ANALYSIS

# %% SHAPEFILE ANALYSIS