"""Reusable validator report model."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class Finding:
    code: str
    path: str
    message: str
    severity: str = "error"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class ValidationReport:
    status: str
    checks: list[dict[str, Any]]
    findings: list[Finding]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "checks": self.checks,
            "findings": [finding.to_dict() for finding in self.findings],
        }
