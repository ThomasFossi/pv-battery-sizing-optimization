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
    
    # Validate simulation horizon.
    if (
        not isinstance(simulation_months, int)
        or isinstance(simulation_months, bool)
        or simulation_months <= 0
    ):
        raise ValueError("Simulation months must be a positive integer.")

    if (
        not isinstance(replacement_month, int)
        or isinstance(replacement_month, bool)
        or replacement_month <= 0
    ):
        raise ValueError("Replacement month must be a positive integer.")

    if battery_capacity_kwh <= 0:
        raise ValueError("Battery capacity must be positive.")

    if not 0 <= min_soc < 1:
        raise ValueError("Minimum SOC must be between 0 and 1.")

    if not (
        battery_capacity_kwh * min_soc
        <= initial_stored_energy_kwh
        <= battery_capacity_kwh
    ):
        raise ValueError(
            "Initial stored energy must be within the permitted SOC limits."
        )

    # Calculate equivalent monthly degradation rates.
    monthly_battery_degradation = calculate_monthly_degradation(
        annual_battery_degradation
    )

    monthly_pv_degradation = calculate_monthly_degradation(
        annual_pv_degradation
    )

    # Prepare the complete hourly energy balance.
    df_balance = prepare_lifetime_monthly_data(
        df_pv=df_pv,
        daily_demand_kwh=daily_demand_kwh,
        simulation_months=simulation_months,
    )

    # Apply PV degradation using elapsed months.
    pv_degradation_factors = {
        month: calculate_degraded_pv_energy(
            initial_pv_energy_kwh=1.0,
            monthly_degradation=monthly_pv_degradation,
            months_elapsed=month - 1,
        )
        for month in range(1, simulation_months + 1)
    }

    df_balance["pv_degradation_factor"] = (
        df_balance["simulation_month"].map(
            pv_degradation_factors
        )
    )

    df_balance["E_pv_degraded_kWh"] = (
        df_balance["E_pv_kWh"]
        * df_balance["pv_degradation_factor"]
    )

    # Initialize battery state.
    current_battery_capacity_kwh = battery_capacity_kwh
    current_stored_energy_kwh = initial_stored_energy_kwh
    battery_age_months = 0

    hourly_results = []
    monthly_results = []

    # Process each month chronologically.
    for month, df_month in df_balance.groupby(
        "simulation_month",
        sort=True,
    ):

        # Initialize monthly accounting fields.
        capacity_fade_loss_kwh = 0.0
        stored_energy_degradation_loss_kwh = 0.0
        replacement_transfer_kwh = 0.0
        replacement_grid_top_up_kwh = 0.0
        battery_replaced = False

        # Apply battery degradation before dispatch,
        # except before the first month.
        if month > 1:
            previous_capacity_kwh = current_battery_capacity_kwh
            previous_stored_energy_kwh = current_stored_energy_kwh

            (
                current_battery_capacity_kwh,
                current_stored_energy_kwh,
                stored_energy_degradation_loss_kwh,
            ) = apply_battery_month_transition(
                current_capacity_kwh=current_battery_capacity_kwh,
                current_stored_energy_kwh=current_stored_energy_kwh,
                monthly_degradation=monthly_battery_degradation,
                min_soc=min_soc,
            )

            capacity_fade_loss_kwh = (
                previous_capacity_kwh
                - current_battery_capacity_kwh
            )

            battery_age_months += 1

        # Replace the battery before dispatch in the specified month.
        if month == replacement_month:
            replacement = transfer_battery_energy(
                old_capacity_kwh=current_battery_capacity_kwh,
                old_stored_energy_kwh=current_stored_energy_kwh,
                new_capacity_kwh=battery_capacity_kwh,
                min_soc=min_soc,
                old_discharge_efficiency=discharge_efficiency,
                new_charge_efficiency=charge_efficiency,
            )

            replacement_transfer_kwh = (
                replacement["transferred_energy_kwh"]
            )

            replacement_grid_top_up_kwh = (
                replacement["grid_top_up_input_kwh"]
            )

            current_battery_capacity_kwh = battery_capacity_kwh
            current_stored_energy_kwh = (
                replacement["new_stored_energy_kwh"]
            )

            battery_age_months = 0
            battery_replaced = True

        # Record the battery state at the beginning of dispatch.
        initial_monthly_stored_energy_kwh = (
            current_stored_energy_kwh
        )

        # Dispatch the battery over the month's hourly intervals.
        df_hourly_month = simulate_monthly_battery_dispatch(
            df_month=df_month,
            initial_stored_energy_kwh=current_stored_energy_kwh,
            battery_capacity_kwh=current_battery_capacity_kwh,
            charge_efficiency=charge_efficiency,
            discharge_efficiency=discharge_efficiency,
            min_soc=min_soc,
            max_charge_power_kw=max_charge_power_kw,
            max_discharge_power_kw=max_discharge_power_kw,
        )

        # Add lifetime metadata to the hourly results.
        df_hourly_month["simulation_month"] = month
        df_hourly_month["battery_age_months"] = battery_age_months
        df_hourly_month["battery_capacity_kwh"] = (
            current_battery_capacity_kwh
        )
        df_hourly_month["pv_degradation_factor"] = (
            pv_degradation_factors[month]
        )

        # Carry final stored energy into the next month.
        current_stored_energy_kwh = (
            df_hourly_month["new_stored_energy_kwh"].iloc[-1]
        )

        # Record monthly results.
        monthly_results.append({
            "month": month,
            "pv_degradation_months": month - 1,
            "battery_age_months": battery_age_months,
            "battery_capacity_kwh": current_battery_capacity_kwh,
            "initial_stored_energy_kwh": (
                initial_monthly_stored_energy_kwh
            ),
            "final_stored_energy_kwh": current_stored_energy_kwh,
            "pv_energy_kwh": df_hourly_month[
                "pv_energy_kwh"
            ].sum(),
            "demand_energy_kwh": df_hourly_month[
                "demand_energy_kwh"
            ].sum(),
            "grid_import_kwh": df_hourly_month[
                "grid_import_kwh"
            ].sum(),
            "grid_export_kwh": df_hourly_month[
                "grid_export_kwh"
            ].sum(),
            "capacity_fade_loss_kwh": capacity_fade_loss_kwh,
            "stored_energy_degradation_loss_kwh": (
                stored_energy_degradation_loss_kwh
            ),
            "battery_replaced": battery_replaced,
            "replacement_transfer_kwh": replacement_transfer_kwh,
            "replacement_grid_top_up_kwh": (
                replacement_grid_top_up_kwh
            ),
        })

        hourly_results.append(df_hourly_month)

    # Combine all hourly and monthly results.
    df_hourly = pd.concat(hourly_results)
    df_monthly = pd.DataFrame(monthly_results).set_index("month")

    # Calculate overall performance metrics.
    total_dispatch_grid_import_kwh = (
        df_monthly["grid_import_kwh"].sum()
    )

    total_replacement_grid_top_up_kwh = (
        df_monthly["replacement_grid_top_up_kwh"].sum()
    )

    summary = {
        "simulation_months": float(simulation_months),
        "total_pv_energy_kwh": df_monthly["pv_energy_kwh"].sum(),
        "total_demand_energy_kwh": df_monthly[
            "demand_energy_kwh"
        ].sum(),
        "total_grid_import_kwh": (
            total_dispatch_grid_import_kwh
            + total_replacement_grid_top_up_kwh
        ),
        "total_dispatch_grid_import_kwh": (
            total_dispatch_grid_import_kwh
        ),
        "total_replacement_grid_top_up_kwh": (
            total_replacement_grid_top_up_kwh
        ),
        "total_grid_export_kwh": df_monthly[
            "grid_export_kwh"
        ].sum(),
        "total_charge_input_kwh": df_hourly[
            "charge_input_kwh"
        ].sum(),
        "total_energy_stored_kwh": df_hourly[
            "energy_stored_kwh"
        ].sum(),
        "total_discharge_output_kwh": df_hourly[
            "discharge_output_kwh"
        ].sum(),
        "total_energy_removed_kwh": df_hourly[
            "energy_removed_kwh"
        ].sum(),
        "initial_battery_capacity_kwh": battery_capacity_kwh,
        "final_battery_capacity_kwh": current_battery_capacity_kwh,
        "initial_stored_energy_kwh": initial_stored_energy_kwh,
        "final_stored_energy_kwh": current_stored_energy_kwh,
        "battery_replacement_count": float(
            df_monthly["battery_replaced"].sum()
        ),
    }

    return LifetimeSimulationOutput(
        df_hourly=df_hourly,
        df_monthly=df_monthly,
        summary=summary,
    )
