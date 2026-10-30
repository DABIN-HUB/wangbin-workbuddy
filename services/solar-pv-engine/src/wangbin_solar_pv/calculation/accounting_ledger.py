"""Phase 3D accounting-ledger relations that are not Phase 3E return metrics."""
from __future__ import annotations
from decimal import Decimal
from ..errors import ContractError
from .common import calculated, integer, nonnegative, nonvalue, number, precision_context

FORMULA_IDS = ("F-CASH-RECEIPTS", "F-DEBT-SERVICE", "F-CAPEX-PAYMENT-BALANCE")
_REQUIRED = {
 "F-CASH-RECEIPTS": ("revenue.invoiced_gross","revenue.other_cash","working_capital.receivables_change","working_capital.advances_change"),
 "F-DEBT-SERVICE": ("debt.principal_due","debt.interest_due","debt.service_fees_due"),
 "F-CAPEX-PAYMENT-BALANCE": ("capex.scope_cash_payments","capex.payable_net_closing","capex.payable_net_opening","capex.scope_accrued_amount","capex.scope_year_ids"),
}
def _ids(value,field):
 if not isinstance(value,(list,tuple)) or len(set(value))!=len(value) or any(type(x) is not str or not x for x in value): raise ContractError("INDEX_IDS_SEQUENCE_REQUIRED",field)
 return tuple(value)
def _map(mapping,ids,field):
 ids=_ids(ids,field)
 if not isinstance(mapping,dict) or set(mapping)!=set(ids):
  if isinstance(mapping,dict) and set(ids)-set(mapping): return None,sorted(set(ids)-set(mapping))
  raise ContractError("INDEXED_VALUES_KEYS",field)
 return [mapping[x] for x in ids],None
def _dispatch(fid,v):
 if fid=="F-CASH-RECEIPTS": return number(v["revenue.invoiced_gross"],"revenue.invoiced_gross")+number(v["revenue.other_cash"],"revenue.other_cash")-number(v["working_capital.receivables_change"],"working_capital.receivables_change")+number(v["working_capital.advances_change"],"working_capital.advances_change")
 if fid=="F-DEBT-SERVICE": return nonnegative(v["debt.principal_due"],"debt.principal_due")+nonnegative(v["debt.interest_due"],"debt.interest_due")+nonnegative(v["debt.service_fees_due"],"debt.service_fees_due")
 payments,missing=_map(v["capex.scope_cash_payments"],v["capex.scope_year_ids"],"capex.scope_cash_payments")
 if missing: return nonvalue("BLOCKED_MISSING_INPUT","BLOCKED_MISSING_INPUT",details={"missing_field_ids":["capex.scope_cash_payments."+x for x in missing]})
 return sum((nonnegative(x,"capex.scope_cash_payments") for x in payments),Decimal(0))+number(v["capex.payable_net_closing"],"capex.payable_net_closing")-number(v["capex.payable_net_opening"],"capex.payable_net_opening")-nonnegative(v["capex.scope_accrued_amount"],"capex.scope_accrued_amount")
def evaluate(formula_id,values,options=None):
 if formula_id not in FORMULA_IDS: raise ContractError("UNKNOWN_FORMULA",formula_id)
 if not isinstance(values,dict): raise ContractError("FORMULA_VALUES_MAPPING_REQUIRED",formula_id)
 required=set(_REQUIRED[formula_id]); actual=set(values)
 if actual!=required:
  if required-actual: return nonvalue("BLOCKED_MISSING_INPUT","BLOCKED_MISSING_INPUT",details={"formula_id":formula_id,"missing_field_ids":sorted(required-actual)})
  raise ContractError("FORMULA_VALUES_KEYS",formula_id)
 options={} if options is None else options; digits=options.get("precision_digits",80); integer(digits,"precision.precision_digits",minimum=34,maximum=1024)
 with precision_context(digits): value=_dispatch(formula_id,values)
 return value if isinstance(value,dict) and "status" in value else calculated(value,details={"formula_id":formula_id,"precision_digits":digits})
