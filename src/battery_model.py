

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