"""demand_model.py

Module for generating and managing synthetic household electricity demand profiles
based on standardized hourly load curves.
"""

import numpy as np
import pandas as pd


def create_household_demand(
    timestamps: pd.DatetimeIndex, daily_energy: float = 8.0
) -> pd.DataFrame:
  """Generates an hourly household electricity demand profile aligned with given timestamps

  using a standardized daily load shape for a German household.

  Parameters:
  - timestamps (pd.DatetimeIndex or array-like): The hourly timeline for the simulation.
  - daily_energy (float): Target daily energy consumption in kWh (default: 8.0 kWh).

  Returns:
  - pd.DataFrame: DataFrame containing 'timestamp' and 'demand_kWh' columns.
  """
  # Standardized 24-hour load shape distribution for a typical German household
  base_profile = np.array([
      0.147,
      0.117,
      0.117,
      0.117,
      0.147,
      0.244,
      0.440,
      0.538,
      0.342,
      0.244,
      0.215,
      0.215,
      0.244,
      0.244,
      0.244,
      0.274,
      0.342,
      0.538,
      0.733,
      0.831,
      0.635,
      0.440,
      0.342,
      0.244,
  ])

  # Normalize base profile to precisely match the target daily energy sum
  base_profile = base_profile * (daily_energy / base_profile.sum())

  # Convert to DatetimeIndex and drop any NaT (Not a Time) rows
  clean_timestamps = pd.DatetimeIndex(pd.to_datetime(timestamps)).dropna()

  # Extract hours safely as an integer numpy array and map to the profile
  hours = clean_timestamps.hour.to_numpy().astype(int)
  demand = base_profile[hours]

  return pd.DataFrame({"timestamp": clean_timestamps, "demand_kWh": demand})