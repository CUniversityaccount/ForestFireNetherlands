"""
This file is made for the visualization of the data.
Furthermore, it highlights different time scales

"""
# %% IMPORT LIBRARIES
import rasterio
from rasterio.mask import mask
from rasterio.plot import show

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os
import calendar
import numpy as np
from scipy import stats
import seaborn as sns

from shapely import wkt
from shapely.geometry import Polygon
from shapely.ops import transform
import pyproj
pyproj.datadir.set_data_dir(os.environ["USERPROFILE"] + "\\Miniconda3\\Library\\share\\proj")

from dotenv import load_dotenv
import sys
sys.path.append("..\\connection")
import connection

load_dotenv()
base_dictiornary = os.getenv("LOCAL_STORAGE")
sns.set_style("ticks", {'legend.frameon': True})

# Conn with databse
conn = connection.Connection()

# Firetypes
if os.getenv("RASTER_CORINE") is None:
    raise FileNotFoundError('RASTER_CORINE location not in enviroment')

landcover_the_netherlands = rasterio.open(os.getenv("RASTER_CORINE"))

# loading Natura 2000 points
natura2000 = gpd.read_file('F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\natura2000\\natura2000.shp')
nationale_parken = gpd.read_file('F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\nationaleparken\\nationaleparken.shp')

# Legend Data
legend = pd.read_csv(
    'F:\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files\\clc2018_clc2018_v2018_20_raster100m\\Legend\\CLC2018_CLC2018_V2018_20_QGIS.txt', sep=",", header=None)
legend.columns = ["id",  "r", "g", "b", "greyscale", "description"]

# %% Pie chart percentage of fire
query = pd.read_sql_query(
    """
    SELECT LandCoverType, COUNT(*) amount_pixels 
    FROM pixel.FirePixelDetail 
    GROUP BY LandCoverType order by 1
    """, con = conn.conn)

def func(pct, allvals):
    percentage = (pct / np.sum(allvals)) * 100
    return "{:.1f}% (n = {:d})".format(percentage, pct)


labels = query["amount_pixels"].map(lambda ap: func(ap, query["amount_pixels"].sum()))

fig, ax = plt.subplots(figsize=(12, 6), subplot_kw=dict(aspect="equal"))
wedges, texts = ax.pie(list(query["amount_pixels"]),  labels=labels, colors=[
    "grey", "gold", "limegreen", "peru", "cornflowerblue"])

legend = [fireType.capitalize()
          for fireType in list(query["landcovertype"])]
ax.legend(wedges, legend,
          title="Firetype",
          loc="upper left",
          bbox_to_anchor=(1, 0, 0.5, 1))
plt.tight_layout()
plt.savefig('firetype_distribution.png', dpi=300)
plt.show()
plt.cla()

# %% Amount of fires for the last couples years
query = pd.read_sql_query(
    """
    SELECT CAST(EXTRACT('year' from fp.date) AS int) AS year,  count(*) count
    FROM pixel.FirePixel fp
    JOIN pixel.FirePixelDetail fpd ON fpd.FirePixelId = fp.Id
    GROUP BY year
    ORDER BY 1
    """, con=conn.conn)

# Line regression
reg_line = stats.linregress(
    np.arange(len(query)),
    np.array(query['count']))

print(reg_line.rvalue ** 2)


sns.lineplot(data=query, x=np.arange(len(query)),
             y='count', ci=None, color="grey", markers="o")
plot = sns.regplot(data=query, x=np.arange(len(query)),
                   y='count', ci=None, scatter=False, color="black")
plot.set_xlabel("Year")
plot.set_ylabel("Amount of firepixels")
plot.set_xticklabels(np.array(query["year"]))
plt.savefig("regression_line_yearly_fires.png", dpi=300)
plt.show()

# %% Plotting Monthly trends landcover
plt.cla()
query = pd.read_sql_query(
    """
    SELECT month, avg(pixels) avg, landcovertype
    FROM (
            WITH TimeSeries (month, year, landcovertype) AS (
                SELECT CAST(EXTRACT('month' from date) AS int) AS month, CAST(EXTRACT('year' from date) AS int) AS year, landcovertypes.landcovertype
                FROM generate_series('01-01-2012'::date, '01-12-2020', '1 month') AS date, 
                    (SELECT distinct landcovertype FROM pixel.FirePixelDetail) AS landcovertypes
            ),
            NormalizedFirePixel (id, date, landcovertype) AS (
                SELECT fp.id, fp.date, fpd.landcovertype
                FROM pixel.FirePixel fp
                JOIN pixel.FirePixelDetail fpd ON fpd.FirePixelId = fp.Id
            )
            SELECT ts.year, ts.month, ts.landcovertype, count(fp.Id) pixels
            FROM TimeSeries ts 
            LEFT OUTER JOIN NormalizedFirePixel fp ON ts.month = EXTRACT('month' from fp.date) 
            AND ts.year = EXTRACT('year' from fp.date)
            AND fp.landcovertype = ts.landcovertype
            GROUP BY ts.year, ts.month, ts.landcovertype
            ORDER BY ts.year, ts.month
        ) AS time_serie 
    GROUP BY month, landcovertype
    ORDER BY 1, 3
    """, con=conn.conn)
query["landcovertype"] = query["landcovertype"].apply(lambda lc: lc.capitalize())
fig = sns.catplot(data=query, x="month",
                  y="avg",
                  hue="landcovertype",
                  aspect=1.25,
                  kind='bar',
                  dodge=True,
                  palette=["grey", "gold", "limegreen", "peru", "cornflowerblue"]
                )
fig.set(xticklabels= calendar.month_abbr[1:])
fig.ax.grid(True, axis="y")
fig.set_axis_labels("Month", "Amount of fire pixels",)
fig.legend.set_title("Firetype")
fig.tight_layout()
plt.savefig("Avg_monthly_fire_grouped_by_landcover.png", dpi = 300)
# fig.set_title("Amount of fire pixels per month per year")
# viirs_monthly.plot(kind="scatter")
plt.show()

# sns.lineplot(data=viirs_monthly, x="month", y="count", hue="year")
#%% Plot monthly over the years
query = pd.read_sql_query(
    """
    WITH TimeSeries (month, year) AS (
        SELECT CAST(EXTRACT('month' from date) AS int) AS month, CAST(EXTRACT('year' from date) AS varchar(4)) AS year
        FROM generate_series('01-01-2012'::date, '01-12-2020', '1 month') AS date
    ),
    NormalizedFirePixel (id, date) AS (
        SELECT fp.id, fp.date
        FROM pixel.FirePixel fp
        JOIN pixel.FirePixelDetail fpd ON fpd.FirePixelId = fp.Id
    )
    SELECT count(fp.Id) amount, ts.year, ts.month AS month
    FROM TimeSeries ts 
    LEFT OUTER JOIN NormalizedFirePixel fp ON ts.month = EXTRACT('month' from fp.date) AND ts.year = CAST(EXTRACT('year' from fp.date) AS varchar(4))
    GROUP BY ts.year, ts.month
    ORDER BY ts.year, ts.month
    """, con=conn.conn)

fig = sns.relplot(data=query, 
                  x="month",
                  y="amount",
                  row="year",
                  kind="line",
                  estimator = None,
                  height=2,
                  aspect=6
                )
fig.set_titles(template="{row_name}")
fig.set(xticks=query['month'].unique(), xticklabels= calendar.month_abbr[1:]) \
    .set_axis_labels("Month", "Firepixels")
for ax in fig.axes.flat:
    ax.xaxis.set_tick_params(labelbottom=True)# set new labels
plt.tight_layout()
# plt.show()
plt.savefig("Monthly_Trend_Years.png", dpi=300)
plt.clf()
# %% Plot the location related to the national parks
query = pd.read_sql_query(
    """
    SELECT ST_AsText(pixel) pixel
    FROM pixel.FirePixelDetail
    """, con=conn.conn)
project_to_meters = pyproj.Transformer.from_crs(pyproj.CRS.from_epsg(4326), "epsg:28992", always_xy=True).transform
query["pixel"] = query["pixel"].apply(lambda p: transform(project_to_meters, wkt.loads(p)))
print(query)

natura_single_geometry = natura2000.unary_union
nationale_parken_single_geometry = nationale_parken.unary_union
natura_mask = query["pixel"].apply(lambda p: p.within(natura_single_geometry)).to_numpy()
national_parks_mask = query["pixel"].apply(lambda p: p.within(nationale_parken_single_geometry)).to_numpy()
# points = points[mask]

data_plot = pd.DataFrame({
    'titles': ['National Parks\nand\nNatura2000', 'National parks', 'Natura2000', 'Outside designated\nnatural areas'],
    'values': [
        (national_parks_mask & natura_mask).sum(),
        (national_parks_mask & ~natura_mask).sum(),
        (natura_mask & ~national_parks_mask).sum(),
        (~national_parks_mask & ~natura_mask).sum()
    ]
})
# %% Plot natura 2000 values
fig = sns.barplot(x="titles", y="values", data=data_plot, color="darkgrey")
plt.xlabel("")
plt.ylabel("Amount of firepixels")
fig.grid(True, axis="y")
for patch in fig.patches:
    _x = patch.get_x() + patch.get_width() / 2
    _y = patch.get_y() + patch.get_height() + 0.25
    percentage = (int(patch.get_height()) / len(query)) * 100
    value = '{:.1f}% ({})'.format(percentage, int(patch.get_height()))
    
    fig.text(_x, _y, value, ha="center") 
sns.despine(ax=fig)
plt.tight_layout()
plt.savefig("fires_within_natural_areas.png", dpi=300)
plt.show()
plt.cla()

# %% BarGraph yearly type

# fig = sns.countplot(x="year", hue="firetype",
#                     data=shapefiles_loaded_viirs_small,
#                     palette=["cornflowerblue", "limegreen",
#                              "peru", "grey", "gold"])

# # Make legend labels
# fig.set_xlabel("Year")
# fig.set_ylabel("Amount of firepixels")
# fig.grid(True, axis="y")
# + 
# # set legend texts
# for t in fig._legend.texts:
#     t.set_text(t.get_text().title())

# legend = fig.get_legend()
# legend.set_title("Firetype")
# legend.get_frame().set_facecolor("white")
# plt.savefig("yearly_fires_firetype.png", dpi=300)


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
