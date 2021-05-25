import os
import pyproj

# Bug Pyproj: cannot find proj if postgis is installed, throws CRS error
pyproj.datadir.set_data_dir(os.environ["USERPROFILE"] + "\\Miniconda3\\Library\\share\\proj")
import pandas as pd 
import numpy as np
import sys
import rasterio
from rasterio.mask import mask
from shapely import wkt, wkb
from shapely.ops import transform
from shapely.geometry import Point, Polygon
import uuid

sys.path.append(os.getcwd() + '\\src\\connection')
import connection
import shapeHandler as sh


conn = None 
row_measurements = 6400 
pixel_nadir = 0.375 # km
satellite_altitude = 833  # km

def add_land_cover_data(pixel, raster, upper_boundary=None, lower_boundary=None):
    """
    Sorts the data on basis of the most prominent pixels which are selected on basis of the upper and lower boundary
    """

    raster_data, transformation_meta = mask(
        raster, [pixel], crop=True)
    raster_data = np.squeeze(raster_data)
    raster_mask_boundaries = ((raster_data > 0) & (raster_data < 500))

    raster_data = raster_data[raster_mask_boundaries]

    if raster_data.size == 0:
        print("The pixel has only water")
        return None

    # First checks if there is any city or industrial in the pixel, because then it is unsure if the fire was an wild or natural fire
    if (any(raster_data < 200)):
        return None

    # Get the most frequent land_cover in the values
    (land_cover_values, counts) = np.unique(
        raster_data, return_counts=True)
    land_cover_mask = (counts == np.max(counts))

    if (all(land_cover_values < 300) or all(land_cover_values[land_cover_mask] < 300)):
        return None

    # Same problem as the urban filter
    if (land_cover_values[land_cover_mask].size > 1 and any(land_cover_values < 300)):
        print("Unsure if it is nature or agriculture")
        return None

    # Nature qualifications by Corine Land Cover (CLC)
    if (all(land_cover_values[land_cover_mask] > 310) and all(land_cover_values[land_cover_mask] < 320)):
        return 'forest'
    elif (all(land_cover_values[land_cover_mask] > 320) and all(land_cover_values[land_cover_mask] < 330)):
        return 'heath'
    elif (all(land_cover_values[land_cover_mask] == 331)):
        return 'dune'
    elif (all(land_cover_values[land_cover_mask] > 410) and all(land_cover_values[land_cover_mask] < 421)):
        return 'peat'
    elif (len(land_cover_values[land_cover_mask]) > 1 and 
        all(((land_cover_values[land_cover_mask] > 310) & (land_cover_values[land_cover_mask] < 332)) | ((land_cover_values[land_cover_mask] > 410) & (land_cover_values[land_cover_mask] < 421)))):
        return 'combined nature'
    
    return None


def set_pixel_characteristics():
    if os.getenv("LOCALDATA_VIIRS") is None:
        raise FileNotFoundError('LOCALDATA_VIIRS location not in enviroment')
    elif os.getenv("RASTER_CORINE") is None:
        raise FileNotFoundError('RASTER_CORINE location not in enviroment')

    raster = rasterio.open(os.getenv("RASTER_CORINE")) # raster projection is epsg 28992

    conn = connection.Connection()

    result = pd.read_sql_query("SELECT id, sample, ST_AsText(ST_MakePoint(longitude, latitude)) point FROM pixel.firepixel WHERE type = 0 and confidence != 'low'", conn.conn)
    # Convert the point to shapely points
    result["point"] = result["point"].apply(lambda p: wkt.loads(p))
    
    pixel_sizes = sh.calculatesPixelSizeVIIRS(result["sample"], pixel_nadir, row_measurements)

    # Convert the pixels size from km to meters
    pixel_sizes["delta_trackline"] *= 1000
    pixel_sizes["delta_scanline"] *= 1000
        
    project_to_meters = pyproj.Transformer.from_crs(pyproj.CRS.from_epsg(4326), "epsg:28992", always_xy=True).transform
    project_from_meters = pyproj.Transformer.from_crs(28992, 4326, always_xy=True).transform
    
    # Make a copu of the result table and add additional information to trans from the point to a polygon
    classification_pixels = result[["id", "point"]].copy()
    classification_pixels.loc[:, "delta_scanline"] = pixel_sizes["delta_scanline"]
    classification_pixels.loc[:, "delta_trackline"] = pixel_sizes["delta_trackline"]

    # Change pixels coordinates to meters 
    classification_pixels["point"] = classification_pixels["point"].apply(lambda p: transform(project_to_meters, p))

    # Add the polygons, the polygons are not converted to coordiantes because the raster is in meters
    classification_pixels.loc[:, "pixel"] = classification_pixels.apply(lambda p: 
            Polygon([
                [p.point.x - (p.delta_scanline / 2), p.point.y  + (p.delta_trackline / 2)], # left upper
                [p.point.x + (p.delta_scanline / 2), p.point.y  + (p.delta_trackline / 2)], # right upper
                [p.point.x + (p.delta_scanline / 2), p.point.y  - (p.delta_trackline / 2)], # right down
                [p.point.x - (p.delta_scanline / 2), p.point.y  - (p.delta_trackline / 2)], # left down
                [p.point.x - (p.delta_scanline / 2), p.point.y  + (p.delta_trackline / 2)]
            ])
        , axis=1
    )
    
    classification_pixels.loc[:, "landcovertype"] = classification_pixels["pixel"].apply(
        lambda p: add_land_cover_data(p, raster, lower_boundary=100, upper_boundary=200) 
    )

    # Changes the pixel values to 
    classification_pixels["pixel"] = classification_pixels["pixel"].apply(lambda p: transform(project_from_meters, p).wkt)
    classification_pixels = classification_pixels.dropna()
    
    # Set ups the FirePixelDetail structure
    classification_pixels.loc[:, "firepixelid"] = classification_pixels["id"]
    classification_pixels.loc[:, "id"] = [ str(uuid.uuid4()) for index in range(len(classification_pixels)) ]
    classification_pixels = classification_pixels[["id", "firepixelid",  "pixel", "landcovertype"]]
    print(str(classification_pixels["pixel"].iloc[0]))
    # Create a list of tupples from the dataframe values
    table = "pixel.firepixeldetail"
    tuples = [tuple(x) for x in classification_pixels.to_numpy()]
    # Comma-separated dataframe columns
    cols = ','.join(list(classification_pixels.columns))
    # SQL quert to execute
    query  = "INSERT INTO %s(%s)" % (table, cols)
    values = ["%s"] * len(classification_pixels.columns)
    query += " VALUES (" + ", ".join(values) + ")"
    cursor = conn.conn.cursor()
    try:
        cursor.executemany(query, tuples)
        conn.conn.commit()
    except (Exception) as error:
        print("Error: %s" % error)
        conn.conn.rollback()
        cursor.close()
    conn.close()

def insert_pixel_characteristics():
    return


if __name__ == '__main__':
    set_pixel_characteristics()