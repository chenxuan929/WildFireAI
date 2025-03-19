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

    elevation = data["elevation"] if "elevation" in data else 0
    elevation2 = data2["elevation"] if "elevation" in data2 else 0 

    moisture = data.get("soil_moisture_0_to_10cm", 0.1)  # Using top 10cm layer
    temperature = data.get("temperature_2m", 25)  # Air temperature at 2m height
    wind_speed = data.get("wind_speed_80m", 5)

    return elevation, elevation2, moisture, temperature, wind_speed

# Calculates slope using elevation difference over a set horizontal distance (default 500m)
def calculate_slope(elevation, elevation2, distance=500):
    slope = ((elevation2 - elevation) / distance) * 100
    return slope  # Return percentage

# Pops a nearby latitude point at a given distance (default 500m)
def get_nearby_location(location, distance=500):
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
    m_f = moisture
    fuel_bed_depth = fuel["Fuel Bed Depth"].values[0]

    # Reaction intensity calculation
    I_R = h * w_0 * (1 - m_f)

    # ρ_p Lookup Table to automatically select ρ_p based on the fuel model
    fuel_type_to_rho_p = {
    "GR": 400,
    "GS": 450,
    "SH": 500,
    "TU": 550,
    "TL": 600,
    "SB": 625
}

    fuel_prefix = fuel_type[:2]
    rho_p = fuel_type_to_rho_p.get(fuel_prefix, 550)
    rho_b = w_0 / fuel_bed_depth
    calculated_beta = rho_b / rho_p
    
    beta = max(calculated_beta, 0.02) # The output based on this beta is too big for now, need further adjustment

    # Wind and slope factor
    #phi_wind = np.log1p(wind_speed * sigma * 0.01)  # Log-based scaling
    phi_wind = 0.4 * (wind_speed / sigma) ** 2
    # phi_slope = slope * 0.02
    phi_slope = 5.275 * (np.tan(np.radians(slope))) ** 1.35

    # Rate of spread
    ROS = (I_R * (1 + phi_wind + phi_slope)) / (beta * sigma)

    return max(ROS, 0.1)  # Ensure non-negative rate

# Test it
location = (40.0, -105.0)  # coordinates input
elevation, elevation2, moisture, temperature, wind_speed = get_environmental_data(location)
slope = calculate_slope(elevation, elevation2)
#fuel_type = "SB1"
fuel_types = ["GR1", "GR2", "GR3", "GR4", "GR5", "GR6", "GR7", "GR8", "GR9", "GS1", "GS2", "GS3", "GS4", "SH1", "SH2", "SH3", "SH4", "SH5", "TU1", "TL1", "TL2", "SB1", "SB2", "SB3", "SB4"]
for fuel_type in fuel_types:
    ros = calculate_ros(fuel_type, wind_speed, slope, moisture)
    print(f"Calculated the Rate of Spread for {fuel_type}: {ros:.3f} m/min")







