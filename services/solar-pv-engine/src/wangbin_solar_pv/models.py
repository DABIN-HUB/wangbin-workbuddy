"""Versioned project input data only: never an energy or investment result object."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from . import SCHEMA_VERSION
from .schemas import validate_shape
from .serialization import dumps


@dataclass(slots=True)
class ProjectData:
    schema_version: str
    baseline_version: str
    baseline_hashes: dict[str, str]
    project_id: str
    pv_type: str
    values: dict[str, dict[str, Any]]
    candidates: dict[str, dict]
    resolutions: list[dict]
    revision: int
    submission_ids: dict[str, str]
    history: list[dict]

    @classmethod
    def new(cls, project_id, pv_type, catalog):
        return cls.from_dict({"schema_version": SCHEMA_VERSION, "baseline_version": catalog.baseline_version,
            "baseline_hashes": deepcopy(catalog.baseline_hashes), "project_id": project_id, "pv_type": pv_type,
            "values": {}, "candidates": {}, "resolutions": [], "revision": 0, "submission_ids": {}, "history": []}, catalog)

    @classmethod
    def from_dict(cls, data, catalog):
        dumps(data)  # Reject non-finite/native non-JSON objects before schema checks.
        validate_shape(data, catalog)
        return cls(**deepcopy(data))

    def to_dict(self):
        return {name: deepcopy(getattr(self, name)) for name in self.__dataclass_fields__}
