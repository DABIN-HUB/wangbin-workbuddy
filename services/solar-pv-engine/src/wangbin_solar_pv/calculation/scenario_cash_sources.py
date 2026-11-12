"""Narrow source-policy reuse for synthetic OPEX-only scenarios, not cash reuse."""
from copy import deepcopy
from hashlib import sha256

from ..errors import ContractError
from ..serialization import dumps
from .trading_fee_payment import validate_trading_fee_payment


def rebind_opex_fee(raw, original, candidate, methods, original_settlement, settlement, scenario_id):
    """Preserve the validated payment rule; bind it to newly computed settlement.

    No other input, payment fraction, period, currency, asset or method change
    is authorized by this adapter. The original bytes remain audit evidence.
    """
    checked = validate_trading_fee_payment(raw, exported=original, methods=methods,
                                          settlement=original_settlement)
    before = deepcopy(original["normalized_inputs"])
    after = deepcopy(candidate["normalized_inputs"])
    for values in (before, after):
        for row in values.get("opex.items", []):
            if row["fields"].get("opex.items.category") in {"maintenance", "cleaning", "operations"}:
                row["fields"].pop("opex.items.base_amount", None)
    if (before != after or original["project"]["project_id"] != candidate["project"]["project_id"]
            or original["project"]["pv_type"] != candidate["project"]["pv_type"]):
        raise ContractError("SCENARIO_CASH_SOURCE_SCOPE_CHANGED")
    contract = deepcopy(checked.contract)
    contract["binding"].update(
        scenario_id=scenario_id, phase2_input_hash=candidate["input_hash"],
        phase2_source_snapshot_id=candidate["source_snapshot_id"],
        d3_content_hash=settlement["source_snapshot"]["datasets"]["content_hash"],
        phase3c_result_hash=settlement["result_hash"])
    rebound = dumps(contract).encode("utf-8")
    validate_trading_fee_payment(rebound, exported=candidate, methods=methods,
                                settlement=settlement, scenario_id=scenario_id)
    return rebound, {"policy": "SYNTHETIC_OPEX_ONLY_RULE_REUSE_NOT_CASH_REUSE",
                     "original_raw_sha256": checked.source_sha256,
                     "derived_raw_sha256": sha256(rebound).hexdigest(),
                     "original_binding": checked.contract["binding"],
                     "candidate_binding": contract["binding"]}
