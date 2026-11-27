"""Orchestration of the complete PV-battery lifetime simulation."""

import pandas as pd

from demand_model import create_household_demand
from energy_balance import validate_and_align_data


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
