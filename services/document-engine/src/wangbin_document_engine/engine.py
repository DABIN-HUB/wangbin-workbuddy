"""Document parsing orchestration with per-file failure isolation."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence

from .errors import EngineError
from .markitdown_adapter import MarkItDownAdapter
from .metadata import file_metadata
from .models import BatchResult, DocumentResult
from .process_runner import convert_in_process
from .resource_slots import hold_resource_slot
from .security import SecurityPolicy


class DocumentEngine:
    def __init__(self, policy: SecurityPolicy | None = None, adapter: MarkItDownAdapter | None = None):
        self.policy = policy or SecurityPolicy()
        # The production path uses a fresh parser process. A supplied adapter is
        # retained for embedders that intentionally control the parser boundary.
        self.adapter = adapter

    def parse_file(self, path: Path, input_root: Path, output_dir: Path | None = None) -> DocumentResult:
        started = time.perf_counter()
        source_name = Path(path).name
        try:
            safe_path = self.policy.validate_input(Path(path), input_root)
            if output_dir is not None:
                self.policy.validate_output_dir(output_dir, input_root)
            with hold_resource_slot(), self.policy.snapshot_input(safe_path, input_root) as staged:
                if self.adapter is None:
                    parsed = convert_in_process(
                        staged,
                        self.policy.timeout_seconds,
                        self.policy.max_cpu_seconds,
                        self.policy.max_memory_bytes,
                    )
                else:
                    parsed = self.adapter.convert(staged)
                metadata = file_metadata(staged)
                size_bytes = staged.stat().st_size
            metadata.update(parsed.metadata)
            sections = self._sections(parsed.text)
            duration = int((time.perf_counter() - started) * 1000)
            quality_notes = list(parsed.quality_notes)
            return DocumentResult(
                source_name=safe_path.name,
                source_type=safe_path.suffix.lower().lstrip("."),
                status="success" if parsed.text.strip() else "success_with_warning",
                size_bytes=size_bytes,
                text=parsed.text,
                metadata={"title": parsed.title, **metadata},
                sections=sections,
                quality_notes=quality_notes,
                duration_ms=duration,
            )
        except EngineError as exc:
            return DocumentResult(
                source_name=source_name,
                source_type=Path(path).suffix.lower().lstrip(".") or "unknown",
                status="failed",
                error={"code": exc.code, "message": exc.public_message},
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception:
            return DocumentResult(
                source_name=source_name,
                source_type=Path(path).suffix.lower().lstrip(".") or "unknown",
                status="failed",
                error={"code": "PARSER_ERROR", "message": "文档解析失败，详细异常已脱敏"},
                duration_ms=int((time.perf_counter() - started) * 1000),
            )

    def parse_many(self, paths: Sequence[Path], input_root: Path, output_dir: Path | None = None) -> BatchResult:
        started = time.perf_counter()
        normalized = [Path(item) for item in paths]
        valid_for_total: list[Path] = []
        for path in normalized:
            try:
                safe = self.policy.validate_input(path, input_root)
                valid_for_total.append(safe)
            except Exception:
                # Individual validation errors are returned as item results so
                # one bad file never discards the rest of the batch.
                continue
        if len(normalized) > self.policy.max_files:
            items = [
                DocumentResult(
                    source_name=Path(item).name,
                    source_type=Path(item).suffix.lower().lstrip(".") or "unknown",
                    status="failed",
                    error={"code": "TOO_MANY_FILES", "message": "批处理文件数量超过限制"},
                )
                for item in normalized
            ]
        elif sum(item.stat().st_size for item in valid_for_total) > self.policy.max_batch_bytes:
            items = [
                DocumentResult(
                    source_name=Path(item).name,
                    source_type=Path(item).suffix.lower().lstrip(".") or "unknown",
                    status="failed",
                    error={"code": "BATCH_TOO_LARGE", "message": "批处理累计大小超过限制"},
                )
                for item in normalized
            ]
        else:
            items = [self.parse_file(path, input_root, output_dir) for path in normalized]
        success = sum(item.status.startswith("success") for item in items)
        failure = len(items) - success
        status = "success" if failure == 0 else ("partial_failure" if success else "failed")
        return BatchResult(status, items, success, failure, int((time.perf_counter() - started) * 1000))

    @staticmethod
    def _sections(text: str) -> list[dict[str, int | str]]:
        sections: list[dict[str, int | str]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip("#"))
                heading = stripped[level:].strip()
                if heading:
                    sections.append({"level": level, "title": heading, "line": line_number})
        return sections
