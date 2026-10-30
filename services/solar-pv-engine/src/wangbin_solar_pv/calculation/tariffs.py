"""Explicit same-grid load/market adapters and bounded settlement price matching.

Calendar tokens describe supplied assumptions, not a holiday/policy database.
Unknown free text and price changes inside an unsplit metering interval fail
closed. No default prices, tax conversion, resampling, subsidy or fixed-charge
avoidance is introduced.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction

from ..errors import ContractError
from ..serialization import dumps
from ..timeseries_bundle import TimeSeriesBundle
from .common import nonnegative, number
from .solar_resource import _stamp


def lineage(inputs, row):
    records = [inputs.record(fid, row=row) for fid in sorted(row["fields"])
               if row["fields"][fid].get("value") is not None
               and row["fields"][fid].get("status") not in {"UNKNOWN","CONFLICT"}]
    return {"row_id": row["row_id"], "source_instance_ids": [r["field_instance_id"] for r in records],
            "source_ids": sorted({r["source_id"] for r in records})}


class SettlementSeries:
    """A checked single forward stream; exact physical intervals, never padding."""

    def __init__(self, field_id, inputs, generation, bundle, meter):
        self.fid, self.inputs, self.meter = field_id, inputs, meter
        if bundle is not None and field_id in bundle.dataset_ids:
            if not isinstance(bundle, TimeSeriesBundle) or dumps(bundle.base_export) != dumps(inputs.validated.export):
                raise ContractError("CALCULATION_DATASET_BASE_MISMATCH")
            header = bundle.manifest["datasets"][field_id]["header"]
            if header.get("license_status") in {"UNKNOWN", "DENIED"}:
                raise ContractError("ENERGY_SOURCE_NOT_AUTHORIZED", field_id)
            evaluation = inputs.evaluation_date.isoformat()
            if ((header.get("effective_from") and header["effective_from"] > evaluation)
                    or (header.get("effective_to") and header["effective_to"] < evaluation)):
                raise ContractError("ENERGY_SOURCE_EXPIRED_OR_NOT_EFFECTIVE", field_id)
            self.rows = iter(bundle.rows(field_id))
            inputs.used[field_id] = {"field_id":field_id,"field_instance_id":header["field_instance_id"],
                "source_id":header["source_id"],"unit":header["unit"],"status":header["status"],
                "transformation_rule_ids":header["transformation_rule_ids"],"reference_kind":"D3_HEADER_NOT_EMPTY_ARRAY"}
        else:
            header = inputs.record(field_id)
            self.rows = iter(inputs.rows(field_id))
        p = header.get("measurement_period")
        if (not isinstance(p, dict) or p.get("coverage") != 1
                or p.get("timezone") != generation.zone.key):
            raise ContractError("CONSUMPTION_SERIES_PERIOD", field_id)
        if (_stamp(p.get("start"), generation.zone) != generation.start
                or _stamp(p.get("end"), generation.zone) != generation.end
                or number(p.get("interval_minutes")) != generation.period["interval_minutes"]):
            raise ContractError("CONSUMPTION_SERIES_ALIGNMENT", field_id)
        self.zone = generation.zone
        self.minutes = number(p["interval_minutes"])
        self.count = 0

    def take(self, start, end):
        row = next(self.rows, None)
        if row is None:
            raise ContractError("CONSUMPTION_SERIES_INCOMPLETE", self.fid)
        self.count += 1
        self.meter.rows += 1
        self.meter.atoms += len(row["fields"])
        self.meter.check()
        stamp = _stamp(self.inputs.value(self.fid+".timestamp", row=row), self.zone)
        minutes = number(self.inputs.value(self.fid+".interval_minutes", row=row))
        micros = Fraction(minutes)*60000000
        if (minutes != self.minutes or micros.denominator != 1
                or stamp != start or stamp+timedelta(microseconds=int(micros)) != end):
            raise ContractError("CONSUMPTION_SERIES_ALIGNMENT", self.fid)
        return row

    def finish(self):
        # Exhaustion runs the D3 reader's closing canonical/content checks.
        if next(self.rows, None) is not None:
            raise ContractError("CONSUMPTION_SERIES_EXTRA_INTERVALS", self.fid)


def load_energy(inputs, row, hours):
    fid = "load.series"
    if inputs.value(fid+".quality_flag", row=row) != "valid":
        raise ContractError("CONSUMPTION_LOAD_QUALITY", fid)
    present = [name for name in ("energy", "power") if fid+"."+name in row["fields"]
               and row["fields"][fid+"."+name].get("value") is not None]
    if not present:
        raise ContractError("BLOCKED_MISSING_INPUT", fid+".energy")
    energy = nonnegative(inputs.numeric(fid+".energy", row=row)) if "energy" in present else None
    from_power = nonnegative(inputs.numeric(fid+".power", row=row))*hours if "power" in present else None
    if energy is not None and from_power is not None:
        tolerance = inputs.methods.require("precision.abs_tolerance")
        relative = inputs.methods.require("precision.rel_tolerance")
        if abs(energy-from_power) > tolerance+relative*max(abs(energy),abs(from_power)):
            raise ContractError("CONSUMPTION_POWER_ENERGY_CONFLICT")
    return energy if energy is not None else from_power


def _calendar_set(text, prefix, upper):
    if text == "ALL":
        return frozenset(range(1, upper+1))
    if not isinstance(text, str) or not text.startswith(prefix):
        raise ContractError("TARIFF_CALENDAR_RULE_REQUIRES_EXPLICIT_MAPPING")
    tokens = text[len(prefix):].split(",")
    if (not tokens or any(not t.isascii() or not t.isdigit() or str(int(t)) != t for t in tokens)
            or len(set(tokens)) != len(tokens)):
        raise ContractError("TARIFF_CALENDAR_RULE_REQUIRES_EXPLICIT_MAPPING")
    values = frozenset(map(int, tokens))
    if not values or min(values) < 1 or max(values) > upper:
        raise ContractError("TARIFF_CALENDAR_RULE_REQUIRES_EXPLICIT_MAPPING")
    return values


def _minute(text):
    h, m = text.split(":")
    return int(h)*60+int(m)


class Tariffs:
    def __init__(self, inputs, generation, bundle, meter):
        self.inputs, self.generation = inputs, generation
        methods = inputs.methods
        self.source = methods.require("settlement.price_source")
        self.revenue_method = methods.require("settlement.revenue_method")
        self.basis = {key:methods.require("settlement."+key) for key in ("currency","price_year","tax_basis","price_basis")}
        if self.basis["currency"] != inputs.value("project.currency"):
            raise ContractError("SETTLEMENT_ECONOMIC_BASIS_MISMATCH")
        self.escalation = methods.require("prices.escalation_fraction")
        self.fee_treatment = methods.require("settlement.fee_treatment")
        methods.require("settlement.negative_price_treatment")
        inputs.value("tariff.contract_id")
        inputs.value("tariff.settlement_mode")
        self.needs_avoid = self.revenue_method in {"OWNER_AVOIDED_COST", "PPA_DISCOUNT"}
        if self.needs_avoid:
            inputs.value("tariff.non_avoidable_charges")
        self.ppa = self.money("tariff.ppa_price") if self.revenue_method == "PPA_FIXED" else None
        self.discount = methods.require("settlement.ppa_discount_factor") if self.revenue_method == "PPA_DISCOUNT" else None
        if self.revenue_method == "PPA_DISCOUNT" and "tariff.ppa_price" in inputs.values:
            raise ContractError("PPA_FIXED_DISCOUNT_PRICE_CONFLICT")
        self.market = SettlementSeries("tariff.market_series", inputs, generation, bundle, meter) if self.source == "MARKET_SERIES" else None
        self.fee = self.money("tariff.transaction_fee") if self.source == "PERIOD_TABLE" else None
        self.table = []
        if self.source == "PERIOD_TABLE" or self.needs_avoid:
            for row in inputs.rows("tariff.periods"):
                meter.check()
                get = lambda key: inputs.value("tariff.periods."+key, row=row)
                first, last = date.fromisoformat(get("effective_from")), date.fromisoformat(get("effective_to"))
                begin, end = _minute(get("start_time")), _minute(get("end_time"))
                if last < first or not 0 <= begin < end <= 1440:
                    raise ContractError("TARIFF_PERIOD_DOMAIN")
                tax_included = get("tax_included")
                if tax_included != (self.basis["tax_basis"] == "inclusive"):
                    raise ContractError("SETTLEMENT_ECONOMIC_BASIS_MISMATCH")
                vat = inputs.numeric("tariff.periods.vat_rate", row=row)
                item = {"first": first, "last": last,
                    "months": _calendar_set(get("season"), "MONTHS:", 12),
                    "weekdays": _calendar_set(get("weekday_rule"), "ISO_WEEKDAYS:", 7),
                    "begin": begin, "end": end, "tax_included": tax_included, "vat_rate": vat,
                    "policy_id": get("policy_id"), "label": get("period_label"), "lineage": lineage(inputs,row)}
                item["avoid"] = self.money("tariff.periods.avoidable_price", row=row) if self.needs_avoid else None
                item["sell"] = self.money("tariff.periods.sale_price", row=row) if self.source == "PERIOD_TABLE" else None
                self.table.append(item)
        self._cached_date = None
        self._cuts = ()

    def money(self, fid, *, row=None):
        record = self.inputs.record(fid, row=row)
        if record.get("economic_basis") != self.basis:
            raise ContractError("SETTLEMENT_ECONOMIC_BASIS_MISMATCH", fid)
        value = number(record["value"], fid)
        if value < 0 and fid.startswith("tariff."):
            self.inputs.value("tariff.negative_price_rule")
        return value

    def _matches(self, point):
        local = point.astimezone(self.generation.zone)
        minute = local.hour*60+local.minute+Decimal(local.second)/60+Decimal(local.microsecond)/60000000
        return [p for p in self.table if p["first"] <= local.date() <= p["last"]
                and local.month in p["months"] and local.isoweekday() in p["weekdays"]
                and p["begin"] <= minute < p["end"]]

    def _cut_points(self, start):
        zone = self.generation.zone
        local_date = start.astimezone(zone).date()
        if self._cached_date != local_date:
            minutes = {0,1440}
            for p in self.table:
                minutes.update((p["begin"], p["end"]))
            cuts = set()
            # Intervals are <= one physical hour. Nearby local days also cover
            # a permanent date-line/offset change; never assume 24 elapsed hours.
            for offset in range(-1,4):
                day = local_date+timedelta(days=offset)
                for minute in minutes:
                    wall = datetime.combine(day,time())+timedelta(minutes=minute)
                    for fold in (0,1):
                        local = wall.replace(tzinfo=zone,fold=fold)
                        instant = local.astimezone(timezone.utc)
                        if instant.astimezone(zone).replace(tzinfo=None) == wall:
                            cuts.add(instant)
            self._cached_date, self._cuts = local_date, tuple(sorted(cuts))
        return self._cuts

    def quote(self, start, end):
        if start.utcoffset() is None or end.utcoffset() is None or not start < end <= start+timedelta(hours=1):
            raise ContractError("TARIFF_INTERVAL_DOMAIN")
        table_item = None
        if self.table:
            last = end-timedelta(microseconds=1)
            points = {start,last,*(p for p in self._cut_points(start) if start < p < end)}
            # A nonexistent wall-clock tariff edge can be jumped over entirely.
            # Inspect the actual offset transition as well as real wall edges;
            # never allocate uniform subinterval energy to repair missing data.
            zone = self.generation.zone
            ordered = sorted(points)
            for left,right in zip(ordered,ordered[1:]):
                offset = left.astimezone(zone).utcoffset()
                if offset != right.astimezone(zone).utcoffset():
                    lo,hi = left,right
                    while hi-lo > timedelta(microseconds=1):
                        middle = lo+(hi-lo)//2
                        if middle.astimezone(zone).utcoffset() == offset:
                            lo = middle
                        else:
                            hi = middle
                    points.add(hi)
            points = sorted(points)
            for point in points:
                matches = self._matches(point)
                if len(matches) != 1:
                    raise ContractError("TARIFF_COVERAGE_GAP_OR_OVERLAP")
                if table_item is not None and table_item is not matches[0]:
                    raise ContractError("TARIFF_INTERVAL_CROSSES_PRICE_CHANGE")
                table_item = matches[0]
        if self.market:
            row = self.market.take(start,end)
            sell = self.money("tariff.market_series.sale_price",row=row)
            fee = self.money("tariff.market_series.transaction_fee",row=row)
            source = lineage(self.inputs,row)
        else:
            sell, fee = table_item["sell"], self.fee
            source = table_item["lineage"]
        if fee < 0:
            raise ContractError("NEGATIVE_TRANSACTION_FEE")
        avoid = table_item["avoid"] if table_item is not None else None
        ppa = self.ppa if self.revenue_method == "PPA_FIXED" else (avoid*self.discount if self.discount is not None else None)
        return {"sell":sell,"avoid":avoid,"ppa":ppa,"fee":fee,"source":source,
                "table":None if table_item is None else {k:table_item[k] for k in ("policy_id","label","tax_included","vat_rate","lineage")}}

    def finish(self):
        if self.market:
            self.market.finish()
