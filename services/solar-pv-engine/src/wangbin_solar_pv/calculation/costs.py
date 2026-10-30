"""Frozen Phase 3D cost, asset and tax formula kernels."""
from __future__ import annotations
from decimal import Decimal
from ..errors import ContractError
from .common import calculated, integer, nonnegative, nonvalue, number, precision_context, ratio

FORMULA_IDS = (
    "F-TAX-EXCLUSIVE-AMOUNT", "F-CAPEX-ITEM-AMOUNT", "F-CAPEX-TOTAL", "F-UNIT-INVESTMENT",
    "F-ANNUAL-OPEX", "F-OPEX-ESCALATION", "F-STRAIGHT-LINE-DEPRECIATION", "F-ASSET-BOOK-VALUE",
    "F-TAXABLE-INCOME-PROJECT", "F-TAXABLE-INCOME-EQUITY", "F-INCOME-TAX-ACCRUAL",
    "F-TAX-LOSS-BALANCE", "F-TAX-CASH-BRIDGE", "F-VAT-CREDIT-BALANCE", "F-OTHER-CASH-TAXES",
    "F-CASH-TAX-TOTAL", "F-DEBT-BALANCE", "F-DEBT-INTEREST", "F-INTEREST-BALANCE",
)
_REQUIRED = {
 "F-TAX-EXCLUSIVE-AMOUNT":("tax.inclusive_amount","tax.vat_rate"),
 "F-CAPEX-ITEM-AMOUNT":("capex.items.quantity","capex.items.unit_price"),
 "F-CAPEX-TOTAL":("capex.items.amount","capex.item_ids"),
 "F-UNIT-INVESTMENT":("capex.total","capacity.dc_kwp"),
 "F-ANNUAL-OPEX":("opex.items.cash_amount","opex.item_ids"),
 "F-OPEX-ESCALATION":("opex.items.base_amount","opex.items.escalation_rates","time.escalation_year"),
 "F-STRAIGHT-LINE-DEPRECIATION":("depreciation.asset_basis","depreciation.asset_residual","depreciation.asset_life_years"),
 "F-ASSET-BOOK-VALUE":("assets.opening_book_value","assets.capitalized_additions","depreciation.asset_annual","assets.disposal_book_value"),
 "F-TAXABLE-INCOME-PROJECT":("revenue.taxable_net","tax.deductible_opex","depreciation.tax_annual","tax.other_deductions","tax.other_adjustments"),
 "F-TAXABLE-INCOME-EQUITY":("tax.project_base_pre_losses","tax.deductible_interest","tax.deductible_finance_fees"),
 "F-INCOME-TAX-ACCRUAL":("tax.income_rate","tax.selected_base_pre_losses","tax.losses_used","finance.tax_basis"),
 "F-TAX-LOSS-BALANCE":("tax.losses_opening","tax.selected_base_pre_losses","tax.losses_used","tax.losses_expired","finance.tax_basis"),
 "F-TAX-CASH-BRIDGE":("tax.income_charge","tax.income_payable_opening","tax.income_payable_closing","tax.income_prepaid_closing","tax.income_prepaid_opening","finance.tax_basis"),
 "F-VAT-CREDIT-BALANCE":("tax.vat_credit_opening","tax.vat_input_eligible","tax.vat_output","tax.vat_cash_paid","tax.vat_cash_refund"),
 "F-OTHER-CASH-TAXES":("tax.other_items_cash","tax.other_item_ids","finance.tax_basis"),
 "F-CASH-TAX-TOTAL":("tax.income_cash_paid","tax.other_cash_total","tax.vat_cash_paid","tax.vat_cash_refund","tax.vat_cash_basis_adjustment","finance.tax_basis"),
 "F-DEBT-BALANCE":("debt.opening_balance","debt.cash_drawdown","debt.capitalized_unpaid_interest","debt.capitalized_unpaid_fees","debt.principal_paid","debt.documented_writeoff"),
 "F-DEBT-INTEREST":("debt.interest_principal_base","debt.annual_interest_rate","debt.daycount_year_fraction","debt.interest_subperiod_ids"),
 "F-INTEREST-BALANCE":("debt.interest_payable_opening","debt.interest_accrued","debt.interest_paid","debt.capitalized_unpaid_interest"),
}

def _ids(value, field):
    if not isinstance(value,(list,tuple)) or len(set(value)) != len(value) or any(type(x) is not str or not x for x in value): raise ContractError("INDEX_IDS_SEQUENCE_REQUIRED",field)
    return tuple(value)
def _values(mapping, ids, field):
    ids=_ids(ids,field)
    if not isinstance(mapping,dict): raise ContractError("INDEXED_VALUES_MAPPING_REQUIRED",field)
    if set(mapping)!=set(ids):
        missing=sorted(set(ids)-set(mapping))
        if missing: return None,missing
        raise ContractError("INDEXED_VALUES_KEYS",field)
    return [mapping[x] for x in ids],None
def _sum(mapping,ids,field):
    values,missing=_values(mapping,ids,field)
    if missing: return nonvalue("BLOCKED_MISSING_INPUT","BLOCKED_MISSING_INPUT",details={"missing_field_ids":[field+"."+x for x in missing]})
    return sum((nonnegative(v,field) for v in values),Decimal(0))
def _dispatch(fid,v):
    if fid=="F-TAX-EXCLUSIVE-AMOUNT":
        return nonnegative(v["tax.inclusive_amount"],"tax.inclusive_amount")/(1+ratio(v["tax.vat_rate"],"tax.vat_rate"))
    if fid=="F-CAPEX-ITEM-AMOUNT": return nonnegative(v["capex.items.quantity"],"capex.items.quantity")*nonnegative(v["capex.items.unit_price"],"capex.items.unit_price")
    if fid=="F-CAPEX-TOTAL": return _sum(v["capex.items.amount"],v["capex.item_ids"],"capex.items.amount")
    if fid=="F-UNIT-INVESTMENT":
        capex=nonnegative(v["capex.total"],"capex.total"); capacity=nonnegative(v["capacity.dc_kwp"],"capacity.dc_kwp")
        return nonvalue("UNDEFINED","ZERO_DC_CAPACITY") if capacity==0 else capex/capacity
    if fid=="F-ANNUAL-OPEX": return _sum(v["opex.items.cash_amount"],v["opex.item_ids"],"opex.items.cash_amount")
    if fid=="F-OPEX-ESCALATION":
        result=nonnegative(v["opex.items.base_amount"],"opex.items.base_amount"); rates=v["opex.items.escalation_rates"]; year=integer(v["time.escalation_year"],"time.escalation_year",minimum=1,maximum=100)
        if not isinstance(rates,(list,tuple)) or len(rates)!=year: raise ContractError("ESCALATION_RATE_PERIOD_MISMATCH")
        for rate in rates:
            rate=number(rate,"opex.items.escalation_rates")
            if rate<=-1: raise ContractError("ESCALATION_RATE_DOMAIN")
            result*=1+rate
        return result
    if fid=="F-STRAIGHT-LINE-DEPRECIATION":
        basis=nonnegative(v["depreciation.asset_basis"],"depreciation.asset_basis"); residual=nonnegative(v["depreciation.asset_residual"],"depreciation.asset_residual"); life=integer(v["depreciation.asset_life_years"],"depreciation.asset_life_years",minimum=1,maximum=100)
        if residual>basis: raise ContractError("DEPRECIATION_RESIDUAL_EXCEEDS_BASIS")
        return (basis-residual)/life
    if fid=="F-ASSET-BOOK-VALUE":
        result=nonnegative(v["assets.opening_book_value"],"assets.opening_book_value")+nonnegative(v["assets.capitalized_additions"],"assets.capitalized_additions")-nonnegative(v["depreciation.asset_annual"],"depreciation.asset_annual")-nonnegative(v["assets.disposal_book_value"],"assets.disposal_book_value")
        if result<0: raise ContractError("ASSET_BOOK_VALUE_NEGATIVE")
        return result
    if fid=="F-TAXABLE-INCOME-PROJECT": return number(v["revenue.taxable_net"],"revenue.taxable_net")-nonnegative(v["tax.deductible_opex"],"tax.deductible_opex")-nonnegative(v["depreciation.tax_annual"],"depreciation.tax_annual")-number(v["tax.other_deductions"],"tax.other_deductions")+number(v["tax.other_adjustments"],"tax.other_adjustments")
    if fid=="F-TAXABLE-INCOME-EQUITY": return number(v["tax.project_base_pre_losses"],"tax.project_base_pre_losses")-nonnegative(v["tax.deductible_interest"],"tax.deductible_interest")-nonnegative(v["tax.deductible_finance_fees"],"tax.deductible_finance_fees")
    if fid=="F-INCOME-TAX-ACCRUAL": return ratio(v["tax.income_rate"],"tax.income_rate")*max(Decimal(0),number(v["tax.selected_base_pre_losses"],"tax.selected_base_pre_losses")-nonnegative(v["tax.losses_used"],"tax.losses_used"))
    if fid=="F-TAX-LOSS-BALANCE":
        result=nonnegative(v["tax.losses_opening"],"tax.losses_opening")+max(-number(v["tax.selected_base_pre_losses"],"tax.selected_base_pre_losses"),Decimal(0))-nonnegative(v["tax.losses_used"],"tax.losses_used")-nonnegative(v["tax.losses_expired"],"tax.losses_expired")
        if result<0: raise ContractError("TAX_LOSS_BALANCE_NEGATIVE")
        return result
    if fid=="F-TAX-CASH-BRIDGE": return number(v["tax.income_charge"],"tax.income_charge")+number(v["tax.income_payable_opening"],"tax.income_payable_opening")-number(v["tax.income_payable_closing"],"tax.income_payable_closing")+number(v["tax.income_prepaid_closing"],"tax.income_prepaid_closing")-number(v["tax.income_prepaid_opening"],"tax.income_prepaid_opening")
    if fid=="F-VAT-CREDIT-BALANCE": return nonnegative(v["tax.vat_credit_opening"],"tax.vat_credit_opening")+nonnegative(v["tax.vat_input_eligible"],"tax.vat_input_eligible")-nonnegative(v["tax.vat_output"],"tax.vat_output")+nonnegative(v["tax.vat_cash_paid"],"tax.vat_cash_paid")-nonnegative(v["tax.vat_cash_refund"],"tax.vat_cash_refund")
    if fid=="F-OTHER-CASH-TAXES": return _sum(v["tax.other_items_cash"],v["tax.other_item_ids"],"tax.other_items_cash")
    if fid=="F-CASH-TAX-TOTAL": return number(v["tax.income_cash_paid"],"tax.income_cash_paid")+number(v["tax.other_cash_total"],"tax.other_cash_total")+number(v["tax.vat_cash_paid"],"tax.vat_cash_paid")-number(v["tax.vat_cash_refund"],"tax.vat_cash_refund")+number(v["tax.vat_cash_basis_adjustment"],"tax.vat_cash_basis_adjustment")
    if fid=="F-DEBT-BALANCE":
        result=nonnegative(v["debt.opening_balance"],"debt.opening_balance")+nonnegative(v["debt.cash_drawdown"],"debt.cash_drawdown")+nonnegative(v["debt.capitalized_unpaid_interest"],"debt.capitalized_unpaid_interest")+nonnegative(v["debt.capitalized_unpaid_fees"],"debt.capitalized_unpaid_fees")-nonnegative(v["debt.principal_paid"],"debt.principal_paid")-nonnegative(v["debt.documented_writeoff"],"debt.documented_writeoff")
        if result<0: raise ContractError("DEBT_BALANCE_NEGATIVE")
        return result
    if fid=="F-DEBT-INTEREST":
        ids=_ids(v["debt.interest_subperiod_ids"],"debt.interest_subperiod_ids"); b,_=_values(v["debt.interest_principal_base"],ids,"debt.interest_principal_base"); i,_=_values(v["debt.annual_interest_rate"],ids,"debt.annual_interest_rate"); d,_=_values(v["debt.daycount_year_fraction"],ids,"debt.daycount_year_fraction")
        return sum((nonnegative(x,"debt.interest_principal_base")*nonnegative(y,"debt.annual_interest_rate")*nonnegative(z,"debt.daycount_year_fraction") for x,y,z in zip(b,i,d)),Decimal(0))
    if fid=="F-INTEREST-BALANCE":
        result=nonnegative(v["debt.interest_payable_opening"],"debt.interest_payable_opening")+nonnegative(v["debt.interest_accrued"],"debt.interest_accrued")-nonnegative(v["debt.interest_paid"],"debt.interest_paid")-nonnegative(v["debt.capitalized_unpaid_interest"],"debt.capitalized_unpaid_interest")
        if result<0: raise ContractError("INTEREST_PAYABLE_NEGATIVE")
        return result
    raise ContractError("UNKNOWN_FORMULA",fid)
def evaluate(formula_id,values,options=None):
    if formula_id not in FORMULA_IDS: raise ContractError("UNKNOWN_FORMULA",formula_id)
    if not isinstance(values,dict): raise ContractError("FORMULA_VALUES_MAPPING_REQUIRED",formula_id)
    required=set(_REQUIRED[formula_id]); actual=set(values)
    if actual!=required:
        if required-actual: return nonvalue("BLOCKED_MISSING_INPUT","BLOCKED_MISSING_INPUT",details={"formula_id":formula_id,"missing_field_ids":sorted(required-actual)})
        raise ContractError("FORMULA_VALUES_KEYS",formula_id)
    options={} if options is None else options; digits=options.get("precision_digits",80)
    integer(digits,"precision.precision_digits",minimum=34,maximum=1024)
    with precision_context(digits): value=_dispatch(formula_id,values)
    return value if isinstance(value,dict) and "status" in value else calculated(value,details={"formula_id":formula_id,"precision_digits":digits})
