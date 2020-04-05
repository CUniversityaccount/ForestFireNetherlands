import ForestFireNetherlands.repository.SatelliteDateRepository as SatelliteDateRepository
import ForestFireNetherlands.model.SatelliteData as SatelliteData

def get_satellite_object(pathfile):
    loaded_data = SatelliteDateRepository.get_text_file(pathfile)

    return loaded_data