# %% LOADING THE FILES
import rasterio
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import os
import numpy as np
from rasterio.mask import mask

def shapefile_list_parser(list_files):
    return [file for file in list_files if file.endswith(".shp")]
    
base_dictiornary = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project"
os.chdir(base_dictiornary)

modis_shapefile_path = base_dictiornary + "\\Files\\MODIS\\ParsedShapeFile"
viirs_shapefile_path = base_dictiornary + "\\Files\\VIIRS\\ParsedShapefile"
list_shapefile_modis = os.listdir(modis_shapefile_path)
list_shapefile_modis = shapefile_list_parser(list_shapefile_modis)

list_shapefile_viirs = os.listdir(viirs_shapefile_path)
list_shapefile_viirs = shapefile_list_parser(list_shapefile_viirs)

# %% Legend Data
legend = pd.read_csv('E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\Legend\\CLC2018_CLC2018_V2018_20_QGIS.txt', sep=",", header=None)
legend.columns = ["id",  "r", "g", "b", "greyscale", "description"]

# %% SHAPEFILE ANALYSIS
def loading_shapefiles(shapefiles, path):

    shapefile_loaded_all = None    

    for shapefile in shapefiles:
        print(shapefile)
        
        # Masks and make the right projection from the data
        shapefile_loaded = gpd.read_file(path + "\\" + shapefile)

        timestamp = shapefile.split(".")[1]
        year = str(timestamp)[:4]
        month = str(timestamp)[4:]
        shapefile_loaded["year"] = year
        shapefile_loaded["month"] = month

        if shapefile_loaded_all is None:
            shapefile_loaded_all = shapefile_loaded
        else:
            shapefile_loaded_all = shapefile_loaded_all.append(shapefile_loaded)            
    
    return shapefile_loaded_all

shapefiles_loaded_viirs = loading_shapefiles(shapefiles=list_shapefile_viirs, path=viirs_shapefile_path)
shapefiles_loaded_modis = loading_shapefiles(shapefiles=list_shapefile_modis, path=modis_shapefile_path)

# %% LOADS THE NETHERLANDS RASTERFILE
raster_pathname = "E:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\NederlandCorine.tif"
landcover_the_netherlands = rasterio.open(raster_pathname)

def sort_pixel_value(polygons, raster, upper_boundary = None, lower_boundary = None):
    """
    Sorts the data on basis of the most prominent pixels which are selected on basis of the upper and lower boundary
    """

    sorted_data = {"raster": [], "area": []}

    for polygon in polygons:
        data_polygon_masked, transformation_meta = mask(raster, [polygon], crop=True)
        data_polygon_masked = np.squeeze(data_polygon_masked)
        
        data_mask_outside_boundary = data_polygon_masked >= 0
        
        total_cells = np.sum(data_mask_outside_boundary) / 2
        
        if lower_boundary is not None:
            data_mask_outside_boundary = ((data_polygon_masked < lower_boundary) | data_mask_outside_boundary)

        if upper_boundary is not None:
            data_mask_outside_boundary = (data_polygon_masked > upper_boundary | data_mask_outside_boundary)
                    
        data_filtered = data_polygon_masked[data_mask_outside_boundary]

        if total_cells <= np.sum(data_mask_outside_boundary) and len(data_filtered) > 0:
            sorted_data["raster"].append(list(data_filtered))
            sorted_data["area"].append(polygon.area)
            
    sorted_data = pd.DataFrame.from_dict(sorted_data)
    return sorted_data


# %% ANALYSIS SURFACE SIZE

def yearly_burned_area(dataframe):
    """
    Before calling this function, the data set needs to be ordered by year. Good function hereby is groupby for pandas
    """
    parsed_years = {}
    for year, data in dataframe:
        corrected_geometry = sort_pixel_value(polygons=data.geometry, 
                                            raster=landcover_the_netherlands, 
                                            lower_boundary=100, 
                                            upper_boundary=200)
        total_burned_area = np.sum(corrected_geometry["area"]) / (1000**2) # km^2 
        parsed_years[year] = total_burned_area
    
    return parsed_years

viirs_yearly_burned_area = yearly_burned_area(dataframe=shapefiles_loaded_viirs.groupby("year"))
modis_yearly_burned_area = yearly_burned_area(dataframe=shapefiles_loaded_modis.groupby("year"))

# %% LAND COVER 
def effected_land_cover(dataframe, raster):

    parsed_years = {}

    for year, data in dataframe:
        corrected_geometry = sort_pixel_value(polygons=data.geometry, 
                                                  raster=landcover_the_netherlands, 
                                                  lower_boundary=100, 
                                                  upper_boundary=200)

        # Get all the unique values from all the arrays
        landcover_values = np.array(sum(list(corrected_geometry["raster"]), []))
        data_sorted_landcover = {}
        for landcover_value in np.unique(landcover_values):
            if landcover_value in data_sorted_landcover.keys():
                data_sorted_landcover[landcover_value] += len(landcover_values[landcover_values == landcover_value])
            else:
                data_sorted_landcover[landcover_value] = len(landcover_values[landcover_values == landcover_value])

        parsed_years[year] = data_sorted_landcover
    
    return parsed_years

viirs_yearly_burned_land_cover = effected_land_cover(dataframe=shapefiles_loaded_viirs.groupby("year"), raster=landcover_the_netherlands)
modis_yearly_burned_land_cover = effected_land_cover(dataframe=shapefiles_loaded_modis.groupby("year"), raster=landcover_the_netherlands)

# %% PLOT BURNED AREA AND 
fig, axs = plt.subplots(1, 1, figsize=(9, 3))
axs.plot(list(viirs_yearly_burned_area.keys()), list(viirs_yearly_burned_area.values()), label="VIIRS")
axs.plot(list(modis_yearly_burned_area.keys()), list(modis_yearly_burned_area.values()), label="MODIS")
axs.legend()
axs.set_ylabel("km^2")
axs.set_xlabel("Time")
fig.savefig('test.png', bbox_inches="tight", dpi=300)

# %% PLOTS LAND COVER

max_values = set(sum([list(data.keys()) for data in list(viirs_yearly_burned_land_cover.values())], []))
fig, axs = plt.subplots(1, 2, figsize=(18, 9))
label_count = np.arange(len(viirs_yearly_burned_land_cover.keys())) + 1
width = 0.5

for count, value in enumerate(max_values):

    bar_values = []
    for land_cover_data in viirs_yearly_burned_land_cover.values():  


        if value in land_cover_data:
            bar_values.append(land_cover_data[value])
        else: 
            bar_values.append(0) 

    color = legend.loc[legend["id"] == value]
    axs[0].bar(label_count, np.array(bar_values), width, color=[(list(color["r"])[0] / 255, list(color["g"])[0] / 255, list(color["b"])[0] / 255, 1)])
axs[0].set_xticks(label_count)
axs[0].set_xticklabels(list(viirs_yearly_burned_land_cover.keys()))

max_values = set(sum([list(data.keys()) for data in list(modis_yearly_burned_land_cover.values())], []))
label_count = np.arange(len(modis_yearly_burned_land_cover.keys()))

for count, value in enumerate(max_values):

    bar_values = []
    for land_cover_data in modis_yearly_burned_land_cover.values():  


        if value in land_cover_data:
            bar_values.append(land_cover_data[value])
        else: 
            bar_values.append(0) 
    color = legend.loc[legend["id"] == value]
    axs[1].bar(label_count, np.array(bar_values), width, 
    color=[(list(color["r"])[0] / 255, list(color["g"])[0] / 255, list(color["b"])[0] / 255, 1)],
    label=list(color["description"])[0])
axs[1].set_xticks(label_count)
axs[1].set_xticklabels(list(modis_yearly_burned_land_cover.keys()))
axs[1].legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
fig.tight_layout()

fig.savefig('land_cover_yearly.png')
 # %%


# %%
