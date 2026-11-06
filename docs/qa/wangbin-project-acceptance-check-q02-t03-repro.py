import csv, hashlib, json, os, subprocess, sys, zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from docx import Document
from openpyxl import load_workbook

repo=Path('F:/ideaWorkSpace/wangbin-workbuddy-project-acceptance-check')
zip_path=repo/'dist/wangbin-project-acceptance-check-0.1.1-skill-candidate.zip'
manifest=json.loads((repo/'dist/wangbin-project-acceptance-check-0.1.1-skill-candidate.zip.manifest.json').read_text(encoding='utf-8'))
sha=hashlib.sha256(zip_path.read_bytes()).hexdigest()
assert sha==manifest['sha256']=='74210b2a9e35074f247173f71909848acddb615da40fb39fa24eff74bb99d958'
assert sha in (repo/'dist/wangbin-project-acceptance-check-0.1.1-skill-candidate.zip.sha256').read_text()
results={'source_commit':'db31fb8f2d4981b497f031785a6d830867db037a','zip_sha256':sha,'cases':{},'zip_members':[]}
with TemporaryDirectory(prefix='q02-qa-',dir=Path(__file__).parent) as td:
    base=Path(td); extracted=base/'extract'; extracted.mkdir()
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        names=z.namelist(); assert len(names)==len(manifest['members'])==9
        for m in manifest['members']:
            assert m['path'] in names
            info=z.getinfo(m['path']); data=z.read(m['path'])
            assert info.file_size==m['size'] and hashlib.sha256(data).hexdigest()==m['sha256']
            assert not Path(m['path']).is_absolute() and '..' not in Path(m['path']).parts
            results['zip_members'].append(m['path'])
        z.extractall(extracted)
    script=extracted/'wangbin-project-acceptance-check/scripts/check_acceptance.py'
    def run(name, files, scopes=(), delivery=(), evidence=(), changes=(), version='', previous=None, expect=0, project='星桥演示平台'):
        root=base/name; root.mkdir(); (root/'out').mkdir()
        for rel,value in files.items():
            p=root/rel; p.parent.mkdir(parents=True,exist_ok=True)
            if isinstance(value,bytes): p.write_bytes(value)
            elif callable(value): value(p)
            else: p.write_text(value,encoding='utf-8')
        cmd=[sys.executable,str(script),'--project-name',project,'--authorized-input-root',str(root),'--output-dir',str(root/'out')]
        for flag,group in (('--scope-source',scopes),('--delivery-source',delivery),('--evidence-source',evidence),('--change-source',changes)):
            for x in group: cmd.extend([flag,x])
        if version: cmd.extend(['--effective-version-ref',version])
        if previous: cmd.extend(['--previous-snapshot',previous])
        cp=subprocess.run(cmd,text=True,capture_output=True,encoding='utf-8')
        item={'exit':cp.returncode,'expected_exit':expect,'stdout':cp.stdout.strip(),'stderr':cp.stderr.strip(),'inputs':files.keys().__str__(),'flags':cmd[3:]}
        snapshot=root/'out'/f'{project}-核查快照.json'
        if snapshot.exists():
            snap=json.loads(snapshot.read_text(encoding='utf-8'))
            item['requirements']=[{'number':r['number'],'id':r['requirement_id'],'status':r['status'],'results':r['results'],'source':r['source']} for r in snap['requirements']]
            item['coverage']=snap['coverage']; item['conflicts']=snap['conflicts']; item['findings']=snap['findings']; item['updates']=snap['updates'];item['limitations']=snap['limitations'];item['sources']=snap['sources']
            wb=load_workbook(root/'out'/f'{project}-验收资料核对.xlsx',read_only=True,data_only=False)
            item['sheets']=wb.sheetnames
            item['rows']={ws.title:[[c.value for c in row] for row in ws.iter_rows()] for ws in wb.worksheets}
            wb.close()
            doc=Document(root/'out'/f'{project}-验收准备报告.docx')
            item['docx_paragraphs']=[p.text for p in doc.paragraphs];item['docx_tables']=[[[c.text for c in row.cells] for row in t.rows] for t in doc.tables]
        results['cases'][name]=item
        return item,root
    common='R01：提供包含端点、请求参数和返回字段的接口文档。\nR02：提供 Windows Server 2019 部署说明。\nR03：提供本项目培训记录。\n'
    r01={'scope.md':common,'interface.md':'D01：接口文档端点 /demo/items，请求参数：item_id，返回字段：name。\n','deploy.md':'D02：仅 Ubuntu 部署步骤，未提供 Windows Server 2019 步骤。\n'}
    a01,root=run('A01',r01,['scope.md'],['interface.md','deploy.md'],version='scope.md')
    assert a01['exit']==0
    snap=(root/'out/星桥演示平台-核查快照.json').read_bytes()
    a02,_=run('A02',{'scope.md':'R01：提供接口文档和部署说明。\n','interface.md':'接口文档包含授权接口说明。\n'},['scope.md'],['interface.md'],version='scope.md')
    a03,_=run('A03',{'scope.md':'R01：提供部署说明。\n','deliverables.csv':'名称,版本,要求原文\n部署说明,v1,仅 Ubuntu 部署说明\n部署说明,v2,Windows 部署说明\n'},['scope.md'],['deliverables.csv'],version='scope.md')
    a04,_=run('A04',{'a.csv':'原始编号,要求原文\nR01,提供接口文档\n','b.csv':'原始编号,要求原文\nR01,提供培训记录\n'},['a.csv','b.csv'],version='a.csv')
    a05,_=run('A05',{'scope.md':'R01：提供包含端点、请求参数和返回字段的接口文档。\n','deliverables.csv':'名称\n接口说明.docx\n'},['scope.md'],['deliverables.csv'],version='scope.md')
    a06,_=run('A06',{'scope.md':'R03：提供本项目培训记录。\n','dev-note.md':'R03 开发完成\n'},['scope.md'],['dev-note.md'],version='scope.md')
    a07,_=run('A07',{'scope.md':'R01：提供用户登录功能测试结果。\nR02：提供用户登录安全测试记录。\n','x.md':'用户登录测试通过。\n','y.md':'用户登录功能测试通过。\n'},['scope.md'],evidence=['x.md','y.md'],version='scope.md')
    a08,_=run('A08',{'scope.md':common,'change.md':'新增离线模式\n'},['scope.md'],changes=['change.md'],version='scope.md')
    a09,_=run('A09',{'previous.json':snap,'training.md':'星桥演示平台 R03 培训记录：2026-01-10 培训议程及签到说明\n'},delivery=['training.md'],previous='previous.json')
    a10,_=run('A10',{'scope.md':'R01：提供接口文档。\n','test-fail.md':'R01 接口文档测试失败。\n','test-pass.md':'R01 接口文档测试通过。\n'},['scope.md'],evidence=['test-fail.md','test-pass.md'],version='scope.md')
    def doc_fixture(p):
        d=Document();t=d.add_table(rows=2,cols=2);t.cell(0,0).text='编号';t.cell(0,1).text='要求原文';t.cell(1,0).text='R03';t.cell(1,1).text='提供本项目培训记录';d.save(p)
    a11,_=run('A11',{'scope.docx':doc_fixture},['scope.docx'],version='scope.docx')
    a12,_=run('A12',{'scope.md':'R01：提供接口文档。\n','broken.docx':b'PK\x03\x04broken','fake.docx':'I am not a DOCX','diagram.pdf':b'%PDF-1.7 fake','test.csv':'证据原文,关联要求\nR01 接口文档测试通过,R01\n'},['scope.md'],evidence=['broken.docx','fake.docx','diagram.pdf','test.csv'],version='scope.md',expect=3)
    bad,_=run('A12-all-bad',{'broken.docx':b'PK\x03\x04broken'},['broken.docx'],expect=2)
    boundary,_=run('B01-no-scope',{'deliverables.csv':'名称\n接口说明.docx\n'},delivery=['deliverables.csv'])
    combo,_=run('B02',{'scope.md':'R01：提供 Windows Server 2019 部署说明和培训记录。\n','deploy.md':'R01：仅 Ubuntu 部署步骤，未提供 Windows Server 2019 步骤。\n'},['scope.md'],['deploy.md'],version='scope.md')
    formula,_=run('B04-formula',{'scope.md':'R01：提供接口文档。\n','evidence.md':'R01：=HYPERLINK("https://example.invalid","text")\n'},['scope.md'],['evidence.md'],version='scope.md')
    traverse,_=run('B04-traversal',{'scope.md':'R01：提供接口文档。\n'},['scope.md','../secret'],expect=3)
    large,_=run('B04-limit',{'scope.md':'R01：提供接口文档。\n','huge.md':'x'*4000001},['scope.md'],['huge.md'],version='scope.md',expect=3)
    # Assertions based on frozen acceptance contract rather than implementation snapshots.
    expected={'A01':[r['status'] for r in a01['requirements']]==['EVIDENCE_FOUND','NONCONFORMING','NO_EVIDENCE_FOUND'] and a01['sheets']==['核查概览','要求追踪','证据索引','缺口与不符合','冲突与待确认','本次更新'],
    'A02':a02['requirements'][0]['status']=='PARTIAL_EVIDENCE','A03':a03['requirements'][0]['status']=='CONFLICT' and a03['coverage']=='N/A' and any(c['type']=='VERSION_CONFLICT' for c in a03['conflicts']),
    'A04':len(a04['requirements'])==2 and len({r['id'] for r in a04['requirements']})==2 and any(c['type']=='DUPLICATE_ID' for c in a04['conflicts']),
    'A05':a05['requirements'][0]['status']=='NO_EVIDENCE_FOUND' and any('LISTED_ONLY' in str(row) for row in a05['rows']['证据索引']),
    'A06':a06['requirements'][0]['status']=='NO_EVIDENCE_FOUND','A07':any(r['status']=='PENDING_CONFIRMATION' for r in a07['requirements']) and any(c['type']=='MAPPING_CANDIDATE' for c in a07['conflicts']),
    'A08':len(a08['requirements'])==3 and any(c['type']=='UNCONFIRMED_CHANGE' for c in a08['conflicts']),
    'A09':a09['requirements'][2]['status']=='EVIDENCE_FOUND' and a09['requirements'][0]['status']=='EVIDENCE_FOUND' and a09['requirements'][1]['status']=='NONCONFORMING' and any(u['type']=='RESOLVED' for u in a09['updates']),
    'A10':a10['requirements'][0]['status']=='CONFLICT' and any(c['type']=='EVIDENCE_CONFLICT' for c in a10['conflicts']),
    'A11':a11['requirements'][0]['status']=='NO_EVIDENCE_FOUND' and '表1/行2/列2' in a11['requirements'][0]['source'],
    'A12':a12['exit']==3 and all(any(code in s for s in a12['limitations']) for code in ('UNSUPPORTED_FORMAT','UNREADABLE_SOURCE')),
    'A12-all-bad':bad['exit']==2 and 'rows' not in bad,
    'A13':all(r['status'] in ' '.join(a01['docx_paragraphs']) for r in a01['requirements']) and all(r['id'] in str(a01['docx_tables']) for r in a01['requirements']),
    'B01-no-scope':boundary['coverage']=='N/A' and any('NO_SCOPE_SOURCE' in s for s in boundary['limitations']),
    'B02':combo['requirements'][0]['status']=='NONCONFORMING' and {g['type'] for g in combo['findings']}>= {'NONCONFORMING','MISSING'},
    'B04-traversal':traverse['exit']==3,'B04-limit':large['exit']==3,
    'B04-formula':all(cell.data_type!='f' for ws in load_workbook(base/'B04-formula/out/星桥演示平台-验收资料核对.xlsx').worksheets for row in ws for cell in row)}
    results['verdicts']=expected
    results['scratch_path']=str(base)
    out=repo/'docs/qa/wangbin-project-acceptance-check-q02-t03-run.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(results,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps({'evidence':str(out),'zip_sha256':sha,'verdicts':expected,'exits':{k:v['exit'] for k,v in results['cases'].items()}},ensure_ascii=False))
