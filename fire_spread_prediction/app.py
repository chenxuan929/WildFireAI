import os
import time
import numpy as np
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from flask import Flask
from fire_spread_prediction import build_env
from fire_spread_prediction import rothermel_model

# Set the environment variable for React version
os.environ['REACT_VERSION'] = '18.2.0'

# Initialize the Flask server and Dash app
server = Flask(__name__)
app = dash.Dash(__name__, server=server)

# Load the fuel model parameters
fuel_model_params = pd.read_csv("./data_retrieval/fuel_model_params.csv", skiprows=1).rename(columns=lambda x: x.strip())

# Fire spread simulation parameters
initial_intensity = 1.0
decay_rate = 0.05
max_ros = 5.0  # Max ROS for scaling probabilities
grid_size = 20
central_coordinate = (30.0549, 100.2426)  # (lat, lon)
radius = 30  # km
start_x, start_y = 10, 10  # Starting cell

# Initialize fire state and intensity
fire_state = np.zeros((grid_size, grid_size))  # UNBURNED = 0
fire_intensity = np.full((grid_size, grid_size), initial_intensity)
fire_state[start_x, start_y] = 1  # Fire starts here (BURNING = 1)

# Build the grid (done once before simulation)
grid = build_env.build_grid(central_coordinate, radius, grid_size)

# Helper function to simulate the fire spread
def run_fire_simulation(iterations=20, max_duration=20):
    global fire_state, fire_intensity
    start_time = time.time()  # Record start time
    frames = []

    for t in range(iterations):
        elapsed_time = time.time() - start_time
        if elapsed_time > max_duration:
            print("Simulation timed out.")
            break

        new_fire_state = fire_state.copy()

        for i in range(grid_size):
            for j in range(grid_size):
                if fire_state[i, j] == 1:  # Burning cell
                    new_fire_state[i, j] = 2  # Mark as burned
                    elevation, elevation2, moisture, temperature, wind_speed, slope, live_fuel_moisture = rothermel_model.get_environmental_data(grid[i][j]['central_coord'])
                    fuel_type = grid[i][j]['fuel_type']
                    ros = rothermel_model.calculate_ros(fuel_type, wind_speed, slope, moisture, live_fuel_moisture, fuel_model_params)['ros']
                    prob = min((ros * fire_intensity[i, j]) / max_ros, 1.0)

                    # Spread fire to neighbors (4-way spreading)
                    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < grid_size and 0 <= nj < grid_size:
                            if fire_state[ni, nj] == 0 and np.random.rand() < prob:  # Only spread to UNBURNED
                                new_fire_state[ni, nj] = 1  # Fire spreads

        fire_state = new_fire_state
        fire_intensity = np.maximum(0, fire_intensity - decay_rate)  # Apply linear decay
        
        # Save the frame (grid state) for further processing if necessary
        frames.append(fire_state)
    
    return frames

# Define the Dash layout
app.layout = dmc.MantineProvider(
    html.Div(
        children=[
            html.Div(
                className='header',
                children=[html.H2("Fire Spread Simulation", style={'textAlign': 'center', 'fontWeight': 200})]
            ),
            # Input form
            html.Div(
                style={'marginLeft': '53px', 'marginRight': '53px', 'marginTop': '10px', 'width': '88.75vw'},
                children=[
                    html.Div(
                        children=[
                            html.Label("Latitude:"),
                            dcc.Input(id='lat-input', type='number', value=30.0549, style={'width': '30%'}),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Label("Longitude:"),
                            dcc.Input(id='lon-input', type='number', value=100.2426, style={'width': '30%'}),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Label("Radius (km):"),
                            dcc.Input(id='radius-input', type='number', value=30, style={'width': '30%'}),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Label("Grid Size:"),
                            dcc.Input(id='grid-size-input', type='number', value=20, style={'width': '30%'}),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Label("Starting Cell (x, y):"),
                            dcc.Input(id='start-x-input', type='number', value=10, style={'width': '10%'}),
                            dcc.Input(id='start-y-input', type='number', value=10, style={'width': '10%'}),
                        ]
                    ),
                ]
            ),
            # Start simulation button
            html.Div(
                style={'marginLeft': '53px', 'marginRight': '53px', 'width': '88.75vw'},
                children=[
                    html.Button('Run Simulation', id='run-simulation-button', n_clicks=0, style={'width': '30%', 'fontSize': '20px'})
                ]
            ),
            # Visualization output (currently not used for images)
            html.Div(id='fire-simulation-output', style={'marginTop': '30px', 'width': '88.75vw'}),
            dcc.Store(id='simulation-frames', data=[])
        ]
    )
)

# Define callback to handle button click and simulation
@app.callback(
    Output('fire-simulation-output', 'children'),
    Output('simulation-frames', 'data'),
    [Input('run-simulation-button', 'n_clicks')],
    [
        State('lat-input', 'value'),
        State('lon-input', 'value'),
        State('radius-input', 'value'),
        State('grid-size-input', 'value'),
        State('start-x-input', 'value'),
        State('start-y-input', 'value'),
        State('simulation-frames', 'data'),
    ]
)
def update_fire_simulation(n_clicks, lat, lon, radius, grid_size, start_x, start_y, frames):
    if n_clicks > 0:
        if not frames:
            frames = run_fire_simulation(iterations=20, max_duration=20)  # Run simulation and store frames
            return [html.Div("Simulation is running...", style={'textAlign': 'left', 'fontWeight': 200, 'marginLeft': 50}), frames]

        # Processing or further analysis can be done with frames if needed, 
        # but we won't display the images here in the dashboard
        return [html.Div("Simulation complete.", style={'textAlign': 'left', 'fontWeight': 200, 'marginLeft': 50}), frames]

if __name__ == '__main__':
    app.run_server(debug=True)
