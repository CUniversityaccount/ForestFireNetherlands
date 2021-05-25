import pandas as pd
import numpy as np
import uuid
import sys
import os
import geopandas
from shapely.geometry import Point
import pyproj
pyproj.datadir.set_data_dir(os.environ["USERPROFILE"] + "\\Miniconda3\\Library\\share\\proj")

from datetime import datetime, date
import time
sys.path.append(os.getcwd() + '\\src\\connection')
import connection

def get_satellite_text_file(filepath, delimiter):

    if not delimiter or not filepath:
        raise ValueError("No delimiter or/and filepath", delimiter, filepath)

    loaded_file = None

    try:

        if delimiter.isspace():
            loaded_file = pd.read_csv(
                filepath, delim_whitespace=True, error_bad_lines=False, skipinitialspace=True,)
        else:
            loaded_file = pd.read_csv(
                filepath, delimiter=delimiter, error_bad_lines=False, skipinitialspace=True,)

        loaded_file_column_headers = [
            name.strip().lower() for name in loaded_file.columns.values]
        loaded_file.columns = loaded_file_column_headers

    except Exception as e:
        raise e

    return loaded_file

def insert_data():
    if os.getenv("LOCALDATA_VIIRS") is None:
        raise FileNotFoundError('LOCALDATA_VIIRS location not in enviroment')
    elif os.getenv("SHAPEFILE_NETHERLANDS") is None:
        raise FileNotFoundError('SHAPEFILE_NETHERLANDS location not in enviroment')

    viirs_files = os.listdir(os.getenv("LOCALDATA_VIIRS"))
    shp_netherlands = geopandas.read_file(os.getenv("SHAPEFILE_NETHERLANDS")).to_crs(pyproj.CRS('EPSG:4326')).geometry[0]
    conn = connection.Connection()

    for viirs_file in viirs_files:
        print(viirs_file)
        loaded_file = get_satellite_text_file(os.getenv("LOCALDATA_VIIRS") + "\\" + viirs_file, ",")

        # Filtering based on the location, filter most fire pixels out
        # Increase the performance for next filtering
        longitude_query = 'lon > ' + \
            str(shp_netherlands.bounds[0]) + ' and lon < ' + str(shp_netherlands.bounds[2])
        latitude_query = 'lat > ' + \
            str(shp_netherlands.bounds[1]) + ' and lat < ' + str(shp_netherlands.bounds[-1])
        loaded_file.query(longitude_query + ' and ' +
                         latitude_query, inplace=True)

        # Filter pixels that are not in the netherlands shapefile
        mask = np.array([shp_netherlands.contains(Point(coordinates)) for coordinates in np.array(loaded_file[["lon", "lat"]])])
        loaded_file = loaded_file[mask]

        loaded_file.insert(loc=0, column="id", value= [ str(uuid.uuid4()) for index in range(len(loaded_file))])

        # setups datetime variables
        loaded_file = loaded_file.astype({'hhmm': str})
        loaded_file = loaded_file.astype({'yyyymmdd': str})
        time_mask = loaded_file["hhmm"].map(lambda x: len(x)) == 3
        loaded_file.loc[:, "hhmm"][time_mask] = "0" + loaded_file["hhmm"][time_mask]

        datetimes =  [pd.to_datetime(date + time, format="%Y%m%d%H%M") for date, time in np.array(loaded_file[["yyyymmdd", "hhmm"]])]

        loaded_file['yyyymmdd'] = [datetime.date().isoformat() for datetime in datetimes]
        loaded_file["hhmm"] = [datetime.time().isoformat() for datetime in datetimes]
        loaded_file = loaded_file.rename(columns={"yyyymmdd": "date", "hhmm": '"time"', "sat": "satellite", "lat": "latitude", "lon": "longitude", "pixarea": "area", "conf": "confidence"})
        if "t4" in loaded_file.columns:
            loaded_file = loaded_file.rename(columns={ "t4": "t_i4", "t5": "t_i5"})
        
        loaded_file = loaded_file[["id", "date", '"time"', "satellite", "latitude", "longitude", "t_i4", "t_i5", "sample", "area", "frp", "confidence", "type"]]

        # Create a list of tupples from the dataframe values
        table = "pixel.firepixel"
        tuples = [tuple(x) for x in loaded_file.to_numpy()]
        # Comma-separated dataframe columns
        cols = ','.join(list(loaded_file.columns))
        # SQL quert to execute
        query  = "INSERT INTO %s(%s)" % (table, cols)
        values = ["%s"] * len(loaded_file.columns)
        query += " VALUES (" + ", ".join(values) + ")"
        cursor = conn.conn.cursor()
        try:
            cursor.executemany(query, tuples)
            conn.conn.commit()
        except (Exception) as error:
            print("Error: %s" % error)
            conn.conn.rollback()
            cursor.close()
            
        loaded_file = None

    conn.close()

if __name__ == '__main__':
    insert_data()
    