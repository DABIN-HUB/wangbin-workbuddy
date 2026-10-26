#!/usr/bin/env python3
"""WorkBuddy Skill adapter for the local wangbin document engine.

The platform-facing skill package intentionally contains only this adapter. The
engine must be installed or exposed through WANGBIN_ENGINE_SRC; missing runtime
is reported as a structured error instead of being hidden.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

engine_src = os.environ.get("WANGBIN_ENGINE_SRC")
if engine_src:
    sys.path.insert(0, engine_src)

try:
    from wangbin_document_engine import DocumentEngine, SpreadsheetService
except ImportError as exc:  # pragma: no cover - exercised by runtime probe
    print(json.dumps({"status": "failed", "error": {"code": "ENGINE_RUNTIME_MISSING", "message": "当前运行环境未提供 wangbin 文档引擎"}}, ensure_ascii=False))
    raise SystemExit(78) from exc


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="wangbin WorkBuddy document engine adapter")
    sub = root.add_subparsers(dest="command", required=True)
    parse = sub.add_parser("parse")
    parse.add_argument("--input", required=True, type=Path)
    parse.add_argument("--input-root", required=True, type=Path)
    parse.add_argument("--output-root", type=Path)
    batch = sub.add_parser("batch")
    batch.add_argument("--files", required=True, nargs="+")
    batch.add_argument("--input-root", required=True, type=Path)
    batch.add_argument("--output-root", type=Path)
    dedup = sub.add_parser("deduplicate")
    dedup.add_argument("--input", required=True, type=Path)
    dedup.add_argument("--input-root", required=True, type=Path)
    dedup.add_argument("--output-root", required=True, type=Path)
    dedup.add_argument("--format", choices=["xlsx", "csv"], default="xlsx")
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "parse":
        result = DocumentEngine().parse_file(args.input, args.input_root, args.output_root)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0 if result.status.startswith("success") else 1
    if args.command == "batch":
        result = DocumentEngine().parse_many([Path(item) for item in args.files], args.input_root, args.output_root)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0 if result.status == "success" else 1
    result = SpreadsheetService().deduplicate(args.input, args.input_root, args.output_root, output_format=args.format)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
