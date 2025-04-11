import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import pickle
import random
import build_env, rothermel_model

# Load fuel model parameters
fuel_model_params = pd.read_csv("./data_retrieval/fuel_model_params.csv", skiprows=1).rename(columns=lambda x: x.strip())

# Simulation parameters
central_coordinate = (36.7783, 119.4179)
radius = 10  # km
grid_size = 30

# Load or build grid
if os.path.exists("saved_grid.pkl"):
    print("Loading saved grid...")
    with open("saved_grid.pkl", "rb") as f:
        grid = pickle.load(f)
else:
    print("Building grid...")
    grid = build_env.build_grid(central_coordinate, radius, grid_size)
    with open("saved_grid.pkl", "wb") as f:
        pickle.dump(grid, f)

# Fire spread parameters
initial_intensity = 1.0
decay_rate = 0.02
max_ros = 1000.0

# Initialize fire state and intensity
fire_state = np.zeros((grid_size, grid_size))  # 0 = unburned, 1 = burning, 2 = burned
fire_intensity = np.full((grid_size, grid_size), initial_intensity)

# Start fire in center
start_x, start_y = grid_size // 2, grid_size // 2
fire_state[start_x, start_y] = 1

# Create dummy firebreak mask (all False)
firebreak_mask = np.zeros((grid_size, grid_size), dtype=bool)

# Visualization
def plot_grid(fire_state):
    fig, ax = plt.subplots(figsize=(8, 8))
    color_matrix = np.empty((grid_size, grid_size), dtype=object)

    for i in range(grid_size):
        for j in range(grid_size):
            if fire_state[i, j] == 1:
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

    ax.set_title("Fire Spread Simulation (No Firebreak)")
    plt.show(block=False)
    plt.pause(0.5)
    plt.clf()

# Run simulation
def run_fire_simulation_without_fb(iterations=30, display=True):
    global fire_state, fire_intensity

    for t in range(iterations):
        #print(f"Iteration {t + 1}/{iterations}")
        new_fire_state = fire_state.copy()

        for i in range(grid_size):
            for j in range(grid_size):
                if fire_state[i, j] == 1:
                    new_fire_state[i, j] = 2
                    elevation, elevation2, moisture, temperature, wind_speed, slope, live_fuel_moisture = rothermel_model.get_environmental_data(grid[i][j]['central_coord'])
                    fuel_type = grid[i][j]['fuel_type']
                    ros = rothermel_model.calculate_ros(fuel_type, wind_speed, slope, moisture, live_fuel_moisture, fuel_model_params)['ros']
                    
                    # Probability of spread
                    prob = min((ros * fire_intensity[i, j]) / max_ros, 1.0)
                    #print(f"Cell ({i},{j}) | ROS: {ros:.2f} | Prob: {prob:.4f}")

                    for di, dj in [(-1,0), (1,0), (0,-1), (0,1)]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < grid_size and 0 <= nj < grid_size:
                            if not grid[ni][nj]['fuel_type'].startswith("NB") and fire_state[ni, nj] == 0 and np.random.rand() < prob:
                                new_fire_state[ni, nj] = 1
                                #print(f"Fire spreads to cell ({ni},{nj})")

        fire_state = new_fire_state
        fire_intensity = np.maximum(0, fire_intensity - decay_rate)

        if display:
            plot_grid(fire_state)
    return fire_state  # Optionally return final state

# Run
run_fire_simulation_without_fb()
