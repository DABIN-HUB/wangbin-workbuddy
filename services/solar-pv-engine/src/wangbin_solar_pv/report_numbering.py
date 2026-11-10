"""Reader-facing Word numbering, separate from frozen report identities."""
from __future__ import annotations

from dataclasses import dataclass
import re

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


_CHINESE_DIGITS = ("", "一", "二", "三", "四", "五", "六", "七", "八", "九")
_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
_ID = re.compile(r"^(CH|APP)(\d{2})(?:\.(\d{2}))?$")


@dataclass(frozen=True)
class HeadingNumber:
    stable_id: str
    parent_stable_id: str | None
    heading_level: int
    display_number: str
    display_title: str
    word_style: str
    bookmark_id: str
    toc_level: int

    @property
    def text(self) -> str:
        separator = " " if self.heading_level == 1 and self.stable_id.startswith("APP") else ""
        return f"{self.display_number}{separator}{self.display_title}"


def _chinese(value: int) -> str:
    if not 1 <= value <= 99:
        raise ValueError("heading ordinal out of range")
    tens, ones = divmod(value, 10)
    return ("十" if tens == 1 else _CHINESE_DIGITS[tens] + "十" if tens else "") + _CHINESE_DIGITS[ones]


def heading_number(stable_id: str, title: str, *, parent_stable_id: str | None = None,
                   parent_level: int | None = None) -> HeadingNumber:
    """Map a frozen ID to a heading, rejecting orphan and skipped levels."""
    match = _ID.fullmatch(stable_id)
    if match is None or not title or title != title.rstrip("。；：,.、 "):
        raise ValueError("invalid heading identity or trailing punctuation")
    kind, major_text, minor_text = match.groups()
    major = int(major_text)
    if major < 1 or major > (18 if kind == "CH" else 13):
        raise ValueError("heading outside frozen outline")
    if minor_text is None:
        if parent_stable_id is not None or parent_level is not None:
            raise ValueError("top-level heading cannot have parent")
        prefix = f"{_chinese(major)}、" if kind == "CH" else f"附录{chr(64 + major)}"
        level = 1
    else:
        minor = int(minor_text)
        if minor < 1 or parent_stable_id != f"{kind}{major_text}" or parent_level != 1:
            raise ValueError("subsection must belong to a level-one heading")
        prefix = f"（{_chinese(minor)}）"
        level = 2
    return HeadingNumber(stable_id, parent_stable_id, level, prefix, title,
                         f"Heading {level}", "PV_" + stable_id.replace(".", "_"), level)


def nested_number(ordinal: int, *, level: int, parent_level: int) -> str:
    """Only permit real consecutive parent/child heading depths."""
    if parent_level != level - 1 or ordinal < 1:
        raise ValueError("skipped heading depth or invalid ordinal")
    if level == 3:
        return f"{ordinal}."
    if level == 4:
        return f"（{ordinal}）"
    if level == 5 and ordinal <= len(_CIRCLED):
        return _CIRCLED[ordinal - 1]
    raise ValueError("unsupported heading level or ordinal")


def add_numbered_heading(document, number: HeadingNumber, bookmark_index: int):
    """Emit an actual Heading with a durable, unique Word bookmark."""
    paragraph = document.add_paragraph(style=number.word_style)
    # Indent continuation lines to the title start, not to the numeral.
    # Chinese punctuation uses full-width glyphs in the configured heading font.
    width = (42 if number.heading_level == 2 else
             47 if number.stable_id.startswith("APP") else 16 * len(number.display_number))
    paragraph.paragraph_format.left_indent = Pt(width)
    paragraph.paragraph_format.first_line_indent = -paragraph.paragraph_format.left_indent
    paragraph.add_run(number.display_number + " " if number.heading_level == 1 and
                      number.stable_id.startswith("APP") else number.display_number)
    paragraph.add_run(number.display_title)
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bookmark_index))
    start.set(qn("w:name"), number.bookmark_id)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bookmark_index))
    paragraph._p.insert(1 if paragraph._p.pPr is not None else 0, start)
    paragraph._p.append(end)
    return paragraph


def validate_numbering(document, chapters, appendices, appendix_titles, formula_ids) -> dict[str, int]:
    """Check the delivered Word structure against frozen identities, not sampled titles."""
    expected = []
    for stable_id, title, items in chapters:
        expected.append(heading_number(stable_id, title))
        expected.extend(heading_number(f"{stable_id}.{index:02d}", name,
                                       parent_stable_id=stable_id, parent_level=1)
                        for index, name in enumerate(items, 1))
    for stable_id, title in appendices:
        expected.append(heading_number(stable_id, title))
        expected.extend(heading_number(f"{stable_id}.{index:02d}", appendix_titles[f"{stable_id}.{index:02d}"],
                                       parent_stable_id=stable_id, parent_level=1) for index in (1, 2))
    actual = [p for p in document.paragraphs if p.style.name in {"Heading 1", "Heading 2", "Heading 3", "Heading 4", "Heading 5"}]
    if len(expected) != len(actual):
        raise ValueError("heading count or depth mismatch")
    stable_names = set()
    for paragraph, number in zip(actual, expected):
        bookmarks = [(node.get(qn("w:name")), node.get(qn("w:id")))
                     for node in paragraph._p.xpath("./w:bookmarkStart")]
        matched = [id_value for name, id_value in bookmarks if name == number.bookmark_id]
        ends = paragraph._p.xpath("./w:bookmarkEnd/@w:id")
        # CH18.01 retains its frozen identity; the reader-facing title may
        # replace the internal four-state design term without renumbering it.
        titles = {number.text}
        if number.stable_id == "CH18.01":
            titles.add(heading_number("CH18.01", "阶段建议", parent_stable_id="CH18",
                                      parent_level=1).text)
        if (paragraph.style.name != number.word_style or paragraph.text not in titles
                or len(matched) != 1 or matched[0] not in ends or
                number.bookmark_id in stable_names):
            raise ValueError(f"heading identity/number mismatch: {number.stable_id}")
        stable_names.add(number.bookmark_id)
    tables = [p.text for p in document.paragraphs if p.style.name == "Caption" and p.text.startswith("表")]
    figures = [p.text for p in document.paragraphs if p.style.name == "Caption" and p.text.startswith("图")]
    for kind, captions, total in (("表", tables, len(document.tables)), ("图", figures, len(document.inline_shapes))):
        if len(captions) != total or any(not caption.startswith(f"{kind}{index} ") or
                                         caption.rstrip("。；：,.、 ") != caption
                                         for index, caption in enumerate(captions, 1)):
            raise ValueError(f"{kind} caption sequence mismatch")
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Caption":
            continue
        for kind, limit in (("图", len(figures)), ("表", len(tables))):
            for match in re.finditer(rf"(?:参见|见|如|参考){kind}\s*(\d+)(?![\d.])", paragraph.text):
                if not 1 <= int(match.group(1)) <= limit:
                    raise ValueError(f"{kind} reference has no caption")
    formulas = [p.text.split("\t")[-1] for p in document.paragraphs if p.style.name == "Solar Equation"]
    actual_ids = [p.text.split(" ", 1)[0] for p in document.paragraphs
                  if p.style.name == "Solar Formula Title" and p.text.startswith("F-")]
    if (actual_ids != list(formula_ids) or
            formulas != [f"（{index}）" for index in range(1, len(formula_ids) + 1)]):
        raise ValueError("formula identity/number mismatch")
    return {"chapters": len(chapters), "body_items": sum(len(items) for _, _, items in chapters),
            "appendices": len(appendices), "appendix_items": len(appendices) * 2,
            "tables": len(tables), "figures": len(figures), "formulas": len(formulas)}
