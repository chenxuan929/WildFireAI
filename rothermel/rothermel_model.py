# Based on a given cell, figure out what it's rothermel model value is.
import pandas as pd
import numpy as np
from open_meteo_client import get_attributes_by_location

# Reads fuel model parameters from csv
fuel_model_params = pd.read_csv("fuel_model_params.csv", skiprows=1).rename(columns=lambda x: x.strip())

# Fire spread constants -> fire spread adjustments for different fuel types
fuel_type_adjustments = {
    "GR": 1.2,  # Grass fires spread faster
    "GS": 1.1,  # Grass-Shrub mix is slightly faster
    "SH": 0.9,  # Shrub fires are slightly slower
    "TU": 0.8,  # Timber-Understory fires are slower
    "TL": 0.7,  # Timber Litter fires are slowest
    "SB": 1.0   # Slash-Blowdown as expected
}

def get_live_fuel_moisture(location):
    # Get real-time live fuel moisture from a weather API
    data = get_attributes_by_location(location)
    return data.get("live_fuel_moisture", 75)  # Default to 75% 
    # I dont think we have that in our API, we could use default value for now?


def get_environmental_data(location):
    second_location = get_nearby_location(location)
    data = get_attributes_by_location(location)
    data2 = get_attributes_by_location(second_location)

    elevation = data["elevation"] if "elevation" in data else 0
    elevation2 = data2["elevation"] if "elevation" in data2 else 0 

    moisture = data.get("Soil Moisture (0-10 cm)")
    
    if moisture is None:
        moisture = 0.1
    
    temperature = data.get("Temperature (2 m)", 25)  # Air temperature at 2m height
    
    wind_speed = data.get("Wind Speed (80 m)", 5)
    

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
def calculate_ros(fuel_type, wind_speed, slope, moisture, live_herb_moisture, fuel_model_params):
    fuel = fuel_model_params[fuel_model_params['Fuel Model Code'] == fuel_type]
    if fuel.empty:
        raise ValueError("Fuel type not found in dataset.")
    
    w_0 = fuel['Fuel Load (1-hr)'].values[0]  # Dead fine fuel load (kg/m^2)
    w_10 = fuel['Fuel Load (10-hr)'].values[0]  # Medium fuel load
    w_100 = fuel['Fuel Load (100-hr)'].values[0]  # Heavy fuel load

    w_live_herb = fuel['Fuel Load (Live herb)'].values[0]  # Live herbaceous fuel
    w_live_woody = fuel['Fuel Load (Live woody)'].values[0]  # Live woody fuel
    extinction_moisture = fuel['Dead Fuel Extincion Moisture Percent'].values[0]
    sigma = fuel['SAV Ratio (Dead 1-hr)'].values[0]  # SAV ratio (m^2/m^3)
    fuel_bed_depth = fuel["Fuel Bed Depth"].values[0]

    h = fuel['Heat Content'].values[0] if 'Heat Content' in fuel.columns else 18000 # Heat content (J/kg)

    # dynamically calculate rho_p
    fuel_prefix = fuel_type[:2]

    transfer_ratio = 1.0 # Default (Fully cured)
    if fuel_prefix in ["GR", "GS", "SH"]:
        if live_herb_moisture >= 120:
            transfer_ratio = 0.0  # Fully green, no transfer
        elif live_herb_moisture >= 90:
            transfer_ratio = 0.33  # 33% cured
        elif live_herb_moisture >= 75:
            transfer_ratio = 0.50  # 50% cured
        elif live_herb_moisture >= 60:
            transfer_ratio = 0.67  # 67% cured

    dead_fuel_converted = w_live_herb * transfer_ratio
    w_0 += dead_fuel_converted
    
    if moisture > extinction_moisture:
        return {
        "fuel_type": fuel_type,
        "ros": 0.0,
        "status_code": 0 # Fire won't spread: Moisture too high
    }
    
    # Wind and slope factor
    phi_wind = 0.4 * (wind_speed / sigma) ** 2
    phi_slope = 5.275 * (np.tan(np.radians(slope))) ** 1.35

    # Dynamically Calculate Bulk Density
    I_R = h * (w_0 + 0.5 * w_10 + 0.2 * w_100) * (1 - moisture)
    rho_b = (w_0 + w_10 + w_100)/ fuel_bed_depth
    beta = max(rho_b / 550, 0.02)

    # Rate of spread
    ROS = (I_R * (1 + phi_wind + phi_slope)) / (beta * sigma)
    ROS *= fuel_type_adjustments.get(fuel_prefix, 1.0)
    ROS = max(ROS, 0.1)

    return {
        "fuel_type": fuel_type,
        "ros": ROS,
        "status_code": 1 # Fire will spread
    }


# Test it
# location = (40.0, -105.0)
location = (34.0549, -118.2426)  # coordinates input
elevation, elevation2, moisture, temperature, wind_speed = get_environmental_data(location)

slope = calculate_slope(elevation, elevation2)
live_herb_moisture = get_live_fuel_moisture(location)
fuel_types = ["GR1", "GR2", "GR3", "GR4", "GR5", "GR6", "GR7", "GR8", "GR9", "GS1", "GS2", "GS3", "GS4", "SH1", "SH2", "SH3", "SH4", "SH5", "TU1", "TL1", "TL2", "SB1", "SB2", "SB3", "SB4"]
for fuel_type in fuel_types:
    ros = calculate_ros(fuel_type, wind_speed, slope, moisture, live_herb_moisture, fuel_model_params)
    print(f"Calculated the Rate of Spread for {ros} m/min")







