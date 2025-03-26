import pandas as pd
import numpy as np
from data_retrieval import open_meteo_client
from data_retrieval import google_earth_segmentation

CSV_LOG_FILE = "ros_results.csv"

# Reads fuel model parameters from csv
fuel_model_params = pd.read_csv("./data_retrieval/fuel_model_params.csv", skiprows=1).rename(columns=lambda x: x.strip())

# Fire spread constants -> fire spread adjustments for different fuel types
fuel_type_adjustments = {
    "GR": 1.2,  # Grass fires spread faster
    "GS": 1.1,  # Grass-Shrub mix is slightly faster
    "SH": 0.9,  # Shrub fires are slightly slower
    "TU": 0.8,  # Timber-Understory fires are slower
    "TL": 0.7,  # Timber Litter fires are slowest
    "SB": 1.0,   # Slash-Blowdown as expected
    "NB": 0.0,  # Non-burnable: urban, water, snow, etc.
    "UNKNOWN": 0.0
}

def get_live_fuel_moisture(location):
    data = open_meteo_client.get_attributes_by_location(location)
    # Use soil moisture in the top layer (0–10 cm)
    sm_top = data.get("Soil Moisture (0-10 cm)", 0.25)
    temp = data.get("Temperature (2 m)", 20.0)
    lfmc = 30 + 100 * sm_top
    if temp > 25:
        adjustment = (temp - 25) * 1.5
        lfmc -= adjustment
        #print(f"[DEBUG] Temp exceeds 25°C, reducing LFMC by {adjustment:.2f}, new LFMC: {lfmc:.2f}")
    lfmc = max(30, min(lfmc, 120))
    #print(f"[DEBUG] Final LFMC after clamping: {lfmc:.2f}") 
    return lfmc
    


def get_environmental_data(location):
    second_location = get_nearby_location(location)
    data = open_meteo_client.get_attributes_by_location(location)
    data2 = open_meteo_client.get_attributes_by_location(second_location)
    elevation = data["elevation"] if "elevation" in data else 0
    elevation2 = data2["elevation"] if "elevation" in data2 else 0 
    slope = calculate_slope(elevation, elevation2)
    moisture = data.get("Soil Moisture (0-10 cm)", 0.1)
    live_fuel_moisture = get_live_fuel_moisture(location)
    if moisture is None:
        moisture = 0.1
    temperature = data.get("Temperature (2 m)", 25)  # Air temperature at 2m height
    wind_speed = data.get("Wind Speed (80 m)", 5)

    return elevation, elevation2, moisture, temperature, wind_speed, slope, live_fuel_moisture

# Calculates slope using elevation difference over a set horizontal distance (default 500m)
def calculate_slope(elevation, elevation2, distance=500):
    slope = ((elevation2 - elevation) / distance) * 100
    return abs(slope)  # Return percentage

# Pops a nearby latitude point at a given distance (default 500m)
def get_nearby_location(location, distance=500):
    lat_shift = distance / 111320  # Convert meters to degrees
    return (location[0] + lat_shift, location[1])  # Move north

def get_fuel_group(fuel_type):
    prefix = fuel_type[:2].upper()
    if prefix in fuel_type_adjustments:
        return prefix
    
    return "UNKNOWN"

# Calculates the rate of spread (ROS)
def calculate_ros(fuel_type, wind_speed, slope, moisture, live_fuel_moisture, fuel_model_params):
    """
    Calculate the Rate of Spread (ROS) using Rothermel model.
    Returns:
        dict: {
            "fuel_type": str,
            "ros": float (m/min),
            "status_code": int (1=spread, 0=won't spread)
        }
    """
    if fuel_type.startswith("NB"):
        return {
        "fuel_type": fuel_type,
        "ros": 0.0,
        "status_code": 0
    }
    fuel = fuel_model_params[fuel_model_params['Fuel Model Code'] == fuel_type]
    
    if fuel.empty:
        raise ValueError("Fuel type not found in dataset.")
    
    w_0 = fuel['Fuel Load (1-hr)'].values[0]  # Dead fine fuel load (kg/m^2)
    w_10 = fuel['Fuel Load (10-hr)'].values[0]  # Medium fuel load
    w_100 = fuel['Fuel Load (100-hr)'].values[0]  # Heavy fuel load

    w_live_herb = fuel['Fuel Load (Live herb)'].values[0]  # Live herbaceous fuel
    extinction_moisture = fuel['Dead Fuel Extincion Moisture Percent'].values[0]
    sigma = fuel['SAV Ratio (Dead 1-hr)'].values[0]  # SAV ratio (m^2/m^3)
    fuel_bed_depth = fuel["Fuel Bed Depth"].values[0]

    h = fuel['Heat Content'].values[0] if 'Heat Content' in fuel.columns else 18000 # Heat content (J/kg)

    # dynamically calculate rho_p
    fuel_prefix = get_fuel_group(fuel_type)

    transfer_ratio = 1.0 # Default (Fully cured)
    if fuel_prefix in ["GR", "GS", "SH"]:
        if live_fuel_moisture >= 120:
            transfer_ratio = 0.0  # Fully green, no transfer
        elif live_fuel_moisture >= 90:
            transfer_ratio = 0.33  # 33% cured
        elif live_fuel_moisture >= 75:
            transfer_ratio = 0.50  # 50% cured
        elif live_fuel_moisture >= 60:
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
    reaction_intensity = h * (w_0 + 0.5 * w_10 + 0.2 * w_100) * (1 - moisture)
    rho_b = (w_0 + w_10 + w_100)/ fuel_bed_depth
    PARTICLE_DENSITY = 512  # kg/m^3
    beta = max(rho_b / PARTICLE_DENSITY, 1e-4)


    # Rate of spread
    ROS = (reaction_intensity * (1 + phi_wind + phi_slope)) / (beta * sigma)
    
    damping_effect = np.exp(-0.1 * (live_fuel_moisture - 30)) 
    ROS *= damping_effect

    ROS *= fuel_type_adjustments.get(fuel_prefix, 1.0)
    if ROS < 0.1:
        return { "fuel_type": fuel_type, "ros": 0.0, "status_code": 0 }

    return {
        "fuel_type": fuel_type,
        "ros": ROS,
        "status_code": 1 # Fire will spread
    }

# Test it
# location = (41.0, -106.0)
# location = (34.0549, -118.2426)  # coordinates input
# elevation, elevation2, moisture, temperature, wind_speed, slope, live_fuel_moisture = get_environmental_data(location)
# fuel_type = "GS2"
# result = calculate_ros(fuel_type, wind_speed, slope, moisture, live_fuel_moisture, fuel_model_params)
# print(f"{result['fuel_type']:>4} | ROS: {result['ros']:.1f} m/min | Status: {'Spread' if result['status_code'] else 'No Spread'}")




# run code : 
# python3 -m fire_spread_prediction.rothermel_model


'''
API response record for further check
API Response: {'Date': Timestamp('2025-03-19 18:00:00+0000', tz='UTC'), 'Temperature (2 m)': 5.4040003, 
'Soil Moisture (0-10 cm)': 0.195, 'Soil Moisture (10-40 cm)': 0.25, 'Soil Moisture (40-100 cm)': 0.232, 
'Soil Moisture (100-200 cm)': 0.251, 'Soil Temperature (0-10 cm)': 4.0115, 'Soil Temperature (10-40 cm)': 5.7115, 
'Soil Temperature (40-100 cm)': 3.9615002, 'Soil Temperature (100-200 cm)': 2.9115, 'Surface Temperature': 9.154, 
'Temperature (80 m)': 2.3245, 'Wind Speed (80 m)': 45.468437, 'Wind Direction (80 m)': 349.04596, 'elevation': 1592.0}
'''






