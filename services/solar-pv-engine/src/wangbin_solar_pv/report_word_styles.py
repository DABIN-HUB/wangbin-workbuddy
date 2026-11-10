"""Shared, presentation-only Word profile for solar PV reports.

All dimensions are Word points or centimetres; no calculation data lives here.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.run import Run


@dataclass(frozen=True)
class SolarWordFormat:
    identifier: str = "SOLAR_PV_WORD_FORMAT_V1"
    chinese: str = "宋体"
    heading_chinese: str = "黑体"
    western: str = "Times New Roman"
    ink: str = "000000"
    page_width_cm: float = 21
    page_height_cm: float = 29.7
    top_cm: float = 2.5
    bottom_cm: float = 2.5
    left_cm: float = 3
    right_cm: float = 2
    body_pt: float = 12
    table_pt: float = 10.5
    foot_pt: float = 9
    body_line_spacing: float = 1.5
    contents_line_spacing: float = 1.25
    table_top_bottom_eighth_pt: int = 12
    table_header_eighth_pt: int = 6

    @property
    def text_width_cm(self) -> float:
        return self.page_width_cm - self.left_cm - self.right_cm


WORD_FORMAT = SolarWordFormat()


def font_pair(font, rpr, *, chinese: str, western: str, size: float, bold: bool | None = None) -> None:
    """Set all three OOXML font families rather than relying on font.name."""
    font.name = western
    font.size = Pt(size)
    font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        font.bold = bold
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for slot, family in (("eastAsia", chinese), ("ascii", western), ("hAnsi", western),
                         ("cs", western)):
        rfonts.set(qn("w:" + slot), family)
    for slot in ("eastAsiaTheme", "asciiTheme", "hAnsiTheme", "cstheme"):
        rfonts.attrib.pop(qn("w:" + slot), None)


def set_run_font(run, *, chinese: str = "宋体", size: float = 12,
                 bold: bool | None = None) -> None:
    font_pair(run.font, run._r.get_or_add_rPr(), chinese=chinese,
              western=WORD_FORMAT.western, size=size, bold=bold)


def render_script_o_glyph(document) -> None:
    """Use a real math-capable font for the frozen script-O *text* in WPS.

    Keep every original Unicode character in its Word run. Substituting an
    ASCII O or editing the formula registry would change the source meaning.
    """
    paragraphs = list(document.paragraphs)
    paragraphs.extend(paragraph for table in document.tables for row in table.rows
                      for cell in row.cells for paragraph in cell.paragraphs)
    seen = set()
    for paragraph in paragraphs:
        if paragraph._p in seen:
            continue
        seen.add(paragraph._p)
        for run in tuple(paragraph.runs):
            if "𝒪" not in run.text:
                continue
            parts = run.text.split("𝒪")
            run.text = parts[0]
            previous = run._r
            for suffix in parts[1:]:
                glyph = Run(deepcopy(run._r), paragraph)
                glyph.text = "𝒪"
                font_pair(glyph.font, glyph._r.get_or_add_rPr(),
                          chinese=WORD_FORMAT.chinese, western="Cambria Math",
                          size=run.font.size.pt if run.font.size else WORD_FORMAT.body_pt)
                previous.addnext(glyph._r)
                previous = glyph._r
                if suffix:
                    remaining = Run(deepcopy(run._r), paragraph)
                    remaining.text = suffix
                    previous.addnext(remaining._r)
                    previous = remaining._r


def _style(document, name: str, *, size: float, chinese: str = "宋体",
           bold: bool = False, alignment=None, before: float = 0,
           after: float = 0, spacing: float = 1.0, indent: float = 0,
           keep_next: bool = False):
    styles = document.styles
    style = styles[name] if name in styles else styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.base_style = styles["Normal"] if name != "Normal" else None
    font_pair(style.font, style._element.get_or_add_rPr(), chinese=chinese,
              western=WORD_FORMAT.western, size=size, bold=bold)
    pf = style.paragraph_format
    pf.alignment = alignment
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = spacing
    pf.first_line_indent = Pt(indent)
    pf.keep_with_next = keep_next
    pf.widow_control = True
    return style


def configure(document, profile: SolarWordFormat = WORD_FORMAT) -> None:
    _style(document, "Normal", size=profile.body_pt, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
           spacing=profile.body_line_spacing, indent=profile.body_pt * 2)
    for name, size, chinese, bold, before, after in (
        ("Heading 1", 16, profile.heading_chinese, False, 8, 8),
        ("Heading 2", 14, profile.heading_chinese, False, 7, 7),
        ("Heading 3", 12, profile.chinese, True, 0, 0),
        ("Heading 4", 12, profile.chinese, False, 0, 0),
        ("Heading 5", 12, profile.chinese, False, 0, 0),
    ):
        _style(document, name, size=size, chinese=chinese, bold=bold,
               alignment=WD_ALIGN_PARAGRAPH.LEFT, before=before, after=after,
               spacing=1.5, keep_next=True)
    _style(document, "Solar Figure Group", size=14, chinese=profile.heading_chinese,
           alignment=WD_ALIGN_PARAGRAPH.LEFT, before=7, after=7, keep_next=True)
    _style(document, "Solar Formula Title", size=12, chinese=profile.chinese,
           bold=True, alignment=WD_ALIGN_PARAGRAPH.LEFT, keep_next=True)
    _style(document, "Solar Unnumbered Title", size=16, chinese=profile.heading_chinese,
           alignment=WD_ALIGN_PARAGRAPH.LEFT, before=8, after=8, keep_next=True)
    _style(document, "Solar Cover Title", size=22, chinese=profile.heading_chinese,
           bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, before=25, after=15)
    _style(document, "Solar Cover Subtitle", size=18, alignment=WD_ALIGN_PARAGRAPH.CENTER,
           before=8, after=14)
    _style(document, "Solar Cover Info", size=14, alignment=WD_ALIGN_PARAGRAPH.CENTER,
           before=6, after=6)
    _style(document, "Solar Abstract Title", size=15, chinese=profile.heading_chinese,
           bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, before=8, after=8, keep_next=True)
    _style(document, "Solar Abstract", size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT,
           before=6, after=6, spacing=1.5)
    _style(document, "Solar Keywords", size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT,
           before=0, after=8)
    _style(document, "Solar Contents Title", size=18, chinese=profile.heading_chinese,
           alignment=WD_ALIGN_PARAGRAPH.CENTER, before=12, after=12, keep_next=True)
    for level in range(1, 4):
        # Word consumes TOC 1; WPS writes cached entries using lowercase toc 1.
        # Configure both so a refreshed document retains the same font/spacing.
        for name in (f"TOC {level}", f"toc {level}"):
            _style(document, name, size=12, bold=level == 1,
                   alignment=WD_ALIGN_PARAGRAPH.LEFT, spacing=profile.contents_line_spacing)
    _style(document, "Caption", size=10.5, alignment=WD_ALIGN_PARAGRAPH.CENTER,
           before=6, after=6, keep_next=True)
    _style(document, "Solar Table", size=profile.table_pt, spacing=1.0)
    _style(document, "Solar Equation", size=profile.body_pt,
           alignment=WD_ALIGN_PARAGRAPH.CENTER, before=6, after=6)
    _style(document, "Solar Formula Note", size=profile.body_pt,
           alignment=WD_ALIGN_PARAGRAPH.LEFT)
    _style(document, "Solar Footer", size=profile.foot_pt,
           alignment=WD_ALIGN_PARAGRAPH.CENTER)
    _style(document, "Solar Header", size=profile.foot_pt,
           alignment=WD_ALIGN_PARAGRAPH.RIGHT)
    _style(document, "Solar References Title", size=18, chinese=profile.heading_chinese,
           alignment=WD_ALIGN_PARAGRAPH.CENTER, keep_next=True)
    _style(document, "Solar Reference", size=10.5, spacing=1.0, indent=-21)
    document.styles["Solar Reference"].paragraph_format.left_indent = Pt(21)
    document.styles["Solar Reference"].paragraph_format.line_spacing = Pt(18)
    for section in document.sections:
        section.page_width = Cm(profile.page_width_cm)
        section.page_height = Cm(profile.page_height_cm)
        section.top_margin = Cm(profile.top_cm)
        section.bottom_margin = Cm(profile.bottom_cm)
        section.left_margin = Cm(profile.left_cm)
        section.right_margin = Cm(profile.right_cm)
        section.header_distance = Cm(1.2)
        section.footer_distance = Cm(1.2)


def borders(table, profile: SolarWordFormat = WORD_FORMAT) -> None:
    """Explicit three rules, no inherited grid or vertical/cell rules."""
    tblpr = table._tbl.tblPr
    previous = tblpr.find(qn("w:tblBorders"))
    if previous is not None:
        tblpr.remove(previous)
    edges = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "left", "right", "insideH", "insideV"):
        node = OxmlElement("w:" + edge)
        node.set(qn("w:val"), "single" if edge in ("top", "bottom") else "nil")
        if edge in ("top", "bottom"):
            node.set(qn("w:sz"), str(profile.table_top_bottom_eighth_pt))
            node.set(qn("w:color"), profile.ink)
        edges.append(node)
    tblpr.append(edges)
    for cell in table.rows[0].cells:
        tcpr = cell._tc.get_or_add_tcPr()
        previous = tcpr.find(qn("w:tcBorders"))
        if previous is not None:
            tcpr.remove(previous)
        cell_edges = OxmlElement("w:tcBorders")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), str(profile.table_header_eighth_pt))
        bottom.set(qn("w:color"), profile.ink)
        cell_edges.append(bottom)
        tcpr.append(cell_edges)


def equation_paragraph(document, math, number: str):
    """Editable Office Math expression, centered with a right-aligned number."""
    paragraph = document.add_paragraph(style="Solar Equation")
    stops = paragraph.paragraph_format.tab_stops
    stops.add_tab_stop(Cm(WORD_FORMAT.text_width_cm / 2), WD_TAB_ALIGNMENT.CENTER)
    stops.add_tab_stop(Cm(WORD_FORMAT.text_width_cm), WD_TAB_ALIGNMENT.RIGHT)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.add_run("\t")
    if math.tag != qn("m:oMath"):
        raise ValueError("equation must contain an editable OMML math object")
    paragraph._p.append(math)
    paragraph.add_run("\t")
    set_run_font(paragraph.add_run(number), size=12)
    return paragraph
