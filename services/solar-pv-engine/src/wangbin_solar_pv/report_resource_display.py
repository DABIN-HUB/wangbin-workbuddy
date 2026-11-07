"""Compact Word-only monthly resource display over the existing Phase 2 binding."""
from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
from typing import Any, Callable


_RESOURCE_FIELDS = ("ghi", "dni", "dhi", "poa", "ambient_temperature", "wind_speed", "coverage")


def prepare_resource_word_rows(
    result: dict[str, Any], rows: list[list[Any]], number: Callable[[Any], str]
) -> tuple[str, list[list[Any]], list[list[Any]], dict[str, dict[str, Any]]]:
    """Index validated M04 cells by project, month and field without shortening provenance itself.

    `rows` must come from report_export._resource_rows; UNKNOWN cells never
    receive a provenance alias. The companion M04 retains full per-atom origin.
    """
    normalized = result["inputs"].get("normalized", {})
    records = result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    parents = [record for record in records if record.get("field_id") == "resource.monthly"]
    parent = parents[0] if len(parents) == 1 else None
    project_id, snapshot_id = result.get("project_id"), result.get("source_snapshot_id")
    prefix = ("R" + sha256(f"{project_id}:{snapshot_id}".encode("utf-8")).hexdigest()[:10].upper()
              if project_id and snapshot_id else None)
    sourced = {row.get("row_id"): row for row in parent.get("value", ()) if isinstance(row, dict)} if parent else {}
    entered = {row.get("fields", {}).get("resource.monthly.month"): row
               for row in normalized.get("resource.monthly", ()) if isinstance(row, dict)}
    irradiance, weather, mapping = [], [], {}
    for row in rows:
        month = row[0]
        input_row = entered.get(month)
        row_id = input_row.get("row_id") if input_row else None
        source_row = sourced.get(row_id)
        alias = (f"{prefix}-M{month:02d}" if prefix and type(month) is int and row_id and
                 source_row and any(cell != "UNKNOWN" for cell in row[1:8])
                 and f"row_id={row_id}" in row[8] else "UNKNOWN")
        if alias != "UNKNOWN":
            for position, field in enumerate(_RESOURCE_FIELDS, 1):
                if row[position] == "UNKNOWN":
                    continue
                atom = source_row.get("fields", {}).get("resource.monthly." + field)
                if not isinstance(atom, dict):
                    continue
                key = f"{alias}/{field}"
                if key in mapping:
                    raise ValueError("RESOURCE_DISPLAY_ALIAS_COLLISION")
                mapping[key] = {
                    "project_id": project_id, "source_snapshot_id": snapshot_id,
                    "dataset_id": normalized.get("resource.dataset_id"), "month": month,
                    "row_id": row_id, "field_id": atom["field_id"],
                    "field_instance_id": atom["field_instance_id"],
                    "source_id": atom["source_id"],
                    "source_url_or_attachment": atom["source_url_or_attachment"],
                    "unit": atom["unit"], "value": atom["value"],
                }
        irradiance.append([month, *row[1:5], alias])
        coverage = row[7]
        coverage_text = ("UNKNOWN" if coverage == "UNKNOWN" else
                         number(Decimal(str(coverage)) * 100) + "%")
        weather.append([month, row[5], row[6], coverage_text, alias])
    if mapping and parent:
        intro = (f"{prefix} 为本项目来源快照的展示前缀；每行索引须与表头变量组合读取，"
                 f"在测算模型 M04 对应逐字段实例、原值、单位及来源号，不合并不同变量。"
                 f"公共数据集：{normalized.get('resource.dataset_id')}，版本 {normalized.get('resource.version')}，"
                 f"时区 {normalized.get('site.timezone')}；登记来源 {parent.get('source_id')}，"
                 f"原始位置 {parent.get('source_url_or_attachment')}。月度资源是已提供汇总，不是发电量。")
    else:
        intro = "本项目尚无完整可引用的月度资源来源；UNKNOWN 不作为实测、已核验数据或发电量。"
    return intro, irradiance, weather, mapping
