"""R5 Word-only presentation contracts over two existing canonical cases."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from docx import Document
from docx.oxml.ns import qn

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.report_export import APPENDICES, CHAPTERS, ReportModel, _appendix_formula_definitions, _write_docx
from wangbin_solar_pv.report_claims import APPENDIX_TITLES
from wangbin_solar_pv.report_numbering import heading_number, nested_number, validate_numbering
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


def _page_boundary_between(paragraphs, start_index, end_index):
    """Return whether a Word page/section boundary separates two paragraphs."""
    for paragraph in paragraphs[start_index:end_index]:
        if paragraph._p.xpath(".//w:br[@w:type='page']"):
            return True
        if paragraph._p.xpath(".//w:sectPr"):
            return True
    return False


def _contents_layout(document):
    paragraphs = document.paragraphs
    contents_index = next(i for i, paragraph in enumerate(paragraphs)
                          if paragraph.style.name == "Solar Contents Title"
                          and paragraph.text == "目录")
    keyword_index = next(i for i, paragraph in enumerate(paragraphs)
                         if paragraph.style.name == "Solar Keywords"
                         and paragraph.text.startswith("关键词："))
    first_heading_index = next(i for i, paragraph in enumerate(paragraphs)
                               if paragraph.style.name == "Heading 1"
                               and paragraph.text == heading_number("CH01", "执行摘要与初步结论").text)
    first_toc_index = next((i for i in range(contents_index + 1, first_heading_index)
                            if paragraphs[i].style.name.lower().startswith("toc ")
                            or paragraphs[i].text.startswith("一、")), None)
    return paragraphs, keyword_index, contents_index, first_toc_index, first_heading_index


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
    headings = [p.text for p in doc.paragraphs if p.style.name == "Heading 1"]
    assert len(headings) == 31
    assert headings[0].startswith("一、") and headings[17].startswith("十八、")
    assert [x.split(" ", 1)[0] for x in headings[18:]] == [f"附录{chr(65 + i)}" for i in range(13)]
    child = [p.text for p in doc.paragraphs if p.style.name == "Heading 2"]
    assert len(child) == 126
    assert next(p for p in doc.paragraphs if p.text.startswith("二、")).paragraph_format.page_break_before


def test_report_word_tables(rendered):
    _, doc, _ = rendered
    captions = [p.text for p in doc.paragraphs if p.style.name == "Caption" and p.text.startswith("表")]
    assert captions == [f"表{i} {name.split(' ', 1)[1]}" for i, name in enumerate(captions, 1)]
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


def test_report_word_front_matter_and_contents_boundary(rendered):
    _, doc, _ = rendered
    paragraphs, keyword_index, contents_index, first_toc_index, first_heading_index = _contents_layout(doc)

    # The cover has its own section; abstract/keywords precede the contents,
    # and the body has a separate section after the contents field.
    assert len(doc.sections) == 3
    assert any(paragraph._p.xpath(".//w:sectPr")
               for paragraph in paragraphs[:next(i for i, p in enumerate(paragraphs)
                                                 if p.style.name == "Solar Abstract Title")])
    assert keyword_index < contents_index < first_heading_index
    assert first_toc_index is not None
    assert first_toc_index > contents_index
    assert _page_boundary_between(paragraphs, keyword_index + 1, contents_index)
    assert _page_boundary_between(paragraphs, first_toc_index + 1, first_heading_index)


def test_report_word_contents_boundary_negative_control(rendered):
    _, doc, _ = rendered
    paragraphs, keyword_index, contents_index, _, _ = _contents_layout(doc)
    page_break = next(paragraph for paragraph in paragraphs[keyword_index + 1:contents_index]
                      if paragraph._p.xpath(".//w:br[@w:type='page']"))
    for node in page_break._p.xpath(".//w:br[@w:type='page']"):
        node.getparent().remove(node)
    assert not _page_boundary_between(paragraphs, keyword_index + 1, contents_index)


def test_report_word_formulas(rendered):
    model, doc, _ = rendered
    equations = [p for p in doc.paragraphs if p.style.name == "Solar Equation"]
    assert len(equations) == 89
    assert [p.text.split("\t")[-1] for p in equations] == [f"（{i}）" for i in range(1, 90)]
    assert any("F-" in p.text for p in doc.paragraphs if p.style.name == "Solar Formula Title")
    assert len([p for p in doc.paragraphs if p.style.name == "Caption" and p.text.startswith("图")]) == len(doc.inline_shapes)
    assert all(shape.width.cm <= 16.05 for shape in doc.inline_shapes)
    definitions = model.result["formula_snapshot"]
    expressions = [entry.get("text_equation") or entry.get("latex")
                   for section in definitions.values() if isinstance(section, dict)
                   for entry in section.values() if isinstance(entry, dict) and entry.get("formula_id")]
    text = "\n".join(p.text for p in equations)
    assert all(expr in text for expr in expressions if expr)


def _check_numbering(model, document):
    return validate_numbering(document, CHAPTERS, APPENDICES, APPENDIX_TITLES,
                              [entry["formula_id"] for entry in _appendix_formula_definitions(model)])


def test_all_frozen_ids_have_distinct_visible_numbers_and_bookmarks(rendered):
    model, document, receipt = rendered
    counts = _check_numbering(model, document)
    assert counts == receipt["numbering"]
    assert counts["chapters"] == 18 and counts["body_items"] == 100
    assert counts["appendices"] == 13 and counts["appendix_items"] == 26
    assert counts["formulas"] == 89
    assert document._element.xpath(".//w:bookmarkStart[@w:name='PV_CH01_01']")
    assert document._element.xpath(".//w:bookmarkStart[@w:name='PV_APP13_02']")
    assert not any(p.style.name.startswith("Heading") for p in document.paragraphs
                   if p.text in ("结果与公式索引", "发电量变化", "术语与公式说明"))
    assert [p.text for p in document.paragraphs if p.style.name == "Heading 2"][:5] == [
        heading_number(f"CH01.{i:02d}", title, parent_stable_id="CH01", parent_level=1).text
        for i, title in enumerate(CHAPTERS[0][2], 1)]
    for paragraph in document.paragraphs:
        if paragraph.style.name in ("Heading 1", "Heading 2"):
            fmt = paragraph.paragraph_format
            assert fmt.left_indent.pt > 0
            assert fmt.first_line_indent.pt == -fmt.left_indent.pt
    assert next(p for p in document.paragraphs if p.text.startswith("十八、")).paragraph_format.left_indent.pt == 48
    assert [nested_number(1, level=3, parent_level=2),
            nested_number(1, level=4, parent_level=3),
            nested_number(1, level=5, parent_level=4)] == ["1.", "（1）", "①"]
    with pytest.raises(ValueError):
        nested_number(1, level=4, parent_level=1)


@pytest.mark.parametrize("replacement", ("（一）、项目识别及方案版本", "1、项目识别及方案版本",
                                            "一.项目识别及方案版本", "（二）项目识别及方案版本"))
def test_numbering_rejects_malformed_or_duplicate_headings(rendered, replacement):
    model, document, _ = rendered
    stream = BytesIO()
    document.save(stream)
    stream.seek(0)
    corrupted = Document(stream)
    next(p for p in corrupted.paragraphs if p.style.name == "Heading 2").text = replacement
    with pytest.raises(ValueError, match="heading"):
        _check_numbering(model, corrupted)


def test_numbering_rejects_missing_parent_repeated_table_and_figure_caption(rendered):
    model, document, _ = rendered
    with pytest.raises(ValueError):
        heading_number("CH01.01", "项目识别", parent_stable_id="CH02", parent_level=1)
    for kind in ("表", "图"):
        stream = BytesIO()
        document.save(stream)
        stream.seek(0)
        corrupted = Document(stream)
        captions = [p for p in corrupted.paragraphs if p.style.name == "Caption" and p.text.startswith(kind)]
        captions[1].text = captions[0].text
        with pytest.raises(ValueError, match=kind):
            _check_numbering(model, corrupted)


def test_numbering_does_not_rewrite_numeric_body_content(rendered):
    _, document, _ = rendered
    body = "\n".join(p.text for p in document.paragraphs)
    assert "DC/AC" in body and "F-NPV" in body
    assert not any(p.style.name in ("Heading 1", "Heading 2") and
                   p.text.startswith(("CH", "APP")) for p in document.paragraphs)


def test_numbering_rejects_figure_reference_without_target(rendered):
    model, document, _ = rendered
    stream = BytesIO()
    document.save(stream)
    stream.seek(0)
    corrupted = Document(stream)
    corrupted.add_paragraph("参见图999。")
    with pytest.raises(ValueError, match="图 reference"):
        _check_numbering(model, corrupted)
