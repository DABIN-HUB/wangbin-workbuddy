#!/usr/bin/env python3
"""Conservative, local text-first tender analysis with bounded evidence."""

from __future__ import annotations

import argparse
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any


PENDING = "待核实"
MAX_INPUT_BYTES = 1_048_576
MAX_EVIDENCE_CHARS = 120
ALLOWED_SUFFIXES = frozenset({".txt", ".md"})
DATE_FIELDS = (
    "投标截止时间",
    "开标时间",
    "报名截止时间",
    "采购文件获取截止时间",
    "答疑截止时间",
    "投标保证金截止时间",
    "合同签订时间",
)
LIMITATIONS = [
    "本脚本只分析已抽取的 UTF-8 文本；扫描件若未提供可靠 OCR 文本，相关内容待核实。",
    "复杂版式、页眉页脚、坐标关系可能在文本抽取中丢失，不能据此推定页面位置。",
    "表格、附件或跨页条款的结构可能丢失，需回看原文件核对。",
    "引文是限长、已脱敏的上下文摘录，不是输入字节的逐字证明；请回看原文件核对。",
]

_DATE_RE = re.compile(
    r"((?:19|20)\d{2}[年/-]\s*\d{1,2}[月/-]\s*\d{1,2}(?:日)?"
    r"(?:\s*\d{1,2}(?::|时)\d{2}(?::\d{2})?(?:分)?)?)"
)
_SENSITIVE_LABEL_RE = re.compile(
    r"(?P<label>联系人|联系电话|手机(?:号码)?|电话|邮箱|电子邮箱|身份证(?:号码|号)?|"
    r"证件(?:号码|号)?|账号|账户|银行卡号|银行卡|开户行|地址|邮编|密码|密钥|token|secret|private)"
    r"\s*[:：=]\s*(?P<value>[^,，;；。|\n]+)",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
_ID_RE = re.compile(r"(?<!\d)(?:\d{17}[\dXx]|\d{15})(?!\d)")
_LONG_NUMBER_RE = re.compile(r"(?<!\d)\d{12,}(?!\d)")


# Keep source paths out of result data, including Windows paths supplied to analyze().
def _basename(source_name: str) -> str:
    return source_name.replace("\\", "/").rsplit("/", 1)[-1]


def _redact_sensitive(text: str) -> str:
    """Remove common contact/credential values before text enters result fields."""
    redacted = _SENSITIVE_LABEL_RE.sub(lambda match: f"{match.group('label')}：[已脱敏]", text)
    redacted = _EMAIL_RE.sub("[已脱敏邮箱]", redacted)
    redacted = _PHONE_RE.sub("[已脱敏电话]", redacted)
    redacted = _ID_RE.sub("[已脱敏证件号]", redacted)
    return _LONG_NUMBER_RE.sub("[已脱敏数字]", redacted)


def _evidence(source_name: str, line_number: int, line: str) -> dict[str, Any]:
    excerpt = _redact_sensitive(line.strip())
    if len(excerpt) > MAX_EVIDENCE_CHARS:
        excerpt = excerpt[: MAX_EVIDENCE_CHARS - 1] + "…"
    return {
        "source_name": source_name,
        "line": line_number,
        "quote": excerpt,
        "label": "redacted excerpt",
    }


def _item(
    name: str,
    line_number: int | None,
    line: str | None,
    source_name: str,
    **fields: Any,
) -> dict[str, Any]:
    item: dict[str, Any] = {"name": name, "status": PENDING}
    item.update(fields)
    item["evidence"] = (
        _evidence(source_name, line_number, line)
        if line_number is not None and line is not None
        else None
    )
    return item


def _is_scoring(line: str) -> bool:
    return bool(re.search(r"评分|评审|分值|满分|得分", line))


def _is_eligibility(line: str) -> bool:
    return bool(
        re.search(
            r"资格|资质|营业执照|注册资本|独立法人|同类项目|类似业绩|信用|投标人须",
            line,
        )
    )


def _is_technical(line: str) -> bool:
    return bool(
        re.search(
            r"技术要求|技术参数|技术指标|性能要求|功能要求|系统应|应支持|兼容|响应时间|附件表格",
            line,
        )
    )


def _score_value(line: str) -> int | float | None:
    match = re.search(r"(?:满分|最高分|分值|分数上限)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*分", line)
    if not match:
        return None
    value = float(match.group(1))
    return int(value) if value.is_integer() else value


def _date_value(line: str) -> str | None:
    match = _DATE_RE.search(line)
    return match.group(1).strip() if match else None


def _date_name(line: str) -> str | None:
    deadline = bool(re.search(r"截止|截止日期|截止时间", line))
    if "投标保证金" in line and deadline:
        return "投标保证金截止时间"
    if ("获取采购文件" in line or "购买招标文件" in line) and deadline:
        return "采购文件获取截止时间"
    if ("投标文件" in line or "响应文件" in line) and re.search(r"递交|提交|截止", line):
        return "投标截止时间"
    if "投标截止" in line or "投标截止日期" in line:
        return "投标截止时间"
    if "报名" in line and deadline:
        return "报名截止时间"
    if "开标" in line:
        return "开标时间"
    if ("答疑" in line or "澄清" in line or "提问" in line) and deadline:
        return "答疑截止时间"
    if "合同" in line and re.search(r"签订|签署", line):
        return "合同签订时间"
    if deadline:
        return "其他截止时间"
    return None


def _contains_ambiguity(line: str) -> bool:
    return bool(re.search(r"另行通知|以.+?为准|待定|另附|视.+?而定|不明确|未说明", line))


def _line_texts(text: str) -> list[tuple[int, str]]:
    return [(number, line.rstrip("\r")) for number, line in enumerate(text.splitlines(), start=1)]


def _evidence_values(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _checklist_item(name: str, evidence: dict[str, Any] | None, requirement: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"name": name, "status": PENDING}
    if requirement is not None:
        item["requirement"] = requirement
    item["evidence"] = evidence
    return item


def _response_checklist(
    lines: list[tuple[int, str]],
    source_name: str,
) -> list[dict[str, Any]]:
    patterns = (
        ("核对保证金/押金要求", r"保证金|押金"),
        ("填写必需表单和函件", r"表格|表单|投标函|响应函|承诺函|声明函|报价函|格式"),
        ("准备附件及证明材料", r"附件|证明材料|材料清单|营业执照|业绩证明|授权委托书|证书"),
        ("核对提交方式、份数和递交要求", r"递交|提交|上传|密封|电子|纸质|平台|截止"),
        ("完成签字、盖章和授权签署", r"签字|签署|盖章|签章|授权代表|法定代表人"),
    )
    checklist: list[dict[str, Any]] = []
    for name, pattern in patterns:
        matches = [(number, line) for number, line in lines if re.search(pattern, line)]
        if matches:
            checklist.extend(
                _checklist_item(name, _evidence(source_name, number, line), _redact_sensitive(line.strip()))
                for number, line in matches
            )
        else:
            checklist.append(_checklist_item(name, None))
    return checklist


def analyze(text: str, source_name: str) -> dict[str, Any]:
    """Analyze already-extracted text without calculating a bid result or inventing pages."""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if not isinstance(source_name, str) or not source_name:
        raise ValueError("source_name must be a non-empty string")
    safe_source_name = _basename(source_name)
    if not safe_source_name:
        raise ValueError("source_name must include a basename")

    lines = _line_texts(text)
    eligibility: list[dict[str, Any]] = []
    scoring: list[dict[str, Any]] = []
    technical: list[dict[str, Any]] = []
    dates_by_name: dict[str, list[dict[str, Any]]] = {}
    date_names_seen: list[str] = []
    risks: list[dict[str, Any]] = []

    for line_number, raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        safe_line = _redact_sensitive(line)

        if _is_scoring(line):
            scoring.append(
                _item(
                    "评分条款",
                    line_number,
                    raw_line,
                    safe_source_name,
                    criterion=safe_line,
                    max_score=_score_value(line),
                    awarded_score=None,
                )
            )
        elif _is_eligibility(line):
            eligibility.append(
                _item(
                    "资格条件",
                    line_number,
                    raw_line,
                    safe_source_name,
                    requirement=safe_line,
                )
            )

        if _is_technical(line):
            technical.append(
                _item(
                    "技术要求",
                    line_number,
                    raw_line,
                    safe_source_name,
                    requirement=safe_line,
                )
            )

        date_name = _date_name(line)
        if date_name:
            date_item = _item(
                date_name,
                line_number,
                raw_line,
                safe_source_name,
                value=_date_value(line),
            )
            dates_by_name.setdefault(date_name, []).append(date_item)
            if date_name not in date_names_seen:
                date_names_seen.append(date_name)

        if _contains_ambiguity(line):
            risks.append(
                _item(
                    "歧义条款",
                    line_number,
                    raw_line,
                    safe_source_name,
                    description=safe_line,
                )
            )

    dates: list[dict[str, Any]] = []
    for name in DATE_FIELDS:
        occurrences = dates_by_name.get(name, [])
        dates.extend(occurrences or [_item(name, None, None, safe_source_name, value=None)])
    dates.extend(
        item for name in date_names_seen if name not in DATE_FIELDS for item in dates_by_name[name]
    )

    for name, occurrences in dates_by_name.items():
        if len(occurrences) < 2:
            continue
        date_evidence = [item["evidence"] for item in occurrences if item.get("evidence")]
        risks.append(
            {
                "name": "日期冲突",
                "status": PENDING,
                "date_name": name,
                "description": f"{name}出现重复或冲突记录，需逐条核对公告、澄清文件和原始采购文件。",
                "values": [item.get("value") for item in occurrences],
                "evidence": date_evidence,
            }
        )

    absent_categories = {
        "资格条件": not eligibility,
        "评分条款": not scoring,
        "技术要求": not technical,
    }
    for name, absent in absent_categories.items():
        if absent:
            risks.append(
                {
                    "name": "缺失信息",
                    "status": PENDING,
                    "description": f"未发现{name}，不能据此判断投标响应或得分。",
                    "evidence": None,
                }
            )
    for name in DATE_FIELDS:
        if not dates_by_name.get(name):
            risks.append(
                {
                    "name": "缺失重要日期",
                    "status": PENDING,
                    "description": f"未发现{name}，需回看采购文件及澄清公告。",
                    "date_name": name,
                    "evidence": None,
                }
            )

    checklist: list[dict[str, Any]] = []
    for category in (eligibility, scoring, technical):
        for item in category:
            requirement = item.get("requirement") or item.get("criterion")
            checklist.append(_checklist_item(f"响应：{item['name']}", item.get("evidence"), requirement))
    for item in dates:
        requirement = f"{item['name']}：{item.get('value')}" if item.get("value") else item["name"]
        checklist.append(_checklist_item(f"核对：{item['name']}", item.get("evidence"), requirement))
    checklist.extend(_response_checklist(lines, safe_source_name))

    evidence: list[dict[str, Any]] = []
    seen_evidence: set[tuple[int, str]] = set()
    for collection in (eligibility, scoring, technical, dates, checklist, risks):
        for item in collection:
            for item_evidence in _evidence_values(item.get("evidence")):
                key = (item_evidence["line"], item_evidence["quote"])
                if key not in seen_evidence:
                    evidence.append(item_evidence)
                    seen_evidence.add(key)

    return {
        "status": "success_with_warning",
        "source_name": safe_source_name,
        "privacy": {
            "execution_scope": "local_script_only",
            "authorization_verified": False,
            "remote_upload": False,
            "full_input_persisted": False,
            "platform_installation": "BLOCKED/NOT_TESTED",
            "platform_call": "BLOCKED/NOT_TESTED",
        },
        "eligibility": eligibility,
        "scoring": scoring,
        "technical": technical,
        "dates": dates,
        "checklist": checklist,
        "risks": risks,
        "limitations": LIMITATIONS.copy(),
        "evidence": evidence,
    }


def _read_authorized_utf8(path: Path) -> str:
    try:
        if path.is_symlink():
            raise ValueError("INPUT_SYMLINK")
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError("INPUT_TYPE_UNSUPPORTED")
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("INPUT_NOT_REGULAR")
        if metadata.st_size > MAX_INPUT_BYTES:
            raise ValueError("INPUT_TOO_LARGE")
        data = path.read_bytes()
        if len(data) > MAX_INPUT_BYTES:
            raise ValueError("INPUT_TOO_LARGE")
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("INVALID_UTF8") from exc
    except ValueError:
        raise
    except FileNotFoundError as exc:
        raise ValueError("INPUT_NOT_FOUND") from exc
    except OSError as exc:
        raise ValueError("INPUT_READ_FAILED") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze one local UTF-8 tender TXT or Markdown file conservatively.")
    parser.add_argument("--input", required=True, type=Path, help="one authorized UTF-8 .txt or .md file")
    args = parser.parse_args(argv)

    try:
        text = _read_authorized_utf8(args.input)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    result = analyze(text, args.input.name)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
