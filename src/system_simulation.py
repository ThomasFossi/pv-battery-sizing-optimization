
"""
system_simulation.py

Consolidation of the PV, household demand,
energy balance, and battery simulation modules.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from battery_model import simulate_battery
from demand_model import create_household_demand
from energy_balance import (
    load_clean_pv_data,
    prepare_battery_simulation_inputs,
    validate_and_align_data,
)


@dataclass
class SimulationOutput:
    """Container for complete system simulation results."""

    df_balance: pd.DataFrame
    df_battery: pd.DataFrame
    summary: dict[str, float]


def compute_simulation_summary(
    df_battery: pd.DataFrame,
    initial_stored_energy_kwh: float,
) -> dict[str, float]:
    """Calculate aggregate energy and performance metrics."""

    if df_battery.empty:
        raise ValueError("Battery simulation results are empty.")

    total_pv_kwh = float(df_battery["pv_energy_kwh"].sum())
    total_demand_kwh = float(df_battery["demand_energy_kwh"].sum())

    charge_input_kwh = float(df_battery["charge_input_kwh"].sum())
    energy_stored_kwh = float(df_battery["energy_stored_kwh"].sum())

    discharge_output_kwh = float(
        df_battery["discharge_output_kwh"].sum()
    )
    energy_removed_kwh = float(df_battery["energy_removed_kwh"].sum())

    grid_import_kwh = float(df_battery["grid_import_kwh"].sum())
    grid_export_kwh = float(df_battery["grid_export_kwh"].sum())

    final_stored_energy_kwh = float(
        df_battery["new_stored_energy_kwh"].iloc[-1]
    )

    pv_self_consumption_pct = (
        (total_pv_kwh - grid_export_kwh) / total_pv_kwh * 100
        if total_pv_kwh > 0
        else 0.0
    )

    household_self_sufficiency_pct = (
        (total_demand_kwh - grid_import_kwh)
        / total_demand_kwh
        * 100
        if total_demand_kwh > 0
        else 0.0
    )

    charge_losses_kwh = charge_input_kwh - energy_stored_kwh

    discharge_losses_kwh = (
        energy_removed_kwh - discharge_output_kwh
    )

    return {
        "total_pv_kwh": total_pv_kwh,
        "total_demand_kwh": total_demand_kwh,
        "charge_input_kwh": charge_input_kwh,
        "energy_stored_kwh": energy_stored_kwh,
        "discharge_output_kwh": discharge_output_kwh,
        "energy_removed_kwh": energy_removed_kwh,
        "grid_import_kwh": grid_import_kwh,
        "grid_export_kwh": grid_export_kwh,
        "initial_stored_energy_kwh": float(
            initial_stored_energy_kwh
        ),
        "final_stored_energy_kwh": final_stored_energy_kwh,
        "charge_losses_kwh": charge_losses_kwh,
        "discharge_losses_kwh": discharge_losses_kwh,
        "total_battery_losses_kwh": (
            charge_losses_kwh + discharge_losses_kwh
        ),
        "pv_self_consumption_pct": pv_self_consumption_pct,
        "household_self_sufficiency_pct": (
            household_self_sufficiency_pct
        ),
    }


def run_system_simulation(
    pv_data_path: str | Path,
    daily_demand_kwh: float = 8.0,
    battery_capacity_kwh: float = 5.0,
    initial_stored_energy_kwh: float = 2.5,
    charge_efficiency: float = 0.95,
    discharge_efficiency: float = 0.95,
    min_soc: float = 0.20,
    max_charge_power_kw: float | None = 1.0,
    max_discharge_power_kw: float | None = 1.0,
    df_pv: pd.DataFrame | None = None,
) -> SimulationOutput:
    """Run the complete PV, demand, and battery simulation."""

    # 1. Load processed PV data or use the supplied DataFrame.
    if df_pv is None:
        pv_df = load_clean_pv_data(pv_data_path)
    else:
        pv_df = df_pv.copy()

    if pv_df.empty:
        raise ValueError("PV dataset is empty.")

    # 2. Generate household electricity demand.
    df_demand = create_household_demand(
        timestamps=pv_df.index,
        daily_energy=daily_demand_kwh,
    )

    # 3. Integrate PV generation and household demand.
    df_balance = validate_and_align_data(
        pv_df,
        df_demand,
    )

    # 4. Prepare inputs using the existing energy balance function.
    intervals = prepare_battery_simulation_inputs(df_balance)

    if not intervals:
        raise ValueError("No battery simulation intervals available.")

    # 5. Run the existing battery simulation.
    sim_records = simulate_battery(
        intervals=intervals,
        initial_stored_energy_kwh=initial_stored_energy_kwh,
        battery_capacity_kwh=battery_capacity_kwh,
        charge_efficiency=charge_efficiency,
        discharge_efficiency=discharge_efficiency,
        min_soc=min_soc,
        max_charge_power_kw=max_charge_power_kw,
        max_discharge_power_kw=max_discharge_power_kw,
    )

    # 6. Convert results into a DataFrame.
    df_battery = pd.DataFrame(sim_records)

    df_battery = df_battery.set_index("timestamp")

    # 7. Calculate overall system performance.
    summary = compute_simulation_summary(
        df_battery,
        initial_stored_energy_kwh,
    )

    return SimulationOutput(
        df_balance=df_balance,
        df_battery=df_battery,
        summary=summary,
    )


if __name__ == "__main__":

    project_root = Path(__file__).resolve().parent.parent

    default_pv_path = (
        project_root
        / "data"
        / "processed"
        / "pvgis_clean.csv"
    )

    output = run_system_simulation(
        pv_data_path=default_pv_path
    )

    print("\nSYSTEM SIMULATION SUMMARY")
    print("-" * 40)

    for key, value in output.summary.items():
        print(f"{key}: {value:.4f}")
