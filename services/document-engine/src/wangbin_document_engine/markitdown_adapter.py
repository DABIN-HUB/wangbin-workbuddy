"""MarkItDown adapter kept behind a small stable boundary."""
from __future__ import annotations

from pathlib import Path

from markitdown import MarkItDown

from .models import ParsedDocument


class MarkItDownAdapter:
    def __init__(self) -> None:
        # Plugins are disabled because input documents are untrusted and the
        # product promises deterministic local parsing without side effects.
        self._converter = MarkItDown(enable_plugins=False)

    def convert(self, path: Path) -> ParsedDocument:
        result = self._converter.convert(str(path))
        text = str(getattr(result, "text_content", "") or "")
        title = getattr(result, "title", None)
        metadata = getattr(result, "metadata", None)
        if not isinstance(metadata, dict):
            metadata = {}
        notes: list[str] = []
        if path.suffix.lower() in {".pdf", ".pptx"}:
            notes.append("复杂布局、扫描图像或视觉位置可能无法完全保留；请人工复核表格和版式。")
        if not text.strip():
            notes.append("解析器未提取到文本，可能是扫描件、空文件或不支持的布局。")
        return ParsedDocument(text=text, title=title, metadata=metadata, quality_notes=notes)
