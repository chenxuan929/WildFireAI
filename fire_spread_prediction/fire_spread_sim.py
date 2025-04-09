import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import pickle
import build_env, rothermel_model, firebreak_utils


# Adjust Rate of Spread when fire enters firebreak

def adjust_ros_with_firebreak(i, j, ros, firebreak_mask, fire_intensity, wind_speed, slope, min_width=2):
    """
    Reduce ROS at (i, j) if there's a firebreak, considering:
    - Firebreak width (surrounding cells)
    - Wind speed
    - Slope
    """
    if not firebreak_mask[i][j]:
        return ros

    # Width of the firebreak in 4-neighbor directions
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    width_count = 1
    for di, dj in directions:
        ni, nj = i + di, j + dj
        if 0 <= ni < firebreak_mask.shape[0] and 0 <= nj < firebreak_mask.shape[1]:
            if firebreak_mask[ni][nj]:
                width_count += 1

    # === Slope impact ===
    if slope >= 20:
        slope_factor = 0.7  # Steep slope → firebreak less effective
    elif slope >= 10:
        slope_factor = 0.4
    else:
        slope_factor = 0.2  # Flatter = more effective

    # === Wind impact ===
    if wind_speed > 15:
        wind_factor = 0.6
    elif wind_speed > 8:
        wind_factor = 0.3
    else:
        wind_factor = 0.1

    # Total reduction factor combines slope, wind, and firebreak width
    base_reduction = min(1.0, (width_count / (min_width + 1)))
    total_reduction = 1.0 - (base_reduction * (1 - slope_factor) * (1 - wind_factor))

    return ros * total_reduction


fuel_model_params = pd.read_csv("./data_retrieval/fuel_model_params.csv", skiprows=1).rename(columns=lambda x: x.strip())

# Define parameters
central_coordinate = (30.0549, 100.2426)  # (lat, lon)
radius = 30  # km
grid_size = 20

# === Load or build grid ===
if os.path.exists("saved_grid.pkl"):
    print("Loading saved grid...")
    with open("saved_grid.pkl", "rb") as f:
        grid = pickle.load(f)
else:
    print("Building grid...")
    grid = build_env.build_grid(central_coordinate, radius, grid_size)
    with open("saved_grid.pkl", "wb") as f:
        pickle.dump(grid, f)

#Place a random firebreak in the real grid
firebreak = firebreak_utils.Firebreak(grid)  # uses your real terrain/moisture/wind grid
firebreak_mask = firebreak.firebreak_mask 

# Fire spread parameters
initial_intensity = 1.0
decay_rate = 0.05
max_ros = 5.0  # Max ROS for scaling probabilities

# Initialize fire state and intensity
fire_state = np.zeros((grid_size, grid_size))  # UNBURNED = 0
fire_intensity = np.full((grid_size, grid_size), initial_intensity)

# Choose a starting cell
start_x, start_y = 10, 10  # Example start point
fire_state[start_x, start_y] = 1  # Fire starts here (BURNING = 1)

# Visualization function
def plot_grid(fire_state):
    fig, ax = plt.subplots(figsize=(8, 8))
    color_matrix = np.empty((grid_size, grid_size), dtype=object)

    for i in range(grid_size):
        for j in range(grid_size):
            if firebreak_mask[i][j]:
                color_matrix[i, j] = "white"  # Always show firebreaks as white
            elif fire_state[i, j] == 1:
                color_matrix[i, j] = "red"
            elif fire_state[i, j] == 2:
                color_matrix[i, j] = "black"
                fire_intensity[fire_state == 2] = 0.0
            else:
                color_matrix[i, j] = grid[i][j]["fuel_type_color"]

    ax.imshow([[0] * grid_size] * grid_size, cmap="gray", alpha=0)

    for i in range(grid_size):
        for j in range(grid_size):
            ax.add_patch(plt.Rectangle((j, grid_size - i - 1), 1, 1, 
                                       color=color_matrix[i, j], edgecolor='black'))

    ax.set_title("Fire Spread Simulation")
    plt.show(block=False)
    plt.pause(0.5)
    plt.clf()

# Fire spread simulation
def run_fire_simulation(iterations=20):
    global fire_state, fire_intensity

    for t in range(iterations):
        print(f"Iteration {t + 1}/{iterations}")
        new_fire_state = fire_state.copy()

        for i in range(grid_size):
            for j in range(grid_size):
                if fire_state[i, j] == 1:
                    new_fire_state[i,j] = 2
                    elevation, elevation2, moisture, temperature, wind_speed, slope, live_fuel_moisture = rothermel_model.get_environmental_data(grid[i][j]['central_coord'])
                    fuel_type = grid[i][j]['fuel_type']
                    print(fuel_type)
                    print(elevation, elevation2, moisture, temperature, wind_speed, slope, live_fuel_moisture)
                    ros = rothermel_model.calculate_ros(fuel_type, wind_speed, slope, moisture, live_fuel_moisture, fuel_model_params)['ros']
                    ros = adjust_ros_with_firebreak(i, j, ros, firebreak_mask, fire_intensity, wind_speed, slope)
                    prob = min((ros * fire_intensity[i, j]) / max_ros, 1.0)

                    print(f"Cell ({i},{j}) | ROS: {ros} | Spread Probability: {prob:.4f}")

                    for di, dj in [(-1,0), (1,0), (0,-1), (0,1)]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < grid_size and 0 <= nj < grid_size:
                            if fire_state[ni, nj] == 0 and np.random.rand() < prob:
                                new_fire_state[ni, nj] = 1
                                print(f"Fire spreads to cell ({ni},{nj})")

        fire_state = new_fire_state
        fire_intensity = np.maximum(0, fire_intensity - decay_rate)
        plot_grid(fire_state)

# Run simulation
run_fire_simulation()

