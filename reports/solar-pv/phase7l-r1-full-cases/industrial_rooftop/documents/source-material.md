# SYNTHETIC Phase 7L 25-year model source v1.0.0

§ model assumptions

Authored 2026-11-06 for offline calculation testing only.
This is not an approval, engineering signoff, real quotation, legal opinion, signed contract,
measured weather record, metered load, actual payment, or tax advice.
Case identity: SYNTHETIC-PHASE7L-ROOF-25Y-165KWP (industrial_rooftop).

## site_model
Fictional factory roof: 3500 m2 gross, 500 m2 setbacks, 3000 m2 usable; 30-year modeled remaining roof service life. No structural load verification or landlord consent.

## engineering_model
300 x 550 Wp modules, 3 x 50 kWac inverters; 20 strings of 15; modeled 25-year horizon. Inverter renewal at year 13 with linked cash CAPEX and one-year downtime scenario.

## commercial_model
Owner self-use plus surplus export. Synthetic representative 2025 hourly resource and factory-load profile; 0.76 CNY/kWh modeled avoidable daytime energy charge and 0.42 CNY/kWh export, no demand-charge savings. Not an executed tariff.

## capital_model
Initial modules 300 x 700 CNY, inverters 3 x 24000 CNY, mounting 90000 CNY, construction 95000 CNY; year-13 replacement inverters 3 x 24000 CNY. All declared paid in scenario, not historical cash proof.

## operating_model
Maintenance 7200 CNY and insurance 3800 CNY per first year, 2% annual escalation through year 25. Unlevered financing, CNY nominal post-tax end-year discount 7.5%; forecast collections and OPEX payments 100% each period.

## constraints
No real roof engineering signoff, fire approval, grid permission, metered load, supplier quote, tax opinion, or legally enforceable land/roof title. All documentary references are authored synthetic modeling notes only.

## Forecast boundary
PROJECT_POST_TAX_NOMINAL_CNY_YEAR_END is the explicitly authored discounted project-cash boundary.
25 operating years begin 2027-01-01, finish 2051-12-31; 2025 8760-hour weather is a
fictional representative resource year; each operating year is recomputed under the declared
annual 0.8% module degradation and explicit year-13 inverter replacement/downtime method.
All forward collections and expenses are planning assumptions, not bank transactions.
Year-25 no-disposition is explicit: no terminal sale proceeds or disposal taxes;
working capital recovery is already in the 3D ledger, not counted twice.

## Professional evidence limitations
Rights, roof structural capacity, fire setback, grid consent, metering, market trading,
geotechnical and flood design remain pending real project verification. Synthetic authored
documents are explicitly classified ASSUMED and cannot pass real-project maturity.
