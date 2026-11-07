"""Developer L3 smoke: run the immutable 0.1.5 ZIP outside source PYTHONPATH."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / 'dist/wangbin-import-precheck-0.1.5-skill-candidate.zip'
EXPECTED = 'f8b4188f6b4fe11a5074a3e6ffc60016f3a1322938b7f28953c1a0a62b6f47ed'
assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == EXPECTED
scratch = Path.home() / 'AppData/Local/hermes/profiles/wb-developer/cache/scratch/q01-r1-015-developer'
scratch.mkdir(parents=True, exist_ok=True)
extract = scratch / 'extracted'
extract.mkdir(exist_ok=True)
with zipfile.ZipFile(ARCHIVE) as archive:
    assert archive.testzip() is None
    archive.extractall(extract)
script = extract / 'wangbin-import-precheck/scripts/precheck.py'
assert script.exists()
assert str(ROOT) not in os.environ.get('PYTHONPATH', '')


def csv_file(path, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        csv.writer(stream).writerows(rows)


def reopen(path):
    wb = load_workbook(path, read_only=True, data_only=False)
    try:
        return {ws.title: [list(row) for row in ws.values] for ws in wb.worksheets}
    finally:
        wb.close()


cases = [
    ('mapped', [['编码', '名称'], ['00123', '甲客户']],
     {'customer_code': {'sources': ['编码'], 'required': True, 'data_type': 'text'},
      'customer_name': {'sources': ['名称'], 'required': True}}, None, None, (1, 0), []),
    ('strip', [['名称'], ['   ']],
     {'customer_name': {'sources': ['名称'], 'required': True}}, None,
     {'customer_name': 'strip'}, (0, 1), ['MISSING_REQUIRED_FIELD']),
    ('lower', [['地区'], ['R01']],
     {'region': {'sources': ['地区'], 'required': True, 'allowed_values': ['R01'], 'reference_key': 'region'}},
     [['region'], ['R01']], {'region': 'lower'}, (0, 1), ['INVALID_VALUE', 'NOT_IN_REFERENCE']),
    ('upper', [['地区'], ['r01']],
     {'region': {'sources': ['地区'], 'required': True, 'allowed_values': ['R01'], 'reference_key': 'region'}},
     [['region'], ['R01']], {'region': 'upper'}, (1, 0), []),
    ('collision', [['编码'], ['abc'], ['ABC']],
     {'code': {'sources': ['编码'], 'required': True, 'unique_group': 'code'}},
     None, {'code': 'upper'}, (0, 2), ['DUPLICATE_KEY', 'DUPLICATE_KEY']),
    ('missing-reference', [['地区'], ['R01']],
     {'region': {'sources': ['地区'], 'required': True, 'reference_key': 'region'}},
     None, None, (0, 1), []),
    ('length', [['名称'], [' ab ']],
     {'name': {'sources': ['名称'], 'required': True, 'min_length': 3}},
     None, {'name': 'strip'}, (0, 1), ['LENGTH_VIOLATION']),
]
results = []
for name, lines, fields, reference_rows, transforms, expected_counts, expected_findings in cases:
    case = scratch / name
    case.mkdir(exist_ok=True)
    source = case / 'input.csv'
    csv_file(source, lines)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    rules = case / 'rules.json'
    rules.write_text(json.dumps({'fields': fields}, ensure_ascii=False), encoding='utf-8')
    output = case / 'output'
    output.mkdir(exist_ok=True)
    cmd = [sys.executable, str(script), '--input', str(source), '--output-dir', str(output),
           '--rules', str(rules), '--split', '--authorization', 'developer fixture: split in scratch']
    if reference_rows:
        ref = case / 'reference.csv'
        csv_file(ref, reference_rows)
        cmd.extend(['--reference', str(ref)])
    if transforms:
        cmd.extend(['--transforms', json.dumps(transforms)])
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    run = subprocess.run(cmd, cwd=extract, env=env, capture_output=True, text=True)
    assert run.returncode == 0, (name, run.stderr)
    receipt = json.loads(run.stdout)
    books = {key: reopen(path) for key, path in receipt['outputs'].items()}
    assert set(books['report']) == {'检查概览', '字段映射', '问题明细', '变更记录', '未检查项'}
    assert (receipt['candidate_records'], receipt['quarantine_records']) == expected_counts, name
    assert [finding['category'] for finding in receipt['finding_details']] == expected_findings, name
    assert len(books['candidate']['候选数据']) - 1 == expected_counts[0]
    assert len(books['quarantine']['隔离记录']) - 1 == expected_counts[1]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    if name == 'mapped':
        assert books['candidate']['候选数据'] == [['customer_code', 'customer_name'], ['00123', '甲客户']]
    if name == 'missing-reference':
        assert receipt['status'] == 'PARTIAL'
        assert books['quarantine']['隔离记录'][1][-2] == 'PENDING_VERIFICATION'
    if name == 'upper':
        assert books['report']['变更记录'][1][-2:] == ['INVALID_VALUE,NOT_IN_REFERENCE', 'PASS']
    results.append({'name': name, 'command': cmd, 'cwd': str(extract), 'exit_code': run.returncode,
                    'status': receipt['status'], 'source_sha256': source_hash,
                    'outputs': receipt['outputs'], 'candidate_records': receipt['candidate_records'],
                    'quarantine_records': receipt['quarantine_records'], 'findings': expected_findings})
evidence = {'zip_sha256': EXPECTED, 'source_script': str(script), 'cases': results}
evidence_path = Path(__file__).with_name('audit-r1-015-selftest-results.json')
evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'evidence': str(evidence_path), 'zip_sha256': EXPECTED,
                  'cases': [(case['name'], case['exit_code'], case['status'],
                             case['candidate_records'], case['quarantine_records']) for case in results]}, ensure_ascii=False))
