"""Performance schedules, distinct from already-clipped annual energy totals."""
from __future__ import annotations

from decimal import Decimal

from ..errors import ContractError
from .common import precision_context, ratio, integer


def performance_schedule(inputs, year_days):
    """Return one bounded record per operating year, never final-energy scaling.

    Replacement fractions apply uniformly to every identical inverter group.
    Missing exact dates use ONLY the declared year-start/equivalent scenario.
    No rule is inferred from arbitrary performance_reset prose or a ceiling.
    """
    years = integer(inputs.value("project.evaluation_years"), minimum=1, maximum=100)
    if len(year_days) != years:
        raise ContractError("ENERGY_YEAR_COUNT")
    method = inputs.methods.require("degradation.method")
    initial = ratio(inputs.numeric("system.first_year_degradation"))
    included = inputs.methods.require("energy.pr_includes_initial_degradation")
    if included and inputs.methods.require("energy.method") != "POA_PR":
        raise ContractError("ENERGY_INITIAL_DEGRADATION_DUPLICATED")
    if method == "ANNUAL":
        annual = ratio(inputs.numeric("system.annual_degradation"), include_one=False)
        rates = [annual] * years
    else:
        rates = [None] * years
        for row in inputs.rows("system.degradation_segments"):
            start = inputs.value("system.degradation_segments.from_year", row=row)
            end = inputs.value("system.degradation_segments.to_year", row=row)
            rate = ratio(inputs.numeric("system.degradation_segments.rate", row=row))
            if start > end or end > years:
                raise ContractError("ENERGY_DEGRADATION_SEGMENT")
            if inputs.value("system.degradation_segments.reset_on_replacement", row=row) != "EXPLICIT_METHOD_RULE":
                raise ContractError("BLOCKED_METHOD_REVIEW", "system.degradation_segments.reset_on_replacement")
            for y in range(start-1, end):
                if rates[y] is not None:
                    raise ContractError("ENERGY_DEGRADATION_OVERLAP")
                rates[y] = rate
        if any(rate is None for rate in rates):
            raise ContractError("ENERGY_DEGRADATION_GAP")
    event_method = inputs.methods.require("replacement.method")
    # Even an explicit no-event scenario must not silently suppress raw events.
    rows = inputs.value("assets.replacements")
    if event_method == "NONE_DECLARED" and rows:
        raise ContractError("ENERGY_REPLACEMENT_CONFLICT")
    events = {}
    if event_method == "EXPLICIT_ASSET_EVENTS":
        rules = inputs.methods.require("replacement.rules")
        mapping = {r["event_id"]: r for r in rules}
        if len(mapping) != len(rules) or set(mapping) != {r["row_id"] for r in rows}:
            raise ContractError("ENERGY_REPLACEMENT_RULES")
        ceiling = inputs.methods.require("degradation.performance_ceiling")
        for row in rows:
            year = inputs.value("assets.replacements.year", row=row)
            if year > years or year in events:
                # Multiple simultaneous affected cohorts need an explicit
                # non-overlap model, not an assumed sum of fractions.
                raise ContractError("ENERGY_REPLACEMENT_AMBIGUOUS")
            rule = mapping[row["row_id"]]
            if inputs.value("assets.replacements.performance_reset", row=row) != "EXPLICIT_METHOD_RULE":
                raise ContractError("BLOCKED_METHOD_REVIEW", "assets.replacements.performance_reset")
            target = rule["target_retention"]
            if rule["scope"] == "MODULES_UNIFORM_FRACTION":
                if target is None or target > ceiling or "inverter_ids" in rule:
                    raise ContractError("ENERGY_REPLACEMENT_TARGET")
            else:
                if target is not None:
                    raise ContractError("ENERGY_INVERTER_RECOVERY_NOT_DC")
                count = inputs.value("system.inverter_count")
                affected = rule.get("inverter_ids", [])
                if not affected or set(affected)-{f"inv-{i+1}" for i in range(count)}:
                    raise ContractError("ENERGY_REPLACEMENT_DEVICE_SCOPE")
                if rule["capacity_fraction"]*count != len(affected):
                    raise ContractError("ENERGY_REPLACEMENT_CAPACITY_SCOPE")
            days = inputs.numeric("assets.replacements.downtime_days", row=row)
            if days > year_days[year-1]:
                raise ContractError("ENERGY_REPLACEMENT_DOWNTIME")
            events[year] = {**rule, "asset_id": inputs.value("assets.replacements.asset_id", row=row),
                           "downtime_days": days}
    with precision_context(inputs.methods.require("precision.digits")):
        retention = Decimal(1) if included else 1-initial
        result = []
        for year in range(1, years+1):
            previous = retention
            rate = Decimal(0) if year == 1 else rates[year-1]
            aged = previous * (1-rate)
            event = events.get(year)
            uplift = Decimal(0)
            downtime = Decimal(1)
            if event:
                fraction = event["capacity_fraction"]
                if event["scope"] == "MODULES_UNIFORM_FRACTION":
                    if event["target_retention"] < aged:
                        raise ContractError("ENERGY_REPLACEMENT_NEGATIVE_RECOVERY")
                    uplift = fraction * (event["target_retention"]-aged)
                downtime = 1-fraction*event["downtime_days"]/year_days[year-1]
            retention = aged+uplift
            result.append({"operating_year": year, "retention": retention,
                "aged_retention_before_replacement": aged,
                "year_days": year_days[year-1],
                "previous_retention": previous, "annual_fraction": rate,
                "replacement_uplift": uplift, "equivalent_availability": downtime,
                "initial_fraction": initial, "initial_in_upstream_pr": included,
                "event": event})
        return result
