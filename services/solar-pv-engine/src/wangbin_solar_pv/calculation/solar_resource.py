"""Explicit POA paths and a bounded, timezone-correct physical time axis.

GHI/DNI/DHI remain in the original evidence. No transposition model is invented;
only declared array-plane interval means or supplied monthly cumulative POA
enter these paths. UTC elapsed time and local calendar aggregation are distinct.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..errors import ContractError
from ..serialization import dumps
from ..timeseries_bundle import TimeSeriesBundle
from .common import nonnegative, number, precision_context
from .energy_inputs import EnergyInputs


@dataclass(frozen=True, slots=True)
class ResourceInterval:
    row_id: str
    start: datetime
    end: datetime
    hours: Decimal
    poa_kw_m2: Decimal
    ambient_c: Decimal
    wind_m_s: Decimal
    source_instance_ids: tuple[str, ...]
    source_ids: tuple[str, ...]


def elapsed_hours(start, end, *, digits=80):
    delta = end.astimezone(timezone.utc) - start.astimezone(timezone.utc)
    micros = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
    with precision_context(digits):
        return Decimal(micros) / Decimal(3600000000)


def _zone(inputs):
    value = inputs.value("site.timezone")
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, TypeError, ValueError):
        raise ContractError("ENERGY_RESOURCE_TIMEZONE", "site.timezone") from None


def _stamp(value, zone):
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.utcoffset() is None:
            raise ValueError
        local = stamp.astimezone(zone)
        if local.replace(tzinfo=None) != stamp.replace(tzinfo=None) or local.utcoffset() != stamp.utcoffset():
            raise ValueError
        return stamp.astimezone(timezone.utc)
    except (ValueError, AttributeError, OverflowError):
        raise ContractError("ENERGY_RESOURCE_TIMEZONE") from None


def intervals(inputs: EnergyInputs, *, bundle=None):
    """Consume to exhaustion before publishing a result: the final gap matters."""
    if not isinstance(inputs, EnergyInputs):
        raise ContractError("CALCULATION_INPUT_NOT_VALIDATED")
    if inputs.value("resource.poa_boundary") != "ARRAY_PLANE_INTERVAL_MEAN":
        raise ContractError("BLOCKED_METHOD_REVIEW", "resource.poa_boundary")
    zone = _zone(inputs)
    fid = "resource.timeseries"
    if bundle is not None:
        if not isinstance(bundle, TimeSeriesBundle):
            raise ContractError("CALCULATION_DATASET_NOT_VALIDATED")
        if dumps(bundle.base_export) != dumps(inputs.validated.export):
            raise ContractError("CALCULATION_DATASET_BASE_MISMATCH")
        if fid not in bundle.dataset_ids:
            raise ContractError("BLOCKED_MISSING_INPUT", fid)
        descriptor = bundle.manifest["datasets"][fid]
        period = descriptor["header"].get("measurement_period")
        records = bundle.rows(fid)
    else:
        header = inputs.record(fid)
        period = header.get("measurement_period")
        records = iter(inputs.rows(fid))
    if not isinstance(period, dict) or period.get("timezone") != zone.key or period.get("coverage") != 1:
        raise ContractError("ENERGY_RESOURCE_PERIOD")
    start, end = _stamp(period.get("start"), zone), _stamp(period.get("end"), zone)
    minutes = number(period.get("interval_minutes"), fid)
    micros = Fraction(minutes) * 60000000
    if minutes <= 0 or micros.denominator != 1 or end <= start:
        raise ContractError("ENERGY_RESOURCE_INTERVAL")
    try:
        step = timedelta(microseconds=int(micros))
    except OverflowError:
        raise ContractError("ENERGY_RESOURCE_INTERVAL") from None
    cursor = start
    digits = inputs.methods.require("precision.digits")
    for row in records:
        with precision_context(digits):
            point = _stamp(inputs.value(fid + ".timestamp", row=row), zone)
            duration = inputs.numeric(fid + ".interval_minutes", row=row)
            if duration != minutes:
                raise ContractError("ENERGY_RESOURCE_INTERVAL")
            if point != cursor or point + step > end:
                raise ContractError("ENERGY_RESOURCE_CONTINUITY")
            if inputs.value(fid + ".quality_flag", row=row) != "valid":
                raise ContractError("ENERGY_RESOURCE_QUALITY")
            if fid + ".poa" not in row["fields"]:
                raise ContractError("BLOCKED_METHOD_REVIEW", fid + ".poa")
            poa = nonnegative(inputs.numeric(fid + ".poa", row=row), fid + ".poa") / 1000
            ambient = inputs.numeric(fid + ".ambient_temperature", row=row)
            wind = nonnegative(inputs.numeric(fid + ".wind_speed", row=row), fid + ".wind_speed")
            used = [inputs.record(fid + "." + key, row=row) for key in
                    ("timestamp", "interval_minutes", "poa", "ambient_temperature", "wind_speed", "quality_flag", "row_id")]
            item = ResourceInterval(row["row_id"], point, point + step,
                elapsed_hours(point, point + step, digits=digits), poa, ambient, wind,
                tuple(r["field_instance_id"] for r in used), tuple(sorted({r["source_id"] for r in used})))
            cursor += step
        yield item
    if cursor != end:
        raise ContractError("ENERGY_RESOURCE_CONTINUITY")


def month_parts(interval, timezone_name):
    """Split one constant-mean power interval at true local month boundaries."""
    zone = ZoneInfo(timezone_name)
    point = interval.start
    while point < interval.end:
        local = point.astimezone(zone)
        y, m = (local.year + 1, 1) if local.month == 12 else (local.year, local.month + 1)
        edge = datetime(y, m, 1, tzinfo=zone).astimezone(timezone.utc)
        finish = min(edge, interval.end)
        yield f"{local.year:04d}-{local.month:02d}", elapsed_hours(point, finish)
        point = finish


def monthly_poa(inputs: EnergyInputs):
    """Full supplied calendar year, not integration or a manufactured hourly year."""
    if inputs.value("resource.poa_boundary") != "ARRAY_PLANE_MONTHLY_CUMULATIVE":
        raise ContractError("BLOCKED_METHOD_REVIEW", "resource.poa_boundary")
    _zone(inputs)
    start = date.fromisoformat(inputs.value("resource.period_start"))
    end = date.fromisoformat(inputs.value("resource.period_end"))
    if start != date(start.year, 1, 1) or end != date(start.year, 12, 31):
        raise ContractError("ENERGY_MONTHLY_CALENDAR_YEAR")
    records = inputs.rows("resource.monthly")
    seen = set()
    result = []
    for row in records:
        month = inputs.value("resource.monthly.month", row=row)
        if type(month) is not int or month not in range(1, 13) or month in seen:
            raise ContractError("ENERGY_MONTHLY_INDEX")
        seen.add(month)
        if inputs.value("resource.monthly.days", row=row) != calendar.monthrange(start.year, month)[1]:
            raise ContractError("ENERGY_MONTHLY_DAYS")
        if inputs.numeric("resource.monthly.coverage", row=row) != 1:
            raise ContractError("ENERGY_MONTHLY_COVERAGE")
        if "resource.monthly.poa" not in row["fields"]:
            raise ContractError("BLOCKED_METHOD_REVIEW", "resource.monthly.poa")
        poa = nonnegative(inputs.numeric("resource.monthly.poa", row=row), "resource.monthly.poa")
        record = inputs.record("resource.monthly.poa", row=row)
        result.append({"month": month, "period": f"{start.year}-{month:02d}", "poa_kwh_m2": poa,
                       "field_instance_id": record["field_instance_id"], "source_id": record["source_id"]})
    if seen != set(range(1, 13)):
        raise ContractError("ENERGY_MONTHLY_COVERAGE")
    return sorted(result, key=lambda item: item["month"])
