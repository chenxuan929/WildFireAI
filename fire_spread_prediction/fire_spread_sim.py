import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import pickle
from fire_spread_prediction import build_env, rothermel_model, firebreak_utils


# Adjust Rate of Spread when fire enters firebreak
def adjust_ros_with_firebreak(i, j, ros, firebreak_mask, p_block=0.8):
    if firebreak_mask[i][j]:
        # Fire might be blocked
        if np.random.rand() < p_block:
            return 0.0  # Completely blocked
        else:
            return ros * 0.2  # Fire slows down but continues
    return ros


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


# Build the grid (done once before simulation)
# print("Building grid...")
# grid = build_env.build_grid(central_coordinate, radius, grid_size)
#Place a random firebreak in the real grid
firebreak = firebreak_utils.Firebreak(grid)  # uses your real terrain/moisture/wind grid
firebreak_mask = firebreak.firebreak_mask 

# Fire spread parameters
initial_intensity = 1.0
decay_rate = 0.05
max_ros = 5.0  # Max ROS for scaling probabilities

# Initialize fire state and intensity
fire_state = np.zeros((grid_size, grid_size))  # UNBURNED = 0
#firebreak_mask = np.zeros((grid_size, grid_size), dtype=bool) 
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
    plt.pause(0.5)  # Pause to show updates
    plt.clf()  # Clear the figure to prepare for the next iteration

# Fire spread simulation
def run_fire_simulation(iterations=20):
    global fire_state, fire_intensity

    for t in range(iterations):
        print(f"Iteration {t + 1}/{iterations}")
        new_fire_state = fire_state.copy()

        for i in range(grid_size):
            for j in range(grid_size):
                if fire_state[i, j] == 1:  # Burning cell
                    # Retrieve environmental conditions
                    new_fire_state[i,j] = 2
                    elevation, elevation2, moisture, temperature, wind_speed, slope, live_fuel_moisture = rothermel_model.get_environmental_data(grid[i][j]['central_coord'])
                    fuel_type = grid[i][j]['fuel_type']
                    print(fuel_type)
                    print(elevation, elevation2, moisture, temperature, wind_speed, slope, live_fuel_moisture)
                    ros = rothermel_model.calculate_ros(fuel_type, wind_speed, slope, moisture, live_fuel_moisture, fuel_model_params)['ros']
                    ros = adjust_ros_with_firebreak(i, j, ros, firebreak_mask)  #  NEW: Modify ROS if firebreak is present
                    prob = min((ros * fire_intensity[i, j]) / max_ros, 1.0)


                    print(f"Cell ({i},{j}) | ROS: {ros} | Spread Probability: {prob:.4f}")

                    # Spread fire to neighbors
                    for di, dj in [(-1,0), (1,0), (0,-1), (0,1)]:  # 4-way spreading
                        ni, nj = i + di, j + dj
                        if 0 <= ni < grid_size and 0 <= nj < grid_size:
                            if fire_state[ni, nj] == 0 and np.random.rand() < prob:  # Only spread to UNBURNED
                                new_fire_state[ni, nj] = 1  # Fire spreads
                                print(f"Fire spreads to cell ({ni},{nj})")

        fire_state = new_fire_state
        fire_intensity = np.maximum(0, fire_intensity - decay_rate)  # Apply linear decay
        
        # Visualize the grid state after each iteration
        plot_grid(fire_state)

# Run simulation
# python3 -m fire_spread_prediction.fire_spread_sim
run_fire_simulation()
