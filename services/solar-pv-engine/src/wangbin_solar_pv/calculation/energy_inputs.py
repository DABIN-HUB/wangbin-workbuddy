"""Calculation-side evidence selection; only revalidated Phase 2 exports enter.

This adapter does not change raw input/source identities or turn an unreviewed
record into verified site data. Missing and expired evidence is never zero.
"""
from __future__ import annotations

from datetime import date
from copy import deepcopy

from ..errors import ContractError
from .common import exact_json_numbers, number
from .input_contract import ValidatedInput, validate_export
from .method_config import MethodConfig


class EnergyInputs:
    """Private checked copy with source/instance references for every selection."""

    def __init__(self, exported, methods, catalog):
        source = exported.export if isinstance(exported, ValidatedInput) else exported
        self.validated = validate_export(source, catalog)
        exact_json_numbers(self.validated.export)
        self.methods = MethodConfig.from_dict(methods.to_dict() if isinstance(methods, MethodConfig) else methods)
        self.catalog = catalog
        catalog.definition_identity()
        self.pv_type = self.validated.project.pv_type
        if self.pv_type not in {"industrial_rooftop", "utility_scale_ground"}:
            raise ContractError("ENERGY_CATEGORY_NOT_IMPLEMENTED")
        if self.pv_type not in self.methods.to_dict()["pv_types"]:
            raise ContractError("METHOD_CONFIG_CATEGORY")
        self.values = self.validated.project.values
        evaluation = self.values.get("project.evaluation_date", {})
        if evaluation.get("status") in {"UNKNOWN", "CONFLICT"} or not evaluation.get("value"):
            raise ContractError("BLOCKED_MISSING_INPUT", "project.evaluation_date")
        self.evaluation_date = date.fromisoformat(evaluation["value"])
        self.used = {}

    def record(self, field_id, *, row=None):
        records = self.values if row is None else row.get("fields", {})
        record = records.get(field_id)
        if not record or record.get("value") is None or record.get("status") in {"UNKNOWN", "CONFLICT"}:
            raise ContractError("BLOCKED_MISSING_INPUT", field_id)
        if (not record.get("source_id") or not record.get("source_url_or_attachment")
                or record.get("license_status") in {"DENIED", "UNKNOWN"}):
            raise ContractError("ENERGY_SOURCE_NOT_AUTHORIZED", field_id)
        if record.get("effective_from") and date.fromisoformat(record["effective_from"][:10]) > self.evaluation_date:
            raise ContractError("ENERGY_SOURCE_NOT_EFFECTIVE", field_id)
        if record.get("effective_to") and date.fromisoformat(record["effective_to"][:10]) < self.evaluation_date:
            raise ContractError("ENERGY_SOURCE_EXPIRED", field_id)
        # Track only small project-level inputs. Per-row lineage remains in its
        # original validated bundle and in each streamed output, not a growing set.
        if row is None:
            self.used[field_id] = {"field_id": field_id, "field_instance_id": record["field_instance_id"],
                                   "source_id": record["source_id"], "unit": record["unit"],
                                   "status": record["status"],
                                   "transformation_rule_ids": deepcopy(record["transformation_rule_ids"])}
        return record

    def value(self, field_id, *, row=None):
        return self.record(field_id, row=row)["value"]

    def numeric(self, field_id, *, row=None):
        return number(self.value(field_id, row=row), field_id)

    def rows(self, field_id):
        value = self.value(field_id)
        if not isinstance(value, list) or not value:
            raise ContractError("BLOCKED_MISSING_INPUT", field_id)
        return value

    def optional(self, field_id):
        if field_id not in self.values:
            return None
        return self.value(field_id)
