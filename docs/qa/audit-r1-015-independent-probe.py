"""Independent black-box audit of immutable 0.1.4 ZIP; fictional fixtures only."""
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

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'dist/wangbin-project-acceptance-check-0.1.4-skill-candidate.zip'
SCRATCH = Path.home() / 'AppData/Local/hermes/profiles/wb-quality/cache/scratch'
SHA = '271f832f461e371f63ea4aea6e11467382e6a8471ff5d4668403ec19b4d2c8ab'
RESULT = {'product_id': 'wangbin-project-acceptance-check', 'task_id': 't_fb3ff37a', 'zip': str(ARCHIVE), 'sha256': hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), 'cases': [], 'checks': []}
assert RESULT['sha256'] == SHA
catalog=json.loads((ROOT/'products/catalog.json').read_text(encoding='utf-8'))
item=next(p for p in catalog['products'] if p['id']==RESULT['product_id'])
expected_old={'0.1.2':'5117bd7202cd6a322c3aae8246dad79edeb4cd9a876cbcae800ee78ad2a9df57','0.1.3':'9b6234744613af39c9d710359c93649044cbc4660aa9805a9bf8e1a8927c797e'}
for version,digest in {**expected_old,'0.1.4':SHA}.items():
    old=ROOT/f'dist/wangbin-project-acceptance-check-{version}-skill-candidate.zip'
    cat=next(v for v in item['versions'] if v['version']==version)
    RESULT['checks'].append({'id':'catalog-and-archive-'+version,'actual':hashlib.sha256(old.read_bytes()).hexdigest(),'expected':digest,'pass':cat['sha256']==digest and cat['candidate']==str(old.relative_to(ROOT)).replace('\\','/') and hashlib.sha256(old.read_bytes()).hexdigest()==digest})
RESULT['checks'].append({'id':'active-old-version','actual':item['active_version'],'pass':item['active_version']=='0.1.2'})
with tempfile.TemporaryDirectory(prefix='acc-015-independent-', dir=SCRATCH) as temporary:
    base = Path(temporary)
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        assert archive.testzip() is None and len(names) == len(set(names)) == 9
        assert all(n.startswith('wangbin-project-acceptance-check/') and '..' not in Path(n).parts and not Path(n).is_absolute() for n in names)
        members = [{'path': n, 'sha256': hashlib.sha256(archive.read(n)).hexdigest(), 'size': len(archive.read(n))} for n in names]
        RESULT['members'] = members
        sidecar = json.loads((ROOT / 'dist/wangbin-project-acceptance-check-0.1.4-skill-candidate.zip.manifest.json').read_text(encoding='utf-8'))
        RESULT['checks'].append({'id':'manifest-members','pass': sidecar['members'] == members and sidecar['sha256'] == SHA and sidecar['version'] == '0.1.4'})
        RESULT['checks'].append({'id':'sha-sidecar','pass': ARCHIVE.with_name(ARCHIVE.name+'.sha256').read_text(encoding='ascii') == f'{SHA}  {ARCHIVE.name}\n'})
        RESULT['checks'].append({'id':'safe-members','pass':len(names)==len(set(names))==9 and all(not (z.external_attr >> 16) & 0o170000 == 0o120000 for z in archive.infolist())})
        archive.extractall(base / 'extract')
    script = base/'extract/wangbin-project-acceptance-check/scripts/check_acceptance.py'
    RESULT['checks'].append({'id':'extracted-script','pass': hashlib.sha256(script.read_bytes()).hexdigest() == next(m['sha256'] for m in members if m['path'].endswith('/scripts/check_acceptance.py'))})

    def run(label, scope, material, expected, role='evidence', suffix='.md', extra=None):
        folder = base/label
        folder.mkdir()
        out = folder/'out'
        out.mkdir()
        if suffix == '.docx':
            d=Document(); d.add_paragraph('R01 '+material); d.save(folder/'material.docx')
        elif suffix == '.xlsx':
            w=Workbook(); w.active.append(['关联要求','证据原文']); w.active.append(['R01',material]); w.save(folder/'material.xlsx')
        else:
            (folder/('material'+suffix)).write_text('R01 '+material+'\n',encoding='utf-8')
        (folder/'scope.md').write_text('R01：'+scope+'\n',encoding='utf-8')
        src='material'+suffix
        cmd=[sys.executable,str(script),'--project-name','QA虚构项目','--authorized-input-root',str(folder),'--output-dir',str(out),'--scope-source','scope.md','--effective-version-ref','scope.md','--'+role+'-source',src]
        if extra:
            (folder/'second.md').write_text('R01 '+extra+'\n',encoding='utf-8')
            cmd.extend(['--'+role+'-source','second.md'])
        before={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()}
        env=os.environ.copy(); env.pop('PYTHONPATH',None)
        p=subprocess.run(cmd,cwd=folder,env=env,text=True,capture_output=True,encoding='utf-8')
        record={'id':label,'inputs':{'scope.md':scope,src:material,**({'second.md':extra} if extra else {})},'input_hashes':before,'command':cmd,'cwd':str(folder),'exit':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip(),'expected':expected}
        record['source_unchanged']=record['input_hashes']=={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()}
        snap=out/'QA虚构项目-核查快照.json'
        if snap.exists():
            data=json.loads(snap.read_text(encoding='utf-8')); req=data['requirements'][0]
            wb=load_workbook(out/'QA虚构项目-验收资料核对.xlsx',read_only=True)
            doc=Document(out/'QA虚构项目-验收准备报告.docx')
            actual=req['status']; overview=wb['核查概览']['B2'].value
            record.update(actual=actual,coverage=data['coverage'],conditions=req['results'],findings=data['findings'],conflicts=data['conflicts'],sources=data['sources'],workbook={'sheets':wb.sheetnames,'overview':overview,'tracking_status':wb['要求追踪']['H2'].value,'tracking_sources':wb['要求追踪']['G2'].value,'gap_rows':list(wb['缺口与不符合'].values)},docx={'paragraphs':[x.text for x in doc.paragraphs],'tables':[[[c.text for c in row.cells] for row in table.rows] for table in doc.tables]},output_hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()})
            wb.close()
            counts={'EVIDENCE_FOUND':'1/1','PARTIAL_EVIDENCE':'1/2'}
            source_ok=all(x['sources'] and all(y.startswith(src+'/') or y.startswith('second.md/') for y in x['sources']) for x in req['results'] if x.get('status') != 'NO_EVIDENCE_FOUND')
            record['pass']=p.returncode == 0 and record['source_unchanged'] and actual == expected and data['coverage']==counts.get(expected,'0/1') and source_ok and record['workbook']['tracking_status']==actual and actual in '\n'.join(record['docx']['paragraphs']) and '已验收通过' not in '\n'.join(record['docx']['paragraphs']) and len(record['workbook']['sheets'])==6
            record['source_ok']=source_ok
        else: record['pass']=False
        RESULT['cases'].append(record)
        print(label,record.get('actual','NO_SNAPSHOT'),expected,'exit',p.returncode,'PASS' if record['pass'] else 'FAIL',flush=True)
        return record

    # Independently selected threshold, unit, setting, version and phrasing variants.
    scope='同一测试场景下并发登录人数不得低于73人。'
    for n,expected in [(72,'NONCONFORMING'),(73,'EVIDENCE_FOUND'),(74,'EVIDENCE_FOUND')]:
        run('F01-people-'+str(n),scope,f'同一压测场景最大支持{n}人并发登录。',expected,suffix='.xlsx')
    run('F01-missing-unit',scope,'同一压测场景最大支持74并发登录。','PENDING_CONFIRMATION')
    run('F01-daily-count',scope,'同一压测场景每日登录74次。','PENDING_CONFIRMATION')
    run('F01-no-scene',scope,'最大支持74人并发登录。','PENDING_CONFIRMATION')
    run('F01-different-object',scope,'同一压测场景最大支持74人并发注册。','NO_EVIDENCE_FOUND')
    run('F01-unrelated-number',scope,'R01 数据库备份74人已登记。','NO_EVIDENCE_FOUND')
    run('F01-strict-equality','同一场景并发登录人数必须超过73人。','同一测试场景最大支持73人并发登录。','NONCONFORMING')
    for os_name,material,expected in [
        ('Debian 13','Debian 13 部署说明：安装服务、配置参数、启动服务、验证健康状态。','EVIDENCE_FOUND'),
        ('Debian 13','Debian 12 部署说明：安装服务、配置参数、启动服务、验证健康状态。','NO_EVIDENCE_FOUND'),
        ('Rocky Linux 9','Rocky Linux 9 部署说明：安装服务、配置参数、启动服务、验证健康状态。','EVIDENCE_FOUND'),
        ('Windows Server 2028','仅覆盖 Debian 13 部署，未提供 Windows Server 2028 步骤。','NONCONFORMING'),
        ('Windows Server 2028','Windows Server 2028 部署说明：安装服务、配置参数、启动服务、验证健康状态。','EVIDENCE_FOUND'),
        ('Windows Server 2028','Windows Server 2028 部署说明：安装服务。','PENDING_CONFIRMATION'),
    ]:
        run('F02-'+str(len(RESULT['cases'])),f'提供 {os_name} 部署说明。',material,expected,role='delivery',suffix='.docx')
    tests='全部登录测试用例通过。'
    for label,material,expected in [
        ('zero','共执行41项登录用例，成功41项，失败0项。','EVIDENCE_FOUND'),
        ('one','共执行41项登录用例，成功40项，失败1项。','NONCONFORMING'),
        ('wrong-total','共执行41项登录用例，成功40项，失败0项。','PENDING_CONFIRMATION'),
        ('unknown','未发现失败。','PENDING_CONFIRMATION'),
        ('other-scope','共执行41项注册用例，成功41项，失败0项。','PENDING_CONFIRMATION')]:
        run('F03-'+label,tests,material,expected,suffix='.docx')
    run('F01-denied-capability',scope,'同一压测场景不支持74人并发登录，最大仅支持72人并发登录。','NONCONFORMING')
    run('F01-declared-inability',scope,'同一压测场景无法支持74人并发登录。','PENDING_CONFIRMATION')
    run('F03-scope-exclusion',tests,'共执行41项登录用例，成功41项，失败0项，但高并发登录用例没有执行。','PENDING_CONFIRMATION')
    run('F01-novel-negative-max',scope,'同一压测场景实际无法达到75人并发登录，实测最高仅72人并发登录。','NONCONFORMING',suffix='.txt')
    run('F01-novel-positive-and-denial',scope,'同一压测场景不能达到74人并发登录；但实际支持73人并发登录。','EVIDENCE_FOUND',suffix='.md')
    run('F01-novel-uncertain-denial',scope,'同一压测场景不支持76人并发登录。','PENDING_CONFIRMATION',suffix='.docx')
    run('F03-novel-omitted',tests,'41项登录用例执行完毕，成功41项，失败0项；但登录安全测试尚未覆盖。','PENDING_CONFIRMATION',suffix='.xlsx')
    run('F03-novel-omitted-alt',tests,'共执行41项登录用例，成功41项，失败0项；但是登录异常路径尚未执行。','PENDING_CONFIRMATION',suffix='.txt')
    run('F04-document-only','提供接口文档和部署说明。','接口文档：端点 /v2、请求参数：id、返回字段：state。','PARTIAL_EVIDENCE',role='delivery')
    run('F04-developer-claim','提供接口文档。','开发完成。','NO_EVIDENCE_FOUND',role='delivery')
    run('F04-two-sources-conflict',tests,'共执行41项登录用例，成功41项，失败0项。','CONFLICT',extra='共执行41项登录用例，成功40项，失败1项。')
    # Invalid input and forbidden traversal must not create successful reports.
    folder=base/'invalid'; folder.mkdir(); (folder/'out').mkdir()
    bad=[sys.executable,str(script),'--project-name','QA虚构项目','--authorized-input-root',str(folder),'--output-dir',str(folder/'out'),'--scope-source','../extract/wangbin-project-acceptance-check/SKILL.md']
    p=subprocess.run(bad,cwd=folder,capture_output=True,text=True,encoding='utf-8')
    RESULT['checks'].append({'id':'reject-traversal','command':bad,'exit':p.returncode,'stderr':p.stderr.strip(),'pass':p.returncode==2 and not list((folder/'out').iterdir())})
RESULT['case_count']=len(RESULT['cases']); RESULT['passed']=sum(c['pass'] for c in RESULT['cases']); RESULT['failed_cases']=[c['id'] for c in RESULT['cases'] if not c['pass']];RESULT['check_failures']=[c['id'] for c in RESULT['checks'] if not c['pass']]
(ROOT/'docs/qa/audit-r1-015-independent-results.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'cases':RESULT['case_count'],'passed':RESULT['passed'],'failed':RESULT['failed_cases'],'check_failures':RESULT['check_failures']},ensure_ascii=False))
