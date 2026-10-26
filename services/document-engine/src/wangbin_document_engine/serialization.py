"""JSON and concise Markdown serialization for CLI/report consumers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(value: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def result_markdown(value: dict[str, Any]) -> str:
    lines = ["# 文档处理结果", ""]
    if "items" in value:
        lines.extend([
            f"- 状态：`{value.get('status')}`",
            f"- 成功：{value.get('success_count', 0)}",
            f"- 失败：{value.get('failure_count', 0)}",
            "",
        ])
        for item in value.get("items", []):
            lines.append(f"## {item.get('source_name', '[unknown]')}")
            lines.append(f"- 状态：`{item.get('status')}`")
            if item.get("error"):
                lines.append(f"- 错误：`{item['error'].get('code')}` {item['error'].get('message')}")
            else:
                lines.append(f"- 类型：`{item.get('source_type')}`；文本长度：{len(item.get('text', ''))}")
                lines.append("")
                lines.append(item.get("text", "")[:8000])
            lines.append("")
    else:
        lines.append(f"- 状态：`{value.get('status')}`")
        lines.append(f"- 文件：`{value.get('source_name', '[unknown]')}`")
        lines.append("")
        lines.append(value.get("text", ""))
    return "\n".join(lines).rstrip() + "\n"


def write_markdown(value: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(result_markdown(value), encoding="utf-8")
