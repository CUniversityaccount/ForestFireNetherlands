#%% Load Packages
import ForestFireNetherlands as FFN
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import ForestFireNetherlands.handler.geopandas as ngpd

import os
import numpy as np
from shapely.geometry import Point
from rasterio.mask import mask
from rasterio.windows import get_data_window
import rasterio


import pyproj
import pandas as pd
import geopandas

pathname = "C:\\Users\\Coen\\Documents\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files"
os.chdir(pathname)

#%% Loading Corina file 
raster_pathname = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\NederlandCorine.tif"
raster = SatelliteDataService.get_satellite_object_raster(raster_pathname)

#%% Loads the borders of the Netherlands
shapefile_the_netherlands = geopandas.read_file("C:\\Users\\Coen\\Documents\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\shapefile_border_netherlands\\bordernetherlands.shp")

#%% Load txt files from MODIS and VIIRS to txt
files = os.listdir()[5:6]
satellite_data_files = []

# Path where to save the files
save_map = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\MODIS\\ParsedRasterData"

delimiter_modis = " " # MODIS
delimiter_viirs = "," # VIIRS

longitude = [3.2 ,7.22] # max and min longitude of the Netherlands in degrees based on EPSG:28992
latitude = [50.75, 53.7] # max and min latitude of the Netherlands in degrees based on EPSG:28992
print
for filename in files:
    satellite_data = SatelliteDataService.get_satellite_object_txt(filepath=filename, 
                                                                   delimiter=delimiter_modis)

    # Data filter
    longitude_query = 'lon > ' + str(longitude[0]) + ' and lon < ' + str(longitude[-1])
    latitude_query = 'lat > ' + str(latitude[0]) + ' and lat < ' + str(latitude[-1])
    satellite_data.query(longitude_query + ' and ' + latitude_query, inplace = True)

    # Adds shapes
    satellite_data['geometry'] = satellite_data.apply(lambda x: Point((float(x.lon), float(x.lat))), axis=1)

    # Manipulates the data to pixel with a resolutio of wich is declared in size
    shapefile = geopandas.GeoDataFrame(satellite_data, geometry='geometry', crs=pyproj.CRS('EPSG:4326'))
    shapefile = shapefile.to_crs(pyproj.CRS('EPSG:28992'))
    joined_shapefile = geopandas.tools.sjoin(shapefile, shapefile_the_netherlands, how="left")
    shapefile = shapefile[joined_shapefile["Landsnaam"] == "Nederland"]
    shapefile.geometry = shapefile.geometry.buffer(500) # buffer in meters
    shapefile.geometry = shapefile.envelope

    # Save the data shape per day
    combined_shapefile = ngpd.unary_union_by_day(shapefile, "yyyymmdd", 'EPSG:28992')
    
    masked_data = None
    transformation_data = []

    for polygon in combined_shapefile.geometry:
        filtered_data = None
        transform_meta = None 

        if polygon.geom_type == 'MultiPolygon':
            filtered_data, transform_meta = mask(raster, polygon, crop = False, nodata=None)

        elif polygon.geom_type == 'Polygon':
            filtered_data, transform_meta = mask(raster, [polygon], crop = False, nodata=None)

        if masked_data is None: 
            masked_data = filtered_data
        else: 
            masked_data = np.vstack((masked_data, filtered_data))
    print(raster.transform)
    out_meta = raster.meta.copy()
    window = get_data_window(raster.read(1, masked=True))
    out_meta.update({"driver": "GTiff",
                     "count": masked_data.shape[0],
                     "height": masked_data.shape[1],
                     "width": masked_data.shape[2],
                     "transform": rasterio.windows.transform(window, raster.transform)})

    with rasterio.open(save_map + "\\landuse_" + filename[:-4] + ".tif", "w", **out_meta) as dest:
        dest.write(masked_data)
    
    del masked_data
    

# %%
