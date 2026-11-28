"""Orchestration of the complete PV-battery lifetime simulation."""

import pandas as pd
from dataclasses import dataclass

from lifetime_simulation import (
    apply_battery_month_transition,
    calculate_monthly_degradation,
    calculate_degraded_pv_energy,
    transfer_battery_energy,
)

from demand_model import create_household_demand
from energy_balance import (
    validate_and_align_data,
    prepare_battery_simulation_inputs,
)
from battery_model import simulate_battery

@dataclass
class LifetimeSimulationOutput:
    """Results of a complete PV-battery lifetime simulation."""

    df_hourly: pd.DataFrame
    df_monthly: pd.DataFrame
    summary: dict[str, float]

def prepare_lifetime_monthly_data(
    df_pv: pd.DataFrame,
    daily_demand_kwh: float = 8.0,
    simulation_months: int = 240,
) -> pd.DataFrame:
    """Prepare hourly energy balances and assign simulation months."""

    if df_pv.empty:
        raise ValueError("PV dataset cannot be empty.")

    if not isinstance(df_pv.index, pd.DatetimeIndex):
        raise TypeError("PV dataset must have a DatetimeIndex.")

    if (
        not isinstance(simulation_months, int)
        or isinstance(simulation_months, bool)
        or simulation_months <= 0
    ):
        raise ValueError("Simulation months must be a positive integer.")

    # 1. Generate household demand over the complete timeline.
    df_demand = create_household_demand(
        timestamps=df_pv.index,
        daily_energy=daily_demand_kwh,
    )

    # 2. Calculate the complete energy balance only once.
    df_balance = validate_and_align_data(
        df_pv,
        df_demand,
    )

    # 3. Generate monthly boundaries aligned with the first timestamp.
    start_timestamp = df_pv.index[0]

    month_boundaries = pd.DatetimeIndex(
        [
            start_timestamp + pd.DateOffset(months=month)
            for month in range(simulation_months + 1)
        ]
    )

    # 4. Assign each hourly observation to its simulation month.
    df_balance["simulation_month"] = (
        month_boundaries.searchsorted(
            df_balance.index,
            side="right",
        )
    )

    # 5. Verify that every observation belongs to a valid month.
    if (
        (df_balance["simulation_month"] < 1).any()
        or (df_balance["simulation_month"] > simulation_months).any()
    ):
        raise ValueError(
            "Some PV observations fall outside the simulation period."
        )

    # 6. Verify that all simulation months contain observations.
    monthly_counts = (
        df_balance["simulation_month"]
        .value_counts()
        .reindex(range(1, simulation_months + 1), fill_value=0)
    )

    if (monthly_counts == 0).any():
        raise ValueError("One or more simulation months are empty.")

    return df_balance


def simulate_monthly_battery_dispatch(
    df_month: pd.DataFrame,
    initial_stored_energy_kwh: float,
    battery_capacity_kwh: float,
    charge_efficiency: float,
    discharge_efficiency: float,
    min_soc: float,
    max_charge_power_kw: float | None = 1.0,
    max_discharge_power_kw: float | None = 1.0,
) -> pd.DataFrame:
    """Simulate battery dispatch over one lifetime simulation month."""

    required_columns = [
        "E_pv_kWh",
        "E_pv_degraded_kWh",
        "E_demand_kWh",
        "time_delta_hours",
        "simulation_month",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df_month.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df_month.empty:
        raise ValueError("Monthly dataset cannot be empty.")

    if df_month["simulation_month"].nunique() != 1:
        raise ValueError(
            "Dataset must contain exactly one simulation month."
        )

    # Create a temporary copy for battery dispatch.
    df_dispatch = df_month.copy()

    # Use degraded PV generation instead of original PV generation.
    df_dispatch["E_pv_kWh"] = df_dispatch["E_pv_degraded_kWh"]

    # Convert the monthly dataframe into battery input intervals.
    intervals = prepare_battery_simulation_inputs(df_dispatch)

    # Simulate battery operation sequentially.
    results = simulate_battery(
        intervals=intervals,
        initial_stored_energy_kwh=initial_stored_energy_kwh,
        battery_capacity_kwh=battery_capacity_kwh,
        charge_efficiency=charge_efficiency,
        discharge_efficiency=discharge_efficiency,
        min_soc=min_soc,
        max_charge_power_kw=max_charge_power_kw,
        max_discharge_power_kw=max_discharge_power_kw,
    )

    # Return hourly results indexed by timestamp.
    df_hourly = pd.DataFrame(results).set_index("timestamp")

    return df_hourly

def run_lifetime_simulation(
    df_pv: pd.DataFrame,
    daily_demand_kwh: float = 8.0,
    battery_capacity_kwh: float = 5.0,
    initial_stored_energy_kwh: float = 2.5,
    charge_efficiency: float = 0.95,
    discharge_efficiency: float = 0.95,
    min_soc: float = 0.20,
    max_charge_power_kw: float | None = 1.0,
    max_discharge_power_kw: float | None = 1.0,
    annual_battery_degradation: float = 0.02,
    annual_pv_degradation: float = 0.0025,
    replacement_month: int = 169,
    simulation_months: int = 240,
) -> LifetimeSimulationOutput:
    """Run a complete monthly PV-battery lifetime simulation."""
    pass