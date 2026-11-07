"""The embedded chart bitmap must carry actual Chinese glyphs, not tofu boxes."""
from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from wangbin_solar_pv import report_export
from wangbin_solar_pv.errors import ContractError


_SPEC = {"metric_id": "energy.monthly.year.1", "title": "月度发电量变化",
         "unit": "kWh", "values": [float(index) for index in range(1, 13)]}


def test_embedded_png_uses_a_verified_chinese_font(monkeypatch):
    rendered = []
    original = ImageDraw.ImageDraw.text

    def capture(draw, xy, text, *args, **kwargs):
        rendered.append((text, kwargs.get("font")))
        return original(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture)
    stream = report_export._chart_png(_SPEC)
    image = Image.open(BytesIO(stream.getvalue()))
    image.load()
    assert image.size == (1200, 500)
    title, font = next((text, font) for text, font in rendered if text.startswith("月度发电量变化"))
    assert font is not None and getattr(font, "path", None)
    assert getattr(font, "size", 0) >= 20
    missing = font.getmask("\U0010ffff")
    missing_shape = missing.size, bytes(missing)
    assert all((font.getmask(char).size, bytes(font.getmask(char))) != missing_shape
               for char in set(title) if not char.isspace())
    assert any(text.startswith("发电量（kWh）") and axis_font is not None
               and getattr(axis_font, "path", None) for text, axis_font in rendered)


def test_missing_chinese_font_fails_instead_of_rendering_boxes(monkeypatch):
    monkeypatch.setattr(report_export, "_chart_font_candidates", lambda: ())
    with pytest.raises(ContractError, match="REPORT_CHART_FONT_GLYPHS_MISSING"):
        report_export._chart_png(_SPEC)
