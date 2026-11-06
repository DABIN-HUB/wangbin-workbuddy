"""Run packaged CLI in a clean isolated fictional workspace; reopen outputs."""
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

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "dist/wangbin-meeting-action-tracker-0.1.0-skill-candidate.zip"
with tempfile.TemporaryDirectory(prefix="mtg-candidate-", dir=os.environ.get("TMPDIR") or None) as tmp:
    folder = Path(tmp)
    with zipfile.ZipFile(ARCHIVE) as z:
        z.extractall(folder / "extracted")
    notes = folder / "fictional.md"
    notes.write_text("2026-11-06 蓝桥演练例会。T02 经会议明确取消。新增事项：检查演练接口 T03；建议由李工负责，尚未获其接受。", encoding="utf-8")
    old = folder / "fictional.csv"
    with old.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["task_id", "任务内容", "执行状态", "来源"])
        w.writeheader()
        w.writerows([{"task_id": "T01", "任务内容": "整理演练清单", "执行状态": "进行中", "来源": "old:2"},
                     {"task_id": "T02", "任务内容": "准备演练培训", "执行状态": "待执行", "来源": "old:3"}])
    original = hashlib.sha256(old.read_bytes()).hexdigest()
    output = folder / "output"
    output.mkdir()
    cli = folder / "extracted/wangbin-meeting-action-tracker/scripts/track.py"
    result = subprocess.run([sys.executable, str(cli), "--meeting-file", str(notes), "--previous-tasks", str(old),
                             "--project-name", "蓝桥演练", "--output-dir", str(output)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    info = json.loads(result.stdout)
    wb = load_workbook(info["xlsx"], read_only=False)
    assert wb.sheetnames == ["当前任务", "本次新增与变化", "待确认事项", "状态历史"]
    rows = {row[0]: row for row in list(wb["当前任务"].values)[1:]}
    assert rows["T01"][6] == "进行中" and rows["T01"][11] == "无新增进展"
    assert rows["T02"][6] == "取消"
    assert len(rows) == 3
    assert hashlib.sha256(old.read_bytes()).hexdigest() == original
    assert Path(info["summary_file"]).read_text(encoding="utf-8").strip()
    print(json.dumps({"status": "PASS", "cli_exit": result.returncode, "archive_sha256": hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
                      "sheets": wb.sheetnames, "rows": len(rows), "old_sha256_unchanged": True, "summary": info["summary"]}, ensure_ascii=False))
    wb.close()
