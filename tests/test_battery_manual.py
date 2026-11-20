import pytest
from battery_model import calculate_battery_charging, check_battery_energy_balance, check_system_energy_balance
from battery_model import calculate_battery_discharging, simulate_battery
from battery_model import dispatch_battery

def test_battery_charging_capacity_limit():
    """Test that battery charging respects capacity limits."""

    result = calculate_battery_charging(
        pv_surplus_kwh=1.5,
        stored_energy_kwh=4.5,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        charge_efficiency=0.95,
        max_charge_power_kw=1.0
    )

    assert abs(result["charge_input_kwh"] - 0.5263157895) < 1e-10
    assert abs(result["energy_stored_kwh"] - 0.5) < 1e-10
    assert abs(result["new_stored_energy_kwh"] - 5.0) < 1e-10
    assert abs(result["remaining_surplus_kwh"] - 0.9736842105) < 1e-10

def test_stored_enrgy_cannot_exceed_capacity():
    """Test that stored energy cannot exceed battery capacity."""

    with pytest.raises(ValueError):
        calculate_battery_charging(
            pv_surplus_kwh=1.5,
            stored_energy_kwh=5.5,
            battery_capacity_kwh=5.0,
            time_delta_hours=1.0,
            charge_efficiency=0.95,
            max_charge_power_kw=1.0
        )


def test_battery_discharging_power_limit():
    result = calculate_battery_discharging(
        demand_deficit_kwh=1.2,
        stored_energy_kwh=4.0,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_discharge_power_kw=1.0,
    )

    assert abs(result["discharge_output_kwh"] - 1.0) < 1e-9
    assert abs(result["energy_removed_kwh"] - 1.0526315789) < 1e-9
    assert abs(result["new_stored_energy_kwh"] - 2.9473684211) < 1e-9
    assert abs(result["remaining_deficit_kwh"] - 0.2) < 1e-9

def test_battery_discharging_min_soc_limit():
    """Test that battery discharging respects minimum state of charge (SOC) limits."""

    result = calculate_battery_discharging(
        demand_deficit_kwh=1.0,
        stored_energy_kwh=1.5,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_discharge_power_kw=1.0,
    )

    assert abs(result["discharge_output_kwh"] - 0.475) < 1e-9
    assert abs(result["energy_removed_kwh"] - 0.5) < 1e-9
    assert abs(result["new_stored_energy_kwh"] - 1.0) < 1e-9
    assert abs(result["remaining_deficit_kwh"] - 0.525) < 1e-9

def test_battery_charging_full_capacity():
    """Test that battery charging respects full capacity limits."""

    result = calculate_battery_charging(
        pv_surplus_kwh=2.0,
        stored_energy_kwh=4.8,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        charge_efficiency=0.95,
        max_charge_power_kw=1.0
    )

    assert abs(result["charge_input_kwh"] - 0.2105263158) < 1e-9
    assert abs(result["energy_stored_kwh"] - 0.2) < 1e-9
    assert abs(result["new_stored_energy_kwh"] - 5.0) < 1e-9
    assert abs(result["remaining_surplus_kwh"] - 1.7894736842) < 1e-9

def test_dispatch_battery_charging():
    result = dispatch_battery(
        pv_energy_kwh=1.5,
        demand_energy_kwh=0.8,
        stored_energy_kwh=2.0,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_charge_power_kw=1.0,
        max_discharge_power_kw=1.0,
    )

    assert abs(result["charge_input_kwh"] - 0.7) < 1e-9
    assert abs(result["energy_stored_kwh"] - 0.665) < 1e-9
    assert abs(result["new_stored_energy_kwh"] - 2.665) < 1e-9
    assert abs(result["grid_export_kwh"]) < 1e-9
    assert abs(result["new_soc"] - 53.3) < 1e-9

    assert result["discharge_output_kwh"] == 0.0
    assert result["grid_import_kwh"] == 0.0

def test_dispatch_battery_discharging():
    result = dispatch_battery(
        pv_energy_kwh=0.5,
        demand_energy_kwh=1.2,
        stored_energy_kwh=3.0,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_charge_power_kw=1.0,
        max_discharge_power_kw=1.0,
    )

    assert abs(result["discharge_output_kwh"] - 0.7) < 1e-9
    assert abs(result["energy_removed_kwh"] - 0.7368421053) < 1e-9
    assert abs(result["new_stored_energy_kwh"] - 2.2631578947) < 1e-9
    assert abs(result["grid_import_kwh"] - 0.0) < 1e-9
    assert abs(result["new_soc"] - 45.2631578947) < 1e-9

    assert result["charge_input_kwh"] == 0.0
    assert result["grid_export_kwh"] == 0.0

def test_dispatch_battery_does_not_charge_and_discharge_simultaneously():
    """Test that the dispatch_battery function does not charge and discharge simultaneously."""

    result = dispatch_battery(
        pv_energy_kwh=2.0,
        demand_energy_kwh=1.0,
        stored_energy_kwh=2.0,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_charge_power_kw=1.0,
        max_discharge_power_kw=1.0,
    )

    assert result["energy_stored_kwh"] == 0.95
    assert result["discharge_output_kwh"] == 0.0
    assert result["new_stored_energy_kwh"] == 2.95
    assert result["grid_export_kwh"] == 0.0
    assert result["grid_import_kwh"] == 0.0


def test_battery_energy_balance_during_discharging():
    result = dispatch_battery(
        pv_energy_kwh=0.5,
        demand_energy_kwh=1.5,
        stored_energy_kwh=3.0,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_charge_power_kw=1.0,
        max_discharge_power_kw=1.0,
    )

    assert check_battery_energy_balance(
        initial_stored_energy_kwh=3.0,
        energy_stored_kwh=result["energy_stored_kwh"],
        energy_removed_kwh=result["energy_removed_kwh"],
        final_stored_energy_kwh=result["new_stored_energy_kwh"],
    )


def test_battery_energy_balance_during_charging():
    result = dispatch_battery(
        pv_energy_kwh=2.0,
        demand_energy_kwh=1.0,
        stored_energy_kwh=2.0,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_charge_power_kw=1.0,
        max_discharge_power_kw=1.0,
    )

    assert check_battery_energy_balance(
        initial_stored_energy_kwh=2.0,
        energy_stored_kwh=result["energy_stored_kwh"],
        energy_removed_kwh=result["energy_removed_kwh"],
        final_stored_energy_kwh=result["new_stored_energy_kwh"],
    )


def test_system_energy_balance_during_charging():
    result = dispatch_battery(
        pv_energy_kwh=2.0,
        demand_energy_kwh=1.0,
        stored_energy_kwh=2.0,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_charge_power_kw=1.0,
        max_discharge_power_kw=1.0,
    )

    assert check_system_energy_balance(
        pv_energy_kwh=2.0,
        demand_energy_kwh=1.0,
        grid_import_kwh=result["grid_import_kwh"],
        grid_export_kwh=result["grid_export_kwh"],
        charge_input_kwh=result["charge_input_kwh"],
        energy_stored_kwh=result["energy_stored_kwh"],
        energy_removed_kwh=result["energy_removed_kwh"],
        discharge_output_kwh=result["discharge_output_kwh"],
    )


def test_system_energy_balance_during_discharging():
    result = dispatch_battery(
        pv_energy_kwh=0.5,
        demand_energy_kwh=1.5,
        stored_energy_kwh=3.0,
        battery_capacity_kwh=5.0,
        time_delta_hours=1.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_charge_power_kw=1.0,
        max_discharge_power_kw=1.0,
    )

    assert check_system_energy_balance(
        pv_energy_kwh=0.5,
        demand_energy_kwh=1.5,
        grid_import_kwh=result["grid_import_kwh"],
        grid_export_kwh=result["grid_export_kwh"],
        charge_input_kwh=result["charge_input_kwh"],
        energy_stored_kwh=result["energy_stored_kwh"],
        energy_removed_kwh=result["energy_removed_kwh"],
        discharge_output_kwh=result["discharge_output_kwh"],
    )


def test_battery_energy_carries_over_between_intervals():

    stored_energy_kwh = 2.5

    intervals = [
        {"pv_energy_kwh": 1.0, "demand_energy_kwh": 0.5},
        {"pv_energy_kwh": 3.0, "demand_energy_kwh": 1.0},
        {"pv_energy_kwh": 0.2, "demand_energy_kwh": 1.5},
    ]

    for interval in intervals:
        result = dispatch_battery(
            pv_energy_kwh=interval["pv_energy_kwh"],
            demand_energy_kwh=interval["demand_energy_kwh"],
            stored_energy_kwh=stored_energy_kwh,
            battery_capacity_kwh=5.0,
            time_delta_hours=1.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=0.20,
            max_charge_power_kw=1.0,
            max_discharge_power_kw=1.0,
        )

        stored_energy_kwh = result["new_stored_energy_kwh"]

    assert abs(stored_energy_kwh - 2.8723684211) < 1e-9


def test_simulate_battery_carries_energy_between_intervals():

    intervals = [
        {
            "pv_energy_kwh": 1.0,
            "demand_energy_kwh": 0.5,
            "time_delta_hours": 1.0,
        },
        {
            "pv_energy_kwh": 3.0,
            "demand_energy_kwh": 1.0,
            "time_delta_hours": 1.0,
        },
        {
            "pv_energy_kwh": 0.2,
            "demand_energy_kwh": 1.5,
            "time_delta_hours": 1.0,
        },
    ]

    results = simulate_battery(
        intervals=intervals,
        initial_stored_energy_kwh=2.5,
        battery_capacity_kwh=5.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_charge_power_kw=1.0,
        max_discharge_power_kw=1.0,
    )

    assert len(results) == 3

    assert abs(
        results[0]["new_stored_energy_kwh"] - 2.975
    ) < 1e-9

    assert abs(
        results[1]["new_stored_energy_kwh"] - 3.925
    ) < 1e-9

    assert abs(
        results[2]["new_stored_energy_kwh"] - 2.8723684211
    ) < 1e-9

def test_simulate_battery_with_empty_intervals():
    """Test that simulate_battery handles an empty list of intervals gracefully."""

    results = simulate_battery(
        intervals=[],
        initial_stored_energy_kwh=2.5,
        battery_capacity_kwh=5.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        min_soc=0.20,
        max_charge_power_kw=1.0,
        max_discharge_power_kw=1.0,
    )

    assert results == []


def test_simulate_battery_rejects_zero_capacity_with_empty_intervals():
    with pytest.raises(ValueError, match="Battery capacity must be positive"):
        simulate_battery(
            intervals=[],
            initial_stored_energy_kwh=0.0,
            battery_capacity_kwh=0.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=0.20,
            max_charge_power_kw=1.0,
            max_discharge_power_kw=1.0,
        )

def test_simulate_battery_rejects_invalid_charge_efficiency():
    with pytest.raises(ValueError, match="Invalid charging efficiency"):
        simulate_battery(
            intervals=[],
            initial_stored_energy_kwh=2.5,
            battery_capacity_kwh=5.0,
            charge_efficiency=0.0,  # Invalid efficiency
            discharge_efficiency=0.95,
            min_soc=0.20,
            max_charge_power_kw=1.0,
            max_discharge_power_kw=1.0,
        )

def test_simulate_battery_rejects_invalid_discharge_efficiency():
    with pytest.raises(ValueError, match="Invalid discharging efficiency"):
        simulate_battery(
            intervals=[],
            initial_stored_energy_kwh=2.5,
            battery_capacity_kwh=5.0,
            charge_efficiency=0.95,
            discharge_efficiency=1.5,  # Invalid efficiency
            min_soc=0.20,
            max_charge_power_kw=1.0,
            max_discharge_power_kw=1.0,
        )
def test_simulate_battery_rejects_invalid_min_soc():
    with pytest.raises(ValueError, match="min_soc must be between 0.0 and 1.0"):
        simulate_battery(
            intervals=[],
            initial_stored_energy_kwh=2.5,
            battery_capacity_kwh=5.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=1.1,  # Invalid min SOC
            max_charge_power_kw=1.0,
            max_discharge_power_kw=1.0,
        )

def test_simulate_battery_rejects_invalid_negative_max_charge_power():
    with pytest.raises(ValueError, match="Maximum charging power must be non-negative"):
        simulate_battery(
            intervals=[],
            initial_stored_energy_kwh=2.5,
            battery_capacity_kwh=5.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=0.20,
            max_charge_power_kw=-1.0,  # Invalid negative max charge power
            max_discharge_power_kw=1.0,
        )

def test_simulate_battery_rejects_invalid_negative_max_discharge_power():
    with pytest.raises(ValueError, match="Maximum discharging power must be non-negative"):
        simulate_battery(
            intervals=[],
            initial_stored_energy_kwh=2.5,
            battery_capacity_kwh=5.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=0.20,
            max_charge_power_kw=1.0,
            max_discharge_power_kw=-1.0,  # Invalid negative max discharge power
        )