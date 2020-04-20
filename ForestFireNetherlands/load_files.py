import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService

def load_satellite_txt_files(pathname, delimiter):
    satellite_object = SatelliteDataService.get_satellite_object_txt(pathname, delimiter)
    
    return satellite_object