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


def validate_and_align_data(
    df_pv: pd.DataFrame, df_demand: pd.DataFrame
) -> pd.DataFrame:
  """Confirms timeline overlap, matching lengths, and time index alignment

  between PV generation and household demand, then computes hourly energy balances.
  """
  # Ensure demand is indexed by timestamp
  if "timestamp" in df_demand.columns:
    df_demand = df_demand.set_index("timestamp")

  # 1. Validation checks
  assert len(df_pv) == len(
      df_demand
  ), f"Length mismatch: PV has {len(df_pv)} rows, Demand has {len(df_demand)} rows."
  assert df_pv.index.equals(
      df_demand.index
  ), "Timestamps between PV data and demand profile do not align perfectly."

  print("✓ Timeline length and timestamp alignment verified successfully.")

  # 2. Combine into a unified modeling DataFrame
  df_model = pd.DataFrame(index=df_pv.index)

  # Convert PV power from Watts (W) to kilowatt-hours (kWh) for 1-hour intervals
  df_model["E_pv_kWh"] = df_pv["P"] / 1000.0
  df_model["E_demand_kWh"] = df_demand["demand_kWh"]

  # 3. Calculate hourly net energy, surplus, and deficit
  # Net = Generation - Demand
  df_model["E_net_kWh"] = df_model["E_pv_kWh"] - df_model["E_demand_kWh"]

  # Surplus: Energy available when generation exceeds demand (stored or exported)
  df_model["surplus_kWh"] = df_model["E_net_kWh"].clip(lower=0)

  # Deficit: Energy needed when demand exceeds generation (drawn from battery or grid)
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