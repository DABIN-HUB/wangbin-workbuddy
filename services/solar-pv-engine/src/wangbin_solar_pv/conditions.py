"""Three-valued frozen input obligations, separate from evidence and calculations."""
from __future__ import annotations

from decimal import Decimal
from .errors import ContractError


def known(project, field_id):
    record = project.values.get(field_id, {})
    if record.get("status") not in {"VERIFIED", "UNVERIFIED"}:
        return None
    return record.get("value")


def _truth(value):
    return "U" if value is None else ("T" if value else "F")


def _and(a, b):
    return "F" if "F" in (a, b) else ("U" if "U" in (a, b) else "T")


def _export(project):
    mode = known(project, "project.sales_mode")
    if mode in {"full_export", "self_use_surplus_export"}:
        return "T"
    if mode == "off_grid":
        return "F"
    return "U"


def _price_method(project):
    mode = known(project, "tariff.settlement_mode")
    if mode in {"fixed", "tou", "fixed_tou", "fixed_price", "contract_fixed"}:
        return "table"
    if mode in {"market", "market_series", "market_timeseries"}:
        return "market"
    return None


def _hourly(project):
    if project.pv_type == "pv_storage" or known(project, "project.has_storage") is True:
        return "T"
    method = known(project, "resource.model_method")
    if method in {"hourly", "subhourly", "timeseries", "pvwatts_hourly"}:
        return "T"
    if method in {"monthly", "monthly_pr", "annual_pr"}:
        return "F"
    return "U"


def condition_state(rule_id, project, catalog):
    mode = known(project, "project.sales_mode")
    reason = "按冻结条件规则评价；未知不会默认为未触发"
    if rule_id == "IN-C01":
        address = known(project, "site.address")
        lat, lon = known(project, "site.latitude"), known(project, "site.longitude")
        truth = "T" if address is not None or (lat is not None and lon is not None) else "U"
    elif rule_id == "IN-C02":
        truth = "T" if any(known(project, fid) is not None for fid in ("site.total_area", "site.usable_area", "system.dc_capacity")) else "U"
    elif rule_id == "IN-C03":
        truth = "T" if any(known(project, fid) is not None for fid in ("targets.payback_years", "targets.project_irr", "targets.equity_irr")) else "U"
    elif rule_id == "IN-C04":
        if mode in {"self_use_surplus_export", "off_grid"}:
            truth = "T"
        elif mode == "full_export":
            truth = "F"
        elif mode == "hybrid":
            dispatch = known(project, "storage.dispatch_mode")
            truth = "T" if project.pv_type != "pv_storage" or dispatch in {"self_consumption", "hybrid"} else ("F" if dispatch == "arbitrage" else "U")
        else:
            truth = "U"
        reason = "实际负荷/自用方案触发；PPA标签本身不创造企业购电节省"
    elif rule_id == "IN-C05":
        truth = _export(project)
    elif rule_id == "IN-C06":
        ratio = known(project, "finance.debt_ratio")
        schedule = known(project, "finance.debt_schedule")
        amounts = []
        if isinstance(schedule, list):
            for row in schedule:
                for name in ("drawdown", "principal", "interest", "fees"):
                    rec = row.get("fields", {}).get("finance.debt_schedule." + name, {})
                    amounts.append(rec.get("value") if rec.get("status") in {"VERIFIED", "UNVERIFIED"} else None)
        if any(isinstance(v, (int, float, Decimal)) and not isinstance(v, bool) and v > 0 for v in amounts):
            truth = "T"
        elif isinstance(ratio, (int, float, Decimal)) and ratio > 0:
            truth = "T"
        elif ratio == 0:
            truth = "U" if schedule and any(v is None for v in amounts) else "F"
        else:
            truth = "U"
        reason = "明确债务证据优先；比例0不能覆盖有债计划，没有协议不等于无债"
    elif rule_id == "IN-C07":
        storage = known(project, "project.has_storage")
        truth = "T" if project.pv_type == "pv_storage" or storage is True else ("F" if storage is False else "U")
    elif rule_id == "IN-C08":
        truth = "U" if project.pv_type == "pv_storage" and known(project, "storage.base_pv_type") is None else "T"
    elif rule_id == "IN-C09":
        truth = "T" if any(known(project, fid) for fid in ("site.boundary_vertices", "resource.timeseries", "load.series", "tariff.market_series", "storage.dispatch")) else "F"
    elif rule_id == "IN-C10":
        ownership = known(project, "project.ownership_mode")
        truth = "T" if ownership in {"ppa", "revenue_share", "lease"} or known(project, "revenue.other_items") else ("F" if ownership in {"owner_invested", "third_party"} else "U")
    elif rule_id == "IN-C11":
        from .validation import iter_records
        truth = "T" if any(r.get("field_id", "").startswith("tariff.") and isinstance(r.get("value"), (int, float, Decimal)) and r["value"] < 0 for r, _ in iter_records(project.values, catalog)) else "F"
    elif rule_id == "IN-C12":
        truth = "T" if any(catalog.fields.get(fid, {}).get("type") == "array" and rec.get("value") is not None for fid, rec in project.values.items()) else "F"
    elif rule_id == "IN-C13":
        method = _price_method(project)
        truth = "T" if method == "table" else ("F" if method == "market" else "U")
        reason = "价格表与市场时序择一；未知结算模式不同时豁免两类价格证据"
    else:
        raise ContractError("UNKNOWN_CONDITIONAL_RULE")
    return {"rule_id": rule_id, "truth": truth, "reason": reason,
            "baseline_reference": "03-input-data-dictionary.md §2 " + rule_id}


def _binding(fid, catalog):
    field = catalog.fields[fid]
    if fid.endswith(".row_id"):
        return "IN-C12", "item_presence"
    if fid.startswith("load."):
        return "IN-C04", "load_required"
    if fid.startswith("finance.debt_schedule") or fid in {"finance.loan_rate", "finance.loan_years", "finance.grace_years", "finance.debt_fee", "finance.loan_agreement_id", "finance.cfads_definition", "finance.repayment_method"}:
        return "IN-C06", "debt_required"
    if fid in {"finance.project_discount_rate", "finance.equity_discount_rate"}:
        return "IN-C10", "full_financial_scope"
    if fid.startswith("resource.timeseries"):
        return "IN-C09", "hourly_method"
    if fid.startswith("storage.dispatch"):
        return "IN-C07", "storage_required"
    if fid.startswith("tariff.market_series"):
        return "IN-C13", "market_price_method"
    if fid == "tariff.periods.avoidable_price":
        return "IN-C13", "table_and_load"
    if fid == "tariff.periods.sale_price":
        return "IN-C05", "export_required"
    if fid.startswith("tariff.periods"):
        return "IN-C13", "table_price_method"
    if fid == "tariff.ppa_price":
        return "IN-C10", "ppa_contract"
    if fid == "tariff.revenue_share":
        return "IN-C10", "share_contract"
    if fid == "tariff.transaction_fee":
        return "IN-C10", "transaction_contract"
    if fid.startswith("revenue.other_items"):
        return "IN-C10", "requested_other_revenue"
    if fid == "targets.budget_ceiling":
        return "IN-C03", "optional_budget_constraint"
    if fid == "targets.payback_basis":
        return "IN-C03", "payback_selected"
    if fid.startswith("targets."):
        return "IN-C03", "selected_target_or"
    if fid in {"site.address", "site.latitude", "site.longitude"}:
        return "IN-C01", "location_or_coordinate_pair"
    if field.get("repeat_group"):
        return _binding(field["repeat_group"], catalog)
    raise ContractError("UNBOUND_CONDITIONAL_FIELD", fid)


def condition_registry(catalog):
    result = {}
    for fid, field in catalog.fields.items():
        if "CONDITIONAL" in field["required_level"].values():
            rule, predicate = _binding(fid, catalog)
            result[fid] = {"field_id": fid, "rule_id": rule, "predicate": predicate,
                           "parent": field.get("repeat_group"),
                           "baseline_reference": "03-input-fields.json#" + fid + ";03-input-data-dictionary.md §2"}
    return result


def effective_requirement(field_id, level, project, catalog):
    if level not in {"L1", "L2", "L3"} or field_id not in catalog.fields:
        raise ContractError("UNKNOWN_FIELD_OR_LEVEL")
    field = catalog.fields[field_id]
    raw = field["required_level"][level]
    special = field_id.startswith("load.") or field_id in {"tariff.periods.sale_price", "tariff.periods.avoidable_price"}
    if raw != "CONDITIONAL" and not special:
        return {"requirement": "REQUIRED" if raw == "REQUIRED" else "OPTIONAL", "rule_id": None, "truth": "T", "reason": "冻结字段等级义务"}
    rule, predicate = _binding(field_id, catalog)
    truth = condition_state(rule, project, catalog)["truth"]
    if predicate == "item_presence":
        truth = "T"
    elif predicate == "full_financial_scope":
        truth = "F" if level == "L1" else "T"
    elif predicate == "hourly_method":
        truth = _hourly(project)
    elif predicate == "table_price_method":
        truth = "T" if _price_method(project) == "table" else ("F" if _price_method(project) == "market" else "U")
    elif predicate == "market_price_method":
        truth = "T" if _price_method(project) == "market" else ("F" if _price_method(project) == "table" else "U")
    elif predicate == "table_and_load":
        truth = _and(condition_state("IN-C13", project, catalog)["truth"], condition_state("IN-C04", project, catalog)["truth"])
    elif predicate == "ppa_contract":
        ownership = known(project, "project.ownership_mode")
        truth = "U" if ownership is None else _truth(ownership == "ppa")
    elif predicate == "share_contract":
        ownership = known(project, "project.ownership_mode")
        truth = "U" if ownership is None else _truth(ownership == "revenue_share")
    elif predicate == "transaction_contract":
        truth = _export(project)
    elif predicate == "requested_other_revenue":
        # No selected revenue item is not a statement that real-world other revenue is zero.
        truth = "T" if field_id.split(".items")[0] in project.values or "revenue.other_items" in project.values else "F"
    elif predicate == "optional_budget_constraint":
        truth = _truth(known(project, field_id) is not None)
    elif predicate == "payback_selected":
        truth = "T" if known(project, "targets.payback_years") is not None else ("F" if condition_state("IN-C03", project, catalog)["truth"] == "T" else "U")
    elif predicate == "selected_target_or":
        truth = "T" if known(project, field_id) is not None else ("F" if condition_state("IN-C03", project, catalog)["truth"] == "T" else "U")
    elif predicate == "location_or_coordinate_pair":
        address, lat, lon = [known(project, f) for f in ("site.address", "site.latitude", "site.longitude")]
        if field_id == "site.address":
            truth = "T" if address is not None else ("F" if lat is not None and lon is not None else "U")
        else:
            own, other = (lat, lon) if field_id == "site.latitude" else (lon, lat)
            truth = "T" if own is not None or other is not None else ("F" if address is not None else "U")
    if truth == "F":
        requirement = "NOT_APPLICABLE"
    elif raw == "OPTIONAL":
        requirement = "OPTIONAL"
    elif truth == "U":
        requirement = "PENDING_CONDITION"
    else:
        requirement = "REQUIRED"
    return {"requirement": requirement, "rule_id": rule, "predicate": predicate, "truth": truth,
            "reason": "条件由已选输入与冻结规则确定，不以缺协议/缺曲线认定未触发"}
