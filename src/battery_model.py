""" Battery model functions for calculating charging and discharging behavior. """

def calculate_battery_charging(
    pv_surplus_kwh: float,
    stored_energy_kwh: float,
    battery_capacity_kwh: float,
    time_delta_hours: float,
    charge_efficiency: float,
    max_charge_power_kw: float | None = None,
) -> dict[str, float]:
  """Calculate battery charging during one time interval."""
  if not (0.0 < charge_efficiency <= 1.0):
    raise ValueError("charge_efficiency must be in the interval (0.0, 1.0].")
  if (
      pv_surplus_kwh < 0
      or stored_energy_kwh < 0
      or battery_capacity_kwh < 0
      or time_delta_hours < 0
  ):
    raise ValueError(
        "Energy, capacity, and time_delta_hours must be non-negative."
    )
  if stored_energy_kwh > battery_capacity_kwh:
    raise ValueError(
        "stored_energy_kwh cannot exceed battery_capacity_kwh."
    )
  if stored_energy_kwh > battery_capacity_kwh:
    raise ValueError(
        "stored_energy_kwh cannot exceed battery_capacity_kwh."
    )
  if max_charge_power_kw is not None and max_charge_power_kw < 0:
    raise ValueError("max_charge_power_kw must be non-negative or None.")

  # Available storage capacity (clamped at 0 against floating-point drift)
  free_capacity_kwh = max(0.0, battery_capacity_kwh - stored_energy_kwh)

  # Maximum energy accepted due to power limit
  if max_charge_power_kw is None:
    max_charge_energy_kwh = float("inf")
  else:
    max_charge_energy_kwh = max_charge_power_kw * time_delta_hours

  # Maximum input energy that can be accepted before hitting capacity
  max_energy_for_capacity_kwh = free_capacity_kwh / charge_efficiency

  # Actual energy drawn from PV surplus
  charge_input_kwh = min(
      pv_surplus_kwh,
      max_charge_energy_kwh,
      max_energy_for_capacity_kwh,
  )

  # Energy actually stored after charging losses
  energy_stored_kwh = charge_input_kwh * charge_efficiency

  # Updated stored energy (clamped to capacity against floating-point drift)
  new_stored_energy_kwh = min(
      battery_capacity_kwh, stored_energy_kwh + energy_stored_kwh
  )

  # Remaining PV surplus
  remaining_surplus_kwh = max(0.0, pv_surplus_kwh - charge_input_kwh)

  return {
      "charge_input_kwh": charge_input_kwh,
      "energy_stored_kwh": energy_stored_kwh,
      "new_stored_energy_kwh": new_stored_energy_kwh,
      "remaining_surplus_kwh": remaining_surplus_kwh,
  }

def calculate_battery_discharging(
    demand_deficit_kwh: float,
    stored_energy_kwh: float,
    battery_capacity_kwh: float,
    time_delta_hours: float,
    discharge_efficiency: float,
    min_soc: float,
    max_discharge_power_kw: float | None = None,
) -> dict[str, float]:

    """Calculate battery discharging during one time interval."""

    if not (0.0 < discharge_efficiency <= 1.0):
        raise ValueError("discharge_efficiency must be in (0.0, 1.0].")

    if not (0.0 <= min_soc <= 1.0):
        raise ValueError("min_soc must be between 0.0 and 1.0.")

    if (
        demand_deficit_kwh < 0
        or stored_energy_kwh < 0
        or battery_capacity_kwh < 0
        or time_delta_hours < 0
    ):
        raise ValueError("Energy, capacity, and time must be non-negative.")

    if stored_energy_kwh > battery_capacity_kwh:
        raise ValueError("Stored energy cannot exceed battery capacity.")

    if max_discharge_power_kw is not None and max_discharge_power_kw < 0:
        raise ValueError("Maximum discharge power must be non-negative.")

    # Minimum energy that must remain in the battery
    minimum_energy_kwh = battery_capacity_kwh * min_soc

    # Available internal energy for discharge
    available_energy_kwh = max(
        0.0, stored_energy_kwh - minimum_energy_kwh
    )

    # Maximum AC energy deliverable under the power limit
    if max_discharge_power_kw is None:
        max_discharge_energy_kwh = float("inf")
    else:
        max_discharge_energy_kwh = (
            max_discharge_power_kw * time_delta_hours
        )

    # Maximum AC energy deliverable based on available stored energy
    max_energy_from_soc_kwh = available_energy_kwh * discharge_efficiency

    # Actual energy delivered to household
    discharge_output_kwh = min(
        demand_deficit_kwh,
        max_discharge_energy_kwh,
        max_energy_from_soc_kwh,
    )

    # Internal energy removed from battery
    energy_removed_kwh = discharge_output_kwh / discharge_efficiency

    # Updated stored energy
    new_stored_energy_kwh = stored_energy_kwh - energy_removed_kwh

    # Remaining household deficit
    remaining_deficit_kwh = demand_deficit_kwh - discharge_output_kwh

    return {
        "discharge_output_kwh": discharge_output_kwh,
        "energy_removed_kwh": energy_removed_kwh,
        "new_stored_energy_kwh": new_stored_energy_kwh,
        "remaining_deficit_kwh": remaining_deficit_kwh,
    }

# Dispatch battery based on net PV surplus or demand deficit
def dispatch_battery(
    pv_energy_kwh: float,
    demand_energy_kwh: float,
    stored_energy_kwh: float,
    battery_capacity_kwh: float,
    time_delta_hours: float,
    charge_efficiency: float,
    discharge_efficiency: float,
    min_soc: float,
    max_charge_power_kw: float | None = None,
    max_discharge_power_kw: float | None = None,
) -> dict[str, float]:

    """Dispatch battery based on net PV surplus or demand deficit."""

    # --- Input validation ---

    if pv_energy_kwh < 0 or demand_energy_kwh < 0:
        raise ValueError("PV energy and demand must be non-negative.")

    if battery_capacity_kwh <= 0:
        raise ValueError("Battery capacity must be positive.")

    if not (0 <= stored_energy_kwh <= battery_capacity_kwh):
        raise ValueError("Stored energy must be within battery capacity.")

    if time_delta_hours <= 0:
        raise ValueError("Time delta must be positive.")

    if not (0 < charge_efficiency <= 1):
        raise ValueError("Invalid charging efficiency.")

    if not (0 < discharge_efficiency <= 1):
        raise ValueError("Invalid discharging efficiency.")

    if not (0 <= min_soc <= 1):
        raise ValueError("min_soc must be between 0 and 1.")

    if max_charge_power_kw is not None and max_charge_power_kw < 0:
        raise ValueError("Maximum charging power must be non-negative.")

    if max_discharge_power_kw is not None and max_discharge_power_kw < 0:
        raise ValueError("Maximum discharging power must be non-negative.")

    # --- Initialize results ---

    results = {
        "charge_input_kwh": 0.0, # Energy drawn from PV to charge the battery
        "energy_stored_kwh": 0.0, # Energy actually stored in the battery after charging
        "new_stored_energy_kwh": stored_energy_kwh,
        "remaining_surplus_kwh": 0.0, # PV surplus energy left after charging
        "discharge_output_kwh": 0.0, # Energy supplied to meet demand from the battery
        "energy_removed_kwh": 0.0, # Energy actually removed from the battery after discharging
        "remaining_deficit_kwh": 0.0, # Demand deficit left after discharging
        "new_soc": stored_energy_kwh / battery_capacity_kwh * 100,
        "grid_import_kwh": 0.0, # Energy imported from the grid to meet demand deficit
        "grid_export_kwh": 0.0, # Energy exported to the grid from PV surplus after battery charging
    }

    # --- Calculate net energy balance ---

    net_energy_kwh = pv_energy_kwh - demand_energy_kwh

    # --- Charging mode ---

    if net_energy_kwh > 0:

        charge_results = calculate_battery_charging(
            pv_surplus_kwh=net_energy_kwh,
            stored_energy_kwh=stored_energy_kwh,
            battery_capacity_kwh=battery_capacity_kwh,
            time_delta_hours=time_delta_hours,
            charge_efficiency=charge_efficiency,
            max_charge_power_kw=max_charge_power_kw,
        )

        results.update(charge_results)

        results["grid_export_kwh"] = (
            charge_results["remaining_surplus_kwh"]
        )

    # --- Discharging mode ---

    elif net_energy_kwh < 0:

        demand_deficit_kwh = abs(net_energy_kwh)

        discharge_results = calculate_battery_discharging(
            demand_deficit_kwh=demand_deficit_kwh,
            stored_energy_kwh=stored_energy_kwh,
            battery_capacity_kwh=battery_capacity_kwh,
            time_delta_hours=time_delta_hours,
            discharge_efficiency=discharge_efficiency,
            min_soc=min_soc,
            max_discharge_power_kw=max_discharge_power_kw,
        )

        results.update(discharge_results)

        results["grid_import_kwh"] = (
            discharge_results["remaining_deficit_kwh"]
        )

    # --- Update final SOC ---

    results["new_soc"] = (
        results["new_stored_energy_kwh"]
        / battery_capacity_kwh
        * 100
    )

    return results
# Check energy balance of the battery system
def check_battery_energy_balance(
    initial_stored_energy_kwh: float,
    energy_stored_kwh: float,
    energy_removed_kwh: float,
    final_stored_energy_kwh: float,
) -> bool:
    """Check energy balance of the battery system."""
    energy_in = (
        initial_stored_energy_kwh + energy_stored_kwh
    )

    energy_out = (
        final_stored_energy_kwh + energy_removed_kwh
    )

    return abs(energy_in - energy_out) < 1e-9

# Check energy balance across the entire household system, including PV, demand, grid, and battery.
def check_system_energy_balance(
    pv_energy_kwh: float,
    demand_energy_kwh: float,
    grid_import_kwh: float,
    grid_export_kwh: float,
    charge_input_kwh: float,
    energy_stored_kwh: float,
    energy_removed_kwh: float,
    discharge_output_kwh: float,
    tolerance: float = 1e-9,
) -> bool:
    """Check energy conservation across the household system."""

    charging_loss_kwh = (
        charge_input_kwh - energy_stored_kwh
    )

    discharging_loss_kwh = (
        energy_removed_kwh - discharge_output_kwh
    )

    total_battery_losses_kwh = (
        charging_loss_kwh + discharging_loss_kwh
    )

    change_in_storage_kwh = (
        energy_stored_kwh - energy_removed_kwh
    )

    energy_in = pv_energy_kwh + grid_import_kwh

    energy_out = (
        demand_energy_kwh
        + grid_export_kwh
        + total_battery_losses_kwh
        + change_in_storage_kwh
    )

    return abs(energy_in - energy_out) <= tolerance


# Simulate battery operation over a series of intervals 
def simulate_battery(
    intervals: list[dict[str, float]],
    initial_stored_energy_kwh: float,
    battery_capacity_kwh: float,
    charge_efficiency: float,
    discharge_efficiency: float,
    min_soc: float,
    max_charge_power_kw: float | None = None,
    max_discharge_power_kw: float | None = None,
) -> list[dict[str, float]]:
    """Simulate battery operation over consecutive intervals."""

    if battery_capacity_kwh <= 0:
        raise ValueError("Battery capacity must be positive.")

    if not (0.0 <= initial_stored_energy_kwh <= battery_capacity_kwh):
        raise ValueError(
            "Initial stored energy must be within battery capacity."
        )

    if not (0.0 < charge_efficiency <= 1.0):
        raise ValueError("Invalid charging efficiency.")

    if not (0.0 < discharge_efficiency <= 1.0):
        raise ValueError("Invalid discharging efficiency.")

    if not (0.0 <= min_soc <= 1.0):
        raise ValueError("min_soc must be between 0.0 and 1.0.")

    if max_charge_power_kw is not None and max_charge_power_kw < 0:
        raise ValueError("Maximum charging power must be non-negative.")

    if max_discharge_power_kw is not None and max_discharge_power_kw < 0:
        raise ValueError("Maximum discharging power must be non-negative.")
    if not (0 < charge_efficiency <= 1):
        raise ValueError("Charge efficiency must be between 0 and 1")

    stored_energy_kwh = initial_stored_energy_kwh
    simulation_results: list[dict[str, float]] = []

    for interval in intervals:
        result = dispatch_battery(
            pv_energy_kwh=interval["pv_energy_kwh"],
            demand_energy_kwh=interval["demand_energy_kwh"],
            stored_energy_kwh=stored_energy_kwh,
            battery_capacity_kwh=battery_capacity_kwh,
            time_delta_hours=interval["time_delta_hours"],
            charge_efficiency=charge_efficiency,
            discharge_efficiency=discharge_efficiency,
            min_soc=min_soc,
            max_charge_power_kw=max_charge_power_kw,
            max_discharge_power_kw=max_discharge_power_kw,
        )

        simulation_results.append({
            **interval,
            **result,
        })

        stored_energy_kwh = result["new_stored_energy_kwh"]

    return simulation_results

