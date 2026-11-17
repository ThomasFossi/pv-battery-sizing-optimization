# Model Assumptions & Methodology

## 1. PVGIS Configuration & Solar Resource Data

The solar generation data is sourced from hourly photovoltaic geographical information system (PVGIS) exports tailored to the project location.

### Location & System Specifications
* **Location:** Nordhausen, Germany (Latitude: $51.50^\circ$, Longitude: $10.81^\circ$).
* **Installed Peak Power ($P_{\text{peak}}$):** $1\text{ kWp}$.
* **System Geometry & Losses:** 
  * Panel Tilt Angle: $35^\circ$
  * Azimuth Angle: $0^\circ$ (South-facing)
  * Estimated System Losses: $14\%$ (standard, accounting for inverter inefficiencies, wiring, and thermal losses).
* **Temporal Resolution & Conventions:** 1-hour time steps covering multi-year weather datasets (e.g., 2022–2023), indexed using standard chronological timestamps.

### Key Dataset Variables (`P` Column)
* **Definition:** The column `P` in the PVGIS export represents the calculated hourly PV system power output.
* **Units:** Watts ($\text{W}$). During preprocessing (`src/pv_model.py`), this power is converted into energy units ($\text{kWh}$) over each dynamic time interval ($\Delta t$).

---

## 2. Household Electricity Demand Profile (Illustrative Assumptions)

To evaluate the system under realistic residential conditions without requiring proprietary smart-meter data, the model utilizes a **synthetic hourly load profile**.

### Core Parameters & Targets
* **Target Daily Energy Consumption ($E_{\text{daily}}$):** $8.0\text{ kWh/day}$.
* **Target Annual Energy Consumption:** $\approx 2,920\text{ kWh/year}$ (representative of a small residential household—approx. 2–3 occupants, non-electric heating, and no EV charging).
* **Temporal Resolution:** 1-hour intervals, perfectly synchronized with the PVGIS dataset.

### Methodology & Shape Distribution
The demand profile is generated using an illustrative normalized 24-hour weight vector designed to model typical residential behavior patterns (such as morning preparation peaks and evening cooking/lighting peaks):
* **Night Baseline (00:00 – 05:00):** Low, constant baseload for refrigeration and standby devices.
* **Morning Peak (06:00 – 08:00):** Rise in activity corresponding to waking up.
* **Daytime Trough (09:00 – 15:00):** Reduced occupancy while residents are away or active outdoors.
* **Evening Peak (17:00 – 21:00):** Maximum household load driven by lighting, cooking, and domestic appliances.

> **Note on Standardization:** The weight distribution represents **illustrative modeling assumptions** capturing general residential activity shapes rather than an officially standardized or measured smart-meter profile. It serves as a reproducible baseline to stress-test storage performance before introducing advanced stochastic load models.

---

## 3. Data Ingestion, Alignment & Energy Balance Pipeline

### Raw Data Preprocessing (`src/pv_model.py`)
* **Cleaning Pipeline:** Dynamically parses time-series headers, strips metadata and unit rows, enforces numeric `float64` types, drops trailing footer artifacts, and exports pristine data to `data/processed/pvgis_clean.csv`.

### Timeline Alignment & Energy Balance (`src/energy_balance.py`)
* **Integrity Checks:** Validates timestamp uniqueness, checks for hourly gaps, verifies data types, and enforces physical plausibility (rejecting negative PV generation or negative demand).
* **Dynamic Energy Calculations:** 
  * Computes time intervals ($\Delta t$) dynamically to ensure the model remains robust if time-step resolutions change.
  * **Net Energy ($E_{\text{net}}$):** $E_{\text{pv}} - E_{\text{demand}}$
  * **Surplus ($E_{\text{surplus}}$):** $\max(0, E_{\text{net}})$ — excess energy available for battery storage or grid export.
  * **Deficit ($E_{\text{deficit}}$):** $\max(0, -E_{\text{net}})$ — energy shortfall requiring battery discharge or grid supply.
* **Aggregations:** Computes cumulative sums across daily, monthly (`ME`), and yearly (`YE`) horizons, saving outputs to the `results/` directory.

---

## 4. Model Verification & Automated Testing

Automated unit tests (`pytest`) validate code reliability:
* **`test_demand_model.py`**: Verifies length consistency, non-negative values, and exact daily energy conservation.
* **`test_energy_balance.py`**: Validates zero PV, zero demand, surplus/deficit scenarios, data validation guardrails, and the strict conservation of energy.