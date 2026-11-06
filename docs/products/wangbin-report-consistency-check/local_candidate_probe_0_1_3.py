"""T04 supplementary local packaging check; run only against the immutable QA-PASS archive.

uv run --no-project --with openpyxl --with python-docx python docs/products/wangbin-report-consistency-check/local_candidate_probe_0_1_3.py
All generated fictional inputs and output live in this worker's scratch directory.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from docx import Document
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[3]
ID = "wangbin-report-consistency-check"
VERSION = "0.1.3"
EXPECTED_SHA = "549111865465d3feb9faf5aaedf69738be6efd48094b1f61dd127e0b29ed9b38"
ARCHIVE = ROOT / "dist" / f"{ID}-{VERSION}-skill-candidate.zip"
SOURCE = ROOT / "packages" / "skills" / ID
SHEETS = ["核查概览", "指标对应", "差异明细", "待确认口径", "未覆盖项"]
PARAMETERS = ("--input-root", "--source-xlsx", "--report-docx", "--output-dir", "--context", "--prior-run")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_archive():
    data = ARCHIVE.read_bytes()
    assert sha(data) == EXPECTED_SHA, "the QA-approved archive was changed"
    manifest = json.loads(Path(str(ARCHIVE) + ".manifest.json").read_text(encoding="utf-8"))
    sidecar = Path(str(ARCHIVE) + ".sha256").read_text(encoding="utf-8").split()
    assert manifest["status"] == "PASS" and manifest["version"] == VERSION and manifest["id"] == ID
    assert manifest["sha256"] == EXPECTED_SHA and sidecar == [EXPECTED_SHA, ARCHIVE.name]
    catalog = json.loads((ROOT / "products/catalog.json").read_text(encoding="utf-8"))
    entries = [v for v in catalog["products"] if v["id"] == ID]
    assert len(entries) == 1
    entry = entries[0]
    versions = [v for v in entry["versions"] if v["version"] == VERSION]
    assert len(versions) == 1 and versions[0]["sha256"] == EXPECTED_SHA
    assert versions[0]["candidate"] == ARCHIVE.relative_to(ROOT).as_posix()
    assert entry["active_version"] == VERSION and entry["status"] != "PUBLISHED"
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        names = z.namelist()
        expected_names = [m["path"] for m in manifest["members"]]
        assert len(names) == len(set(names)) == len(expected_names) == 4
        assert sorted(names) == sorted(expected_names)
        for n in names:
            p = Path(n)
            assert not p.is_absolute() and ".." not in p.parts and p.parts[0] == ID
        for m in manifest["members"]:
            content = z.read(m["path"])
            source = SOURCE.joinpath(*Path(m["path"]).parts[1:])
            assert len(content) == m["size"]
            assert sha(content) == m["sha256"] == sha(source.read_bytes())
    return manifest


def verify_metadata():
    requirements = (ROOT / "docs/products" / ID / "requirements.md").read_text(encoding="utf-8")
    skill = (SOURCE / "SKILL.md").read_text(encoding="utf-8")
    expected_zh = [
        "这是月度经营报告和原始 Excel，帮我核对收入、成本和完成率，口径不同的先说明。",
        "检查报告里元和万元的换算，以及合计、占比有没有写错。",
        "我修改了原始数据，请重新检查报告，并说明相比上次新增或已经解决的问题。",
    ]
    expected_en = [
        "Check revenue, cost, and completion rates in this monthly report against the source Excel file, identifying definition differences first.",
        "Check currency-unit conversions, totals, and ratios in the report.",
        "I have updated the source data. Recheck the report and explain which issues are new, resolved, or still pending.",
    ]
    for language, lines in (("examples_zh", expected_zh), ("examples_en", expected_en)):
        block = skill.split(language + ":\n", 1)[1].split("\n" + ("examples_en" if language == "examples_zh" else "---") + ":" if language == "examples_zh" else "\n---", 1)[0]
        assert [line.strip()[2:] for line in block.splitlines() if line.strip().startswith("- ")] == lines
        assert all(text in requirements for text in lines)
    assert "version: " + VERSION in skill
    script = (SOURCE / "scripts/check_report.py").read_text(encoding="utf-8")
    assert "for arg in ('source-xlsx','report-docx','input-root','output-dir'):" in script
    assert "p.add_argument('--'+arg, required=True)" in script
    assert all("p.add_argument('" + name + "'" in script for name in PARAMETERS[-2:])
    assert all(name in skill for name in PARAMETERS)
    return {"recommendations_zh": expected_zh, "recommendations_en": expected_en, "parameters": list(PARAMETERS)}


def verify_clean_run():
    scratch = Path(os.environ["LOCALAPPDATA"]) / "hermes/profiles/wb-developer/cache/scratch"
    assert scratch.is_dir() and "scratch" in scratch.parts
    with tempfile.TemporaryDirectory(prefix="q05-t04-", dir=scratch) as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(ARCHIVE) as z:
            z.extractall(root / "extracted")
        extracted = root / "extracted" / ID
        for m in json.loads(Path(str(ARCHIVE) + ".manifest.json").read_text(encoding="utf-8"))["members"]:
            assert sha((extracted / Path(*Path(m["path"]).parts[1:])).read_bytes()) == m["sha256"]
        inputs, outputs = root / "input", root / "output"
        inputs.mkdir()
        outputs.mkdir()
        wb = Workbook()
        ws = wb.active
        assert ws is not None
        ws.title = "数据"
        ws["A1"], ws["B1"] = "项目", "青禾公司6月实际未税收入/CNY/元"
        ws["A2"], ws["B2"] = "虚构样本", 1280000
        xlsx = inputs / "source.xlsx"
        wb.save(xlsx)
        doc = Document()
        doc.add_paragraph("青禾公司6月实际未税收入125万元")
        docx = inputs / "report.docx"
        doc.save(str(docx))
        (inputs / "context.json").write_text('{"exact":true}', encoding="utf-8")
        before = {f.name: sha(f.read_bytes()) for f in inputs.iterdir()}
        command = [sys.executable, str(extracted / "scripts/check_report.py"), "--input-root", str(inputs), "--source-xlsx", str(xlsx), "--report-docx", str(docx), "--output-dir", str(outputs), "--context", str(inputs / "context.json")]
        proc = subprocess.run(command, capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, (proc.stdout, proc.stderr)
        result = json.loads(proc.stdout)
        assert result["status"] == "PARTIAL" and result["counts"].get("MISMATCH") == 1 and result["uncovered"] == 1, result
        out = Path(result["output"])
        assert out.parent == outputs and out.is_file() and Path(result["snapshot"]).is_file()
        reopened = load_workbook(out, data_only=False)
        assert reopened.sheetnames == SHEETS
        rows = {name: [list(r) for r in reopened[name].values] for name in SHEETS}
        assert all(rows[name] and rows[name][0] for name in SHEETS)
        assert all(cell.data_type != "f" for sheet in reopened for row in sheet for cell in row)
        detail = rows["差异明细"]
        assert len(detail) == 2 and detail[1][19] == "MISMATCH" and str(detail[1][20]) == "-30000", detail
        assert "数据!B2" in str(detail[1])
        assert before == {f.name: sha(f.read_bytes()) for f in inputs.iterdir()}
        assert len(list(outputs.iterdir())) == 2
        return {"cli_exit": proc.returncode, "cli_status": result["status"], "sheets": reopened.sheetnames, "detail_status": detail[1][19], "difference_report_minus_source_yuan": str(detail[1][20]), "source_cell": "数据!B2", "input_hashes_unchanged": True, "scratch_removed_after_run": True}


def main():
    manifest = verify_archive()
    static = verify_metadata()
    sample = verify_clean_run()
    print(json.dumps({"product_id": ID, "candidate": ARCHIVE.relative_to(ROOT).as_posix(), "candidate_sha256": EXPECTED_SHA, "manifest_snapshot_sha256": manifest["payload_snapshot_sha256"], "members": manifest["members"], "catalog_active_version": VERSION, "metadata": static, "sample": sample, "scope": "local packaging and fictional sample; no WorkBuddy/runtime/license/rights/platform approval"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
