import numpy as np
import matplotlib.pyplot as plt
from data_retrieval import open_meteo_client
from data_retrieval import google_earth_segmentation


# Builds grid of specified grid_size (n x n), based on a fixed central coordinate
# and radius. Each cell in the grid contains a dictionary of its properties, such as
# center, temperature, moisture, elevation, etc.
def build_grid(central_coordinate, radius, grid_size):
    lat_step, lon_step = get_step_size(central_coordinate, radius, grid_size)

    # If is n is odd, central coordinate will be in a cell.
    # If is n is even, central coordinate will be on the intersection of cells.
    lat_origin = central_coordinate[0] - (grid_size / 2) * lat_step
    lon_origin = central_coordinate[1] - (grid_size / 2) * lon_step

    grid = [[{} for _ in range(grid_size)] for _ in range(grid_size)]

    for i in range(grid_size):
        for j in range(grid_size):
            lat = lat_origin + (i + 0.5) * lat_step
            lon = lon_origin + (j + 0.5) * lon_step

            #print(f"Getting attributes for cell ({i}, {j}): ({lat}, {lon})")

            grid[i][j]['central_coord'] = (lat, lon)
            hourly_data = open_meteo_client.get_attributes_by_location((lat, lon))
            for feature in hourly_data:
                grid[i][j][feature] = hourly_data[feature]
            grid[i][j]["fuel_type"] = google_earth_segmentation.get_landcover_info(lat, lon)[2]
            grid[i][j]["fuel_type_color"] = google_earth_segmentation.get_landcover_info(lat, lon)[1]

            grid[i][j]["original_fuel_type"] = grid[i][j]["fuel_type"]
            grid[i][j]["original_color"] = grid[i][j]["fuel_type_color"]

            
            # print(grid[i][j]["fuel_type"])
    print("YESSS! All grid attributes initialized!")
    return grid

# Visualizes the raw grid, just the central coordinates (without any 
# other qualifying details). Primarily to make sure cell dimensions and
# locations are correct.
def visualize_raw_grid(central_coordinate, radius, grid):
    grid_size = len(grid)
    lat_step, lon_step = get_step_size(central_coordinate, radius, grid_size)

    longitudes = []
    latitudes = []
    for i in range(grid_size):
        for j in range(grid_size):
            lat, lon = grid[i][j]['central_coord']
            latitudes.append(lat)
            longitudes.append(lon)

    plt.figure(figsize=(8, 8))
    plt.scatter(longitudes, latitudes, c='blue', s=10, label='Grid Points')
    plt.scatter(central_coordinate[1], central_coordinate[0], c='red', marker='x', s=100, label='Central Point')

    # Add grid box outlines
    for i in range(grid_size):
        for j in range(grid_size):
            lat, lon = grid[i][j]['central_coord']

            # Define the four corners of the grid cell
            corners = [
                (lat - lat_step / 2, lon - lon_step / 2),  # Bottom-left
                (lat - lat_step / 2, lon + lon_step / 2),  # Bottom-right
                (lat + lat_step / 2, lon + lon_step / 2),  # Top-right
                (lat + lat_step / 2, lon - lon_step / 2),  # Top-left
                (lat - lat_step / 2, lon - lon_step / 2)   # Closing the box
            ]

            # Extract the latitude and longitude points
            box_lats, box_lons = zip(*corners)

            # Plot the outline of the grid cell
            plt.plot(box_lons, box_lats, c='black', linewidth=0.5)

    # Formatting
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("2D Geographic Grid with Cell Boundaries")
    plt.legend()
    plt.grid(True)
    plt.show()

def get_step_size(central_coordinate, grid_rad, grid_size):
    step_km = (2 * grid_rad) / grid_size # Size of each cell in km.

    lat_step = step_km / 111
    lon_step = step_km / (111 * np.cos(np.radians(central_coordinate[0])))

    return lat_step, lon_step

# central_coordinate = (34.0549, 118.2426)  # (lat, lon)
# radius = 30 # km
# grid_size = 20

# grid = build_grid(central_coordinate, radius, grid_size)
# visualize_raw_grid(central_coordinate, radius, grid)
# print(grid[0][0])