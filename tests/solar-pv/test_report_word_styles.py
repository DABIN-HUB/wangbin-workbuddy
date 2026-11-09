"""R5 Word-only presentation contracts over two existing canonical cases."""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from docx import Document
from docx.oxml.ns import qn

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.report_export import ReportModel, _write_docx
from wangbin_solar_pv.report_word_styles import WORD_FORMAT
from wangbin_solar_pv.serialization import loads


CASES = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r1-full-cases"


@pytest.fixture(scope="module", params=("industrial_rooftop", "utility_scale_ground"))
def rendered(request):
    category = request.param
    canonical = CASES / category / "project/canonical.json"
    original_hash = sha256(canonical.read_bytes()).hexdigest()
    model = ReportModel.from_result(loads(canonical.read_bytes()), Catalog())
    with TemporaryDirectory(prefix="word-r5-", dir=os.getenv("TMPDIR")) as directory:
        target = Path(directory) / "report.docx"
        receipt = _write_docx(model, target, category, category)
        document = Document(target)
        assert sha256(canonical.read_bytes()).hexdigest() == original_hash
        assert receipt["chapter_items"] == 100 and receipt["appendix_items"] == 26
        yield model, document, receipt


def _fonts(style):
    fonts = style._element.xpath("./w:rPr/w:rFonts")
    assert len(fonts) == 1
    return fonts[0]


def test_report_word_styles(rendered):
    _, doc, _ = rendered
    assert WORD_FORMAT.identifier == "SOLAR_PV_WORD_FORMAT_V1"
    for section in doc.sections:
        assert abs(section.page_width.cm - 21) < .02
        assert abs(section.page_height.cm - 29.7) < .02
        assert abs(section.top_margin.cm - 2.5) < .02
        assert abs(section.bottom_margin.cm - 2.5) < .02
        assert abs(section.left_margin.cm - 3) < .02
        assert abs(section.right_margin.cm - 2) < .02
    for style_name, east, points, bold in (("Normal", "宋体", 12, False),
                                           ("Heading 1", "黑体", 16, False),
                                           ("Heading 2", "黑体", 14, False),
                                           ("Heading 3", "宋体", 12, True),
                                           ("Caption", "宋体", 10.5, False),
                                           ("Solar Table", "宋体", 10.5, False)):
        style = doc.styles[style_name]
        font = _fonts(style)
        assert font.get(qn("w:eastAsia")) == east
        assert font.get(qn("w:ascii")) == font.get(qn("w:hAnsi")) == "Times New Roman"
        assert style.font.size.pt == points and style.font.bold is bold
        assert str(style.font.color.rgb) == "000000"
    normal = doc.styles["Normal"].paragraph_format
    assert normal.first_line_indent.pt == 24
    assert normal.line_spacing == 1.5
    assert doc.styles["Solar Abstract"].paragraph_format.first_line_indent.pt == 0
    assert doc.styles["Solar Cover Title"].font.size.pt == 22
    assert doc.styles["Solar Cover Subtitle"].font.size.pt == 18
    assert doc.styles["Solar Contents Title"].font.size.pt == 18
    assert doc.styles["Solar Footer"].font.size.pt == 9
    assert any(p.style.name == "Solar Keywords" and p.text.startswith("关键词：") for p in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    assert para.style.name == "Solar Table"
                    for run in para.runs:
                        assert run.font.size.pt == 10.5
                        assert run._r.xpath("./w:rPr/w:rFonts")[0].get(qn("w:ascii")) == "Times New Roman"


def test_report_word_sections(rendered):
    _, doc, _ = rendered
    assert len(doc.sections) == 3
    assert not doc.sections[0].footer._element.xpath(".//w:fldSimple")
    assert not doc.sections[1].footer._element.xpath(".//w:fldSimple")
    assert doc.sections[2]._sectPr.xpath("./w:pgNumType/@w:start") == ["1"]
    assert [f.get(qn("w:instr")) for f in doc.sections[2].footer._element.xpath(".//w:fldSimple")] == ["PAGE"]
    headings = [p.text.split(" ", 1)[0] for p in doc.paragraphs if p.style.name == "Heading 1"]
    assert headings[:18] == [f"CH{i:02}" for i in range(1, 19)]
    assert [x for x in headings if x.startswith("APP")] == [f"APP{i:02}" for i in range(1, 14)]
    child = [p.text.split(" ", 1)[0] for p in doc.paragraphs if p.style.name == "Heading 2"]
    assert len([x for x in child if x.startswith("CH")]) == 100
    assert len([x for x in child if x.startswith("APP")]) == 26
    assert next(p for p in doc.paragraphs if p.text.startswith("CH02 ")).paragraph_format.page_break_before


def test_report_word_tables(rendered):
    _, doc, _ = rendered
    captions = [p.text for p in doc.paragraphs if p.style.name == "Caption" and p.text.startswith("表 ")]
    assert captions == [f"表 {i} {name.split(' ', 2)[2]}" for i, name in enumerate(captions, 1)]
    assert len(captions) == len(doc.tables)
    assert all(sum(col.width.cm for col in table.columns) <= 16.05 for table in doc.tables)
    for table in doc.tables:
        assert not table._tbl.xpath("./w:tblPr/w:tblStyle[@w:val='TableGrid']")
        edge = table._tbl.tblPr.xpath("./w:tblBorders")[0]
        assert [edge.find(qn("w:" + e)).get(qn("w:val")) for e in ("top", "bottom", "left", "right", "insideH", "insideV")] == ["single", "single", "nil", "nil", "nil", "nil"]
        assert all(c._tc.xpath("./w:tcPr/w:tcBorders/w:bottom/@w:sz") == ["6"] for c in table.rows[0].cells)
        assert table.rows[0]._tr.xpath("./w:trPr/w:tblHeader")
        assert all(row._tr.xpath("./w:trPr/w:cantSplit") for row in table.rows)
        assert not table._tbl.xpath(".//w:shd[@w:fill='1F2937']")


def test_report_word_toc(rendered):
    _, doc, _ = rendered
    field = doc._element.xpath(".//w:instrText")
    assert len(field) == 1 and field[0].text.startswith('TOC \\o "1-3"')
    assert doc.settings._element.xpath("./w:updateFields/@w:val") == ["true"]
    assert not any("章节索引（页码待" in p.text for p in doc.paragraphs)
    assert any(p.style.name == "Solar Contents Title" and p.text == "目录" for p in doc.paragraphs)


def test_report_word_formulas(rendered):
    model, doc, _ = rendered
    equations = [p for p in doc.paragraphs if p.style.name == "Solar Equation"]
    assert len(equations) == 89
    assert all("\t" in p.text and "（11-" in p.text for p in equations)
    assert any("F-" in p.text for p in doc.paragraphs if p.style.name == "Heading 3")
    assert len([p for p in doc.paragraphs if p.style.name == "Caption" and p.text.startswith("图 8.")]) == len(doc.inline_shapes)
    assert all(shape.width.cm <= 16.05 for shape in doc.inline_shapes)
    definitions = model.result["formula_snapshot"]
    expressions = [entry.get("text_equation") or entry.get("latex")
                   for section in definitions.values() if isinstance(section, dict)
                   for entry in section.values() if isinstance(entry, dict) and entry.get("formula_id")]
    text = "\n".join(p.text for p in equations)
    assert all(expr in text for expr in expressions if expr)
