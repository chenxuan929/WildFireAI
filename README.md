# Predicting Wildfire Spread and Optimizing Firebreak Placement  

## 1. Fire Spread Forecasting  

For a given environment (whether randomly generated or derived from specific coordinates), predict the likelihood of fire spread from a starting cell based on factors such as:  

- **Vegetation Type / Fuel Type**  
- **Elevation**  
- **Moisture**  
- **Temperature**  
- **Wind Speed / Direction** (to be incorporated later)  

### **Markov Model Approach**  

#### **Environment Representation**  
The environment consists of an **n × n** grid of cells, each representing a fixed area. The properties of each cell are derived from:  

- **Land Cover / Fuel Type**: Google Earth Engine, US Land Cover  
- **Elevation, Moisture, Temperature**: Open-Meteo API  

#### **State of Each Cell**  
Each cell exists in one of three states:  
1. **Untouched**  
2. **Burning**  
3. **Burned**  

#### **Transition Probabilities**  
Fire spread transitions are modeled using the **Rothermel Model**, considering:  
- **Fuel Load**  
- **Surface-Area-to-Volume (SAV) Ratio**  
- **Fuel Depth**  
- **Dead Fuel Extinction (Moisture Content)**  
- **Heat Content (Temperature)**  

There are **7 main classifications** for fuel types.  

#### **Simulation Mechanism**  
- The agent will have access only to **directly adjacent cells**.  
- Fire spread probabilities are assigned based on transition probabilities.  

---

## 2. Firebreak Optimization  

Using wildfire simulation runs (or multiple runs from different starting cells) within the same environment, the model will:  
- Analyze fire spread patterns  
- Suggest **optimal locations** for firebreak placement  

---

## 3. End-to-End Workflow  

- **High-Level Design Choices**  
  - Environment selection  
  - Algorithm and model selection  
  - Fire spread simulation approach  

- **Team Responsibilities & Timeline**  
  - **Tentative division of work**  
  - **Soft deliverables and milestones**  
