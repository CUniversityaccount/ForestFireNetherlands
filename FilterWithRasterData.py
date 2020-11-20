# %% LOADING THE FILES AND LIBRARIES
import rasterio
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import os
import uuid

import numpy as np
from rasterio.mask import mask
import pyproj


def shapefile_list_parser(list_files):
    return [file for file in list_files if "burned" in file and file.endswith(".shp")]


base_dictiornary = "F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project"
os.chdir(base_dictiornary)

modis_shapefile_path = base_dictiornary + "\\Files\\MODIS\\ParsedShapeFile"
viirs_shapefile_path_375m = base_dictiornary + \
    "\\Files\\VIIRS375M\\ParsedShapefile"

files_of_viirs_375m = os.listdir(viirs_shapefile_path_375m)
list_shapefile_viirs_small = shapefile_list_parser(files_of_viirs_375m)

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
            shapefile_loaded_all = shapefile_loaded_all.append(
                shapefile_loaded)

    return shapefile_loaded_all


# shapefiles_loaded_viirs_big = loading_shapefiles(shapefiles=list_shapefile_viirs_big, path=viirs_shapefile_path_big)
shapefiles_loaded_viirs_small = loading_shapefiles(
    shapefiles=list_shapefile_viirs_small, path=viirs_shapefile_path_375m)
# shapefiles_loaded_modis = loading_shapefiles(shapefiles=list_shapefile_modis, path=modis_shapefile_path)


# %% LOADS THE NETHERLANDS RASTERFILE
raster_pathname = "F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\NederlandCorine.tif"
landcover_the_netherlands = rasterio.open(raster_pathname)

# %% CHECKS IF THE PIXEL HAS BEEN A FIRE


def filter_pixels_with_land_cover_data(dataframe_polygons, raster, upper_boundary=None, lower_boundary=None):
    """
    Sorts the data on basis of the most prominent pixels which are selected on basis of the upper and lower boundary
    """

    sorted_data = pd.DataFrame(data=None, columns=dataframe_polygons.columns)

    for index, polygon in dataframe_polygons.iterrows():

        raster_data, transformation_meta = mask(
            raster, [polygon.geometry], crop=True)
        raster_data = np.squeeze(raster_data)
        raster_mask_boundaries = ((raster_data > 0) & (raster_data < 500))

        raster_data = raster_data[raster_mask_boundaries]

        if raster_data.size == 0:
            print("The pixel has only water")
            continue

        # First checks if there is any city or industrial in the pixel, because then it is unsure if the fire was an wild or natural fire
        if (any(raster_data < 200)):
            continue

        # Get the most frequent land_cover in the values
        (land_cover_values, counts) = np.unique(
            raster_data, return_counts=True)
        land_cover_mask = (counts == np.max(counts))

        if (all(land_cover_values < 300) or all(land_cover_values[land_cover_mask] < 300)):
            continue

        # Same problem as the urban filter
        if (land_cover_values[land_cover_mask].size > 1 and any(land_cover_values < 300)):
            print("Unsure if it is nature or agriculture")
            continue

        polygon['id'] = str(uuid.uuid4())

        # Nature qualifications by Corine Land Cover (CLC)
        if (all(land_cover_values[land_cover_mask] > 310) and all(land_cover_values[land_cover_mask] < 320)):
            polygon['firetype'] = 'forest'
        elif (all(land_cover_values[land_cover_mask] > 320) and all(land_cover_values[land_cover_mask] < 330)):
            polygon['firetype'] = 'heath'
        elif (all(land_cover_values[land_cover_mask] == 331)):
            polygon['firetype'] = 'dune'
        elif (all(land_cover_values[land_cover_mask] > 410) and all(land_cover_values[land_cover_mask] < 420)):
            polygon['firetype'] = 'peat'
        elif (len(land_cover_values[land_cover_mask]) > 1 and all((land_cover_values > 300) & (land_cover_values < 332))):
            polygon['firetype'] = 'combined nature'

        if 'firetype' in list(polygon.keys()):
            print("Polygon added")
            sorted_data = sorted_data.append(polygon)

        # if len(data_filtered) > total_cells:
        #     sorted_data = sorted_data.append(polygon)

    return sorted_data


shapefiles_loaded_viirs_375m = filter_pixels_with_land_cover_data(dataframe_polygons=shapefiles_loaded_viirs_small,
                                                                  raster=landcover_the_netherlands,
                                                                  lower_boundary=100,
                                                                  upper_boundary=200)
# shapefiles_loaded_viirs_big =  filter_pixels_with_land_cover_data(dataframe_polygons=shapefiles_loaded_viirs_big,
#                                             raster=landcover_the_netherlands,
#                                             lower_boundary=100,
#                                             upper_boundary=200)
# shapefiles_loaded_modis =  filter_pixels_with_land_cover_data(dataframe_polygons=shapefiles_loaded_modis,
#                                             raster=landcover_the_netherlands,
#                                             lower_boundary=100,
#                                             upper_boundary=200)
# gpd.GeoDataFrame(shapefiles_loaded_viirs_big, geometry=shapefiles_loaded_viirs_big.geometry, crs=pyproj.CRS('EPSG:28992')).to_file(viirs_shapefile_path_big + "//filtered_pixels_VIIRS_750M.shp")
gpd.GeoDataFrame(shapefiles_loaded_viirs_375m, geometry=shapefiles_loaded_viirs_375m.geometry, crs=pyproj.CRS(
    'EPSG:28992')).to_file(viirs_shapefile_path_375m + "//filtered_pixels_VIIRS_375M_v2.shp")
# gpd.GeoDataFrame(shapefiles_loaded_modis, geometry=shapefiles_loaded_modis.geometry, crs=pyproj.CRS('EPSG:28992')).to_file(modis_shapefile_path + "//filtered_pixels_MODIS.shp")

# %%
