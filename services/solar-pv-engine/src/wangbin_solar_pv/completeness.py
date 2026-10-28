"""Evidence-qualified input levels; never a report grade or investment recommendation."""
from __future__ import annotations

from .applicability import validate_applicability
from .conditions import known, effective_requirement, condition_state
from .errors import ContractError, Issue
from .quality import assess_input_quality
from .schemas import validate_shape
from .validation import validate_project, iter_records

AXES = ("identity", "site_rights", "engineering", "resource", "grid", "consumption_tariff", "cost_operation", "finance_tax", "traceability")


def _axis(fid):
    prefix = fid.split(".")[0]
    if prefix in {"project", "targets", "schedule"}: return "identity"
    if prefix == "site": return "site_rights"
    if prefix in {"roof", "system", "layout", "agri", "fishery", "public", "residential", "carport_bipv", "desert_mining", "storage", "scenarios"}: return "engineering"
    if prefix == "resource": return "resource"
    if prefix == "grid": return "grid"
    if prefix in {"load", "tariff", "revenue"}: return "consumption_tariff"
    if prefix in {"capex", "opex", "assets"}: return "cost_operation"
    if prefix in {"finance", "tax"}: return "finance_tax"
    return "traceability"


def _record_ready(record, field, level):
    if not record or record.get("value") is None or record.get("status") in {"UNKNOWN", "CONFLICT"}:
        return False, "VALUE_OR_EVIDENCE_UNKNOWN"
    if field["type"] == "array" and not record["value"] and field["field_id"] != "schedule.tasks.predecessor_ids":
        return False, "EMPTY_ARRAY_NOT_EVIDENCE"
    status = record.get("status")
    if level == "L1":
        return status in {"VERIFIED", "UNVERIFIED", "ASSUMED"}, "L1_DECLARED_INPUT"
    if status == "ASSUMED":
        assumption = record.get("assumption") or {}
        substitution = field.get("substitutable", {})
        ceiling = substitution.get("max_maturity", assumption.get("maturity_ceiling", "L1"))
        acceptable = level == "L2" and ceiling == "L2" and substitution.get("allowed") and assumption.get("noncritical") and assumption.get("decision_invariant") and assumption.get("lower") is not None and assumption.get("upper") is not None and record.get("reviewer")
        return bool(acceptable), "ASSUMPTION_MATURITY_CEILING"
    sufficient = status == "VERIFIED" and record.get("license_status") == "AUTHORIZED" and record.get("reviewer") and record.get("source_section_or_cell")
    return bool(sufficient), "VERIFIED_EVIDENCE_REQUIRED"


def _questions(project, catalog, missing, issues, limit=5):
    questions=[]
    def add(qid, fields, text, priority):
        if qid not in {q["question_id"] for q in questions}:
            questions.append({"question_id":qid,"field_ids":fields,"question_zh":text,"priority":priority})
    if known(project,"project.pv_type") is None:
        add("Q-TYPE",["project.pv_type"],"请确认项目分类；光储还需明确基础光伏类型。",0)
    if condition_state("IN-C01",project,catalog)["truth"] != "T":
        add("Q-LOCATION",["site.address","site.latitude","site.longitude"],"请补充具体屋顶/地块地址，或一对有坐标系依据的经纬度；只有城市时保持站址待核。",1)
    if condition_state("IN-C02",project,catalog)["truth"] != "T":
        add("Q-SIZE",["site.total_area","site.usable_area","system.dc_capacity"],"请提供面积或已有直流装机计划之一；预算可暂缺，不要求先知道投资。",2)
    if known(project,"project.sales_mode") in {None,"undecided"}:
        add("Q-SALES",["project.sales_mode"],"计划自用余电上网、全额售电、离网还是尚待比较？",3)
    if condition_state("IN-C03",project,catalog)["truth"] != "T":
        add("Q-TARGET",["targets.payback_years","targets.project_irr","targets.equity_irr"],"是否有回收期或IRR门槛？它们仅作目标，不反推客观参数；未定也可继续补资料。",4)
    if known(project,"project.has_storage") is None:
        add("Q-STORAGE",["project.has_storage"],"是否包含储能？未知时不会自动按无储能处理。",5)
    if known(project,"finance.debt_ratio") is None:
        add("Q-DEBT",["finance.debt_ratio"],"是否使用贷款？明确无债请登记比例0；缺协议不等于无债。",6)
    priorities={"site_rights":10,"engineering":11,"grid":12,"resource":13,"consumption_tariff":14,"cost_operation":15,"finance_tax":16,"identity":17,"traceability":18}
    for item in sorted(missing,key=lambda item:(priorities.get(item["axis"],20),item["field_id"])):
        fid=item["field_id"]
        definition=catalog.fields[fid]
        ask_fid=definition.get("repeat_group",fid)
        add("Q-FIELD-"+ask_fid,[ask_fid],"请补充或复核“"+catalog.fields[ask_fid]["label_zh"]+"”的资料、单位与来源；未知请明确标记，不填猜测值。",priorities.get(item["axis"],20))
    for issue in issues:
        if issue.severity == "ERROR" and issue.field_id in catalog.fields:
            add("Q-REVIEW-"+issue.field_id,[issue.field_id],"请复核该字段的类型、来源或相互冲突的资料；不会自动覆盖原值。",0)
    return sorted(questions,key=lambda q:(q["priority"],q["question_id"]))[:limit]


def evaluate_completeness(project, catalog, *, target_level="L2", question_limit=5):
    if target_level not in {"L1","L2","L3"} or type(question_limit) is not int or not 1 <= question_limit <= 5:
        raise ContractError("INVALID_COMPLETENESS_OPTIONS")
    try:
        validate_shape(project.to_dict(),catalog)
    except ContractError:
        return {"current_level":"L1_DRAFT","qualified_level":None,"level_scope":"INPUT_EVIDENCE_ONLY",
                "assessment_basis":"INVALID_INPUT_SCHEMA","report_maturity":"NOT_EVALUATED",
                "available_fields":[],"missing_required_fields":[],"conflicting_fields":[],"unverified_fields":[],"unverified_assumptions":[],
                "condition_pending_fields":[],"levels":{},"axes":{},"quality_issues":[],
                "validation_issues":[Issue("PROJECT_SCHEMA","","项目结构/版本不合法，不对无效结构计算等级").to_dict()],
                "inputs_ready_for_calculation":False,"can_enter_next_calculation_stage":False,"can_execute_calculation":False,
                "grid_connection_status":"PENDING_VERIFICATION","self_use_ratio_status":"UNKNOWN",
                "next_questions":[{"question_id":"Q-SCHEMA","field_ids":[],"question_zh":"请先修正输入Schema或版本，不会使用默认值补齐。","priority":0}],
                "calculation_status":"NOT_IMPLEMENTED","execution_blockers":["INPUT_SCHEMA_INVALID","CALCULATION_ENGINE_NOT_IMPLEMENTED"]}
    from .categories import category_contract, validate_category
    base=known(project,"storage.base_pv_type") if project.pv_type=="pv_storage" else None
    contract=category_contract(project.pv_type,catalog,base_pv_type=base)
    allowed=set(contract["allowed_field_ids"])
    validation=validate_project(project,catalog)+validate_category(project,catalog)
    applicability_issues=validate_applicability(project,catalog)
    validation.extend(applicability_issues)
    invalid_na={i.field_id for i in applicability_issues}
    approved_na={key for key,entry in project.applicability.items() if entry.get("status")=="NOT_APPLICABLE" and entry.get("field_id") not in invalid_na}
    quality=[] if any(i.code in {"FIELD_SCHEMA","UNKNOWN_FIELD"} for i in validation) else assess_input_quality(project,catalog)
    # Capability status is an execution blocker, not missing input evidence.
    quality.extend(i for i in validation if i.severity=="WARNING" and i.code != "NOT_IMPLEMENTED")
    records=[r for r,_ in iter_records(project.values,catalog)]
    available=[{"field_id":r["field_id"],"field_instance_id":r["field_instance_id"],"status":r["status"]} for r in records if r.get("value") is not None]
    conflicting=[{"field_id":r["field_id"],"field_instance_id":r["field_instance_id"],"candidate_ids":r["candidate_ids"]} for r in records if r["status"]=="CONFLICT"]
    unverified=[{"field_id":r["field_id"],"field_instance_id":r["field_instance_id"],"reason":"来源未核实"} for r in records if r["status"]=="UNVERIFIED"]
    assumed=[{"field_id":r["field_id"],"field_instance_id":r["field_instance_id"],"assumption":r.get("assumption"),"frozen_substitution":catalog.fields[r["field_id"]]["substitutable"]} for r in records if r["status"]=="ASSUMED"]
    levels={}
    for level in ("L1","L2","L3"):
        missing=[];pending=[];exempt=[]
        def check(fid, record, row_id=None):
            if fid not in allowed:
                return
            key=fid+("@"+row_id if row_id is not None else "")
            requirement=effective_requirement(fid,level,project,catalog)
            if key in approved_na or requirement["requirement"]=="NOT_APPLICABLE":
                exempt.append({"field_id":fid,"row_id":row_id,"rule_id":requirement.get("rule_id"),"reason":"已复核专项不适用" if key in approved_na else requirement["reason"]})
                return
            if requirement["requirement"]=="PENDING_CONDITION":
                pending.append({"field_id":fid,"row_id":row_id,"rule_id":requirement["rule_id"],"axis":_axis(fid),"reason":"适用条件未知，不按未触发豁免"})
                return
            definition=catalog.fields[fid]
            if requirement["requirement"]=="REQUIRED":
                ready,reason=_record_ready(record,definition,level)
                if not ready:
                    missing.append({"field_id":fid,"row_id":row_id,"axis":_axis(fid),"reason":reason,"level":level})
            if definition["type"]=="array" and record and isinstance(record.get("value"),list):
                if definition["constraints"]["items"]["type"]=="object":
                    for row in record["value"]:
                        for child in definition["constraints"]["items"]["field_ids"]:
                            check(child,row.get("fields",{}).get(child),row["row_id"])
                else:
                    for element in record["value"]:
                        check(fid,element,row_id)
        for fid,definition in catalog.fields.items():
            if not definition.get("repeat_group"):
                check(fid,project.values.get(fid))
        # Conflicts/unknown conditions and evidence floors cannot be averaged away.
        assumption_ceiling=[]
        for entry in assumed:
            fid=entry["field_id"]
            if fid not in allowed:
                continue
            definition=catalog.fields[fid]
            spec=definition.get("substitutable",{})
            ceiling=spec.get("max_maturity",(entry.get("assumption") or {}).get("maturity_ceiling","L1"))
            if level!="L1" and (not spec.get("allowed") or ceiling=="L1" or level=="L3"):
                assumption_ceiling.append(fid)
        deeper=[]
        if level=="L3":
            yearly=project.values.get("resource.annual_comparison",{}).get("value") or []
            if len({r.get("fields",{}).get("resource.annual_comparison.year",{}).get("value") for r in yearly})<2:
                deeper.append("MULTIYEAR_CROSSCHECK_REQUIRED")
        failed_validation=any(i.severity=="ERROR" for i in validation)
        blocking_quality=bool(quality) and level!="L1"
        passed=not (missing or pending or failed_validation or blocking_quality or assumption_ceiling or deeper or (conflicting and level!="L1"))
        levels[level]={"passed":passed,"missing_required_fields":missing,"condition_pending_fields":pending,"not_applicable_fields":exempt,
                       "assumption_ceiling_fields":assumption_ceiling,"deeper_evidence_gaps":deeper,"quality_blocked":blocking_quality}
    qualified=next((level for level in ("L3","L2","L1") if levels[level]["passed"]),None)
    current=qualified or "L1_DRAFT"
    selected=levels[target_level]
    gaps=selected["missing_required_fields"]+selected["condition_pending_fields"]
    axes={}
    for axis in AXES:
        axis_level=None
        for level in ("L1","L2","L3"):
            failures=[x for x in levels[level]["missing_required_fields"]+levels[level]["condition_pending_fields"] if x["axis"]==axis]
            relevant_quality=[i for i in quality if _axis(i.field_id)==axis] if level!="L1" else []
            if not failures and not relevant_quality:
                axis_level=level
            else:
                break
        axes[axis]={"qualified_level":axis_level,"scope":"input evidence only"}
    grid="PENDING_VERIFICATION"
    if known(project,"grid.opinion_status")=="confirmed" and all(project.values.get(fid,{}).get("status")=="VERIFIED" and project.values[fid].get("value") for fid in ("grid.opinion_attachment_id","grid.permit_reference","grid.opinion_valid_until")) and not any(i.code in {"GRID_OPINION_EXPIRED","GRID_REJECTED"} for i in quality):
        grid="CONFIRMED_DECLARATION_WITH_EVIDENCE"
    load_needed=condition_state("IN-C04",project,catalog)["truth"]
    self_status="NOT_APPLICABLE" if load_needed=="F" else ("NOT_COMPUTED" if project.values.get("load.series",{}).get("value") and not any(i.field_id.startswith("load.") for i in quality) else "UNKNOWN")
    ready=qualified in {"L2","L3"} and project.pv_type in {"industrial_rooftop","utility_scale_ground"}
    return {"current_level":current,"qualified_level":qualified,"level_scope":"INPUT_EVIDENCE_ONLY",
            "assessment_basis":"DECLARED_EVIDENCE_WITH_LOCAL_STRUCTURE_AND_CONSISTENCY_CHECKS","report_maturity":"NOT_EVALUATED",
            "available_fields":available,"missing_required_fields":selected["missing_required_fields"],"condition_pending_fields":selected["condition_pending_fields"],
            "conflicting_fields":conflicting,"unverified_fields":unverified,"unverified_assumptions":assumed,
            "not_applicable_fields":selected["not_applicable_fields"],"levels":levels,"axes":axes,
            "quality_issues":[i.to_dict() for i in quality],"validation_issues":[i.to_dict() for i in validation],
            "inputs_ready_for_calculation":ready,"can_enter_next_calculation_stage":ready,"can_execute_calculation":False,
            "execution_blockers":["CALCULATION_ENGINE_NOT_IMPLEMENTED"]+([] if ready else ["INPUT_EVIDENCE_OR_CATEGORY_NOT_READY"]),
            "grid_connection_status":grid,"self_use_ratio_status":self_status,
            "next_questions":_questions(project,catalog,gaps,validation+quality,question_limit),
            "calculation_status":"NOT_IMPLEMENTED","category_input_contract":contract["input_contract_status"]}
