"""Independent old 0.1.2 ZIP black-box baseline; fictional files; no production imports."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from openpyxl import load_workbook
from docx import Document

ROOT = Path(__file__).resolve().parents[2]
ZIP = ROOT / 'dist/wangbin-project-acceptance-check-0.1.2-skill-candidate.zip'
EXPECTED_SHA = '5117bd7202cd6a322c3aae8246dad79edeb4cd9a876cbcae800ee78ad2a9df57'
SCRATCH = Path.home()/'AppData/Local/hermes/profiles/wb-quality/cache/scratch'
RESULT = {'archive': str(ZIP), 'sha256': hashlib.sha256(ZIP.read_bytes()).hexdigest(), 'cases': [], 'layers': {'L1':'ZIP static inspection', 'L2':'NOT_TESTED (no mock/isolated function tests)', 'L3':'real extracted ZIP CLI, XLSX/DOCX/JSON reopened', 'L4':'NOT_TESTED', 'L5':'NOT_TESTED'}}
assert RESULT['sha256'] == EXPECTED_SHA
with tempfile.TemporaryDirectory(prefix='acc-r1-baseline-',dir=SCRATCH) as d:
    base=Path(d)
    with zipfile.ZipFile(ZIP) as z:
        names=z.namelist()
        assert z.testzip() is None and len(names)==len(set(names))==9
        assert all(x.startswith('wangbin-project-acceptance-check/') and '..' not in Path(x).parts and not x.startswith('/') for x in names)
        RESULT['members']=[{'path':n,'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in names]
        z.extractall(base/'extracted')
    script=base/'extracted/wangbin-project-acceptance-check/scripts/check_acceptance.py'
    RESULT['static']={'script':str(script),'observations':['conditions(): composite deployment regex fixes Windows Server 2019','evaluate_condition(): explicit R01 reference can become SUPPORT without semantic threshold comparison','evaluate_condition(): negative regex includes literal 失败, without count/scope']}
    def run(id, scope, documents, expectation, evidence_names=(), delivery_names=()):
        # Keep explicit R01 inside the evidence body (no colon); the reader strips 'R01：' into a separate number.
        documents={name:text.replace('R01：','R01 ') for name,text in documents.items()}
        folder=base/id; folder.mkdir(); out=folder/'output'; out.mkdir()
        (folder/'scope.md').write_text('R01：'+scope+'\n',encoding='utf-8')
        for name, text in documents.items(): (folder/name).write_text(text+'\n',encoding='utf-8')
        args=[sys.executable,str(script),'--project-name','星桥演示平台','--authorized-input-root',str(folder),'--output-dir',str(out),'--scope-source','scope.md','--effective-version-ref','scope.md']
        for name in evidence_names: args+=['--evidence-source',name]
        for name in delivery_names: args+=['--delivery-source',name]
        env=os.environ.copy();env.pop('PYTHONPATH',None)
        p=subprocess.run(args,cwd=folder,env=env,capture_output=True,text=True,encoding='utf-8')
        item={'id':id,'input':{'scope.md':'R01：'+scope,**documents},'input_sha256':{n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ['scope.md',*documents]},'command':args,'cwd':str(folder),'exit':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip(),'expected':expectation}
        snapfile=out/'星桥演示平台-核查快照.json'
        if snapfile.exists():
            snap=json.loads(snapfile.read_text(encoding='utf-8'))
            item['actual']={'coverage':snap['coverage'],'requirements':[{'number':r['number'],'text':r['text'],'status':r['status'],'source':r['source'],'conditions':r['results']} for r in snap['requirements']],'findings':snap['findings'],'conflicts':snap['conflicts'],'limitations':snap['limitations'],'evidence':snap['evidence']}
            wbfile=out/'星桥演示平台-验收资料核对.xlsx'; docfile=out/'星桥演示平台-验收准备报告.docx'
            wb=load_workbook(wbfile,read_only=True); item['xlsx']={s.title:[[c for c in row] for row in s.values] for s in wb.worksheets};wb.close()
            doc=Document(docfile);item['docx']={'paragraphs':[x.text for x in doc.paragraphs],'tables':[[[c.text for c in row.cells] for row in t.rows] for t in doc.tables]}
            item['output_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}
            item['actual_status']=snap['requirements'][0]['status']
        RESULT['cases'].append(item)
        return item
    login='同一测试场景下至少支持10000个并发登录。'
    for n, num, expected in [('10',10,'NONCONFORMING'),('12000',12000,'EVIDENCE_FOUND'),('9999',9999,'NONCONFORMING'),('10000',10000,'EVIDENCE_FOUND'),('10001',10001,'EVIDENCE_FOUND')]:
        run('F01-login-'+n,login,{'test.md':f'R01：同一测试场景下实测最大支持{num}个并发登录。'},expected,evidence_names=['test.md'])
    run('F01-unrelated',login,{'backup.md':'R01：数据库备份操作完成，恢复成功。'},'NO_EVIDENCE_FOUND',evidence_names=['backup.md'])
    run('F01-no-quantity',login,{'test.md':'R01：同一测试场景下已测试并发登录。'},'PENDING_CONFIRMATION (quantity missing)',evidence_names=['test.md'])
    run('F01-unit-mismatch',login,{'test.md':'R01：同一测试场景下支持12000次每日登录。'},'PENDING_CONFIRMATION (different unit)',evidence_names=['test.md'])
    deploy='提供 Windows Server 2022 部署说明。'
    run('F02-ubuntu',deploy,{'deploy.md':'R01：Ubuntu 部署说明：安装软件并配置端口。'},'NO_EVIDENCE_FOUND (target OS not evidenced)',delivery_names=['deploy.md'])
    run('F02-only-ubuntu',deploy,{'deploy.md':'R01：仅覆盖 Ubuntu 部署，未提供 Windows Server 2022 步骤。'},'NONCONFORMING (submitted deliverable excludes target)',delivery_names=['deploy.md'])
    run('F02-win-full',deploy,{'deploy.md':'R01：Windows Server 2022 部署说明：先安装服务组件、配置端口、启动服务，随后检查健康接口。'},'EVIDENCE_FOUND',delivery_names=['deploy.md'])
    run('F02-win-2025','提供 Windows Server 2025 部署说明。',{'deploy.md':'R01：Windows Server 2025 部署说明：安装服务组件、配置端口、启动服务并验收健康接口。'},'EVIDENCE_FOUND',delivery_names=['deploy.md'])
    run('F02-linux','提供 Debian 12 部署说明。',{'deploy.md':'R01：Ubuntu 22.04 部署说明：安装服务组件、配置端口、启动服务。'},'NO_EVIDENCE_FOUND (target OS not evidenced)',delivery_names=['deploy.md'])
    all_pass='全部登录测试用例通过。'
    run('F03-zero',all_pass,{'test.md':'R01：全部登录测试共执行100项，成功100项，失败次数为0。'},'EVIDENCE_FOUND',evidence_names=['test.md'])
    run('F03-one',all_pass,{'test.md':'R01：全部登录测试共执行100项，成功99项，失败1项。'},'NONCONFORMING',evidence_names=['test.md'])
    run('F03-unspecified',all_pass,{'test.md':'R01：未发现失败。'},'PENDING_CONFIRMATION (test scope unspecified)',evidence_names=['test.md'])
    run('F04-compound','提供接口文档和部署说明。',{'interface.md':'R01：接口文档：端点 /demo、请求参数：id、返回字段：name。'},'PARTIAL_EVIDENCE (deployment missing)',delivery_names=['interface.md'])
    run('F04-claim','提供接口文档。',{'claim.md':'R01：开发完成。'},'NO_EVIDENCE_FOUND (claim alone)',delivery_names=['claim.md'])
    run('F04-conflict','全部登录测试用例通过。',{'pass.md':'R01：全部登录测试共100项，全部通过。','fail.md':'R01：全部登录测试共100项，成功99项，失败1项。'},'CONFLICT (retain both sources)',evidence_names=['pass.md','fail.md'])
    run('F04-two-docs','提供接口文档和部署说明。',{'interface.md':'R01：接口文档：端点 /demo、请求参数：id、返回字段：name。','deploy.md':'R01：Windows Server 2022 部署说明：安装组件、配置端口、启动并验证服务。'},'EVIDENCE_FOUND (both)',delivery_names=['interface.md','deploy.md'])
report=ROOT/'docs/qa/audit-r1-012-baseline-results.json'
report.write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'sha256':RESULT['sha256'],'cases':[(c['id'],c['exit'],c.get('actual_status'),c['expected']) for c in RESULT['cases']],'report':str(report)},ensure_ascii=False))
