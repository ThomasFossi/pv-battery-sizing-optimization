
"""Battery lifetime simulation functions."""


def apply_battery_year_transition(
    current_capacity_kwh,
    current_stored_energy_kwh,
    annual_degradation,
    min_soc,
):
    """Apply one year of relative battery capacity degradation."""

    if not 0 <= annual_degradation < 1:
        raise ValueError("Annual degradation must be between 0 and 1.")

    if not 0 <= min_soc < 1:
        raise ValueError("Minimum SOC must be between 0 and 1.")

    if current_capacity_kwh <= 0:
        raise ValueError("Battery capacity must be positive.")

    minimum_stored_energy_kwh = current_capacity_kwh * min_soc

    if not (
        minimum_stored_energy_kwh
        <= current_stored_energy_kwh
        <= current_capacity_kwh
    ):
        raise ValueError(
            "Stored energy must be within the permitted SOC limits."
        )

    new_capacity_kwh = (
        current_capacity_kwh * (1 - annual_degradation)
    )

    new_stored_energy_kwh = (
        current_stored_energy_kwh * (1 - annual_degradation)
    )

    capacity_fade_loss_kwh = (
        current_stored_energy_kwh - new_stored_energy_kwh
    )

    return (
        new_capacity_kwh,
        new_stored_energy_kwh,
        capacity_fade_loss_kwh,
    )



def transfer_battery_energy(
    old_capacity_kwh,
    old_stored_energy_kwh,
    new_capacity_kwh,
    min_soc,
    old_discharge_efficiency,
    new_charge_efficiency,
):
    """Transfer stored energy from an old battery to its replacement."""

    if old_capacity_kwh <= 0 or new_capacity_kwh <= 0:
        raise ValueError("Battery capacities must be positive.")

    if not 0 <= min_soc < 1:
        raise ValueError("Minimum SOC must be between 0 and 1.")

    if not 0 < old_discharge_efficiency <= 1:
        raise ValueError("Old discharge efficiency must be above 0 and at most 1.")

    if not 0 < new_charge_efficiency <= 1:
        raise ValueError("New charge efficiency must be above 0 and at most 1.")

    old_minimum_energy = old_capacity_kwh * min_soc

    if not old_minimum_energy <= old_stored_energy_kwh <= old_capacity_kwh:
        raise ValueError("Old stored energy is outside permitted SOC limits.")

    # Energy available above the old battery's minimum SOC.
    available_energy = old_stored_energy_kwh - old_minimum_energy

    # Loss during discharge of the old battery.
    old_discharge_loss = (
        available_energy * (1 - old_discharge_efficiency)
    )

    energy_delivered = available_energy * old_discharge_efficiency

    # Loss during charging of the replacement battery.
    new_charge_loss = energy_delivered * (1 - new_charge_efficiency)

    potential_transferred_energy = (
        energy_delivered * new_charge_efficiency
    )

    # The replacement battery cannot exceed its maximum capacity.
    transferred_energy = min(
        potential_transferred_energy,
        new_capacity_kwh,
    )

    capacity_overflow_loss = (
        potential_transferred_energy - transferred_energy
    )

    # Grid top-up if transferred energy is below the new battery's minimum SOC.
    new_minimum_energy = new_capacity_kwh * min_soc

    grid_top_up_stored_energy = max(
        0.0,
        new_minimum_energy - transferred_energy,
    )

    grid_top_up_input = (
        grid_top_up_stored_energy / new_charge_efficiency
    )

    grid_top_up_charge_loss = (
        grid_top_up_input - grid_top_up_stored_energy
    )

    new_stored_energy = (
        transferred_energy + grid_top_up_stored_energy
    )

    return {
        "available_energy_kwh": available_energy,
        "old_battery_residual_energy_kwh": old_minimum_energy,
        "old_discharge_loss_kwh": old_discharge_loss,
        "energy_delivered_kwh": energy_delivered,
        "new_charge_loss_kwh": new_charge_loss,
        "transferred_energy_kwh": transferred_energy,
        "capacity_overflow_loss_kwh": capacity_overflow_loss,
        "grid_top_up_input_kwh": grid_top_up_input,
        "grid_top_up_charge_loss_kwh": grid_top_up_charge_loss,
        "new_stored_energy_kwh": new_stored_energy,
    }


def calculate_monthly_degradation(annual_degradation):
    """Convert an annual degradation rate into an equivalent monthly rate."""

    if not 0 <= annual_degradation < 1:
        raise ValueError(
            "Annual degradation must be between 0 and 1."
        )

    monthly_degradation = 1 - (
        1 - annual_degradation
    ) ** (1 / 12)

    return monthly_degradation


def calculate_degraded_pv_energy(
    initial_pv_energy_kwh,
    monthly_degradation,
    months_elapsed,
):
    """Calculate PV energy generation capacity after cumulative monthly degradation."""

    if initial_pv_energy_kwh < 0:
        raise ValueError("Initial PV energy cannot be negative.")

    if not 0 <= monthly_degradation < 1:
        raise ValueError(
            "Monthly degradation must be between 0 and 1."
        )

    if not isinstance(months_elapsed, int) or months_elapsed < 0:
        raise ValueError(
            "Months elapsed must be a non-negative integer."
        )

    degraded_energy_kwh = (
        initial_pv_energy_kwh
        * (1 - monthly_degradation) ** months_elapsed
    )

    return degraded_energy_kwh


def apply_battery_month_transition(
    current_capacity_kwh,
    current_stored_energy_kwh,
    monthly_degradation,
    min_soc,
):
    """Apply one month of relative battery capacity degradation."""

    if not 0 <= monthly_degradation < 1:
        raise ValueError(
            "Monthly degradation must be between 0 and 1."
        )

    if not 0 <= min_soc < 1:
        raise ValueError("Minimum SOC must be between 0 and 1.")

    if current_capacity_kwh <= 0:
        raise ValueError("Battery capacity must be positive.")

    minimum_stored_energy_kwh = current_capacity_kwh * min_soc

    if not (
        minimum_stored_energy_kwh
        <= current_stored_energy_kwh
        <= current_capacity_kwh
    ):
        raise ValueError(
            "Stored energy must be within the permitted SOC limits."
        )

    new_capacity_kwh = (
        current_capacity_kwh * (1 - monthly_degradation)
    )

    new_stored_energy_kwh = (
        current_stored_energy_kwh * (1 - monthly_degradation)
    )

    capacity_fade_loss_kwh = (
        current_stored_energy_kwh - new_stored_energy_kwh
    )

    return (
        new_capacity_kwh,
        new_stored_energy_kwh,
        capacity_fade_loss_kwh,
    )
