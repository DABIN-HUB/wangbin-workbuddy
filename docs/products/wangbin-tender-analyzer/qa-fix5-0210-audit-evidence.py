"""Read-only audit of the sole FIX-5 QA run; never executes the candidate again."""
import hashlib
import json
from pathlib import Path
from openpyxl import load_workbook

root = Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check')
doc = root / 'docs/products/wangbin-tender-analyzer'
scr = Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_fix5_independent_0210_once')
current = json.loads((doc/'qa-fix5-0210-independent-results.json').read_text(encoding='utf-8'))
prior = json.loads((doc/'qa-fix4-029-independent-results.json').read_text(encoding='utf-8'))
assert len(current['cases']) == 94 and len(prior['cases']) == 82
for old, new in zip(prior['cases'],current['cases']):
    assert old['id'] == new['id'] and old['expected'] == new['expected'] and old['input_sha'] == new['input_sha'], old['id']
for r in current['cases']:
    for name, digest in r['output_sha'].items():
        p = Path(r['output_paths']['xlsx'] if name.endswith('.xlsx') else r['output_paths']['md'])
        assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == digest, r['id']
    for name,digest in r['input_sha'].items():
        p=Path(r['cwd'])/name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest, r['id']
print('FROZEN 82 expected/input_sha identical; 94 output files and all inputs match recorded sha')
for r in current['cases']:
    if r['id'] in ('H06-unknown-synonym','H10-license-title-only','H12-license-insufficient') or r['issues']:
        print('\nCASE',r['id'],'exit',r['exit'],'issues',r['issues'])
        print('inputs',r['input_sha'])
        print('expected',r['expected'],'actual',r.get('actual'))
        print('matrix',r.get('matrix_rows'))
        print('attachments',r.get('attachment_rows'))
        print('pending',r.get('pending_rows'))
        print('md',r.get('md_text'))
        print('output_sha',r['output_sha'])
