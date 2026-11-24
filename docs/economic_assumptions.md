Economic Assumptions – PV and Battery Sizing Optimisation

1. Project objective

This document defines the economic assumptions used to evaluate residential photovoltaic (PV) and battery storage configurations over a 20-year project lifetime.

The objective is to identify the combination of PV capacity and battery capacity that minimises the household's total discounted electricity-system cost, accounting for:

- Initial investment costs
- Grid electricity purchases
- Revenue from surplus electricity exported to the grid
- Operation and maintenance costs
- Equipment degradation and replacement
- The time value of money

The analysis considers two economic scenarios: current German market conditions (Scenario A) and alternative future market conditions (Scenario B).

2. Reference household

Parameter| Assumption
Household size| 3 people
Annual electricity demand| 2,920 kWh
Average daily electricity demand| 8 kWh
Space heating| Central
Domestic hot water| Central
PV resource location| Nordhausen, Germany
Reference PV capacity| 1 kWp

3. Financial assumptions

Parameter| Value| Unit
Evaluation period| 20| years
Initial grid electricity price| 0.3618| €/kWh
Annual electricity price escalation| 2| %
Nominal discount rate| 4| %

The electricity price escalation and discount rate are initial modelling assumptions and will be examined through sensitivity analysis.

4. Scenario A – Current German market conditions

Scenario A represents the baseline economic case.

- Grid electricity price: €0.3618/kWh initially.
- Annual electricity price escalation: 2%.
- Nominal discount rate: 4%.
- PV and battery investment costs: current German market benchmarks.
- Feed-in remuneration: applicable German EEG rate, depending on system size, commissioning date and export arrangement.

5. Scenario B – Future market conditions

Scenario B examines alternative future economic developments.

The following variations will be investigated:

- Electricity price escalation: 1% and 4% annually.
- PV investment cost reductions: 10% and 20%.
- Battery investment cost reductions: 10% and 20%.
- Discount rate: initially unchanged at 4%.

These are sensitivity assumptions, not predictions of future market conditions.

6. Technical and financial parameters still to be established

The following inputs require further research or engineering justification:

- PV investment cost (€/kWp)
- Battery investment cost (€/kWh)
- Inverter and installation costs
- Annual operation and maintenance costs
- PV annual degradation rate
- Battery degradation model
- Battery replacement assumptions
- Inverter replacement assumptions
- Feed-in remuneration over the evaluation period
- Residual equipment value at year 20

7. Methodology

The economic performance of each configuration will be assessed using a 20-year net present value (NPV) calculation.

The analysis will distinguish between observed market data, official regulatory values and engineering modelling assumptions.

All assumptions will be documented with their units, sources and justification. Sensitivity analysis will be used to assess the effect of uncertainty on the optimal system configuration.

---

8. PV investment costs – Germany

8.1 Reference data

PV investment costs are based on the price analysis published by Verbraucherzentrale NRW on 28 August 2026.

The analysis evaluates 71 residential PV installation quotations collected between January 2025 and August 2026.

The reported average costs are:

PV system size| Average cost
4–6 kWp| €2,090/kWp
Above 6–8 kWp| €1,820/kWp
Above 8–9 kWp| €1,520/kWp
Above 9–10 kWp| €1,410/kWp
Above 10–12 kWp| €1,290/kWp
Above 12–14 kWp| €1,240/kWp

These figures refer to the PV installation without battery storage. Additional electrical work and optional features are excluded.

8.2 Modelling approach

PV investment cost will be modelled as a function of installed PV capacity rather than using one constant cost per kWp.

For the initial optimisation, the investigated PV capacity range will be 4–10 kWp.

The average costs for the corresponding capacity ranges will be used as initial investment-cost benchmarks.

These values are market reference assumptions and not guaranteed installation quotations.

8.3 Scenario B cost sensitivity

Scenario B will investigate two reductions in PV investment costs relative to Scenario A:

- 10% reduction.
- 20% reduction.

8.4 Source

Verbraucherzentrale NRW (2026). Was kostet eine Photovoltaikanlage?

https://www.verbraucherzentrale.nrw/wissen/energie/erneuerbare-energien/was-kostet-eine-photovoltaikanlage-49155

Publication date: 28 August 2026.

---

9. Battery investment costs – Germany

9.1 Reference data

Battery investment costs are based on the price index published by Verbraucherzentrale, updated on 3 November 2026.

The analysis evaluates 70 real quotations for battery storage systems installed together with residential PV systems. The quotations were collected between January 2025 and August 2026.

The reported average costs are:

Battery capacity| Average installed cost
4–6 kWh| 510 €/kWh
Above 6–8 kWh| 480 €/kWh
Above 8–10 kWh| 410 €/kWh
Above 10–12 kWh| 390 €/kWh
Above 12–16 kWh| 360 €/kWh

The price per kWh decreases with increasing storage capacity because fixed system costs are distributed across a larger number of battery modules.

These values are market reference assumptions rather than guaranteed installation quotations.

9.2 Modelling approach

Battery investment costs will be modelled as a function of installed storage capacity.

For the initial optimisation, the investigated configurations will include:

- No battery storage (reference case).
- Battery capacities between 4 and 12 kWh.

The average price corresponding to each capacity range will be used to estimate total battery investment.

The source concerns batteries installed together with new PV systems. The model will therefore distinguish battery costs from PV-system costs and avoid double-counting shared equipment, inverter and installation costs.

The rated capacity basis must also be checked against the capacity convention used in the technical battery model.

9.3 Scenario B cost sensitivity

Scenario B will investigate two reductions in battery investment costs relative to Scenario A:

- 10% reduction.
- 20% reduction.

9.4 Source

Verbraucherzentrale (2026). Was kostet eine Photovoltaikanlage?

https://www.verbraucherzentrale.de/wissen/energie/erneuerbare-energien/was-kostet-eine-photovoltaikanlage-49155

Last updated: 3 November 2026.

Battery price analysis based on 70 quotations collected between January 2025 and August 2026.

---

9.5 Nominal and usable battery capacity

The technical battery model uses nominal battery capacity.

This is confirmed by the SOC calculation, which divides stored energy by the full battery capacity, and by the minimum SOC constraint, which is applied as a fraction of nominal capacity.

For the reference configuration:

- Nominal battery capacity: 5 kWh.
- Minimum SOC: 20%.
- Maximum SOC: 100%.
- Usable battery capacity: 4 kWh.

The relationship is:

[
E_{\mathrm{usable}} =
E_{\mathrm{nominal}}\times
(SOC_{\max}-SOC_{\min})
]

Market investment costs must be converted according to the capacity convention used by the source:

- Prices expressed in €/kWh nominal capacity are multiplied by nominal capacity.
- Prices expressed in €/kWh usable capacity are multiplied by usable capacity.

The economic model will explicitly distinguish nominal and usable capacity. The existing technical simulation interface will remain unchanged.

---

10. Inverter and replacement costs

10.1 Inverter architecture

The economic model distinguishes between:

- PV inverters, which convert DC electricity from PV modules into AC electricity.
- Battery inverters, which manage electricity conversion between battery storage and the AC electrical system.
- Hybrid inverters, which combine PV and battery inverter functions.

Two configurations are considered: separate PV and battery inverters, and hybrid inverter systems.

The selected architecture must be consistent with the cost assumptions used for each system configuration.

10.2 Initial inverter investment

Initial inverter costs should be included in the installed PV and battery system prices whenever the underlying market-price data already includes these components.

Separate inverter costs must only be added when they represent additional equipment not already included in the installation price.

The cost scope of market quotations must therefore be checked before combining individual component costs.

10.3 PV inverter lifetime and replacement

According to ADAC (2026), residential PV inverters typically have an expected service life of approximately 10–15 years.

The reference replacement cost is:

- €80–150 per kWp of installed PV capacity.

For the initial economic model, inverter replacement will be assumed in year 12.

The replacement year and cost will be examined through sensitivity analysis.

10.4 Battery replacement

The June 2026 PV2027 study commissioned by the Solarenergie-Förderverein Deutschland uses the following battery replacement assumption:

- Replacement after 15 years.
- Replacement expenditure equal to 50% of the initial battery investment.

This will be used as an initial modelling assumption rather than a universal battery replacement rule.

The economic model must avoid counting battery inverter replacement separately if it is already included in the battery replacement cost.

10.5 Operating costs

The PV2027 study assumes annual PV operating costs equal to 1.5% of the initial PV investment.

This will be retained as a reference assumption for sensitivity analysis. We will distinguish recurring operating costs from one-off replacement expenditure.

10.6 Sources

ADAC (2026). Wechselrichter: Funktion, Kosten und Unterschiede.

https://www.adac.de/rund-ums-haus/energie/wechselrichter/

ADAC (2026). Repowering der PV-Anlage: Alte Solaranlage aufrüsten, Leistung steigern.

https://www.adac.de/rund-ums-haus/energie/versorgung/repowering-pv-anlage/

Weniger, J. and Buchholz, K. (2026). PV2027-Studie – Wirtschaftlichkeit von privaten PV-Anlagen unter dem EEG 2027. Study commissioned by Solarenergie-Förderverein Deutschland e.V., June 2026.

https://www.sfv.de/media/7014/download/PV2027-Studie.pdf

---

11. PV and battery degradation

11.1 PV degradation

PV generation is assumed to decrease gradually over the project lifetime due to module ageing.

The initial baseline degradation rate is 0.25% per year, based on the reference assumptions used in the June 2026 PV2027 study commissioned by SFV.

The annual PV generation is calculated as:

[
E_{\mathrm{PV},t} =
E_{\mathrm{PV},1}(1-d_{\mathrm{PV}})^{t-1}
]

Where:

- (E_{\mathrm{PV},t}): PV generation in year (t).
- (E_{\mathrm{PV},1}): PV generation in the first year.
- (d_{\mathrm{PV}}): annual PV degradation rate.

Sensitivity analysis will investigate degradation rates of 0.15%, 0.25% and 0.5% per year.

The 0.15% reference is supported by Fraunhofer ISE measurements of quality-tested German rooftop installations. The 0.5% assumption represents a conservative modelling case.

11.2 Battery capacity degradation

Battery storage capacity decreases over time due to calendar ageing and cycling.

The initial baseline assumption is a 2% annual relative reduction in usable battery capacity, following the reference assumptions in the June 2026 PV2027 study.

The usable battery capacity is calculated as:

[
C_{\mathrm{usable},t} =
C_{\mathrm{usable},1}(1-d_{\mathrm{battery}})^{t-1}
]

Where:

- (C_{\mathrm{usable},t}): usable battery capacity in year (t).
- (C_{\mathrm{usable},1}): initial usable battery capacity.
- (d_{\mathrm{battery}}): annual relative battery capacity degradation rate.

Sensitivity analysis will investigate annual relative degradation rates of 1%, 2% and 3%.

These rates are modelling assumptions. They should not be interpreted as universal degradation guarantees for all battery chemistries or products.

11.3 Battery replacement

The initial economic assumption is battery replacement in year 15.

Replacement expenditure is assumed to equal 50% of the original battery investment cost, following the PV2027 study.

The model will account for the replacement battery's capacity separately from the ageing of the original battery.

The replacement year and replacement expenditure will be examined through sensitivity analysis.

11.4 Technical implementation considerations

The economic model must distinguish between nominal battery capacity and usable battery capacity.

Battery ageing must reduce the effective capacity available to the technical simulation without changing the original nominal capacity convention.

PV degradation will be represented by scaling the annual PV generation profile.

The economic model must also account for battery replacement without double-counting replacement costs.

11.5 Sources

Fraunhofer ISE (2026). Aktuelle Fakten zur Photovoltaik in Deutschland, version 5 May 2026.

https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/studies/aktuelle-fakten-zur-photovoltaik-in-deutschland.pdf

Weniger, J. et al. (2024). Multi-year field measurements of home storage systems and their use in capacity estimation. Nature Energy, 9, 1438–1447.

https://doi.org/10.1038/s41560-024-01620-9

Weniger, J. and Buchholz, K. (2026). PV2027-Studie – Wirtschaftlichkeit von privaten PV-Anlagen unter dem EEG 2027. June 2026.

https://www.sfv.de/media/7014/download/PV2027-Studie.pdf