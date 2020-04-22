import ForestFireNetherlands.repository.SatelliteDateRepository as SatelliteDateRepository
import ForestFireNetherlands.model.SatelliteData as SatelliteData

def get_satellite_object_txt(filepath, delimiter):
    loaded_data = SatelliteDateRepository.get_text_file(filepath = filepath, delimiter = delimiter)
    return loaded_data

def get_satellite_object_raster(filepath):
    loaded_data = SatelliteDateRepository.get_raster_file(filepath = filepath)
    return loaded_data