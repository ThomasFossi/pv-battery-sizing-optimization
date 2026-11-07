# Model Assumptions & Methodology

## 1. Household Electricity Demand Profile (Synthetic)

To evaluate the PV and battery system under realistic residential conditions without requiring proprietary smart-meter datasets, the model employs a **synthetic hourly load profile**.

### Core Parameters & Targets
* **Target Daily Energy Consumption ($E_{\text{daily}}$):** $8.0\text{ kWh/day}$
* **Target Annual Energy Consumption:** $\approx 2,920\text{ kWh/year}$ (typical for a small-to-medium multi-person household in Germany).
* **Temporal Resolution:** 1-hour intervals, perfectly synchronized with the PVGIS weather and generation dataset.

### Methodology & Shape Distribution
The demand profile is generated using a standardized 24-hour normalized weight vector that captures typical residential behavior patterns (such as morning preparation peaks and prominent evening cooking/lighting peaks):
* **Night Baseline (00:00 – 05:00):** Low, constant baseload for refrigeration and standby devices.
* **Morning Peak (06:00 – 08:00):** Rise in activity corresponding to waking up and breakfast.
* **Daytime Trough (09:00 – 15:00):** Reduced occupancy/demand while residents are away or active outdoors.
* **Evening Peak (17:00 – 21:00):** Maximum household load driven by lighting, cooking, entertainment, and domestic appliances.

### Synthetic Nature & Limitations
* **Deterministic Shape:** The load shape uses a fixed daily distribution pattern mapped across all days of the year. It does not currently incorporate stochastic variability (random fluctuations), weekend vs. weekday variations, or seasonal shifts in heating/cooling loads.
* **Purpose:** It serves as a robust, reproducible baseline to stress-test battery sizing algorithms before introducing advanced stochastic load generation models.

---

## 2. Model Verification & Automated Testing

To maintain software engineering rigor alongside energy modeling, automated unit tests are implemented using `pytest`.

### Test Suite Structure (`tests/`)
* **`test_demand_model.py`**: Verifies the synthetic demand generation pipeline by checking:
  1. **Dimensionality consistency:** Ensures output lengths match input timeline lengths precisely.
  2. **Physical constraints:** Confirms that all generated power values are strictly non-negative ($\ge 0$).
  3. **Energy conservation:** Validates that the integrated 24-hour energy sum matches the target daily consumption ($8.0\text{ kWh/day}$) within tight floating-point tolerances.