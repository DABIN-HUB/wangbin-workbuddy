"""Pure, boundary-scoped multiplicative loss ledgers."""
from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from ..errors import ContractError
from .common import calculated, number, precision_context


LOSS_KINDS = (
    "shading",
    "soiling",
    "snow",
    "temperature",
    "mismatch",
    "dc_cable",
    "inverter",
    "clipping",
    "availability",
    "ac_cable",
    "transformer",
    "export_line",
    "curtailment",
)
BOUNDARIES = ("DC", "AC", "GRID")
_KIND_ORDER = {kind: index for index, kind in enumerate(LOSS_KINDS)}


def _field(record: Mapping, *names, default=None):
    for name in names:
        if name in record:
            return record[name]
    return default


def _source_ids(record: Mapping, loss_id: str) -> tuple[str, ...]:
    raw = _field(record, "source_ids", "source")
    if isinstance(raw, str):
        raw = (raw,)
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ContractError("LOSS_SOURCE_REQUIRED", loss_id)
    result = []
    for source_id in raw:
        if not isinstance(source_id, str) or not source_id:
            raise ContractError("LOSS_SOURCE_REQUIRED", loss_id)
        result.append(source_id)
    if len(set(result)) != len(result):
        raise ContractError("LOSS_SOURCE_DUPLICATE", loss_id)
    return tuple(result)


def _normalise_loss(record, index: int) -> dict:
    if not isinstance(record, Mapping):
        raise ContractError("LOSS_RECORD_SHAPE", str(index))
    loss_id = _field(record, "id", "loss_id", "row_id")
    if not isinstance(loss_id, str) or not loss_id:
        raise ContractError("LOSS_ID_REQUIRED", str(index))
    kind = record.get("kind")
    if kind not in _KIND_ORDER:
        raise ContractError("LOSS_KIND_UNSUPPORTED", loss_id)
    boundary = record.get("boundary")
    if not isinstance(boundary, str) or not boundary:
        raise ContractError("LOSS_BOUNDARY_REQUIRED", loss_id)
    rate = number(record.get("rate"), f"losses[{loss_id}].rate")
    if rate < 0 or rate > 1:
        raise ContractError("LOSS_RATE_DOMAIN", loss_id)
    sequence = record.get("sequence")
    if sequence is not None and (type(sequence) is not int or sequence < 0):
        raise ContractError("LOSS_SEQUENCE_DOMAIN", loss_id)
    included = record.get("included_in_source", False)
    if type(included) is not bool:
        raise ContractError("LOSS_INCLUDED_FLAG", loss_id)
    source_ids = _source_ids(record, loss_id)
    return {
        "loss_id": loss_id,
        "kind": kind,
        "boundary": boundary,
        "rate": rate,
        "sequence": sequence,
        "included_in_source": included,
        "source_ids": source_ids,
    }


def loss_ledger(energy, losses, *, boundary, upstream_included=(), digits=80) -> dict:
    """Apply independent losses at one explicit DC/AC/GRID boundary.

    The original stable row ID, frozen ``kind`` enum and optional source
    sequence are retained in every ledger item.  Records are ordered by the
    supplied physical sequence, then the frozen kind order, then stable ID;
    the boundary argument is never inferred from an untrusted record.
    """
    if boundary not in BOUNDARIES:
        raise ContractError("LOSS_BOUNDARY_UNSUPPORTED", "boundary")
    if not isinstance(losses, (list, tuple)):
        raise ContractError("LOSS_LIST_REQUIRED", "losses")
    if not isinstance(upstream_included, (list, tuple, set, frozenset)):
        raise ContractError("LOSS_UPSTREAM_SET_REQUIRED", "upstream_included")
    upstream = tuple(upstream_included)
    if any(not isinstance(item, str) or not item for item in upstream):
        raise ContractError("LOSS_UPSTREAM_ID_REQUIRED", "upstream_included")
    if len(set(upstream)) != len(upstream):
        raise ContractError("LOSS_UPSTREAM_DUPLICATE", "upstream_included")
    initial = number(energy, "energy")
    if initial < 0:
        raise ContractError("NEGATIVE_INPUT", "energy")

    records = [_normalise_loss(record, index) for index, record in enumerate(losses)]
    seen = set()
    for record in records:
        loss_id = record["loss_id"]
        if loss_id in seen:
            raise ContractError("LOSS_DUPLICATE_ID", loss_id)
        seen.add(loss_id)
        if record["boundary"] != boundary:
            raise ContractError("LOSS_BOUNDARY_MISMATCH", loss_id)
        if record["included_in_source"]:
            raise ContractError("LOSS_ALREADY_INCLUDED", loss_id)
        if loss_id in upstream:
            raise ContractError("LOSS_ALREADY_INCLUDED", loss_id)

    ordered = sorted(
        records,
        key=lambda row: (
            row["sequence"] is None,
            row["sequence"] if row["sequence"] is not None else 0,
            _KIND_ORDER[row["kind"]],
            row["loss_id"],
        ),
    )
    with precision_context(digits):
        before = initial
        items = []
        for record in ordered:
            after = before * (Decimal(1) - record["rate"])
            lost = before - after
            items.append({
                "loss_id": record["loss_id"],
                "kind": record["kind"],
                "boundary": record["boundary"],
                "sequence": record["sequence"],
                "rate": record["rate"],
                "source_ids": list(record["source_ids"]),
                "included_in_source": record["included_in_source"],
                "before": before,
                "lost": lost,
                "after": after,
            })
            before = after
        total_lost = sum((item["lost"] for item in items), Decimal(0))
        residual = initial - (total_lost + before)
        if residual != 0:
            raise ContractError("LOSS_CONSERVATION", boundary)
        return calculated(
            before,
            details={
                "boundary": boundary,
                "items": items,
                "total_lost": total_lost,
                "conservation": {
                    "initial": initial,
                    "after": before,
                    "residual": residual,
                },
            },
        )
