#%% Load Packages
import ForestFireNetherlands as FFN
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import ForestFireNetherlands.handler.geopandas as ngpd
import ForestFireNetherlands.handler.calculations as calc

import os
import numpy as np
from shapely.geometry import Point, MultiPoint
from rasterio.mask import mask
from rasterio.windows import get_data_window
import rasterio


import pyproj
import pandas as pd
import geopandas

# pathname = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\MODIS\\OriginalData"
pathname = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\VIIRS\\OriginalData"
os.chdir(pathname)

#%% Loading Corina file 
raster_pathname = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\NederlandCorine.tif"
raster = SatelliteDataService.get_satellite_object_raster(raster_pathname)

#%% Loads the borders of the Netherlands
shapefile_the_netherlands = geopandas.read_file("C:\\Users\\Coen\\Documents\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\shapefile_border_netherlands\\bordernetherlands.shp")

#%% Load txt files from MODIS and VIIRS to txt
files = os.listdir()
satellite_data_files = []

# Path where to save the files
# save_map_raster = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\MODIS\\ParsedRasterData" # MODIS
save_map_raster = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\VIIRS\\ParsedRasterData" # VIIRS
# save_map_shapefile = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\MODIS\\ParsedShapeFile" # MODIS
save_map_shapefile = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\VIIRS\\ParsedShapeFile" # VIIRS

delimiter_modis = " " # MODIS
delimiter_viirs = "," # VIIRS 750m

longitude = [3.2 ,7.22] # max and min longitude of the Netherlands in degrees based on EPSG:28992
latitude = [50.75, 53.7] # max and min latitude of the Netherlands in degrees based on EPSG:28992

# Sets if the file is Modis or VIIRS file 
satellite = "VIIRS"


for filename in files:
    delimiter = None

    if satellite == "VIIRS":
        delimiter = delimiter_viirs
    elif satellite == "MODIS":
        delimiter == delimiter_modis

    satellite_data = SatelliteDataService.get_satellite_object_txt(filepath=filename, 
                                                                    delimiter=delimiter)
    
    # Data filter
    longitude_query = 'lon > ' + str(longitude[0]) + ' and lon < ' + str(longitude[-1])
    latitude_query = 'lat > ' + str(latitude[0]) + ' and lat < ' + str(latitude[-1])
    satellite_data.query(longitude_query + ' and ' + latitude_query, inplace = True)

    # Adds shapes
    satellite_data['geometry'] = satellite_data.apply(lambda x: Point((float(x.lon), float(x.lat))), axis=1)

    # Masks and make the right projection from the data
    shapefile = geopandas.GeoDataFrame(satellite_data, geometry='geometry', crs=pyproj.CRS('EPSG:4326'))
    shapefile = shapefile.to_crs(pyproj.CRS('EPSG:28992'))
    joined_shapefile = geopandas.tools.sjoin(shapefile, shapefile_the_netherlands, how="left")
    shapefile = shapefile[joined_shapefile["Landsnaam"] == "Nederland"]
    print(shapefile)
    if (len(shapefile.geometry) == 0):
        print("No pixels")
        continue

    pixel_sizes = None

    # Calculates The corners of the area
    if satellite == "VIIRS":
        row_measurements = 3200
        pixel_nadir = 0.750 # km
        satellite_altitude = 833 # km
        pixel_sizes = calc.calculatesPixelSizeVIIRS(shapefile["sample"], pixel_nadir, row_measurements)
    elif satellite == "MODIS":
        row_measurements = 1354
        pixel_nadir = 1 # km
        satellite_altitude = 705 # km
        scan_angle = calc.calculatesScanAngleMODIS(amount_row_measurements = row_measurements, height= satellite_altitude, pixel_nadir= pixel_nadir, row_number = np.array(shapefile["sample"]))
        pixel_sizes = calc.calculatesPixelSizeMODIS(scan_angle, satellite_altitude, pixel_nadir)
        
        
    # Convert the pixels size from km to meters
    pixel_sizes["delta_scanline"] = pixel_sizes["delta_scanline"] * 1000
    pixel_sizes["delta_trackline"] = pixel_sizes["delta_trackline"] * 1000

    # Makes multipoints from the size
    geometry = np.array(shapefile.geometry)
    new_geometry = []
    
    for index in range(len(shapefile.geometry)):
        leftupper_point = Point(geometry[index].x - pixel_sizes["delta_scanline"][index] / 2, geometry[index].y + pixel_sizes["delta_trackline"][index] / 2)
        rightdown_point = Point(geometry[index].x + pixel_sizes["delta_scanline"][index] / 2, geometry[index].y - pixel_sizes["delta_trackline"][index] / 2)
        new_geometry.append(MultiPoint(points=[leftupper_point, rightdown_point]).envelope)
    
    # Makes pixel from the points
    shapefile.geometry = np.array(new_geometry)

    # Save the data shape per day
    combined_shapefile = ngpd.unary_union_by_day(shapefile, 'EPSG:28992')

    # Add dates       
    transformation_data = []
    
    masked_data, transformation_meta = mask(raster, combined_shapefile.geometry, crop=False, nodata=None)
    out_meta = raster.meta.copy()

    window = get_data_window(raster.read(1, masked=True))
    out_meta.update({"driver": "GTiff",
                     "count": masked_data.shape[0],
                     "height": masked_data.shape[1],
                     "width": masked_data.shape[2],
                     "transform": transformation_meta })

    # Saving rasterdata to correct map
    with rasterio.open(save_map_raster + "\\landuse_" + filename[:-4] + ".tif", "w", **out_meta) as dest:
        dest.write(masked_data)
    
    # Saving Shapefile
    combined_shapefile.to_file(save_map_shapefile + "\\burned_areas_" + filename[:-4] + ".shp")
    del masked_data


# %%
