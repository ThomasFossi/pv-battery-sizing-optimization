
import pytest

from lifetime_simulation import apply_battery_year_transition
from lifetime_simulation import transfer_battery_energy

def test_battery_capacity_decreases_with_annual_degradation():
    new_capacity_kwh, new_stored_energy_kwh, capacity_fade_loss_kwh = (
        apply_battery_year_transition(
            current_capacity_kwh=5.0,
            current_stored_energy_kwh=2.5,
            annual_degradation=0.02,
            min_soc=0.20,
            replacement=False,
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
