"""energy_balance.py

Module for merging cleaned PV generation and synthetic household demand,
validating time and unit alignment, calculating hourly energy balances (surplus/deficit),
and aggregating metrics at daily, monthly, and yearly intervals.
"""

from pathlib import Path
import pandas as pd
from demand_model import create_household_demand


def load_clean_pv_data(file_path: str | Path) -> pd.DataFrame:
  """Loads the preprocessed PVGIS clean dataset with a DatetimeIndex."""
  file_path = Path(file_path)
  if not file_path.exists():
    raise FileNotFoundError(f"Processed PV data not found at: {file_path}")

  df_pv = pd.read_csv(file_path, parse_dates=["time"], index_col="time")
  return df_pv

# CAlculate time deltas function is defined to compute the time intervals between consecutive timestamps in hours. 
# It handles the first timestamp by using the next available interval and defaults to 1 hour for a single-timestamp dataset. 
# The function returns a pandas Series of time deltas.
def calculate_time_deltas(index: pd.DatetimeIndex) -> pd.Series:
    """
    Calculate time intervals between consecutive timestamps in hours.

    The first timestamp uses the next available interval.
    For a single-timestamp dataset, a default of 1 hour is used.
    """

    time_deltas = (
        index.to_series().diff().dt.total_seconds() / 3600.0
    )

    # Backfill the first row's NaN delta
    time_deltas = time_deltas.bfill().fillna(1.0)

    return time_deltas


def validate_and_align_data(
    df_pv: pd.DataFrame, df_demand: pd.DataFrame
) -> pd.DataFrame:
  """Confirms timeline alignment, checks for missing/duplicate timestamps, 
  validates data types, and ensures physical plausibility (no negative PV or demand) 
  before computing hourly energy balances.
  """
  # Ensure demand is indexed by timestamp if passed as column
  if "timestamp" in df_demand.columns:
    df_demand = df_demand.set_index("timestamp")

  # --- 1. Timestamp & Index Integrity Checks ---
  if not df_pv.index.is_unique:
    raise ValueError("Duplicate timestamps detected in PV dataset index.")
  if not df_demand.index.is_unique:
    raise ValueError("Duplicate timestamps detected in Demand dataset index.")

  # Check for missing timestamps (gaps in hourly frequency)
  # Assuming 1-hour frequency for both datasets
  expected_pv_index = pd.date_range(start=df_pv.index.min(), end=df_pv.index.max(), freq="h")
  if not df_pv.index.equals(expected_pv_index):
    missing_pv = expected_pv_index.difference(df_pv.index)
    if len(missing_pv) > 0:
      raise ValueError(f"Missing timestamps detected in PV dataset: {len(missing_pv)} gaps found.")

  expected_demand_index = pd.date_range(start=df_demand.index.min(), end=df_demand.index.max(), freq="h")
  if not df_demand.index.equals(expected_demand_index):
    missing_demand = expected_demand_index.difference(df_demand.index)
    if len(missing_demand) > 0:
      raise ValueError(f"Missing timestamps detected in Demand dataset: {len(missing_demand)} gaps found.")

  # --- 2. Length & Alignment Checks ---
  assert len(df_pv) == len(
      df_demand
  ), f"Length mismatch: PV has {len(df_pv)} rows, Demand has {len(df_demand)} rows."
  assert df_pv.index.equals(
      df_demand.index
  ), "Timestamps between PV data and demand profile do not align perfectly."

  # --- 3. Data Type & Missing Value Checks ---
  if df_pv["P"].isna().any():
    raise ValueError("Missing (NaN) values detected in PV power column 'P'.")
  if df_demand["demand_kWh"].isna().any():
    raise ValueError("Missing (NaN) values detected in household demand column.")

  if not pd.api.types.is_numeric_dtype(df_pv["P"]):
    raise TypeError("PV power column 'P' contains non-numeric data types.")
  if not pd.api.types.is_numeric_dtype(df_demand["demand_kWh"]):
    raise TypeError("Household demand column contains non-numeric data types.")

  # --- 4. Physical Plausibility Checks ---
  if (df_pv["P"] < 0).any():
    raise ValueError("Physical violation: Negative PV generation values detected.")
  if (df_demand["demand_kWh"] < 0).any():
    raise ValueError("Physical violation: Negative household demand values detected.")

  print("✓ All timestamp, alignment, data type, and physical plausibility checks passed successfully.")

  # --- 5. Compute Dynamic Time Deltas & Energy Balance ---

  df_model = pd.DataFrame(index=df_pv.index)

  # Calculate actual time intervals in hours
  time_deltas = calculate_time_deltas(df_pv.index)
  df_model["time_delta_hours"] = time_deltas

  # Energy (kWh) = Power (W) * Time (hours) / 1000
  df_model["E_pv_kWh"] = (df_pv["P"] * time_deltas) / 1000.0

  # Scale demand energy by the actual time interval length
  df_model["E_demand_kWh"] = df_demand["demand_kWh"] * time_deltas

  # Net energy, surplus, and deficit calculations
  df_model["E_net_kWh"] = df_model["E_pv_kWh"] - df_model["E_demand_kWh"]
  df_model["surplus_kWh"] = df_model["E_net_kWh"].clip(lower=0)
  df_model["deficit_kWh"] = (-df_model["E_net_kWh"]).clip(lower=0)

  return df_model


def calculate_aggregations(df_model: pd.DataFrame) -> dict:
  """Calculates total energy metrics aggregated across daily, monthly, and yearly intervals."""

  cols_to_sum = ["E_pv_kWh", "E_demand_kWh", "surplus_kWh", "deficit_kWh"]

  # Resample to daily, monthly ('ME' for month-end), and yearly ('YE' for year-end) sums
  daily = df_model[cols_to_sum].resample("D").sum()
  monthly = df_model[cols_to_sum].resample("ME").sum()
  yearly = df_model[cols_to_sum].resample("YE").sum()

  return {"daily": daily, "monthly": monthly, "yearly": yearly}


def save_energy_balance_results(
    # Save hourly simulation and aggregated results to the specified output directory.
    df_model: pd.DataFrame, aggregations: dict, output_dir: str | Path = "../results"
) -> None:
  """Saves hourly simulation and aggregated results to the results/ directory."""
  out_dir = Path(output_dir)
  out_dir.mkdir(parents=True, exist_ok=True)

  df_model.to_csv(out_dir / "hourly_energy_balance.csv")
  aggregations["daily"].to_csv(out_dir / "daily_energy_balance.csv")
  aggregations["monthly"].to_csv(out_dir / "monthly_energy_balance.csv")
  aggregations["yearly"].to_csv(out_dir / "yearly_energy_balance.csv")

  print(f"✓ All energy balance results successfully saved to: {out_dir.resolve()}")

# Prepare battery simulation inputs function is defined to convert the energy balance DataFrame into a list of dictionaries, 
# each representing an interval with relevant energy metrics. This prepares the data for battery simulation by extracting 
# PV energy, demand energy, and time delta for each timestamp.
def prepare_battery_simulation_inputs(
    df_model: pd.DataFrame,
) -> list[dict[str, float]]:
    """Prepares the necessary inputs for battery simulation based on the energy balance model."""
    intervals = []
    for timestamp, row in df_model.iterrows():
        interval = {
            "timestamp": timestamp,
            "pv_energy_kwh": row["E_pv_kWh"],
            "demand_energy_kwh": row["E_demand_kWh"],
            "time_delta_hours": row["time_delta_hours"],
        }
        intervals.append(interval)
    return intervals


if __name__ == "__main__":
  # Execution script when run directly
  pv_path = "../data/processed/pvgis_clean.csv"
  
  print("Loading clean PV data...")
  df_pv = load_clean_pv_data(pv_path)

  print("Generating synthetic demand profile...")
  df_demand = create_household_demand(df_pv.index, daily_energy=8.0)

  print("Validating alignment and calculating energy balance...")
  df_model = validate_and_align_data(df_pv, df_demand)

  print("Computing daily, monthly, and yearly aggregations...")
  aggs = calculate_aggregations(df_model)

  print("Saving results...")
  save_energy_balance_results(df_model, aggs)
