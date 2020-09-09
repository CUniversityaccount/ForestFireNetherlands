"""
This file is made for the visualization of the data.
Furthermore, it highlights different time scales 

"""
# %% IMPORT LIBRARIES
import rasterio
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import os
import numpy as np
from rasterio.mask import mask

# %% LOAD THE FILES
def shapefile_list_parser(list_files):
    return [file for file in list_files if file.endswith(".shp") and "filtered" in file]
    
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


# %% Legend Data
legend = pd.read_csv('E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\Legend\\CLC2018_CLC2018_V2018_20_QGIS.txt', sep=",", header=None)
legend.columns = ["id",  "r", "g", "b", "greyscale", "description"]

# %% LOADING SHAPEFILES
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


# %% ANALYSIS SURFACE SIZE

def yearly_burned_area(dataframe):
    """
    Before calling this function, the data set needs to be ordered by year. Good function hereby is groupby for pandas
    """
    parsed_years = {}
    for year, data in dataframe:
        total_burned_area = np.sum(data.area) / (1000**2) # km^2 
        parsed_years[year] = total_burned_area
    
    return parsed_years

viirs_big_yearly_burned_area = yearly_burned_area(dataframe=shapefiles_loaded_viirs_big.groupby("year"))
viirs_small_yearly_burned_area = yearly_burned_area(dataframe=shapefiles_loaded_viirs_small.groupby("year"))
modis_yearly_burned_area = yearly_burned_area(dataframe=shapefiles_loaded_modis.groupby("year"))

# %% LAND COVER 
def sum_effected_land_cover(dataframe, raster):

    parsed_years = {}

    for year, data in dataframe:

        # Get all the unique values from all the arrays
        selected_raster_data, meta = mask(raster, data.geometry, crop=True)
        filtered_raster_data = selected_raster_data[selected_raster_data > 0]
        landcover_values = np.unique(filtered_raster_data)
        data_sorted_landcover = {}

        for landcover_value in landcover_values:
            if landcover_value in data_sorted_landcover.keys():
                data_sorted_landcover[landcover_value] += len(filtered_raster_data[filtered_raster_data == landcover_value])
            else:
                data_sorted_landcover[landcover_value] = len(filtered_raster_data[filtered_raster_data == landcover_value])

        parsed_years[year] = data_sorted_landcover
    
    return parsed_years

viirs_big_yearly_burned_land_cover = sum_effected_land_cover(dataframe=shapefiles_loaded_viirs_big.groupby("year"), raster=landcover_the_netherlands)
viirs_small_yearly_burned_land_cover = sum_effected_land_cover(dataframe=shapefiles_loaded_viirs_small.groupby("year"), raster=landcover_the_netherlands)
modis_yearly_burned_land_cover = sum_effected_land_cover(dataframe=shapefiles_loaded_modis.groupby("year"), raster=landcover_the_netherlands)

# %% PLOT BURNED AREA AND 
fig, axs = plt.subplots(1, 1, figsize=(9, 3))
axs.plot(list(viirs_small_yearly_burned_area.keys()), list(viirs_small_yearly_burned_area.values()), label="VIIRS375M")
axs.plot(list(viirs_big_yearly_burned_area.keys()), list(viirs_big_yearly_burned_area.values()), label="VIIRS750M")
axs.plot(list(modis_yearly_burned_area.keys()), list(modis_yearly_burned_area.values()), label="MODIS")
axs.legend()
axs.set_ylabel("km^2")
axs.set_xlabel("Time")
fig.suptitle("Total Burned Area Yearly")
fig.savefig('burned_area_total_yearly_v1.png', bbox_inches="tight", dpi=400)

# %% PLOTS LAND COVER

fig, axs = plt.subplots(1, 3, figsize=(18, 9), sharey=True)
label_count = np.arange(len(viirs_big_yearly_burned_land_cover.keys())) + 1
width = 0.5

def bar_plot(satellite_data, legend, subplot):
    max_values = [] 

    # Gets the unique values of the satellite data
    for data in list(satellite_data.values()):
        max_values.extend(data)
    max_values = np.unique(np.array(max_values))

    bottom = None

    for count, value in enumerate(max_values):
        bar_values = []

        for land_cover_data in satellite_data.values():  
                   
            if value in land_cover_data:
                bar_values.append(land_cover_data[value])
            else: 
                bar_values.append(0) 

        color = legend.loc[legend["id"] == value]
        if (bottom is None):
            subplot.bar(label_count, np.array(bar_values), width, 
            color=[(list(color["r"])[0] / 255, list(color["g"])[0] / 255, list(color["b"])[0] / 255, 1)],
            label=list(color["description"])[0])
            bottom = np.array(bar_values)
        else:
            subplot.bar(label_count, np.array(bar_values), width, 
            color=[(list(color["r"])[0] / 255, list(color["g"])[0] / 255, list(color["b"])[0] / 255, 1)],
            label=list(color["description"])[0], bottom=bottom)
            bottom += np.array(bar_values)

    
    return subplot

axs[0] = bar_plot(viirs_small_yearly_burned_land_cover, legend, axs[0])    
axs[0].set_title("VIIRS 375M")
axs[0].set_xticks(label_count)
axs[0].set_xticklabels(list(viirs_small_yearly_burned_land_cover.keys()))

label_count = np.arange(len(viirs_big_yearly_burned_land_cover.keys())) + 1
axs[1] = bar_plot(viirs_big_yearly_burned_land_cover, legend, axs[1])
axs[1].set_title("VIIRS 750M")    
axs[1].set_xticks(label_count)
axs[1].set_xticklabels(list(viirs_big_yearly_burned_land_cover.keys()))

label_count = np.arange(len(modis_yearly_burned_land_cover.keys()))

axs[2] = bar_plot(modis_yearly_burned_land_cover, legend, axs[2])    
axs[2].set_title("MODIS")
axs[2].set_xticks(label_count)
axs[2].set_xticklabels(list(modis_yearly_burned_land_cover.keys()))
axs[2].legend(loc='center left', bbox_to_anchor=(1.0, 0.5))

fig.tight_layout()
fig.suptitle("Total LandCover yearly")
fig.savefig('land_cover_total_yearly_v1.png', bbox_inches="tight", dpi=300)


# %% MONTHLY ANALYSIS

# First attempt
def mean_landcover(dataframe, raster):
    
    parsed_keys = {}

    for key, data in dataframe:

        # Get all the unique values from all the arrays
        selected_raster_data, meta = mask(raster, data.geometry, crop=True)
        filtered_raster_data = selected_raster_data[selected_raster_data > 0]
        landcover_values = np.unique(filtered_raster_data)
        data_sorted_landcover = {}

        for landcover_value in landcover_values:
            if landcover_value in data_sorted_landcover.keys():
                data_sorted_landcover[landcover_value] += len(filtered_raster_data[filtered_raster_data == landcover_value])
            else:
                data_sorted_landcover[landcover_value] = len(filtered_raster_data[filtered_raster_data == landcover_value])

        parsed_keys[key] = data_sorted_landcover

    calculated_mean_data = {}
    for key, landcover in parsed_keys.items():
        new_values = {}
        
        for key, values in landcover.items():
            calculated_value = int(values) / len(dataframe.groups.keys())
            
            new_values[key] = calculated_value
        
        calculated_mean_data[key] = new_values
    
    return parsed_keys

viirs_small_monthly_mean_land_cover = mean_landcover(shapefiles_loaded_viirs_small.groupby("month"), raster=landcover_the_netherlands)
viirs_big_monthly_mean_land_cover = mean_landcover(shapefiles_loaded_viirs_big.groupby("month"), raster=landcover_the_netherlands)
modis_monthly_mean_land_cover = mean_landcover(shapefiles_loaded_modis.groupby("month"), raster=landcover_the_netherlands)

# %% Plots the monthly data
fig, axs = plt.subplots(1, 3, figsize=(18, 9), sharey=True)
label_count = np.arange(len(viirs_small_monthly_mean_land_cover.keys())) + 1
width = 0.5

axs[0] = bar_plot(viirs_small_monthly_mean_land_cover, legend, axs[0])    
axs[0].set_title("VIIRS 375M")
axs[0].set_xticks(label_count)
axs[0].set_xticklabels(list(viirs_small_monthly_mean_land_cover.keys()))

label_count = np.arange(len(viirs_big_monthly_mean_land_cover.keys())) + 1
axs[1] = bar_plot(viirs_big_monthly_mean_land_cover, legend, axs[1])
axs[1].set_title("VIIRS 750M")    
axs[1].set_xticks(label_count)
axs[1].set_xticklabels(list(viirs_big_monthly_mean_land_cover.keys()))

label_count = np.arange(len(modis_monthly_mean_land_cover.keys()))

axs[2] = bar_plot(modis_monthly_mean_land_cover, legend, axs[2])    
axs[2].set_title("MODIS")
axs[2].set_xticks(label_count)
axs[2].set_xticklabels(list(modis_monthly_mean_land_cover.keys()))
axs[2].legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
fig.suptitle("Mean Landcover Monthly")
fig.tight_layout()

fig.savefig('land_cover_mean_monthly_v1.png', bbox_inches="tight", dpi=300)

# %% MONTHLY BURNED AREA 
def mean_burned_area(dataframe):
    parsed_key = {}

    for key, data in dataframe:
        total_burned_area = np.sum(data.area) / (1000**2) # km^2 
        parsed_key[key] = total_burned_area
    
    for key, data in parsed_key.items():
        parsed_key[key] = parsed_key[key] / len(dataframe.groups.keys())

    return parsed_key

viirs_small_monthly_mean_burned_area = mean_burned_area(shapefiles_loaded_viirs_small.groupby("month"))
viirs_big_monthly_mean_burned_area = mean_burned_area(shapefiles_loaded_viirs_big.groupby("month"))
modis_monthly_burned_area = mean_burned_area(shapefiles_loaded_modis.groupby("month"))

# %% Plots the monthly average burned area

fig, axs = plt.subplots(1, 1, figsize=(9, 3))
axs.plot(list(viirs_small_monthly_mean_burned_area.keys()), list(viirs_small_monthly_mean_burned_area.values()), label="VIIRS375M")
axs.plot(list(viirs_big_monthly_mean_burned_area.keys()), list(viirs_big_monthly_mean_burned_area.values()), label="VIIRS750M")
axs.plot(list(modis_monthly_burned_area.keys()), list(modis_monthly_burned_area.values()), label="MODIS")
axs.legend()
fig.suptitle("Mean Burned Area monthly")
axs.set_ylabel("km^2")
axs.set_xlabel("Time")
fig.savefig('burned_area_mean_monthly_v1.png', bbox_inches="tight", dpi=300)


# %% Plots the distance of the fire spot to the road

shapefile_roads_and_railroads = gpd.read_file("E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\VIIRS375M\\Join_wegen\\VIIRS375M_Distance.shp")

plt.hist(shapefile_roads_and_railroads['distance'], bins=20)
plt.title("Distribution of distances of fires from roads")
plt.xlabel("Distance (m)")
plt.ylabel("Amount")
plt.savefig('distance_distribution.png', bbox_inches="tight", dpi=300)

# %%
