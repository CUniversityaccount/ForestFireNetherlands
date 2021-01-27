import rasterio
import numpy as np
import pandas as pd
import os
import sys


def get_satellite_text_file(filepath, delimiter):

    if not delimiter or not filepath:
        raise ValueError("No delimiter or/and filepath", delimiter, filepath)

    loaded_file = None

    try:

        if delimiter.isspace():
            loaded_file = pd.read_csv(
                filepath, delim_whitespace=True, error_bad_lines=False)
        else:
            loaded_file = pd.read_csv(
                filepath, delimiter=delimiter, error_bad_lines=False)

        loaded_file_column_headers = [
            name.strip().lower() for name in loaded_file.columns.values]
        loaded_file.columns = loaded_file_column_headers

    except Exception as e:
        raise e

    return loaded_file


def calculatesScanAngleMODIS(amount_row_measurements, height, pixel_nadir, row_number):
    """
    Calculates the scan angle for MODIS on basis of the location of the pixel

    return the scan angle in radians
    """
    scan_angle = abs((pixel_nadir / height) *
                     (-0.5 * amount_row_measurements + 0.5 + (row_number - 1)))
    return scan_angle


def calculatesPixelSizeMODIS(scan_angle, satellite_height, pixel_nadir):
    """

    scan_angle needs to be in radians
    all distances needs to be in kilometer
    Calculation of a pixel size 
    (Ichoku, C. and Kaufman, Y. J. (2005) ‘A method to derive smoke emission rates from MODIS fire radiative energy measurements’, IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING. 445 HOES LANE, PISCATAWAY, NJ 08855-4141 USA: IEEE-INST ELECTRICAL ELECTRONICS ENGINEERS INC, 43(11), pp. 2636–2649. doi: 10.1109/TGRS.2005.857328.)

    return the horizontal and vertical size of a pixel
    """

    # constant in the calculation
    earth_radius = 6378.137  # km

    r = satellite_height + earth_radius
    s = pixel_nadir / satellite_height
    delta_S = earth_radius * s * \
        (np.cos(scan_angle) /
         np.sqrt(((earth_radius / r) ** 2) - (np.sin(scan_angle) ** 2)) - 1)
    delta_T = r * s * (np.cos(scan_angle) -
                       np.sqrt((earth_radius / r) ** 2 - (np.sin(scan_angle) ** 2)))
    return {"delta_scanline": delta_S, "delta_trackline": delta_T}


def calculatesPixelSizeVIIRS(samples, pixel_nadir, amount_row_measurements):
    """
    VIIRS pixels containt the same pixel size until a thresshold.
    so this function parses these thresholds
    see Schroeder, W. et al. (2014) ‘The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment’, REMOTE SENSING OF ENVIRONMENT. 360 PARK AVE SOUTH, NEW YORK, NY 10010-1710 USA: ELSEVIER SCIENCE INC, 143, pp. 85–96. doi: 10.1016/j.rse.2013.12.008.
    see Schueler, C. F., Lee, T. F. and Miller, S. D. (2013) ‘VIIRS constant spatial-resolution advantages’, INTERNATIONAL JOURNAL OF REMOTE SENSING. 4 PARK SQUARE, MILTON PARK, ABINGDON OX14 4RN, OXON, ENGLAND: TAYLOR & FRANCIS LTD, 34(16), pp. 5761–5777. doi: 10.1080/01431161.2013.796102.
    """
    delta_S = []
    delta_T = []

    # TODO find less hardcoded option for
    for sample in samples:
        sample = abs(sample - (amount_row_measurements / 2))
        if pixel_nadir >= 0.750:
            if sample < 1260:
                delta_S.append(0.75)
                delta_T.append(0.75)
            else:
                delta_S.append(1.6)
                delta_T.append(1.6)
        elif pixel_nadir <= 0.375:
            if sample < 2520:
                delta_S.append(0.375)
                delta_T.append(0.375)
            else:
                delta_S.append(0.75)
                delta_T.append(0.75)

    return {"delta_scanline": np.array(delta_S), "delta_trackline": np.array(delta_T)}
