"""Local candidate smoke verification; uses only fictional data in isolated scratch."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
PID = "wangbin-meeting-action-tracker"
ARCHIVE = ROOT / "dist" / f"{PID}-0.1.1-skill-candidate.zip"
EXPECTED = "5f5f0bc86ca469c89d758010194d8768e27badc96584791495e4b71c8ef745ae"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    manifest = json.loads(Path(str(ARCHIVE) + ".manifest.json").read_text(encoding="utf-8"))
    sidecar = Path(str(ARCHIVE) + ".sha256").read_text(encoding="utf-8").strip()
    catalog = next(item for item in json.loads((ROOT / "products/catalog.json").read_text(encoding="utf-8"))["products"] if item["id"] == PID)
    assert sha(ARCHIVE.read_bytes()) == manifest["sha256"] == EXPECTED
    assert sidecar == EXPECTED + "  " + ARCHIVE.name
    assert manifest["id"] == PID and manifest["version"] == catalog["active_version"] == "0.1.1"
    assert next(v["sha256"] for v in catalog["versions"] if v["version"] == "0.1.1") == EXPECTED
    assert catalog["status"] == "DEVELOPING" and catalog["review_status"] == "NOT_TESTED"
    members = {entry["path"]: entry for entry in manifest["members"]}
    assert len(members) == 3
    with zipfile.ZipFile(ARCHIVE) as archive:
        assert archive.testzip() is None and set(archive.namelist()) == set(members)
        for name, entry in members.items():
            data = archive.read(name)
            source = ROOT / "packages/skills" / PID / name.removeprefix(PID + "/")
            assert len(data) == entry["size"] and sha(data) == entry["sha256"]
            assert data == source.read_bytes()
        skill = archive.read(PID + "/SKILL.md").decode("utf-8")
        inner = json.loads(archive.read(PID + "/manifest.json"))
        assert inner["version"] == "0.1.1" and "version: 0.1.1" in skill
        with tempfile.TemporaryDirectory(prefix="meeting-t04-", dir=os.environ.get("TMPDIR")) as tmp:
            scratch = Path(tmp)
            archive.extractall(scratch / "extracted")
            meeting = scratch / "meeting.md"
            meeting.write_text("2026-11-06 蓝桥演练例会。T02 经会议明确取消，原因：模拟需求撤回。新增事项：检查演练接口 T03；建议由李工负责，尚未获其接受。", encoding="utf-8")
            previous = scratch / "previous.csv"
            columns = ["task_id", "任务内容", "负责人", "负责人确认状态", "截止时间", "截止时间确认状态", "执行状态", "完成证据", "是否逾期", "逾期判断依据", "来源", "最近变更"]
            with previous.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(columns)
                writer.writerow(["T01", "整理演练清单", "王工", "已确认", "2026-11-05", "已确认", "进行中", "", "", "", "old.csv:行2", ""])
                writer.writerow(["T02", "准备演练培训", "", "", "", "", "待执行", "", "", "", "old.csv:行3", ""])
            before = sha(previous.read_bytes())
            output = scratch / "out"
            output.mkdir()
            command = [sys.executable, str(scratch / "extracted" / PID / "scripts/track.py"), "--meeting-file", str(meeting), "--previous-tasks", str(previous), "--project-name", "蓝桥演练", "--response-mode", "export", "--output-dir", str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            assert result.returncode == 0, (command, result.stdout, result.stderr)
            response = json.loads(result.stdout)
            workbook = load_workbook(response["xlsx"], read_only=True, data_only=False)
            names = workbook.sheetnames
            assert names == ["当前任务", "本次新增与变化", "待确认事项", "状态历史"]
            sheets = {name: list(workbook[name].values) for name in names}
            workbook.close()
            tasks = {row["task_id"]: row for values in sheets["当前任务"][1:] for row in [dict(zip(sheets["当前任务"][0], values))]}
            events = [dict(zip(sheets["状态历史"][0], values)) for values in sheets["状态历史"][1:]]
            assert tasks["T02"]["执行状态"] == "取消" and tasks["T01"]["执行状态"] == "进行中"
            assert any(event["task_id"] == "T02" and event["事件类型"] == "取消" for event in events)
            assert sha(previous.read_bytes()) == before
            requirements = (ROOT / "docs/products" / PID / "requirements.md").read_text(encoding="utf-8")
            zh = ["对照上次任务表和这次会议记录，更新任务进展，没有提到的任务不要自动算完成。", "把这次会议新增的决议、负责人和截止时间整理出来，不明确的地方单独标记。", "这些是补充的完成记录，请更新任务表，并帮我写一段下一次例会前的跟进消息。"]
            en = ["Update the previous action list using these meeting notes. Do not mark unmentioned tasks as completed.", "Extract new decisions, owners, and deadlines, clearly marking anything not yet confirmed.", "Use these completion records to update the action list and draft a follow-up message before the next meeting."]
            assert all(text in skill and text in requirements for text in zh + en)
            print(json.dumps({"archive_sha256": EXPECTED, "members": members, "sidecar": "PASS", "source_bytes": "PASS", "zip_testzip": "PASS", "catalog": {key: catalog[key] for key in ("active_version", "status", "review_status")}, "cli_exit": result.returncode, "cli_args": ["--meeting-file", "meeting.md", "--previous-tasks", "previous.csv", "--project-name", "蓝桥演练", "--response-mode", "export", "--output-dir", "out"], "sheets": names, "rows": {name: len(rows) - 1 for name, rows in sheets.items()}, "T02": tasks["T02"]["执行状态"], "old_csv_unchanged": True, "recommendations_zh_en": "6/6 exact"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
