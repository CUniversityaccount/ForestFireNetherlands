import ForestFireNetherlands.repository.SatelliteDateRepository as SatelliteDateRepository
import ForestFireNetherlands.model.SatelliteData as SatelliteData

def get_satellite_object_txt(pathname, delimiter):
    loaded_data = SatelliteDateRepository.get_text_file(pathname, delimiter)

    
    return loaded_data