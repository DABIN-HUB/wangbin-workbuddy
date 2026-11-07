"""Independent, immutable 0.2.9 ZIP QA. Run from any cwd; output only in wb-quality scratch and Q06 QA evidence.
No production import, PYTHONPATH, or developer replay/probe. Original inputs are bytes from the frozen 0.2.7 evidence ZIP.
"""
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
SCRATCH_PARENT = Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch')
SCR = Path(sys.argv[1]) if len(sys.argv) == 2 else SCRATCH_PARENT / 'q06_fix4_independent_029_once'
assert SCR.parent.resolve() == SCRATCH_PARENT.resolve() and SCR.name.startswith('q06_fix4_independent_029_'), 'scratch restricted to profile-owned new QA directory'
ARCH = ROOT / 'dist/wangbin-tender-analyzer-0.2.9-skill-candidate.zip'
OLD = ROOT / 'dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip'
FIXTURE = DOC / 'qa-audit-r1-new-027-fixtures-outputs.zip'
FROZEN = DOC / 'qa-audit-r1-new-027-results.json'
NEW_HASH = 'd5ed3fd8e06c92046dee6ce6db01a53120be65883d3e6e807b8e3f408fde83ce'
OLD_HASH = '12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09'
PREVIOUS_HASH = '8eddf4883c35da2eb645ef97acaf1b6f8d77e8384b01e4256382d26b1ea282be'
FIXTURE_HASH = 'a791979b9e6d83b36b8e533cde7f65ab1ac3267ced9a909512827413dbc3c986'
DIMS = ('响应存在状态', '条件覆盖状态', '附件实际提供状态', '内容支持状态')
SHEETS = ['核查概览', '要求响应矩阵', '附件核对', '补遗与版本', '待确认事项']
H = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not SCR.exists(), 'independent scratch must not exist before execution'
assert H(ARCH) == NEW_HASH and H(OLD) == OLD_HASH and H(FIXTURE) == FIXTURE_HASH
assert H(ROOT / 'dist/wangbin-tender-analyzer-0.2.8-skill-candidate.zip') == PREVIOUS_HASH
old = json.loads(FROZEN.read_text(encoding='utf-8'))
assert old['zip_sha'] == OLD_HASH and len(old['cases']) == 53 and len({c['id'] for c in old['cases']}) == 53
assert sum(bool(c['issues']) for c in old['cases']) == 6
manifest = json.loads(Path(str(ARCH) + '.manifest.json').read_text(encoding='utf-8'))
assert manifest['sha256'] == NEW_HASH and manifest['version'] == '0.2.9' and manifest['id'] == 'wangbin-tender-analyzer'
assert Path(str(ARCH) + '.sha256').read_text(encoding='utf-8').strip() == NEW_HASH + '  ' + ARCH.name
SCR.mkdir(parents=True)
package = {'new_sha256': H(ARCH), 'old_sha256': H(OLD), 'fixture_sha256': H(FIXTURE), 'members': [], 'issues': []}
with zipfile.ZipFile(ARCH) as z:
    assert z.testzip() is None
    names = z.namelist()
    assert len(names) == len(set(names)) == len(manifest['members']) == 11
    assert names == [m['path'] for m in manifest['members']]
    for m in manifest['members']:
        n = m['path']; path = PurePosixPath(n)
        assert n.startswith('wangbin-tender-analyzer/') and not path.is_absolute() and '..' not in path.parts and '\\' not in n
        assert not any(x in n.lower() for x in ('/.git/', '/.env', '__pycache__', '/private/'))
        raw = z.read(n)
        assert len(raw) == m['size'] and hashlib.sha256(raw).hexdigest() == m['sha256']
        assert H(ROOT / 'packages/skills' / n) == m['sha256']
        package['members'].append(m)
    skill = z.read('wangbin-tender-analyzer/SKILL.md').decode('utf-8')
    front = yaml.safe_load(skill.split('---', 2)[1]); assert front['name'] == manifest['id'] and front['version'] == manifest['version']
    assert all(front.get(k) for k in ('display_name', 'display_name_en', 'description', 'description_zh', 'description_en', 'author'))
    assert len(front['examples_zh']) == len(front['examples_en']) == 3
    assert 'openpyxl>=3.1,<4' in skill and 'check_response.py' in skill and 'analyze_tender.py' in skill
    z.extractall(SCR / 'extract')
package['skill_frontmatter'] = front
catalog = json.loads((ROOT / 'products/catalog.json').read_text(encoding='utf-8'))
product = next(x for x in (catalog if isinstance(catalog, list) else catalog['products']) if x['id'] == manifest['id'])
package['catalog_versions'] = {k: product.get(k) for k in ('active_version', 'candidate_version')}
assert '0.2.9' in package['catalog_versions'].values()
base = SCR / 'extract/wangbin-tender-analyzer'
script = base / 'scripts/check_response.py'
assert H(script) == '479284e406316ff9c407cbbe6739b0e1c82af973338a8548457cc1887e850df0'
with zipfile.ZipFile(FIXTURE) as f:
    assert f.testzip() is None
    fixture_names = f.namelist(); assert len(fixture_names) == len(set(fixture_names))
    for c in old['cases']:
        for n, expected_hash in c['input_sha'].items():
            data = f.read('cases/' + c['id'] + '/' + n)
            assert hashlib.sha256(data).hexdigest() == expected_hash
            p = SCR / 'cases' / c['id'] / n; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
package['fixture_members'] = len(fixture_names)

# Independent additions, predeclared expected before any new CLI execution; not copied from developer tests.
P = ('已定位', '已覆盖（文本层面）', '不适用', '不适用')
N = ('已定位', '可能不充分', '不适用', '不适用')
E_NEG = ('已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）')
E_POS = ('已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）')
E_UNK = ('已定位', '待确认', '已提供（可读文本）', '待确认')
variants = [
 {'id':'Z01-current-unavailable','t':'1. 必须支持自动备份。','r':'1. 自动备份目前尚无法提供。','expected':[N]},
 {'id':'Z02-future-instead','t':'1. 必须支持自动备份。','r':'1. 自动备份已经列入下一阶段计划，现阶段无法提供。','expected':[N]},
 {'id':'Z03-positive-installed','t':'1. 必须支持自动备份。','r':'1. 自动备份已部署启用，可正常执行。','expected':[P]},
 {'id':'Z04-unknown-status','t':'1. 必须支持自动备份。','r':'1. 自动备份功能是否已经上线尚待核实。','expected':[('已定位','待确认','不适用','不适用')]},
 {'id':'Z05-two-functions','t':'1. 必须支持自动备份。\n2. 必须支持离线查询。','r':'1. 自动备份尚未投入使用。\n2. 离线查询已部署启用。','expected':[N,P]},
 {'id':'Z06-two-functions-invert','t':'1. 必须支持自动备份。\n2. 必须支持离线查询。','r':'1. 自动备份已部署启用。\n2. 离线查询目前尚无法提供。','expected':[P,N]},
 {'id':'Z07-license-not-issued','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'营业执照尚未颁发，本件是申请材料，不是营业执照。'},'expected':[E_NEG]},
 {'id':'Z08-license-wrapper','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'营业执照示意页；不包含任何证照正文。'},'expected':[E_NEG]},
 {'id':'Z09-license-positive','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'营业执照文本：统一社会信用代码为虚构示例编号。'},'expected':[E_POS]},
 {'id':'Z10-license-uncertain','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'本件仅为登记信息，是否构成正式营业执照尚待核实。'},'expected':[E_UNK]},
 {'id':'Z11-two-materials','t':'1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。','r':'1. 甲类证明已提交。\n2. 乙类证明已提交。','e':{'甲类.txt':'甲类证明文本：甲类有效。','乙类.txt':'乙类证明尚在申请；本文件不是乙类证明。'},'expected':[E_POS,E_NEG]},
 {'id':'Z12-two-materials-reversed','t':'1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。','r':'1. 甲类证明已提交。\n2. 乙类证明已提交。','e':{'甲类.txt':'甲类证明尚未颁发，本件只是申请回执。','乙类.txt':'乙类证明文本：乙类有效。'},'expected':[E_NEG,E_POS]},
 {'id':'Z13-other-material-no-proof','t':'1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。','r':'1. 甲类证明已提交。\n2. 乙类证明已提交。','e':{'乙类.txt':'乙类证明文本：乙类有效。'},'expected':[('已定位','可能不充分','未提供（限已提供材料）','未核验'),E_POS]},
]
for v in variants:
    d = SCR / 'cases' / v['id']; d.mkdir(parents=True, exist_ok=False)
    for name, value in [('tender.txt',v['t']),('response.md',v['r']),*v.get('e',{}).items()]:
        (d / name).write_text(value, encoding='utf-8')

# Independently specified FIX-4 holdouts: new wording and paired controls, not renamed Z01-Z13.
holdouts = [
 {'id':'H01-live-backup','t':'1. 必须支持自动备份。','r':'1. 自动备份现已投入运行，当前可正常执行。','expected':[P]},
 {'id':'H02-disable-backup','t':'1. 必须支持自动备份。','r':'1. 自动备份功能目前未启用，无法按要求运行。','expected':[N]},
 {'id':'H03-not-online','t':'1. 必须支持自动备份。','r':'1. 自动备份尚未上线，暂无法使用。','expected':[N]},
 {'id':'H04-roadmap','t':'1. 必须支持自动备份。','r':'1. 自动备份准备在下一版上线，目前不具备此项能力。','expected':[N]},
 {'id':'H05-design-only','t':'1. 必须支持自动备份。','r':'1. 自动备份只有设计方案，当前尚未实现。','expected':[N]},
 {'id':'H06-unknown-synonym','t':'1. 必须支持自动备份。','r':'1. 自动备份的实际投用情况目前无法确认。','expected':[('已定位','待确认','不适用','不适用')]},
 {'id':'H07-other-function-running','t':'1. 必须支持自动备份。\n2. 必须支持离线查询。','r':'1. 自动备份尚未启用。\n2. 离线查询已经正常运行。','expected':[N,P]},
 {'id':'H08-other-function-negative','t':'1. 必须支持自动备份。\n2. 必须支持离线查询。','r':'1. 自动备份现在可以使用。\n2. 离线查询尚未实现。','expected':[P,N]},
 {'id':'H09-license-application','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'营业执照申请回执：仍在审批，尚未取得营业执照。'},'expected':[E_NEG]},
 {'id':'H10-license-title-only','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'营业执照\n本文件仅有标题，没有证照正文或登记内容。'},'expected':[E_NEG]},
 {'id':'H11-license-denied','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'营业执照尚未核发；这里是申请受理记录，不是有效执照。'},'expected':[E_NEG]},
 {'id':'H12-license-insufficient','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'营业执照材料不完整，缺少正文，仅有封面。'},'expected':[E_NEG]},
 {'id':'H13-license-substantive','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'营业执照文本：名称为虚构星云有限公司；统一社会信用代码为虚构示例编号。'},'expected':[E_POS]},
 {'id':'H14-license-unknown','t':'1. 必须提供营业执照。','r':'1. 营业执照见附件。','e':{'营业执照.txt':'仅有登记摘要；能否作为有效营业执照暂无法确定。'},'expected':[E_UNK]},
 {'id':'H15-other-certificate-not-borrowed','t':'1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。','r':'1. 甲类证明已提交。\n2. 乙类证明已提交。','e':{'乙类.txt':'乙类证明文本：乙类资质有效。'},'expected':[('已定位','可能不充分','未提供（限已提供材料）','未核验'),E_POS]},
 {'id':'H16-two-material-polarity','t':'1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。','r':'1. 甲类证明已提交。\n2. 乙类证明已提交。','e':{'甲类.txt':'甲类证明文本：甲类资质有效。','乙类.txt':'乙类证明尚未核发，只有申请回执。'},'expected':[E_POS,E_NEG]},
]
for v in holdouts:
    d = SCR / 'cases' / v['id']; d.mkdir(parents=True, exist_ok=False)
    for name, value in [('tender.txt',v['t']),('response.md',v['r']),*v.get('e',{}).items()]:
        (d / name).write_text(value, encoding='utf-8')

def execute(id, expected, baseline=None):
    d = SCR / 'cases' / id; out = d / 'out'; out.mkdir(exist_ok=False)
    if baseline:
        prev = baseline['argv']; args = [sys.executable,str(script)]
        for flag in ('--tender','--output-dir','--project','--mode','--response','--attachment-catalog'):
            if flag in prev:
                value = prev[prev.index(flag)+1]
                if flag in ('--tender','--response','--attachment-catalog'): value = str(d / Path(value).name)
                if flag == '--output-dir': value = str(out)
                args += [flag,value]
        for flag in ('--evidence-file','--amendment'):
            for i, entry in enumerate(prev):
                if entry == flag: args += [flag,str(d / Path(prev[i+1]).name)]
        # Keep original argument semantics; order of flags is not meaningful for argparse.
    else:
        args=[sys.executable,str(script),'--tender',str(d/'tender.txt'),'--mode','check','--response',str(d/'response.md'),'--output-dir',str(out),'--project','虚构核验'+id]
        for p in sorted(d.iterdir()):
            if p.name not in ('tender.txt','response.md','out'): args += ['--evidence-file',str(p)]
    inputs = {p.name:H(p) for p in d.iterdir() if p.is_file()}
    env = dict(os.environ); env.pop('PYTHONPATH',None)
    cp = subprocess.run(args,cwd=d,env=env,text=True,capture_output=True,timeout=45)
    rec={'id':id,'origin':'frozen53' if baseline else ('fix3_13' if id.startswith('Z') else 'fix4_holdout'),'argv':args,'cwd':str(d),'exit':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'input_sha':inputs,'output_paths':{'xlsx':str(next((p for p in out.iterdir() if p.suffix=='.xlsx'),'')),'md':str(next((p for p in out.iterdir() if p.suffix=='.md'),''))},'output_sha':{p.name:H(p) for p in out.iterdir()},'expected':expected,'issues':[]}
    issues=rec['issues']
    if baseline and inputs != baseline['input_sha']: issues.append('original input hash changed')
    if cp.returncode: issues.append('CLI nonzero exit')
    outputs=list(out.iterdir()); xls=[p for p in outputs if p.suffix=='.xlsx']; mds=[p for p in outputs if p.suffix=='.md']
    if len(outputs)!=2 or len(xls)!=1 or len(mds)!=1: issues.append('two genuine XLSX+MD outputs expected'); return rec
    try:
        wb=load_workbook(xls[0],read_only=False,data_only=False)
        rec['sheets']=wb.sheetnames
        if wb.sheetnames != SHEETS: issues.append('five sheet names/order')
        matrix=list(wb['要求响应矩阵'].values); cols=matrix[0]; rows=[dict(zip(cols,row)) for row in matrix[1:]]
        rec['matrix_rows']=rows
        rec['actual']=[tuple(row.get(dim) for dim in DIMS) for row in rows]
        exp=([expected] if expected and isinstance(expected,list) and isinstance(expected[0],str) else expected) if isinstance(expected,list) else [expected] if expected else []
        if exp and len(rows)!=len(exp): issues.append('matrix row count expected '+str(len(exp))+' actual '+str(len(rows)))
        for row, want in zip(rows,exp):
            for dim,value in zip(DIMS,want):
                if value is not None and row.get(dim)!=value: issues.append(f"{row.get('唯一ID')} {dim}: expected {value}, actual {row.get(dim)}")
        md=mds[0].read_text(encoding='utf-8'); rec['md_text']=md
        rec['attachment_rows']=list(wb['附件核对'].values)[1:]
        rec['pending_rows']=list(wb['待确认事项'].values)[1:]
        rec['amendment_rows']=list(wb['补遗与版本'].values)[1:]
        rec['overview_rows']=list(wb['核查概览'].values)
        for dim in DIMS:
            tally=Counter(row[dim] for row in rows)
            overview={r[1]:r[2] for r in list(wb['核查概览'].values) if r[0]==dim and len(r)>2 and r[1]!='状态'}
            if dict(tally)!=overview: issues.append('overview mismatch '+dim+': '+str(overview)+' vs '+str(dict(tally)))
        if any(cell.data_type=='f' for sheet in wb for line in sheet for cell in line):issues.append('formula injection in generated workbook')
        for i,row in enumerate(rows):
            rid=str(row.get('唯一ID')); gap=row.get('缺口'); provenance=str(row.get('来源') or '')
            if (gap or row.get('条件覆盖状态')=='可能不充分') and rid not in md:issues.append('MD missing gap row '+rid)
            covered=md.split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]
            if gap and rid in covered:issues.append('MD falsely lists gap as covered '+rid)
            if gap and not provenance:issues.append('gap without provenance '+rid)
            if i<len(exp) and exp[i] and exp[i][1]=='可能不充分' and not gap:issues.append('definite negative missing gap '+rid)
            if id in ('Q02-not-available-yet','Q03-proposed-future','Q05-no-cross-subject','Q06-evidence-not-issued','Q07-evidence-empty-wrapper','Q10-cross-object-negative') or not baseline:
                if i<len(exp) and exp[i] and exp[i][1]=='可能不充分':
                    if f'tender.txt:{i+1}' not in provenance:issues.append('missing tender source '+rid)
                    if f'response.md:{i+1}' not in str(row.get('响应位置') or ''):issues.append('missing response location '+rid)
                    if exp[i][3]=='不支持（文本层面）' and not row.get('证据位置'):issues.append('negative evidence missing position '+rid)
        if id in ('Q10-cross-object-negative','Z11-two-materials','Z12-two-materials-reversed','Z13-other-material-no-proof','H07-other-function-running','H08-other-function-negative','H15-other-certificate-not-borrowed','H16-two-material-polarity'):
            for i,row in enumerate(rows):
                other=2 if i==0 else 1
                if f'response.md:{other}' in str(row.get('响应位置') or ''):issues.append('cross-duty response location '+str(row.get('唯一ID')))
        if id=='V09-amendment' and (len(rows)!=2 or '版本冲突' not in str(rows[1].get('缺口'))):issues.append('formal amendment conflict missing')
        if baseline and id=='R18-no-catalog' and 'certificate.txt:1' not in str(rows[0].get('证据位置')):issues.append('uncatalogued evidence location missing')
        if id in ('Q06-evidence-not-issued','Q07-evidence-empty-wrapper','Q10-cross-object-negative','Z07-license-not-issued','Z08-license-wrapper','Z11-two-materials','Z12-two-materials-reversed','H09-license-application','H10-license-title-only','H11-license-denied','H12-license-insufficient','H16-two-material-polarity'):
            for row in rows:
                if row.get('内容支持状态')=='不支持（文本层面）':
                    if not any(str(row.get('唯一ID')) in str(a) and '不支持（文本层面）' in str(a) for a in rec['attachment_rows']):issues.append('attachment row lacks negative support '+str(row.get('唯一ID')))
        wb.close()
    except Exception as ex:
        issues.append('output decode: '+repr(ex))
    if {p.name:H(p) for p in d.iterdir() if p.is_file()} != inputs:issues.append('source input modified')
    return rec

records=[]
for frozen in old['cases']:
    rec=execute(frozen['id'],frozen['expected'],frozen);records.append(rec)
    print('ORIGINAL',rec['id'],'PASS' if not rec['issues'] else 'FAIL',rec['issues'],flush=True)
for variant in variants:
    rec=execute(variant['id'],variant['expected']);records.append(rec)
    print('VARIANT',rec['id'],'PASS' if not rec['issues'] else 'FAIL',rec['issues'],flush=True)
for variant in holdouts:
    rec=execute(variant['id'],variant['expected']);records.append(rec)
    print('HOLDOUT',rec['id'],'PASS' if not rec['issues'] else 'FAIL',rec['issues'],flush=True)
legacy_cmd=[sys.executable,str(base/'scripts/analyze_tender.py'),'--input',str(base/'examples/fictional-tender.txt')]
cp=subprocess.run(legacy_cmd,cwd=SCR,text=True,capture_output=True,env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'},timeout=45)
with zipfile.ZipFile(OLD) as z: previous=json.loads(z.read('wangbin-tender-analyzer/examples/fictional-tender.expected.json'))
legacy={'argv':legacy_cmd,'exit':cp.returncode,'stdout_sha256':hashlib.sha256(cp.stdout.encode()).hexdigest(),'stderr':cp.stderr,'snapshot_match':cp.returncode==0 and json.loads(cp.stdout)==previous}
# Independent formal error probes, including a success control.
e=SCR/'errors';e.mkdir(); (e/'tender.txt').write_text('1. 必须支持自动备份。',encoding='utf-8');(e/'response.md').write_text('1. 我方支持自动备份。',encoding='utf-8');(e/'bad.md').write_bytes(b'\xff\xfe');(e/'bad.xlsx').write_bytes(b'not xlsx');(e/'bad.pdf').write_text('fake pdf',encoding='utf-8')
err_cases=[('missing_response',['--mode','check'],'MISSING_RESPONSE'),('invalid_utf8',['--mode','check','--response',str(e/'bad.md')],'INVALID_UTF8'),('unsupported',['--mode','check','--response',str(e/'bad.pdf')],'INPUT_TYPE_UNSUPPORTED'),('catalog_corrupt',['--mode','check','--response',str(e/'response.md'),'--attachment-catalog',str(e/'bad.xlsx')],'CATALOG_READ_FAILED'),('project_escape',['--mode','check','--response',str(e/'response.md'),'--project','../outside'],'OUTPUT_PATH_INVALID'),('positive',['--mode','check','--response',str(e/'response.md')],None)]
errors=[]
for name,opts,want in err_cases:
    out=e/name;out.mkdir();cmd=[sys.executable,str(script),'--tender',str(e/'tender.txt'),'--output-dir',str(out),*opts]
    p=subprocess.run(cmd,cwd=e,env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'},text=True,capture_output=True,timeout=45)
    outputs={x.name:H(x) for x in out.iterdir()};passed=(p.returncode==2 and 'ERROR '+want in p.stderr and not outputs) if want else (p.returncode==0 and len(outputs)==2)
    errors.append({'id':name,'argv':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'output_sha':outputs,'pass':passed})
    print('ERROR',name,'PASS' if passed else 'FAIL',p.returncode,flush=True)
assert H(ARCH)==NEW_HASH and H(OLD)==OLD_HASH and H(ROOT / 'dist/wangbin-tender-analyzer-0.2.8-skill-candidate.zip')==PREVIOUS_HASH
summary={'frozen_total':53,'frozen_pass':sum(not r['issues'] for r in records[:53]),'variant_total':len(variants),'variant_pass':sum(not r['issues'] for r in records[53:53+len(variants)]),'holdout_total':len(holdouts),'holdout_pass':sum(not r['issues'] for r in records[53+len(variants):]),'errors_pass':sum(r['pass'] for r in errors),'errors_total':len(errors),'legacy_pass':legacy['snapshot_match'],'old_six':{r['id']:r['issues'] for r in records[:53] if r['id'] in ('Q02-not-available-yet','Q03-proposed-future','Q05-no-cross-subject','Q06-evidence-not-issued','Q07-evidence-empty-wrapper','Q10-cross-object-negative')}}
results={'summary':summary,'package':package,'legacy':legacy,'errors':errors,'cases':records}
(SCR/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
(DOC/'qa-fix4-029-independent-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print('SUMMARY',json.dumps(summary,ensure_ascii=False),flush=True)
