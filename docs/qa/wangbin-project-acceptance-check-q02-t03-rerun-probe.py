"""Independent frozen-contract ZIP black-box rerun; fictional fixtures only."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from docx import Document
from openpyxl import load_workbook

REPO = Path(__file__).resolve().parents[2]
PRODUCT = 'wangbin-project-acceptance-check'
PREFIX = '星桥演示平台'
ZIP = REPO / 'dist' / f'{PRODUCT}-0.1.2-skill-candidate.zip'
META = json.loads((Path(str(ZIP) + '.manifest.json')).read_text(encoding='utf-8'))
RESULT = {'source_commit': '54e0fd900cfd9cb2c71f9256e22dd23f25244660', 'zip_sha256': hashlib.sha256(ZIP.read_bytes()).hexdigest(), 'members': [], 'cases': {}, 'checks': {}}
assert RESULT['zip_sha256'] == META['sha256'] == Path(str(ZIP) + '.sha256').read_text(encoding='utf-8').split()[0]
assert META['version'] == '0.1.2' and META['id'] == PRODUCT
assert len(META['members']) == 9

with tempfile.TemporaryDirectory(prefix='q02-rerun-', dir=Path.home()/'AppData/Local/hermes/profiles/wb-quality/cache/scratch') as tmp:
    base = Path(tmp)
    extract = base / 'clean'; extract.mkdir()
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist())) == 9
        assert set(z.namelist()) == {m['path'] for m in META['members']}
        for member in META['members']:
            path = member['path']
            assert not path.startswith('/') and '\\' not in path and '..' not in Path(path).parts
            data = z.read(path)
            assert len(data) == member['size'] and hashlib.sha256(data).hexdigest() == member['sha256']
            source = REPO/'packages/skills'/path
            assert source.is_file() and source.read_bytes() == data, path
            RESULT['members'].append({'path': path, 'sha256': member['sha256'], 'size': member['size']})
        z.extractall(extract)
    script = extract/PRODUCT/'scripts/check_acceptance.py'
    assert script.is_file()
    def case(name, files, scope=(), delivery=(), evidence=(), changes=(), version='', prior=None, expected_exit=0):
        root = base/name; root.mkdir(); out = root/'output'; out.mkdir()
        for rel, data in files.items():
            target = root/rel; target.parent.mkdir(parents=True, exist_ok=True)
            if callable(data): data(target)
            elif isinstance(data, bytes): target.write_bytes(data)
            else: target.write_text(data, encoding='utf-8')
        args = [sys.executable, str(script), '--project-name', PREFIX, '--authorized-input-root', str(root), '--output-dir', str(out)]
        for flag, values in (('--scope-source',scope),('--delivery-source',delivery),('--evidence-source',evidence),('--change-source',changes)):
            for value in values: args.extend([flag,value])
        if version: args.extend(['--effective-version-ref', version])
        if prior: args.extend(['--previous-snapshot', prior])
        proc = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')
        record = {'args': args[2:], 'exit': proc.returncode, 'expected_exit': expected_exit, 'stdout': proc.stdout.strip(), 'stderr': proc.stderr.strip(), 'files': {k: hashlib.sha256((root/k).read_bytes()).hexdigest() for k in files}}
        snap_path = out/f'{PREFIX}-核查快照.json'
        snap = None
        if snap_path.exists():
            snap = json.loads(snap_path.read_text(encoding='utf-8'))
            wb = load_workbook(out/f'{PREFIX}-验收资料核对.xlsx', read_only=False, data_only=False)
            sheets = {ws.title: [[cell.value for cell in row] for row in ws] for ws in wb.worksheets}
            formula_count = sum(cell.data_type == 'f' for ws in wb.worksheets for row in ws for cell in row)
            wb.close()
            doc = Document(out/f'{PREFIX}-验收准备报告.docx')
            paragraphs = [p.text for p in doc.paragraphs]
            tables = [[[c.text for c in row.cells] for row in table.rows] for table in doc.tables]
            record.update(snapshot=snap, sheets=sheets, docx_paragraphs=paragraphs, docx_tables=tables, formula_count=formula_count)
            assert list(sheets) == ['核查概览','要求追踪','证据索引','缺口与不符合','冲突与待确认','本次更新']
            assert formula_count == 0
            assert all(r['requirement_id'] in str(sheets['要求追踪']) and r['requirement_id'] in str(tables) and r['status'] in str(sheets['要求追踪']) and r['status'] in str(paragraphs) for r in snap['requirements'])
            assert all(f['id'] in str(sheets['缺口与不符合']) and f['id'] in str(tables) for f in snap['findings'])
            assert all(c['type'] in str(sheets['冲突与待确认']) and c['type'] in str(paragraphs) for c in snap['conflicts'])
            assert '验收准备报告' in paragraphs[0] and '草稿' in paragraphs[0]
            assert '项目已通过验收' not in str(paragraphs) and '项目已通过验收' not in str(tables)
            for src in snap['sources']:
                if src['path'] in files:
                    assert src['sha256'] == record['files'][src['path']], (name, src)
            for ev in snap['evidence']:
                loc = ev['source']
                path = loc.split('/行')[0].split('/表')[0].split('/工作表')[0]
                if path not in files:
                    assert prior and path in {s['path'] for s in json.loads((root/prior).read_text(encoding='utf-8'))['sources']}, (name,loc)
                    continue
                assert loc in str(sheets['证据索引']), (name,loc)
                if '/行' in loc and path.endswith(('.md','.txt')):
                    line = int(loc.split('/行')[1].split('/')[0].split('-')[0])
                    content = (root/path).read_text(encoding='utf-8-sig').splitlines()
                    assert 1 <= line <= len(content) and ev['text'] in content[line-1], (name,loc,ev['text'])
        RESULT['cases'][name] = record
        assert proc.returncode == expected_exit, (name,proc.returncode,proc.stderr)
        return snap, root, record
    def check(name, ok):
        RESULT['checks'][name] = bool(ok)
    scope_text='R01：提供包含端点、请求参数和返回字段的接口文档。\nR02：提供 Windows Server 2019 部署说明。\nR03：提供本项目培训记录。\n'
    a01, root, rec = case('A01', {'scope.md':scope_text, 'interface.md':'D01：接口文档端点 /demo/items，请求参数：item_id，返回字段：name。\n', 'deploy.md':'D02：仅 Ubuntu 部署步骤，未提供 Windows Server 2019 步骤。\n'}, ['scope.md'], ['interface.md','deploy.md'],version='scope.md')
    a01_record=rec
    r=a01['requirements']; gap=a01['findings']
    check('A01_D1', [x['status'] for x in r]==['EVIDENCE_FOUND','NONCONFORMING','NO_EVIDENCE_FOUND'] and a01['coverage']=='3/5' and len(r[0]['results'])==3 and any(g['type']=='NONCONFORMING' and 'deploy.md/行1' in g['sources'] for g in gap) and any(g['type']=='MISSING' and g['requirement_id']==r[1]['requirement_id'] for g in gap) and 'deploy.md/行1' in str(rec['sheets']['要求追踪']) and 'NONCONFORMING' in str(rec['docx_tables']))
    previous=(root/'output'/f'{PREFIX}-核查快照.json').read_bytes()
    a02,_,_=case('A02',{'scope.md':'R01：提供接口文档和部署说明。\n','interface.md':'接口文档包含授权接口说明。\n'},['scope.md'],['interface.md'],version='scope.md')
    check('A02',len(a02['requirements'][0]['results'])==2 and a02['requirements'][0]['status']=='PARTIAL_EVIDENCE' and a02['coverage']=='1/2' and any(g['type']=='MISSING' for g in a02['findings']))
    a03,_,_=case('A03',{'scope.md':'R01：提供部署说明。\n','deliverables.csv':'名称,版本,要求原文\n部署说明,v1,仅 Ubuntu 部署说明\n部署说明,v2,Windows 部署说明\n'},['scope.md'],['deliverables.csv'],version='scope.md')
    check('A03',a03['coverage']=='N/A' and a03['requirements'][0]['status']=='CONFLICT' and any(c['type']=='VERSION_CONFLICT' and len(c['sources'])==2 for c in a03['conflicts']))
    a04,_,_=case('A04',{'a.csv':'原始编号,要求原文\nR01,提供接口文档\n','b.csv':'原始编号,要求原文\nR01,提供培训记录\n'},['a.csv','b.csv'],version='a.csv')
    check('A04',len(a04['requirements'])==len({r['requirement_id'] for r in a04['requirements']})==2 and len({r['source'] for r in a04['requirements']})==2 and any(c['type']=='DUPLICATE_ID' for c in a04['conflicts']))
    a05,_,rec=case('A05',{'scope.md':'R01：提供包含端点、请求参数和返回字段的接口文档。\n','list.csv':'名称\n接口说明.docx\n'},['scope.md'],['list.csv'],version='scope.md')
    check('A05',a05['requirements'][0]['status']=='NO_EVIDENCE_FOUND' and 'LISTED_ONLY' in str(rec['sheets']['证据索引']))
    a06,_,rec=case('A06',{'scope.md':'R03：提供本项目培训记录。\n','dev.md':'R03 开发完成\n'},['scope.md'],['dev.md'],version='scope.md')
    check('A06',a06['requirements'][0]['status']=='NO_EVIDENCE_FOUND' and 'CLAIM_ONLY' in str(rec['sheets']['证据索引']))
    a07,_,_=case('A07',{'scope.md':'R01：提供用户登录功能测试结果。\nR02：提供用户登录安全测试记录。\n','x.md':'用户登录测试通过。\n','y.md':'用户登录功能测试通过。\n'},['scope.md'],evidence=['x.md','y.md'],version='scope.md')
    check('A07',all(r['status']=='PENDING_CONFIRMATION' for r in a07['requirements']) and all(c['type']=='MAPPING_CANDIDATE' and len(c['sources'])>=2 for c in a07['conflicts']) and a07['coverage']=='0/2')
    a08,_,_=case('A08',{'scope.md':scope_text,'change.md':'新增离线模式\n'},['scope.md'],changes=['change.md'],version='scope.md')
    check('A08',len(a08['requirements'])==3 and any(c['type']=='UNCONFIRMED_CHANGE' and any('change.md/行1' in x for x in c['sources']) for c in a08['conflicts']))
    a09,_,rec=case('A09',{'before.json':previous,'training.md':'星桥演示平台 R03 培训记录：2026-01-10 培训议程及签到说明\n'},delivery=['training.md'],prior='before.json')
    check('A09_D1', [x['status'] for x in a09['requirements']]==['EVIDENCE_FOUND','NONCONFORMING','EVIDENCE_FOUND'] and [x['requirement_id'] for x in a09['requirements']]==[x['requirement_id'] for x in a01['requirements']] and any(u['type']=='RESOLVED' and u['evidence'] for u in a09['updates']) and any(u['type']=='UNCHANGED' for u in a09['updates']) and 'RESOLVED' in str(rec['sheets']['本次更新']))
    a10,_,_=case('A10',{'scope.md':'R01：提供接口文档。\n','fail.md':'R01 接口文档测试失败。\n','pass.md':'R01 接口文档测试通过。\n'},['scope.md'],evidence=['fail.md','pass.md'],version='scope.md')
    check('A10',a10['requirements'][0]['status']=='CONFLICT' and any(c['type']=='EVIDENCE_CONFLICT' and len(c['sources'])==2 for c in a10['conflicts']))
    def doc_fixture(p):
        d=Document(); t=d.add_table(rows=2,cols=2); t.cell(0,0).text='编号';t.cell(0,1).text='要求原文';t.cell(1,0).text='R03';t.cell(1,1).text='提供本项目培训记录';d.save(p)
    a11,_,_=case('A11',{'scope.docx':doc_fixture},['scope.docx'],version='scope.docx')
    check('A11',a11['requirements'][0]['status']=='NO_EVIDENCE_FOUND' and '表1/行2/列2' in a11['requirements'][0]['source'])
    a12,_,_=case('A12',{'scope.md':'R01：提供接口文档。\n','broken.docx':b'PK\x03\x04broken','fake.docx':'I am not a DOCX','diagram.pdf':b'%PDF-1.7 fake','test.csv':'证据原文,关联要求\nR01 接口文档测试通过,R01\n'},['scope.md'],evidence=['broken.docx','fake.docx','diagram.pdf','test.csv'],version='scope.md',expected_exit=3)
    check('A12_D3',a12['requirements'][0]['status']=='EVIDENCE_FOUND' and any('broken.docx' in s and 'UNREADABLE_SOURCE' in s for s in a12['limitations']) and any('fake.docx' in s and 'UNSUPPORTED_FORMAT' in s for s in a12['limitations']) and any('diagram.pdf' in s and 'UNSUPPORTED_FORMAT' in s for s in a12['limitations']))
    bad,_,badrec=case('A12-all-bad',{'broken.docx':b'PK\x03\x04broken'},['broken.docx'],expected_exit=2)
    check('A12-all-bad',bad is None and 'INVALID_INPUT' in badrec['stderr'])
    check('A13', all(s in a01_record['docx_paragraphs'] for s in ['项目及核查范围','本次资料与有效版本','主要发现','要求与证据概况','资料缺口和明确不符合','冲突及未确认变更','验收准备建议','来源和限制']) and len(a01_record['docx_tables'])>=2)
    # Every reported trace must point to a supplied source or a saved prior snapshot; inspect both output formats.
    trace_ok=True
    for name in ['A01','A03','A07','A10','A11']:
        item=RESULT['cases'][name]; sn=item['snapshot']; paths={s['path'] for s in sn['sources']}
        for r in sn['requirements']:
            trace_ok &= r['source'].split('/行')[0].split('/表')[0] in paths
            for condition in r['results']:
                for loc in condition['sources']:
                    trace_ok &= loc.split('/行')[0].split('/表')[0] in paths and loc in str(item['sheets']) and loc in str(item['docx_tables'])
        for conflict in sn['conflicts']:
            for loc in conflict['sources']:
                trace_ok &= loc.split('/行')[0].split('/表')[0] in paths and loc in str(item['sheets']) and loc in str(item['docx_paragraphs'])
    check('A14',trace_ok)
    b01,_,_=case('B01',{'list.csv':'名称\n接口说明.docx\n'},delivery=['list.csv'])
    check('B01',b01['coverage']=='N/A' and any('NO_SCOPE_SOURCE' in s for s in b01['limitations']))
    b02,_,rec=case('B02',{'scope.md':'R01：提供 Windows Server 2019 部署说明和培训记录。\n','deploy.md':'R01：仅 Ubuntu 部署步骤，未提供 Windows Server 2019 步骤。\n'},['scope.md'],['deploy.md'],version='scope.md')
    check('B02_D2',len(b02['requirements'][0]['results'])>=2 and b02['requirements'][0]['status']=='NONCONFORMING' and b02['coverage']=='0/2' and {f['type'] for f in b02['findings']} >= {'NONCONFORMING','MISSING'} and 'deploy.md/行1' in str(rec['docx_tables']))
    traversal,_,_=case('B04-traversal',{'scope.md':'R01：提供接口文档。\n'},['scope.md','../secret'],expected_exit=3)
    check('B04-traversal',any('INVALID_INPUT' in x for x in traversal['limitations']))
    huge,_,_=case('B04-limit',{'scope.md':'R01：提供接口文档。\n','huge.md':'x'*4000001},['scope.md'],['huge.md'],version='scope.md',expected_exit=3)
    check('B04-limit',any('RESOURCE_LIMIT' in x for x in huge['limitations']))
    formula,_,rec=case('B04-formula',{'scope.md':'R01：提供接口文档。\n','evidence.md':'R01：=HYPERLINK("https://example.invalid","text")\n'},['scope.md'],['evidence.md'],version='scope.md')
    check('B04-formula',rec['formula_count']==0 and 'HYPERLINK' in str(rec['sheets']))
    RESULT['checks']['ZIP-source-alignment']=True
    RESULT['checks']['ZIP-integrity']=True
    RESULT['checks']['all-exits']=True

report=REPO/'docs/qa'/f'{PRODUCT}-q02-t03-rerun-run.json'
report.write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':str(report),'zip_sha256':RESULT['zip_sha256'],'members':len(RESULT['members']),'checks':RESULT['checks'],'exits':{k:v['exit'] for k,v in RESULT['cases'].items()}},ensure_ascii=False))
if not all(RESULT['checks'].values()): sys.exit(1)
