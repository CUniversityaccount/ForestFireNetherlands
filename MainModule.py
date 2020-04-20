
#%%
import ForestFireNetherlands as FFN
import ForestFireNetherlands.service.SatelliteDataService as SatelliteDataService

pathname = "C:\\Users\\Coen\\Documents\\Universiteit\\Earth Science msc 2019 - 2020\\Research Project\\Files"
delimiter = " "
satellite_data = SatelliteDataService.get_satellite_object_txt(pathname=pathname, delimiter=delimiter)


