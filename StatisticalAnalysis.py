"""
This file is made for the visualization of the data.
Furthermore, it highlights different time scales

"""
# %% IMPORT LIBRARIES
import rasterio
from rasterio.mask import mask
from rasterio.plot import show
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService
import os
import numpy as np
import datetime
import seaborn as sns
from scipy import stats

# Month parser for easier date parsing
months_choices = {}
for i in range(1, 13):
    month = str(i)
    if (i < 10):
        month = "0" + str(i)

    months_choices[month] = datetime.date(2008, i, 1).strftime('%B')

# Firetypes
firetypes = ['forest', 'heath', 'peat', 'dune', 'combined nature']
# Load the shapefiles


def shapefile_list_parser(list_files):
    return [file for file in list_files if file.endswith(".shp") and "filtered" in file and "v2" in file]


base_dictiornary = "F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project"
os.chdir(base_dictiornary)

viirs_shapefile_path_small = base_dictiornary + \
    "\\Files\\VIIRS375M\\ParsedShapefile"

natura2000_path = base_dictiornary + "\\Files\\natura2000\\natura2000.shp"

# list_shapefile_modis = os.listdir(modis_shapefile_path)
# list_shapefile_modis = shapefile_list_parser(list_shapefile_modis)

# list_shapefile_viirs_big = os.listdir(viirs_shapefile_path_big)
# list_shapefile_viirs_big = shapefile_list_parser(list_shapefile_viirs_big)

list_shapefile_viirs_small = os.listdir(viirs_shapefile_path_small)
list_shapefile_viirs_small = shapefile_list_parser(list_shapefile_viirs_small)

# LOADING SHAPEFILES


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
    shapefiles=list_shapefile_viirs_small, path=viirs_shapefile_path_small)
# shapefiles_loaded_modis = loading_shapefiles(shapefiles=list_shapefile_modis, path=modis_shapefile_path)

# Loading Dutch Raster
raster_pathname = "F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\NederlandCorine.tif"
landcover_the_netherlands = rasterio.open(raster_pathname)

# loading Natura 2000 points
natura2000 = gpd.read_file(natura2000_path)
# Legend Data
legend = pd.read_csv(
    'F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\Legend\\CLC2018_CLC2018_V2018_20_QGIS.txt', sep=",", header=None)
legend.columns = ["id",  "r", "g", "b", "greyscale", "description"]

# %% Amount of fires for the last couples years
viirs_yearly_fires = shapefiles_loaded_viirs_small.query(
    "year != '2020'")["year"].value_counts().sort_index()

# Line regression
reg_line = stats.linregress(
    np.arange(len(viirs_yearly_fires.keys())),
    viirs_yearly_fires.values)

print(reg_line.rvalue ** 2)

sns.set_style("darkgrid")

sns.lineplot(data=viirs_yearly_fires, x=np.arange(len(viirs_yearly_fires.keys())),
             y=viirs_yearly_fires.values, ci=None, color="grey", markers="o")
plot = sns.regplot(data=viirs_yearly_fires, x=np.arange(len(viirs_yearly_fires.keys())),
                   y=viirs_yearly_fires.values, ci=None, scatter=False, color="black")
plot.set_xlabel("year")
plot.set_ylabel("amount of firepixels")
plot.set_xticklabels(viirs_yearly_fires.keys())


# %% Plotting Monthly trends
print(months_choices)
viirs_monthly = shapefiles_loaded_viirs_small.pivot_table(values="id",
                                                          index=["month"],
                                                          columns="year",
                                                          aggfunc=len,
                                                          fill_value=0)
print(viirs_monthly)
viirs_monthly.plot(kind='bar')

# %% Plot fires in natural areas
points = shapefiles_loaded_viirs_small["geometry"].centroid
# fig, ax = plt.subplots(figsize=(12, 19))
# show(landcover_the_netherlands, ax=ax)
# points.plot(ax=ax, color="red")
natura2000_union = natura2000.unary_union
mask = points.within(natura2000_union)
points = points.loc[mask]
print(points)


# %% FIRETYPE


def bar_plot_firetype(shapefiles, subplot, time_periods, time_type):
    max_values = []

    # Gets the unique values of the satellite data
    max_values = np.unique(np.array(max_values))

    bottom = None

    ind = np.arange(len(time_periods))
    for firetype in firetypes[::-1]:

        bar_values = []

        if firetype not in shapefiles.groups.keys():
            bar_values = [0] * 12
        else:
            values = shapefiles.get_group(firetype)

            for time in time_periods:

                filtered_data = values.query(time_type + ' == "' + time + '"')

                if len(filtered_data) > 0:
                    bar_values.append(len(filtered_data))
                else:
                    bar_values.append(0)

        if (bottom is None):
            subplot.bar(ind, np.array(bar_values),
                        label=firetype, bottom=bottom)
            bottom = np.array(bar_values)
        else:
            subplot.bar(ind, np.array(bar_values),
                        label=firetype, bottom=bottom)
            bottom += np.array(bar_values)
    print(bottom)
    return subplot


viirs_relative = shapefiles_loaded_viirs_small.pivot_table(values="id",
                                                           index=[
                                                               "firetype"],
                                                           columns="year",
                                                           aggfunc=len,
                                                           fill_value=0)
viirs_relative_sum = (viirs_relative / viirs_relative.sum()) * 100
# %% yearly relative effected land type

fig, axs = plt.subplots(1, 1, figsize=(18, 9), sharey=True)
years = list(shapefiles_loaded_viirs_small.groupby("year").groups.keys())
viirs_relative_monthly = shapefiles_loaded_viirs_small.groupby("year")
axs = bar_plot_firetype(shapefiles_loaded_viirs_small.groupby(
    "firetype"), axs, years, 'year')
plt.xticks(np.arange(len(years)), years)
fig.suptitle("Yearly amount of fires")
plt.legend()
plt.savefig('fire_types_yearly.png', bbox_inches="tight", dpi=300)
# %% Monthly
fig, axs = plt.subplots(1, 1, figsize=(18, 9), sharey=True)
years = list(shapefiles_loaded_viirs_small.groupby("year").groups.keys())
axs = bar_plot_firetype(shapefiles_loaded_viirs_small.groupby(
    "firetype"), axs, list(months_choices.keys()), 'month')
plt.xticks(np.arange(len(months_choices.values())),
           list(months_choices.values()))
fig.suptitle("Monthly amount of fires")
plt.legend()
plt.savefig('fire_types_monthly.png', bbox_inches="tight", dpi=300)

# %% Plots the different years with land use changes

viirs_data_years = shapefiles_loaded_viirs_small.groupby("year")
fig, axs = plt.subplots(3, 3, figsize=(18, 9), sharey=True)
axs = axs.flatten()

for index, (year, data) in enumerate(viirs_data_years):
    axs[index] = bar_plot_firetype(data.groupby(
        "firetype"), axs[index], list(months_choices.keys()), 'month')
    axs[index].set_title(year)
    axs[index].set_xticks(np.arange(len(months_choices.values())))
    axs[index].set_xticklabels(list(months_choices.values()), rotation=90)
    axs[index].legend()

plt.tight_layout()
# %% Plots the distance of the fire spot to the road

# nog een 95% graden lijn van de afstand
shapefile_roads_and_railroads = gpd.read_file(
    "F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\VIIRS375M\\Join_wegen\\VIIRS375M_Distance.shp")

plt.hist(shapefile_roads_and_railroads['distance'], bins=20, rwidth=0.8)
plt.title("Distribution of distances of fires from roads")
plt.xlabel("Distance (m)")
plt.ylabel("Amount")
plt.savefig('distance_distribution.png', bbox_inches="tight", dpi=300)

# %%
