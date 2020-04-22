#%% Load Packages
import ForestFireNetherlands as FFN
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import os
import numpy as np


pathname = "C:\\Users\\Coen\\Documents\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files"
os.chdir(pathname)

#%% Loading Corina file 
raster_pathname = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\NederlandCorine.tif"
raster = SatelliteDataService.get_satellite_object_raster(raster_pathname)

#%% Load txt files from MODIS and VIIRS to txt
files = os.listdir()
satellite_data_files = []
selected_files = files[5:6]

for thing in files[5:6]: 
    delimiter = " "
    satellite_data_files.append(SatelliteDataService.get_satellite_object_txt(filepath=thing, delimiter=delimiter))
    
#%% Masking Script
longitude = [3.2 ,7.22] # max and min longitude of the Netherlands in degrees based on EPSG:28992
latitude = [50.75, 53.7] # max and min latitude of the Netherlands in degrees based on EPSG:28992
filtered_data = []

for satellite_data in satellite_data_files:
    longitude_query = 'lon > ' + str(longitude[0]) + ' and lon < ' + str(longitude[-1])
    latitude_query = 'lat > ' + str(latitude[0]) + ' and lat < ' + str(latitude[-1])

    satellite_data.query(longitude_query + ' and ' + latitude_query, inplace = True)
    filtered_data.append(satellite_data)


# %% Changing from txt to shp 

from shapely.geometry import Point

for satelite_data in filtered_data:
    satellite_data['geometry'] = satellite_data.apply(lambda x: Point((float(x.lon), float(x.lat))), axis=1)
    
# %% Changing to geopandas and buffer the points 
import geopandas
import pyproj

shapefile_the_netherlands = geopandas.read_file("C:\\Users\\Coen\\Documents\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\shapefile_border_netherlands\\bordernetherlands.shp")

shapefiles = []

for satellite_data in filtered_data:
    shapefile = geopandas.GeoDataFrame(satellite_data, geometry='geometry', crs=pyproj.CRS('EPSG:4326'))
    shapefile = shapefile.to_crs(pyproj.CRS('EPSG:28992'))
    
    joined_shapefile = geopandas.tools.sjoin(shapefile, shapefile_the_netherlands, how="left")
    shapefile = shapefile[joined_shapefile["Landsnaam"] == "Nederland"]
    shapefile.geometry = shapefile.geometry.buffer(500) # buffer in meters
    shapefile.geometry = shapefile.envelope
    shapefiles.append(shapefile)

# %% Plot the graph
import matplotlib.pyplot as plt
from rasterio.plot import show

fig, ax = plt.subplots()

# shapefile_the_netherlands.boundary.plot(ax=ax)
shapefiles[0].plot(ax=ax, color="red")
show(raster, ax=ax)
plt.axis("off")
plt.tight_layout()
plt.savefig("test.png", dpi=1000)

plt.show()  

# %%
