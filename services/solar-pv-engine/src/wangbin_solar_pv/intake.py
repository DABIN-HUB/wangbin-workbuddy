"""Local, transactional multi-round intake. This interface cannot write engine results."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import re

from . import __version__
from .categories import validate_category, category_contract
from .completeness import evaluate_completeness
from .conditions import known
from .errors import ContractError
from .models import ProjectData
from .provenance import make_record, register_candidate, resolve_conflict, source_snapshot
from .schemas import validate_shape
from .serialization import digest
from .validation import validate_project, iter_records

_METADATA = {"source_id", "source_url_or_attachment", "source_section_or_cell", "measurement_period", "published_at", "retrieved_at", "effective_from", "effective_to", "geography", "confidence_basis", "missing_reason", "license_status", "sensitivity", "assumption", "economic_basis", "decimal_places", "rounding"}


def _raise_issues(issues):
    errors=[i for i in issues if i.severity=="ERROR"]
    if errors:
        exc=ContractError("INPUT_VALIDATION_FAILED",errors[0].field_id)
        exc.issues=[i.to_dict() for i in errors]
        raise exc


def _unwrapped(record):
    value=record.get("value")
    if isinstance(value,list):
        result=[]
        for item in value:
            if "fields" in item:
                result.append({"row_id":item["row_id"],"fields":{fid:_unwrapped(r) for fid,r in item["fields"].items()}})
            else:
                result.append(_unwrapped(item))
        return result
    return deepcopy(value)


class IntakeSession:
    def __init__(self,project,catalog):
        self.project=project
        self.catalog=catalog

    @classmethod
    def new(cls,project_id,pv_type,catalog):
        project=ProjectData.new(project_id,pv_type,catalog)
        # The routing choice is an actual explicit caller statement, not a default.
        record=make_record(catalog,"project.pv_type",pv_type,source_kind="USER_PROVIDED",source_id="user:session-start",
            source_url_or_attachment="user:session-start",source_section_or_cell="new/pv_type",
            confidence_basis="用户显式选择分类，尚未核实",location_status="TEXT_FRAGMENT")
        register_candidate(project,record,catalog)
        return cls(project,catalog)

    @classmethod
    def from_dict(cls,data,catalog):
        return cls(ProjectData.from_dict(data,catalog),catalog)

    def _begin(self,submission_id,payload,expected_revision):
        if not isinstance(submission_id,str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}",submission_id) is None:
            raise ContractError("INVALID_SUBMISSION_ID")
        payload_hash=digest(payload)
        previous=self.project.submission_ids.get(submission_id)
        if previous is not None:
            if previous!=payload_hash:
                raise ContractError("SUBMISSION_ID_REUSED")
            return None,payload_hash
        if type(expected_revision) is not int or expected_revision!=self.project.revision:
            raise ContractError("REVISION_CONFLICT")
        return deepcopy(self.project),payload_hash

    def _finish(self,draft,submission_id,payload_hash,candidate_ids=(),invalidated=()):
        validate_shape(draft.to_dict(),self.catalog)
        _raise_issues(validate_project(draft,self.catalog)+validate_category(draft,self.catalog))
        draft.submission_ids[submission_id]=payload_hash
        draft.revision+=1
        draft.history.append({"event":"submission_committed","submission_id":submission_id,"revision":draft.revision,
                              "at":datetime.now(timezone.utc).isoformat()})
        self.project=draft
        return self._response(False,candidate_ids,invalidated)

    def _response(self,duplicate=False,candidate_ids=(),invalidated=()):
        return {"revision":self.project.revision,"duplicate":duplicate,"accepted_candidate_ids":list(candidate_ids),
                "invalidated_field_ids":list(invalidated),"maturity":evaluate_completeness(self.project,self.catalog)}

    def _build(self,update,submission_id,path,*,currency=None,instance_id=None):
        if not isinstance(update,dict) or set(update)-({"field_id","value","unit","source_kind","status"}|_METADATA):
            raise ContractError("UNKNOWN_UPDATE_PROPERTY")
        fid=update.get("field_id")
        if not isinstance(fid,str) or fid not in self.catalog.fields or "value" not in update:
            raise ContractError("UNKNOWN_UPDATE_FIELD")
        field=self.catalog.fields[fid]
        kind=update.get("source_kind","USER_PROVIDED")
        if not isinstance(kind,str) or kind not in {"USER_PROVIDED","ASSUMPTION","UNKNOWN"}:
            raise ContractError("USER_CANNOT_WRITE_CALCULATED_OR_EXTRACTED_RECORD",fid)
        expected_status={"USER_PROVIDED":"UNVERIFIED","ASSUMPTION":"ASSUMED","UNKNOWN":"UNKNOWN"}[kind]
        if "status" in update and update["status"]!=expected_status:
            raise ContractError("EXPLICIT_REVIEW_REQUIRED",fid)
        value=deepcopy(update["value"])
        if field["type"] in {"number","integer"} and value is not None and ("unit" not in update or update["unit"] is None):
            raise ContractError("UNIT_REQUIRED",fid)
        if field["type"] not in {"number","integer"} and update.get("unit") not in (None,field["unit"]):
            raise ContractError("UNIT_MISMATCH",fid)
        metadata={key:deepcopy(update[key]) for key in _METADATA if key in update}
        metadata.setdefault("source_id","user:"+submission_id)
        metadata.setdefault("source_url_or_attachment","user:"+submission_id)
        metadata.setdefault("source_section_or_cell","submission:"+submission_id+"/"+path)
        metadata.setdefault("confidence_basis","用户显式提交；来源及适用性尚未核实")
        metadata.setdefault("missing_reason","未提供元数据保持未知；不是零值或默认工程参数")
        if field["type"]=="array" and value is not None:
            if not isinstance(value,list):
                raise ContractError("ARRAY_REQUIRED",fid)
            items=field["constraints"]["items"]
            transformed=[]
            if items["type"]=="object":
                for n,item in enumerate(value):
                    if not isinstance(item,dict) or set(item)!={"row_id","fields"} or not isinstance(item["fields"],dict):
                        raise ContractError("ARRAY_ROW_REQUIRED",fid)
                    row_id=item["row_id"]
                    if not isinstance(row_id,str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}",row_id) is None:
                        raise ContractError("ROW_ID_REQUIRED",fid)
                    children={}
                    for child,payload in item["fields"].items():
                        if child not in items["field_ids"]:
                            raise ContractError("UNKNOWN_ARRAY_FIELD",fid)
                        if not isinstance(payload,dict) or "value" not in payload:
                            payload={"value":payload}
                        children[child]=self._build({**payload,"field_id":child},submission_id,path+f"/value/{n}/fields/{child}",
                            currency=currency,instance_id=fid+":"+row_id+":"+child)
                    row_field=fid+".row_id"
                    if row_field not in children:
                        children[row_field]=make_record(self.catalog,row_field,row_id,source_kind="USER_PROVIDED",
                            field_instance_id=fid+":"+row_id+":row_id",source_id="user:"+submission_id,
                            source_url_or_attachment="user:"+submission_id,source_section_or_cell="submission:"+submission_id+"/"+path+f"/value/{n}/row_id",
                            confidence_basis="用户显式提供的稳定行标识，非虚构工程数据",location_status="TEXT_FRAGMENT")
                    transformed.append({"row_id":row_id,"fields":children})
            else:
                for n,item in enumerate(value):
                    if not isinstance(item,str):
                        raise ContractError("SCALAR_ARRAY_STRING_REQUIRED",fid)
                    transformed.append(make_record(self.catalog,fid,item,source_kind=kind,
                        field_instance_id=(instance_id or fid)+":element:"+str(n),**{**metadata,"source_section_or_cell":"submission:"+submission_id+"/"+path+f"/value/{n}"}))
            value=transformed
        return make_record(self.catalog,fid,value,source_kind=kind,original_unit=update.get("unit"),currency=currency,
                           field_instance_id=instance_id,location_status="TEXT_FRAGMENT",**metadata)

    def submit(self,submission_id,updates,*,expected_revision,reason=None):
        if not isinstance(updates,list) or not updates or len(updates)>1000:
            raise ContractError("INVALID_UPDATES")
        payload={"action":"revise" if reason else "submit","updates":updates,"reason":reason}
        draft,payload_hash=self._begin(submission_id,payload,expected_revision)
        if draft is None:
            return self._response(True)
        ids=[u.get("field_id") for u in updates if isinstance(u,dict)]
        if len(ids)!=len(updates) or any(not isinstance(fid,str) for fid in ids) or len(set(ids))!=len(ids):
            raise ContractError("DUPLICATE_OR_INVALID_UPDATE_FIELD")
        currency=known(draft,"project.currency")
        for update in updates:
            if update.get("field_id")=="project.currency":
                currency=update.get("value")
        changed=[];candidate_ids=[]
        for n,update in enumerate(updates):
            fid=update.get("field_id")
            if fid in self.catalog.fields and self.catalog.fields[fid].get("repeat_group"):
                raise ContractError("ARRAY_ITEM_REQUIRES_PARENT",fid)
            record=self._build(update,submission_id,"updates/"+str(n),currency=currency)
            old=known(draft,fid)
            cid=register_candidate(draft,record,self.catalog,replacement_reason=reason)
            candidate_ids.append(cid)
            if old!=known(draft,fid):
                changed.append(fid)
            if fid=="project.pv_type" and known(draft,fid) is not None:
                draft.pv_type=known(draft,fid)
        invalidated=self._invalidate_context(draft,changed,set(ids))
        return self._finish(draft,submission_id,payload_hash,candidate_ids,invalidated)

    def revise(self,submission_id,updates,*,expected_revision,reason):
        if not isinstance(reason,str) or not reason.strip():
            raise ContractError("CHANGE_REASON_REQUIRED")
        return self.submit(submission_id,updates,expected_revision=expected_revision,reason=reason)

    def resolve(self,submission_id,field_id,candidate_id,*,expected_revision,reviewer,reason):
        payload={"action":"resolve","field_id":field_id,"candidate_id":candidate_id,"reviewer":reviewer,"reason":reason}
        draft,payload_hash=self._begin(submission_id,payload,expected_revision)
        if draft is None:
            return self._response(True)
        if candidate_id not in draft.candidates:
            raise ContractError("INVALID_CONFLICT_CHOICE",field_id)
        before=known(draft,field_id)
        resolve_conflict(draft,field_id,candidate_id,reviewer=reviewer,reason=reason)
        if field_id=="project.pv_type" and known(draft,field_id) is not None:
            draft.pv_type=known(draft,field_id)
        changed=[field_id] if before!=known(draft,field_id) else []
        invalidated=self._invalidate_context(draft,changed,{field_id})
        return self._finish(draft,submission_id,payload_hash,[candidate_id],invalidated)

    def review(self,submission_id,field_id,*,expected_revision,reviewer,reason,license_status):
        if not reviewer or not reason or license_status!="AUTHORIZED":
            raise ContractError("REVIEW_EVIDENCE_REQUIRED")
        payload={"action":"review","field_id":field_id,"reviewer":reviewer,"reason":reason,"license_status":license_status}
        draft,payload_hash=self._begin(submission_id,payload,expected_revision)
        if draft is None:
            return self._response(True)
        record=deepcopy(draft.values.get(field_id))
        if not record or record["status"] in {"UNKNOWN","CONFLICT","ASSUMED"} or record["source_kind"] not in {"USER_PROVIDED","DOCUMENT_EXTRACTED","EXTERNAL_SOURCE"}:
            raise ContractError("REVIEW_CANNOT_PROMOTE_UNKNOWN_OR_ASSUMPTION",field_id)
        for atom,_ in iter_records({field_id:record},self.catalog):
            if atom["status"] in {"UNKNOWN","CONFLICT","ASSUMED"}:
                raise ContractError("REVIEW_CANNOT_PROMOTE_UNKNOWN_OR_ASSUMPTION",atom["field_id"])
            atom.update(status="VERIFIED",reviewer=reviewer,license_status=license_status,last_updated=datetime.now(timezone.utc).isoformat(),
                        confidence_basis=atom["confidence_basis"]+"；人工复核依据："+reason)
        cid=register_candidate(draft,record,self.catalog,replacement_reason="explicit review: "+reason)
        return self._finish(draft,submission_id,payload_hash,[cid])

    def remove(self,submission_id,field_ids,*,expected_revision,reason):
        if not isinstance(field_ids,list) or not field_ids or not reason:
            raise ContractError("REMOVAL_REASON_REQUIRED")
        payload={"action":"remove","field_ids":field_ids,"reason":reason}
        draft,payload_hash=self._begin(submission_id,payload,expected_revision)
        if draft is None:
            return self._response(True)
        for fid in field_ids:
            if fid not in self.catalog.fields or self.catalog.fields[fid].get("repeat_group"):
                raise ContractError("UNKNOWN_REMOVAL_FIELD")
            old=draft.values.pop(fid,None)
            if old:
                cid="candidate-"+digest(old)
                draft.candidates.setdefault(cid,deepcopy(old))
                draft.history.append({"event":"field_removed","field_id":fid,"candidate_id":cid,"reason":reason})
        invalidated=self._invalidate_context(draft,field_ids,set(field_ids))
        return self._finish(draft,submission_id,payload_hash,invalidated=invalidated)

    def accept_candidates(self,submission_id,parsed,indices,*,expected_revision):
        payload={"action":"accept_candidates","parsed":parsed,"indices":indices}
        draft,payload_hash=self._begin(submission_id,payload,expected_revision)
        if draft is None:
            return self._response(True)
        if parsed.get("status") not in {"PARSED","PARTIAL"} or not isinstance(indices,list) or not indices or len(set(indices))!=len(indices):
            raise ContractError("INVALID_ATTACHMENT_CANDIDATE_SELECTION")
        sha=parsed.get("sha256","")
        if not isinstance(sha,str) or re.fullmatch(r"[0-9a-f]{64}",sha) is None or parsed.get("attachment_id")!="att-"+sha[:16]:
            raise ContractError("INVALID_ATTACHMENT_EVIDENCE")
        ids=[];changed=[]
        for index in indices:
            if type(index) is not int or not 0<=index<len(parsed.get("candidates",[])):
                raise ContractError("INVALID_ATTACHMENT_CANDIDATE_INDEX")
            record=deepcopy(parsed["candidates"][index]);fid=record.get("field_id")
            for atom,_ in iter_records({fid:record},self.catalog):
                if atom.get("source_kind")!="DOCUMENT_EXTRACTED" or atom.get("status")!="UNVERIFIED" or atom.get("source_id")!=parsed["attachment_id"]:
                    raise ContractError("ATTACHMENT_IS_NOT_VERIFIED_DATA")
            before=known(draft,fid)
            ids.append(register_candidate(draft,record,self.catalog))
            if before!=known(draft,fid): changed.append(fid)
        draft.history.append({"event":"attachment_registered","attachment_id":parsed["attachment_id"],"sha256":sha,
                              "source_name":parsed.get("source_name"),"format":parsed.get("format"),"candidate_ids":list(ids)})
        invalidated=self._invalidate_context(draft,changed,set(changed))
        return self._finish(draft,submission_id,payload_hash,ids,invalidated)

    def _invalidate_context(self,draft,changed,exclude):
        geographic=any(fid in {"site.address","site.latitude","site.longitude","site.crs","site.timezone","project.pv_type"} for fid in changed)
        if not geographic:
            return []
        invalidated=[]
        for fid,record in draft.values.items():
            if fid in exclude or not fid.startswith(("resource.","grid.","roof.","load.","tariff.","policy.","site.rights_")):
                continue
            for atom,_ in iter_records({fid:record},self.catalog):
                if atom["status"]=="VERIFIED":
                    atom.update(status="UNVERIFIED",reviewer=None,last_updated=datetime.now(timezone.utc).isoformat(),
                                confidence_basis=atom["confidence_basis"]+"；站址/分类上下文变更，需重新核验")
            invalidated.append(fid)
        if invalidated:
            draft.history.append({"event":"context_invalidated","field_ids":invalidated,"reason":"site/category changed; numeric values preserved"})
        return invalidated

    def status(self):
        return self._response()

    def export(self):
        maturity=evaluate_completeness(self.project,self.catalog)
        snapshot=source_snapshot(self.project,self.catalog)
        normalized={fid:_unwrapped(record) for fid,record in self.project.values.items()}
        business={"schema_version":self.project.schema_version,"baseline_version":self.project.baseline_version,
            "baseline_hashes":self.project.baseline_hashes,"pv_type":self.project.pv_type,"normalized_inputs":normalized,
            "provenance_snapshot":snapshot,"applicability":self.project.applicability}
        base=known(self.project,"storage.base_pv_type") if self.project.pv_type=="pv_storage" else None
        category=category_contract(self.project.pv_type,self.catalog,base_pv_type=base)
        return {"schema_version":"solar-pv-input-export/1.0.0","input_module_version":__version__,"project":self.project.to_dict(),
            "normalized_inputs":normalized,"provenance_records":snapshot["records"],"source_snapshot":snapshot,
            "source_snapshot_id":snapshot["source_snapshot_id"],"input_hash":digest(business),"hash_algorithm_version":"sha256/solar-pv-input-v1",
            "scenario_config":{"pv_type":self.project.pv_type,"base_pv_type":base,"input_contract_id":category["contract_id"],"calculation_status":"NOT_IMPLEMENTED"},
            "input_maturity":maturity,"calculation_status":"NOT_IMPLEMENTED","result_contract_status":"NOT_CREATED"}
