"""Offline evidence-linked meeting action reconciliation. Python 3.11+, openpyxl, python-docx."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook, load_workbook
from docx import Document

SHEETS = {
    "当前任务": "task_id,任务内容,负责人,负责人确认状态,截止时间,截止时间确认状态,执行状态,完成证据,是否逾期,逾期判断依据,来源,最近变更".split(","),
    "本次新增与变化": "task_id,关联原任务,变化类型,原值,新值,确认状态,来源,event_id".split(","),
    "待确认事项": "task_id,待确认字段,候选值或问题,原因,候选来源,建议用户确认内容".split(","),
    "状态历史": "event_id,task_id,事件类型,原值,新值,来源,会议或用户确认时间,是否存在冲突".split(","),
}
MAX_BYTES = 5_000_000
MAX_ZIP_UNPACKED = 20_000_000
MAX_ROWS = 5000
MAX_TEXT = 300_000

class InputError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_cell(value):
    value = str(value if value is not None else "")
    return "'" + value if value.startswith(("=", "+", "-", "@")) else value


def checked(path, suffixes):
    path = Path(path)
    if path.suffix.lower() not in suffixes:
        raise InputError("INVALID_FORMAT", f"{path.name}: 只接受 {', '.join(sorted(suffixes))}")
    try:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_BYTES:
            raise InputError("INVALID_FORMAT", f"{path.name}: 不存在、符号链接或超过 {MAX_BYTES} 字节")
        if path.suffix.lower() in {".docx", ".xlsx"}:
            if not zipfile.is_zipfile(path):
                raise InputError("CORRUPT_INPUT", f"{path.name}: 非有效 Office ZIP")
            with zipfile.ZipFile(path) as z:
                members = z.infolist()
                if (len(members) > 2000 or sum(m.file_size for m in members) > MAX_ZIP_UNPACKED
                    or any(m.file_size > MAX_ZIP_UNPACKED or m.filename.startswith(("/", "\\"))
                           or ".." in Path(m.filename).parts for m in members)):
                    raise InputError("INVALID_FORMAT", f"{path.name}: 压缩内容超过安全限额")
                if z.testzip():
                    raise InputError("CORRUPT_INPUT", f"{path.name}: 压缩内容损坏")
                if any("externalLink" in m.filename or "vbaProject" in m.filename for m in members):
                    raise InputError("INVALID_FORMAT", f"{path.name}: 不接受外链或宏")
    except OSError as exc:
        raise InputError("CORRUPT_INPUT", f"{path.name}: 无法读取") from exc
    return path


def read_text(path):
    path = checked(path, {".txt", ".md", ".docx"})
    try:
        if path.suffix.lower() == ".docx":
            doc = Document(path)
            lines = [p.text for p in doc.paragraphs]
            lines += [" | ".join(c.text for c in row.cells) for table in doc.tables for row in table.rows]
        else:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        result = [(i, s.strip()) for i, s in enumerate(lines, 1) if s.strip()]
        if sum(len(s) for _, s in result) > MAX_TEXT:
            raise InputError("INVALID_FORMAT", f"{path.name}: 文本超限")
        return result
    except (OSError, UnicodeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        raise InputError("CORRUPT_INPUT", f"{path.name}: 无法解析") from exc


def previous(path):
    if not path:
        return {}, []
    path = checked(path, {".csv", ".xlsx"})
    try:
        if path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
                headers = list(rows[0]) if rows else list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")).fieldnames or [])
            histories = []
        else:
            wb = load_workbook(path, read_only=True, data_only=True)
            ws = wb["当前任务"] if "当前任务" in wb else wb.active
            values = ws.values
            headers = [str(v or "") for v in next(values)]
            rows = [dict(zip(headers, row)) for row in values]
            histories = []
            if "状态历史" in wb:
                hvals = wb["状态历史"].values
                hhead = [str(v or "") for v in next(hvals)]
                if hhead != SHEETS["状态历史"]:
                    raise InputError("INVALID_PREVIOUS_SCHEMA", "状态历史表头不匹配")
                histories = [dict(zip(hhead, row)) for row in hvals]
            wb.close()
        if len(rows) > MAX_ROWS or len(histories) > MAX_ROWS * 10 or not {"task_id", "任务内容", "执行状态"}.issubset(headers):
            raise InputError("INVALID_PREVIOUS_SCHEMA", "旧表缺 task_id/任务内容/执行状态或行数超限")
        result = {}
        for row in rows:
            task = {key: str(row.get(key) or "") for key in SHEETS["当前任务"]}
            tid = task["task_id"].strip()
            if not tid:
                raise InputError("INVALID_PREVIOUS_SCHEMA", "旧表含空任务 ID")
            if tid in result:
                raise InputError("DUPLICATE_TASK_ID", f"旧表任务 ID 重复: {tid}")
            result[tid] = task
        history = [{key: str(row.get(key) or "") for key in SHEETS["状态历史"]} for row in histories]
        return result, history
    except InputError:
        raise
    except (OSError, ValueError, KeyError, StopIteration, UnicodeError, csv.Error, zipfile.BadZipFile) as exc:
        raise InputError("CORRUPT_INPUT", f"{path.name}: 旧表读取失败") from exc


def iso(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise InputError("INVALID_DATE", "日期必须为合法 YYYY-MM-DD") from exc


def statements(lines, filename):
    # Separate independent decisions while keeping their original line as evidence.
    for line, text in lines:
        for segment in re.split(r"[。；;\n]", text):
            segment = segment.strip(" ，、\t")
            if segment:
                yield segment, f"{filename}:行{line}：{segment[:200]}"


def reconcile(meeting_file, previous_tasks=None, supplemental_evidence=None, corrections=None,
              project_name="会议", check_date=None, timezone=None, response_mode="export",
              draft_followup=False, output_dir=None):
    if response_mode not in {"export", "summary", "one_sentence"}:
        raise InputError("INVALID_FORMAT", "response_mode 无效")
    if not project_name or re.search(r"[/\\:\x00-\x1f]", project_name) or project_name.strip(" .").upper() in {"CON", "PRN", "AUX", "NUL"} or ".." in project_name:
        raise InputError("INVALID_FORMAT", "项目名不能包含路径或设备名")
    if check_date:
        check_date = iso(check_date)
    meeting_file = checked(meeting_file, {".txt", ".md", ".docx"})
    lines = read_text(meeting_file)
    if not lines:
        raise InputError("EMPTY_MEETING", f"{meeting_file.name}: 会议内容为空")
    tasks, history = previous(previous_tasks)
    history_by_id = {h["event_id"]: h for h in history if h["event_id"]}
    changes, questions = [], []
    for task in tasks.values():
        task["最近变更"] = "无新增进展"
    full = "\n".join(s for _, s in lines)
    dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", full))
    meeting_dates = sorted({iso(d) for d in dates if re.search(re.escape(d) + r"[^。；\n]{0,20}(?:会议|例会)", full)})
    meeting_date = meeting_dates[0] if len(meeting_dates) == 1 else None

    def ask(tid, field, value, reason, source):
        row = dict(zip(SHEETS["待确认事项"], [tid, field, value, reason, source, f"请确认 {tid or '该事项'} 的{field}及依据"] ))
        if row not in questions:
            questions.append(row)

    def event(tid, typ, old, new, source, confirmed=True, conflict=False):
        semantic = "|".join([tid, typ, str(old), str(new), str(conflict)])
        eid = "EV-" + digest(semantic)[:20]
        if eid in history_by_id:
            return
        row = dict(zip(SHEETS["状态历史"], [eid, tid, typ, old, new, source, meeting_date or "", "是" if conflict else "否"]))
        history_by_id[eid] = row
        changes.append(dict(zip(SHEETS["本次新增与变化"], [tid, tid if tid in tasks else "", typ, old, new, "待确认" if conflict or not confirmed else "已确认", source, eid])))

    def locate(segment, source):
        ids = [tid for tid in tasks if re.search(r"(?<![\w-])" + re.escape(tid) + r"(?![\w-])", segment, re.I)]
        if len(ids) == 1:
            return ids[0]
        if len(ids) > 1:
            ask("", "任务关联", segment, "多个任务 ID", source)
            return None
        matches = [tid for tid, t in tasks.items() if t["任务内容"] and t["任务内容"] in segment]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            ask("", "任务关联", segment, "多个匹配事项", source)
        return None

    def update(tid, field, value, typ, source, confirmed=True):
        task = tasks[tid]
        old = task.get(field, "")
        if not confirmed:
            event(tid, typ, old, value, source, False)
            ask(tid, field, value, "仅为建议或未获确认", source)
            return
        if old == value:
            return
        event(tid, typ, old, value, source)
        task[field] = value
        task["最近变更"] = typ
        task["来源"] = source

    recent_new = []
    def apply(segment, source, evidence=False, correction=False):
        tid = locate(segment, source)
        if tid is None and not evidence and not correction and re.search(r"建议由|由.*确认负责", segment) and len(recent_new) == 1:
            tid = recent_new[0]
        new_match = re.search(r"(?:新增(?:事项|任务)?|决定新增|决议新增)\s*[：:]?\s*(.+)", segment)
        if tid is None and new_match:
            description = re.split(r"[，,](?:由|建议|截止|明天)", new_match.group(1))[0].strip(" .；。")
            if not description:
                ask("", "任务内容", segment, "无法抽取新任务", source)
                return
            key = re.sub(r"\s+", "", description)
            tid = "MTG-" + digest(project_name + "|" + key)[:16].upper()
            if tid not in tasks:
                tasks[tid] = {key: "" for key in SHEETS["当前任务"]}
                tasks[tid].update(task_id=tid, 任务内容=description, 执行状态="待执行", 来源=source, 最近变更="新增")
                event(tid, "新增", "", description, source)
            recent_new[:] = [tid]
        if tid is None:
            if evidence or correction or re.search(r"(已完成|取消|负责|明天|截止|重开|进行中)", segment):
                ask("", "任务关联", segment, "无法唯一定位旧任务", source)
            return
        task = tasks[tid]
        explicit = bool(re.search(r"(明确|决定|确认|已签收|更正|改由|重新开启|已完成|取消)", segment))
        if re.search(r"(验收单|交付确认记录|验收记录|签收记录)", segment) and re.search(r"(签收|确认|已交付|已验收|E-\d+)", segment):
            update(tid, "完成证据", f"{segment}（提交材料所称证据，未独立核验；{source}）", "证据确认完成", source)
            update(tid, "执行状态", "证据确认完成", "证据确认完成", source)
        elif re.search(r"已完成|完成了", segment):
            update(tid, "执行状态", "报告完成", "报告完成", source)
        elif re.search(r"重新开启|重开", segment):
            if explicit and not re.search(r"考虑|建议|拟", segment):
                update(tid, "执行状态", "待执行", "重新开启", source)
            else:
                ask(tid, "执行状态", segment, "仅为重开提议", source)
        elif re.search(r"取消", segment):
            if explicit and not re.search(r"考虑|建议|拟", segment):
                update(tid, "执行状态", "取消", "取消", source)
            else:
                ask(tid, "执行状态", segment, "仅为取消提议", source)
        elif re.search(r"进行中", segment):
            update(tid, "执行状态", "进行中", "进展", source)
        owner = re.search(r"(?:改由|由|建议由|建议)\s*([^，,。；;\s]{1,20}?(?:工|人|经理))\s*(?:确认接受|确认负责|负责|接手)?", segment)
        if owner:
            confirmed = bool(re.search(r"确认接受|确认负责|明确由|改由.*确认", segment)) or correction
            update(tid, "负责人", owner.group(1), "负责人变更", source, confirmed)
            if confirmed:
                task["负责人确认状态"] = "已确认"
            elif not task["负责人确认状态"]:
                task["负责人确认状态"] = "建议"
        if "明天" in segment or "下周" in segment or "尽快" in segment or "下阶段" in segment:
            if "明天" in segment and meeting_date:
                day = (date.fromisoformat(meeting_date) + timedelta(days=1)).isoformat()
                update(tid, "截止时间", day, "期限变更", source + f"（基准会议日 {meeting_date}，明天）")
                task["截止时间确认状态"] = "已确认"
            else:
                task["截止时间确认状态"] = "待确认"
                ask(tid, "截止时间", segment, "缺会议日或相对期限不唯一", source)
        else:
            match = re.search(r"(?:截止(?:日|时间)?|更正为|改到)\s*[：:]?\s*(\d{4}-\d{2}-\d{2})", segment)
            if match:
                day = iso(match.group(1))
                update(tid, "截止时间", day, "用户更正" if correction else "期限变更", source)
                task["截止时间确认状态"] = "已确认"

    for seg, src in statements(lines, meeting_file.name):
        apply(seg, src)
    supplements = []
    for path in (supplemental_evidence or []):
        if isinstance(path, Path) or isinstance(path, str) and Path(path).is_file():
            supplements.extend(statements(read_text(path), Path(path).name))
        else:
            supplements.extend(statements([(1, str(path))], "用户补充"))
    # Evaluate equal-authority contradictory assertions as a group, independent of upload order.
    claims = {}
    for seg, src in supplements:
        tid = locate(seg, src)
        if tid:
            status = "取消" if "取消" in seg else "进行中" if "进行中" in seg else None
            if status:
                claims.setdefault(tid, []).append((status, src, seg))
    conflicted = {tid for tid, entries in claims.items() if len({e[0] for e in entries}) > 1}
    for tid in sorted(conflicted):
        entries = sorted(claims[tid])
        detail = "；".join(f"{status} [{src}]" for status, src, _ in entries)
        event(tid, "冲突", tasks[tid]["执行状态"], detail, "；".join(src for _, src, _ in entries), conflict=True)
        ask(tid, "执行状态", detail, "同等权威来源相互矛盾，原确认值保留", "；".join(src for _, src, _ in entries))
    for seg, src in supplements:
        tid = locate(seg, src)
        if tid not in conflicted:
            apply(seg, src, evidence=True)
    for text in corrections or []:
        for seg, src in statements([(1, text)], "用户更正"):
            apply(seg, src, correction=True)
    for task in tasks.values():
        due = task["截止时间"]
        status = task["执行状态"]
        if status in {"取消", "证据确认完成"}:
            task["是否逾期"], task["逾期判断依据"] = "否", "任务已取消或证据确认完成，不列入逾期未完成"
        elif status == "报告完成":
            task["是否逾期"], task["逾期判断依据"] = "无法判断", "报告完成尚无验收证据"
        elif not check_date or not due or task["截止时间确认状态"] != "已确认":
            task["是否逾期"], task["逾期判断依据"] = "无法判断", "缺核查日或已确认截止日"
        elif timezone is None and ("时区" in full or "UTC" in full):
            task["是否逾期"], task["逾期判断依据"] = "无法判断", "涉及跨时区但未提供时区"
        else:
            task["是否逾期"], task["逾期判断依据"] = ("是" if iso(due) < check_date else "否"), f"截止日 {due}；核查日 {check_date}；时区 {timezone or '日期比较'}"
    change_count = len(changes)
    summary = f"本次对照会议记录，记录{change_count}项新增或变化；{len(questions)}处待确认。"
    if questions:
        summary += " 待确认事项包括：" + "；".join(q["待确认字段"] + "（" + q["原因"] + "）" for q in questions[:3]) + "。"
    if any(t["执行状态"] == "报告完成" for t in tasks.values()):
        summary += " 有任务仅报告完成，未提供可核验的验收凭据。"
    if not previous_tasks:
        summary += " 未提供旧任务表，本次为首版。"
    result = {"summary": summary, "tasks": tasks, "history": sorted(history_by_id.values(), key=lambda h: h["event_id"]),
              "changes": changes, "questions": questions}
    if draft_followup:
        result["followup_draft"] = "【草稿，未发送】请核实待确认事项及报告完成项的验收凭据，例会前反馈进展。"
    if response_mode == "one_sentence":
        return {"summary": f"本次记录{change_count}项变化、{len(questions)}处待确认，未提及的旧任务保持原状态。", "followup_draft": result.get("followup_draft", "")}
    if response_mode != "export":
        return result
    output = Path(output_dir or ".")
    if not output.is_dir() or output.is_symlink():
        raise InputError("OUTPUT_FAILED", "输出目录不存在或为符号链接，请换可写目录")
    target = output / f"{project_name}-任务跟踪.xlsx"
    summary_path = output / f"{project_name}-会议决议摘要.md"
    if any(target.resolve() == Path(p).resolve() or summary_path.resolve() == Path(p).resolve() for p in [meeting_file, previous_tasks, *(supplemental_evidence or [])] if p and Path(str(p)).is_file()):
        raise InputError("OUTPUT_FAILED", "输出路径与输入重合，拒绝覆盖")
    if target.exists() or summary_path.exists():
        raise InputError("OUTPUT_FAILED", "输出文件已存在；请使用新的隔离输出目录以免覆盖旧证据")
    tmp = []
    try:
        wb = Workbook()
        wb.remove(wb.active)
        for sheet, columns in SHEETS.items():
            ws = wb.create_sheet(sheet)
            ws.append(columns)
            items = ({"当前任务": sorted(tasks.values(), key=lambda t: t["task_id"]), "本次新增与变化": changes,
                      "待确认事项": questions, "状态历史": result["history"]})[sheet]
            for row in items:
                ws.append([safe_cell(row.get(c, "")) for c in columns])
        with tempfile.NamedTemporaryFile(dir=output, prefix=".mtg-", suffix=".xlsx", delete=False) as f:
            temp_x = Path(f.name)
        tmp.append(temp_x)
        wb.save(temp_x)
        reopened = load_workbook(temp_x, read_only=True, data_only=False)
        if reopened.sheetnames != list(SHEETS) or any([c.value for c in reopened[s][1]] != columns for s, columns in SHEETS.items()):
            raise InputError("OUTPUT_FAILED", "输出重开校验失败")
        reopened.close()
        with tempfile.NamedTemporaryFile(dir=output, prefix=".mtg-", suffix=".md", mode="w", encoding="utf-8", delete=False) as f:
            f.write(summary + "\n")
            temp_m = Path(f.name)
        tmp.append(temp_m)
        os.replace(temp_x, target)
        os.replace(temp_m, summary_path)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        target.unlink(missing_ok=True)
        raise InputError("OUTPUT_FAILED", "生成或校验失败，请检查输出目录与剩余空间") from exc
    finally:
        for p in tmp:
            p.unlink(missing_ok=True)
    result["xlsx"] = str(target)
    result["summary_file"] = str(summary_path)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="本地会议行动项合并；不会发送消息或访问网络")
    parser.add_argument("--meeting-file", required=True)
    parser.add_argument("--previous-tasks")
    parser.add_argument("--supplemental-evidence", action="append", default=[])
    parser.add_argument("--correction", action="append", default=[])
    parser.add_argument("--project-name", default="会议")
    parser.add_argument("--check-date")
    parser.add_argument("--timezone")
    parser.add_argument("--response-mode", choices=("export", "summary", "one_sentence"), default="export")
    parser.add_argument("--draft-followup", action="store_true")
    parser.add_argument("--output-dir")
    args = parser.parse_args(argv)
    try:
        result = reconcile(args.meeting_file, args.previous_tasks, args.supplemental_evidence, args.correction,
                           args.project_name, args.check_date, args.timezone, args.response_mode, args.draft_followup, args.output_dir)
        print(json.dumps({k: v for k, v in result.items() if k not in {"tasks", "history", "changes", "questions"}}, ensure_ascii=False))
        return 0
    except InputError as exc:
        print(json.dumps({"status": exc.code, "reason": str(exc), "recovery": "请核对输入格式、来源与输出目录后重试"}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
