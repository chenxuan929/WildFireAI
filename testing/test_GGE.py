import ee
import geemap

ee.Initialize(project='fuel-type')

collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
    .filterDate('2021-07-01', '2021-07-10') \
    .filterBounds(ee.Geometry.Point([-122.45, 37.75])) \
    .sort('CLOUD_COVER')

image = collection.first()
print(image.getInfo()['id'])

