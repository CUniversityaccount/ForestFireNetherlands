"""
Gets the Natura 2000 files
"""
import geopandas as gpd
import matplotlib.pyplot as plt

# Retrieve data from PDOK
year = 2018  # kies hier het jaar waarin je geinteresseerd bent

# f before string is the same as $ in c#
# geodata_url = f'https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=1.1.0&typeName=cbsgebiedsindelingen:cbs_provincie_{year}_gegeneraliseerd&outputFormat=json'
# natura2000_url = 'https://geodata.nationaalgeoregister.nl/natura2000/wfs?request=GetFeature&version=2.0.0&service=wfs&outputFormat=json&typeName=natura2000:natura2000'

nationaleparken_url = 'https://geodata.nationaalgeoregister.nl/nationaleparken/wfs?request=GetFeature&version=2.0.0&service=wfs&outputFormat=json&typeName=nationaleparken:nationaleparken'
nationaleparkenGPD = gpd.read_file(nationaleparken_url)
print(nationaleparkenGPD)

# Plot grenzen
fig, ax = plt.subplots(figsize=(5.5, 5.5))
nationaleparkenGPD.boundary.plot(
    color=None, edgecolor="k", linewidth=0.8, ax=ax)

# To shapefile
nationaleparkenGPD.to_file('nationaleparken')
