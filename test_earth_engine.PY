import ee

PROJECT_ID = "sih26162-thermal-intelligence"

# Initialize Earth Engine
ee.Initialize(project=PROJECT_ID)

print("Earth Engine initialized successfully!")

# Small test area in Maharashtra
point = ee.Geometry.Point([73.85, 18.52])

# Dynamic World collection
dw = (
    ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    .filterBounds(point)
    .sort("system:time_start", False)
)

# Get the latest image
image = dw.first()

# Extract land-cover probabilities
probabilities = image.select([
    "water",
    "trees",
    "grass",
    "flooded_vegetation",
    "crops",
    "shrub_and_scrub",
    "built",
    "bare",
    "snow_and_ice",
]).reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=point.buffer(100),
    scale=10,
    maxPixels=10000,
)

print("Dynamic World query successful!")
print(probabilities.getInfo())