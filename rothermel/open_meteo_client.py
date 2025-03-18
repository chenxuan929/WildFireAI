import openmeteo_requests
import requests_cache
import pandas as pd
import numpy as np
from retry_requests import retry
from datetime import datetime, timezone

# Setup Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Pulls latest data based on closest hourly time (to current) in UCT.
def get_attributes_by_location(location):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": location[0],
        "longitude": location[1],
        "hourly": "temperature_2m,soil_moisture_0_to_10cm,soil_moisture_10_to_40cm,"
                  "soil_moisture_40_to_100cm,soil_moisture_100_to_200cm,"
                  "soil_temperature_0_to_10cm,soil_temperature_10_to_40cm,"
                  "soil_temperature_40_to_100cm,soil_temperature_100_to_200cm,"
                  "surface_temperature,temperature_80m,wind_speed_80m,wind_direction_80m",
        "models": "best_match"
    }
    
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    elevation = response.Elevation()
    print(f"Debug API Response: {response}")

    print(f"Coordinates: {response.Latitude()}°N, {response.Longitude()}°E, Elevation: {elevation}m")

    hourly = response.Hourly()
    num_vars = hourly.VariablesLength()
    print(f"Number of available variables: {num_vars}")

    feature_names = {
        "temperature_2m": "Temperature (2 m)",
        "soil_moisture_0_to_10cm": "Soil Moisture (0-10 cm)",
        "soil_moisture_10_to_40cm": "Soil Moisture (10-40 cm)",
        "soil_moisture_40_to_100cm": "Soil Moisture (40-100 cm)",
        "soil_moisture_100_to_200cm": "Soil Moisture (100-200 cm)",
        "soil_temperature_0_to_10cm": "Soil Temperature (0-10 cm)",
        "soil_temperature_10_to_40cm": "Soil Temperature (10-40 cm)",
        "soil_temperature_40_to_100cm": "Soil Temperature (40-100 cm)",
        "soil_temperature_100_to_200cm": "Soil Temperature (100-200 cm)",
        "surface_temperature": "Surface Temperature",
        "temperature_80m": "Temperature (80 m)",
        "wind_speed_80m": "Wind Speed (80 m)",
        "wind_direction_80m": "Wind Direction (80 m)"
    }

    # Convert timestamps to pandas datetime format.
    timestamps = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )

    # Get current UTC time.
    current_time = datetime.now(timezone.utc)

    # Find the index of the closest timestamp.
    closest_idx = np.argmin(np.abs(timestamps - current_time))

    # Extract the data for the closest time.
    hourly_data = {"Date": timestamps[closest_idx]}

    for i, feature in enumerate(feature_names.keys()):
        if i < num_vars:  # Ensure the variable exists in response.
            values = hourly.Variables(i).ValuesAsNumpy()
            hourly_data[feature_names[feature]] = values[closest_idx]  # Pick closest time value.
        else:
            print(f"Warning: {feature} is missing in the response!")
            hourly_data[feature_names[feature]] = None  # Assign None if missing.

    # Convert to a one-row DataFrame
    # hourly_dataframe = pd.DataFrame([hourly_data])
    hourly_data["elevation"] = elevation
    # print(hourly_data)
    return hourly_data

# Test it.
# get_attributes_by_location((34.0549, -118.2426))
