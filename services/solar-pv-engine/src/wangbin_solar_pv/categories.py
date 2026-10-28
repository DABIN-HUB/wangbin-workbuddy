"""Independent category input contracts; no yield, finance, templates or E2E."""
from __future__ import annotations

from pathlib import Path

from .errors import ContractError, Issue
from .serialization import loads


def category_contract(pv_type: str, catalog, *, base_pv_type: str | None = None) -> dict:
    """Project frozen definitions into a category, without redefining any field."""
    if not isinstance(pv_type, str) or pv_type not in catalog.pv_types:
        raise ContractError("UNKNOWN_CATEGORY", "project.pv_type")
    if pv_type != "pv_storage" and base_pv_type is not None:
        raise ContractError("BASE_ONLY_FOR_STORAGE", "storage.base_pv_type")
    contract = loads((Path(__file__).parent / "scenarios" / pv_type / "contract.json").read_bytes())
    allowed = [fid for fid, field in catalog.fields.items() if pv_type in field["pv_types"]
               and fid not in contract["forbidden_field_ids"]
               and not any(fid.startswith(prefix) for prefix in contract["forbidden_field_prefixes"])]
    if pv_type == "pv_storage":
        contract.update(base_pv_type=base_pv_type,
                        base_input_status="UNKNOWN" if base_pv_type is None else "SELECTED",
                        base_calculation_status="NOT_IMPLEMENTED")
        if base_pv_type is not None:
            if not isinstance(base_pv_type, str) or base_pv_type not in contract["allowed_base_pv_types"]:
                raise ContractError("INVALID_STORAGE_BASE", "storage.base_pv_type")
            base = category_contract(base_pv_type, catalog)
            storage_only = {fid for fid, field in catalog.fields.items() if field["pv_types"] == ["pv_storage"]}
            selected = set(base["allowed_field_ids"]) | storage_only
            allowed = [fid for fid in catalog.fields if fid in selected]
            contract["required_special_field_ids"] += base["required_special_field_ids"]
            contract["forbidden_field_ids"] = base["forbidden_field_ids"]
            contract["forbidden_field_prefixes"] = base["forbidden_field_prefixes"]
            contract["allowed_sales_modes"] = base["allowed_sales_modes"]
            contract["subtype_field_id"] = base["subtype_field_id"]
            for key in ("forbidden_values", "revenue_kind_forbidden_markers", "revenue_other_items_review_required"):
                if key in base:
                    contract[key] = base[key]
            contract["restriction"] += " 基座限制：" + base["restriction"]
    contract["allowed_field_ids"] = allowed
    return contract


def category_schema(pv_type, catalog, *, base_pv_type=None) -> dict:
    """Clone the full schema; category semantics remain in validate_category.

    All 469 $defs (including shared array child definitions) remain byte-for-byte
    equivalent as Python data. Only values root keys and root pv_type narrow.
    """
    contract = category_contract(pv_type, catalog, base_pv_type=base_pv_type)
    schema = catalog.project_schema()
    schema["properties"]["pv_type"] = {"const": pv_type}
    roots = schema["properties"]["values"]["properties"]
    allowed = set(contract["allowed_field_ids"])
    schema["properties"]["values"]["properties"] = {fid: ref for fid, ref in roots.items() if fid in allowed}
    return schema


def _fact(record):
    if not isinstance(record, dict) or record.get("status") in {"UNKNOWN", "CONFLICT"}:
        return None
    return record.get("value")


def _records(values):
    """Inspect mapping keys, not only envelope IDs, including nested rows."""
    for fid, record in values.items():
        yield fid, record
        value = record.get("value") if isinstance(record, dict) else None
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and isinstance(item.get("fields"), dict):
                    yield from _records(item["fields"])


def validate_category(project, catalog) -> list[Issue]:
    """Validate category routing and supplied domain inputs, preserving drafts.

    Combine with validate_project for the full shape/provenance/unit contract;
    warnings here never certify evidence maturity or a business calculation.
    """
    result = []
    def issue(code, fid, message, severity="ERROR", record=None):
        instance = record.get("field_instance_id") if isinstance(record, dict) else None
        result.append(Issue(code, fid, message, severity, instance))

    base = _fact(project.values.get("storage.base_pv_type")) if project.pv_type == "pv_storage" else None
    try:
        contract = category_contract(project.pv_type, catalog, base_pv_type=base)
    except ContractError as exc:
        issue(exc.code, exc.field_id or "project.pv_type", "分类或储能基座不在允许的稳定枚举中")
        if exc.code != "INVALID_STORAGE_BASE":
            return result
        contract = category_contract("pv_storage", catalog)

    if project.pv_type == "pv_storage" and base is None:
        issue("STORAGE_BASE_UNKNOWN", "storage.base_pv_type", "储能基座待核；保持UNKNOWN草稿，不默认屋顶或声明基座已验收", "WARNING")
    ground_storage = project.pv_type == "pv_storage" and base == "utility_scale_ground"
    if ground_storage and _fact(project.values.get("storage.dispatch_mode")) in ("self_consumption", "hybrid"):
        issue("STORAGE_BASE_DISPATCH_CONFLICT", "storage.dispatch_mode", "地面基座输入边界无工业自用负荷；当前自用调度方案须独立专项规则，不可调用无储能模型")

    declared = _fact(project.values.get("project.pv_type"))
    if declared is not None and declared != project.pv_type:
        issue("CATEGORY_MISMATCH", "project.pv_type", "项目分类与根契约不符")
    storage_flag = _fact(project.values.get("project.has_storage"))
    if storage_flag is True and project.pv_type != "pv_storage":
        issue("STORAGE_CATEGORY_REQUIRED", "project.has_storage", "配储项目必须显式选择pv_storage，不得借用无储能类型")
    if storage_flag is False and project.pv_type == "pv_storage":
        issue("STORAGE_FLAG_CONFLICT", "project.has_storage", "光储分类与明确不配储声明冲突")

    sales_mode = _fact(project.values.get("project.sales_mode"))
    if sales_mode is None or sales_mode == "undecided":
        issue("CATEGORY_SALES_MODE_UNKNOWN", "project.sales_mode", "销售模式待核；不视为已确定售电方案", "WARNING")
    elif sales_mode not in contract["allowed_sales_modes"]:
        issue("CATEGORY_SALES_MODE_INVALID", "project.sales_mode", "销售模式不属于当前分类或基座输入边界")

    allowed = set(contract["allowed_field_ids"])
    for fid, record in _records(project.values):
        if fid not in allowed:
            issue("CATEGORY_FIELD_NOT_ALLOWED", fid, "字段不属于当前分类或显式选择的非储能基座", record=record)
        value = _fact(record)
        if ground_storage and fid == "storage.dispatch.discharge_to_load" and value is not None and value != 0:
            issue("STORAGE_BASE_DISPATCH_CONFLICT", fid, "地面储能向用户负荷放电与当前基座输入边界冲突，须独立方案核验", record=record)
        if value is not None and value in contract.get("forbidden_values", {}).get(fid, []):
            issue("CATEGORY_COST_NOT_ALLOWED", fid, "地面工程不得沿用屋顶加固或屋顶租金成本", record=record)
        if fid == "revenue.other_items.kind" and contract.get("revenue_other_items_review_required"):
            if isinstance(value, str) and any(marker in value for marker in contract["revenue_kind_forbidden_markers"]):
                issue("CATEGORY_REVENUE_NOT_ALLOWED", fid, "集中式地面不得输入工商业自用节省或屋顶租赁收入模型", record=record)
            else:
                issue("CATEGORY_REVENUE_REVIEW_REQUIRED", fid, "其他收入须独立合同、排他边界及用途核验；输入保留不代表可计算或已准入", "WARNING", record)

    for fid in contract["required_special_field_ids"]:
        if _fact(project.values.get(fid)) is None:
            issue("CATEGORY_SPECIAL_UNKNOWN", fid, "专项资料待核；保留草稿，不代表专项契约义务已满足", "WARNING")
    subtype = contract["subtype_field_id"]
    if subtype:
        value = _fact(project.values.get(subtype))
        if value is None:
            issue("CATEGORY_SUBTYPE_UNKNOWN", subtype, "专项子型待核，不能默认屋顶或借用其他子型", "WARNING")
        elif value not in catalog.fields[subtype]["constraints"]["enum"]:
            issue("CATEGORY_SUBTYPE_INVALID", subtype, "专项子型不在冻结目录枚举中")
    issue("NOT_IMPLEMENTED", "project.pv_type", "仅实现分类输入契约；业务计算、四文件E2E及平台能力均NOT_IMPLEMENTED", "WARNING")
    return result
