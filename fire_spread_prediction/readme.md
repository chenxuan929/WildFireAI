# WildFireAI: Rothermel Fire Spread Model

This project simulates wildfire spread across a 2D landscape using the Rothermel model, integrating real-time environmental data from Open-Meteo and land cover data from Google Earth Engine.

## Features

- Calculates Rate of Spread (ROS) using the Rothermel fire spread model
- Dynamically adjusts for live fuel moisture content (LFMC) using soil moisture and temperature
- Uses wind, slope, and fuel type to simulate fire behavior
- Models curing of live herbaceous fuel into dead fuel
- Prevents fire spread in overly moist or non-burnable fuel types
- Includes fuel-specific adjustment factors

## File Overview

### `rothermel_model.py`
Core logic for calculating ROS per cell based on environmental and fuel parameters:
- `calculate_ros(...)`: Main ROS calculation function
- `get_environmental_data(...)`: Gathers weather and slope data
- `get_live_fuel_moisture(...)`: Estimates LFMC from soil moisture and temperature
- `calculate_slope(...)`: Computes slope based on elevation difference
- `get_fuel_group(...)`: Classifies fuel into broad categories (e.g., GR, GS, SH)

- \[
\text{ROS} = \text{ROS}_{\text{base}} \times (1 + 0.045 \times \text{wind\_speed}) \times (1 + 0.069 \times \text{slope}) \times \left(1 - \frac{\text{moisture} + 0.5 \times \text{live\_fuel\_moisture}}{\text{Moisture of extinction for the fuel}} \right)
\]


### `open_meteo_client.py`
Retrieves real-time weather data from Open-Meteo API.

### `google_earth_segmentation.py`
Maps GEE land cover codes to fuel models.

## Model Formulas and Logic

### 1. **Live Fuel Moisture (LFMC)**
Derived from top-layer soil moisture and air temperature:

```
lfmc = 30 + 100 * sm_top
if temperature > 25:
    lfmc -= (temperature - 25) * 1.5
lfmc = clamp(lfmc, 30, 120)
```

### 2. **Transfer Ratio for Live Herbaceous Fuels**
Live herbaceous fuel is partially converted to dead fuel depending on LFMC:

```
if lfmc >= 120: transfer_ratio = 0.0
elif lfmc >= 90: transfer_ratio = 0.33
elif lfmc >= 75: transfer_ratio = 0.50
elif lfmc >= 60: transfer_ratio = 0.67
else: transfer_ratio = 1.0
```

The converted fuel is added to the 1-hr dead fuel load:

```
w_0 += w_live_herb * transfer_ratio
```

### 3. **Moisture Cutoff**
If the current moisture exceeds extinction moisture:

```
if moisture > extinction_moisture:
    return ros = 0.0, status_code = 0
```

### 4. **Slope and Wind Factors**
Wind and slope affect the forward spread rate:

```
phi_wind = 0.4 * (wind_speed / sigma)^2
phi_slope = 5.275 * (tan(slope_angle))^1.35
```

### 5. **Bulk Density and Reaction Intensity**

```
reaction_intensity = h * (w_0 + 0.5 * w_10 + 0.2 * w_100) * (1 - moisture)
rho_b = (w_0 + w_10 + w_100) / fuel_bed_depth
beta = max(rho_b / particle_density, 1e-4)
```

### 6. **Base ROS Calculation**

```
ROS = (reaction_intensity * (1 + phi_wind + phi_slope)) / (beta * sigma)
```

### 7. **Damping by LFMC**

```
damping_effect = exp(-0.1 * (lfmc - 30))
ROS *= damping_effect
```

### 8. **Final Adjustment by Fuel Type**

```
ROS *= fuel_type_adjustment
if ROS < 10.0:
    return ros = 0.0, status_code = 0
```

## Example Simulation Run

To run the fire spread simulation:

```bash
python3 -m fire_spread_prediction.fire_spread_sim
```

## Output Format

```
Cell (10,10) | ROS: 184.0 | Spread Probability: 0.95
Fire spreads to cell (10,11)
```

## References

- Rothermel, R.C. (1972). A Mathematical Model for Predicting Fire Spread in Wildland Fuels
- Open-Meteo API (https://open-meteo.com/)
- LANDFIRE Fuel Models (https://landfire.gov/fuel.php)
```


