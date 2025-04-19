# Fire Spread Modeling & Firebreak Optimization
## Overview
This project looks to serve as an assistive tool to observe wildfire spread, identify high-risk areas, and suggest optimal firebreak placements for a given region to aid in reducing overall potential damage. 

Part 1: For fire spread, a modified MDP approach is used in addition to specifications outlined by the Rothermel Model to determine transition probablities based on environmental factors. Data is retrieved from: 
- [GlobCover: Global Land Cover Map](https://developers.google.com/earth-engine/datasets/catalog/ESA_GLOBCOVER_L4_200901_200912_V2_3) (Fuel Type)
- [Open-Meteo Forecasting API](https://open-meteo.com/en/docs) (Atmospheric Temperature, Surface Temperature, Soil Moisture, Wind Speed & Direction)

Part 2: In conjunction, local search (with simulated annealing) is utilized after simulating fire spread to determine the best length, angle, and location of a firebreak.  


## Demos for Different Regions


| <img src="https://github.com/user-attachments/assets/442eaa77-cfd7-4cdd-8a1f-4b082b010227" width="300"/> | <img src="https://github.com/user-attachments/assets/f7945bcd-84dc-48e3-bdd7-ad40af6fb95f" width="295"/> | <img src="https://github.com/user-attachments/assets/76d93de4-bb45-4d7a-aa65-aa486b7f5532" width="303"/> | 
|--------|--------|--------|
| <div align="center">Sierra Nevada Forest<br>Forest<br>(37.7397, -119.5746)</div> | <div align="center">Okefenokee Swamp<br>Swamp/Wetland<br>(30.7194, -82.1500)</div> | <div align="center">Lake Tahoe<br>Water Body<br>(39.0968, -120.0324)</div> |

## Directory Structure

```
## Directory Structure
- cached_grid_states/           # Saved environments that can be used (to reduce wait time).
- modeling/                     # Contains scripts for building environment, running the simulation, and utils
  - data_retrieval/             # GEE image segmentation, Open-Meteo interpeter, Rothermel look-up table.
  - fire_spread_sim.py          # Entry point to run optimization.
- sim_experimentation/          # Exploratory work done initially (2D and 3D visualizations).
- testing/                      # Test scripts to validate behavior of modeling scripts.
```

## Running the Project
### 1. Clone the repository.
```
git clone <repo_url>
cd <repo_name>
```

### 2. Install Dependencies
Make sure you have Python 3.8+ installed on your system. Then, install the dependencies listed in `requirements.txt`:
```
pip install -r requirements.txt
```

### 3. Configure Environment Specifics
You can either use a previously saved environment or specify your own parameters and generate a new one.
1. Using an existing environment: 
- From `cached_grid_states/environments` drag any one `.pkl` file out to the root directory. You are all set.

> [!WARNING]  
> If the steps below still prompt that you don't have access, then we would have to manually add the user as a contributor to the GCP Project.
2. Specifying your own environment:
   - Note: You will need a Google Earth Engine & Google Cloud Account to generate an environment. If new parameters are specified, a new environment must be constructed, and corresponding data is retrieved. New users may be asked on authenticate within the command line.
   - Navigate to `modeling/fire_spread_sim.py` and lines 57-60 to define the parameters:

```
# Define parameters (example values shown).
central_coordinate = (37.4869, -118.7086)  # (lat, lon)
radius = 10  # km
grid_size = 30  # n, makes up n x n grid
```

3. Specify the ignition point.
Also in `modeling/fire_spread_sim.py`, the ignition point can be adjusted on line 93 (defaults to center of the grid).
```
# Choose a fixed starting cell
start_x, start_y = grid_size // 2, grid_size // 2  # center of the new grid
```

### 4. Run the simulation script.
Navigate to `modeling/` and run:
```
python3 fire_spread_sim.py
```
If creating a new environment, it will take 5-10 minutes to build before running the simulation (also depends on the size of the grid). Logs are provided to help track where the program is.
