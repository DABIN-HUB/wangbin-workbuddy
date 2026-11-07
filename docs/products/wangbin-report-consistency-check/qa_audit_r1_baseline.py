"""Independent Q05 audit against immutable old ZIP. Expected facts are frozen below, not learned from implementation."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from docx import Document
from openpyxl import Workbook, load_workbook

ZIP = Path('dist/wangbin-report-consistency-check-0.1.3-skill-candidate.zip').resolve()
EXPECTED_SHA = '549111865465d3feb9faf5aaedf69738be6efd48094b1f61dd127e0b29ed9b38'
assert hashlib.sha256(ZIP.read_bytes()).hexdigest() == EXPECTED_SHA
scratch = Path(os.environ['LOCALAPPDATA']) / 'hermes/profiles/wb-quality/cache/scratch'
scratch.mkdir(parents=True, exist_ok=True)
work = Path(tempfile.mkdtemp(prefix='q05-r1-old-', dir=scratch))
with zipfile.ZipFile(ZIP) as z:
    assert z.testzip() is None
    names = z.namelist()
    assert len(names) == len(set(names)) and all('..' not in Path(n).parts and not n.startswith('/') and '\\' not in n for n in names)
    z.extractall(work/'package')
script = work/'package/wangbin-report-consistency-check/scripts/check_report.py'
assert script.exists()

# Explicit expected constraints: equality requires verified operands and matching identity/unit.
CASES = [
    dict(id='F01-formula-cache', cols=[('上期完成率',.1,'0%','=1/10'),('本期完成率',.12,'0%','=12/100')], paragraphs=['完成率由10%提高至12%'], expect='UNVERIFIED_FORMULA_CACHE, formula provenance, no MATCH or DIRECT_CELLS'),
    dict(id='F01-direct-positive', cols=[('上期完成率',.1,'0%',None),('本期完成率',.12,'0%',None)], paragraphs=['完成率由10%提高至12%'], expect='MATCH, 2pp, 20%'),
    dict(id='F02-header-percent', cols=[('上期完成率(%)',10,'General',None),('本期完成率(%)',12,'General',None)], paragraphs=['完成率由10%提高至12%'], expect='MATCH, 10% to 12%, 2pp, 20%'),
    dict(id='F02-zero-prior', cols=[('上期完成率(%)',0,'General',None),('本期完成率(%)',12,'General',None)], paragraphs=['完成率由0%提高至12%'], expect='12pp; relative increase undefined, not 0%'),
    dict(id='F02-unknown-unit', cols=[('上期完成率',.1,'General',None),('本期完成率',.12,'General',None)], paragraphs=['完成率由10%提高至12%'], expect='PENDING_CONFIRMATION; 0.1 alone does not imply 10%'),
    dict(id='F03-normal-table', cols=[('青禾公司6月实际未税收入/CNY/元',1280000,'General',None)], table=[['指标','数值'],['收入','128万元']], expect='one table income indicator MATCH; cell R2C1 and R2C2 traced'),
    dict(id='F03-zero-table', cols=[('青禾公司6月实际未税收入/CNY/元',0,'General',None)], table=[['指标','数值'],['收入','0元']], expect='zero is numeric indicator, not missing'),
    dict(id='F03-empty-table', cols=[('青禾公司6月实际未税收入/CNY/元',0,'General',None)], table=[['指标','数值'],['收入','']], expect='missing table value not zero'),
    dict(id='F04-mapped-profit', cols=[('青禾公司6月实际未税净利润/CNY/元',1280000,'General',None)], paragraphs=['青禾公司6月实际未税净利润为128万元'], context={'mappings':{'净利润':'数据!A2'},'exact':True}, expect='净利润 indicator MATCH; user-provided mapping accepted'),
    dict(id='F05-three-metrics', cols=[('收入/CNY/元',1280000,'General',None),('成本/CNY/元',500000,'General',None),('上期完成率','0.1','0%',None),('本期完成率','0.12','0%',None)], paragraphs=['收入128万元','成本50万元','完成率由10%提高至12%'], expect='three indicators independent: revenue MATCH, cost MATCH, rate MATCH'),
    dict(id='F05-currency', cols=[('收入/USD/元',1280000,'General',None)], paragraphs=['收入128万元人民币'], expect='NOT_COMPARABLE; blank delta'),
    dict(id='F05-period', cols=[('青禾6月累计实际收入/CNY/元',1280000,'General',None)], paragraphs=['青禾6月本月实际收入128万元'], expect='NOT_COMPARABLE; blank delta'),
    dict(id='F05-tax', cols=[('青禾6月含税收入/CNY/元',1280000,'General',None)], paragraphs=['青禾6月未税收入128万元'], expect='NOT_COMPARABLE; blank delta'),
    dict(id='F05-rounding', cols=[('收入/CNY/元',1283500,'General',None)], paragraphs=['收入128.4万元'], context={'rounding':{'收入':{'mode':'ROUND_HALF_UP','places':1}}}, expect='MATCH; raw delta +500'),
    dict(id='F05-no-rounding', cols=[('收入/CNY/元',1283500,'General',None)], paragraphs=['收入128.4万元'], expect='RAW_DIFFERENCE_ROUNDING_PENDING; raw delta +500'),
    dict(id='F05-missing-denominator', cols=[('完成量',10,'General',None),('目标量',None,'General',None)], paragraphs=['完成率100%'], context={'rules':{'完成率':{'op':'ratio','cells':['数据!A2','数据!B2']}}}, expect='MISSING_OPERAND; blank delta'),
    dict(id='F05-zero-denominator', cols=[('完成量',10,'General',None),('目标量',0,'General',None)], paragraphs=['完成率100%'], context={'rules':{'完成率':{'op':'ratio','cells':['数据!A2','数据!B2']}}}, expect='ZERO_DENOMINATOR; blank delta'),
]
records=[]
for case in CASES:
    home=work/case['id']; inp=home/'in'; out=home/'out'; inp.mkdir(parents=True); out.mkdir()
    wb=Workbook(); ws=wb.active; ws.title='数据'
    for col,(header,value,fmt,formula) in enumerate(case['cols'],1):
        cell=ws.cell(1,col,header); cell=ws.cell(2,col,formula if formula else value); cell.number_format=fmt
    source=inp/'source.xlsx'; wb.save(source)
    if case['id']=='F01-formula-cache':
        # openpyxl does not write cached formula values; insert authentic cached values into OOXML.
        import re
        with zipfile.ZipFile(source) as z:
            files={n:z.read(n) for n in z.namelist()}
        xml=files['xl/worksheets/sheet1.xml'].decode()
        for addr,value in [('A2','0.1'),('B2','0.12')]:
            pattern=r'(<c\b[^>]*\br="'+addr+r'"[^>]*>.*?<f>.*?</f><v>)(.*?)(</v>)'
            xml,count=re.subn(pattern,lambda m:m.group(1)+value+m.group(3),xml,count=1)
            assert count==1,addr
        files['xl/worksheets/sheet1.xml']=xml.encode()
        with zipfile.ZipFile(source,'w') as z:
            for name,blob in files.items(): z.writestr(name,blob)
        assert [load_workbook(source,data_only=True).active[x].value for x in ('A2','B2')]==[.1,.12]
    doc=Document()
    for para in case.get('paragraphs',[]): doc.add_paragraph(para)
    if 'table' in case:
        t=doc.add_table(rows=len(case['table']),cols=len(case['table'][0]))
        for i,row in enumerate(case['table']):
            for j,text in enumerate(row): t.cell(i,j).text=text
    report=inp/'report.docx'; doc.save(report)
    if case.get('context') is not None: (inp/'context.json').write_text(json.dumps(case['context'],ensure_ascii=False),encoding='utf-8')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inp.iterdir()}
    cmd=[sys.executable,str(script),'--input-root',str(inp),'--source-xlsx',str(source),'--report-docx',str(report),'--output-dir',str(out)]
    if case.get('context') is not None: cmd+=['--context',str(inp/'context.json')]
    env=os.environ.copy(); env.pop('PYTHONPATH',None)
    p=subprocess.run(cmd,cwd=home,env=env,text=True,capture_output=True,timeout=45)
    record={'id':case['id'],'input':{k:case[k] for k in ('cols','paragraphs','table','context') if k in case},'expected':case['expect'],'command':cmd,'cwd':str(home),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'input_sha256':hashes,'input_unchanged':hashes=={q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in inp.iterdir()}}
    if p.returncode==0:
        data=json.loads(p.stdout)
        book=load_workbook(data['output'])
        record['sheets']={s:[list(row) for row in book[s].values] for s in book.sheetnames}
        record['snapshot']=json.loads(Path(data['snapshot']).read_text(encoding='utf-8'))
        record['output_sha256']={Path(data[k]).name:hashlib.sha256(Path(data[k]).read_bytes()).hexdigest() for k in ('output','snapshot')}
        record['no_output_formula']=all(cell.data_type!='f' for sheet in book for row in sheet for cell in row)
    records.append(record)
    print(case['id'],p.returncode,p.stdout.strip(),p.stderr.strip(),flush=True)
# Independent verdicts check actual reopened XLSX and JSON, not just subprocess status.
expectations={
    'F01-formula-cache':(['UNVERIFIED_FORMULA_CACHE'],None),
    'F01-direct-positive':(['MATCH'],'2.00'),
    'F02-header-percent':(['MATCH'],'2'),
    'F02-zero-prior':(['MATCH'],'12'),
    'F02-unknown-unit':(['PENDING_CONFIRMATION'],None),
    'F03-normal-table':(['MATCH'],None),
    'F03-zero-table':(['MATCH'],None),
    'F03-empty-table':(['MISSING_OPERAND'],None),
    'F04-mapped-profit':(['MATCH'],None),
    'F05-three-metrics':(['MATCH','MATCH','MATCH'],None),
    'F05-currency':(['NOT_COMPARABLE'],None),
    'F05-period':(['NOT_COMPARABLE'],None),
    'F05-tax':(['NOT_COMPARABLE'],None),
    'F05-rounding':(['MATCH'],None),
    'F05-no-rounding':(['RAW_DIFFERENCE_ROUNDING_PENDING'],None),
    'F05-missing-denominator':(['MISSING_OPERAND'],None),
    'F05-zero-denominator':(['ZERO_DENOMINATOR'],None),
}
for record in records:
    actual=record.get('snapshot',{}).get('results',[])
    expected,pp=expectations[record['id']]
    statuses=[r['status'] for r in actual]
    issues=[]
    if record['exit']!=0 or not record['input_unchanged'] or not record.get('no_output_formula'):
        issues.append('CLI/output/input integrity')
    if list(record.get('sheets',{}))!=['核查概览','指标对应','差异明细','待确认口径','未覆盖项']:
        issues.append('five-sheet output')
    if sorted(statuses)!=sorted(expected):
        issues.append(f'statuses expected {expected}, actual {statuses}')
    if pp is not None and (not actual or str(actual[0]['source_value'])!=pp):
        issues.append(f'percentage-point delta expected {pp}')
    if record['id']=='F01-formula-cache' and actual and (not actual[0]['formula'] or actual[0]['provenance']=='DIRECT_CELLS'):
        issues.append('formula provenance hidden')
    if record['id']=='F03-normal-table' and actual and not ('R2C1' in str(actual[0]) and 'R2C2' in str(actual[0])):
        issues.append('table label/value cells not both traced')
    if record['id']=='F05-three-metrics' and sorted(r['metric'] for r in actual)!=['完成率变化','成本','收入']:
        issues.append('income/cost/rate not independently verified')
    if record['id']=='F02-zero-prior' and actual and ('相对增幅未计算' not in actual[0]['explanation']):
        issues.append('zero prior relative growth must remain undefined')
    if record['id']=='F05-rounding' and actual and str(actual[0]['delta']) not in ('500','500.0'):
        issues.append('raw rounding delta must be +500元')
    if record['id'] in ('F05-currency','F05-period','F05-tax','F05-missing-denominator','F05-zero-denominator') and actual and actual[0]['delta'] is not None:
        issues.append('noncomparable/undefined delta populated')
    record['verdict']='PASS' if not issues else 'FAIL'
    record['issues']=issues
path=Path('docs/products/wangbin-report-consistency-check/qa-audit-r1-baseline-results.json')
path.write_text(json.dumps({'product_id':'wangbin-report-consistency-check','archive_sha256':EXPECTED_SHA,'scratch':str(work),'records':records},ensure_ascii=False,indent=2),encoding='utf-8')
print('EVIDENCE',path,'CASES',len(records),'PASS',sum(r['verdict']=='PASS' for r in records),'FAIL',sum(r['verdict']=='FAIL' for r in records))
