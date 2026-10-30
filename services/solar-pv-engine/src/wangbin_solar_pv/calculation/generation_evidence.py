"""Bounded, integrity-checked consumption of an existing Phase 3B result.

No irradiance, loss, clipping or degradation model runs here. The caller pins
an upstream result hash; hashes establish integrity, not real-site truth or a
signature. The private source directory must remain ACL-controlled throughout.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
import hashlib
import re
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from ..errors import ContractError
from ..serialization import MAX_JSON_BYTES, loads, dumps, digest
from ..timeseries_bundle import _encode, TimeSeriesBundle
from ..timeseries_private import checked_read, local_target
from .common import integer, nonnegative, number
from .result_contract import validate_result
from .solar_resource import elapsed_hours, month_parts, _stamp


class GenerationEvidence:
    """One forward-only pass, with complete closing checks before publication."""

    def __init__(self, supplied, expected_hash, inputs, meter, bundle=None):
        if not isinstance(expected_hash, str) or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None:
            raise ContractError("GENERATION_RESULT_HASH_REQUIRED")
        self.path = local_target(supplied)
        self.meter, self.inputs = meter, inputs
        self.result_bytes = checked_read(self.path/"result.json", MAX_JSON_BYTES, meter)
        self.receipt_bytes = checked_read(self.path/"receipt.json", MAX_JSON_BYTES, meter)
        self.result = validate_result(loads(self.result_bytes), inputs.catalog)
        self.receipt = loads(self.receipt_bytes)
        if not isinstance(self.receipt,dict):
            raise ContractError("GENERATION_TRACE_MANIFEST")
        if self.result["result_hash"] != expected_hash or self.receipt.get("result_hash") != expected_hash:
            raise ContractError("GENERATION_RESULT_HASH_MISMATCH")
        if (self.result["project_id"] != inputs.validated.project.project_id
                or self.result["pv_type"] != inputs.pv_type):
            raise ContractError("GENERATION_PROJECT_CATEGORY_MISMATCH")
        self.boundary = "GRID_DELIVERABLE" if inputs.pv_type == "utility_scale_ground" else "AVAILABLE_PRE_CONSUMPTION"
        boundary = self.result["boundaries"].get(self.boundary, {})
        if boundary.get("method") != "INTERVAL_DC_AC" or boundary.get("unit") != "kWh":
            raise ContractError("GENERATION_INTERVAL_BOUNDARY_REQUIRED")
        self.repetition = boundary.get("resource_repetition")
        if self.repetition not in {"YEAR_SPECIFIC", "EXPLICIT_REPRESENTATIVE_SCENARIO"}:
            raise ContractError("GENERATION_TIME_SCENARIO")
        self.period = deepcopy(boundary["resource_period"])
        self.zone = ZoneInfo(inputs.value("site.timezone"))
        if self.period.get("timezone") != self.zone.key or self.period.get("coverage") != 1:
            raise ContractError("GENERATION_PERIOD")
        self.start = _stamp(self.period.get("start"), self.zone)
        self.end = _stamp(self.period.get("end"), self.zone)
        minutes = number(self.period.get("interval_minutes"))
        micros = Fraction(minutes)*60000000
        if minutes <= 0 or minutes > 60 or micros.denominator != 1 or self.end <= self.start:
            raise ContractError("GENERATION_INTERVAL")
        self.step = timedelta(microseconds=int(micros))
        self.years = integer(inputs.value("project.evaluation_years"), minimum=1, maximum=100)
        self.first_year = self.start.astimezone(self.zone).year
        self.metrics = {m["metric_id"]: m for m in self.result["results"]["metrics"]}
        self.proof = self.result["evidence"].get("interval-calculations", {})
        if not isinstance(self.proof,dict) or not self.proof.get("canonical_array_hash") or not self.proof.get("physical_chain"):
            raise ContractError("GENERATION_TRACE_IDENTITY_REQUIRED")
        self.chunks = self.receipt.get("chunks")
        if not isinstance(self.chunks, list) or not self.chunks or len(self.chunks) > meter.budget.max_rows:
            raise ContractError("GENERATION_TRACE_MANIFEST")
        for i, chunk in enumerate(self.chunks):
            if (not isinstance(chunk,dict) or set(chunk) != {"file", "bytes", "sha256"} or chunk["file"] != f"interval-{i:05d}.jsonl"
                    or type(chunk["bytes"]) is not int or not 0 < chunk["bytes"] <= 4*1024**2
                    or not isinstance(chunk["sha256"], str)
                    or re.fullmatch(r"[0-9a-f]{64}", chunk["sha256"]) is None):
                raise ContractError("GENERATION_TRACE_MANIFEST")
        self.names = {"result.json", "receipt.json", *(c["file"] for c in self.chunks)}
        self._membership()
        self._compatible_inputs(bundle)
        self.complete = False

    def _membership(self):
        if {p.name for p in self.path.iterdir()} != self.names:
            raise ContractError("GENERATION_TRACE_MEMBERSHIP")

    def _compatible_inputs(self,bundle):
        # A settlement input may add/change commercial facts, never silently
        # substitute physical facts underneath a previously calculated result.
        ignored = {"project.sales_mode", "project.ownership_mode", "grid.metering_boundary"}
        prior = self.result["inputs"]["normalized"]
        records = self.result["source_snapshot"]["phase2"]["records"]
        old = {r["field_id"]: r for r in records if r["field_id"] in prior}
        commercial = {"grid.opinion_status","grid.opinion_valid_until","grid.opinion_attachment_id",
            "grid.transaction_opinion","grid.permit_reference","grid.connection_point"}
        if self.inputs.pv_type == "industrial_rooftop":
            commercial.update(("grid.export_power_limit","grid.available_capacity"))
        for fid in set(self.inputs.values)-set(prior):
            if fid in ignored|commercial or fid == "resource.timeseries":
                continue
            if fid.startswith(("site.","roof.","layout.","system.","resource.","assets.","grid.")):
                raise ContractError("GENERATION_PHYSICAL_INPUT_CHANGED",fid)
        for fid in prior:
            if fid in ignored or fid.startswith(("load.", "tariff.", "revenue.")):
                continue
            if fid not in old or dumps(old[fid]) != dumps(self.inputs.values.get(fid)):
                raise ContractError("GENERATION_PHYSICAL_INPUT_CHANGED", fid)
        old_parameters = self.result["source_snapshot"]["methods"]["parameters"]
        new_parameters = self.inputs.methods.to_dict()["parameters"]
        for pid, parameter in old_parameters.items():
            if pid.startswith(("consumption.", "settlement.", "prices.")):
                continue
            if new_parameters.get(pid) != parameter:
                raise ContractError("GENERATION_PHYSICAL_METHOD_CHANGED")
        for pid in set(new_parameters)-set(old_parameters):
            if pid.startswith(("energy.","thermal.","degradation.","replacement.","constants.")):
                raise ContractError("GENERATION_PHYSICAL_METHOD_CHANGED")
        self._compatible_resource(bundle,old)
        if self.inputs.value("grid.metering_boundary") != self.boundary:
            raise ContractError("CONSUMPTION_METERING_BOUNDARY")

    def _compatible_resource(self,bundle,old):
        fid = "resource.timeseries"
        upstream = self.result["source_snapshot"].get("datasets",{}).get("datasets",{}).get(fid)
        def inline(record):
            rows = record["value"]
            return {"header":{k:v for k,v in record.items() if k not in {"value","original_value"}},
                "row_count":len(rows),"canonical_array_hash":digest(rows)}
        if upstream is None and fid in old:
            upstream = inline(old[fid])
        current = None
        if bundle is not None:
            if not isinstance(bundle,TimeSeriesBundle) or dumps(bundle.base_export) != dumps(self.inputs.validated.export):
                raise ContractError("CALCULATION_DATASET_BASE_MISMATCH")
            if fid in bundle.dataset_ids:
                current = bundle.manifest["datasets"][fid]
        if fid in self.inputs.values:
            if current is not None:
                raise ContractError("GENERATION_RESOURCE_INPUT_CONFLICT")
            current = inline(self.inputs.record(fid))
        # Settlement-only input is valid. If physical resources are supplied,
        # compare per-dataset canonical content AND provenance, never the whole
        # bundle hash (its base export correctly changes with settlement facts).
        if current is not None and (upstream is None or any(current[k] != upstream[k] for k in
                ("header","row_count","canonical_array_hash"))):
            raise ContractError("GENERATION_RESOURCE_INPUT_CONFLICT")

    def _near(self, a, b):
        absolute = self.inputs.methods.require("precision.abs_tolerance")
        relative = self.inputs.methods.require("precision.rel_tolerance")
        return abs(a-b) <= absolute+relative*max(abs(a), abs(b))

    def rows(self):
        cursor = self.start
        count = 0
        canonical = hashlib.sha256(b"[")
        annual = [Decimal(0) for _ in range(self.years)]
        monthly = [[Decimal(0) for _ in range(12)] for _ in range(self.years)]
        hours_by_year = [Decimal(0) for _ in range(self.years)]
        for chunk in self.chunks:
            payload = checked_read(self.path/chunk["file"], 4*1024**2, self.meter)
            if len(payload) != chunk["bytes"] or hashlib.sha256(payload).hexdigest() != chunk["sha256"]:
                raise ContractError("GENERATION_TRACE_FILE_HASH")
            if not payload.endswith(b"\n"):
                raise ContractError("GENERATION_TRACE_ENCODING")
            for line in payload.splitlines():
                self.meter.rows += 1
                self.meter.check()
                if not line or len(line) > 1024**2:
                    raise ContractError("GENERATION_TRACE_ROW_LIMIT")
                row = loads(line)
                if (not isinstance(row,dict) or set(row) != {"resource_row_id","start","end","hours","poa_kw_m2","source_ids","source_instance_ids","calculations"}
                        or not isinstance(row["resource_row_id"],str) or not row["resource_row_id"]):
                    raise ContractError("GENERATION_TRACE_ROW_SCHEMA")
                if _encode(row, 1024**2) != line:
                    raise ContractError("GENERATION_TRACE_NONCANONICAL")
                if count:
                    canonical.update(b",")
                canonical.update(line)
                count += 1
                # Generation traces are UTC instants; _stamp additionally checks
                # the actual local resource axis after converting each instant.
                try:
                    start = datetime.fromisoformat(row["start"])
                    end = datetime.fromisoformat(row["end"])
                    if start.utcoffset() is None or end.utcoffset() is None:
                        raise ValueError
                    start, end = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
                except (KeyError, TypeError, ValueError):
                    raise ContractError("GENERATION_TRACE_TIME") from None
                if start != cursor or end != start+self.step or end > self.end:
                    raise ContractError("GENERATION_TRACE_CONTINUITY")
                hours = elapsed_hours(start, end, digits=self.inputs.methods.require("precision.digits"))
                if number(row.get("hours")) != hours:
                    raise ContractError("GENERATION_TRACE_DURATION")
                expected = (list(range(1, self.years+1)) if self.repetition == "EXPLICIT_REPRESENTATIVE_SCENARIO"
                            else [start.astimezone(self.zone).year-self.first_year+1])
                calculations = row.get("calculations")
                if (not isinstance(calculations, list)
                        or any(not isinstance(c,dict) or set(c) != {"operating_year","state"} or not isinstance(c["state"],dict) for c in calculations)
                        or [c.get("operating_year") for c in calculations] != expected
                        or any(type(c.get("operating_year")) is not int for c in calculations)
                        or any(y < 1 or y > self.years for y in expected)):
                    raise ContractError("GENERATION_TRACE_YEAR_SET")
                parts = list(month_parts(SimpleNamespace(start=start, end=end), self.zone.key))
                for c in calculations:
                    i = c["operating_year"]-1
                    power = nonnegative(c.get("state", {}).get("output_kw"))
                    annual[i] += power*hours
                    hours_by_year[i] += hours
                    for month, duration in parts:
                        monthly[i][int(month[-2:])-1] += power*duration
                cursor = end
                yield row, start, end, hours
        canonical.update(b"]")
        if (cursor != self.end or count != self.proof.get("row_count")
                or count != self.receipt.get("input_rows")
                or canonical.hexdigest() != self.proof["canonical_array_hash"]):
            raise ContractError("GENERATION_TRACE_CONTENT_HASH")
        for i in range(self.years):
            a = self.metrics.get(f"energy.year.{i+1}", {})
            m = self.metrics.get(f"energy.monthly.year.{i+1}", {})
            if (a.get("status") != "CALCULATED" or a.get("boundary_id") != self.boundary
                    or not self._near(annual[i], number(a.get("value")))
                    or a.get("details", {}).get("actual_hours") != hours_by_year[i]
                    or not isinstance(m.get("value"), list) or len(m["value"]) != 12
                    or any(not self._near(x, number(y)) for x,y in zip(monthly[i],m["value"]))):
                raise ContractError("GENERATION_TRACE_AGGREGATION")
        if (not self._near(sum(annual), number(self.metrics.get("energy.lifecycle", {}).get("value")))
                or self.metrics.get("energy.annual_array", {}).get("value") != [self.metrics[f"energy.year.{i+1}"]["value"] for i in range(self.years)]):
            raise ContractError("GENERATION_TRACE_AGGREGATION")
        self._membership()
        if (checked_read(self.path/"result.json", MAX_JSON_BYTES, self.meter, account=False) != self.result_bytes
                or checked_read(self.path/"receipt.json", MAX_JSON_BYTES, self.meter, account=False) != self.receipt_bytes):
            raise ContractError("GENERATION_TRACE_CHANGED")
        self.complete = True
