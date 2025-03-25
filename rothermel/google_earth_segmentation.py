import ee
import geemap

# Authenticate and initialize Google Earth Engine
ee.Initialize(project='fuel-type')

# Load dataset
dataset = ee.Image('ESA/GLOBCOVER_L4_200901_200912_V2_3')
landcover = dataset.select('landcover')

# Define landcover visualization parameters
landcover_palette = {
    11: '#aaefef', 14: '#ffff63', 20: '#dcef63', 30: '#cdcd64', 40: '#006300',
    50: '#009f00', 60: '#aac700', 70: '#003b00', 90: '#286300', 100: '#788300',
    110: '#8d9f00', 120: '#bd9500', 130: '#956300', 140: '#ffb431', 150: '#ffebae',
    160: '#00785a', 170: '#009578', 180: '#00dc83', 190: '#c31300', 200: '#fff5d6',
    210: '#0046c7', 220: '#ffffff', 230: '#743411'
}

landcover_descriptions = {
    11: "Post-flooding or irrigated croplands",
    14: "Rainfed croplands",
    20: "Mosaic cropland (50-70%) / vegetation (grassland, shrubland, forest) (20-50%)",
    30: "Mosaic vegetation (grassland, shrubland, forest) (50-70%) / cropland (20-50%)",
    40: "Closed to open (>15%) broadleaved evergreen and/or semi-deciduous forest (>5m)",
    50: "Closed (>40%) broadleaved deciduous forest (>5m)",
    60: "Open (15-40%) broadleaved deciduous forest (>5m)",
    70: "Closed (>40%) needleleaved evergreen forest (>5m)",
    90: "Open (15-40%) needleleaved deciduous or evergreen forest (>5m)",
    100: "Closed to open (>15%) mixed broadleaved and needleleaved forest (>5m)",
    110: "Mosaic forest-shrubland (50-70%) / grassland (20-50%)",
    120: "Mosaic grassland (50-70%) / forest-shrubland (20-50%)",
    130: "Closed to open (>15%) shrubland (<5m)",
    140: "Closed to open (>15%) grassland",
    150: "Sparse (>15%) vegetation (woody vegetation, shrubs, grassland)",
    160: "Closed (>40%) broadleaved forest regularly flooded - Fresh water",
    170: "Closed (>40%) broadleaved semi-deciduous and/or evergreen forest regularly flooded - saline water",
    180: "Closed to open (>15%) vegetation (grassland, shrubland, woody vegetation) on regularly flooded or waterlogged soil - fresh, brackish or saline water",
    190: "Artificial surfaces and associated areas (urban areas >50%)",
    200: "Bare areas",
    210: "Water bodies",
    220: "Permanent snow and ice",
    230: "Unclassified"
}

# Mapping from GLOBCOVER land cover codes to fuel model codes
globcover_to_fuel_type = {
    11: "GR3",
    14: "GR2",
    20: "GR4",
    30: "GR4",
    40: "TU2",
    50: "TU1",
    60: "TU1",
    70: "TU1",
    90: "TU2",
    100: "TU2",
    110: "GS2",
    120: "GR4",
    130: "SH5",
    140: "GR1",
    150: "NB8",
    160: "NB8",
    170: "NB8",
    180: "NB8",
    190: "NB9",
    200: "NB9",
    210: "NB8",
    220: "NB9",
    230: "NB9"
}


# Function to get landcover value & color at a coordinate
def get_landcover_info(lat, lon):
    point = ee.Geometry.Point(lon, lat)
    landcover_value = landcover.sample(region=point, scale=30).first().get('landcover').getInfo()
    
    # Find corresponding color
    landcover_color = landcover_palette.get(landcover_value, 'Unknown')
    landcover_desc = landcover_descriptions.get(landcover_value, 'Unknown')
    fuel_type = globcover_to_fuel_type.get(landcover_value, 'NB9')
    
    
    return landcover_value, landcover_color, fuel_type, landcover_desc

# # Example coordinate
#  # This is in long, lat, vs. lat., long for some reason?
# longitude, latitude = 118.2426, 34.0549

# value, color, desc = get_landcover_info(latitude, longitude)

# print(f"Landcover Value: {value}")
# print(f"Hex Color: {color}")
# print(f"Description: {desc}")

# # Create a map
# Map = geemap.Map()
# Map.setCenter(longitude, latitude, 3)  # Center the map

# # Add the landcover layer
# Map.addLayer(landcover, {'palette': list(landcover_palette.values()), 'min': 11, 'max': 230}, 'Landcover')

# # # Save the map
# # Map.save("land_cover_map.html")
# # print("Map saved as land_cover_map.html. Open it in a browser to view.")

