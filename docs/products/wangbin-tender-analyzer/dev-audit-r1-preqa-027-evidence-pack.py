"""Persist PRE-QA real-file outputs and hashes from the clean 0.2.7 ZIP replay."""
import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
scratch = Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/q06_preqa_027_final')
out = root / 'docs/products/wangbin-tender-analyzer'
raw = json.loads((scratch / 'results.json').read_text(encoding='utf-8'))
assert raw['zip_sha'] == '12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09'
assert len(raw['cases']) == len({case['id'] for case in raw['cases']}) == 41
assert all(not case['issues'] and case['exit'] == 0 and len(case['output_sha']) == 2 for case in raw['cases'])
assert raw['legacy']['match']
(out / 'dev-audit-r1-preqa-027-results.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
errors = json.loads((scratch / 'errors/results.json').read_text(encoding='utf-8'))
assert len(errors) == 6 and all(item['pass'] for item in errors)
(out / 'dev-audit-r1-preqa-027-errors.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding='utf-8')
archive = out / 'dev-audit-r1-preqa-027-fixtures-outputs.zip'
files = sorted(p for p in (scratch / 'cases').rglob('*') if p.is_file())
assert files and not archive.exists()
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, p.relative_to(scratch).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and len(z.namelist()) == len(files)
    for p in files:
        assert hashlib.sha256(z.read(p.relative_to(scratch).as_posix())).digest() == hashlib.sha256(p.read_bytes()).digest()
print('cases', len(raw['cases']), 'files', len(files), 'archive_sha256', hashlib.sha256(archive.read_bytes()).hexdigest())
