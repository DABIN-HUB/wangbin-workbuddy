import csv, hashlib, json, os, shutil, subprocess, sys, zipfile
from collections import Counter
from pathlib import Path
from openpyxl import Workbook, load_workbook
ROOT=Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check')
SCR=Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_independent_025_adjudicated')
ZIP=ROOT/'dist/wangbin-tender-analyzer-0.2.5-skill-candidate.zip'
SID=ROOT/'dist/wangbin-tender-analyzer-0.2.5-skill-candidate.zip.manifest.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(ZIP.read_bytes())=='69e1a9f2ef0698e40a174faf711e1eb627aecc68fb1106c567a506d063493c06'
assert sha((ROOT/'dist/wangbin-tender-analyzer-0.2.3-skill-candidate.zip').read_bytes())=='5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce'
manifest=json.loads(SID.read_text(encoding='utf-8'));assert manifest['sha256']==sha(ZIP.read_bytes()) and manifest['version']=='0.2.5'
assert not SCR.exists(), 'scratch already exists; no overwrite'
SCR.mkdir(parents=True)
with zipfile.ZipFile(ZIP) as z:
 assert z.testzip() is None
 names=z.namelist();assert len(names)==len(set(names))==len(manifest['members'])
 assert set(names)=={x['path'] for x in manifest['members']}
 for m in manifest['members']:
  assert not Path(m['path']).is_absolute() and '..' not in Path(m['path']).parts
  raw=z.read(m['path']);assert sha(raw)==m['sha256'] and len(raw)==m['size']
 z.extractall(SCR/'extract')
BASE=SCR/'extract/wangbin-tender-analyzer'
SCRIPT=BASE/'scripts/check_response.py'
assert sha(SCRIPT.read_bytes())=='60c1372ad713b6fd57d40160294e7017b701456e8c73027d6bdf60cd07cf4be7'
# Each case has its own physical inputs and dedicated empty output directory.
cases=[]
def add(id,t,r=None,e=None,c=None,expected=None,am=None): cases.append(dict(id=id,t=t,r=r,e=e or {},c=c,expected=expected,am=am or []))
# Expected: response/coverage/attachment/support; None means scoped invariant rather than exact status.
POS=('已定位','已覆盖（文本层面）','不适用','不适用')
add('R01-expiry','1. 甲类资质须有效覆盖2028-01-01至2028-12-31，附甲类证明 certificate.txt。','1. 甲类有效期覆盖该期，见certificate.txt。',{'certificate.txt':'甲类证明：2027-01-01生效，有效截止2027-12-31。'},[['certificate.txt','1']],('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('R02-start','1. 甲类资质须覆盖2028-01-01至2028-12-31，附certificate.txt。','1. 甲类资质覆盖期间，见certificate.txt。',{'certificate.txt':'甲类证明：2028-01-02生效，有效截止2029-12-31。'},[['certificate.txt','1']],('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('R03-edge-positive','1. 甲类资质须覆盖2027-01-01至2027-12-31，附certificate.txt。','1. 甲类资质覆盖期间，见certificate.txt。',{'certificate.txt':'甲类证明签发于2026-04-03，2027-01-01生效，2027-12-31失效。'},[['certificate.txt','1']],('已定位','已覆盖（文本层面）','已提供（可读文本）','支持（文本层面）'))
add('R04-issued-only','1. 甲类资质须覆盖2027-01-01至2027-12-31，附certificate.txt。','1. 甲类资质覆盖期间，见certificate.txt。',{'certificate.txt':'甲类证明签发于2026-04-03。'},[['certificate.txt','1']],('已定位','待确认','已提供（可读文本）','待确认'))
add('R05-two-certificates','1. 甲类资质须有效覆盖2028-01-01至2028-12-31，附甲类证明 certificate.txt。','1. 甲类有效期覆盖该期，见certificate.txt。',{'certificate.txt':'乙类证明有效期2026-01-01至2035-12-31。\n甲类证明有效期2027-01-01至2027-12-31。'},[['certificate.txt','1']],('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('R06-shift','1. 甲类资质须有效覆盖2033-01-01至2033-12-31，附甲类证明 certificate.txt。','1. 甲类有效期覆盖该期，见certificate.txt。',{'certificate.txt':'甲类证明：2032-01-01生效，有效截止2032-12-31。'},[['certificate.txt','1']],('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('R07-ambiguous-year','1. 甲类资质须覆盖2028年，附certificate.txt。','1. 甲类证明见附件。',{'certificate.txt':'甲类证明签发于2027-02-02；有效期另行确定。'},[['certificate.txt','1']],('已定位','待确认','已提供（可读文本）','待确认'))
add('R08-no-backup','1. 必须支持自动备份。','1. 我方不支持自动备份。',expected=('已定位','可能不充分','不适用','不适用'))
add('R09-yes-backup','1. 必须支持自动备份。','1. 我方支持自动备份。',expected=POS)
add('R10-neg-neg','1. 不使用外部云存储。','1. 本方案不使用外部云存储。',expected=POS)
add('R11-conditional','1. 必须支持自动备份。','1. 若另行购买模块，我方才支持自动备份。',expected=('已定位','可能不充分','不适用','不适用'))
add('R11-not-implemented','1. 必须支持自动备份。','1. 我方拟于交付后支持自动备份，当前尚未实现。',expected=('已定位','可能不充分','不适用','不适用'))
add('R12-scope','1. 必须支持备份。\n2. 必须支持离线查询。','1. 我方不支持备份。\n2. 我方支持离线查询。',expected=[('已定位','可能不充分','不适用','不适用'),POS])
add('R13-license-missing','1. 必须提供营业执照。','1. 我方提供营业执照。',expected=('已定位','可能不充分','未提供（限已提供材料）','未核验'))
add('R14-catalog-csv','1. 必须提供营业执照。','1. 我方提供营业执照。',c=[['营业执照.txt','1']],expected=('已定位','可能不充分','仅目录登记','未核验'))
add('R14-catalog-xlsx','1. 必须提供营业执照。','1. 我方提供营业执照。',c=[['营业执照.txt','1']],expected=('已定位','可能不充分','仅目录登记','未核验'))
add('R15-license-negative','1. 必须提供营业执照。','1. 我方提供营业执照。',{'营业执照.txt':'本件是目录占位；营业执照正在申请，尚未取得。'},[['营业执照.txt','1']],('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('R16-license-positive','1. 必须提供营业执照。','1. 我方提供营业执照。',{'营业执照.txt':'营业执照文本：统一社会信用代码为虚构示例编号。'},[['营业执照.txt','1']],('已定位','已覆盖（文本层面）','已提供（可读文本）','支持（文本层面）'))
add('R16-duplicate','1. 必须提供营业执照。','1. 我方提供营业执照。',{'营业执照.txt':'营业执照文本：虚构示例编号。'},[['营业执照.txt','1'],['营业执照.txt','1']],('已定位',None,'待确认','待确认'))
add('R17-empty-conditions','1. 须提供certificate.txt资质证明。','1. 证书见certificate.txt。',{'certificate.txt':'certificate.txt：仅为目录占位，不含证书。'},[['certificate.txt','1']],('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('R18-no-catalog','1. 须提供certificate.txt资质证明。','1. 证书见certificate.txt。',{'certificate.txt':'certificate.txt：仅为目录占位，不含证书。'},expected=('已定位',None,None,None))
add('R19-before','1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。','1. 甲类证明已提交。\n2. 乙类证明已提交。',c=[['甲类.txt','1'],['乙类.txt','2']],expected=[('已定位','可能不充分','仅目录登记','未核验')]*2)
add('R19-after','1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。','1. 甲类证明已提交。\n2. 乙类证明已提交。',{'甲类.txt':'甲类证明文本：甲类有效。'},[['甲类.txt','1'],['乙类.txt','2']],[(None,None,'已提供（可读文本）','支持（文本层面）'),('已定位','可能不充分','仅目录登记','未核验')])
# Unpublished variants, not copied from the frozen table.
add('V01-shift-object','1. 丙类资质应覆盖2041-05-17至2042-05-16，附丙类证明 license-note.txt。','1. 丙类资质覆盖对应期限，见license-note.txt。',{'license-note.txt':'丙类证明：2040-05-17生效，有效截止2042-05-15。'},[['license-note.txt','1']],('已定位','可能不充分','已提供（可读文本）','不支持（文本层面）'))
add('V02-shift-boundary','1. 丙类资质应覆盖2041-05-17至2042-05-16，附丙类证明 license-note.txt。','1. 丙类资质覆盖对应期限，见license-note.txt。',{'license-note.txt':'丙类证明：2041-05-17生效，有效截止2042-05-16。'},[['license-note.txt','1']],('已定位','已覆盖（文本层面）','已提供（可读文本）','支持（文本层面）'))
add('V03-cross-negation','1. 不使用外部云存储。','1. 本方案使用外部云存储。',expected=('已定位','可能不充分','不适用','不适用'))
add('V04-rephrase-no','1. 必须支持自动备份。','1. 本产品无法支持自动备份。',expected=('已定位','可能不充分','不适用','不适用'))
add('V05-rephrase-promise','1. 必须支持自动备份。','1. 正式交付后方可支持自动备份。',expected=('已定位','可能不充分','不适用','不适用'))
add('V06-irrelevant','1. 必须支持自动备份。','1. 只提供自动备份设计文档，功能未上线。',expected=('已定位','可能不充分','不适用','不适用'))
add('V07-irrelevant-evidence','1. 甲类资质须覆盖2041-05-17至2042-05-16，附certificate.txt。','1. 甲类资质覆盖期间，见certificate.txt。',{'certificate.txt':'甲类证明附录：系统备份流程。'},[['certificate.txt','1']],('已定位','待确认','已提供（可读文本）','待确认'))
add('V08-prepare','1. 必须支持自动备份。',expected=('未核查','未核查','不适用','不适用'))
add('V09-amendment','5. 交付期为30日。','5. 交付期30日。',am=['正式补遗第1号：原第5条交付期30日替换为45日。'])
records=[]
for case in cases:
 id=case['id'];folder=SCR/'cases'/id;folder.mkdir(parents=True);out=folder/'out';out.mkdir()
 def file(n,s):
  p=folder/n;p.write_text(s,encoding='utf-8');return p
 args=[sys.executable,str(SCRIPT),'--tender',str(file('tender.txt',case['t'])),'--output-dir',str(out),'--project','虚构核验'+id]
 if case['r'] is not None:args+=['--mode','check','--response',str(file('response.md',case['r']))]
 for n,s in case['e'].items():args+=['--evidence-file',str(file(n,s))]
 if case['c'] is not None:
  if id.endswith('xlsx'):
   wb=Workbook();wb.active.append(['附件名称','关联要求编号']);[wb.active.append(row) for row in case['c']];p=folder/'catalog.xlsx';wb.save(p)
  else:
   p=folder/'catalog.csv'
   with p.open('w',encoding='utf-8',newline='') as f: w=csv.writer(f);w.writerow(['附件名称','关联要求编号']);w.writerows(case['c'])
  args+=['--attachment-catalog',str(p)]
 for i,s in enumerate(case['am']):args+=['--amendment',str(file('amendment'+str(i)+'.txt',s))]
 inputs={p.name:sha(p.read_bytes()) for p in folder.iterdir() if p.is_file()}
 env=dict(os.environ);env.pop('PYTHONPATH',None)
 cp=subprocess.run(args,cwd=str(folder),env=env,capture_output=True,text=True,timeout=30)
 rec=dict(id=id,argv=args,cwd=str(folder),exit=cp.returncode,stdout=cp.stdout,stderr=cp.stderr,input_sha=inputs,output_sha={},actual=[],expected=case['expected'],issues=[])
 if cp.returncode != 0:rec['issues'].append('CLI exit != 0')
 outputs=list(out.iterdir());rec['output_sha']={p.name:sha(p.read_bytes()) for p in outputs}
 if len(outputs)!=2:rec['issues'].append('two outputs expected')
 xlsx=next((p for p in outputs if p.suffix=='.xlsx'),None);md=next((p for p in outputs if p.suffix=='.md'),None)
 if xlsx and md:
  wb=load_workbook(xlsx,data_only=False);rec['sheets']=wb.sheetnames
  if wb.sheetnames!=['核查概览','要求响应矩阵','附件核对','补遗与版本','待确认事项']:rec['issues'].append('five sheets/order')
  matrix=list(wb['要求响应矩阵'].values);columns=matrix[0];rows=[dict(zip(columns,r)) for r in matrix[1:]]
  rec['actual']=[{k:v for k,v in row.items() if k in ('唯一ID','响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态','缺口','证据位置','来源','建议')} for row in rows]
  exp=case['expected'];exps=exp if isinstance(exp,list) else [exp] if exp else []
  if exps and len(rows)!=len(exps):rec['issues'].append('matrix row count '+str(len(rows)))
  for row,ex in zip(rows,exps):
   for col,want in zip(('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态'),ex):
    if want is not None and row[col]!=want:rec['issues'].append(f"{row['唯一ID']} {col} expected {want} actual {row[col]}")
  if id=='R18-no-catalog' and any(row['附件实际提供状态']=='未提供（限已提供材料）' for row in rows):rec['issues'].append('explicit uniquely named evidence submitted but falsely reported not provided')
  if id=='R18-no-catalog' and any(row['内容支持状态']=='支持（文本层面）' for row in rows):rec['issues'].append('negative placeholder falsely supported')
  if id=='V09-amendment' and (len(rows)!=2 or '版本冲突' not in str(rows[1]['缺口'])):rec['issues'].append('formal amendment old response conflict missing')
  mdtext=md.read_text(encoding='utf-8');rec['md_length']=len(mdtext)
  for row in rows:
   rid=row['唯一ID'];st=[row[d] for d in ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态')]
   if (row['缺口'] or row['条件覆盖状态']=='可能不充分') and rid not in mdtext:rec['issues'].append('MD missing gap ID '+rid)
   if row['缺口'] and rid in mdtext.split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]:rec['issues'].append('MD falsely covered '+rid)
   if id.startswith(('R01','R02','R05','R06','V01')) and '不支持' in st[-1] and not row['证据位置']:rec['issues'].append('missing evidence location')
  for dimension in ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态'):
   actual=Counter(row[dimension] for row in rows);observed={r[1]:r[2] for r in list(wb['核查概览'].values) if r[0]==dimension and len(r)>2 and r[1]!='状态'}
   if actual!=observed:rec['issues'].append('overview count mismatch '+dimension)
  rec['attachment_rows']=list(wb['附件核对'].values)[1:];rec['pending_rows']=list(wb['待确认事项'].values)[1:];rec['amendment_rows']=list(wb['补遗与版本'].values)[1:]
  if any(c.data_type=='f' for s in wb for line in s for c in line):rec['issues'].append('formula in output')
  wb.close()
 records.append(rec)
 print(id, 'PASS' if not rec['issues'] else 'FAIL',rec['exit'],[(x.get('响应存在状态'),x.get('条件覆盖状态'),x.get('附件实际提供状态'),x.get('内容支持状态')) for x in rec['actual']],rec['issues'],flush=True)
# Old original JSON snapshot from old immutable ZIP, not generated from new output.
legacy_cmd=[sys.executable,str(BASE/'scripts/analyze_tender.py'),'--input',str(BASE/'examples/fictional-tender.txt')]
p=subprocess.run(legacy_cmd,cwd=str(SCR),capture_output=True,text=True,env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'})
with zipfile.ZipFile(ROOT/'dist/wangbin-tender-analyzer-0.2.3-skill-candidate.zip') as old:
 old_expected=json.loads(old.read('wangbin-tender-analyzer/examples/fictional-tender.expected.json'))
legacy=dict(argv=legacy_cmd,exit=p.returncode,stdout_sha=sha(p.stdout.encode()),stderr=p.stderr,original_expected_sha=sha(json.dumps(old_expected,ensure_ascii=False,sort_keys=True).encode()),match=p.returncode==0 and json.loads(p.stdout)==old_expected)
(SCR/'results.json').write_text(json.dumps(dict(zip_sha=sha(ZIP.read_bytes()),manifest=manifest,cases=records,legacy=legacy),ensure_ascii=False,indent=2),encoding='utf-8')
print('TOTAL',len(records),'FAILED',sum(bool(r['issues']) for r in records),'LEGACY',legacy,flush=True)
