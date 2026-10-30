"""Independent calendar, provenance, interval and price-basis acceptance."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from consumption_case_support import atom,case,extend,axis,inline_series,load_rows,market_rows,period_row,parameter,BASIS
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.calculation.energy_inputs import EnergyInputs
from wangbin_solar_pv.calculation.tariffs import Tariffs,SettlementSeries,load_energy
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.timeseries_bundle import BundleBudget
from wangbin_solar_pv.timeseries_private import Meter


@pytest.fixture(scope="module")
def catalog():
    return Catalog()


def setup(catalog,*,market=False,ppa=None,zone="Asia/Shanghai",minutes=60):
    s,m = case(catalog,zone=zone)
    s,m = extend(s,m,market=market,ppa=ppa)
    a = axis(zone=zone,minutes=minutes,days=1)
    if market:
        inline_series(s,"tariff.market_series",a,market_rows(catalog,a))
    return s,m,a


def inputs(s,m):
    return EnergyInputs(s.export(),m,s.catalog)


def tariffs(s,m,a):
    return Tariffs(inputs(s,m),a,None,Meter(BundleBudget()))


@pytest.mark.parametrize("minutes,expected",[(60,D(40)),(15,D(10))])
@pytest.mark.parametrize("use_power",[False,True])
def test_same_grid_load_energy_and_power_are_not_mixed_or_multiplied_twice(catalog,minutes,expected,use_power):
    s,m,a = setup(catalog,minutes=minutes)
    rows = list(load_rows(catalog,a,use_power=use_power))
    inline_series(s,"load.series",a,rows)
    i = inputs(s,m);series = SettlementSeries("load.series",i,a,None,Meter(BundleBudget()))
    count = 0
    while count < len(rows):
        start = a.start+timedelta(minutes=count*minutes)
        r = series.take(start,start+timedelta(minutes=minutes))
        assert load_energy(i,r,D(minutes)/60) == expected
        count += 1
    series.finish()
    assert series.count == len(rows)


def test_power_and_energy_conflict_is_not_silently_selected(catalog):
    s,m,a = setup(catalog,minutes=15)
    row = next(load_rows(catalog,a))
    row["fields"]["load.series.power"] = atom(catalog,"load.series.power",D(80),"conflicting-load-power")
    i = inputs(s,m)
    with pytest.raises(ContractError,match="CONSUMPTION_POWER_ENERGY_CONFLICT"):
        load_energy(i,row,D("0.25"))


@pytest.mark.parametrize("change",["timezone","start","end","interval_minutes","coverage"])
def test_series_header_misalignment_or_incomplete_coverage_is_blocked(catalog,change):
    s,m,a = setup(catalog)
    inline_series(s,"load.series",a,load_rows(catalog,a))
    p = s.project.values["load.series"]["measurement_period"]
    changes = {"timezone":"UTC","start":"2025-01-01T01:00:00+08:00","end":"2025-01-01T23:00:00+08:00","interval_minutes":15,"coverage":D("0.9")}
    p[change] = changes[change]
    with pytest.raises(ContractError):
        SettlementSeries("load.series",inputs(s,m),a,None,Meter(BundleBudget()))


@pytest.mark.parametrize("quality",["missing","estimated","outlier"])
def test_unqualified_load_rows_are_not_replaced_with_zero(catalog,quality):
    s,m,a = setup(catalog)
    row = next(load_rows(catalog,a))
    row["fields"]["load.series.quality_flag"] = atom(catalog,"load.series.quality_flag",quality,"invalid-load-quality")
    with pytest.raises(ContractError,match="CONSUMPTION_LOAD_QUALITY"):
        load_energy(inputs(s,m),row,D(1))


def test_empty_or_missing_load_is_not_zero(catalog):
    s,m,a = setup(catalog)
    with pytest.raises(ContractError,match="BLOCKED_MISSING_INPUT"):
        SettlementSeries("load.series",inputs(s,m),a,None,Meter(BundleBudget()))
    with pytest.raises(ContractError,match="BLOCKED_MISSING_INPUT"):
        load_energy(inputs(s,m),{"row_id":"missing","fields":{"load.series.quality_flag":atom(catalog,"load.series.quality_flag","valid","missing-quality")}},D(1))


def test_single_contract_price_and_explicit_fee(catalog):
    s,m,a = setup(catalog)
    t = tariffs(s,m,a);q = t.quote(a.start,a.start+timedelta(hours=1))
    assert (q["avoid"],q["sell"],q["fee"]) == (D("0.8"),D("0.4"),D("0.01"))
    assert q["table"]["policy_id"] == "SYNTHETIC-POLICY-NOT-REAL"


def test_tou_prices_follow_same_local_settlement_interval(catalog):
    s,m,a = setup(catalog)
    rows = [period_row(catalog,"offpeak",start="00:00",end="08:00",price=D("0.2"),avoid=D("0.5")),
            period_row(catalog,"peak",start="08:00",end="24:00",price=D("0.6"),avoid=D("1.2"))]
    s.project.values["tariff.periods"] = atom(catalog,"tariff.periods",rows)
    t = tariffs(s,m,a)
    assert t.quote(a.start+timedelta(hours=7),a.start+timedelta(hours=8))["avoid"] == D("0.5")
    assert t.quote(a.start+timedelta(hours=8),a.start+timedelta(hours=9))["avoid"] == D("1.2")


@pytest.mark.parametrize("kind",["gap","overlap","inside_interval","unknown_calendar"])
def test_price_coverage_is_not_guessed_or_pro_rated(catalog,kind):
    s,m,a = setup(catalog)
    rows = [period_row(catalog,"one",start="00:00",end="12:00")]
    if kind == "overlap":
        rows.append(period_row(catalog,"two",start="11:00",end="24:00"))
    elif kind == "inside_interval":
        rows = [period_row(catalog,"one",start="00:00",end="11:30"),period_row(catalog,"two",start="11:30",end="24:00",price=D("0.6"))]
    elif kind == "unknown_calendar":
        rows = [period_row(catalog,"unknown",weekdays="unclear holiday text")]
    s.project.values["tariff.periods"] = atom(catalog,"tariff.periods",rows)
    with pytest.raises(ContractError):
        t = tariffs(s,m,a)
        hour = 12 if kind == "gap" else 11
        t.quote(a.start+timedelta(hours=hour),a.start+timedelta(hours=hour+1))


def test_explicit_month_and_iso_weekday_rules(catalog):
    s,m,a = setup(catalog)
    s.project.values["tariff.periods"] = atom(catalog,"tariff.periods",[period_row(catalog,"jan-wed",months="MONTHS:1",weekdays="ISO_WEEKDAYS:3")])
    t = tariffs(s,m,a)
    assert t.quote(a.start,a.start+timedelta(hours=1))["sell"] == D("0.4")
    with pytest.raises(ContractError,match="TARIFF_COVERAGE_GAP_OR_OVERLAP"):
        t.quote(a.start+timedelta(days=1),a.start+timedelta(days=1,hours=1))


@pytest.mark.parametrize("ppa,expected",[("PPA_FIXED",D("0.5")),("PPA_DISCOUNT",D("0.6"))])
def test_ppa_fixed_and_explicit_discount_are_distinct_from_host_avoided_cost(catalog,ppa,expected):
    s,m,a = setup(catalog,ppa=ppa)
    q = tariffs(s,m,a).quote(a.start,a.start+timedelta(hours=1))
    assert q["ppa"] == expected
    assert q["ppa"] != D("0.8")


def test_ppa_discount_cannot_silently_override_an_explicit_fixed_contract_price(catalog):
    s,m,a = setup(catalog,ppa="PPA_DISCOUNT")
    s.project.values["tariff.ppa_price"] = atom(catalog,"tariff.ppa_price",D("0.55"))
    with pytest.raises(ContractError,match="PPA_FIXED_DISCOUNT_PRICE_CONFLICT"):
        tariffs(s,m,a)


def test_market_signed_price_and_fee_are_time_matched(catalog):
    s,m,a = setup(catalog,market=True)
    t = tariffs(s,m,a)
    for hour in range(24):
        q = t.quote(a.start+timedelta(hours=hour),a.start+timedelta(hours=hour+1))
        assert q["sell"] == (D("-0.1") if 12 <= hour < 14 else D("0.4"))
        assert q["fee"] == D("0.01")
    t.finish()


@pytest.mark.parametrize("basis_key,value",[("currency","USD"),("price_year",2024),("tax_basis","exclusive"),("price_basis","real")])
def test_mixed_economic_bases_are_blocked_without_implicit_tax_or_fx_conversion(catalog,basis_key,value):
    s,m,a = setup(catalog)
    basis = {**BASIS,basis_key:value}
    s.project.values["tariff.periods"] = atom(catalog,"tariff.periods",[period_row(catalog,"mixed",basis=basis)])
    expected_code = "INPUT_VALIDATION_FAILED" if basis_key == "currency" else "SETTLEMENT_ECONOMIC_BASIS_MISMATCH"
    with pytest.raises(ContractError,match=expected_code) as caught:
        tariffs(s,m,a)
    if basis_key == "currency":
        assert any(issue["code"] == "CURRENCY_CONTEXT_MISMATCH" for issue in caught.value.issues)


def test_explicit_tax_exclusive_inputs_remain_exclusive(catalog):
    s,m = case(catalog)
    basis = {**BASIS,"tax_basis":"exclusive"}
    s,m = extend(s,m,basis=basis)
    s.project.values["tariff.transaction_fee"] = atom(catalog,"tariff.transaction_fee",D("0.01"),economic_basis=basis)
    s.project.values["tariff.periods"] = atom(catalog,"tariff.periods",[period_row(catalog,"exclusive",price=D("0.4"),basis=basis)])
    a = axis(days=1);t = tariffs(s,m,a)
    assert t.basis["tax_basis"] == "exclusive"
    assert t.quote(a.start,a.start+timedelta(hours=1))["sell"] == D("0.4")


@pytest.mark.parametrize("field",["tariff.transaction_fee","tariff.contract_id"])
def test_missing_settlement_conditions_are_not_defaulted(catalog,field):
    s,m,a = setup(catalog)
    del s.project.values[field]
    with pytest.raises(ContractError,match="BLOCKED_MISSING_INPUT"):
        tariffs(s,m,a)


def test_expired_or_conflicting_price_sources_are_blocked(catalog):
    s,m,a = setup(catalog)
    rec = s.project.values["tariff.transaction_fee"]
    rec["effective_to"] = "2026-10-28"
    with pytest.raises(ContractError,match="ENERGY_SOURCE_EXPIRED"):
        tariffs(s,m,a)
    rec["effective_to"] = None;rec["status"] = "CONFLICT"
    with pytest.raises(ContractError):
        tariffs(s,m,a)


def test_autumn_repeated_wall_hour_is_two_real_price_intervals(catalog):
    s,m,a = setup(catalog,zone="America/New_York")
    t = tariffs(s,m,a)
    first = datetime(2025,11,2,5,tzinfo=timezone.utc)
    second = first+timedelta(hours=1)
    assert t.quote(first,second)["sell"] == D("0.4")
    assert t.quote(second,second+timedelta(hours=1))["sell"] == D("0.4")


def test_spring_price_gap_transition_inside_45_minute_interval_is_not_missed(catalog):
    s,m,a = setup(catalog,zone="America/New_York",minutes=45)
    s.project.values["tariff.periods"] = atom(catalog,"tariff.periods",[
        period_row(catalog,"pre-gap",start="00:00",end="02:00",price=D("0.2")),
        period_row(catalog,"post-gap",start="02:00",end="24:00",price=D("0.6"))])
    t = tariffs(s,m,a)
    start = datetime(2026,3,8,6,30,tzinfo=timezone.utc)
    with pytest.raises(ContractError,match="TARIFF_INTERVAL_CROSSES_PRICE_CHANGE"):
        t.quote(start,start+timedelta(minutes=45))


def test_original_watts_are_normalized_once_before_quarter_hour_energy(catalog):
    s,m,a = setup(catalog,minutes=15)
    row = next(load_rows(catalog,a,use_power=True))
    row["fields"]["load.series.power"] = atom(catalog,"load.series.power",40000,"watts-input",original_unit="W")
    assert row["fields"]["load.series.power"]["value"] == D(40)
    assert load_energy(inputs(s,m),row,D("0.25")) == D(10)
