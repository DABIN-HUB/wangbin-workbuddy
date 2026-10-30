"""Phase 3D financial foundation ledger.

Consumes a sealed Phase 3C settlement result and produces CAPEX, OPEX, asset,
debt, tax, working-capital and cash-receipt foundation schedules. It does not
assemble Phase 3E project/equity cash flow or calculate return metrics.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from ..catalog import Catalog
from ..errors import ContractError
from ..serialization import digest, dumps, loads
from ..timeseries_private import local_target
from . import MODEL_VERSION, RESULT_SCHEMA_VERSION
from .accounting_ledger import evaluate as ledger_formula
from .common import nonnegative, number, ratio
from .costs import evaluate as cost_formula
from .energy_inputs import EnergyInputs
from .energy_yield import _metric
from .input_contract import calculation_identity
from .method_config import MethodConfig
from .result_contract import seal_result, validate_result

FORMULA_IDS = (
    "F-TAX-EXCLUSIVE-AMOUNT", "F-CAPEX-ITEM-AMOUNT", "F-CAPEX-TOTAL", "F-UNIT-INVESTMENT",
    "F-ANNUAL-OPEX", "F-OPEX-ESCALATION", "F-STRAIGHT-LINE-DEPRECIATION", "F-ASSET-BOOK-VALUE",
    "F-TAXABLE-INCOME-PROJECT", "F-TAXABLE-INCOME-EQUITY", "F-INCOME-TAX-ACCRUAL",
    "F-TAX-LOSS-BALANCE", "F-TAX-CASH-BRIDGE", "F-VAT-CREDIT-BALANCE", "F-OTHER-CASH-TAXES",
    "F-CASH-TAX-TOTAL", "F-DEBT-BALANCE", "F-DEBT-INTEREST", "F-INTEREST-BALANCE",
    "F-CASH-RECEIPTS", "F-DEBT-SERVICE", "F-CAPEX-PAYMENT-BALANCE",
)

def _value(inputs, fid, row=None): return inputs.value(fid, row=row)
def _row(inputs, row, fid): return _value(inputs, fid, row=row)
def _method(methods, fid): return methods.require(fid)
def _vec(methods, fid, n):
    value=_method(methods,fid)
    if not isinstance(value,list) or len(value)!=n: raise ContractError("METHOD_PERIOD_VECTOR_MISMATCH",fid)
    return [ratio(x,fid) for x in value]
def _periods(years): return ["CONSTRUCTION"]+[f"OPERATING_YEAR_{y}" for y in range(1,years+1)]
def _period_for_year(y): return "CONSTRUCTION" if y==0 else f"OPERATING_YEAR_{y}"
def _jsonable(value):
    if isinstance(value,dict): return {str(k):_jsonable(v) for k,v in value.items()}
    if isinstance(value,list): return [_jsonable(v) for v in value]
    return value
def _year(text, commissioning, years):
    d=date.fromisoformat(text)
    if d<commissioning: return 0
    return min(max(d.year-commissioning.year+1,1),years)
def _capacity(inputs):
    count=nonnegative(_value(inputs,"system.module_count"),"system.module_count")
    watts=nonnegative(_value(inputs,"system.module_power"),"system.module_power")
    if count==0 or watts==0: raise ContractError("ZERO_DC_CAPACITY")
    return count*watts/Decimal(1000)
def _annual_revenue(settlement, years):
    rows=[]
    for y in range(1,years+1):
        metric=next((m for m in settlement["results"]["metrics"] if m["metric_id"]==f"revenue.year.{y}"),None)
        if metric is None or metric["status"]!="CALCULATED": raise ContractError("UPSTREAM_REVENUE_LEDGER_MISSING",y)
        ledger=metric.get("details",{}).get("ledger")
        keys=("gross_benefit","benefit_after_transaction_cost","export_sales_revenue","self_value")
        if not isinstance(ledger,dict) or any(ledger.get(k) is None for k in keys): raise ContractError("UPSTREAM_REVENUE_LEDGER_INCOMPLETE",y)
        rows.append({k:number(ledger[k],f"revenue.year.{y}.{k}") for k in keys})
    return rows

def _check_upstream(inputs, settlement):
    if settlement.get("project_id")!=inputs.validated.project.project_id: raise ContractError("UPSTREAM_PROJECT_ID_MISMATCH")
    if settlement.get("pv_type")!=inputs.pv_type: raise ContractError("UPSTREAM_CATEGORY_MISMATCH")
    if settlement.get("status") not in {"CALCULATED_SYNTHETIC","CALCULATED_CONDITIONAL","PARTIAL"}: raise ContractError("UPSTREAM_RESULT_NOT_ACCEPTABLE")
    old=settlement.get("inputs",{}).get("normalized",{}); current=inputs.validated.export.get("normalized_inputs",{})
    financial_overlay_prefixes=("capex.","opex.","assets.","tax.","finance.","equity.","working_capital.")
    for fid,val in old.items():
        if fid=="schedule.commissioning_date" or any(fid.startswith(prefix) for prefix in financial_overlay_prefixes):
            continue
        if current.get(fid)!=val: raise ContractError("UPSTREAM_INPUT_FIELD_MISMATCH",fid)
    if not settlement.get("result_hash"): raise ContractError("UPSTREAM_RESULT_HASH_MISSING")
    return settlement["result_hash"]

def _capex(inputs, currency, commissioning, years):
    rows=inputs.rows("capex.items"); ids=[]; amounts={}; net={}; payment={}; basis=Decimal(0); recoverable=Decimal(0); categories={}; entries=[]
    for r in rows:
        rid=str(_row(inputs,r,"capex.items.row_id"))
        if rid in ids: raise ContractError("DUPLICATE_CAPEX_ROW_ID",rid)
        ids.append(rid)
        if _row(inputs,r,"capex.items.currency")!=currency or nonnegative(_row(inputs,r,"capex.items.fx_rate"),"capex.items.fx_rate")!=1: raise ContractError("CAPEX_CURRENCY_CONVERSION_NOT_APPROVED",rid)
        amount=cost_formula("F-CAPEX-ITEM-AMOUNT",{"capex.items.quantity":nonnegative(_row(inputs,r,"capex.items.quantity"),"capex.items.quantity"),"capex.items.unit_price":nonnegative(_row(inputs,r,"capex.items.unit_price"),"capex.items.unit_price")})["value"]
        declared=nonnegative(_row(inputs,r,"capex.items.amount"),"capex.items.amount")
        if declared!=amount: raise ContractError("CAPEX_AMOUNT_RECONCILIATION",rid)
        vat=ratio(_row(inputs,r,"capex.items.vat_rate"),"capex.items.vat_rate")
        net_amount=cost_formula("F-TAX-EXCLUSIVE-AMOUNT",{"tax.inclusive_amount":amount,"tax.vat_rate":vat})["value"] if _row(inputs,r,"capex.items.tax_included") else amount
        vat_amount=amount-net_amount; recoverable+=vat_amount*ratio(_row(inputs,r,"capex.items.recoverable_vat_share"),"capex.items.recoverable_vat_share")
        basis+=net_amount+vat_amount*(1-ratio(_row(inputs,r,"capex.items.recoverable_vat_share"),"capex.items.recoverable_vat_share"))
        amounts[rid]=amount; net[rid]=net_amount; categories[rid]=_row(inputs,r,"capex.items.category")
        paid_on=date.fromisoformat(_row(inputs,r,"capex.items.payment_date")); y=_year(paid_on.isoformat(),commissioning,years)
        if paid_on.year-commissioning.year+1>years: raise ContractError("CAPEX_PAYMENT_OUTSIDE_HORIZON",rid)
        payment[y]=payment.get(y,Decimal(0))+amount
        entries.append((rid,_row(inputs,r,"capex.items.asset_id"),amount,y,vat_amount*ratio(_row(inputs,r,"capex.items.recoverable_vat_share"),"capex.items.recoverable_vat_share")))
    replacement_accrued={y:Decimal(0) for y in range(1,years+1)}; replacement_paid={y:Decimal(0) for y in range(1,years+1)}; replacement_vat={y:Decimal(0) for y in range(1,years+1)}; linked=set(); links={}
    for event in inputs.optional("assets.replacements") or []:
        event_id=_row(inputs,event,"assets.replacements.row_id"); asset=_row(inputs,event,"assets.replacements.asset_id"); year=int(_row(inputs,event,"assets.replacements.year")); cost=nonnegative(_row(inputs,event,"assets.replacements.cost"),"assets.replacements.cost")
        candidates=[e for e in entries if e[1]==asset and e[2]==cost and e[3]>=year and e[0] not in linked]
        if len(candidates)!=1: raise ContractError("REPLACEMENT_PAYMENT_SOURCE_REQUIRED",event_id)
        row_id,_,_,payment_year,eligible_vat=candidates[0]
        linked.add(row_id); links[event_id]={"capex_row_id":row_id,"asset_id":asset,"capitalization_year":year,"payment_year":payment_year,"amount":cost}
        replacement_accrued[year]+=cost; replacement_paid[payment_year]+=cost; replacement_vat[year]+=eligible_vat
    if any(year>0 and row_id not in linked for row_id,_,_,year,_ in entries):
        raise ContractError("FUTURE_CAPEX_SCOPE_NOT_APPROVED")
    total=cost_formula("F-CAPEX-TOTAL",{"capex.items.amount":amounts,"capex.item_ids":ids})["value"]
    initial_total=sum((amount for row_id,_,amount,_,_ in entries if row_id not in linked),Decimal(0))
    return {"ids":ids,"amounts":amounts,"net_amounts":net,"categories":categories,"payment_by_year":payment,"total":total,"initial_total":initial_total,"replacement_accrued_by_year":replacement_accrued,"replacement_paid_by_year":replacement_paid,"replacement_vat_by_year":replacement_vat,"replacement_links":links,"net_total":sum(net.values(),Decimal(0)),"recoverable_vat":recoverable-sum(replacement_vat.values(),Decimal(0)),"depreciable_basis":basis}

def _opex(inputs, years):
    rows=inputs.rows("opex.items"); annual={y:Decimal(0) for y in range(1,years+1)}; net={y:Decimal(0) for y in range(1,years+1)}; vat={y:Decimal(0) for y in range(1,years+1)}
    for r in rows:
        start=int(_row(inputs,r,"opex.items.from_year")); end=int(_row(inputs,r,"opex.items.to_year")); base=nonnegative(_row(inputs,r,"opex.items.base_amount"),"opex.items.base_amount"); rate=number(_row(inputs,r,"opex.items.escalation_rate"),"opex.items.escalation_rate")
        if start<1 or end<start or end>years or rate<=-1: raise ContractError("OPEX_PERIOD_OR_RATE_DOMAIN")
        vr=ratio(_row(inputs,r,"opex.items.vat_rate"),"opex.items.vat_rate"); share=ratio(_row(inputs,r,"opex.items.recoverable_vat_share"),"opex.items.recoverable_vat_share")
        for y in range(start,end+1):
            amount=cost_formula("F-OPEX-ESCALATION",{"opex.items.base_amount":base,"opex.items.escalation_rates":[rate]*(y-start+1),"time.escalation_year":y-start+1})["value"]
            n=cost_formula("F-TAX-EXCLUSIVE-AMOUNT",{"tax.inclusive_amount":amount,"tax.vat_rate":vr})["value"] if _row(inputs,r,"opex.items.tax_included") else amount
            annual[y]+=amount; net[y]+=n; vat[y]+=(amount-n)*share
    return {"annual":annual,"net":net,"recoverable_vat":vat}

def _assets(inputs, years, commissioning):
    assets={}
    for r in inputs.rows("assets.depreciation"):
        aid=str(_row(inputs,r,"assets.depreciation.asset_id"))
        if aid in assets or _row(inputs,r,"assets.depreciation.method")!="straight_line": raise ContractError("DEPRECIATION_METHOD_OR_ASSET_ID")
        assets[aid]={"basis":nonnegative(_row(inputs,r,"assets.depreciation.depreciable_basis"),"assets.depreciation.depreciable_basis"),"residual":nonnegative(_row(inputs,r,"assets.depreciation.residual_value"),"assets.depreciation.residual_value"),"life":int(_row(inputs,r,"assets.depreciation.depreciation_years")),"start":max(1,_year(_row(inputs,r,"assets.depreciation.in_service_date"),commissioning,years)),"replacements":{}}
    replacement_rows=inputs.optional("assets.replacements") or []
    for r in replacement_rows:
        aid=_row(inputs,r,"assets.replacements.asset_id"); y=int(_row(inputs,r,"assets.replacements.year"))
        if aid not in assets or y<1 or y>years or y in assets[aid]["replacements"]: raise ContractError("REPLACEMENT_ASSET_OR_YEAR")
        assets[aid]["replacements"][y]={"cost":nonnegative(_row(inputs,r,"assets.replacements.cost"),"assets.replacements.cost"),"residual":nonnegative(_row(inputs,r,"assets.replacements.salvage"),"assets.replacements.salvage"),"life":int(number(_row(inputs,r,"assets.replacements.new_life"),"assets.replacements.new_life"))}
    return assets

def _depreciation(inputs, assets, years, timing):
    if timing!="FULL_OPERATION_YEAR": raise ContractError("DEPRECIATION_TIMING_NOT_IMPLEMENTED",timing)
    dep={y:Decimal(0) for y in range(1,years+1)}; book={0:Decimal(0)}; records=[]
    for aid,a in assets.items():
        opening=Decimal(0); basis=a["basis"]; residual=a["residual"]; life=a["life"]
        for y in range(1,years+1):
            addition=Decimal(0); disposal=Decimal(0)
            if y==a["start"]: addition=basis
            if y in a["replacements"]:
                disposal=opening; addition=a["replacements"][y]["cost"]; basis=a["replacements"][y]["cost"]; residual=a["replacements"][y]["residual"]; life=a["replacements"][y]["life"]
            annual=Decimal(0)
            if y>=a["start"]:
                annual=min(cost_formula("F-STRAIGHT-LINE-DEPRECIATION",{"depreciation.asset_basis":basis,"depreciation.asset_residual":residual,"depreciation.asset_life_years":life})["value"],max(Decimal(0),opening+addition-residual))
            closing=cost_formula("F-ASSET-BOOK-VALUE",{"assets.opening_book_value":opening,"assets.capitalized_additions":addition,"depreciation.asset_annual":annual,"assets.disposal_book_value":disposal})["value"]
            dep[y]+=annual; records.append({"asset_id":aid,"year":y,"opening":opening,"addition":addition,"disposal":disposal,"depreciation":annual,"closing":closing}); opening=closing
    for y in range(1,years+1): book[y]=sum((r["closing"] for r in records if r["year"]==y),Decimal(0))
    return {"annual":dep,"book":book,"records":records}

def _debt(inputs, methods, capex, periods, years):
    ratio_value=ratio(_value(inputs,"finance.debt_ratio"),"finance.debt_ratio"); basis=_method(methods,"debt.drawdown_basis"); rows={p:{"drawdown":Decimal(0),"principal_due":Decimal(0),"fees_due":Decimal(0)} for p in periods}
    raw=inputs.optional("finance.debt_schedule") or []
    for r in raw:
        y=int(_row(inputs,r,"finance.debt_schedule.date")[:4])-int(_value(inputs,"schedule.commissioning_date")[:4])+1; y=0 if y<1 else min(y,years); p=_period_for_year(y)
        rows[p]["drawdown"]+=nonnegative(_row(inputs,r,"finance.debt_schedule.drawdown"),"finance.debt_schedule.drawdown"); rows[p]["fees_due"]+=nonnegative(_row(inputs,r,"finance.debt_schedule.fees"),"finance.debt_schedule.fees")
        rows[p]["raw_principal"] = rows[p].get("raw_principal",Decimal(0))+nonnegative(_row(inputs,r,"finance.debt_schedule.principal"),"finance.debt_schedule.principal")
    if basis=="NO_DEBT_DECLARED" and ratio_value!=0: raise ContractError("DEBT_BASIS_RATIO_CONFLICT")
    if basis=="CAPEX_PROPORTIONAL_SCENARIO":
        for p in periods: rows[p]["drawdown"]=capex["initial_total"]*ratio_value if p=="CONSTRUCTION" else Decimal(0)
    if basis=="EXPLICIT_RAW_SCHEDULE" and ratio_value>0 and not any(x["drawdown"] for x in rows.values()): raise ContractError("DEBT_DRAWdown_MISSING")
    if ratio_value==0: return {"rows":rows,"has_debt":False,"opening":Decimal(0)}
    repayment=_value(inputs,"finance.repayment_method"); total=sum((x["drawdown"] for x in rows.values()),Decimal(0)); loan_years=int(_value(inputs,"finance.loan_years")); grace=int(_value(inputs,"finance.grace_years")); rate=ratio(_value(inputs,"finance.loan_rate"),"finance.loan_rate")
    eligible=[y for y in range(1,years+1) if y>grace]
    if repayment=="custom_schedule":
        for y in eligible: rows[f"OPERATING_YEAR_{y}"]["principal_due"]=rows[f"OPERATING_YEAR_{y}"].get("raw_principal",Decimal(0))
    elif repayment=="equal_principal":
        for y in eligible[:loan_years]: rows[f"OPERATING_YEAR_{y}"]["principal_due"]=total/loan_years
    elif repayment=="bullet":
        if eligible: rows[f"OPERATING_YEAR_{eligible[min(loan_years,len(eligible))-1]}"]["principal_due"]=total
    elif repayment=="annuity":
        n=min(loan_years,len(eligible)); payment=total*rate*(1+rate)**n/((1+rate)**n-1) if rate else total/n; balance=total
        for y in eligible[:n]: rows[f"OPERATING_YEAR_{y}"]["principal_due"]=max(Decimal(0),payment-balance*rate); balance-=rows[f"OPERATING_YEAR_{y}"]["principal_due"]
    else: raise ContractError("REPAYMENT_METHOD_NOT_SUPPORTED")
    return {"rows":rows,"has_debt":True,"opening":nonnegative(_method(methods,"debt.opening_principal"),"debt.opening_principal"),"rate":rate}

def _income_tax_schedule(base, loss, payable, prepaid, income_rate, loss_fraction, payment_fraction, tax_basis):
    used=min(loss,max(Decimal(0),base))*loss_fraction
    charge=cost_formula("F-INCOME-TAX-ACCRUAL",{"tax.income_rate":income_rate,"tax.selected_base_pre_losses":base,"tax.losses_used":used,"finance.tax_basis":tax_basis})["value"]
    loss_close=cost_formula("F-TAX-LOSS-BALANCE",{"tax.losses_opening":loss,"tax.selected_base_pre_losses":base,"tax.losses_used":used,"tax.losses_expired":Decimal(0),"finance.tax_basis":tax_basis})["value"]
    paid=charge*payment_fraction; payable_close=payable+charge-paid
    bridge=cost_formula("F-TAX-CASH-BRIDGE",{"tax.income_charge":charge,"tax.income_payable_opening":payable,"tax.income_payable_closing":payable_close,"tax.income_prepaid_closing":prepaid,"tax.income_prepaid_opening":prepaid,"finance.tax_basis":tax_basis})["value"]
    return charge,loss_close,paid,payable_close,bridge

def calculate_financial_ledger(exported, methods, settlement, *, catalog=None, scenario_id="BASE"):
    catalog=catalog or Catalog(); methods=methods if isinstance(methods,MethodConfig) else MethodConfig.from_dict(methods); inputs=EnergyInputs(exported,methods,catalog)
    if isinstance(settlement,(str,Path)): settlement=loads(Path(settlement).read_bytes())
    validate_result(settlement,catalog); upstream_hash=_check_upstream(inputs,settlement)
    years=int(_value(inputs,"project.evaluation_years")); currency=_value(inputs,"project.currency"); commissioning=date.fromisoformat(_value(inputs,"schedule.commissioning_date")); periods=_periods(years)
    capex_fraction=_vec(methods,"cash.capex_payment_fractions",len(periods)); opex_fraction=_vec(methods,"cash.opex_payment_fractions",years); collection_fraction=_vec(methods,"cash.collection_fractions",years); tax_fraction=_vec(methods,"cash.tax_payment_fractions",years); vat_fraction=_vec(methods,"cash.vat_payment_fractions",years)
    if _method(methods,"time.horizon_basis")!="OPERATING_YEARS": raise ContractError("BLOCKED_METHOD_REVIEW","time.horizon_basis")
    if _method(methods,"cash.method") not in {"DIRECT_CASH","ACCRUAL_WORKING_CAPITAL"}: raise ContractError("BLOCKED_METHOD_REVIEW","cash.method")
    _method(methods,"tax.method"); timing=_method(methods,"tax.asset_depreciation_timing"); tax_self=_method(methods,"tax.self_use_basis"); day_count=_method(methods,"time.day_count")
    capex=_capex(inputs,currency,commissioning,years); opex=_opex(inputs,years); assets=_assets(inputs,years,commissioning); depreciation=_depreciation(inputs,assets,years,timing); revenues=_annual_revenue(settlement,years); debt=_debt(inputs,methods,capex,periods,years)
    income_rate=ratio(_value(inputs,"tax.corporate_income_rate"),"tax.corporate_income_rate"); vat_rate=ratio(_value(inputs,"tax.vat_output_rate"),"tax.vat_output_rate"); surcharge_rate=ratio(_value(inputs,"tax.surcharge_rate"),"tax.surcharge_rate"); loss_fraction=ratio(_method(methods,"tax.loss_usage_fraction"),"tax.loss_usage_fraction"); refund_fraction=ratio(_method(methods,"tax.vat_refund_fraction"),"tax.vat_refund_fraction")
    project_loss=nonnegative(_method(methods,"tax.opening_project_losses"),"tax.opening_project_losses"); equity_loss=nonnegative(_method(methods,"tax.opening_equity_losses"),"tax.opening_equity_losses"); project_payable=nonnegative(_method(methods,"tax.opening_income_payable"),"tax.opening_income_payable"); equity_payable=project_payable; prepaid=nonnegative(_method(methods,"tax.opening_income_prepaid"),"tax.opening_income_prepaid"); vat_credit=nonnegative(_method(methods,"tax.opening_vat_credit"),"tax.opening_vat_credit"); debt_balance=debt["opening"]; interest_payable=nonnegative(_method(methods,"debt.opening_interest_payable"),"debt.opening_interest_payable"); ar=nonnegative(_method(methods,"cash.opening_receivables"),"cash.opening_receivables"); advances=nonnegative(_method(methods,"cash.opening_advances"),"cash.opening_advances")
    principal_fraction=_vec(methods,"debt.principal_payment_fractions",len(periods)) if debt["has_debt"] else [Decimal(0)]*len(periods)
    interest_fraction=_vec(methods,"debt.interest_payment_fractions",len(periods)) if debt["has_debt"] else [Decimal(0)]*len(periods)
    capitalization_fraction=_vec(methods,"debt.interest_capitalization_fractions",len(periods)) if debt["has_debt"] else [Decimal(0)]*len(periods)
    fee_fraction=_vec(methods,"debt.fee_payment_fractions",len(periods)) if debt["has_debt"] else [Decimal(0)]*len(periods)
    annual=[]; total_depr=sum(depreciation["annual"].values(),Decimal(0)); capex_payable=capex["initial_total"]; capex_paid_to_date=Decimal(0)
    construction_pay=capex["initial_total"]*capex_fraction[0]; capex_payable-=construction_pay
    if construction_pay!=capex["payment_by_year"].get(0,Decimal(0)): raise ContractError("CAPEX_DATE_PAYMENT_MISMATCH","CONSTRUCTION")
    capex_paid_to_date += construction_pay
    construction_residual=ledger_formula("F-CAPEX-PAYMENT-BALANCE",{"capex.scope_cash_payments":{"CONSTRUCTION":construction_pay},"capex.payable_net_closing":capex_payable,"capex.payable_net_opening":Decimal(0),"capex.scope_accrued_amount":capex["initial_total"],"capex.scope_year_ids":["CONSTRUCTION"]})["value"]
    annual.append({"period":"CONSTRUCTION","capex_accrued":capex["initial_total"],"capex_cash_paid":construction_pay,"capex_payable_closing":capex_payable,"capex_payment_residual":construction_residual,"debt_drawdown":debt["rows"]["CONSTRUCTION"]["drawdown"],"working_capital_increase":nonnegative(_value(inputs,"finance.working_capital"),"finance.working_capital"),"phase3e_cashflow":None})
    debt_balance += debt["rows"]["CONSTRUCTION"]["drawdown"]
    for y in range(1,years+1):
        period=f"OPERATING_YEAR_{y}"; rev=revenues[y-1]; taxable_net=rev["benefit_after_transaction_cost"] if tax_self=="TAXABLE_INCREMENTAL_SAVING" else rev["export_sales_revenue"]
        opex_accrual=opex["annual"][y]; opex_cash=opex_accrual*opex_fraction[y-1]; dep=depreciation["annual"][y]; dr=debt["rows"][period]; rate=debt.get("rate",Decimal(0)); replacement_accrued=capex["replacement_accrued_by_year"][y]; replacement_paid=capex["replacement_paid_by_year"][y]; capex_cash=capex["initial_total"]*capex_fraction[y]+replacement_paid
        if capex_cash!=capex["payment_by_year"].get(y,Decimal(0)): raise ContractError("CAPEX_DATE_PAYMENT_MISMATCH",period)
        capex_paid_to_date+=capex_cash; opening_capex_payable=capex_payable; capex_payable+=replacement_accrued-capex_cash
        if capex_payable<0: raise ContractError("CAPEX_PAYMENT_EXCEEDS_ACCRUAL")
        capex_residual=ledger_formula("F-CAPEX-PAYMENT-BALANCE",{"capex.scope_cash_payments":{"CONSTRUCTION":Decimal(0),period:capex_cash},"capex.payable_net_closing":capex_payable,"capex.payable_net_opening":opening_capex_payable,"capex.scope_accrued_amount":replacement_accrued,"capex.scope_year_ids":["CONSTRUCTION",period]})["value"]
        interest=cost_formula("F-DEBT-INTEREST",{"debt.interest_principal_base":{"YEAR":debt_balance+dr["drawdown"]},"debt.annual_interest_rate":{"YEAR":rate},"debt.daycount_year_fraction":{"YEAR":Decimal(1)},"debt.interest_subperiod_ids":["YEAR"]})["value"] if debt["has_debt"] else Decimal(0)
        cap_int=interest*capitalization_fraction[y]; paid_int=interest*interest_fraction[y]; paid_principal=dr["principal_due"]*principal_fraction[y]; fee_paid=dr["fees_due"]*fee_fraction[y]
        if interest_fraction[y]+capitalization_fraction[y]>1: raise ContractError("DEBT_INTEREST_SPLIT_OVERCOMMIT")
        debt_close=cost_formula("F-DEBT-BALANCE",{"debt.opening_balance":debt_balance,"debt.cash_drawdown":dr["drawdown"],"debt.capitalized_unpaid_interest":cap_int,"debt.capitalized_unpaid_fees":Decimal(0),"debt.principal_paid":paid_principal,"debt.documented_writeoff":Decimal(0)})["value"]
        interest_close=cost_formula("F-INTEREST-BALANCE",{"debt.interest_payable_opening":interest_payable,"debt.interest_accrued":interest,"debt.interest_paid":paid_int,"debt.capitalized_unpaid_interest":cap_int})["value"]
        project_base=cost_formula("F-TAXABLE-INCOME-PROJECT",{"revenue.taxable_net":taxable_net,"tax.deductible_opex":opex["net"][y],"depreciation.tax_annual":dep,"tax.other_deductions":Decimal(0),"tax.other_adjustments":Decimal(0)})["value"]
        equity_base=cost_formula("F-TAXABLE-INCOME-EQUITY",{"tax.project_base_pre_losses":project_base,"tax.deductible_interest":interest-cap_int,"tax.deductible_finance_fees":fee_paid})["value"]
        project_charge,project_loss_close,project_paid,project_payable_close,project_bridge=_income_tax_schedule(project_base,project_loss,project_payable,prepaid,income_rate,loss_fraction,tax_fraction[y-1],"PROJECT")
        equity_charge,equity_loss_close,equity_paid,equity_payable_close,equity_bridge=_income_tax_schedule(equity_base,equity_loss,equity_payable,prepaid,income_rate,loss_fraction,tax_fraction[y-1],"EQUITY")
        tax_charge=equity_charge if debt["has_debt"] else project_charge; tax_paid=equity_paid if debt["has_debt"] else project_paid; payable_close=equity_payable_close if debt["has_debt"] else project_payable_close; loss_close=equity_loss_close if debt["has_debt"] else project_loss_close; tax_bridge=equity_bridge if debt["has_debt"] else project_bridge
        export=rev["export_sales_revenue"]; vat_output=(export*vat_rate if _method(methods,"settlement.tax_basis")=="exclusive" else export-export/(1+vat_rate)) if vat_rate else Decimal(0); vat_input=(capex["recoverable_vat"] if y==1 else Decimal(0))+capex["replacement_vat_by_year"][y]+opex["recoverable_vat"][y]; vat_due=max(Decimal(0),vat_output-vat_credit-vat_input); vat_paid=vat_due*vat_fraction[y-1]; vat_refund=max(Decimal(0),vat_credit+vat_input-vat_output)*refund_fraction; vat_close=cost_formula("F-VAT-CREDIT-BALANCE",{"tax.vat_credit_opening":vat_credit,"tax.vat_input_eligible":vat_input,"tax.vat_output":vat_output,"tax.vat_cash_paid":vat_paid,"tax.vat_cash_refund":vat_refund})["value"]
        if vat_close<0 and vat_close>-Decimal("1e-18"): vat_close=Decimal(0)
        if vat_close<0: raise ContractError("VAT_PAYABLE_REQUIRES_EXPLICIT_LEDGER")
        other=cost_formula("F-OTHER-CASH-TAXES",{"tax.other_items_cash":{"surcharge":tax_charge*surcharge_rate},"tax.other_item_ids":["surcharge"],"finance.tax_basis":"EQUITY" if debt["has_debt"] else "PROJECT"})["value"]
        project_other=cost_formula("F-OTHER-CASH-TAXES",{"tax.other_items_cash":{"surcharge":project_charge*surcharge_rate},"tax.other_item_ids":["surcharge"],"finance.tax_basis":"PROJECT"})["value"]
        cash_tax=cost_formula("F-CASH-TAX-TOTAL",{"tax.income_cash_paid":tax_paid,"tax.other_cash_total":other,"tax.vat_cash_paid":vat_paid,"tax.vat_cash_refund":vat_refund,"tax.vat_cash_basis_adjustment":Decimal(0),"finance.tax_basis":"EQUITY" if debt["has_debt"] else "PROJECT"})["value"]
        project_cash_tax=cost_formula("F-CASH-TAX-TOTAL",{"tax.income_cash_paid":project_paid,"tax.other_cash_total":project_other,"tax.vat_cash_paid":vat_paid,"tax.vat_cash_refund":vat_refund,"tax.vat_cash_basis_adjustment":Decimal(0),"finance.tax_basis":"PROJECT"})["value"]
        self_treatment=_method(methods,"cash.self_use_treatment")
        invoice=export+(rev["self_value"] if self_treatment=="CONTRACT_PPA" else Decimal(0))
        avoided=rev["self_value"] if self_treatment=="INCREMENTAL_AVOIDED_EXPENDITURE" else Decimal(0)
        ar_opening=ar; current_collection=invoice*collection_fraction[y-1]
        terminal_collection=(ar_opening+invoice-current_collection)*ratio(_method(methods,"cash.terminal_collection_fraction"),"cash.terminal_collection_fraction") if y==years else Decimal(0)
        ar=ar_opening+invoice-current_collection-terminal_collection
        if ar<0: raise ContractError("NEGATIVE_ACCOUNTS_RECEIVABLE",period)
        receipt=ledger_formula("F-CASH-RECEIPTS",{"revenue.invoiced_gross":invoice,"revenue.other_cash":Decimal(0),"working_capital.receivables_change":ar-ar_opening,"working_capital.advances_change":Decimal(0)})["value"]
        if abs(receipt-current_collection-terminal_collection)>nonnegative(_method(methods,"precision.abs_tolerance"),"precision.abs_tolerance"): raise ContractError("RECEIVABLE_CASH_BRIDGE_MISMATCH",period)
        service=ledger_formula("F-DEBT-SERVICE",{"debt.principal_due":dr["principal_due"],"debt.interest_due":interest,"debt.service_fees_due":dr["fees_due"]})["value"]
        row={"period":period,"revenue_after_transaction_cost":rev["benefit_after_transaction_cost"],"invoiced_gross":invoice,"self_use_avoided_expenditure":avoided,"revenue_cash_receipts":receipt,"receivables_opening":ar_opening,"receivables_terminal_collection":terminal_collection,"accounts_receivable_closing":ar,"opex_accrued":opex_accrual,"opex_cash_paid":opex_cash,"depreciation":dep,"asset_book_value_closing":depreciation["book"][y],"capex_accrued":replacement_accrued,"replacement_capex_accrued":replacement_accrued,"replacement_cash_paid":replacement_paid,"capex_cash_paid":capex_cash,"capex_payable_opening":opening_capex_payable,"capex_payable_closing":capex_payable,"capex_payment_residual":capex_residual,"principal_due":dr["principal_due"],"principal_paid":paid_principal,"interest_accrued":interest,"interest_paid":paid_int,"interest_capitalized":cap_int,"interest_payable_closing":interest_close,"debt_service_due":service,"debt_balance_closing":debt_close,"taxable_income_project":project_base,"taxable_income_equity":equity_base,"tax_loss_closing":loss_close,"tax_loss_project_closing":project_loss_close,"tax_loss_equity_closing":equity_loss_close,"income_tax_accrual":tax_charge,"income_tax_accrual_project":project_charge,"income_tax_accrual_equity":equity_charge,"income_tax_cash_paid":tax_paid,"income_tax_cash_paid_project":project_paid,"income_tax_cash_paid_equity":equity_paid,"income_tax_payable_closing":payable_close,"income_tax_payable_project_closing":project_payable_close,"income_tax_payable_equity_closing":equity_payable_close,"tax_cash_bridge":tax_bridge,"tax_cash_bridge_project":project_bridge,"tax_cash_bridge_equity":equity_bridge,"vat_output":vat_output,"vat_input_eligible":vat_input,"vat_credit_closing":vat_close,"other_cash_taxes":other,"other_cash_taxes_project":project_other,"cash_tax_total":cash_tax,"cash_tax_total_project":project_cash_tax,"cash_tax_total_equity":cash_tax if debt["has_debt"] else project_cash_tax,"working_capital_increase":Decimal(0),"working_capital_release":nonnegative(_value(inputs,"finance.working_capital"),"finance.working_capital") if y==years else Decimal(0),"phase3e_cashflow":None}
        annual.append(row); debt_balance=debt_close; interest_payable=interest_close; project_loss=project_loss_close; equity_loss=equity_loss_close; project_payable=project_payable_close; equity_payable=equity_payable_close; vat_credit=vat_close
    if capex_payable != 0:
        raise ContractError("CAPEX_PAYMENT_BALANCE_NOT_CLOSED")
    identity=calculation_identity(inputs.validated,methods,catalog); snapshot=identity["source_snapshot"]; snapshot["phase3c_settlement"]={"result_hash":upstream_hash,"project_id":inputs.validated.project.project_id}; source_id=digest(snapshot); payload=identity["input_identity_payload"]; payload["source_snapshot_id"]=source_id; payload["upstream_settlement_result_hash"]=upstream_hash; input_hash=digest(payload)
    result=deepcopy(settlement); result.update({"schema_version":RESULT_SCHEMA_VERSION,"model_version":MODEL_VERSION,"run_id":str(uuid4()),"created_at":datetime.now(timezone.utc).isoformat(),"input_hash":input_hash,"source_snapshot_id":source_id,"source_snapshot":snapshot,"status":"CALCULATED_SYNTHETIC" if methods.data_mode=="SYNTHETIC" else "CALCULATED_CONDITIONAL","inputs":{**result["inputs"],"identity_payload":payload,"normalized":inputs.validated.export["normalized_inputs"],"method_config_hash":methods.hash,"used_fields":sorted(set(result["inputs"].get("used_fields",[]))|set(inputs.used)),"upstream_settlement_result_hash":upstream_hash},"boundaries":{**result["boundaries"],"FINANCIAL_LEDGER":{"phase":"3D","cashflow_assembly":"PHASE3E_NOT_IMPLEMENTED","currency":currency}},"formula_snapshot":{**result["formula_snapshot"],"financial_definitions":{fid:catalog.formulas[fid] for fid in FORMULA_IDS}},"evidence":{**result["evidence"],"financial-ledger":_jsonable({"periods":periods,"annual":annual,"capex":capex,"opex":opex,"depreciation":depreciation,"upstream_settlement_result_hash":upstream_hash,"lifecycle":{"capex_total":capex["total"],"opex_cash":sum((x.get("opex_cash_paid",Decimal(0)) for x in annual),Decimal(0)),"depreciation":total_depr,"ending_debt":debt_balance}}),"deferred-financial-domains":{"project_cash_flow":"PHASE3E_NOT_IMPLEMENTED","equity_cash_flow":"PHASE3E_NOT_IMPLEMENTED","NPV":"PHASE3E_NOT_IMPLEMENTED","IRR":"PHASE3E_NOT_IMPLEMENTED","LCOE":"PHASE3E_NOT_IMPLEMENTED"}}})
    result["results"]["metrics"]=[m for m in result["results"]["metrics"] if not m["metric_id"].startswith("financial.")]
    for row in annual: _metric(result,catalog,"financial.ledger."+row["period"],row.get("cash_tax_total",row.get("capex_cash_paid",Decimal(0))),currency,"F-CASH-TAX-TOTAL" if row["period"]!="CONSTRUCTION" else "F-CAPEX-TOTAL","FINANCIAL_LEDGER",row["period"],details=row)
    _metric(result,catalog,"financial.capex.total",capex["total"],currency,"F-CAPEX-TOTAL","FINANCIAL_LEDGER","LIFECYCLE",details={"items":capex["amounts"],"net_total":capex["net_total"]})
    _metric(result,catalog,"financial.unit_investment",cost_formula("F-UNIT-INVESTMENT",{"capex.total":capex["total"],"capacity.dc_kwp":_capacity(inputs)})["value"],currency,"F-UNIT-INVESTMENT","FINANCIAL_LEDGER","LIFECYCLE")
    _metric(result,catalog,"financial.opex.cash_lifecycle",sum((x.get("opex_cash_paid",Decimal(0)) for x in annual),Decimal(0)),currency,"F-ANNUAL-OPEX","FINANCIAL_LEDGER","LIFECYCLE")
    _metric(result,catalog,"financial.debt.ending_balance",debt_balance,currency,"F-DEBT-BALANCE","FINANCIAL_LEDGER","LIFECYCLE")
    _metric(result,catalog,"financial.tax.cash_lifecycle",sum((x.get("cash_tax_total",Decimal(0)) for x in annual),Decimal(0)),currency,"F-CASH-TAX-TOTAL","FINANCIAL_LEDGER","LIFECYCLE")
    _metric(result,catalog,"financial.asset.ending_book_value",depreciation["book"][years],currency,"F-ASSET-BOOK-VALUE","FINANCIAL_LEDGER","LIFECYCLE")
    result["findings"]=[f for f in result.get("findings",[]) if f.get("code")!="FINANCE_TAX_CASHFLOW_AND_FINANCIAL_RETURNS_NOT_IMPLEMENTED"]; result["findings"].append({"code":"PHASE3E_CASHFLOW_AND_FINANCIAL_RETURNS_NOT_IMPLEMENTED","status":"NOT_IMPLEMENTED"})
    result["maturity"]["calculation"]="CALCULATED_SYNTHETIC" if methods.data_mode=="SYNTHETIC" else "CALCULATED_CONDITIONAL"
    result["results"]["domains"]["financial_ledger"]=[m["metric_id"] for m in result["results"]["metrics"] if m["metric_id"].startswith("financial.")]
    return seal_result(result)

def write_financial_bundle(result, output_dir):
    target=local_target(output_dir)
    target.mkdir()
    (target/"result.json").write_text(dumps(result),encoding="utf-8")
    (target/"result.sha256").write_text(result["result_hash"]+"\n",encoding="utf-8")
    return target
