import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
import pyproj


def unary_union_by_day(shapefile, column_name_date, projection):
    shapefile = shapefile.groupby(column_name_date)

    unionized = pd.DataFrame(columns=["day", "geometry", "surface_area"]) 

    for day, group in shapefile:
        combined_polygon = group.unary_union
        unionized = unionized.append({"day": day, 
                                    "geometry": combined_polygon,
                                    "surface_area": shape(combined_polygon).area },
                                    ignore_index=True)
        
    unionized = gpd.GeoDataFrame(unionized, 
                            geometry='geometry',
                            crs=pyproj.CRS(projection))
    return unionized
