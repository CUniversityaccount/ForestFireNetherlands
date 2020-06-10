# %% LOADING THE FILES AND LIBRARIES
import rasterio
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import os

import numpy as np
from rasterio.mask import mask
import pyproj

def shapefile_list_parser(list_files):
    return [file for file in list_files if "burned" in file and file.endswith(".shp")]
    
base_dictiornary = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project"
os.chdir(base_dictiornary)

modis_shapefile_path = base_dictiornary + "\\Files\\MODIS\\ParsedShapeFile"
viirs_shapefile_path_big = base_dictiornary + "\\Files\\VIIRS750M\\ParsedShapefile"
viirs_shapefile_path_small = base_dictiornary + "\\Files\\VIIRS375M\\ParsedShapefile"

list_shapefile_modis = os.listdir(modis_shapefile_path)
list_shapefile_modis = shapefile_list_parser(list_shapefile_modis)

list_shapefile_viirs_big = os.listdir(viirs_shapefile_path_big)
list_shapefile_viirs_big = shapefile_list_parser(list_shapefile_viirs_big)

list_shapefile_viirs_small = os.listdir(viirs_shapefile_path_small)
list_shapefile_viirs_small = shapefile_list_parser(list_shapefile_viirs_small)

# %% SHAPEFILE ANALYSIS
def loading_shapefiles(shapefiles, path):

    shapefile_loaded_all = None    

    for shapefile in shapefiles:
        print(shapefile)
        
        # Masks and make the right projection from the data
        shapefile_loaded = gpd.read_file(path + "\\" + shapefile)

        if shapefile_loaded_all is None:
            shapefile_loaded_all = shapefile_loaded
        else:
            shapefile_loaded_all = shapefile_loaded_all.append(shapefile_loaded)            
    
    return shapefile_loaded_all

shapefiles_loaded_viirs_big = loading_shapefiles(shapefiles=list_shapefile_viirs_big, path=viirs_shapefile_path_big)
shapefiles_loaded_viirs_small = loading_shapefiles(shapefiles=list_shapefile_viirs_small, path=viirs_shapefile_path_small)
shapefiles_loaded_modis = loading_shapefiles(shapefiles=list_shapefile_modis, path=modis_shapefile_path)


# %% LOADS THE NETHERLANDS RASTERFILE
raster_pathname = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\NederlandCorine.tif"
landcover_the_netherlands = rasterio.open(raster_pathname)

# %% CHECKS IF THE PIXEL HAS BEEN A FIRE
def sort_pixel_value(dataframe_polygons, raster, upper_boundary = None, lower_boundary = None):
    """
    Sorts the data on basis of the most prominent pixels which are selected on basis of the upper and lower boundary
    """

    sorted_data = pd.DataFrame(data=None, columns=dataframe_polygons.columns)

    for index, polygon in dataframe_polygons.iterrows():
        raster_data, transformation_meta = mask(raster, [polygon.geometry], crop=True)
        raster_data = np.squeeze(raster_data)
        
        # Alls cels with no data
        total_cells = len(raster_data.flatten()) / 2
        raster_mask = ((raster_data > 500) | (raster_data < 0))
        
        if lower_boundary is not None and upper_boundary is not None:
            raster_mask_boundaries = ((raster_data > lower_boundary) & (raster_data < upper_boundary))
            raster_mask = (raster_mask | raster_mask_boundaries)
   
        data_filtered = raster_data[~raster_mask]
        
        if len(data_filtered) > total_cells:
            sorted_data = sorted_data.append(polygon)

    return sorted_data

shapefiles_loaded_viirs_small =  sort_pixel_value(dataframe_polygons=shapefiles_loaded_viirs_small, 
                                            raster=landcover_the_netherlands, 
                                            lower_boundary=100, 
                                            upper_boundary=200)
shapefiles_loaded_viirs_big =  sort_pixel_value(dataframe_polygons=shapefiles_loaded_viirs_big, 
                                            raster=landcover_the_netherlands, 
                                            lower_boundary=100, 
                                            upper_boundary=200)
shapefiles_loaded_modis =  sort_pixel_value(dataframe_polygons=shapefiles_loaded_modis, 
                                            raster=landcover_the_netherlands, 
                                            lower_boundary=100, 
                                            upper_boundary=200)


# %%
gpd.GeoDataFrame(shapefiles_loaded_viirs_big, geometry=shapefiles_loaded_viirs_big.geometry, crs=pyproj.CRS('EPSG:28992')).to_file(viirs_shapefile_path_big + "//filtered_pixels_VIIRS_750M.shp")
gpd.GeoDataFrame(shapefiles_loaded_viirs_small, geometry=shapefiles_loaded_viirs_small.geometry, crs=pyproj.CRS('EPSG:28992')).to_file(viirs_shapefile_path_small + "//filtered_pixels_VIIRS_375M.shp")
gpd.GeoDataFrame(shapefiles_loaded_modis, geometry=shapefiles_loaded_modis.geometry, crs=pyproj.CRS('EPSG:28992')).to_file(modis_shapefile_path + "//filtered_pixels_MODIS.shp")

# %%
