"""test_energy_balance.py

Unit tests for the energy balance module, validating zero PV, zero demand,
surplus, and deficit scenarios, as well as energy conservation laws.
"""

import pandas as pd
import pytest
from energy_balance import validate_and_align_data


def test_energy_balance_scenarios():
  """Test energy balance calculations under specific test scenarios:

  - Zero PV generation (Pure deficit)
  - Zero demand (Pure surplus)
  - Surplus condition (PV > Demand)
  - Deficit condition (Demand > PV)
  """
  timestamps = pd.date_range(start="2022-01-01", periods=4, freq="h")

  # Define mock test inputs:
  # Row 0: 0 W PV, 1.0 kWh Demand (Zero PV / Deficit case)
  # Row 1: 2000 W (2.0 kWh) PV, 0 kWh Demand (Zero Demand / Surplus case)
  # Row 2: 1500 W (1.5 kWh) PV, 0.5 kWh Demand (Surplus case: PV > Demand)
  # Row 3: 500 W (0.5 kWh) PV, 1.2 kWh Demand (Deficit case: Demand > PV)
  df_pv = pd.DataFrame({"P": [0.0, 2000.0, 1500.0, 500.0]}, index=timestamps)

  df_demand = pd.DataFrame({"demand_kWh": [1.0, 0.0, 0.5, 1.2]}, index=timestamps)

  # Run alignment and balance calculation
  df_model = validate_and_align_data(df_pv, df_demand)

  # 1. Spot checks for specific scenario values
  assert df_model.loc[timestamps[0], "deficit_kWh"] == pytest.approx(1.0)
  assert df_model.loc[timestamps[0], "surplus_kWh"] == pytest.approx(0.0)

  assert df_model.loc[timestamps[1], "surplus_kWh"] == pytest.approx(2.0)
  assert df_model.loc[timestamps[1], "deficit_kWh"] == pytest.approx(0.0)

  assert df_model.loc[timestamps[2], "surplus_kWh"] == pytest.approx(1.0)
  assert df_model.loc[timestamps[2], "deficit_kWh"] == pytest.approx(0.0)

  assert df_model.loc[timestamps[3], "deficit_kWh"] == pytest.approx(0.7)
  assert df_model.loc[timestamps[3], "surplus_kWh"] == pytest.approx(0.0)

  # 2. Conservation of Energy Checks
  # Net energy must equal Generation minus Demand
  expected_net = df_model["E_pv_kWh"] - df_model["E_demand_kWh"]
  pd.testing.assert_series_equal(
      df_model["E_net_kWh"], expected_net, check_names=False
  )

  # Net energy must also equal Surplus minus Deficit
  net_from_components = df_model["surplus_kWh"] - df_model["deficit_kWh"]
  pd.testing.assert_series_equal(
      df_model["E_net_kWh"], net_from_components, check_names=False
  )

  # 3. Physical Boundary Checks (Surplus and Deficit can never be negative)
  assert (df_model["surplus_kWh"] >= 0).all()
  assert (df_model["deficit_kWh"] >= 0).all()