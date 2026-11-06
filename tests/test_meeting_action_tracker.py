"""Focused fictional MTG-CORE/A02-A14 and safety regression checks."""
import csv
import importlib.util
from pathlib import Path

import pytest
from docx import Document
from openpyxl import Workbook, load_workbook

SOURCE = Path(__file__).resolve().parents[1] / "packages/skills/wangbin-meeting-action-tracker/scripts/track.py"
spec = importlib.util.spec_from_file_location("meeting_tracker", SOURCE)
tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker)


def notes(tmp_path, text, suffix=".md"):
    p = tmp_path / ("meeting" + suffix)
    if suffix == ".docx":
        doc = Document()
        doc.add_paragraph(text)
        doc.save(p)
    else:
        p.write_text(text, encoding="utf-8")
    return p


def old(tmp_path, rows=None, suffix=".csv"):
    p = tmp_path / ("old" + suffix)
    rows = rows or [{"task_id": "T01", "任务内容": "整理演练清单", "执行状态": "进行中", "负责人": "王工", "负责人确认状态": "已确认", "截止时间": "2026-11-05", "截止时间确认状态": "已确认", "来源": "old.csv:行2"},
                    {"task_id": "T02", "任务内容": "准备演练培训", "执行状态": "待执行", "来源": "old.csv:行3"}]
    if suffix == ".csv":
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "当前任务"
        ws.append(list(rows[0]))
        for row in rows:
            ws.append(list(row.values()))
        wb.save(p)
    return p


def run(tmp_path, text, previous=None, **kw):
    return tracker.reconcile(notes(tmp_path, text), previous, project_name="蓝桥演练", response_mode="summary", **kw)


def test_core(tmp_path):
    r = run(tmp_path, "2026-11-06 蓝桥演练例会。T02 经会议明确取消。新增事项：检查演练接口 T03；建议由李工负责，尚未获其接受。", old(tmp_path))
    assert r["tasks"]["T01"]["执行状态"] == "进行中"
    assert r["tasks"]["T01"]["最近变更"] == "无新增进展"
    assert r["tasks"]["T02"]["执行状态"] == "取消"
    assert not any(h["task_id"] == "T01" and "完成" in h["事件类型"] for h in r["history"])
    assert any(t["负责人确认状态"] == "建议" for t in r["tasks"].values())


def test_explicit_cancel_with_simulation_reason_and_unaccepted_owner(tmp_path):
    r = run(tmp_path, "2026-11-06 蓝桥演练例会。T02 经会议明确取消，原因：模拟需求撤回。新增事项：检查演练接口 T03；建议由李工负责，尚未获其接受。", old(tmp_path), check_date="2026-11-07")
    assert r["tasks"]["T02"]["执行状态"] == "取消"
    assert r["tasks"]["T02"]["是否逾期"] == "否"
    assert sum(h["task_id"] == "T02" and h["事件类型"] == "取消" for h in r["history"]) == 1
    assert not any(q["task_id"] == "T02" and q["待确认字段"] == "执行状态" for q in r["questions"])
    assert any(q["待确认字段"] == "负责人" for q in r["questions"])


@pytest.mark.parametrize("phrase", ["拟取消", "考虑取消", "建议取消", "建议将 T02 取消"])
def test_cancel_proposal_remains_pending(tmp_path, phrase):
    r = run(tmp_path, f"T02 会议{phrase}。", old(tmp_path))
    assert r["tasks"]["T02"]["执行状态"] == "待执行"
    assert not any(h["task_id"] == "T02" and h["事件类型"] == "取消" for h in r["history"])
    assert any(q["task_id"] == "T02" and q["待确认字段"] == "执行状态" for q in r["questions"])


def test_reopen_proposal_and_simulation_reason(tmp_path):
    p = old(tmp_path, [{"task_id": "T02", "任务内容": "准备演练培训", "执行状态": "取消"}])
    proposed = run(tmp_path, "T02 拟重开。", p)
    assert proposed["tasks"]["T02"]["执行状态"] == "取消"
    assert any(q["待确认字段"] == "执行状态" for q in proposed["questions"])
    decided = run(tmp_path, "T02 明确重新开启，原因：模拟演练恢复。", p)
    assert decided["tasks"]["T02"]["执行状态"] == "待执行"


def test_a02_a03_stable_repeat_and_reorder(tmp_path):
    p = notes(tmp_path, "2026-11-06 决定新增：编写演练纪要，由周工确认负责。决定新增：检查演练接口 B。")
    first = tracker.reconcile(p, project_name="蓝桥演练", output_dir=tmp_path)
    ids = set(first["tasks"])
    p.write_text("决定新增：检查演练接口 B。2026-11-06 决定新增：编写演练纪要，由周工确认负责。", encoding="utf-8")
    second = tracker.reconcile(p, first["xlsx"], project_name="蓝桥演练", response_mode="summary")
    assert set(second["tasks"]) == ids
    assert {h["event_id"] for h in first["history"]} == {h["event_id"] for h in second["history"]}
    assert any(t["负责人确认状态"] == "已确认" for t in first["tasks"].values())


def test_a04_a05_matching_owner(tmp_path):
    p = old(tmp_path, [{"task_id":"T01", "任务内容":"检查演练接口 A", "执行状态":"待执行", "负责人":"王工", "负责人确认状态":"已确认"}])
    r = run(tmp_path, "检查演练接口 A 现改由周工负责，周工确认接受 T01。决定新增：检查演练接口 B。", p)
    assert len(r["tasks"]) == 2
    assert r["tasks"]["T01"]["负责人"] == "周工"
    assert any(h["原值"] == "王工" and h["新值"] == "周工" for h in r["history"])


@pytest.mark.parametrize("date_prefix,expected", [("2026-11-06 例会。", "2026-11-07"), ("", "2026-11-05")])
def test_a06_a07_dates(tmp_path, date_prefix, expected):
    r = run(tmp_path, date_prefix + "T01 明天交。", old(tmp_path))
    assert r["tasks"]["T01"]["截止时间"] == expected
    if not date_prefix:
        assert any(q["待确认字段"] == "截止时间" for q in r["questions"])


def test_a08_a13_report_evidence_isolation(tmp_path):
    p = old(tmp_path)
    first = run(tmp_path, "T02 已完成。", p)
    assert first["tasks"]["T02"]["执行状态"] == "报告完成"
    assert not first["tasks"]["T02"]["完成证据"]
    second = run(tmp_path, "其他事项暂不更新。", p, supplemental_evidence=["T02 交付确认记录 E-9 已签收"])
    assert second["tasks"]["T02"]["执行状态"] == "证据确认完成"
    assert second["tasks"]["T01"]["执行状态"] == "进行中"
    assert second["tasks"]["T01"]["最近变更"] == "无新增进展"


def test_a09_conflict_order_independence(tmp_path):
    p = old(tmp_path)
    a = run(tmp_path, "例会记录。", p, supplemental_evidence=["T01 进行中", "T01 决定取消"])
    b = run(tmp_path, "例会记录。", p, supplemental_evidence=["T01 决定取消", "T01 进行中"])
    assert a["tasks"]["T01"]["执行状态"] == b["tasks"]["T01"]["执行状态"] == "进行中"
    assert [h["event_id"] for h in a["history"]] == [h["event_id"] for h in b["history"]]
    assert any(h["是否存在冲突"] == "是" for h in a["history"])
    assert a["questions"]


def test_a10_cancel_reopen(tmp_path):
    p = old(tmp_path)
    r = run(tmp_path, "会议决定取消 T02。会议决定重新开启 T02。", p)
    assert r["tasks"]["T02"]["执行状态"] == "待执行"
    assert {h["事件类型"] for h in r["history"]} >= {"取消", "重新开启"}
    proposed = run(tmp_path, "会议决定取消 T02。考虑重开 T02。", p)
    assert proposed["tasks"]["T02"]["执行状态"] == "取消"


def test_a11_overdue(tmp_path):
    p = old(tmp_path)
    r = run(tmp_path, "本次无任务变更。", p)
    assert r["tasks"]["T01"]["是否逾期"] == "无法判断"
    r = run(tmp_path, "本次无任务变更。", p, check_date="2026-11-06")
    assert r["tasks"]["T01"]["是否逾期"] == "是"
    r = run(tmp_path, "会议决定取消 T01。", p, check_date="2026-11-06")
    assert r["tasks"]["T01"]["是否逾期"] == "否"


def test_a12_concise(tmp_path):
    r = tracker.reconcile(notes(tmp_path, "会议决定取消 T02。"), old(tmp_path), response_mode="one_sentence")
    assert set(r) == {"summary", "followup_draft"}
    assert r["summary"].count("。") == 1


def test_a14_failure_preserves_output(tmp_path):
    p = old(tmp_path)
    existing = tmp_path / "existing.xlsx"
    existing.write_bytes(b"preserve")
    bad = notes(tmp_path, "not zip", ".docx") if False else tmp_path / "bad.docx"
    bad.write_text("not zip", encoding="utf-8")
    with pytest.raises(tracker.InputError) as e:
        tracker.reconcile(bad, p, output_dir=tmp_path)
    assert e.value.code == "CORRUPT_INPUT"
    assert existing.read_bytes() == b"preserve"
    with pytest.raises(tracker.InputError) as e:
        tracker.reconcile(notes(tmp_path, "hello", ".exe"), p)
    assert e.value.code == "INVALID_FORMAT"


def test_export_docx_xlsx_and_formula(tmp_path):
    p = old(tmp_path, suffix=".xlsx")
    m = notes(tmp_path, "2026-11-06 例会。决定新增：=HYPERLINK(\"evil\")。T02 已完成。", ".docx")
    before = p.read_bytes()
    r = tracker.reconcile(m, p, project_name="蓝桥演练", output_dir=tmp_path, draft_followup=True)
    wb = load_workbook(r["xlsx"])
    assert wb.sheetnames == list(tracker.SHEETS)
    assert all([c.value for c in wb[s][1]] == columns for s, columns in tracker.SHEETS.items())
    assert all(c.data_type != "f" for ws in wb for row in ws for c in row)
    assert "未发送" in r["followup_draft"]
    assert p.read_bytes() == before
    assert Path(r["summary_file"]).read_text(encoding="utf-8")
    wb.close()


def test_errors_and_corrections(tmp_path):
    p = old(tmp_path)
    r = run(tmp_path, "无变化。", p, corrections=["将 T01 截止日更正为 2026-11-10"])
    assert r["tasks"]["T01"]["截止时间"] == "2026-11-10"
    with pytest.raises(tracker.InputError) as e:
        run(tmp_path, "内容。", p, check_date="2026-02-30")
    assert e.value.code == "INVALID_DATE"
    with pytest.raises(tracker.InputError) as e:
        run(tmp_path, "内容。", old(tmp_path, [{"task_id":"A", "任务内容":"one", "执行状态":"待执行"}, {"task_id":"A", "任务内容":"two", "执行状态":"进行中"}]))
    assert e.value.code == "DUPLICATE_TASK_ID"


def test_two_round_history_and_atomic_existing(tmp_path):
    old_file = old(tmp_path)
    meeting = notes(tmp_path, "T02 已完成。")
    first_dir = tmp_path / "first"
    first_dir.mkdir()
    first = tracker.reconcile(meeting, old_file, project_name="演练", output_dir=first_dir)
    old_bytes = Path(first["xlsx"]).read_bytes()
    meeting.write_text("本轮记录没有其他任务变化。", encoding="utf-8")
    second = tracker.reconcile(meeting, first["xlsx"], supplemental_evidence=["T02 交付确认记录 E-7 已签收"],
                               response_mode="summary")
    assert second["tasks"]["T02"]["执行状态"] == "证据确认完成"
    assert {"报告完成", "证据确认完成"}.issubset({h["事件类型"] for h in second["history"]})
    assert Path(first["xlsx"]).read_bytes() == old_bytes
    with pytest.raises(tracker.InputError) as exc:
        tracker.reconcile(meeting, first["xlsx"], project_name="演练", output_dir=first_dir)
    assert exc.value.code == "OUTPUT_FAILED"
    assert Path(first["xlsx"]).read_bytes() == old_bytes
