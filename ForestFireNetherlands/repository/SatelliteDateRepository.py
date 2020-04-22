import rasterio
import numpy as np
import pandas as pd
import os
import sys

def get_text_file(filepath, delimiter):
     
    if not delimiter or not filepath:
        raise ValueError("No delimiter or/and filepath", delimiter, filepath)

    loaded_file = None
    
    try:

        if delimiter.isspace():
            loaded_file = pd.read_csv(filepath, delim_whitespace=True, error_bad_lines=False)
        else:
            loaded_file = pd.read_csv(filepath, delimiter=delimiter, error_bad_lines=False)

        loaded_file_column_headers = [ name.strip().lower() for name in loaded_file.columns.values ] 
        loaded_file.columns = loaded_file_column_headers
        
    except Exception as e:
        raise e

    return loaded_file

def get_raster_file(filepath):
    try:
        raster = rasterio.open(filepath)
    except Exception as e:
        raise e

    return raster