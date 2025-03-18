# Based on a given cell, figure out what it's rothermel model value is.
import pandas as pd
import numpy as np
from open_meteo_client import get_attributes_by_location

# Reads fuel model parameters from csv
fuel_model_params = pd.read_csv("fuel_model_params.csv", skiprows=1).rename(columns=lambda x: x.strip())

def get_environmental_data(location):
    second_location = get_nearby_location(location)
    data = get_attributes_by_location(location)
    data2 = get_attributes_by_location(second_location)
    # elevation = data.get("elevation", 0)
    # elevation2 = data2.get("elevation", 0)
    elevation = data["elevation"] if "elevation" in data else 0
    elevation2 = data2["elevation"] if "elevation" in data2 else 0 


    moisture = data.get("soil_moisture_0_to_10cm", 0.1)  # Using top 10cm layer
    temperature = data.get("temperature_2m", 25)  # Air temperature at 2m height
    return elevation, elevation2, moisture, temperature

def calculate_slope(elevation, elevation2, distance=500):
    # Calculates slope using elevation difference over a set horizontal distance (default 500m)
    # print(f"Debug: Elevation 1 = {elevation}m, Elevation 2 = {elevation2}m, Distance = {distance}m")
    slope = ((elevation2 - elevation) / distance) * 100
    # print(f"Debug: Computed Slope (Raw) = {slope}%")
    return slope  # Return percentage

def get_nearby_location(location, distance=500):
    # Pops a nearby latitude point at a given distance (default 500m)
    lat_shift = distance / 111320  # Convert meters to degrees
    return (location[0] + lat_shift, location[1])  # Move north

# Calculates the rate of spread (ROS)
def calculate_ros(fuel_type, wind_speed, slope, moisture):
    fuel = fuel_model_params[fuel_model_params['Fuel Model Code'] == fuel_type]
    if fuel.empty:
        raise ValueError("Fuel type not found in dataset.")
    
    w_0 = fuel['Fuel Load (1-hr)'].values[0]  # Fuel load (kg/m^2)
    sigma = fuel['SAV Ratio (Dead 1-hr)'].values[0]  # SAV ratio (m^2/m^3)
    h = fuel['Heat Content'].values[0] if 'Heat Content' in fuel.columns else 18000 # Heat content (J/kg)
    m_f = moisture  # Moisture

    # Simplified packing ratio calculation
    beta = w_0 / (1 + w_0)
    
    # Reaction intensity calculation
    I_R = h * w_0 * (1 - m_f)
    
    # Wind and slope factor
    phi_wind = np.log1p(wind_speed * sigma * 0.01)  # Log-based scaling
    phi_slope = slope * 0.02
    
    # Print to check value
    # print(f"Fuel Load (1-hr): {w_0} kg/m^2")
    # print(f"SAV Ratio (Dead 1-hr): {sigma} m^2/m^3")
    # print(f"Heat Content: {h} J/kg")
    # print(f"Moisture Content: {m_f}")
    # print(f"Wind Speed: {wind_speed} m/s")
    # print(f"Slope: {slope} (converted from elevation)")
    # print(f"Wind Factor: {phi_wind}")
    # print(f"Slope Factor: {phi_slope}")

    # Rate of spread
    ROS = (I_R * (1 + phi_wind + phi_slope)) / (beta * sigma)
    return max(ROS, 0)  # Ensure non-negative rate

# Test
# location = (40.0, -105.0)  # coordinates
# wind_speed = 10  # m/s
# elevation, elevation2, moisture, temperature = get_environmental_data(location)
# slope = calculate_slope(elevation, elevation2)
# print(f"Slope: {slope:.8f}% (computed from real elevation data)")
# fuel_type = "GR1"
# ros = calculate_ros(fuel_type, wind_speed, slope, moisture)

# print(f"Calculated the Rate of Spread: {ros:.3f} m/min")







