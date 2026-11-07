"""Developer PRE-QA replay of QA's immutable 41-case expectations against 0.2.7.

Does not edit the QA report/probe or generate its expected values from actual output.
All temporary inputs and outputs are written to a new developer scratch directory.
"""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
original = (root / 'docs/products/wangbin-tender-analyzer/qa-audit-r1-new-026-probe.py').read_text(encoding='utf-8')
archive = root / 'dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip'
manifest = json.loads((root / (str(archive.relative_to(root)) + '.manifest.json')).read_text(encoding='utf-8'))
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
assert manifest['version'] == '0.2.7' and digest == manifest['sha256']
script_sha = next(m['sha256'] for m in manifest['members'] if m['path'].endswith('/scripts/check_response.py'))
scratch = Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/q06_preqa_027_final')
assert not scratch.exists(), 'refuse to reuse prior extraction/output'
original = original.replace("SCR=Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_independent_026_rerun1')", f"SCR=Path('{scratch.as_posix()}')")
original = original.replace("ZIP=ROOT/'dist/wangbin-tender-analyzer-0.2.6-skill-candidate.zip'", "ZIP=ROOT/'dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip'")
original = original.replace("SID=ROOT/'dist/wangbin-tender-analyzer-0.2.6-skill-candidate.zip.manifest.json'", "SID=ROOT/'dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip.manifest.json'")
original = original.replace("assert sha(ZIP.read_bytes())=='1c18b43f8cb465eb261ae4ccdc950259399f64b9c70477496809e3102dd4753a'", f"assert sha(ZIP.read_bytes())=='{digest}'")
original = original.replace("assert manifest['sha256']==sha(ZIP.read_bytes()) and manifest['version']=='0.2.6'", "assert manifest['sha256']==sha(ZIP.read_bytes()) and manifest['version']=='0.2.7'")
original = original.replace("'1c18b43f8cb465eb261ae4ccdc950259399f64b9c70477496809e3102dd4753a' in (ROOT/'dist/wangbin-tender-analyzer-0.2.6-skill-candidate.zip.sha256')", f"'{digest}' in (ROOT/'dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip.sha256')")
original = original.replace("assert sha(SCRIPT.read_bytes())=='c687c1f81e348fd573997a96719726f362e76dffe71cb62818ec54b11460c4db'", f"assert sha(SCRIPT.read_bytes())=='{script_sha}'")
assert "ZIP=ROOT/'dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip'" in original
exec(compile(original, str(root / 'docs/products/wangbin-tender-analyzer/qa-audit-r1-new-026-probe.py'), 'exec'), {'__name__': '__main__'})
results = json.loads((scratch / 'results.json').read_text(encoding='utf-8'))
failures = [r['id'] for r in results['cases'] if r['issues']]
assert len(results['cases']) == 41, len(results['cases'])
assert results['legacy']['match'], 'original legacy JSON mismatch'
print('PRE_QA', len(results['cases']) - len(failures), '/', len(results['cases']), 'FAILURES', failures, 'SCRATCH', scratch)
if failures:
    raise SystemExit(1)
