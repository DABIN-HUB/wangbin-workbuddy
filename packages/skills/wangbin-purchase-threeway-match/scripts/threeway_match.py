"""Deterministic local PO/receipt/invoice three-way matcher.

Usage: python threeway_match.py --manifest manifest.json --output output
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, sys, zipfile
from xml.etree import ElementTree
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

try:
    from openpyxl import load_workbook, Workbook
except ImportError:  # pragma: no cover
    load_workbook = Workbook = None

SHEETS = ["Match Summary", "Line Results", "Exceptions", "Unmatched Receipts", "Unmatched Invoices", "Source Trace", "Run Manifest"]
SUMMARY_HEADERS = ["comparison_key", "status", "ordered_quantity", "received_quantity", "invoiced_quantity", "receipt_variance", "invoice_variance", "expected_amount", "expected_amount_source", "invoiced_amount", "amount_variance", "weighted_invoice_unit_price", "currency", "invoice_currencies", "invoice_amounts_by_currency", "uom", "exception_codes", "source_file", "source_sheet", "source_row_number"]
EXCEPTION_HEADERS = ["comparison_key", "exception_code", "source_row_reference"]
UNMATCHED_HEADERS = ["po_number", "po_line_id", "item_code", "reason", "source_file", "source_sheet", "source_row_number", "original_key_values", "source_row_hash"]
TRACE_HEADERS = ["po_number", "po_line_id", "item_code", "source_file", "source_sheet", "source_row_number", "original_key_values", "source_row_hash", "currency", "uom", "ordered_quantity", "po_unit_price", "po_amount", "received_quantity", "invoiced_quantity", "invoice_unit_price", "invoice_amount", "_kind", "_reason"]
MANIFEST_HEADERS = ["product_id", "version", "input_files", "row_counts", "limits", "completion_status"]
DEFAULT_LIMITS = {"max_file_bytes": 50*1024*1024, "max_files": 50, "max_batch_bytes": 200*1024*1024}
KEY_FIELDS = ["po_number", "po_line_id", "item_code"]
REQ = {
 "po": KEY_FIELDS + ["ordered_quantity", "po_unit_price", "currency", "uom"],
 "receipt": KEY_FIELDS + ["receipt_number", "receipt_line_id", "received_quantity", "uom"],
 "invoice": KEY_FIELDS + ["invoice_number", "invoice_line_id", "invoiced_quantity", "invoice_unit_price", "invoice_amount", "currency", "uom"],
}

class MatchError(Exception):
    def __init__(self, code: str, message: str): self.code, self.message = code, message

def dec(value: Any) -> Decimal | None:
    if value is None or str(value).strip() in {"", "NA", "-"}: return None
    try:
        result = Decimal(str(value).strip())
        if not result.is_finite(): return None
        return result
    except (InvalidOperation, ValueError): return None

def text(value: Any) -> str:
    return "" if value is None else str(value).strip()

def safe_cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)): value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    s = text(value)
    if s.startswith(("=", "+", "-", "@")): return "'" + s
    return value

def hash_row(row: dict[str, Any]) -> str:
    raw = json.dumps({k: text(row.get(k)) for k in sorted(row)}, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()

def key_of(row: dict[str, Any], case_insensitive=False) -> tuple[str, ...] | None:
    vals = tuple(text(row.get(k)) for k in KEY_FIELDS)
    if any(not x for x in vals): return None
    return tuple(x.casefold() for x in vals) if case_insensitive else vals

def read_file(path: Path, sheet: str | None, kind: str, root: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        actual_sheet = ""
    elif path.suffix.lower() == ".xlsx":
        if load_workbook is None: raise MatchError("INVALID_INPUT", "openpyxl is required for XLSX")
        # Fail closed on active spreadsheet content; data_only=False alone does
        # not make formula cells safe data or report the hazard to the caller.
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if any(name.lower().startswith("xl/externallinks/") or name.lower().endswith("vbaproject.bin") for name in names):
                raise MatchError("INVALID_INPUT", f"{path.name}: XLSX external link or macro is not supported")
            if any(entry.startswith("xl/") and entry.endswith(".rels") and
                   any(link.get("TargetMode", "").lower() == "external" for link in ElementTree.fromstring(archive.read(entry)))
                   for entry in names):
                raise MatchError("INVALID_INPUT", f"{path.name}: XLSX external relationship is not supported")
        wb = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        names = [sheet] if sheet else ([wb.sheetnames[0]] if len(wb.sheetnames) == 1 else [])
        if not names or names[0] not in wb.sheetnames: raise MatchError("INVALID_INPUT", "XLSX worksheet must be explicitly named when ambiguous")
        ws = wb[names[0]]
        if any(cell.data_type == "f" for worksheet in wb for row in worksheet for cell in row):
            raise MatchError("INVALID_INPUT", f"{path.name}: XLSX formula is not supported")
        values = list(ws.values)
        if not values: rows = []
        else:
            headers = [text(v) for v in values[0]]
            rows = [dict(zip(headers, r)) for r in values[1:]]
        actual_sheet = names[0]
    else: raise MatchError("INVALID_INPUT", "unsupported extension")
    out=[]
    for i, row in enumerate(rows, 2):
        row = {str(k): v for k,v in row.items() if k is not None}
        row["source_file"] = path.name; row["source_sheet"] = actual_sheet; row["source_row_number"] = i
        row["original_key_values"] = json.dumps([row.get(k) for k in KEY_FIELDS], ensure_ascii=False, separators=(",", ":"))
        row["source_row_hash"] = hash_row(row)
        row["_kind"] = kind; row["_path"] = str(path)
        out.append(row)
    return out

def tol(config: dict, name: str, variance: Decimal, expected: Decimal | None) -> bool:
    obj=config.get(name, {"mode":"absolute", "value":"0"}); value=dec(obj.get("value", "0")) or Decimal(0)
    allowed=value if obj.get("mode", "absolute")=="absolute" else max(Decimal(0), (abs(expected or Decimal(0))*value))
    return abs(variance) <= allowed

def main_match(manifest: dict[str, Any], output: Path, manifest_dir: Path | None = None) -> dict[str, Any]:
    input_root = manifest.get("input_root", "")
    # A manifest is a portable document: resolve its relative root beside the
    # manifest, not beside the caller's current working directory.
    if manifest_dir is not None and isinstance(input_root, str) and not Path(input_root).is_absolute():
        input_root = str(manifest_dir / input_root)
    root=Path(input_root).resolve()
    if not root.is_dir() or root.is_symlink(): raise MatchError("INVALID_INPUT", "input_root must be a directory")
    out=output.resolve();
    if out == root or root in out.parents: raise MatchError("INVALID_INPUT", "output root must be distinct")
    cfg=manifest.get("config", {}); key_ci=bool(cfg.get("case_insensitive", False)); limits={**DEFAULT_LIMITS, **cfg.get("limits", {})}
    if any(type(limits[name]) is not int or limits[name] < 0 or limits[name] > maximum
           for name, maximum in DEFAULT_LIMITS.items()):
        raise MatchError("INVALID_INPUT", "limits must be nonnegative integers no higher than defaults")
    files=[]; source=[]
    for kind in ("po", "receipt", "invoice"):
        for item in manifest.get(f"{kind}_files", []):
            rel=item.get("path") if isinstance(item, dict) else item; sheet=item.get("sheet") if isinstance(item, dict) else None
            if not isinstance(rel, str) or not rel.strip(): raise MatchError("INVALID_INPUT", "input path is required")
            p=Path(rel)
            if p.is_absolute() or ".." in p.parts: raise MatchError("INVALID_INPUT", "path outside input_root")
            full=(root/p).resolve()
            if not full.is_file() or full.is_symlink() or root not in full.parents: raise MatchError("INVALID_INPUT", "invalid input path")
            if full.suffix.lower() not in {".csv", ".xlsx"}: raise MatchError("INVALID_INPUT", "unsupported extension")
            size=full.stat().st_size
            if size > limits["max_file_bytes"]: raise MatchError("LIMIT_EXCEEDED", f"{full.name}: {size} bytes exceeds file limit {limits['max_file_bytes']}")
            files.append(full)
            if len(files)>limits["max_files"] or sum(p.stat().st_size for p in files)>limits["max_batch_bytes"]:
                raise MatchError("LIMIT_EXCEEDED", f"{full.name}: batch exceeds {limits['max_files']} files or {limits['max_batch_bytes']} bytes")
            source.extend(read_file(full, sheet, kind, root))
    groups={k: [r for r in source if r["_kind"]==k] for k in ("po","receipt","invoice")}
    trace=[]; invalid=[]
    numeric_fields = {
        "po": ("ordered_quantity", "po_unit_price", "po_amount"),
        "receipt": ("received_quantity",),
        "invoice": ("invoiced_quantity", "invoice_unit_price", "invoice_amount"),
    }
    for kind, rows in groups.items():
        for r in rows:
            missing=[f for f in REQ[kind] if text(r.get(f))==""]
            r["_key"]=key_of(r,key_ci)
            malformed=[f for f in numeric_fields[kind] if text(r.get(f)) and dec(r.get(f)) is None]
            negative=[f for f in numeric_fields[kind] if dec(r.get(f)) is not None and dec(r.get(f)) < 0]
            # A complete PO key still identifies the order when a numeric
            # operand is blank. Retain it for comparison, but never aggregate
            # the absent quantity or treat a blank price as zero.
            po_missing_operand = (kind == "po" and r["_key"] is not None
                                  and set(missing) <= {"ordered_quantity", "po_unit_price"}
                                  and not (malformed or negative))
            if missing:
                r["_reason"]="MISSING_REQUIRED_FIELD"; r["_invalid_fields"]=missing
                if not po_missing_operand: invalid.append(r)
            elif malformed or negative:
                r["_reason"]="INVALID_INPUT"; r["_invalid_fields"]=malformed + negative; invalid.append(r)
            elif r["_key"] is None: r["_reason"]="AMBIGUOUS_KEY"; invalid.append(r)
            else: r["_reason"]="INCLUDED"
            trace.append(r)
    pos=defaultdict(list); receipts=defaultdict(list); invoices=defaultdict(list)
    for r in groups["po"]:
        if r.get("_key") is not None and (r.get("_reason")=="INCLUDED" or
            (r.get("_reason")=="MISSING_REQUIRED_FIELD" and
             set(r.get("_invalid_fields", [])) <= {"ordered_quantity", "po_unit_price"})):
            pos[r["_key"]].append(r)
    for r in groups["receipt"]:
        if r.get("_key") is not None and r.get("_reason")=="INCLUDED": receipts[r["_key"]].append(r)
    for r in groups["invoice"]:
        if r.get("_key") is not None and r.get("_reason")=="INCLUDED": invoices[r["_key"]].append(r)
    duplicate_sources=set()
    for kind, rows, ids in (("receipt",groups["receipt"],("receipt_number","receipt_line_id")),("invoice",groups["invoice"],("invoice_number","invoice_line_id"))):
        seen=Counter(tuple(text(r.get(x)) for x in ids) for r in rows)
        duplicate_sources |= {k for k,v in seen.items() if k and v>1}
    results=[]; exceptions=[]; unmatched_r=[]; unmatched_i=[]
    keys=sorted(set(pos)|set(receipts)|set(invoices))
    precedence={"INVALID_INPUT":0,"AMBIGUOUS_KEY":1,"DUPLICATE_PO_KEY":1,"DUPLICATE_SOURCE_ROW":1,"MISSING_REQUIRED_FIELD":2,"CURRENCY_MISMATCH":3,"UOM_MISMATCH":3,"QTY_OVER":4,"QTY_UNDER":4,"PRICE_MISMATCH":5,"AMOUNT_MISMATCH":6}
    for key in keys:
        ps=pos.get(key,[]); rs=receipts.get(key,[]); ins=invoices.get(key,[]); codes=[]
        if len(ps)>1 and not cfg.get("allow_repeated_po_lines",False): codes.append("DUPLICATE_PO_KEY")
        if not ps:
            for r in rs:
                unmatched_r.append({**r,"reason":"ORPHAN_RECEIPT"})
                exceptions.append({"comparison_key":json.dumps(key),"exception_code":"ORPHAN_RECEIPT","source_row_reference":r["source_file"]+":"+str(r["source_row_number"])})
            for r in ins:
                unmatched_i.append({**r,"reason":"ORPHAN_INVOICE"})
                exceptions.append({"comparison_key":json.dumps(key),"exception_code":"ORPHAN_INVOICE","source_row_reference":r["source_file"]+":"+str(r["source_row_number"])})
            continue
        po=ps[0]; oq=dec(po.get("ordered_quantity")); price=dec(po.get("po_unit_price")); po_amt=dec(po.get("po_amount")); rq_values=[dec(r.get("received_quantity")) for r in rs]; iq_values=[dec(r.get("invoiced_quantity")) for r in ins]; ia_values=[dec(r.get("invoice_amount")) for r in ins]
        if any(p.get("_reason")=="MISSING_REQUIRED_FIELD" for p in ps): codes.append("MISSING_REQUIRED_FIELD")
        rq=sum(rq_values,Decimal(0)) if rq_values and all(x is not None for x in rq_values) else None
        iq=sum(iq_values,Decimal(0)) if iq_values and all(x is not None for x in iq_values) else None
        # Keep each original currency separate. A partial same-currency subset
        # must never be presented as the total for all invoice rows.
        invoice_currencies=sorted({text(x.get("currency")) for x in ins if text(x.get("currency"))})
        by_currency=defaultdict(list)
        for invoice in ins:
            by_currency[text(invoice.get("currency"))].append(invoice)
        currency_amounts={currency: str(sum((dec(x["invoice_amount"]) for x in rows), Decimal(0)))
                          for currency, rows in sorted(by_currency.items())
                          if currency and all(dec(x.get("invoice_amount")) is not None for x in rows)}
        same_currency=len(invoice_currencies)==1 and invoice_currencies[0]==text(po.get("currency")) and len(ins)==len(by_currency[invoice_currencies[0]])
        ia=sum(ia_values,Decimal(0)) if same_currency and ia_values and all(x is not None for x in ia_values) else None
        if oq is None or price is None: codes.append("NOT_COMPARABLE")
        # A missing/invalid physical side is unavailable evidence, never a
        # passing comparison. In particular, a receipt row with a missing
        # item_code is excluded above and must prevent MATCHED/matched counts.
        if not rs or rq is None or not ins or iq is None: codes.append("NOT_COMPARABLE")
        rv=(rq-oq) if rq is not None and oq is not None else None; iv=(iq-oq) if iq is not None and oq is not None else None
        if rv is not None and not tol(cfg,"quantity_tolerance",rv,oq): codes.append("QTY_OVER" if rv>0 else "QTY_UNDER")
        if iv is not None and not tol(cfg,"quantity_tolerance",iv,oq): codes.append("QTY_OVER" if iv>0 else "QTY_UNDER")
        currencies={text(x.get("currency")) for x in [po,*ins] if text(x.get("currency"))}; uoms={text(x.get("uom")) for x in [po,*rs,*ins] if text(x.get("uom"))}
        if len(currencies)>1: codes += ["CURRENCY_MISMATCH","NOT_COMPARABLE"]
        if len(uoms)>1: codes += ["UOM_MISMATCH","NOT_COMPARABLE"]
        comparable=same_currency and len(uoms)==1
        weighted=(sum(dec(x.get("invoiced_quantity"))*dec(x.get("invoice_unit_price")) for x in ins)/iq) if comparable and iq and all(dec(x.get("invoiced_quantity")) is not None and dec(x.get("invoice_unit_price")) is not None for x in ins) else None
        if weighted is not None and price is not None and not tol(cfg,"unit_price_tolerance",weighted-price,price): codes.append("PRICE_MISMATCH")
        expected=po_amt if po_amt is not None else ((oq*price) if oq is not None and price is not None else None)
        av=(ia-expected) if comparable and ia is not None and expected is not None else None
        if av is None: codes.append("NOT_COMPARABLE")
        elif not tol(cfg,"amount_tolerance",av,expected): codes.append("AMOUNT_MISMATCH")
        # A document's own arithmetic is meaningful in its original currency
        # and UOM even when PO-vs-invoice monetary comparison is unavailable.
        for invoice in ins:
            qty=dec(invoice.get("invoiced_quantity")); unit_price=dec(invoice.get("invoice_unit_price")); amount=dec(invoice.get("invoice_amount"))
            if qty is not None and unit_price is not None and amount is not None and not tol(cfg,"amount_tolerance",amount-qty*unit_price,qty*unit_price):
                codes.append("AMOUNT_MISMATCH")
        for r in rs+ins:
            ident=tuple(text(r.get(x)) for x in (("receipt_number","receipt_line_id") if r["_kind"]=="receipt" else ("invoice_number","invoice_line_id")))
            if ident in duplicate_sources: codes.append("DUPLICATE_SOURCE_ROW")
        codes=list(dict.fromkeys(codes)); status="MATCHED" if not codes else min(codes,key=lambda x:precedence.get(x,99))
        result={"comparison_key":json.dumps(key,ensure_ascii=False),"status":status,"ordered_quantity":str(oq) if oq is not None else "NOT_AVAILABLE","received_quantity":str(rq) if rq is not None else "NOT_AVAILABLE","invoiced_quantity":str(iq) if iq is not None else "NOT_AVAILABLE","receipt_variance":str(rv) if rv is not None else "NOT_AVAILABLE","invoice_variance":str(iv) if iv is not None else "NOT_AVAILABLE","expected_amount":str(expected) if expected is not None else "NOT_AVAILABLE","expected_amount_source":"SUPPLIED" if po_amt is not None else ("DERIVED" if expected is not None else "NOT_AVAILABLE"),"invoiced_amount":str(ia) if ia is not None else "NOT_AVAILABLE","amount_variance":str(av) if av is not None else "NOT_AVAILABLE","weighted_invoice_unit_price":str(weighted) if weighted is not None else "NOT_AVAILABLE","currency":text(po.get("currency")),"invoice_currencies":";".join(invoice_currencies),"invoice_amounts_by_currency":currency_amounts,"uom":text(po.get("uom")),"exception_codes":";".join(codes),"source_file":po["source_file"],"source_sheet":po["source_sheet"],"source_row_number":po["source_row_number"]}
        results.append(result)
        for c in codes:
            source_rows = (rs + ins) if c == "DUPLICATE_SOURCE_ROW" else [po]
            for source in source_rows:
                if c == "DUPLICATE_SOURCE_ROW":
                    ident=tuple(text(source.get(x)) for x in (("receipt_number","receipt_line_id") if source["_kind"]=="receipt" else ("invoice_number","invoice_line_id")))
                    if ident not in duplicate_sources: continue
                exceptions.append({"comparison_key":result["comparison_key"],"exception_code":c,"source_row_reference":source["source_file"]+":"+str(source["source_row_number"])})
    # Invalid/incomplete physical rows are retained exactly once and do not
    # participate in aggregate keys. This also covers ambiguous keys.
    for r in invalid:
        reason=r["_reason"]
        target=unmatched_r if r["_kind"]=="receipt" else unmatched_i if r["_kind"]=="invoice" else None
        if target is not None: target.append({**r,"reason":reason})
        code = "INVALID_INPUT" if reason == "INVALID_INPUT" else reason
        exceptions.append({"comparison_key":json.dumps(r.get("_key") or json.loads(r["original_key_values"]), ensure_ascii=False),"exception_code":code,"source_row_reference":r["source_file"]+":"+str(r["source_row_number"])})
    out.mkdir(parents=True,exist_ok=False)
    summary={"schema_version":"1.0","run_status":"SUCCEEDED_WITH_EXCEPTIONS" if exceptions or invalid else "SUCCEEDED","totals":{"po_keys":len(results),"matched":sum(x["status"]=="MATCHED" for x in results),"exceptions":len(exceptions)},"exception_code_counts":dict(sorted(Counter(x["exception_code"] for x in exceptions).items())),"line_results":results,"output_file_references":{"workbook":"threeway_match.xlsx","report":"report.md"}}
    manifest_out={"product_id":"wangbin-purchase-threeway-match","version":"0.1.3","input_files":[{"name":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],"row_counts":{k:len(v) for k,v in groups.items()},"limits":limits,"completion_status":summary["run_status"]}
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    exception_lines = [
        f"- `{code}`: {count}"
        for code, count in summary["exception_code_counts"].items()
    ] or ["- None"]
    detail_lines = [
        f"- `{x['exception_code']}` at `{x['source_row_reference']}` for `{x['comparison_key']}`"
        for x in exceptions
    ] or ["- None"]
    missing_invoice_lines = [
        f"- 无法匹配 / cannot match: `{r['source_file']}:{r['source_row_number']}` "
        f"缺少必需的完整键 / missing required exact key ({', '.join(f for f in KEY_FIELDS if not text(r.get(f)))}); "
        "不推断候选 / no candidate inferred."
        for r in unmatched_i
        if r["reason"] == "MISSING_REQUIRED_FIELD" and key_of(r, key_ci) is None
    ]
    report = "\n".join([
        "# 采购三单匹配 / Purchase three-way match",
        "",
        "本地确定性结果；例外需人工复核，不代表批准或付款。",
        "Deterministic local result; exceptions require human review and do not approve payment.",
        "",
        f"- 状态 / Status: `{summary['run_status']}`",
        f"- PO keys / PO 键: `{summary['totals']['po_keys']}`",
        f"- Matched / 已匹配: `{summary['totals']['matched']}`",
        f"- Exceptions / 例外数: `{summary['totals']['exceptions']}`",
        "",
        "## Exception counts / 例外统计",
        *exception_lines,
        "",
        "## Evidence / 证据行引用",
        *detail_lines,
        *missing_invoice_lines,
        *[f"- 币种不可比 / currencies not comparable: `{r['comparison_key']}`; PO {r['currency']} {r['expected_amount']}, invoice {json.dumps(r['invoice_amounts_by_currency'],ensure_ascii=False,sort_keys=True)}; no exchange conversion or cross-currency price/amount variance. See Source Trace for original values."
          for r in results if "CURRENCY_MISMATCH" in r["exception_codes"].split(";")],
        "",
        "See the seven worksheets, especially `Exceptions`, `Unmatched Receipts`, `Unmatched Invoices`, and `Source Trace`.",
        "详见七个工作表，重点查看 `Exceptions`、`Unmatched Receipts`、`Unmatched Invoices` 和 `Source Trace`。",
        "",
    ])
    (out/"report.md").write_text(report, encoding="utf-8")
    if Workbook is not None:
        wb=Workbook(); wb.remove(wb.active)
        line_rows=results
        exception_rows=[{"comparison_key":x["comparison_key"],"exception_code":x["exception_code"],"source_row_reference":x["source_row_reference"]} for x in exceptions]
        trace_rows=[{**{k:v for k,v in r.items() if not k.startswith("_")}, "_kind": r.get("_kind"), "_reason": r.get("_reason")} for r in trace]
        sheet_rows=[results,line_rows,exception_rows,unmatched_r,unmatched_i,trace_rows,[manifest_out]]
        headers=[SUMMARY_HEADERS, SUMMARY_HEADERS, EXCEPTION_HEADERS, UNMATCHED_HEADERS, UNMATCHED_HEADERS, TRACE_HEADERS, MANIFEST_HEADERS]
        for name, rows, hs in zip(SHEETS,sheet_rows,headers):
            ws=wb.create_sheet(name); ws.append([safe_cell(x) for x in hs])
            for row in rows: ws.append([safe_cell(row.get(x)) for x in hs])
        wb.save(out/"threeway_match.xlsx")
    return summary

def cli() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",required=True); ap.add_argument("--output",required=True); args=ap.parse_args()
    manifest_path=Path(args.manifest).resolve()
    try: print(json.dumps(main_match(json.loads(manifest_path.read_text(encoding="utf-8")),Path(args.output),manifest_path.parent),ensure_ascii=False,indent=2)); return 0
    except MatchError as e: print(json.dumps({"run_status":"FAILED_INPUT" if e.code=="INVALID_INPUT" else "FAILED_LIMIT","error_code":e.code,"message":e.message}),file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(cli())
