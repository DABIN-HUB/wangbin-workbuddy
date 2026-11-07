"""Independent immutable-archive CLI QA; fictional OOXML, no production import. Run via uv with openpyxl/python-docx."""
import hashlib, json, os, subprocess, sys, zipfile
from pathlib import Path
from decimal import Decimal
from docx import Document
from openpyxl import Workbook, load_workbook

ROOT=Path(__file__).resolve().parents[1]
ZIP=ROOT/'dist/wangbin-report-consistency-check-0.1.4-skill-candidate.zip'
SCRATCH=Path(os.environ['QA_SCRATCH'])
SHEETS=['核查概览','指标对应','差异明细','待确认口径','未覆盖项']
archive_hash=hashlib.sha256(ZIP.read_bytes()).hexdigest()
assert archive_hash=='f1df883c3fd5f8eab84a27b09a931e5e2bdf152fdeebad889caf4c24b0f53a8e'
side=json.loads(ZIP.with_suffix('.zip.manifest.json').read_text(encoding='utf8'))
with zipfile.ZipFile(ZIP) as z:
    assert z.testzip() is None
    names=z.namelist()
    assert len(names)==len(set(names))==len(side['members'])==4
    assert sorted(names)==sorted(m['path'] for m in side['members'])
    for m in side['members']:
        n=m['path']; payload=z.read(n)
        assert n.startswith('wangbin-report-consistency-check/') and '..' not in Path(n).parts
        assert hashlib.sha256(payload).hexdigest()==m['sha256'] and len(payload)==m['size']
        assert payload==(ROOT/'packages/skills'/n).read_bytes(),n
SCRATCH.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(ZIP) as z: z.extractall(SCRATCH/'extracted')
SCRIPT=SCRATCH/'extracted/wangbin-report-consistency-check/scripts/check_report.py'
assert SCRIPT.is_file()
records=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name, cells, paragraphs=(), table=None, context=None, expected=(), prior=None, source_edit=None, report_bytes=None):
    base=SCRATCH/name; inp=base/'input'; out=base/'output'; inp.mkdir(parents=True);out.mkdir()
    w=Workbook();s=w.active
    assert s is not None
    s.title='数据'
    for address,value,fmt in cells:
        s[address]=value
        if fmt:s[address].number_format=fmt
    if source_edit:source_edit(w)
    source=inp/'source.xlsx';w.save(source)
    d=Document()
    for text in paragraphs:d.add_paragraph(text)
    for table_rows in (table or []):
        t=d.add_table(rows=0,cols=len(table_rows[0]))
        for row in table_rows:
            for c,v in zip(t.add_row().cells,row):c.text=str(v)
    report=inp/'report.docx';d.save(report)
    if report_bytes is not None:report.write_bytes(report_bytes)
    if context is not None:(inp/'context.json').write_text(json.dumps(context,ensure_ascii=False),encoding='utf8')
    if prior is not None:(inp/'prior.json').write_bytes(Path(prior).read_bytes())
    old=(sha(source),sha(report));cmd=[sys.executable,str(SCRIPT),'--input-root',str(inp),'--source-xlsx',str(source),'--report-docx',str(report),'--output-dir',str(out)]
    if context is not None:cmd+=['--context',str(inp/'context.json')]
    if prior is not None:cmd+=['--prior-run',str(inp/'prior.json')]
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    proc=subprocess.run(cmd,capture_output=True,text=True,timeout=50,cwd=base,env=env)
    record={'case':name,'command':cmd,'cwd':str(base),'exit':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'input_sha256':{'source':old[0],'report':old[1]},'expected':expected}
    errors=[]
    if proc.returncode!=0:errors.append('CLI expected exit0')
    if old!=(sha(source),sha(report)):errors.append('input modified')
    xlsx=out/'report-数字一致性检查.xlsx'; snapshot=out/'report-数字一致性检查.json'
    if not xlsx.exists() or not snapshot.exists():errors.append('missing output')
    if xlsx.exists() and snapshot.exists():
        wb=load_workbook(xlsx);data=json.loads(snapshot.read_text(encoding='utf8'))
        rows=data['results'];mat={n:list(wb[n].values) for n in wb.sheetnames}
        record['actual']={'results':rows,'sheets':mat,'changes':data.get('changes'), 'output_sha256':{'xlsx':sha(xlsx),'json':sha(snapshot)}}
        if wb.sheetnames!=SHEETS:errors.append('wrong sheets')
        if len(mat.get('核查概览',[]))<7 or len(mat.get('未覆盖项',[]))<2:errors.append('summary/uncovered absent')
        if len(rows)!=len(expected):errors.append(f'result count {len(rows)} != {len(expected)}')
        for i,e in enumerate(expected):
            if i>=len(rows):break
            r=rows[i]
            for k,v in e.items():
                if k=='contains':
                    for key,fragment in v.items():
                        if fragment not in str(r.get(key,'')):errors.append(f'row{i} {key} missing {fragment}')
                elif k=='delta':
                    if (r[k] is None) != (v is None) or (v is not None and Decimal(str(r[k]))!=Decimal(str(v))):errors.append(f'row{i} delta {r[k]} != {v}')
                elif k=='source_value' and v is not None:
                    if r[k] is None or Decimal(str(r[k]))!=Decimal(str(v)):errors.append(f'row{i} source_value {r[k]} != {v}')
                elif r.get(k)!=v:errors.append(f'row{i} {k} {r.get(k)!r} != {v!r}')
            pending=mat['待确认口径'];details=mat['差异明细']; mapping=mat['指标对应']
            if i+1>=len(mapping) or mapping[i+1][12]!=r['status']:errors.append('mapping mismatch')
            if r['status'] in ('MATCH','MISMATCH','RAW_DIFFERENCE_ROUNDING_PENDING'):
                if not any(v[0]==r['metric_id'] and v[19]==r['status'] for v in details[1:]):errors.append('details mismatch')
            else:
                if not any(v[0]==r['metric_id'] and v[6]==r['status'] and v[7] is None for v in pending[1:]):errors.append('pending mismatch')
        for sheet in wb:
            for cellsrow in sheet:
                if any(cell.data_type=='f' for cell in cellsrow):errors.append('unsafe formula output')
        wb.close()
    record['errors']=errors;record['verdict']='FAIL' if errors else 'PASS';records.append(record)
    print(name, record['verdict'], ' / '.join(errors),flush=True)
    return record, snapshot

def C(*row):return list(row)
if __name__=='__main__':
    run('rate-format-7-to-9',C(('A1','上期完成率',None),('B1','本期完成率',None),('A2',.07,'0.0%'),('B2',.09,'0.0%')),['完成率由7%提高至9%'],expected=[{'status':'MATCH','metric':'完成率变化','delta':0,'source_value':'2.0','contains':{'explanation':'28.57','source_cell':'A2','formula':''}}])
    run('rate-header-7-to-9',C(('A1','上期完成率(%)',None),('B1','本期完成率(%)',None),('A2',7,None),('B2',9,None)),['完成率由7%提高至9%'],expected=[{'status':'MATCH','delta':0,'contains':{'explanation':'2.00个百分点','source_cell':'B2'}}])
    run('rate-zero',C(('A1','上期完成率(%)',None),('B1','本期完成率(%)',None),('A2',0,None),('B2',9,None)),['完成率由0%提高至9%'],expected=[{'status':'MATCH','delta':0,'contains':{'explanation':'相对增幅未计算'}}])
    run('rate-unit-unknown',C(('A1','上期完成率',None),('B1','本期完成率',None),('A2',.07,None),('B2',.09,None)),['完成率由7%提高至9%'],expected=[{'status':'PENDING_CONFIRMATION','delta':None}])
    run('rate-formulas',C(('A1','上期完成率(%)',None),('B1','本期完成率(%)',None),('A2','=7/100','0%'),('B2','=9/100','0%')),['完成率由7%提高至9%'],expected=[{'status':'UNVERIFIED_FORMULA_CACHE','delta':None,'source_value':None,'contains':{'formula':'=7/100','provenance':'UNVERIFIED_FORMULA_CACHE'}}])
    run('rate-direction',C(('A1','上期完成率',None),('B1','本期完成率',None),('A2',.12,'0%'),('B2',.10,'0%')),['完成率由12%提高至10%'],expected=[{'status':'MISMATCH','delta':0,'contains':{'explanation':'报告声称提高但来源显示下降'}}])
    run('table-ordinary',C(('B1','收入/CNY/元',None),('B2',1370000,None)),table=[[['指标','数值'],['收入','137万元']]],expected=[{'status':'MATCH','delta':0,'contains':{'where':'表格1!R2C1,表格1!R2C2','source_cell':'B2'}}])
    run('table-zero',C(('B1','收入/CNY/元',None),('B2',0,None)),table=[[['指标','数值'],['收入','0元']]],expected=[{'status':'MATCH','delta':0}])
    run('table-blank',C(('B1','收入/CNY/元',None),('B2',0,None)),table=[[['指标','数值'],['收入','']]],expected=[{'status':'MISSING_OPERAND','delta':None,'contains':{'where':'R2C2'}}])
    run('table-period-columns',C(('A1','本月收入/CNY/元',None),('B1','累计收入/CNY/元',None),('A2',1370000,None),('B2',3000000,None)),table=[[['指标','本月(万元)','累计(万元)'],['收入','137','300']]],expected=[{'status':'MATCH','delta':0},{'status':'MATCH','delta':0}])
    run('mapped-net-profit',C(('A1','青禾公司6月实际未税净利润/CNY/元',None),('A2',1370000,None)),['青禾公司6月实际未税净利润为137万元'],context={'mappings':{'净利润':'数据!A2'}},expected=[{'status':'MATCH','metric':'净利润','delta':0,'contains':{'where':'段落1','rule':'mapping=数据!A2'}}])
    run('three-metrics',C(('A1','青禾公司6月实际未税收入/CNY/元',None),('B1','青禾公司6月实际未税成本/CNY/元',None),('C1','上期完成率(%)',None),('D1','本期完成率(%)',None),('A2',1370000,None),('B2',430000,None),('C2',7,None),('D2',9,None)),['青禾公司6月实际未税收入137万元','青禾公司6月实际未税成本43万元','完成率由7%提高至9%'],expected=[{'status':'MATCH','delta':0},{'status':'MATCH','delta':0},{'status':'MATCH','delta':0}])
    run('no-rule-raw-difference',C(('B1','收入/CNY/元',None),('B2',1283500,None)),['收入128.4万元'],expected=[{'status':'RAW_DIFFERENCE_ROUNDING_PENDING','delta':500}])
    run('round-half-up',C(('B1','收入/CNY/元',None),('B2',1283500,None)),['收入128.4万元'],context={'rounding':{'收入':{'mode':'ROUND_HALF_UP','places':1}}},expected=[{'status':'MATCH','delta':500,'contains':{'explanation':'ROUND_HALF_UP'}}])
    run('mismatch-direction',C(('B1','收入/CNY/元',None),('B2',1280000,None)),['收入125万元'],context={'exact':True},expected=[{'status':'MISMATCH','delta':-30000}])
    run('period-not-comparable',C(('B1','青禾6月累计实际收入/CNY/元',None),('B2',100000,None)),['青禾6月本月实际收入10万元'],expected=[{'status':'NOT_COMPARABLE','delta':None}])
    run('currency-not-comparable',C(('B1','青禾6月收入/USD/元',None),('B2',100,None)),['青禾6月收入100元人民币'],expected=[{'status':'NOT_COMPARABLE','delta':None}])
    run('tax-not-comparable',C(('B1','青禾6月含税收入/CNY/元',None),('B2',100000,None)),['青禾6月未税收入10万元'],expected=[{'status':'NOT_COMPARABLE','delta':None}])
    run('budget-not-comparable',C(('B1','青禾6月收入预算/CNY/元',None),('B2',100000,None)),['青禾6月实际收入10万元'],expected=[{'status':'NOT_COMPARABLE','delta':None}])
    run('missing-denominator',C(('A1','完成量',None),('B1','目标量',None),('A2',10,None)),['完成率100%'],context={'rules':{'完成率':{'op':'ratio','cells':['数据!A2','数据!B2']}}},expected=[{'status':'MISSING_OPERAND','delta':None}])
    run('zero-denominator',C(('A1','完成量',None),('B1','目标量',None),('A2',10,None),('B2',0,None)),['完成率100%'],context={'rules':{'完成率':{'op':'ratio','cells':['数据!A2','数据!B2']}}},expected=[{'status':'ZERO_DENOMINATOR','delta':None}])
    run('ambiguous-two-sources',C(('B1','青禾6月实际收入/CNY/元',None),('C1','青禾6月实际收入/CNY/元',None),('B2',100000,None),('C2',120000,None)),['青禾6月实际收入12万元'],expected=[{'status':'AMBIGUOUS_MAPPING','delta':None,'candidates':['数据!B2','数据!C2']}])
    run('mapped-two-sources',C(('B1','青禾6月实际收入/CNY/元',None),('C1','青禾6月实际收入/CNY/元',None),('B2',100000,None),('C2',120000,None)),['青禾6月实际收入12万元'],context={'mappings':{'收入':'数据!C2'},'exact':True},expected=[{'status':'MATCH','delta':0,'candidates':['数据!C2']}])
    run('formula-direct-unverified',C(('A1','基数',None),('B1','收入/CNY/元',None),('A2',65,None),('B2','=A2*2',None)),['收入130元'],expected=[{'status':'UNVERIFIED_FORMULA_CACHE','delta':None,'contains':{'formula':'=A2*2'}}])
    run('formula-rule-independent',C(('A1','基数',None),('B1','收入/CNY/元',None),('A2',65,None),('B2','=A2*2',None)),['收入130元'],context={'rules':{'收入':{'op':'multiply','cells':['数据!A2'],'constants':['2'],'unit':'元'}}},expected=[{'status':'MATCH','delta':0,'contains':{'formula':'=A2*2','provenance':'INDEPENDENT_RULE_RESULT'}}])
    run('unknown-profit-rule',C(('A1','收入/元',None),('B1','成本/元',None),('A2',100,None),('B2',70,None)),['毛利30元'],expected=[{'status':'PENDING_CONFIRMATION','delta':None}])
    run('no-metric',C(('B1','收入/元',None),('B2',100,None)),['第3.2节 2026-06'],expected=[])
    run('report-conflict',C(('B1','收入/CNY/元',None),('B2',100000,None)),['收入10万元'],table=[[['指标','数值'],['收入','9万元']]],context={'exact':True},expected=[{'status':'MISMATCH','delta':-10000,'contains':{'explanation':'冲突'}},{'status':'MATCH','delta':0,'contains':{'explanation':'冲突'}}])
    common=C(('A1','收入/CNY/元',None),('B1','成本/CNY/元',None),('C1','上期完成率(%)',None),('D1','本期完成率(%)',None),('A2',1250000,None),('B2',430000,None),('C2',7,None),('D2',9,None))
    paragraphs=['收入128万元','成本43万元','完成率由7%提高至9%']
    before,snapshot=run('multi-before',common,paragraphs,context={'exact':True},expected=[{'status':'MISMATCH','delta':30000},{'status':'MATCH','delta':0},{'status':'MATCH','delta':0}])
    updated=[(addr,1280000 if addr=='A2' else val,fmt) for addr,val,fmt in common]
    after,_=run('multi-after',updated,paragraphs,context={'exact':True},prior=snapshot,report_bytes=(SCRATCH/'multi-before/input/report.docx').read_bytes(),expected=[{'status':'MATCH','delta':0},{'status':'MATCH','delta':0},{'status':'MATCH','delta':0}])
    if before['actual']['output_sha256']['json']==after['actual']['output_sha256']['json'] or before['input_sha256']['source']==after['input_sha256']['source'] or list(after['actual']['changes'].values())!=['RESOLVED','UNCHANGED','UNCHANGED']:
        after['errors'].append('multi-round source/hash/change accounting');after['verdict']='FAIL'
    # Two identically valued statements from distinct Word locations must remain independently traceable.
    run('duplicate-positions',C(('A1','收入/CNY/元',None),('A2',100000,None)),['收入10万元','收入10万元'],expected=[{'status':'MATCH','delta':0,'where':'段落1'},{'status':'MATCH','delta':0,'where':'段落2'}])
    # A local corrupted OOXML zip, a spoof, and output-root rejection must remain distinct; no output files are created.
    def negative(name, payload, code, output_in_input=False):
        b=SCRATCH/name;i=b/'input';o=i if output_in_input else b/'out';i.mkdir(parents=True)
        if not output_in_input:o.mkdir()
        source=i/'source.xlsx';source.write_bytes(payload)
        d=Document();d.add_paragraph('收入100元');report=i/'report.docx';d.save(report)
        old=(sha(source),sha(report));cmd=[sys.executable,str(SCRIPT),'--input-root',str(i),'--source-xlsx',str(source),'--report-docx',str(report),'--output-dir',str(o)]
        env=os.environ.copy();env.pop('PYTHONPATH',None)
        p=subprocess.run(cmd,cwd=b,capture_output=True,text=True,env=env,timeout=40)
        err=[]
        if p.returncode!=2 or code not in p.stderr or (sha(source),sha(report))!=old or any(o.glob('*数字一致性检查*')):err.append('expected exit2/'+code+'/immutable inputs/no output')
        rec={'case':name,'command':cmd,'cwd':str(b),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'expected':code,'input_sha256':{'source':old[0],'report':old[1]},'errors':err,'verdict':'FAIL' if err else 'PASS'}
        records.append(rec);print(name,rec['verdict'],err,flush=True)
    negative('spoof-not-zip',b'not a ZIP','UNSUPPORTED_OR_SPOOFED')
    negative('corrupt-real-zip-prefix',b'PK\x03\x04broken central directory','UNREADABLE_OR_ENCRYPTED')
    # Valid source must reach output authorization check.
    valid=(SCRATCH/'multi-before/input/source.xlsx').read_bytes()
    negative('forbidden-output',valid,'OUTPUT_REJECTED',True)
    summary={'archive_sha256':archive_hash,'total':len(records),'passed':sum(r['verdict']=='PASS' for r in records),'failed':[{'case':r['case'],'errors':r['errors']} for r in records if r['errors']],'cases':records}
    path=ROOT/'docs/products/wangbin-report-consistency-check/qa-audit-r1-new-014-results.json';path.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    print('RESULT',summary['passed'],'/',summary['total'],'evidence',path,flush=True)
    sys.exit(1 if summary['failed'] else 0)
