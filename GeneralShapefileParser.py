"""
Parse the txt files of VIIRS and MODIS from the ftp database to a shapefile with filtered pixels
VNP14IMG resolution = 375 m
VNP14 resolution = 750 m 
MODIS res = 1 km 
"""

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
# pathname = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\VIIRS750M\\OriginalData"
pathname = "F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\VIIRS375M\\OriginalData"

os.chdir(pathname)

#%% Loads the borders of the Netherlands
shapefile_the_netherlands = geopandas.read_file("C:\\Users\\Coen\\Documents\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\shapefile_border_netherlands\\bordernetherlands.shp")

#%% Load txt files from MODIS and VIIRS to txt
files = os.listdir()
satellite_data_files = []

# Path where to save the files
save_map_shapefile = "F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\VIIRS375M\\ParsedShapeFile" # VIIRS 375M
delimiter_modis = " " # MODIS
delimiter_viirs = "," # VIIRS 750m

longitude = [3.2 ,7.22] # max and min longitude of the Netherlands in degrees based on EPSG:28992
latitude = [50.75, 53.7] # max and min latitude of the Netherlands in degrees based on EPSG:28992

# Sets if the file is Modis or VIIRS file 
# satellite = "MODIS"
satellite = "VIIRS"

final_shapefile = None

for filename in files:
    print(filename)
    delimiter = None

    if satellite == "VIIRS":
        delimiter = delimiter_viirs
    elif satellite == "MODIS":
        delimiter = delimiter_modis

    satellite_data = SatelliteDataService.get_satellite_object_txt(filepath=filename, 
                                                                    delimiter=delimiter)

    # Filtering based on the location
    longitude_query = 'lon > ' + str(longitude[0]) + ' and lon < ' + str(longitude[-1])
    latitude_query = 'lat > ' + str(latitude[0]) + ' and lat < ' + str(latitude[-1])
    satellite_data.query(longitude_query + ' and ' + latitude_query, inplace = True)

    # Filtering based on type
    satellite_data.query('type == 0', inplace = True) # Type 0 = presumed vegetation data

    # checks 
    if satellite_data.empty:
        print("No fire pixels")
        continue

    # Change pixel area to m^2
    satellite_data.pixarea = satellite_data.pixarea * (1000 ** 2)
    print(satellite_data)
    # Makes the longitude and the latitude to a point
    satellite_data['geometry'] = satellite_data.apply(lambda x: Point((float(x.lon), float(x.lat))), axis=1)

    # Masks and make the right projection from the data
    shapefile = geopandas.GeoDataFrame(satellite_data, geometry='geometry', crs=pyproj.CRS('EPSG:4326'))
    shapefile = shapefile.to_crs(pyproj.CRS('EPSG:28992'))
    joined_shapefile = geopandas.tools.sjoin(shapefile, shapefile_the_netherlands, how="left")
    shapefile = shapefile[joined_shapefile["Landsnaam"] == "Nederland"]

    if (len(shapefile.geometry) == 0):
        print("No pixels")
        continue

    pixel_sizes = None

    # Calculates The corners of the area
    if satellite == "VIIRS":
        row_measurements = 3200
        pixel_nadir = 0.750 # km
        satellite_altitude = 833 # km
        if "375" in pathname:
            pixel_nadir = 0.375
            row_measurements = 6400

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
    # combined_shapefile = ngpd.unary_union_by_day(shapefile, 'EPSG:28992')
    filename = filename.split(".")

    shapefile = pd.DataFrame({
        "area": shapefile.pixarea, 
        "year": filename[1][:4], 
        "month": filename[1][4:], 
        "geometry": shapefile.geometry 
    })
    
    # Adds to dataframe 
    if final_shapefile is None:
        final_shapefile = geopandas.GeoDataFrame(shapefile, geometry=shapefile.geometry, crs=pyproj.CRS('EPSG:28992'))
    else:
        final_shapefile = final_shapefile.append(geopandas.GeoDataFrame(shapefile, geometry=shapefile.geometry))

# Saving Shapefile
final_shapefile.to_file(save_map_shapefile + "\\burned_areas_MODIS.shp")

# %%
