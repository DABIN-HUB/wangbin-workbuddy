"""Run the explicit pytest suite and capture non-fabricated evidence."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def run_tests(root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    command = [sys.executable, "-m", "pytest", "tests", "-q", "--tb=short"]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=600)
    duration = round(time.perf_counter() - started, 3)
    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "duration_seconds": duration,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-12000:],
    }


def write_test_report(result: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(
        "# 自动化测试报告\n\n"
        f"- 状态：`{result['status']}`\n"
        f"- 命令：`{result['command']}`\n"
        f"- 退出码：`{result['exit_code']}`\n"
        f"- 耗时：`{result['duration_seconds']}` 秒\n\n"
        "## 标准输出\n\n```text\n"
        f"{result.get('stdout', '')}\n````\n\n"
        "## 标准错误（已截断）\n\n```text\n"
        f"{result.get('stderr', '')}\n```\n",
        encoding="utf-8",
    )
