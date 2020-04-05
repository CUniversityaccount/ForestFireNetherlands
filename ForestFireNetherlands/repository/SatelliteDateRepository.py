import numpy as np
import pandas as pd
import pathlib
import os

def get_text_file(pathfile):
    original_path = os.getcwd()

    # changes path to the file env
    os.chdir(pathfile)
    
    satelite_data_file = pd.read_csv(pathfile, sep=",")

    # changes to original map
    os.chdir(original_path)
    return satelite_data_file