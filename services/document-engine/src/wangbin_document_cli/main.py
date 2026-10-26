"""WorkBuddy-compatible, local-only Python CLI entry point.

Business commands never download packages or contact a document processing API.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from pathlib import Path

from . import __version__

_REQUIRED = {"wangbin-document-cli": __version__, "markitdown": "0.1.9", "openpyxl": "3.1.5"}


def _health() -> list[str]:
    failures = []
    for name, expected in _REQUIRED.items():
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            failures.append(f"{name}: NOT_INSTALLED")
        else:
            if actual != expected:
                failures.append(f"{name}: expected {expected}, found {actual}")
    if not failures:
        try:
            importlib.import_module("wangbin_document_engine")
        except (ImportError, OSError):
            failures.append("wangbin_document_engine: IMPORT_FAILED")
    return failures


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wangbin-document-cli")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("version", "doctor", "auth", "status", "logout"):
        sub.add_parser(command)
    parse = sub.add_parser("parse")
    parse.add_argument("--input", type=Path, required=True)
    parse.add_argument("--input-root", type=Path, required=True)
    parse.add_argument("--output-root", type=Path)
    batch = sub.add_parser("batch")
    batch.add_argument("--files", type=Path, nargs="+", required=True)
    batch.add_argument("--input-root", type=Path, required=True)
    batch.add_argument("--output-root", type=Path)
    dedup = sub.add_parser("deduplicate")
    dedup.add_argument("--input", type=Path, required=True)
    dedup.add_argument("--input-root", type=Path, required=True)
    dedup.add_argument("--output-root", type=Path, required=True)
    dedup.add_argument("--format", choices=("xlsx", "csv"), default="xlsx")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "version":
        _emit({"status": "success", "version": __version__})
        return 0
    if args.command == "logout":
        _emit({"status": "success", "auth_mode": "none", "message": "无远程会话；未删除任何用户文件"})
        return 0
    failures = _health()
    if args.command == "auth":
        if failures:
            _emit({"status": "failed", "error": {"code": "ENGINE_RUNTIME_MISSING", "message": "本地 CLI 未准备就绪；请重新安装", "issues": failures}})
            return 78
        _emit({"status": "success", "auth_mode": "none", "message": "仅本地处理，无外部账号或授权链接"})
        return 0
    if args.command == "doctor":
        _emit({"status": "success" if not failures else "failed", "version": __version__, "runtime": sys.version.split()[0], "dependencies": "ready" if not failures else "missing_or_mismatched", "issues": failures})
        return 0 if not failures else 78
    if args.command == "status":
        if failures:
            _emit({"status": "failed", "error": {"code": "ENGINE_RUNTIME_MISSING", "message": "请先安装或修复 CLI 及其声明的 Python 依赖", "issues": failures}})
            return 78
        print("LOCAL_READY")
        return 0
    if failures:
        _emit({"status": "failed", "error": {"code": "ENGINE_RUNTIME_MISSING", "message": "请先安装或修复 CLI 及其声明的 Python 依赖", "issues": failures}})
        return 78
    try:
        from wangbin_document_engine.errors import EngineError
        from wangbin_document_engine import DocumentEngine, SpreadsheetService
        if args.command == "parse":
            result = DocumentEngine().parse_file(args.input, args.input_root, args.output_root)
        elif args.command == "batch":
            result = DocumentEngine().parse_many(args.files, args.input_root, args.output_root)
        else:
            result = SpreadsheetService().deduplicate(args.input, args.input_root, args.output_root, output_format=args.format)
        _emit(result.to_dict())
        return 0 if result.status.startswith("success") else 1
    except ModuleNotFoundError:
        _emit({"status": "failed", "error": {"code": "ENGINE_RUNTIME_MISSING", "message": "文档解析依赖未完整安装；请重新安装受信任的发行包"}})
        return 78
    except EngineError as exc:
        _emit({"status": "failed", "error": {"code": exc.code, "message": exc.public_message}})
        return 1
    except Exception:
        _emit({"status": "failed", "error": {"code": "RUNTIME_ERROR", "message": "处理失败；检查输入目录、输出权限和文件格式"}})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
