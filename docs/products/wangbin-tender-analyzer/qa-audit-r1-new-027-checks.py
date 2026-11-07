"""Independent read-only package metadata verification and formal CLI error probe on exact ZIP extraction."""
import hashlib, json, os, subprocess, sys, zipfile
from pathlib import Path, PurePosixPath
import yaml
root=Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check')
base=root/'dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip'
scratch=Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_independent_027_rerun1')
sha=lambda b:hashlib.sha256(b).hexdigest()
known={'0.2.3':'5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce','0.2.5':'69e1a9f2ef0698e40a174faf711e1eb627aecc68fb1106c567a506d063493c06','0.2.6':'1c18b43f8cb465eb261ae4ccdc950259399f64b9c70477496809e3102dd4753a','0.2.7':'12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09'}
for ver,want in known.items():assert sha((root/f'dist/wangbin-tender-analyzer-{ver}-skill-candidate.zip').read_bytes())==want
manifest=json.loads(Path(str(base)+'.manifest.json').read_text(encoding='utf-8'))
assert manifest['id']=='wangbin-tender-analyzer' and manifest['version']=='0.2.7' and manifest['sha256']==known['0.2.7']
assert known['0.2.7'] in Path(str(base)+'.sha256').read_text(encoding='utf-8')
with zipfile.ZipFile(base) as z:
 assert z.testzip() is None
 names=z.namelist();assert len(names)==len(set(names))==11 and names==[m['path'] for m in manifest['members']]
 for m in manifest['members']:
  name=m['path'];p=PurePosixPath(name)
  assert name.startswith('wangbin-tender-analyzer/') and not p.is_absolute() and '..' not in p.parts and '\\' not in name
  assert not any(t in name.lower() for t in ('/.git/','/.env','private','__pycache__'))
  raw=z.read(name);assert len(raw)==m['size'] and sha(raw)==m['sha256']
  assert sha((root/'packages/skills'/name).read_bytes())==m['sha256']
 skill=z.read('wangbin-tender-analyzer/SKILL.md').decode('utf-8')
 front=yaml.safe_load(skill.split('---',2)[1]);assert front['name']==manifest['id'] and front['version']==manifest['version']
 assert all(front.get(x) for x in ('display_name','display_name_en','description','description_zh','description_en','author'))
 assert len(front['examples_zh'])==len(front['examples_en'])==3
 assert 'openpyxl>=3.1,<4' in skill and '<解压目录>/wangbin-tender-analyzer/scripts/check_response.py' in skill
 assert 'expected' in skill
catalog=json.loads((root/'products/catalog.json').read_text(encoding='utf-8'))
product=next(x for x in (catalog if isinstance(catalog,list) else catalog['products']) if x['id']==manifest['id'])
assert '0.2.7' in (product.get('active_version'),product.get('candidate_version'))
package={'hashes':known,'members':names,'sidecar_match':True,'manifest_match':True,'source_hash_match':True,'yaml':front,'catalog_active':product.get('active_version'),'catalog_candidate':product.get('candidate_version')}
(scratch/'package-check.json').write_text(json.dumps(package,ensure_ascii=False,indent=2),encoding='utf-8')
print('PACKAGE PASS',known['0.2.7'],'members',len(names),'catalog',product.get('active_version'),product.get('candidate_version'))
script=scratch/'extract/wangbin-tender-analyzer/scripts/check_response.py';errors=scratch/'errors';errors.mkdir(exist_ok=False)
tender=errors/'tender.txt';tender.write_text('1. 必须支持自动备份。',encoding='utf-8')
response=errors/'response.md';response.write_text('1. 我方支持自动备份。',encoding='utf-8')
(errors/'bad.md').write_bytes(b'\xff\xfe');(errors/'bad.xlsx').write_bytes(b'not xlsx');(errors/'bad.pdf').write_text('fake pdf',encoding='utf-8')
cases={'missing_response':['--mode','check'],'invalid_utf8':['--mode','check','--response',str(errors/'bad.md')],'unsupported':['--mode','check','--response',str(errors/'bad.pdf')],'catalog_corrupt':['--mode','check','--response',str(response),'--attachment-catalog',str(errors/'bad.xlsx')],'project_escape':['--mode','check','--response',str(response),'--project','../outside'],'positive':['--mode','check','--response',str(response)]}
wants=['MISSING_RESPONSE','INVALID_UTF8','INPUT_TYPE_UNSUPPORTED','CATALOG_READ_FAILED','OUTPUT_PATH_INVALID',None]
records=[]
for (name,opts),code in zip(cases.items(),wants):
 out=errors/name;out.mkdir();cmd=[sys.executable,str(script),'--tender',str(tender),'--output-dir',str(out),*opts]
 run=subprocess.run(cmd,cwd=str(errors),env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'},capture_output=True,text=True,timeout=30)
 files={p.name:sha(p.read_bytes()) for p in out.iterdir()};ok=(run.returncode==2 and 'ERROR '+code in run.stderr and not files) if code else (run.returncode==0 and len(files)==2)
 records.append(dict(id=name,argv=cmd,exit=run.returncode,stdout=run.stdout,stderr=run.stderr,output_sha=files,pass_=ok,input_sha={p.name:sha(p.read_bytes()) for p in (tender,response,errors/'bad.md',errors/'bad.xlsx',errors/'bad.pdf')}))
 print('ERROR',name,'PASS' if ok else 'FAIL','exit',run.returncode)
(errors/'results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(x['pass_'] for x in records)
