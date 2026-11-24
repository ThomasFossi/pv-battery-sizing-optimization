
import pytest

from lifetime_simulation import apply_battery_year_transition
from lifetime_simulation import transfer_battery_energy
from lifetime_simulation import calculate_monthly_degradation
from lifetime_simulation import calculate_degraded_pv_energy

def test_battery_capacity_decreases_with_annual_degradation():
    new_capacity_kwh, new_stored_energy_kwh, capacity_fade_loss_kwh = (
        apply_battery_year_transition(
            current_capacity_kwh=5.0,
            current_stored_energy_kwh=2.5,
            annual_degradation=0.02,
            min_soc=0.20,
        )
    )

    assert new_capacity_kwh == pytest.approx(4.9)
    assert new_stored_energy_kwh == pytest.approx(2.45)
    assert capacity_fade_loss_kwh == pytest.approx(0.05)


def test_battery_replacement_accounts_for_transfer_losses():
    result = transfer_battery_energy(
        old_capacity_kwh=5.0,
        old_stored_energy_kwh=2.5,
        new_capacity_kwh=5.0,
        min_soc=0.20,
        old_discharge_efficiency=0.95,
        new_charge_efficiency=0.95,
    )

    assert result["available_energy_kwh"] == pytest.approx(1.5)
    assert result["old_discharge_loss_kwh"] == pytest.approx(0.075)
    assert result["energy_delivered_kwh"] == pytest.approx(1.425)
    assert result["new_charge_loss_kwh"] == pytest.approx(0.07125)
    assert result["transferred_energy_kwh"] == pytest.approx(1.35375)
    assert result["new_stored_energy_kwh"] == pytest.approx(1.35375)
    assert result["grid_top_up_input_kwh"] == pytest.approx(0.0)


def test_battery_replacement_uses_grid_top_up_when_needed():
    result = transfer_battery_energy(
        old_capacity_kwh=5.0,
        old_stored_energy_kwh=1.0,
        new_capacity_kwh=5.0,
        min_soc=0.20,
        old_discharge_efficiency=0.95,
        new_charge_efficiency=0.95,
    )

    assert result["transferred_energy_kwh"] == pytest.approx(0.0)
    assert result["new_stored_energy_kwh"] == pytest.approx(1.0)
    assert result["grid_top_up_input_kwh"] == pytest.approx(1.0 / 0.95)


def test_battery_replacement_energy_balance():
    result = transfer_battery_energy(
        old_capacity_kwh=5.0,
        old_stored_energy_kwh=1.2,
        new_capacity_kwh=5.0,
        min_soc=0.20,
        old_discharge_efficiency=0.95,
        new_charge_efficiency=0.95,
    )

    energy_in = (
        1.2 + result["grid_top_up_input_kwh"]
    )

    energy_out = (
        result["old_battery_residual_energy_kwh"]
        + result["old_discharge_loss_kwh"]
        + result["new_charge_loss_kwh"]
        + result["grid_top_up_charge_loss_kwh"]
        + result["capacity_overflow_loss_kwh"]
        + result["new_stored_energy_kwh"]
    )

    assert energy_in == pytest.approx(energy_out)


def test_battery_soc_is_preserved_after_degradation():
    initial_capacity_kwh = 5.0
    initial_stored_energy_kwh = 2.5

    new_capacity, new_stored_energy, _ = (
        apply_battery_year_transition(
            current_capacity_kwh=initial_capacity_kwh,
            current_stored_energy_kwh=initial_stored_energy_kwh,
            annual_degradation=0.02,
            min_soc=0.20,
        )
    )

    initial_soc = initial_stored_energy_kwh / initial_capacity_kwh
    new_soc = new_stored_energy / new_capacity

    assert new_soc == pytest.approx(initial_soc)


def test_battery_transition_rejects_energy_below_minimum_soc():
    with pytest.raises(ValueError):
        apply_battery_year_transition(
            current_capacity_kwh=5.0,
            current_stored_energy_kwh=0.5,
            annual_degradation=0.02,
            min_soc=0.20,
        )


def test_monthly_battery_degradation():
    monthly_rate = calculate_monthly_degradation(0.02)

    assert monthly_rate == pytest.approx(0.001682, abs=0.000001)


def test_twelve_months_equal_annual_degradation():
    annual_rate = 0.02

    monthly_rate = calculate_monthly_degradation(annual_rate)

    remaining_capacity = (1 - monthly_rate) ** 12

    assert remaining_capacity == pytest.approx(1 - annual_rate)


def test_monthly_degradation_rejects_invalid_rate():
    with pytest.raises(ValueError):
        calculate_monthly_degradation(1.0)


def test_pv_energy_unchanged_at_zero_months():
    result = calculate_degraded_pv_energy(
        initial_pv_energy_kwh=1.0,
        monthly_degradation=0.0002087,
        months_elapsed=0,
    )

    assert result == pytest.approx(1.0)


def test_pv_energy_after_twelve_months():
    monthly_rate = calculate_monthly_degradation(0.0025)

    result = calculate_degraded_pv_energy(
        initial_pv_energy_kwh=1.0,
        monthly_degradation=monthly_rate,
        months_elapsed=12,
    )

    assert result == pytest.approx(0.9975)


def test_pv_energy_decreases_over_time():
    monthly_rate = calculate_monthly_degradation(0.0025)

    energy_after_12_months = calculate_degraded_pv_energy(
        1.0, monthly_rate, 12
    )

    energy_after_24_months = calculate_degraded_pv_energy(
        1.0, monthly_rate, 24
    )

    assert energy_after_24_months < energy_after_12_months


def test_pv_degradation_rejects_negative_energy():
    with pytest.raises(ValueError):
        calculate_degraded_pv_energy(-1.0, 0.001, 12)
