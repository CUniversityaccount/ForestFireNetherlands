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
from dotenv import load_dotenv, find_dotenv, dotenv_values

load_dotenv(find_dotenv())
base_dictiornary = os.getenv("LOCAL_STORAGE")

sns.set_style("ticks", {'legend.frameon': True})

# Month parser for easier date parsing
months_choices = {}
for i in range(1, 13):
    month = str(i)
    if (i < 10):
        month = "0" + str(i)

    months_choices[month] = i

# Firetypes
firetypes = ['forest', 'heath', 'peat', 'dune', 'combined nature']
# Load the shapefiles


def shapefile_list_parser(list_files):
    return [file for file in list_files if file.endswith(".shp") and "filtered" in file and "v2" in file]


os.chdir(base_dictiornary)

viirs_shapefile_path_small = base_dictiornary + \
    "\\Files\\VIIRS375M\\ParsedShapefile"

natura2000_path = base_dictiornary + "\\Files\\natura2000\\natura2000.shp"
nationale_parken_path = base_dictiornary + \
    "\\Files\\nationaleparken\\nationaleparken.shp"

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
shapefiles_loaded_viirs_small = shapefiles_loaded_viirs_small.replace(
    {'month': months_choices})
# Loading Dutch Raster
raster_pathname = "F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\NederlandCorine.tif"
landcover_the_netherlands = rasterio.open(raster_pathname)

# loading Natura 2000 points
natura2000 = gpd.read_file(natura2000_path)
nationale_parken = gpd.read_file(nationale_parken_path)


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


sns.lineplot(data=viirs_yearly_fires, x=np.arange(len(viirs_yearly_fires.keys())),
             y=viirs_yearly_fires.values, ci=None, color="grey", markers="o")
plot = sns.regplot(data=viirs_yearly_fires, x=np.arange(len(viirs_yearly_fires.keys())),
                   y=viirs_yearly_fires.values, ci=None, scatter=False, color="black")
plot.set_xlabel("Year")
plot.set_ylabel("Amount of firepixels")
plot.set_xticklabels(viirs_yearly_fires.keys())
plt.savefig("regression_line_yearly_fires.png", dpi=300)

# %% Plotting Monthly trends
plt.cla()
viirs_monthly = shapefiles_loaded_viirs_small.pivot_table(values="id",
                                                          index=["month"],
                                                          columns="year",
                                                          aggfunc=len,
                                                          fill_value=0).reset_index()
viirs_monthly = viirs_monthly.melt(id_vars=["month"], value_name="count")
years = viirs_monthly["year"].unique()
fig = sns.catplot(data=viirs_monthly, x="month",
                  y="count",
                  hue="year",
                    aspect=1.25,
                  style="year",
                  kind="point",
                  dodge=True)
fig.ax.grid(True, axis="both")
fig.set_axis_labels("Month", "Amount of fire pixels",)
fig.legend.set_title("FireType")
# fig.set_title("Amount of fire pixels per month per year")
# viirs_monthly.plot(kind="scatter")

# sns.lineplot(data=viirs_monthly, x="month", y="count", hue="year")
# %% Plot the location related to the national parks
viirs_points = shapefiles_loaded_viirs_small["geometry"]
natura_single_geometry = natura2000.unary_union
nationale_parken_single_geometry = nationale_parken.unary_union
# show(landcover_the_netherlands, ax=ax)
# points.plot(ax=ax, color="red")
natura_mask = viirs_points.within(natura_single_geometry)
national_parks_mask = viirs_points.within(nationale_parken_single_geometry)
# points = points[mask]

# %% Plot
data_plot = pd.DataFrame({
    'titles': ['National Parks\nand\nNatura2000', 'National parks', 'Natura2000', 'None'],
    'values': [
        (national_parks_mask & natura_mask).sum(),
        (national_parks_mask & ~natura_mask).sum(),
        (natura_mask & ~national_parks_mask).sum(),
        (~national_parks_mask & ~natura_mask).sum()
    ]
})

fig = sns.barplot(x="titles", y="values", data=data_plot, color="darkgrey")
plt.xlabel("")
plt.ylabel("Amount of firepixels")
fig.grid(True, axis="y")
plt.savefig("fires_within_natural_areas.png", dpi=300)

# %% BarGraph yearly type
plt.cla()

fig = sns.countplot(x="year", hue="firetype",
                    data=shapefiles_loaded_viirs_small,
                    palette=["cornflowerblue", "limegreen",
                             "peru", "grey", "gold"])

# Make legend labels
fig.set_xlabel("Year")
fig.set_ylabel("Amount of firepixels")
fig.grid(True, axis="y")

# set legend texts
for t in fig._legend.texts:
    t.set_text(t.get_text().title())

legend = fig.get_legend()
legend.set_title("Firetype")
legend.get_frame().set_facecolor("white")
plt.savefig("yearly_fires_firetype.png", dpi=300)

# %% FIRETYPE overview monthly for each year
plt.cla()
viirs_relative = shapefiles_loaded_viirs_small.pivot_table(values="id",
                                                           index=[
                                                               "firetype", "year"],
                                                           columns="month",
                                                           aggfunc=len,
                                                           fill_value=0).reset_index()
years = list(viirs_relative["year"].unique())

viirs_relative = viirs_relative.melt(
    id_vars=["firetype", "year"], value_name="count")
viirs_relative = viirs_relative.sort_values(by="year")

legend_labels = sorted(list(map(lambda firetype: firetype.title(),
                                shapefiles_loaded_viirs_small["firetype"].unique())))
fig = sns.catplot(data=viirs_relative, x="month", y="count",
                  col="year",
                  col_wrap=3,
                  kind="bar",
                  hue="firetype",
                  palette=["peru",  "limegreen",
                           "cornflowerblue", "grey", "gold"],
                  aspect=1.50)

for ax in fig.axes.flat:
    ax.grid(True, axis="y")

fig.set_axis_labels("Month", "Amount of fire pixels")
for (row_val), ax in fig.axes_dict.items():
    ax.set_title(row_val)

# set legend texts
for t in fig._legend.texts:
    t.set_text(t.get_text().title())
#
fig.legend.set_title("Year")
plt.savefig('monthly_fires_type.png', dpi=600)


# %% Plots the distance of the fire spot to the road

# nog een 95% graden lijn van de afstand
shapefile_roads_and_railroads = gpd.read_file(
    "F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\VIIRS375M\\Join_wegen\\VIIRS375M_Distance.shp")

sns.displot(shapefile_roads_and_railroads,
            x="distance", bins=20, color="darkgrey")
plt.title("Distribution of distances of fires from roads")
plt.xlabel("Distance (m)")
plt.ylabel("Amount of pixels")
plt.savefig('distance_distribution.png', bbox_inches="tight", dpi=300)

# %%
