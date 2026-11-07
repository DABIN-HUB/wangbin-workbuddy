import json,os,subprocess,sys,zipfile,hashlib
from pathlib import Path
from openpyxl import load_workbook
base=Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_independent_025_rerun')
script=base/'extract/wangbin-tender-analyzer/scripts/check_response.py';root=base/'errors';root.mkdir(exist_ok=True)
inputs=root/'tender.txt';inputs.write_text('1. 必须支持自动备份。',encoding='utf-8')
response=root/'response.md';response.write_text('1. 我方支持自动备份。',encoding='utf-8')
(root/'bad.md').write_bytes(b'\xff\xfe')
(root/'bad.xlsx').write_bytes(b'not xlsx')
(root/'bad.pdf').write_text('fake pdf',encoding='utf-8')
cases={'missing_response':['--mode','check'],'invalid_utf8':['--mode','check','--response',str(root/'bad.md')],'unsupported':['--mode','check','--response',str(root/'bad.pdf')],'catalog_corrupt':['--mode','check','--response',str(response),'--attachment-catalog',str(root/'bad.xlsx')],'project_escape':['--mode','check','--response',str(response),'--project','../outside'],'positive':['--mode','check','--response',str(response)]}
expected=['MISSING_RESPONSE','INVALID_UTF8','INPUT_TYPE_UNSUPPORTED','CATALOG_READ_FAILED','OUTPUT_PATH_INVALID',None]
records=[]
for (name,opts),code in zip(cases.items(),expected):
 out=root/name;out.mkdir();cmd=[sys.executable,str(script),'--tender',str(inputs),'--output-dir',str(out),*opts]
 p=subprocess.run(cmd,cwd=str(root),capture_output=True,text=True,env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'})
 rec={'name':name,'command':cmd,'exit':p.returncode,'stderr':p.stderr,'stdout':p.stdout,'outputs':[x.name for x in out.iterdir()]};rec['pass']=((p.returncode==2 and 'ERROR '+code in p.stderr and not rec['outputs']) if code else (p.returncode==0 and len(rec['outputs'])==2))
 records.append(rec);print(name,rec['pass'],p.returncode,rec['stderr'],rec['outputs'])
 (root/'results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
