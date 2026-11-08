"""Independent ZIP-only L3 QA; optional isolated product .runtime base."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / 'dist/wangbin-import-precheck-0.1.5-skill-candidate.zip'
SHA = 'f8b4188f6b4fe11a5074a3e6ffc60016f3a1322938b7f28953c1a0a62b6f47ed'
OLD = ROOT.parent / 'wangbin-workbuddy-delivery/six-skills-final/reports/Q01/history/wangbin-import-precheck-0.1.4-skill-candidate.zip'
assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == SHA
assert hashlib.sha256(OLD.read_bytes()).hexdigest() == '536763a9c5d64d5b5b53364f5e6e7be93c13457351624b544a0b722b07955d3c'
configured_base = os.environ.get('WANGBIN_Q01_PROBE_BASE')
if configured_base is None:
    BASE = (Path.home() / 'AppData/Local/hermes/profiles/wb-quality/cache/scratch/q01-015-independent-t_c8518a89').resolve()
    assert ROOT not in BASE.parents and BASE != ROOT
else:
    requested = Path(configured_base)
    runtime = ROOT / '.runtime'
    assert requested.is_absolute() and '..' not in requested.parts
    assert runtime.resolve() == runtime  # Do not follow a redirected temporary root.
    BASE = requested.resolve()
    assert runtime in BASE.parents  # Never write to the product root or arbitrary locations.
BASE.mkdir(parents=True, exist_ok=True)
EXTRACT = BASE / 'extract'
EXTRACT.mkdir(exist_ok=True)
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
    names = z.namelist()
    assert names == sorted(names) and len(names) == len(set(names))
    assert set(names) == {'wangbin-import-precheck/' + n for n in ('README.md','SKILL.md','references/rules.md','scripts/precheck.py')}
    for i in z.infolist():
        assert not i.filename.startswith('/') and '..' not in Path(i.filename).parts and i.file_size < 1000000
    z.extractall(EXTRACT)
SCRIPT = EXTRACT / 'wangbin-import-precheck/scripts/precheck.py'
assert 'version: 0.1.5' in (SCRIPT.parents[1] / 'SKILL.md').read_text(encoding='utf-8')
assert '0.1.5' in (SCRIPT.parents[1] / 'README.md').read_text(encoding='utf-8').splitlines()[0]
manifest = json.loads((ROOT / (str(ARCHIVE.relative_to(ROOT)) + '.manifest.json')).read_text(encoding='utf-8'))
catalog = json.loads((ROOT / 'products/catalog.json').read_text(encoding='utf-8'))
item = next(x for x in catalog['products'] if x['id'] == 'wangbin-import-precheck')
v = next(x for x in item['versions'] if x['version'] == '0.1.5')
assert item['active_version'] == '0.1.4' and v['sha256'] == SHA and manifest['sha256'] == SHA and manifest['version'] == '0.1.5'
assert (ROOT / (str(ARCHIVE.relative_to(ROOT)) + '.sha256')).read_text(encoding='ascii') == f'{SHA}  {ARCHIVE.name}\n'
assert {m['path'] for m in manifest['members']} == set(names)
with zipfile.ZipFile(ARCHIVE) as z:
    for m in manifest['members']:
        assert hashlib.sha256(z.read(m['path'])).hexdigest() == m['sha256'] and len(z.read(m['path'])) == m['size']

def csvfile(p, rows):
    with p.open('w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows(rows)

def bookfile(p, rows, sheets=None):
    wb = Workbook(); ws = wb.active
    for row in rows:
        ws.append(row)
    if sheets:
        ws.title = sheets[0]
        for name in sheets[1:]:
            other = wb.create_sheet(name)
            for row in rows:
                other.append(row)
    wb.save(p)

def snapshot(path):
    wb = load_workbook(path, read_only=False, data_only=False)
    try:
        return {w.title: {'rows': [[v for v in row] for row in w.values],
                          'types': [[w.cell(r,c).data_type for c in range(1,w.max_column+1)] for r in range(1,w.max_row+1)]}
                for w in wb.worksheets}
    finally:
        wb.close()

# Separate independently selected data, especially Z09, text length after strip, mixed reference and numerical/zero boundaries.
CASES = [
 ('map', ['编码','名称','附注'], [['00000000000000000123','笛客户','不夹带']], {'customer_code':{'sources':['编码'],'required':True,'data_type':'text'},'customer_name':{'sources':['名称'],'required':True}}, None, None, None, (1,0,0,0), ['customer_code','customer_name']),
 ('template', ['customer_name','customer_code','extra'], [['青客户','00038','不夹带']], None, None, None, ['customer_code','customer_name'], (1,0,0,0), ['customer_code','customer_name']),
 ('strip', ['名称'], [['   ']], {'customer_name':{'sources':['名称'],'required':True}}, None, {'customer_name':'strip'}, None, (0,1,1,0), ['customer_name']),
 ('length', ['名称'], [[' abc ']], {'customer_name':{'sources':['名称'],'required':True,'min_length':4}}, None, {'customer_name':'strip'}, None, (0,1,1,0), ['customer_name']),
 ('lower-Z09', ['地区'], [['Z09']], {'region':{'sources':['地区'],'required':True,'allowed_values':['Z09'],'reference_key':'region'}}, [['region'],['Z09']], {'region':'lower'}, None, (0,1,2,0), ['region']),
 ('upper-Z09', ['地区'], [['z09']], {'region':{'sources':['地区'],'required':True,'allowed_values':['Z09'],'reference_key':'region'}}, [['region'],['Z09']], {'region':'upper'}, None, (1,0,0,0), ['region']),
 ('collision', ['编码'], [['aB'],['AB']], {'code':{'sources':['编码'],'required':True,'unique_group':'UNIQ'}}, None, {'code':'upper'}, None, (0,2,2,0), ['code']),
 ('missing-ref', ['地区'], [['Z09'],['X77']], {'region':{'sources':['地区'],'required':True,'reference_key':'region'}}, None, None, None, (0,2,0,2), ['region']),
 ('mixed-ref', ['地区'], [['Z09'],['X77']], {'region':{'sources':['地区'],'required':True,'reference_key':'region'}}, [['region'],['Z09']], None, None, (1,1,1,0), ['region']),
 ('ambig-ref', ['地区'], [['Z09'],['X77']], {'region':{'sources':['地区'],'required':True,'reference_key':'region'}}, [['region','备注'],['Z09','A'],['Z09','B']], None, None, (0,2,2,1), ['region']),
 ('ambig-map', ['客户名称','名称'], [['甲','乙']], {'name':{'sources':['客户名称','名称'],'required':True}}, None, None, None, ('NEEDS_INPUT',), None),
 ('zero-null', ['值','批次'], [['0','A'],['NULL','B'],['','C']], {'value':{'sources':['值'],'required':True}}, None, None, None, (2,1,1,0), ['value']),
 ('full-pending', ['地区'], [['Z09']], {'region':{'sources':['地区'],'required':True,'reference_key':'region'}}, None, None, None, ('FULL',), ['region']),
 ('xlsx-text', ['编码','名称'], [['00000000000000000123','丙客户']], {'code':{'sources':['编码'],'required':True,'data_type':'text'},'name':{'sources':['名称'],'required':True}}, None, None, None, (1,0,0,0), ['code','name']),
 ('multisheet', ['编码'], [['A1']], {'code':{'sources':['编码'],'required':True}}, None, None, None, ('NEEDS_INPUT',), None),
 ('formula-text', ['名称','批次'], [['=1+1','A'],['+SUM(1,2)','B'],['-1+2','C'],['@SUM(1,2)','D']], {'name':{'sources':['名称'],'required':True}}, None, None, None, (4,0,0,0), ['name']),
 ('regression', ['编码','名称','地区'], [['00123','甲','R01'],['00123','乙','R99'],['123','丙','R02'],['00007','','R01']], {'code':{'sources':['编码'],'required':True,'unique_group':'code','data_type':'text'},'name':{'sources':['名称'],'required':True},'region':{'sources':['地区'],'reference_key':'region'}}, [['region'],['R01'],['R02']], None, None, (1,3,4,0), ['code','name','region']),
]
all_results = {'product_id':'wangbin-import-precheck','task_id':'t_c8518a89','zip_sha256':SHA,'old_zip_sha256':hashlib.sha256(OLD.read_bytes()).hexdigest(), 'extracted_script':str(SCRIPT),'python':sys.version,'manifest':manifest,'cases':{},'failures':[]}
for cid, headers, rows, fields, refs, transforms, template, expected, cols in CASES:
    directory = BASE / cid; directory.mkdir(exist_ok=True)
    src = directory / ('source.xlsx' if cid in ('xlsx-text','multisheet') else 'source.csv')
    if src.suffix == '.xlsx': bookfile(src,[headers,*rows], ['客户','备份'] if cid == 'multisheet' else None)
    else: csvfile(src,[headers,*rows])
    output = directory / 'output'; output.mkdir(exist_ok=True)
    command = [sys.executable,str(SCRIPT),'--input',str(src),'--output-dir',str(output)]
    if cid != 'multisheet': command += ['--authorization','本轮明确授权隔离目录生成核对副本','--candidate' if cid == 'full-pending' else '--split']
    if template:
        template_path = directory / 'template.csv'; csvfile(template_path,[template]); command += ['--template',str(template_path)]
    elif fields is not None:
        rule_path = directory / 'rules.json'; rule_path.write_text(json.dumps({'fields':fields},ensure_ascii=False),encoding='utf-8'); command += ['--rules',str(rule_path)]
    if refs:
        ref_path = directory / 'reference.csv'; csvfile(ref_path,refs); command += ['--reference',str(ref_path)]
    if transforms: command += ['--transforms',json.dumps(transforms,ensure_ascii=False)]
    before = hashlib.sha256(src.read_bytes()).hexdigest()
    env = dict(os.environ); env.pop('PYTHONPATH',None)
    run = subprocess.run(command,cwd=EXTRACT,env=env,text=True,capture_output=True)
    try: receipt = json.loads(run.stdout if run.stdout else run.stderr)
    except json.JSONDecodeError: receipt = {}
    result = {'command':command,'cwd':str(EXTRACT),'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'input_sha256':before,'receipt':receipt,'workbooks':{},'assertions':[]}
    def check(predicate, label):
        result['assertions'].append({'check':label,'pass':bool(predicate)})
        if not predicate: all_results['failures'].append(f'{cid}: {label}')
    check(hashlib.sha256(src.read_bytes()).hexdigest() == before,'source bytes unchanged')
    for label,path in receipt.get('outputs',{}).items():
        result['workbooks'][label] = {'path':path,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'sheets':snapshot(path)}
    check(run.returncode == 0,'CLI exit 0')
    if expected == ('NEEDS_INPUT',):
        check(receipt.get('status') == 'NEEDS_INPUT' and not result['workbooks'],'ambiguity needs input and no output')
    else:
        check(bool(result['workbooks'].get('report')),'five-sheet report present')
        report = result['workbooks'].get('report',{}).get('sheets',{})
        check(set(report) == {'检查概览','字段映射','问题明细','变更记录','未检查项'},'report five sheets')
        overview = dict(report.get('检查概览',{}).get('rows',[])[1:])
        check(str(overview.get('源SHA256')) == before,'report source SHA matches')
        candidate = result['workbooks'].get('candidate',{}).get('sheets',{})
        check(candidate.get('候选数据',{}).get('rows',[None])[0] == cols,'target columns exact and ordered')
        if expected == ('FULL',):
            check(receipt.get('pending_records') == 1 and receipt.get('candidate_records') == 1 and '资格追踪_不可直接导入' in candidate,'full copy explicitly flags pending')
        else:
            c,q,f,p = expected
            check(receipt.get('candidate_records') == c and receipt.get('quarantine_records') == q and receipt.get('findings') == f and receipt.get('pending_records') == p,'counts match independent expected')
            check(len(candidate.get('候选数据',{}).get('rows',[]))-1 == c,'reopened candidate row count')
            isolated = result['workbooks'].get('quarantine',{}).get('sheets',{}).get('隔离记录',{}).get('rows',[])
            check(len(isolated)-1 == q and c+q == len(rows),'quarantine reopen and conservation')
            check(len({str(row[0]) for row in isolated[1:]}) == q,'quarantine distinct row ids')
            if cid == 'map': check(candidate['候选数据']['rows'][1] == ['00000000000000000123','笛客户'] and candidate['候选数据']['types'][1] == ['s','s'],'long textual code preserved, no extra fields')
            if cid == 'template': check(candidate['候选数据']['rows'][1] == ['00038','青客户'],'template target order and extra source omitted')
            if cid == 'regression': check(receipt.get('duplicate_groups') == 1 and receipt.get('affected_records') == 3 and candidate['候选数据']['rows'][1] == ['123','丙','R02'],'A01/A11 regression findings, duplicate and qualified row')
            if cid == 'formula-text': check(bool(candidate.get('候选数据')) and all(x == 's' for t in candidate.get('候选数据',{}).get('types',[])[1:] for x in t),'potential formula payload is literal string')
            if cid == 'ambig-ref': check('PENDING_VERIFICATION' in str(isolated[1]) and 'VIOLATION' in str(isolated[2]),'ambiguous key distinct from invalid key')
            if cid == 'missing-ref': check(all('PENDING_VERIFICATION' in str(r) for r in isolated[1:]),'missing reference is pending not false positive')
    all_results['cases'][cid] = result
EVIDENCE = Path(os.environ.get('WANGBIN_Q01_PROBE_EVIDENCE', str(Path(__file__).with_name('audit-r1-015-independent-results.json'))))
EVIDENCE.write_text(json.dumps(all_results,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print(json.dumps({'evidence':str(EVIDENCE),'cases':len(CASES),'assertions':sum(len(x['assertions']) for x in all_results['cases'].values()),'failures':all_results['failures']},ensure_ascii=False,indent=2))
sys.exit(1 if all_results['failures'] else 0)
