"""Read-only formula-to-input queries; no numerical method or ledger is executed."""
from __future__ import annotations
from copy import deepcopy

from .conditions import effective_requirement
from .errors import ContractError
from .validation import iter_records, validate_record

_LEDGER={"CALCULATED_OR_VALIDATED_LEDGER_OUTPUT","CALCULATION_LEDGER_STATE"}


class FormulaBindings:
    def __init__(self,catalog):
        self.catalog=catalog
        for formula in catalog.formulas.values():
            for symbol in formula["every_symbol_definition"]:
                if symbol["field_id"] not in catalog.bindings and not (symbol["field_id"] is None and symbol["role"]=="index_or_constant"):
                    raise ContractError("UNBOUND_FORMULA_SYMBOL")
        for binding in catalog.bindings.values():
            if any(fid not in catalog.fields for fid in binding["input_field_ids"]):
                raise ContractError("UNBOUND_FORMULA_INPUT")

    def _input(self,fid,project,level):
        field=self.catalog.fields[fid]
        result={"field_id":fid,"type":field["type"],"unit":field["unit"],"repeat_group":field.get("repeat_group"),
            "source_requirements":deepcopy(field["provenance_kinds"]),"required_level":deepcopy(field["required_level"]),
            "acquisition":deepcopy(field.get("acquisition_zh")),"availability":"NOT_EVALUATED","instances":[],"missing_instances":[]}
        if project is None:
            result["requirement"]={"requirement":field["required_level"][level],"truth":"NOT_EVALUATED","rule_id":field.get("conditional_rule_id")}
            return result
        req=effective_requirement(fid,level,project,self.catalog)
        parent=field.get("repeat_group")
        if parent:
            parent_req=effective_requirement(parent,level,project,self.catalog)
            if parent_req["requirement"] in {"NOT_APPLICABLE","PENDING_CONDITION"}:
                req=parent_req
        result["requirement"]=req
        if project.pv_type not in field["pv_types"] or req["requirement"]=="NOT_APPLICABLE":
            result["availability"]="NOT_APPLICABLE"
            return result
        found=[(record,scalar) for record,scalar in iter_records(project.values,self.catalog) if record["field_id"]==fid]
        # iter_records' second value is a scalar-array flag, never a row ID.
        # Recover row context from the actual table, not by parsing instance IDs.
        row_by_instance={}
        if parent:
            rows=project.values.get(parent,{}).get("value")
            if isinstance(rows,list):
                for row in rows:
                    for atom,_ in iter_records(row["fields"],self.catalog):
                        row_by_instance[id(atom)]=row["row_id"]
        missing=[];invalid=False;statuses=[]
        for record,scalar_item in found:
            rid=row_by_instance.get(id(record))
            status=record["status"];statuses.append(status)
            errors=[i.code for i in validate_record(record,self.catalog,scalar_item=scalar_item) if i.severity=="ERROR"]
            invalid=invalid or bool(errors)
            result["instances"].append({"field_instance_id":record["field_instance_id"],"row_id":rid,"status":status,
                "unit":record["unit"],"source_id":record["source_id"],"source_kind":record["source_kind"],"issue_codes":errors})
            if record.get("value") is None or status in {"UNKNOWN","CONFLICT"}:
                missing.append({"field_id":fid,"field_instance_id":record["field_instance_id"],"row_id":rid,"reason":status})
        # A populated table does not make an absent field in its other rows present.
        if parent:
            parent_record=project.values.get(parent,{})
            rows=parent_record.get("value")
            if isinstance(rows,list):
                for row in rows:
                    if fid not in row["fields"]:
                        missing.append({"field_id":fid,"field_instance_id":None,"row_id":row["row_id"],"reason":"ABSENT_AT_ROW"})
        if not found and not missing:
            missing.append({"field_id":fid,"field_instance_id":None,"row_id":None,"reason":"ABSENT"})
        result["missing_instances"]=missing
        result["availability"]=("CONFLICT" if "CONFLICT" in statuses else "MISSING" if missing else "INVALID" if invalid
            else "ASSUMED" if "ASSUMED" in statuses else "UNVERIFIED" if "UNVERIFIED" in statuses else "PRESENT")
        return result

    def describe_field(self,formula_field_id,project=None,*,level="L2"):
        if formula_field_id not in self.catalog.bindings:
            raise ContractError("UNKNOWN_FORMULA_FIELD")
        if level not in {"L1","L2","L3"}:
            raise ContractError("UNKNOWN_FIELD_OR_LEVEL")
        binding=deepcopy(self.catalog.bindings[formula_field_id])
        inputs=[self._input(fid,project,level) for fid in binding["input_field_ids"]]
        kind=binding["kind"]
        if kind in _LEDGER:
            status="NOT_COMPUTED"
        elif kind=="DEFINITION_CONSTANT":
            status="CONSTANT_DEFINED" if binding["constant_definition"]["value"] is not None else "CONSTANT_UNVERIFIED"
        elif project is None:
            status="INPUT_NOT_EVALUATED"
        elif inputs and all(x["availability"]=="NOT_APPLICABLE" for x in inputs):
            status="NOT_APPLICABLE"
        elif any(x["missing_instances"] for x in inputs):
            status="MISSING_INPUT"
        else:
            status="INPUTS_PRESENT_TRANSFORM_NOT_IMPLEMENTED"
        missing=[fid for fid in binding["input_field_ids"] if any(x["field_id"]==fid and x["missing_instances"] for x in inputs)]
        return {**self.catalog.definition_identity(),"binding":binding,"binding_status":status,"data_type":{"kind":kind,
            "input_types":[{"field_id":x["field_id"],"type":x["type"],"repeat_group":x["repeat_group"]} for x in inputs],
            "formula_ledger_type":"NOT_DECLARED_IN_FROZEN_MAPPING" if kind in _LEDGER else "EXPLICIT_INPUT_OR_CONSTANT_DEFINITION"},
            "supporting_inputs":inputs,"missing_input_field_ids":missing,
            "missing_instances":[m for x in inputs for m in x["missing_instances"]],
            "unresolved_input_field_ids":[x["field_id"] for x in inputs if x["availability"] not in {"PRESENT","NOT_APPLICABLE","NOT_EVALUATED"}],
            "execution_status":"NOT_IMPLEMENTED"}

    def describe(self,formula_id,project=None,*,level="L2"):
        if formula_id not in self.catalog.formulas:
            raise ContractError("UNKNOWN_FORMULA")
        formula=deepcopy(self.catalog.formulas[formula_id]);symbols=[]
        required=[];conditional=[];missing_variables=[];uncomputed=[];constant_gaps=[];input_ids=set()
        for definition in formula["every_symbol_definition"]:
            if definition["field_id"] is None:
                symbols.append({"definition":deepcopy(definition),"binding":None,"binding_status":"SYMBOLIC_INDEX_OR_SOLVER_PARAMETER",
                    "data_type":{"kind":"SYMBOLIC_INDEX_OR_SOLVER_PARAMETER","declared_unit":definition["unit"]},
                    "supporting_inputs":[],"missing_input_field_ids":[],"missing_instances":[]})
                continue
            info=self.describe_field(definition["field_id"],project,level=level)
            symbols.append({"definition":deepcopy(definition),**info})
            input_ids.update(info["binding"]["input_field_ids"])
            if info["binding_status"]=="NOT_COMPUTED":
                uncomputed.append(definition["field_id"])
            if info["binding_status"]=="CONSTANT_UNVERIFIED":
                constant_gaps.append(definition["field_id"])
            if definition["role"]=="input":
                if info["missing_input_field_ids"]:
                    missing_variables.append(definition["field_id"])
                if any(x["required_level"][level]=="CONDITIONAL" or x["requirement"].get("rule_id") for x in info["supporting_inputs"]):
                    conditional.append(definition["field_id"])
                else:
                    required.append(definition["field_id"])
        applicable=set(self.catalog.pv_types)
        for fid in input_ids:
            applicable.intersection_update(self.catalog.fields[fid]["pv_types"])
        return {**self.catalog.definition_identity(),"schema_version":"solar-pv-formula-input-query/1.0.0","formula":formula,"symbols":symbols,
            "formula_id":formula_id,"name_zh":formula["chinese_name"],"explanation_zh":formula["calculation_boundary"],
            "required_parameters":sorted(set(required)),"conditional_parameters":sorted(set(conditional)),
            "missing_input_field_ids":sorted({fid for s in symbols if s["definition"]["role"]!="output" for fid in s["missing_input_field_ids"]}),
            "missing_variable_field_ids":sorted(set(missing_variables)),
            "missing_instances":[m for s in symbols if s["definition"]["role"]!="output" for m in s["missing_instances"]],
            "uncomputed_formula_field_ids":sorted(set(uncomputed)),"unverified_constant_field_ids":sorted(set(constant_gaps)),
            "applicable_pv_types":sorted(applicable),"input_presence_evaluated":project is not None,
            "scope_policy":"变量输入类型来自冻结03目录；账簿输出类型/数值/模型在Phase3及分类阶段另行实现，不从支持输入类型推断。多输入绑定是支持项清单，非已实现聚合/单位转换。",
            "calculation_status":"NOT_IMPLEMENTED","numerical_validation_status":"NOT_TESTED","can_execute_calculation":False,
            "baseline_reference":{"version":self.catalog.baseline_version,"files":deepcopy(self.catalog.baseline_hashes)}}
