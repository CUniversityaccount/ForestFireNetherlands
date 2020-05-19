import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
import pyproj


def unary_union_by_day(shapefile, projection):
    unionized = pd.DataFrame(columns=["geometry", "surface_area"]) 

    unionized_polygons = shapefile.geometry.unary_union
    seperated_shapes = None
    
    if unionized_polygons.geom_type == 'MultiPolygon':
        seperated_shapes = [polygon for polygon in unionized_polygons]
    else:
        seperated_shapes = [unionized_polygons]
        
    for polygon in seperated_shapes:
        unionized = unionized.append({
                                    "geometry": polygon,
                                    "surface_area": shape(polygon).area },
                                    ignore_index=True)
        
    unionized = gpd.GeoDataFrame(unionized, 
                            geometry='geometry',
                            crs=pyproj.CRS(projection))
    return unionized
