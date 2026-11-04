"""F04's ten frozen source/assumption sheets, as a private draft XLSX.

Never renders raw attachments or a guessed financial number. This is not the
four-file report exporter, and never changes the canonical result.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import os
from pathlib import Path
import tempfile

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .calculation.result_contract import validate_result
from .errors import ContractError
from .local_files import Workspace
from .serialization import digest, dumps

SHEETS = (
    ("S01", "输入台账"), ("S02", "气象与地理来源"), ("S03", "政策适用性"),
    ("S04", "设备与成本来源"), ("S05", "案例对标"), ("S06", "假设清单"),
    ("S07", "冲突与缺口"), ("S08", "变更与复核记录"),
    ("S09", "变量-术语词典"), ("S10", "资料授权说明"),
)
MAX_ROWS = 25000


def _display(value):
    if value is None:
        return "UNKNOWN"
    if isinstance(value, (dict, list)):
        if isinstance(value, list):
            return f"[ARRAY:{len(value)}; 详见逐项台账/受控canonical]"
        return dumps(value)
    return str(value) if not isinstance(value, (str, int, bool)) else value


def _rows(result, catalog, formula_map):
    snapshot = result["source_snapshot"].get("phase2", {})
    records = snapshot.get("records", [])
    if not isinstance(records, list) or len(records) > MAX_ROWS:
        raise ContractError("SOURCE_XLSX_RECORD_LIMIT")
    rows_by_sheet = {sheet: [] for _, sheet in SHEETS}
    row_ids = {}
    for record in records:
        if isinstance(record.get("value"), list):
            for row in record["value"]:
                if isinstance(row, dict) and "row_id" in row:
                    for child in row.get("fields", {}).values():
                        if isinstance(child, dict):
                            row_ids[child.get("field_instance_id")] = row["row_id"]
    candidates = list(snapshot.get("candidates", {}).values())
    for state, record in [("ACTIVE", r) for r in records] + [("CANDIDATE", r) for r in candidates]:
        fid = record["field_id"]
        row = [state, fid, record["field_instance_id"], row_ids.get(record["field_instance_id"], ""),
               _display(record.get("original_value")), _display(record.get("value")),
               _display(record.get("unit")), _display(record.get("provenance_kind")),
               record.get("source_kind"), _display(record.get("source_id")), record.get("status"),
               record.get("license_status"), _display(record.get("source_section_or_cell")),
               _display(record.get("effective_from")), _display(record.get("effective_to")),
               _display(record.get("confidence_basis")), _display(record.get("reviewer"))]
        rows_by_sheet["输入台账"].append(row)
        if fid.startswith(("site.", "resource.")):
            rows_by_sheet["气象与地理来源"].append(row)
        if fid.startswith("policy."):
            rows_by_sheet["政策适用性"].append(row)
        if fid.startswith(("system.", "capex.", "opex.", "assets.")):
            rows_by_sheet["设备与成本来源"].append(row)
        if record.get("source_kind") == "ASSUMPTION" or record["status"] == "ASSUMED":
            assumption = record.get("assumption") or {}
            rows_by_sheet["假设清单"].append([fid, record["field_instance_id"],
                _display(record.get("value")), _display(record.get("unit")),
                record.get("source_id") or "UNKNOWN", record["status"],
                _display(assumption.get("reason")), _display(assumption.get("method")),
                _display(assumption.get("maturity_ceiling"))])
        if record["status"] in {"UNKNOWN", "CONFLICT"} or record["license_status"] != "AUTHORIZED":
            rows_by_sheet["冲突与缺口"].append([fid, record["field_instance_id"],
                record["status"], record["license_status"],
                _display(record.get("missing_reason")), ",".join(record.get("candidate_ids") or []),
                "待人工补充/审核", "UNKNOWN"])
    for metric in result["results"]["metrics"]:
        if metric["status"].startswith("BLOCKED_"):
            rows_by_sheet["冲突与缺口"].append([metric["formula_id"], metric["metric_id"],
                metric["status"], "UNKNOWN", metric["reason"], "", "待核实公式上游", "UNKNOWN"])
    if formula_map is not None:
        for row in formula_map["formulas"]:
            if row["project_status"] in {"NOT_TESTED", "NOT_IMPLEMENTED"}:
                rows_by_sheet["冲突与缺口"].append([row["formula_id"], "", row["project_status"],
                    "UNKNOWN", "未提供本项目数值证据", "", "待后续专项", "UNKNOWN"])
    for event in snapshot.get("resolutions", []) + snapshot.get("context_invalidations", []):
        rows_by_sheet["变更与复核记录"].append([
            _display(event.get("event", "人工冲突选择")), _display(event.get("field_id", event.get("field_ids"))),
            _display(event.get("candidate_id")), _display(event.get("reviewer")),
            _display(event.get("reason")), _display(event.get("at", event.get("reviewed_at"))),
            result["input_hash"], result["result_hash"]])
    for fid, field in sorted(catalog.fields.items()):
        rows_by_sheet["变量-术语词典"].append(["FIELD", fid, field.get("label_zh"),
            _display(field.get("unit")), _display(field.get("chapter_ids")), "冻结字段"])
    for fid, formula in sorted(catalog.formulas.items()):
        rows_by_sheet["变量-术语词典"].append(["FORMULA", fid, formula.get("chinese_name"),
            _display(formula.get("unit")), _display(formula.get("report_chapter_ids")),
            result["formula_snapshot"]["definition_version"]])
    sources = defaultdict(list)
    for record in records + candidates:
        sources[record.get("source_id") or "UNKNOWN"].append(record)
    for source_id, entries in sorted(sources.items()):
        rows_by_sheet["资料授权说明"].append([source_id,
            ",".join(sorted({r["license_status"] for r in entries})),
            ",".join(sorted({r["source_kind"] for r in entries})),
            ",".join(sorted({r["sensitivity"] for r in entries})),
            ",".join(sorted({r["status"] for r in entries})),
            "NOT_AUTHORIZED_FOR_UPLOAD", "原始附件及URL仅见受控canonical/来源存储"])
    headers = {
        "输入台账": ["选用", "field_id", "instance_id", "row_id", "原值", "规范值", "单位", "U/D/C/AI", "来源类型", "source_id", "质量状态", "授权状态", "原件位置", "有效起", "有效止", "证据依据", "核验人"],
        "气象与地理来源": ["选用", "field_id", "instance_id", "row_id", "原值", "规范值", "单位", "U/D/C/AI", "来源类型", "source_id", "质量状态", "授权状态", "原件位置", "有效起", "有效止", "证据依据", "核验人"],
        "政策适用性": ["选用", "field_id", "instance_id", "row_id", "原值", "规范值", "单位", "U/D/C/AI", "来源类型", "source_id", "质量状态", "授权状态", "原件位置", "有效起", "有效止", "证据依据", "核验人"],
        "设备与成本来源": ["选用", "field_id", "instance_id", "row_id", "原值", "规范值", "单位", "U/D/C/AI", "来源类型", "source_id", "质量状态", "授权状态", "原件位置", "有效起", "有效止", "证据依据", "核验人"],
        "案例对标": ["案例ID", "来源ID", "真实项目核验", "许可", "缺口说明"],
        "假设清单": ["field_id", "instance_id", "假设值", "单位", "source_id", "状态", "理由", "方法", "成熟度上限"],
        "冲突与缺口": ["field/formula_id", "instance/metric_id", "状态", "许可", "原因", "候选", "责任", "关闭证据"],
        "变更与复核记录": ["事件", "字段", "候选", "复核人", "理由", "时间", "input_hash", "result_hash"],
        "变量-术语词典": ["类型", "冻结ID", "中文名", "单位", "章节", "版本/说明"],
        "资料授权说明": ["source_id", "许可状态", "来源类型", "敏感级", "核验状态", "远传", "访问说明"],
    }
    for sheet in ("案例对标", "变更与复核记录", "政策适用性", "假设清单"):
        if not rows_by_sheet[sheet]:
            rows_by_sheet[sheet].append(["UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "无可核实来源；不填零"])
    for sheet in rows_by_sheet:
        if len(rows_by_sheet[sheet]) + 9 > MAX_ROWS:
            raise ContractError("SOURCE_XLSX_RECORD_LIMIT")
    return headers, rows_by_sheet


def create_source_workbook(result, catalog, workspace, filename, *, formula_map=None):
    """Create and parse back a single F04 DRAFT_PARTIAL diagnostic workbook."""
    if not isinstance(workspace, Workspace) or not isinstance(filename, str) or not filename.endswith(".xlsx"):
        raise ContractError("SOURCE_XLSX_TARGET")
    output = workspace.path(filename, json_only=False)
    if output.exists():
        raise ContractError("OUTPUT_EXISTS")
    result = validate_result(result, catalog)
    if formula_map is not None:
        if (formula_map.get("canonical_result_hash") != result["result_hash"]
                or formula_map.get("project_id") != result["project_id"]
                or formula_map.get("scenario_id") != result["scenario_id"]
                or formula_map.get("mapping_hash") != digest({k: v for k, v in formula_map.items() if k != "mapping_hash"})):
            raise ContractError("SOURCE_XLSX_FORMULA_IDENTITY")
    headers, data = _rows(result, catalog, formula_map)
    book = Workbook()
    book.remove(book.active)
    for sid, name in SHEETS:
        ws = book.create_sheet(name)
        ws.append([sid, "资料来源与假设清单", "DRAFT_PARTIAL；非四文件交付／非投资决策依据"])
        if sid == "S09":
            ws.append(["逻辑工作表名", "变量/术语词典", "Excel禁用斜杠；物理工作表名：变量-术语词典"])
        else:
            ws.append(["状态", "DRAFT_PARTIAL", "仅受控私有工作区；不远传"])
        for key in ("model_version", "run_id", "input_hash", "source_snapshot_id", "result_hash"):
            ws.append([key, _display(result[key])])
        ws.append(["项目与场景", result["project_id"], result["scenario_id"]])
        ws.append(headers[name])
        for row in data[name]:
            ws.append([_display(value) for value in row])
        ws.freeze_panes = "A10"
        ws.auto_filter.ref = f"A9:{get_column_letter(len(headers[name]))}{ws.max_row}"
        ws.column_dimensions["A"].width = 24
        ws.column_dimensions["B"].width = 35
        ws.column_dimensions["C"].width = 39
        for cell in ws[9]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="16446B")
        for row in ws:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.data_type = "s"  # even '=HYPERLINK(...)' is literal, never a formula
                    cell.number_format = "@"
                cell.alignment = Alignment(vertical="top")
    descriptor, tmp = tempfile.mkstemp(prefix=".source-f04-", suffix=".xlsx", dir=output.parent)
    os.close(descriptor)
    try:
        book.save(tmp)
        if os.path.getsize(tmp) > 16 * 1024 * 1024:
            raise ContractError("SOURCE_XLSX_SIZE_LIMIT")
        # Real OOXML round-trip, including all ten exact physical sheet names.
        inspected = load_workbook(tmp, read_only=True, data_only=False)
        try:
            if inspected.sheetnames != [name for _, name in SHEETS]:
                raise ContractError("SOURCE_XLSX_SHEETS")
            for ws in inspected:
                if ws[5][1].value != result["input_hash"] or ws[7][1].value != result["result_hash"]:
                    raise ContractError("SOURCE_XLSX_IDENTITY")
        finally:
            inspected.close()
        workspace.path(filename, json_only=False)
        try:
            os.link(tmp, output)
        except FileExistsError:
            raise ContractError("OUTPUT_EXISTS") from None
        with output.open("rb") as saved:
            file_hash = sha256(saved.read()).hexdigest()
        return {"status": "DRAFT_PARTIAL", "file": filename, "project_id": result["project_id"],
                "scenario_id": result["scenario_id"], "input_hash": result["input_hash"],
                "source_snapshot_id": result["source_snapshot_id"],
                "result_hash": result["result_hash"], "sha256": file_hash,
                "sheets": [name for _, name in SHEETS]}
    finally:
        Path(tmp).unlink(missing_ok=True)
