"""Archive immutable independent QA fixtures and actual outputs, not a Skill ZIP."""
import hashlib
import json
import zipfile
from pathlib import Path

root = Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check')
scratch = Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_independent_026_rerun1')
out = root / 'docs/products/wangbin-tender-analyzer'
raw = json.loads((scratch / 'results.json').read_text(encoding='utf-8'))
assert raw['zip_sha'] == '1c18b43f8cb465eb261ae4ccdc950259399f64b9c70477496809e3102dd4753a'
assert len(raw['cases']) == 41
assert len({case['id'] for case in raw['cases']}) == 41
assert sum(bool(case['issues']) for case in raw['cases']) == 5
(out / 'qa-audit-r1-new-026-results.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
errors = scratch / 'errors/results.json'
assert errors.exists() and all(x['pass'] for x in json.loads(errors.read_text(encoding='utf-8')))
(out / 'qa-audit-r1-new-026-errors.json').write_bytes(errors.read_bytes())
archive = out / 'qa-audit-r1-new-026-fixtures-outputs.zip'
files = sorted(p for p in (scratch / 'cases').rglob('*') if p.is_file())
assert files
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, p.relative_to(scratch).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and len(z.namelist()) == len(files)
    for p in files:
        assert hashlib.sha256(z.read(p.relative_to(scratch).as_posix())).digest() == hashlib.sha256(p.read_bytes()).digest()
print('files', len(files), 'sha256', hashlib.sha256(archive.read_bytes()).hexdigest())
