"""Materialize immutable independent FIX-6 fixtures and SHA manifest; NEVER run production CLI.
Run once before development. Refuse any existing fixture or manifest; no imports from product.
"""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
cases_path = D / 'qa-fix6-prefreeze-cases.json'
fixture_root = D / 'qa-fix6-prefreeze-fixtures'
manifest_path = D / 'qa-fix6-prefreeze-sha.json'
assert not fixture_root.exists() and not manifest_path.exists(), 'freeze is immutable: refuse overwrite'
cases = json.loads(cases_path.read_text(encoding='utf-8'))
assert len(cases['cases']) == 15 and len({c['id'] for c in cases['cases']}) == 15
assert cases['baseline'] == '4fe1e9cd4bc88fc608c6af19e3b788fc4f42fed5'
assert all(len(c['rows']) in (1, 2) and all(len(r['expected']) == 4 for r in c['rows']) for c in cases['cases'])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = {'schema': cases['schema'], 'case_file': cases_path.name, 'case_file_sha256': sha(cases_path),
            'inputs': {}, 'fixture_count': 0, 'no_cli_executed': True}
for case in cases['cases']:
    folder = fixture_root / case['id']
    folder.mkdir(parents=True, exist_ok=False)
    manifest['inputs'][case['id']] = {}
    for name, text in case['inputs'].items():
        assert name in ('tender.txt', 'response.md', '营业执照.txt')
        file = folder / name
        file.write_bytes(text.encode('utf-8'))
        manifest['inputs'][case['id']][name] = sha(file)
        manifest['fixture_count'] += 1
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert all(sha(fixture_root / id / n) == digest for id, files in manifest['inputs'].items() for n, digest in files.items())
print(json.dumps({'cases': len(cases['cases']), 'fixture_count': manifest['fixture_count'],
                  'case_file_sha256': manifest['case_file_sha256'], 'sha_manifest_sha256': sha(manifest_path),
                  'no_cli_executed': True}, ensure_ascii=False))
