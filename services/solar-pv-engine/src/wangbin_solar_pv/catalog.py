"""Read-only adapter to the frozen input/formula namespaces; never duplicates definitions."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

from .errors import ContractError
from .serialization import loads


class Catalog:
    def __init__(self, baseline_dir: Path | str | None = None):
        package = Path(__file__).resolve().parent
        lock = loads((package / "baseline-lock.json").read_bytes())
        self.baseline_dir = Path(baseline_dir) if baseline_dir is not None else package.parents[3] / "docs/solar-pv"
        self.baseline_hashes = dict(lock["files"])
        self.documents = {}
        for name, expected in self.baseline_hashes.items():
            try:
                payload = (self.baseline_dir / name).read_bytes()
            except OSError as exc:
                raise ContractError("BASELINE_UNAVAILABLE") from exc
            # Git CRLF checkout does not change the UTF-8 content contract.
            normalized = payload.decode("utf-8-sig").replace("\r\n", "\n").encode("utf-8")
            if hashlib.sha256(normalized).hexdigest() != expected:
                raise ContractError("BASELINE_DRIFT", name)
            if name.endswith(".json"):
                self.documents[name] = loads(normalized)
        field_catalog = self.documents["03-input-fields.json"]
        self.fields = {item["field_id"]: deepcopy(item) for item in field_catalog["fields"]}
        if len(self.fields) != len(field_catalog["fields"]):
            raise ContractError("DUPLICATE_FIELD_ID")
        self.pv_types = tuple(field_catalog["pv_types"])
        self.baseline_version = self.documents["08-baseline-contract.json"]["baseline_version"]
        self.bindings = {item["formula_field_id"]: deepcopy(item) for item in self.documents["05-field-bindings.json"]["bindings"]}
        self.formulas = {}
        for name in ("05-formulas.json", "05-formula-extensions.json"):
            for item in self.documents[name]["formulas"]:
                if item["formula_id"] in self.formulas:
                    raise ContractError("DUPLICATE_FORMULA_ID")
                self.formulas[item["formula_id"]] = deepcopy(item)
        self.field_catalog = field_catalog
        self._schema = None

    def metadata(self, field_id: str) -> dict:
        if field_id not in self.fields:
            raise ContractError("UNKNOWN_FIELD", field_id)
        record = deepcopy(self.fields[field_id])
        record.update(
            technical_name=field_id,
            evidence_requirements=deepcopy(self.field_catalog["provenance_record"]),
            validation_status="SCHEMA_SUPPORTED_CALCULATION_NOT_IMPLEMENTED",
            formula_bindings=[deepcopy(b) for b in self.bindings.values() if field_id in b["input_field_ids"]],
            baseline_reference={"version": self.field_catalog["contract_version"], "file": "03-input-fields.json", "sha256": self.baseline_hashes["03-input-fields.json"]},
        )
        return record

    def project_schema(self) -> dict:
        if self._schema is None:
            from .schemas import build_schema
            self._schema = build_schema(self)
        return deepcopy(self._schema)
