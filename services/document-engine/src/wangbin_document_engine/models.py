"""Stable result and parser data models for the wangbin document engine."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ParsedDocument:
    text: str
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    quality_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DocumentResult:
    source_name: str
    source_type: str
    status: str
    size_bytes: int = 0
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    sections: list[dict[str, Any]] = field(default_factory=list)
    quality_notes: list[str] = field(default_factory=list)
    error: dict[str, str] | None = None
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BatchResult:
    status: str
    items: list[DocumentResult]
    success_count: int
    failure_count: int
    duration_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "items": [item.to_dict() for item in self.items],
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "duration_ms": self.duration_ms,
        }


@dataclass(slots=True)
class SpreadsheetSummary:
    source_name: str
    worksheets: list[dict[str, Any]]
    total_rows: int
    total_null_cells: int
    total_duplicate_rows: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExportResult:
    status: str
    output_path: str | None
    source_name: str
    rows_read: int
    rows_written: int
    duplicates_removed: int
    error: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
