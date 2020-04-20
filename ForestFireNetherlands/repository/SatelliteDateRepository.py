import numpy as np
import pandas as pd
import os
import sys

def get_text_file(pathfile, delimiter):
    original_path = os.getcwd()

    # changes path to the file env
    os.chdir(pathfile)
    
    files = os.listdir()

    loaded_files = []
    for file in files: 
        if not delimiter:
            raise ValueError("No delimiter", delimiter)
        
        try:
            loaded_file = None
            
            if delimiter.isspace():
                loaded_file = pd.read_csv(file, delim_whitespace=True, error_bad_lines=False)
            else:
                loaded_file = pd.read_csv(file, delimiter=delimiter, error_bad_lines=False)

            if loaded_file is not None:
                loaded_files.append(loaded_file)

        except Exception as e:
            raise e
    
    # changes to original map
    os.chdir(original_path)


    print(loaded_files)
    return loaded_files