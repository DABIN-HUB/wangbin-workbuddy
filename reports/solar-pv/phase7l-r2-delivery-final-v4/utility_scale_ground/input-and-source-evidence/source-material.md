# SYNTHETIC Phase 7L 25-year model source v2.0.0

§ model assumptions

Authored 2026-11-06 for offline calculation testing only.
This is not an approval, engineering signoff, real quotation, legal opinion, signed contract,
measured weather record, metered load, actual payment, or tax advice.
Case identity: SYNTHETIC-PHASE7L-R2-GROUND-25Y-330KWP (utility_scale_ground).

## site_model
Fictional 10000 m2 ground parcel with 1000 m2 roads and drainage exclusion, 9000 m2 usable and modeled rights through 2052. No surveyed boundary, geotechnical study, flood study or verified land title.

## engineering_model
600 x 550 Wp modules, 3 x 100 kWac inverters; 30 strings of 20; modeled 25-year horizon. Inverter renewal at year 13 with linked cash CAPEX and one-year downtime scenario.

## commercial_model
Full export at a modeled 2025 hourly market price including signed negative midday price; synthetic resource is an explicit representative year, not 25 observed meteorological years. No executed grid connection or trading agreement.

## capital_model
Initial modules 600 x 700 CNY, inverters 3 x 45000 CNY, mounting 220000 CNY, construction 175000 CNY; year-13 replacement inverters 3 x 45000 CNY. All declared paid in scenario, not historical cash proof.

## operating_model
Maintenance 15000 CNY and insurance 9500 CNY per first year, 2% annual escalation through year 25. Unlevered financing, CNY nominal post-tax end-year discount 7.5%; forecast collections and OPEX payments 100% each period.

## constraints
No real land right, construction approval, geotechnical or flood report, grid permission, market trading contract, supplier quote, tax opinion, or legal certification. All documentary references are authored synthetic modeling notes only.

## Phase 2 task schedule — SYNTHETIC planning assumption
All task dates, predecessors, and owners below are fictional model inputs;
review gates record planned work, NOT completed reviews or legal approvals.
Inclusive calendar-day durations are derived from start_date and finish_date.
Construction is conditional on obtaining real title, design reviews and permits.

- ground-design: SYNTHETIC site/drainage/connection concept planning; 2026-11-06 through 2026-11-20; duration=15 inclusive calendar day(s); predecessors=NONE_PLANNED; owner=Fictional model engineering team; critical_path=True.
- ground-readiness: SYNTHETIC title/geotechnical/grid review gate planning; approvals remain pending; 2026-11-21 through 2026-11-30; duration=10 inclusive calendar day(s); predecessors=ground-design; owner=Fictional model sponsor; critical_path=True.
- ground-build: SYNTHETIC ground civil and array works, conditional on real clearances; 2026-12-01 through 2026-12-20; duration=20 inclusive calendar day(s); predecessors=ground-readiness; owner=Fictional model construction team; critical_path=True.
- ground-test: SYNTHETIC grid interface testing plan, not grid consent; 2026-12-21 through 2026-12-31; duration=11 inclusive calendar day(s); predecessors=ground-build; owner=Fictional model operations team; critical_path=True.
- ground-milestone: SYNTHETIC commissioning milestone assumption, not permission to operate; 2027-01-01 through 2027-01-01; duration=1 inclusive calendar day(s); predecessors=ground-test; owner=Fictional model sponsor; critical_path=True.

Commissioning milestone is 2027-01-01 (one modeled day),
not an actual commissioning certificate or permission to energize.

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
