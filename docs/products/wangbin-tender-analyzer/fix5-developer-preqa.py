"""PRE-QA only: immutable original 82 expectations, replay from fresh candidate ZIP.

Run with candidate ZIP path as argument; writes only to this profile's scratch.
Never modifies original independent QA evidence or expected values.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(__file__).resolve().parent
ARCH = Path(sys.argv[1]).resolve() if sys.argv[1] != '--source' else None
ORIGINAL = json.loads((DOC/'qa-fix4-029-independent-results.json').read_text(encoding='utf-8'))
QA = ast.parse((DOC/'qa-fix4-029-independent.py').read_text(encoding='utf-8'))
SHA = lambda b: hashlib.sha256(b).hexdigest()
assert len(ORIGINAL['cases']) == 82
assert SHA((DOC/'qa-fix4-029-independent-results.json').read_bytes()) == '0e99b0fb53d47e80eeb4d4efd8a1d0356ba25ddaefed6e25ba93759bee94421d'
assert ARCH is None or ARCH.name == 'wangbin-tender-analyzer-0.2.10-skill-candidate.zip'

# Parse frozen data declarations only; do not execute the old QA runner (it writes its own report).
names = {}
def frozen(expr):
    if isinstance(expr, ast.Name):
        return names[expr.id]
    if isinstance(expr, ast.Tuple):
        return tuple(frozen(x) for x in expr.elts)
    if isinstance(expr, ast.List):
        return [frozen(x) for x in expr.elts]
    if isinstance(expr, ast.Dict):
        return {frozen(k): frozen(v) for k, v in zip(expr.keys, expr.values)}
    return ast.literal_eval(expr)
for stmt in QA.body:
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        if stmt.targets[0].id in ('P','N','E_NEG','E_POS','E_UNK','variants','holdouts'):
            names[stmt.targets[0].id] = frozen(stmt.value)
variants = {v['id']:v for v in names['variants'] + names['holdouts']}
assert len(variants)==29
assert set(variants) == {r['id'] for r in ORIGINAL['cases'][53:]}
old = json.loads((DOC/'qa-audit-r1-new-027-results.json').read_text(encoding='utf-8'))
assert len(old['cases']) == 53
old_by_id = {r['id']:r for r in old['cases']}
counts = Counter()
failures = []
SCRATCH_PARENT = Path.home()/'AppData/Local/hermes/profiles/wb-developer/cache/scratch'
assert SCRATCH_PARENT.is_dir()
with tempfile.TemporaryDirectory(prefix='fix5-preqa-', dir=SCRATCH_PARENT) as tmp:
    scratch = Path(tmp)
    if ARCH is not None:
        with zipfile.ZipFile(ARCH) as archive:
            assert archive.testzip() is None
            archive.extractall(scratch/'extract')
        script = scratch/'extract/wangbin-tender-analyzer/scripts/check_response.py'
    else:
        script = ROOT/'packages/skills/wangbin-tender-analyzer/scripts/check_response.py'
    with zipfile.ZipFile(DOC/'qa-audit-r1-new-027-fixtures-outputs.zip') as fixture:
        for original in ORIGINAL['cases']:
            ident = original['id']
            group = original['origin']
            case = scratch/'cases'/ident
            case.mkdir(parents=True)
            if ident in old_by_id:
                for filename, sha in original['input_sha'].items():
                    data = fixture.read('cases/'+ident+'/'+filename)
                    assert SHA(data) == sha
                    (case/filename).write_bytes(data)
            else:
                variant = variants[ident]
                for filename, data in [('tender.txt',variant['t']),('response.md',variant['r']),*variant.get('e',{}).items()]:
                    (case/filename).write_text(data, encoding='utf-8')
            assert {p.name:SHA(p.read_bytes()) for p in case.iterdir()} == original['input_sha'], ident
            prior = original['argv']
            args=[sys.executable,str(script)]
            for flag in ('--tender','--output-dir','--project','--mode','--response','--attachment-catalog'):
                if flag in prior:
                    value = prior[prior.index(flag)+1]
                    if flag == '--output-dir':
                        value = str(case/'out')
                        (case/'out').mkdir()
                    elif flag in ('--tender','--response','--attachment-catalog'):
                        value = str(case/Path(value).name)
                    args += [flag,value]
            for flag in ('--evidence-file','--amendment'):
                for pos, entry in enumerate(prior):
                    if entry == flag:
                        args += [flag,str(case/Path(prior[pos+1]).name)]
            run = subprocess.run(args, cwd=case, capture_output=True, text=True, encoding='utf-8',timeout=45,
                                 env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'})
            issues=[]
            if run.returncode != 0:
                issues.append(f'CLI exit {run.returncode}: {run.stderr}')
            outputs = list((case/'out').iterdir())
            if len(outputs)!=2 or {p.suffix for p in outputs}!={'.md','.xlsx'}:
                issues.append('not exactly XLSX+MD')
            if not issues:
                book = load_workbook(next(p for p in outputs if p.suffix=='.xlsx'),read_only=True)
                if book.sheetnames != ['核查概览','要求响应矩阵','附件核对','补遗与版本','待确认事项']:
                    issues.append('five sheet order')
                grid=list(book['要求响应矩阵'].values)
                rows=[dict(zip(grid[0],r)) for r in grid[1:]]
                expected=original['expected']
                expected = [expected] if expected and isinstance(expected[0],str) else expected
                if expected is None:
                    expected = [None] * len(rows)
                if len(rows)!=len(expected):
                    issues.append(f'row count {len(rows)} vs {len(expected)}')
                for row,want in zip(rows,expected):
                    actual = tuple(row[d] for d in ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态'))
                    if want is not None and any(v is not None and v != got for v,got in zip(want,actual)):
                        issues.append(f'{row["唯一ID"]} expected {want} actual {actual}')
                    if row['缺口'] and row['唯一ID'] in next(p for p in outputs if p.suffix=='.md').read_text(encoding='utf-8').split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]:
                        issues.append('gap incorrectly covered in MD')
                for dim in ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态'):
                    tally=Counter(row[dim] for row in rows)
                    overview={r[1]:r[2] for r in book['核查概览'].values if r[0]==dim and len(r)>2 and r[1]!='状态'}
                    if dict(tally)!=overview:
                        issues.append('overview tally '+dim)
                if ident in ('H06-unknown-synonym','H10-license-title-only','H12-license-insufficient'):
                    row=rows[0]
                    md=next(p for p in outputs if p.suffix=='.md').read_text(encoding='utf-8')
                    if ident.startswith('H06'):
                        if row['唯一ID'] not in md.split('## 需要人工确认')[1].split('## 已覆盖范围')[0] or row['缺口']:
                            issues.append('UNKNOWN not pending-only')
                    elif not row['缺口'] or row['唯一ID'] not in md.split('## 确定需要补资料')[1].split('## 需要人工确认')[0] or row['唯一ID'] not in md.split('## 未覆盖范围')[1]:
                        issues.append('missing definite text gap in MD')
                    print('THREE', ident, 'prior', original['actual'], 'new', [tuple(row[d] for d in ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态'))], 'evidence',row['证据位置'],'gap',row['缺口'], 'issues',issues,flush=True)
                book.close()
            counts[(group,'total')]+=1
            counts[(group,'pass' if not issues else 'fail')]+=1
            if issues:
                failures.append((ident,issues))
            print(group,ident,'PASS' if not issues else 'FAIL',issues,flush=True)
    legacy_script = (script.parent/'analyze_tender.py')
    legacy_input = (script.parent.parent/'examples/fictional-tender.txt')
    legacy_expected = json.loads((script.parent.parent/'examples/fictional-tender.expected.json').read_text(encoding='utf-8'))
    legacy = subprocess.run([sys.executable,str(legacy_script),'--input',str(legacy_input)], cwd=scratch,
                            capture_output=True,text=True,encoding='utf-8',timeout=45)
    legacy_ok = legacy.returncode == 0 and json.loads(legacy.stdout) == legacy_expected
    print('LEGACY ZIP SNAPSHOT', 'PASS' if legacy_ok else 'FAIL', 'exit',legacy.returncode,flush=True)
    if not legacy_ok:
        failures.append(('legacy snapshot', [legacy.stderr]))
    err = scratch/'errors'; err.mkdir()
    (err/'tender.txt').write_text('1. 必须支持自动备份。',encoding='utf-8')
    (err/'response.md').write_text('1. 我方支持自动备份。',encoding='utf-8')
    (err/'invalid.md').write_bytes(b'\xff\xfe')
    (err/'bad.pdf').write_text('not supported',encoding='utf-8')
    (err/'bad.xlsx').write_bytes(b'not an xlsx')
    probes=[('missing', [],'MISSING_RESPONSE'),
            ('utf8',['--response',str(err/'invalid.md')],'INVALID_UTF8'),
            ('type',['--response',str(err/'bad.pdf')],'INPUT_TYPE_UNSUPPORTED'),
            ('catalog',['--response',str(err/'response.md'),'--attachment-catalog',str(err/'bad.xlsx')],'CATALOG_READ_FAILED'),
            ('escape',['--response',str(err/'response.md'),'--project','../outside'],'OUTPUT_PATH_INVALID'),
            ('positive',['--response',str(err/'response.md')],None)]
    errors_pass = 0
    for label, opts, code in probes:
        folder = err/label; folder.mkdir()
        cp = subprocess.run([sys.executable,str(script),'--tender',str(err/'tender.txt'),'--mode','check',
                             '--output-dir',str(folder),*opts],cwd=err,capture_output=True,text=True,encoding='utf-8',timeout=45)
        generated=list(folder.iterdir())
        ok = (cp.returncode==2 and 'ERROR '+code in cp.stderr and not generated) if code else (cp.returncode==0 and len(generated)==2)
        errors_pass += ok
        print('ERROR PROBE',label,'PASS' if ok else 'FAIL','exit',cp.returncode,flush=True)
        if not ok:
            failures.append(('error '+label,[str(cp.returncode),cp.stderr]))
print('PRE-QA COUNTS',dict(counts),'error probes',errors_pass,'/ 6','legacy',legacy_ok,flush=True)
print('PRE-QA FAILURES',failures,flush=True)
sys.exit(bool(failures))
