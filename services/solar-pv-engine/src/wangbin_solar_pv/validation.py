"""Supplied-input validation, not solar yield or financial forecasting."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from fractions import Fraction
import re
from urllib.parse import parse_qs, urlsplit

from jsonschema import FormatChecker

from .errors import ContractError, Issue
from .schemas import StrictValidator, format_checker
from .serialization import dumps


def _schema(catalog):
    if catalog._schema is None:
        from .schemas import build_schema
        catalog._schema = build_schema(catalog)
    return catalog._schema


def iter_records(values, catalog):
    """Yield (envelope, scalar_array_item) without collapsing independent provenance."""
    for record in values.values():
        if not isinstance(record, dict):
            continue
        yield record, False
        field = catalog.fields.get(record.get("field_id"), {})
        if field.get("type") == "array" and isinstance(record.get("value"), list):
            if field["constraints"]["items"]["type"] == "object":
                for row in record["value"]:
                    if isinstance(row, dict):
                        yield from iter_records(row.get("fields", {}), catalog)
            else:
                for element in record["value"]:
                    if isinstance(element, dict):
                        yield element, True


def validate_record(record, catalog, *, scalar_item=False):
    fid = record.get("field_id", "") if isinstance(record, dict) else ""
    if fid not in catalog.fields:
        return [Issue("UNKNOWN_FIELD", fid, "字段未在冻结目录中定义")]
    field = catalog.fields[fid]
    result = []
    def issue(code, message, severity="ERROR"):
        result.append(Issue(code, fid, message, severity, record.get("field_instance_id")))
    schema = _schema(catalog)
    if scalar_item:
        from copy import deepcopy
        item_schema = deepcopy(schema["$defs"][fid])
        item_schema["properties"]["value"] = {"type": "string", "minLength": 1}
        validator = StrictValidator(item_schema, format_checker=format_checker())
    else:
        validator = StrictValidator({"$ref": "#/$defs/" + fid, "$defs": schema["$defs"]}, format_checker=format_checker())
    try:
        dumps(record)
        if next(validator.iter_errors(record), None) is not None:
            issue("FIELD_SCHEMA", "字段类型、范围、单位或信封结构不符合冻结Schema")
    except (ContractError, ValueError, TypeError, OverflowError):
        issue("FIELD_SCHEMA", "字段包含非有限数或无效结构")
    if result:
        if record.get("status") == "UNKNOWN" and record.get("value") is not None:
            issue("UNKNOWN_MUST_BE_NULL", "未知不能伪造数值/零值")
        return result
    kind = record.get("source_kind")
    provenance = record.get("provenance_kind")
    from .provenance import SOURCE_KINDS
    if kind not in SOURCE_KINDS or provenance != SOURCE_KINDS.get(kind):
        issue("SOURCE_KIND_MISMATCH", "来源类型与U/D/C/AI不一致")
    if provenance is not None and provenance not in field["provenance_kinds"]:
        issue("SOURCE_NOT_ALLOWED", "本字段不接受该来源类型")
    status = record.get("status")
    value = record.get("value")
    basis = record.get("confidence_basis")
    if not isinstance(basis, str) or not basis.strip() or re.fullmatch(r"\s*[+-]?[0-9.]+\s*%?\s*", basis):
        issue("CONFIDENCE_BASIS_REQUIRED", "可信度必须有证据文字依据，不能只有数字概率")
    if (kind == "UNKNOWN" or status == "UNKNOWN") and value is not None:
        issue("UNKNOWN_MUST_BE_NULL", "未知不能伪造数值/零值")
    if value is None and status not in {"UNKNOWN", "CONFLICT"}:
        issue("NULL_REQUIRES_UNKNOWN", "空值必须有UNKNOWN或CONFLICT状态")
    if status == "UNKNOWN" and not record.get("missing_reason"):
        issue("MISSING_REASON_REQUIRED", "未知值必须说明待补原因")
    if kind == "ASSUMPTION":
        if status != "ASSUMED":
            issue("ASSUMPTION_NOT_FACT", "假设不能登记为已核实事实")
        if not record.get("assumption"):
            issue("ASSUMPTION_METADATA_REQUIRED", "假设须有方法、理由及成熟度上限")
    if status == "ASSUMED" and (kind != "ASSUMPTION" or not record.get("assumption")):
        issue("ASSUMPTION_METADATA_REQUIRED", "假设状态须明确来源类型与假设登记")
    if status == "VERIFIED":
        if not all(record.get(k) for k in ("source_id", "source_url_or_attachment", "source_section_or_cell", "reviewer", "confidence_basis")):
            issue("VERIFICATION_EVIDENCE_REQUIRED", "核实须有来源、实际位置、核验者与依据")
        if record.get("location_status") == "UNKNOWN":
            # Text fragments may be real even when page/cell cannot be established.
            if not record.get("source_section_or_cell"):
                issue("VERIFICATION_EVIDENCE_REQUIRED", "不可编造精确位置")
        if record.get("license_status") != "AUTHORIZED":
            issue("VERIFICATION_LICENSE_REQUIRED", "未核实授权不能升级为可靠证据")
    if kind not in {"UNKNOWN", "ASSUMPTION"} and value is not None and not record.get("source_id"):
        issue("SOURCE_ID_REQUIRED", "实际候选值必须登记来源ID")
    if provenance == "C":
        if not all(record.get(k) for k in ("formula_id", "formula_version", "run_id", "upstream_instance_ids")):
            issue("CALCULATION_LINEAGE_REQUIRED", "C类必须有公式版本、运行和上游实例链")
        elif record["formula_id"] not in catalog.formulas:
            issue("UNKNOWN_FORMULA", "计算公式必须引用冻结注册表")
        elif fid == "capex.items.amount" and record["formula_id"] != "F-CAPEX-ITEM-AMOUNT":
            issue("CALCULATION_LINEAGE_MISMATCH", "投资分项金额必须关联相应数量单价公式")
    reference = record.get("source_url_or_attachment")
    if isinstance(reference, str):
        if re.match(r"^[A-Za-z]:[\\/]", reference) or reference.startswith(("/", "\\")):
            issue("PRIVATE_PATH_REFERENCE", "来源必须使用脱敏附件标识而非私密绝对路径")
        if reference.startswith(("http://", "https://")):
            url = urlsplit(reference)
            if url.username or url.password or any(k.casefold() in {"token", "api_key", "password", "access_token"} for k in parse_qs(url.query)):
                issue("CREDENTIAL_URL", "来源引用不能携带凭据")
    if record.get("effective_from") and record.get("effective_to") and record["effective_from"] > record["effective_to"]:
        issue("INVALID_EFFECTIVE_PERIOD", "生效日不能晚于失效日")
    if field["constraints"].get("format") == "date-time" and isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.utcoffset() is None:
                raise ValueError
        except ValueError:
            issue("TIMEZONE_REQUIRED", "时序必须采用真实日期和明确时区偏移")
    if value is not None and record.get("original_unit") != record.get("unit") and field["type"] in {"number", "integer"}:
        if not record.get("normalization") or not record.get("transformation_rule_ids"):
            issue("NORMALIZATION_LINEAGE_REQUIRED", "单位变换必须保留原值与转换规则")
        else:
            from .units import convert_unit
            normalization = record["normalization"]
            policy = normalization.get("rounding_policy") or {}
            try:
                replay = convert_unit(record.get("original_value"), record.get("original_unit"), record.get("unit"),
                    currency=(record.get("economic_basis") or {}).get("currency"),
                    decimal_places=policy.get("decimal_places"), rounding=policy.get("rounding"))
                if replay.value != value or replay.rule_id != normalization.get("rule_id") or replay.exact != normalization.get("exact"):
                    issue("NORMALIZATION_REPLAY_MISMATCH", "规范值与已声明的原值/单位/转换规则不符")
            except (ContractError, TypeError, ValueError):
                issue("NORMALIZATION_REPLAY_MISMATCH", "单位转换血缘不可复算")
    if field["type"] == "array" and isinstance(value, list) and not scalar_item:
        items = field["constraints"]["items"]
        if items["type"] == "object":
            row_ids = []
            for row in value:
                if not isinstance(row, dict):
                    continue
                row_ids.append(row.get("row_id"))
                for child_key, child in row.get("fields", {}).items():
                    if isinstance(child, dict) and child.get("field_id") != child_key:
                        issue("ROW_FIELD_ID_MISMATCH", "行字段键与信封ID不符")
                row_field = row.get("fields", {}).get(fid + ".row_id", {})
                if not row_field:
                    issue("ROW_ID_PROVENANCE_MISSING", "对象数组row_id也必须有独立原子来源记录")
                if row_field.get("value") is not None and row_field["value"] != row.get("row_id"):
                    issue("ROW_ID_MISMATCH", "行标识与row_id原子记录不符")
            if len(row_ids) != len(set(row_ids)):
                issue("DUPLICATE_ROW_ID", "行标识必须稳定唯一")
        else:
            scalars = [item.get("value") for item in value if isinstance(item, dict)]
            if len(scalars) != len(set(scalars)):
                issue("DUPLICATE_SCALAR_ITEM", "前置ID不能重复")
    return result


def compatible_economic_basis(a, b):
    required = {"currency", "price_year", "tax_basis", "price_basis"}
    return isinstance(a, dict) and isinstance(b, dict) and required <= a.keys() and required <= b.keys() and all(a[k] == b[k] for k in required)


def _value(project, fid):
    record = project.values.get(fid, {})
    return record.get("value") if record.get("status") not in {"UNKNOWN", "CONFLICT"} else None


def _rows(project, fid):
    value = _value(project, fid)
    return value if isinstance(value, list) else []


def row_value(row, fid):
    record = row.get("fields", {}).get(fid, {})
    return record.get("value") if record.get("status") not in {"UNKNOWN", "CONFLICT"} else None


def validate_project(project, catalog):
    result = []
    instances = {}
    for record, scalar in iter_records(project.values, catalog):
        result.extend(validate_record(record, catalog, scalar_item=scalar))
        instance = record.get("field_instance_id")
        if instance in instances:
            result.append(Issue("DUPLICATE_INSTANCE_ID", record.get("field_id", ""), "每个原子值实例ID必须唯一", instance_id=instance))
        instances[instance] = record
    for key, record in project.values.items():
        if not isinstance(record, dict):
            result.append(Issue("FIELD_SCHEMA", key, "字段值必须是来源信封"))
        elif record.get("field_id") != key:
            result.append(Issue("FIELD_ID_MISMATCH", key, "字段键与信封ID不符"))
    if any(i.code in {"FIELD_SCHEMA", "UNKNOWN_FIELD"} for i in result):
        # No arithmetic/graph checks on malformed records; preserve issues, not exceptions.
        return result
    for record in instances.values():
        if record.get("provenance_kind") == "C":
            upstream = [instances.get(k) for k in record.get("upstream_instance_ids", [])]
            if any(item is None for item in upstream):
                result.append(Issue("UPSTREAM_INSTANCE_MISSING", record["field_id"], "计算值的上游实例必须存在"))
            if record["field_id"] == "capex.items.amount" and {item["field_id"] for item in upstream if item} != {"capex.items.quantity", "capex.items.unit_price"}:
                result.append(Issue("AMOUNT_LINEAGE_INPUTS", record["field_id"], "计算金额须链接同明细的数量和单价"))
    total, usable = _value(project,"site.total_area"), _value(project,"site.usable_area")
    if isinstance(total, (int,float,Decimal)) and isinstance(usable,(int,float,Decimal)) and usable > total:
        result.append(Issue("USABLE_AREA_EXCEEDS_TOTAL","site.usable_area","可用面积不能超过总面积"))
    if _value(project,"project.pv_type") not in {None, project.pv_type}:
        result.append(Issue("CATEGORY_MISMATCH","project.pv_type","项目分类与根契约不符"))
    grace, term = _value(project,"finance.grace_years"), _value(project,"finance.loan_years")
    if isinstance(grace,int) and isinstance(term,int) and grace > term:
        result.append(Issue("GRACE_EXCEEDS_TERM","finance.grace_years","宽限期不能超过贷款期限"))
    if _value(project,"finance.debt_ratio") == 0 and _rows(project,"finance.debt_schedule"):
        debt_amounts = [row_value(row,"finance.debt_schedule."+name) for row in _rows(project,"finance.debt_schedule") for name in ("drawdown","principal","interest","fees")]
        if any(isinstance(v,(int,float,Decimal)) and v != 0 for v in debt_amounts):
            result.append(Issue("ZERO_DEBT_WITH_SCHEDULE","finance.debt_ratio","无债务声明与债务计划冲突"))
    start, end = _value(project,"schedule.construction_start"), _value(project,"schedule.commissioning_date")
    if isinstance(start,str) and isinstance(end,str) and start > end:
        result.append(Issue("SCHEDULE_ORDER","schedule.commissioning_date","投产日不能早于建设开始日"))
    # Input time-of-use schedule, tasks and observation quality, not model execution.
    result.extend(_validate_tasks(project))
    result.extend(_validate_tariffs(project))
    result.extend(_validate_time_series(project))
    from .consistency import validate_input_relations
    result.extend(validate_input_relations(project, catalog))
    return result


def _validate_tasks(project):
    result = []
    graph = {}
    for row in _rows(project,"schedule.tasks"):
        task = row_value(row,"schedule.tasks.task_id")
        predecessors = row_value(row,"schedule.tasks.predecessor_ids")
        if task is None:
            continue
        if task in graph:
            result.append(Issue("DUPLICATE_TASK_ID","schedule.tasks.task_id","任务ID不能重复"))
        graph[task] = [item.get("value") for item in predecessors] if isinstance(predecessors,list) else []
        if predecessors is None:
            result.append(Issue("PREDECESSORS_UNKNOWN","schedule.tasks.predecessor_ids","null为未知，不等于无前置", "WARNING"))
    for task, refs in graph.items():
        if task in refs:
            result.append(Issue("TASK_SELF_REFERENCE","schedule.tasks.predecessor_ids","任务不能引用自身"))
        if any(ref not in graph for ref in refs):
            result.append(Issue("TASK_REFERENCE_MISSING","schedule.tasks.predecessor_ids","前置任务ID必须存在"))
    from collections import defaultdict, deque
    dependents = defaultdict(list)
    degree = {}
    for task, refs in graph.items():
        known = {ref for ref in refs if ref in graph}
        degree[task] = len(known)
        for ref in known:
            dependents[ref].append(task)
    queue = deque(task for task, count in degree.items() if count == 0)
    processed = 0
    while queue:
        task = queue.popleft()
        processed += 1
        for dependent in dependents[task]:
            degree[dependent] -= 1
            if degree[dependent] == 0:
                queue.append(dependent)
    if processed != len(graph):
        result.append(Issue("TASK_CYCLE","schedule.tasks.predecessor_ids","前置关系不能形成循环"))
    return result


def _validate_tariffs(project):
    result = []
    groups = {}
    for row in _rows(project,"tariff.periods"):
        start, end = row_value(row,"tariff.periods.start_time"), row_value(row,"tariff.periods.end_time")
        if not isinstance(start,str) or not isinstance(end,str):
            continue
        good_start = re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", start)
        good_end = re.fullmatch(r"(?:(?:[01][0-9]|2[0-3]):[0-5][0-9]|24:00)", end)
        if not good_start or not good_end:
            result.append(Issue("INVALID_TARIFF_TIME","tariff.periods","起点00..23，终点仅可额外24:00")); continue
        a = int(start[:2])*60+int(start[3:]); b=int(end[:2])*60+int(end[3:])
        if a >= b:
            result.append(Issue("TARIFF_CROSS_MIDNIGHT","tariff.periods","跨午夜须拆为日内半开时段")); continue
        key = tuple(str(row_value(row,"tariff.periods."+name)) for name in ("season","weekday_rule","effective_from","effective_to"))
        groups.setdefault(key,[]).append((a,b))
    for intervals in groups.values():
        intervals.sort()
        if any(a < previous[1] for previous,(a,b) in zip(intervals,intervals[1:])):
            result.append(Issue("TARIFF_OVERLAP","tariff.periods","同适用域的时段不能重叠"))
        if intervals[0][0] != 0 or intervals[-1][1] != 1440 or any(a != previous[1] for previous,(a,b) in zip(intervals,intervals[1:])):
            result.append(Issue("TARIFF_COVERAGE_GAP","tariff.periods","日内时段存在缺口，不补造电价", "WARNING"))
    return result


def _validate_time_series(project):
    result = []
    for group in ("resource.timeseries","load.series","tariff.market_series","storage.dispatch"):
        previous = None
        previous_interval = None
        seen = set()
        for row in _rows(project,group):
            stamp = row_value(row,group+".timestamp")
            if not isinstance(stamp,str):
                continue
            try:
                dt = datetime.fromisoformat(stamp.replace("Z","+00:00"))
                if dt.utcoffset() is None:
                    raise ValueError
                point = dt.astimezone(timezone.utc)
            except ValueError:
                result.append(Issue("TIMEZONE_REQUIRED",group+".timestamp","时序须有合法日期/时区")); continue
            if point in seen:
                result.append(Issue("DUPLICATE_TIMESTAMP",group,"重复时刻不能静默丢弃"))
            if previous is not None:
                if point < previous:
                    result.append(Issue("TIMESERIES_ORDER",group,"时序不能逆序"))
                if previous_interval is not None and Fraction(str((point-previous).total_seconds())) != Fraction(str(previous_interval))*60:
                    result.append(Issue("TIMESERIES_GAP",group,"时段重叠或缺口，不补零", "WARNING"))
            seen.add(point); previous=point
            previous_interval=row_value(row,group+".interval_minutes")
    return result
