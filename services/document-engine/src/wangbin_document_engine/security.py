"""Input and output path safety controls."""
from __future__ import annotations

import os
import stat
import tempfile
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .errors import SecurityViolation

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".html", ".htm", ".txt", ".md", ".markdown"}
_OFFICE_REQUIRED = {
    ".docx": "word/document.xml",
    ".xlsx": "xl/workbook.xml",
    ".pptx": "ppt/presentation.xml",
}


def _has_link_component(path: Path) -> bool:
    """Reject symlinks and Windows junctions before resolving a file path."""
    absolute = Path(os.path.abspath(path.expanduser()))
    return any(part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()) for part in (absolute, *absolute.parents))


@dataclass(frozen=True, slots=True)
class SecurityPolicy:
    max_file_bytes: int = 50 * 1024 * 1024
    max_files: int = 50
    max_batch_bytes: int = 200 * 1024 * 1024
    max_uncompressed_bytes: int = 200 * 1024 * 1024
    max_zip_entries: int = 10_000
    timeout_seconds: float = 60.0
    max_cpu_seconds: int = 60
    max_memory_bytes: int = 2 * 1024 * 1024 * 1024
    max_spreadsheet_rows: int = 100_000
    max_spreadsheet_cells: int = 500_000
    max_export_bytes: int = 50 * 1024 * 1024

    def validate_input(self, path: Path, input_root: Path) -> Path:
        if not input_root.expanduser().is_dir():
            raise SecurityViolation("INPUT_ROOT_MISSING", "允许的输入根目录不存在或不可访问")
        root = input_root.expanduser().resolve(strict=True)
        candidate = path.expanduser()
        if _has_link_component(candidate):
            raise SecurityViolation("SYMLINK_INPUT", "符号链接或目录联接输入不允许处理")
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise SecurityViolation("PATH_OUTSIDE_ROOT", "输入文件不在允许的输入目录内") from exc
        if not resolved.exists():
            raise SecurityViolation("FILE_NOT_FOUND", "输入文件不存在")
        if not resolved.is_file():
            raise SecurityViolation("NOT_A_FILE", "输入路径不是普通文件")
        if resolved.stat().st_size > self.max_file_bytes:
            raise SecurityViolation("FILE_TOO_LARGE", "输入文件超过大小限制")
        suffix = resolved.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise SecurityViolation("UNSUPPORTED_FORMAT", f"不支持的文件格式: {suffix or '[无扩展名]'}")
        self.validate_signature(resolved, suffix)
        if suffix in _OFFICE_REQUIRED:
            self.validate_container(resolved)
        return resolved

    @contextmanager
    def snapshot_input(self, path: Path, input_root: Path) -> Iterator[Path]:
        """Copy a checked open handle to a private, revalidated parsing snapshot."""
        source = self.validate_input(path, input_root)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
        try:
            fd = os.open(source, flags)
        except OSError as exc:
            raise SecurityViolation("INPUT_CHANGED", "输入文件在检查后发生变化") from exc
        with os.fdopen(fd, "rb") as stream:
            initial = os.fstat(stream.fileno())
            try:
                current = source.lstat()
            except OSError as exc:
                raise SecurityViolation("INPUT_CHANGED", "输入文件在检查后发生变化") from exc
            if (not stat.S_ISREG(initial.st_mode) or not stat.S_ISREG(current.st_mode)
                    or (initial.st_dev, initial.st_ino) != (current.st_dev, current.st_ino)
                    or _has_link_component(source) or not source.resolve().is_relative_to(input_root.resolve())):
                raise SecurityViolation("INPUT_CHANGED", "输入文件在检查后发生变化")
            with tempfile.TemporaryDirectory(prefix="wangbin-document-") as private_dir:
                staged = Path(private_dir) / source.name
                copied = 0
                with staged.open("xb") as target:
                    while chunk := stream.read(1024 * 1024):
                        copied += len(chunk)
                        if copied > self.max_file_bytes:
                            raise SecurityViolation("FILE_TOO_LARGE", "输入文件超过大小限制")
                        target.write(chunk)
                finished = os.fstat(stream.fileno())
                if (initial.st_size, initial.st_mtime_ns) != (finished.st_size, finished.st_mtime_ns) or copied != finished.st_size:
                    raise SecurityViolation("INPUT_CHANGED", "复制过程中输入文件发生变化")
                os.utime(staged, ns=(initial.st_atime_ns, initial.st_mtime_ns))
                self.validate_input(staged, staged.parent)
                yield staged

    def validate_batch(self, paths: list[Path]) -> None:
        if len(paths) > self.max_files:
            raise SecurityViolation("TOO_MANY_FILES", "批处理文件数量超过限制")
        total = sum(p.stat().st_size for p in paths if p.exists() and p.is_file())
        if total > self.max_batch_bytes:
            raise SecurityViolation("BATCH_TOO_LARGE", "批处理累计大小超过限制")

    def validate_output_dir(self, output_dir: Path, input_root: Path) -> Path:
        root = input_root.expanduser().resolve(strict=True)
        if _has_link_component(output_dir):
            raise SecurityViolation("SYMLINK_OUTPUT", "输出目录不能包含符号链接或目录联接")
        output = output_dir.expanduser().resolve(strict=False)
        if output == root or output.is_relative_to(root):
            raise SecurityViolation("OUTPUT_EQUALS_INPUT_ROOT", "输出目录必须位于输入根目录之外")
        if output.exists() and not output.is_dir():
            raise SecurityViolation("OUTPUT_PATH_INVALID", "输出路径不是目录")
        try:
            output.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise SecurityViolation("OUTPUT_PERMISSION_DENIED", "没有权限创建输出目录") from exc
        except FileExistsError as exc:
            raise SecurityViolation("OUTPUT_PATH_INVALID", "输出路径不是目录") from exc
        return output

    def validate_signature(self, path: Path, suffix: str) -> None:
        with path.open("rb") as handle:
            prefix = handle.read(16)
        if suffix == ".pdf" and not prefix.startswith(b"%PDF-"):
            raise SecurityViolation("MISMATCHED_EXTENSION", "文件扩展名为 PDF 但文件签名不匹配")
        if suffix == ".pdf":
            with path.open("rb") as handle:
                handle.seek(max(0, path.stat().st_size - 64))
                if b"%%EOF" not in handle.read():
                    raise SecurityViolation("CORRUPT_DOCUMENT", "PDF 文件缺少结束标记")
        if suffix in _OFFICE_REQUIRED and not zipfile.is_zipfile(path):
            raise SecurityViolation("MISMATCHED_EXTENSION", "Office 文件不是有效的 ZIP 容器")

    def validate_container(self, path: Path) -> None:
        try:
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                if len(entries) > self.max_zip_entries:
                    raise SecurityViolation("ZIP_TOO_MANY_ENTRIES", "Office 容器条目数量超过限制")
                total = 0
                for info in entries:
                    name = info.filename.replace("\\", "/")
                    if name.startswith("/") or ".." in name.split("/") or ":" in name.split("/")[0]:
                        raise SecurityViolation("ZIP_PATH_TRAVERSAL", "Office 容器包含路径穿越条目")
                    if info.flag_bits & 1:
                        raise SecurityViolation("ZIP_ENCRYPTED", "不支持加密的 Office 容器")
                    if info.file_size > 1024 * max(info.compress_size, 1):
                        raise SecurityViolation("ZIP_COMPRESSION_RATIO", "Office 容器压缩比过高")
                    if info.file_size > self.max_uncompressed_bytes:
                        raise SecurityViolation("ZIP_ENTRY_TOO_LARGE", "Office 容器单条目展开大小超过限制")
                    total += info.file_size
                    if total > self.max_uncompressed_bytes:
                        raise SecurityViolation("ZIP_TOO_LARGE", "Office 容器累计展开大小超过限制")
                required = _OFFICE_REQUIRED[path.suffix.lower()]
                names = {i.filename for i in entries}
                if "[Content_Types].xml" not in names or required not in names:
                    raise SecurityViolation("MISMATCHED_EXTENSION", "Office 文件内容类型与扩展名不匹配")
        except zipfile.BadZipFile as exc:
            raise SecurityViolation("CORRUPT_CONTAINER", "Office 文件容器损坏") from exc


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
