"""Preserve actual 0.2.7 QA input/output files, hash and results; never rewrite prior verdict."""
from pathlib import Path
import json, hashlib, zipfile
root=Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check/docs/products/wangbin-tender-analyzer')
scratch=Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_independent_027_rerun1')
data=json.loads((scratch/'results.json').read_text(encoding='utf-8'))
assert data['zip_sha']=='12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09'
assert len(data['cases'])==len({x['id'] for x in data['cases']})==53
assert sum(bool(x['issues']) for x in data['cases'])==6
assert all(not x['issues'] for x in data['cases'][:41])
assert data['legacy']['match']
for x in data['cases']:
 folder=scratch/'cases'/x['id'];actual={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}
 outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (folder/'out').iterdir()}
 assert actual==x['input_sha'] and outputs==x['output_sha']
(root/'qa-audit-r1-new-027-results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for source,dest in [(scratch/'errors/results.json',root/'qa-audit-r1-new-027-errors.json'),(scratch/'package-check.json',root/'qa-audit-r1-new-027-package.json')]:
 assert source.exists();dest.write_bytes(source.read_bytes())
files=sorted(p for p in (scratch/'cases').rglob('*') if p.is_file())
archive=root/'qa-audit-r1-new-027-fixtures-outputs.zip'
assert not archive.exists()
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(scratch).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None and len(z.namelist())==len(files)==len(set(z.namelist()))
 for p in files:assert hashlib.sha256(z.read(p.relative_to(scratch).as_posix())).digest()==hashlib.sha256(p.read_bytes()).digest()
print('QA_CASES',len(data['cases']),'FAILED',sum(bool(x['issues']) for x in data['cases']),'files',len(files),'evidence_sha256',hashlib.sha256(archive.read_bytes()).hexdigest())
