"""Independent FIX-6 QA from immutable archive; only writes new QA evidence and profile scratch."""
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from openpyxl import load_workbook
import yaml

ROOT = Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check')
DOC = ROOT / 'docs/products/wangbin-tender-analyzer'
SCRATCH = Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch')
SCR = SCRATCH / 'q06_fix6_independent_0213_r1'
ARCH = ROOT / 'dist/wangbin-tender-analyzer-0.2.13-skill-candidate.zip'
FIXTURE = DOC / 'qa-audit-r1-new-027-fixtures-outputs.zip'
BASE = DOC / 'qa-fix5-0210-independent-results.json'
Q0 = DOC / 'qa-fix6-prefreeze-cases.json'
LOCK = DOC / 'qa-fix6-prefreeze-sha.json'
DIMS = ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态')
SHEETS = ['核查概览','要求响应矩阵','附件核对','补遗与版本','待确认事项']
H = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not SCR.exists(), 'one-shot fresh extraction only'
assert H(ARCH) == '3cb421197398c93cfed512d171a1ac2bdea7b413c44685f5a172b24348c5f781'
assert H(BASE) == 'a7886ea08aba45199332a8477f24ed9f5bc518af6db48de138d1fa4a56e90656'
assert H(FIXTURE) == 'a791979b9e6d83b36b8e533cde7f65ab1ac3267ced9a909512827413dbc3c986'
lock=json.loads(LOCK.read_text(encoding='utf-8'))
assert H(Q0)==lock['case_file_sha256'] and H(LOCK)=='0ed79b688e2b631d8c7d4d177df43a85e90e0a2c7b6d3cb491cd6903a722e74e'
base=json.loads(BASE.read_text(encoding='utf-8')); q0=json.loads(Q0.read_text(encoding='utf-8'))
assert len(base['cases'])==94 and len(q0['cases'])==15
manifest=json.loads(Path(str(ARCH)+'.manifest.json').read_text(encoding='utf-8'))
assert manifest['sha256']==H(ARCH) and manifest['version']=='0.2.13' and manifest['id']=='wangbin-tender-analyzer'
assert Path(str(ARCH)+'.sha256').read_text(encoding='utf-8').strip()==H(ARCH)+'  '+ARCH.name
SCR.mkdir(parents=True)
package={'sha256':H(ARCH),'manifest_sha256':H(Path(str(ARCH)+'.manifest.json')),'members':[],'fixture_sha256':H(FIXTURE),'issues':[]}
with zipfile.ZipFile(ARCH) as z:
    assert z.testzip() is None
    names=z.namelist()
    assert len(names)==len(set(names))==len(manifest['members'])==11 and names==[m['path'] for m in manifest['members']]
    for m in manifest['members']:
        name=m['path']; parsed=PurePosixPath(name)
        assert name.startswith('wangbin-tender-analyzer/') and '..' not in parsed.parts and not parsed.is_absolute() and '\\' not in name
        assert not any(s in name.lower() for s in ('/.git/','/.env','__pycache__','/private/'))
        raw=z.read(name)
        assert len(raw)==m['size'] and hashlib.sha256(raw).hexdigest()==m['sha256']==H(ROOT/'packages/skills'/name)
        package['members'].append(m)
    skill=z.read('wangbin-tender-analyzer/SKILL.md').decode('utf-8')
    front=yaml.safe_load(skill.split('---',2)[1])
    assert front['name']==manifest['id'] and front['version']==manifest['version']
    z.extractall(SCR/'extract')
script=SCR/'extract/wangbin-tender-analyzer/scripts/check_response.py'
assert H(script)==next(m['sha256'] for m in manifest['members'] if m['path'].endswith('/scripts/check_response.py'))
# Parse prior independent fixture literals without executing historical runner or developer tests.
def declarations(file, wanted):
    values={}
    def parse(x):
        if isinstance(x,ast.Name): return values[x.id]
        if isinstance(x,(ast.List,ast.Tuple)): return [parse(t) for t in x.elts]
        if isinstance(x,ast.Dict): return {parse(k):parse(v) for k,v in zip(x.keys,x.values)}
        return ast.literal_eval(x)
    for stmt in ast.parse(file.read_text(encoding='utf-8')).body:
        if isinstance(stmt,ast.Assign) and len(stmt.targets)==1 and isinstance(stmt.targets[0],ast.Name) and stmt.targets[0].id in wanted:
            values[stmt.targets[0].id]=parse(stmt.value)
    return values
v4=declarations(DOC/'qa-fix4-029-independent.py', {'P','N','E_NEG','E_POS','E_UNK','variants','holdouts'})
v5=declarations(DOC/'qa-fix5-0210-independent.py', {'P','N','E_NEG','E_POS','E_UNK','U','E_ABS','variants','holdouts','fresh'})
variants={v['id']:v for v in v4['variants']+v4['holdouts']+v5['fresh']}
assert len(variants)==41 and len({c['id'] for c in base['cases']})==94
with zipfile.ZipFile(FIXTURE) as z:
    assert z.testzip() is None
    for record in base['cases']:
        ident=record['id']; case=SCR/'cases'/ident;case.mkdir(parents=True)
        if ident in variants:
            v=variants[ident]
            for name,text in [('tender.txt',v['t']),('response.md',v['r']),*v.get('e',{}).items()]: (case/name).write_text(text,encoding='utf-8')
        else:
            for name in record['input_sha']: (case/name).write_bytes(z.read('cases/'+ident+'/'+name))
        assert {p.name:H(p) for p in case.iterdir()}==record['input_sha'],ident
for record in q0['cases']:
    ident=record['id']; case=SCR/'cases'/ident;case.mkdir(parents=True)
    for name,text in record['inputs'].items(): (case/name).write_bytes(text.encode('utf-8'))
    assert {p.name:H(p) for p in case.iterdir()}==lock['inputs'][ident],ident

def run(ident, prior=None, frozen=None):
    case=SCR/'cases'/ident; out=SCR/'outputs'/ident; out.mkdir(parents=True)
    if prior:
        old=prior['argv']; args=[sys.executable,str(script)]
        flags={'--tender','--response','--attachment-catalog','--evidence-file','--amendment','--project','--mode','--output-dir'}
        i=0
        while i<len(old):
            if old[i] in flags:
                flag=old[i];val=old[i+1]
                if flag in {'--tender','--response','--attachment-catalog','--evidence-file','--amendment'}: val=str(case/Path(val).name)
                elif flag=='--output-dir': val=str(out)
                args.extend((flag,val));i+=2
            else:i+=1
        expected=prior['expected']; origin=prior['origin']
    else:
        args=[sys.executable,str(script),'--tender',str(case/'tender.txt'),'--response',str(case/'response.md'),'--mode','check','--project',ident,'--output-dir',str(out)]
        for name in frozen['inputs']:
            if name not in ('tender.txt','response.md'):args.extend(('--evidence-file',str(case/name)))
        expected=[row['expected'] for row in frozen['rows']];origin='Q0_15'
    env=dict(os.environ);env.pop('PYTHONPATH',None)
    cp=subprocess.run(args,cwd=case,env=env,text=True,encoding='utf-8',capture_output=True,timeout=45)
    files=list(out.iterdir()); issues=[]
    rec={'id':ident,'origin':origin,'argv':args,'cwd':str(case),'exit':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'input_sha':{p.name:H(p) for p in case.iterdir()},'output_sha':{p.name:H(p) for p in files},'expected':expected,'issues':issues}
    if cp.returncode!=0:issues.append('CLI nonzero exit')
    if len(files)!=2 or {p.suffix for p in files}!={'.xlsx','.md'}:
        issues.append('expected exactly one XLSX and one MD');return rec
    xlsx=next(p for p in files if p.suffix=='.xlsx');mdfile=next(p for p in files if p.suffix=='.md')
    md=mdfile.read_text(encoding='utf-8');wb=load_workbook(xlsx,read_only=False,data_only=False)
    rec['sheets']=wb.sheetnames
    if wb.sheetnames!=SHEETS:issues.append('five-sheet order mismatch');return rec
    table=list(wb['要求响应矩阵'].values);rows=[dict(zip(table[0],line)) for line in table[1:]]
    rec['actual']=[[row.get(d) for d in DIMS] for row in rows]
    rec['matrix_rows']=rows
    rec['attachment_rows']=list(wb['附件核对'].values)[1:]
    rec['pending_rows']=list(wb['待确认事项'].values)[1:]
    rec['amendment_rows']=list(wb['补遗与版本'].values)[1:]
    rec['overview_rows']=list(wb['核查概览'].values)
    exp=[expected] if expected and isinstance(expected[0],str) else expected
    if exp is not None and len(rows)!=len(exp):issues.append(f'matrix count {len(rows)} != {len(exp)}')
    for i,row in enumerate(rows):
        if exp and i<len(exp) and exp[i]:
            for d,want in zip(DIMS,exp[i]):
                if want is not None and want!=row.get(d):issues.append(f'row {i+1} {d}: expected {want!r}; actual {row.get(d)!r}')
        if row.get('缺口') and str(row.get('唯一ID')) in md.split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]:issues.append('definite gap falsely listed covered')
        if exp and i<len(exp) and exp[i] and exp[i][1]=='可能不充分' and not row.get('缺口'):issues.append(f'row {i+1} definite gap absent')
    for d in DIMS:
        tally=Counter(row.get(d) for row in rows)
        overview={line[1]:line[2] for line in wb['核查概览'].values if line[0]==d and line[1]!='状态'}
        if dict(tally)!=overview or sum(overview.values())!=len(rows):issues.append('overview accounting mismatch '+d)
    if any(cell.data_type=='f' for sheet in wb for line in sheet for cell in line):issues.append('formula in output workbook')
    if prior:
        if ident in variants:
            v=variants[ident]
            for source in v.get('conflict',[]):
                if source not in str(rows)+str(rec['pending_rows'])+md:issues.append('missing frozen conflict source '+source)
            if v.get('evidence_line') and v['evidence_line'] not in str(rows):issues.append('missing frozen negative evidence line')
            if ident.startswith('F08') and not any('不支持（文本层面）' in str(line) for line in rec['attachment_rows']):issues.append('negative attachment not marked unsupported')
    else:
        if len(rows)!=len(frozen['rows']):return rec
        for i,(row,want) in enumerate(zip(rows,frozen['rows'])):
            rid=str(row.get('唯一ID')); evidence=' '.join(str(v or '') for v in row.values())
            if want['source'] not in str(row.get('来源')):issues.append(f'row {i+1} missing tender source')
            for source in want['response_sources']:
                if source not in str(row.get('响应位置')):issues.append(f'row {i+1} missing response source {source}')
            for source in want.get('excluded_sources',[]):
                if source in str(row.get('响应位置'))+str(row.get('响应内容'))+str(row.get('建议'))+str(row.get('候选及理由')):issues.append(f'row {i+1} cross-object source {source}')
            for source in want.get('evidence_sources',[]):
                if source not in str(row.get('证据位置')):issues.append(f'row {i+1} missing evidence source {source}')
                if source not in str(rec['attachment_rows']):issues.append(f'row {i+1} attachment missing source {source}')
            if want['gap'] is not None:
                section=md.split('## 确定需要补资料（已提供范围）')[-1].split('## 需要人工确认')[0]
                if not row.get('缺口') or rid not in section or rid in md.split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]:issues.append(f'row {i+1} gap/MD mismatch')
                if want['expected'][3]=='不支持（文本层面）' and not any('不支持（文本层面）' in str(line) for line in rec['attachment_rows']):issues.append(f'row {i+1} negative attachment support mismatch')
            if want['pending'] is not None:
                section=md.split('## 需要人工确认')[-1].split('## 已覆盖范围')[0]
                if row.get('缺口') or not any(rid in str(line) for line in rec['pending_rows']) or rid not in section or rid in md.split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]:issues.append(f'row {i+1} pending/MD mismatch')
            if want['md_section']=='已覆盖范围（仅文本层面）' and rid not in md.split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]:issues.append(f'row {i+1} positive MD section absent')
            if ident in ('V05-conflict-negative-first-renumber','V06-conflict-positive-first-renumber','V14-positive-negative-body-conflict'):
                sources=want.get('evidence_sources',[]) if ident.startswith('V14') else want['response_sources']
                if not all(s in evidence+str(rec['pending_rows'])+md for s in sources):issues.append(f'row {i+1} conflict not auditable')
                for source in sources:
                    name,line=source.rsplit(':',1)
                    phrase=frozen['inputs'][name].splitlines()[int(line)-1].strip()
                    if ident.startswith('V14'):
                        for face, text in [('attachment',str(rec['attachment_rows'])), ('matrix',str(row)), ('pending',str(rec['pending_rows'])), ('MD',md)]:
                            if phrase not in text:issues.append('body conflict quotation absent '+source+' in '+face)
                    elif phrase not in str(row.get('响应内容')):issues.append('response conflict quotation absent '+source)
        if rec['amendment_rows'] and any('正式替换' in str(line) and '无已证明正式替换关系' not in str(line) for line in rec['amendment_rows']):issues.append('invented formal amendment replacement')
    rec['md_sha256']=H(mdfile)
    if issues:rec['md_text']=md
    wb.close()
    return rec

results=[]
for prior in base['cases']:results.append(run(prior['id'],prior=prior))
for frozen in q0['cases']:results.append(run(frozen['id'],frozen=frozen))
# Regression probes and original JSON entrypoint execute only extracted bytes.
probe=SCR/'errors';probe.mkdir()
(probe/'tender.txt').write_text('1. 必须支持自动备份。',encoding='utf-8')
(probe/'response.md').write_text('1. 我方支持自动备份。',encoding='utf-8')
(probe/'bad.md').write_bytes(b'\xff\xfe')
(probe/'bad.pdf').write_text('unsupported',encoding='utf-8')
(probe/'bad.xlsx').write_bytes(b'not a spreadsheet')
probes=[('missing',[], 'MISSING_RESPONSE'),('utf8',['--response',str(probe/'bad.md')],'INVALID_UTF8'),('type',['--response',str(probe/'bad.pdf')],'INPUT_TYPE_UNSUPPORTED'),('catalog',['--response',str(probe/'response.md'),'--attachment-catalog',str(probe/'bad.xlsx')],'CATALOG_READ_FAILED'),('escape',['--response',str(probe/'response.md'),'--project','../outside'],'OUTPUT_PATH_INVALID'),('positive',['--response',str(probe/'response.md')],None)]
errors=[]
for name,additional,code in probes:
    out=probe/name;out.mkdir()
    args=[sys.executable,str(script),'--tender',str(probe/'tender.txt'),'--mode','check','--output-dir',str(out),*additional]
    cp=subprocess.run(args,cwd=probe,env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'},capture_output=True,text=True,encoding='utf-8',timeout=45)
    files=list(out.iterdir());ok=(cp.returncode==2 and 'ERROR '+code in cp.stderr and not files) if code else cp.returncode==0 and len(files)==2 and {p.suffix for p in files}=={'.xlsx','.md'}
    errors.append({'id':name,'argv':args,'cwd':str(probe),'exit':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'expected':code or 'successful two outputs','ok':ok,'input_sha':{p.name:H(p) for p in probe.iterdir() if p.is_file()},'output_sha':{p.name:H(p) for p in files}})
legacy_script=script.with_name('analyze_tender.py');legacy_input=script.parent.parent/'examples/fictional-tender.txt'
legacy_cmd=[sys.executable,str(legacy_script),'--input',str(legacy_input)]
legacy_cp=subprocess.run(legacy_cmd,cwd=SCR,env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'},capture_output=True,text=True,encoding='utf-8',timeout=45)
legacy_expected=json.loads((script.parent.parent/'examples/fictional-tender.expected.json').read_text(encoding='utf-8'))
legacy={'argv':legacy_cmd,'cwd':str(SCR),'exit':legacy_cp.returncode,'stdout':legacy_cp.stdout,'stdout_sha256':hashlib.sha256(legacy_cp.stdout.encode('utf-8')).hexdigest(),'stderr':legacy_cp.stderr,'input_sha256':H(legacy_input),'expected_sha256':H(script.parent.parent/'examples/fictional-tender.expected.json'),'ok':legacy_cp.returncode==0 and json.loads(legacy_cp.stdout)==legacy_expected}
counts={origin:{'total':sum(r['origin']==origin for r in results),'pass':sum(r['origin']==origin and not r['issues'] for r in results)} for origin in sorted({r['origin'] for r in results})}
verdict='LOCAL_QA_PASS' if all(not r['issues'] for r in results) and all(x['ok'] for x in errors) and legacy['ok'] and not package['issues'] else 'LOCAL_QA_FAIL'
report={'verdict':verdict,'package':package,'pre_frozen_sha':{'base':H(BASE),'q0':H(Q0),'q0_inputs':H(LOCK)},'counts':counts,'cases':results,'error_probes':errors,'legacy':legacy}
output=DOC/'qa-fix6-0213-independent-results.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
# Preserve real failing source inputs and raw outputs as a separate attached artifact, never the historical evidence.
with zipfile.ZipFile(DOC/'qa-fix6-0213-raw-evidence.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for r in results:
        for p in (SCR/'cases'/r['id']).iterdir():z.write(p,'cases/'+r['id']+'/'+p.name)
        for p in (SCR/'outputs'/r['id']).iterdir():z.write(p,'outputs/'+r['id']+'/'+p.name)
    for p in probe.iterdir():
        if p.is_file():z.write(p,'errors/inputs/'+p.name)
    for p in (probe/'positive').iterdir():z.write(p,'errors/positive/'+p.name)
print(json.dumps({'verdict':verdict,'counts':counts,'error_probes':{x['id']:x['ok'] for x in errors},'legacy':legacy['ok'],'failures':{r['id']:r['issues'] for r in results if r['issues']},'results':str(output)},ensure_ascii=False),flush=True)
sys.exit(verdict!='LOCAL_QA_PASS')
