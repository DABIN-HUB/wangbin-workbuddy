"""Phase 3C independent rooftop/ground settlement over verified 3B evidence.

Only the existing canonical result is produced. Generation is not recomputed;
transaction expenses are disclosed separately from the frozen gross-benefit
formulas, and no cash collection, tax, financing or financial return is inferred.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import shutil
from types import SimpleNamespace
from uuid import uuid4

from ..errors import ContractError
from ..serialization import digest, dumps
from ..timeseries_bundle import BundleBudget
from ..timeseries_private import Meter, local_target, write_file
from .common import precision_context
from .consumption import evaluate, FORMULA_IDS
from .energy_inputs import EnergyInputs
from .energy_yield import _EvidenceWriter, _metric
from .generation_evidence import GenerationEvidence
from .input_contract import calculation_identity
from .result_contract import seal_result, validate_result
from .solar_resource import month_parts
from .tariffs import Tariffs, SettlementSeries, load_energy, lineage

ENERGY_KEYS = ("available_kwh", "self_kwh", "export_kwh", "curtailed_kwh", "delivered_kwh", "balance_residual_kwh")
MONEY_KEYS = ("self_value", "export_sales_revenue", "transaction_cost", "embedded_transaction_cost", "other_benefit", "gross_benefit", "benefit_after_transaction_cost")


class _SettlementInputs(EnergyInputs):
    """Bounded raw-field references, not an unbounded set of row identifiers."""

    def __init__(self,*args):
        self.field_ids = set()
        super().__init__(*args)

    def record(self,field_id,*,row=None):
        record = super().record(field_id,row=row)
        self.field_ids.add(field_id)  # At most the frozen 469 raw field IDs.
        return record


def _near(inputs, a, b):
    return abs(a-b) <= inputs.methods.require("precision.abs_tolerance")+inputs.methods.require("precision.rel_tolerance")*max(abs(a),abs(b))


def _scalar(inputs, fid, values):
    answer = evaluate(fid, values, {"precision_digits":inputs.methods.require("precision.digits")})
    if answer["status"] != "CALCULATED":
        raise ContractError(answer["reason"])
    return answer["value"]


def _business(inputs, category, generation):
    if inputs.pv_type != category:
        raise ContractError("CONSUMPTION_CATEGORY_MISMATCH")
    if inputs.value("project.has_storage") is not False:
        raise ContractError("CONSUMPTION_STORAGE_NOT_IMPLEMENTED")
    mode = inputs.value("project.sales_mode")
    method = inputs.methods.require("settlement.revenue_method")
    repetition = inputs.methods.require("consumption.load_repetition")
    cap = inputs.methods.require("consumption.commercial_export_limit_kw")
    if category == "utility_scale_ground":
        if mode != "full_export" or method != "EXPORT_ONLY" or repetition != "NO_LOAD_GROUND":
            raise ContractError("CONSUMPTION_GROUND_SALES_MODEL")
        if any(fid.startswith("load.") for fid in inputs.values):
            raise ContractError("CONSUMPTION_GROUND_LOAD_FORBIDDEN")
        return False, cap
    if mode == "full_export":
        if method != "EXPORT_ONLY" or repetition != "NO_LOAD_FULL_EXPORT":
            raise ContractError("CONSUMPTION_ROOFTOP_FULL_EXPORT_MODEL")
        need_load = False
    elif mode == "self_use_surplus_export":
        if repetition != generation.repetition:
            raise ContractError("CONSUMPTION_LOAD_TIME_SCENARIO")
        if inputs.value("load.timezone") != generation.zone.key:
            raise ContractError("CONSUMPTION_LOAD_TIMEZONE")
        if inputs.value("load.meter_boundary") != generation.boundary:
            raise ContractError("CONSUMPTION_METERING_BOUNDARY")
        inputs.value("load.meter_id")
        inputs.value("load.quality_basis")
        owner = inputs.value("project.ownership_mode")
        if ((method == "OWNER_AVOIDED_COST" and owner != "owner_invested")
                or (method in {"PPA_FIXED", "PPA_DISCOUNT"} and owner not in {"ppa", "third_party"})
                or method == "EXPORT_ONLY"):
            raise ContractError("CONSUMPTION_REVENUE_OWNERSHIP_MISMATCH")
        need_load = True
    else:
        raise ContractError("CONSUMPTION_SALES_MODEL_NOT_IMPLEMENTED")
    # These are same-node AC export power bounds, not system loss rates. Ground
    # generation already applied them upstream; only its new commercial cap is
    # applied above. Rooftop available energy has not yet been dispatched.
    return need_load, min(cap,inputs.numeric("grid.export_power_limit"),inputs.numeric("grid.available_capacity"))


def _empty_ledger(need_load):
    return {**{k:Decimal(0) for k in ENERGY_KEYS+MONEY_KEYS}, "load_kwh":Decimal(0) if need_load else None}


def _other_benefits(inputs, tariffs, years, meter):
    rows = inputs.value("revenue.other_items")
    assignments = inputs.methods.require("settlement.other_benefit_months")
    mapping = {a["row_id"]:a["month"] for a in assignments}
    if len(mapping) != len(assignments) or set(mapping) != {r["row_id"] for r in rows}:
        raise ContractError("SETTLEMENT_OTHER_BENEFIT_MONTH_MAPPING")
    monthly = [[Decimal(0) for _ in range(12)] for _ in range(years)]
    proof = []
    for row in rows:
        meter.check()
        get = lambda key:inputs.value("revenue.other_items."+key,row=row)
        year = get("year")
        if year > years or get("exclusive_boundary") != "EXCLUDES_SELF_USE_EXPORT_AND_PPA":
            raise ContractError("SETTLEMENT_OTHER_BENEFIT_BOUNDARY")
        get("contract_id"); get("kind")
        amount = tariffs.money("revenue.other_items.amount",row=row)
        month = mapping[row["row_id"]]
        monthly[year-1][month-1] += amount
        proof.append({"operating_year":year,"month":month,"amount":amount,"lineage":lineage(inputs,row)})
    return monthly,proof


def _receipt(target, meter, writer, result, counts, calls):
    payload = dumps(result)
    write_file(target/"result.pending",payload.encode("utf-8"),meter)
    stats = meter.stats()
    receipt = {"stats":{k:Decimal(str(v)) if isinstance(v,float) else v for k,v in stats.items()},
        "input_rows_by_role":counts,"year_interval_settlements":calls,
        "resource_enforcement":"COOPERATIVE_APPLICATION_CHECKPOINTS_NOT_OS_SANDBOX",
        "measurement_scope":"RESULT_DATA_FSYNC_COMPLETE; DISK_INCLUDES_INPUTS_AND_RECEIPT; TIME_AND_MEMORY_SAMPLED_BEFORE_RECEIPT_FSYNC",
        "chunks":writer.chunks,"result_hash":result["result_hash"]}
    for _ in range(8):
        data = dumps(receipt).encode("utf-8")
        total = meter.disk+len(data)
        if receipt["stats"]["disk_bytes"] == total:
            break
        receipt["stats"]["disk_bytes"] = total
        receipt["stats"]["peak_disk_reserved_bytes"] = max(stats["peak_disk_reserved_bytes"],total)
    else:
        raise ContractError("SETTLEMENT_RECEIPT_SIZE")
    write_file(target/"receipt.json",data,meter)
    meter.check()
    (target/"result.pending").rename(target/"result.json")


def _calculate(exported, methods, *, generation_dir, generation_result_hash, catalog, output_dir, budget, bundle, category):
    if type(budget) is not BundleBudget:
        raise ContractError("BUNDLE_BUDGET")
    budget.__post_init__()
    meter = Meter(budget)
    inputs = _SettlementInputs(exported,methods,catalog)
    meter.input = bundle.stats["input_bytes"] if bundle is not None else len(dumps(inputs.validated.export).encode("utf-8"))
    meter.disk = meter.input
    meter.check()
    target = local_target(output_dir)
    try:
        target.mkdir()
    except FileExistsError:
        raise ContractError("CONSUMPTION_OUTPUT_EXISTS") from None
    try:
        with precision_context(inputs.methods.require("precision.digits")):
            generation = GenerationEvidence(generation_dir,generation_result_hash,inputs,meter,bundle)
            need_load,cap = _business(inputs,category,generation)
            if category == "utility_scale_ground" and bundle is not None and "load.series" in bundle.dataset_ids:
                raise ContractError("CONSUMPTION_GROUND_LOAD_FORBIDDEN")
            load = SettlementSeries("load.series",inputs,generation,bundle,meter) if need_load else None
            tariffs = Tariffs(inputs,generation,bundle,meter)
            other,other_proof = _other_benefits(inputs,tariffs,generation.years,meter)
            annual = [_empty_ledger(need_load) for _ in range(generation.years)]
            monthly = [[_empty_ledger(need_load) for _ in range(12)] for _ in range(generation.years)]
            writer = _EvidenceWriter(target,meter)
            count = calls = 0
            for row,start,end,hours in generation.rows():
                count += 1
                load_row = load.take(start,end) if load else None
                demand = load_energy(inputs,load_row,hours) if load_row is not None else None
                quote = tariffs.quote(start,end)
                parts = list(month_parts(SimpleNamespace(start=start,end=end),generation.zone.key))
                calculations = []
                for calculation in row["calculations"]:
                    year = calculation["operating_year"]
                    a = annual[year-1]
                    available = calculation["state"]["output_kw"]*hours
                    used = (_scalar(inputs,"F-SELF-CONSUMPTION",{"energy.available_kwh":available,"load.interval_kwh":demand})
                            if need_load else Decimal(0))
                    limit = cap*hours
                    exported_energy = _scalar(inputs,"F-EXPORTED-ENERGY",{"energy.available_kwh":available,"consumption.self_kwh":used,"grid.export_limit_kwh":limit})
                    curtailed = _scalar(inputs,"F-CURTAILED-ENERGY",{"energy.available_kwh":available,"consumption.self_kwh":used,"consumption.export_kwh":exported_energy})
                    balance = _scalar(inputs,"F-ENERGY-BALANCE",{"energy.available_kwh":available,"consumption.self_kwh":used,"consumption.export_kwh":exported_energy,"consumption.curtailed_kwh":curtailed})
                    if not _near(inputs,balance,Decimal(0)) or used > available or (need_load and used > demand) or exported_energy > limit:
                        raise ContractError("CONSUMPTION_ENERGY_CONSERVATION")
                    factor = (1+tariffs.escalation)**(year-1)
                    sell_price = quote["sell"]*factor
                    self_price = ((quote["avoid"] if tariffs.revenue_method == "OWNER_AVOIDED_COST" else quote["ppa"])*factor
                                  if need_load else None)
                    self_value = used*self_price if need_load and used != 0 else Decimal(0)
                    sales = exported_energy*sell_price if exported_energy != 0 else Decimal(0)
                    fee_amount = exported_energy*quote["fee"]*factor
                    expense = fee_amount if tariffs.fee_treatment == "SEPARATE_LEDGER" else Decimal(0)
                    embedded = fee_amount if tariffs.fee_treatment == "ALREADY_IN_PRICE" else Decimal(0)
                    values = {"available_kwh":available,"load_kwh":demand,"self_kwh":used,"export_kwh":exported_energy,
                        "curtailed_kwh":curtailed,"delivered_kwh":used+exported_energy,"balance_residual_kwh":balance,
                        "self_value":self_value,"export_sales_revenue":sales,"transaction_cost":expense,
                        "embedded_transaction_cost":embedded,"other_benefit":Decimal(0),"gross_benefit":self_value+sales,
                        "benefit_after_transaction_cost":self_value+sales-expense}
                    for key,value in values.items():
                        if value is not None:
                            a[key] += value
                    for month,duration in parts:
                        m = monthly[year-1][int(month[-2:])-1]
                        for key,value in values.items():
                            if value is not None:
                                m[key] += value*duration/hours
                    calculations.append({"operating_year":year,"ledger":values,"export_limit_kwh":limit,
                        "self_price":self_price,"sale_price":sell_price,"fee_price":quote["fee"]*factor,
                        "price_escalation_factor":factor})
                    calls += 1
                    meter.check()
                writer.add({"generation_result_hash":generation_result_hash,"generation_resource_row_id":row["resource_row_id"],
                    "start":start.isoformat(),"end":end.isoformat(),"hours":hours,
                    "load":None if load_row is None else lineage(inputs,load_row),
                    "prices":quote,"calculations":calculations})
            if load:
                load.finish()
            tariffs.finish()
            if not generation.complete:
                raise ContractError("GENERATION_TRACE_INCOMPLETE")
            for i,a in enumerate(annual):
                for month,amount in enumerate(other[i]):
                    m = monthly[i][month]
                    for key in ("other_benefit","gross_benefit","benefit_after_transaction_cost"):
                        m[key] += amount
                        a[key] += amount
                for key,value in a.items():
                    if value is not None and not _near(inputs,value,sum(m[key] for m in monthly[i])):
                        raise ContractError("CONSUMPTION_MONTHLY_AGGREGATION")
                if (not _near(inputs,a["available_kwh"],generation.metrics[f"energy.year.{i+1}"]["value"])
                        or not _near(inputs,a["gross_benefit"],a["self_value"]+a["export_sales_revenue"]+a["other_benefit"])
                        or not _near(inputs,a["benefit_after_transaction_cost"],a["gross_benefit"]-a["transaction_cost"])):
                    raise ContractError("CONSUMPTION_ANNUAL_CONSERVATION")
            identity = calculation_identity(inputs.validated,inputs.methods,catalog,datasets=bundle)
            result = deepcopy(generation.result)
            result["run_id"],result["created_at"] = str(uuid4()),datetime.now(timezone.utc).isoformat()
            snapshot = identity["source_snapshot"]
            snapshot["generation"] = {"result_hash":generation_result_hash,"input_hash":generation.result["input_hash"],
                "source_snapshot_id":generation.result["source_snapshot_id"],"source_snapshot":generation.result["source_snapshot"],
                "interval_identity":generation.proof}
            source_id = digest(snapshot)
            payload = identity["input_identity_payload"]
            payload["source_snapshot_id"] = source_id
            payload["generation_result_hash"] = generation_result_hash
            result.update(input_hash=digest(payload),source_snapshot_id=source_id,source_snapshot=snapshot,
                          evaluation_date=inputs.evaluation_date.isoformat(),currency=inputs.value("project.currency"))
            result["inputs"].update(identity_payload=payload,method_config_hash=inputs.methods.hash,
                normalized=inputs.validated.export["normalized_inputs"],
                used_fields=sorted(inputs.field_ids|set(generation.result["inputs"]["used_fields"])),
                used_sources=sorted({r["source_id"] for r in inputs.used.values()}|set(generation.result["inputs"]["used_sources"])),
                generation_result_hash=generation_result_hash)
            trace = writer.finish()
            trace.update(status="CALCULATED",formula_version=catalog.definition_version,formula_ids=list(FORMULA_IDS),
                         time_rule="SAME_UTC_INTERVALS_NO_RESAMPLING",generation_boundary=generation.boundary)
            result["evidence"].update({"consumption-intervals":trace,"settlement-other-benefits":other_proof,
                "settlement-input-lineage":inputs.used,"settlement-basis":tariffs.basis})
            result["boundaries"].update({"CONSUMPTION":{**generation.result["boundaries"][generation.boundary],
                "position":generation.boundary,"curtailment":"ADDITIONAL_COMMERCIAL_ONLY_NO_REPEATED_ELECTRICAL_LOSSES"},
                "SETTLEMENT":{**tariffs.basis,"revenue_method":tariffs.revenue_method,"fee_treatment":tariffs.fee_treatment,
                    "self_use_saving_is_cash_receipt":False,"cash_collection":"NOT_IMPLEMENTED"}})
            result["formula_snapshot"]["consumption_definitions"] = {fid:catalog.formulas[fid] for fid in FORMULA_IDS}
            result["artifact_manifest"] = [
                {"kind":"UPSTREAM_PHASE3B_GENERATION","directory":str(generation.path),"result_hash":generation_result_hash}]
            result["evidence"]["deferred-financial-domains"] = {name:"NOT_IMPLEMENTED" for name in
                ("investment","operating_expenses","depreciation","tax_payments","financing","cashflow","NPV","IRR","LCOE")}
            result["findings"] = [f for f in result["findings"] if f.get("code") != "NO_PHASE3C_LOAD_OR_REVENUE_CALCULATIONS"]
            result["findings"].extend([
                {"code":"FINANCE_TAX_CASHFLOW_AND_FINANCIAL_RETURNS_NOT_IMPLEMENTED","status":"NOT_IMPLEMENTED"},
                {"code":"INTERVAL_MEAN_SAME_GRID_NOT_INSTANTANEOUS_LOAD_MATCH","status":"KNOWN_LIMITATION"},
                {"code":"ECONOMIC_BASIS_NOT_TAX_PAYMENT_OR_CURRENCY_CONVERSION","status":"KNOWN_LIMITATION"}])
            if need_load and generation.repetition == "EXPLICIT_REPRESENTATIVE_SCENARIO":
                result["findings"].append({"code":"REPEATED_LOAD_AND_BASE_PERIOD_PRICES_ARE_EXPLICIT_SCENARIOS_NOT_OBSERVED_FUTURE_YEARS","status":"DECLARED_SCENARIO"})
            if inputs.values.get("grid.opinion_status",{}).get("value") != "confirmed":
                result["findings"].append({"code":"GRID_ACCEPTANCE_UNCONFIRMED_SCENARIO_NOT_APPROVAL","status":"CONDITIONAL"})
            result["results"]["metrics"] = [m for m in result["results"]["metrics"] if m["metric_id"] not in {"consumption","revenue"}]
            currency = result["currency"]
            formula = "F-PPA-REVENUE" if tariffs.revenue_method.startswith("PPA_") else "F-ENERGY-REVENUE"
            for i,a in enumerate(annual,1):
                details = {"ledger":a,"monthly":monthly[i-1],"load_applicability":"REQUIRED_AND_VALIDATED" if need_load else "NOT_APPLICABLE_EXPLICIT_FULL_EXPORT",
                           "self_value_kind":tariffs.revenue_method,"upstream_generation_metric":f"energy.year.{i}"}
                _metric(result,catalog,f"consumption.year.{i}",a["self_kwh"],"kWh","F-SELF-CONSUMPTION","CONSUMPTION",f"OPERATING_YEAR_{i}",details=details)
                _metric(result,catalog,f"revenue.year.{i}",a["gross_benefit"],currency,formula,"SETTLEMENT",f"OPERATING_YEAR_{i}",details={"ledger":a,"monthly":monthly[i-1]})
                _metric(result,catalog,f"consumption.self_ratio.year.{i}",None if a["delivered_kwh"] == 0 else a["self_kwh"]/a["delivered_kwh"],"1","F-SELF-CONSUMPTION-RATIO","CONSUMPTION",f"OPERATING_YEAR_{i}",
                    status="UNDEFINED" if a["delivered_kwh"] == 0 else "CALCULATED",reason="ZERO_DELIVERED_ENERGY" if a["delivered_kwh"] == 0 else None,
                    details={"denominator":"SELF_PLUS_EXPORT_EXCLUDES_CURTAILMENT","export_fraction_of_delivered":None if a["delivered_kwh"] == 0 else a["export_kwh"]/a["delivered_kwh"]})
                coverage = None if not need_load or a["load_kwh"] == 0 else a["self_kwh"]/a["load_kwh"]
                _metric(result,catalog,f"consumption.load_coverage.year.{i}",coverage,"1","F-LOAD-COVERAGE-RATIO","CONSUMPTION",f"OPERATING_YEAR_{i}",
                    status="NOT_APPLICABLE" if not need_load else ("UNDEFINED" if coverage is None else "CALCULATED"),
                    reason="EXPLICIT_FULL_EXPORT_NO_CUSTOMER_LOAD" if not need_load else ("ZERO_LOAD" if coverage is None else None))
                _metric(result,catalog,f"energy.delivered.year.{i}",a["delivered_kwh"],"kWh","F-DELIVERED-ENERGY","CONSUMPTION",f"OPERATING_YEAR_{i}")
            lifecycle = {key:(None if annual[0][key] is None else sum(a[key] for a in annual)) for key in annual[0]}
            _metric(result,catalog,"consumption",lifecycle["self_kwh"],"kWh","F-SELF-CONSUMPTION","CONSUMPTION","LIFECYCLE",details={"ledger":lifecycle})
            _metric(result,catalog,"revenue",lifecycle["gross_benefit"],currency,formula,"SETTLEMENT","LIFECYCLE",details={"ledger":lifecycle,"cash_receipts":"NOT_CALCULATED"})
            for metric in result["results"]["metrics"]:
                mid = metric["metric_id"]
                if mid.startswith("consumption.year."):
                    metric["upstream_metric_ids"] = ["energy.year."+mid.rsplit(".",1)[1]]
                elif mid.startswith(("revenue.year.","consumption.self_ratio.year.","consumption.load_coverage.year.","energy.delivered.year.")):
                    metric["upstream_metric_ids"] = ["consumption.year."+mid.rsplit(".",1)[1]]
                elif mid in {"consumption","revenue"}:
                    metric["upstream_metric_ids"] = [f"{mid}.year.{i}" for i in range(1,generation.years+1)]
            for domain,prefix in (("consumption","consumption"),("revenue","revenue")):
                result["results"]["domains"][domain] = [m["metric_id"] for m in result["results"]["metrics"] if m["metric_id"] == prefix or m["metric_id"].startswith(prefix+".")]
            result["results"]["domains"]["delivered_energy"] = [f"energy.delivered.year.{i}" for i in range(1,generation.years+1)]
            result["status"] = "PARTIAL"
            result["maturity"]["calculation"] = ("CALCULATED_SYNTHETIC" if inputs.methods.data_mode == "SYNTHETIC" or generation.result["maturity"]["calculation"] == "CALCULATED_SYNTHETIC" else "CALCULATED_CONDITIONAL")
            result = seal_result(result)
            validate_result(result,catalog)
            _receipt(target,meter,writer,result,{"generation":count,"load":load.count if load else 0,
                "market":tariffs.market.count if tariffs.market else 0},calls)
            return result
    except BaseException:
        shutil.rmtree(target)
        raise


def calculate_rooftop(exported,methods,*,generation_dir,generation_result_hash,catalog,output_dir,budget,bundle=None):
    return _calculate(exported,methods,generation_dir=generation_dir,generation_result_hash=generation_result_hash,
        catalog=catalog,output_dir=output_dir,budget=budget,bundle=bundle,category="industrial_rooftop")


def calculate_ground(exported,methods,*,generation_dir,generation_result_hash,catalog,output_dir,budget,bundle=None):
    return _calculate(exported,methods,generation_dir=generation_dir,generation_result_hash=generation_result_hash,
        catalog=catalog,output_dir=output_dir,budget=budget,bundle=bundle,category="utility_scale_ground")
