"""Independent historical 0.1.4 ZIP probe; optional isolated product .runtime base."""
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
ZIP = ROOT.parent / 'wangbin-workbuddy-delivery/six-skills-final/reports/Q01/history/wangbin-import-precheck-0.1.4-skill-candidate.zip'
EXPECTED_SHA = '536763a9c5d64d5b5b53364f5e6e7be93c13457351624b544a0b722b07955d3c'
assert hashlib.sha256(ZIP.read_bytes()).hexdigest() == EXPECTED_SHA
configured_base = os.environ.get('WANGBIN_Q01_PROBE_BASE')
if configured_base is None:
    base = (Path.home() / 'AppData/Local/hermes/profiles/wb-quality/cache/scratch/audit-r1-q01-baseline-t_0eaab29a').resolve()
    assert ROOT not in base.parents and base != ROOT
else:
    requested = Path(configured_base)
    runtime = ROOT / '.runtime'
    assert requested.is_absolute() and '..' not in requested.parts
    assert runtime.resolve() == runtime  # Do not follow a redirected temporary root.
    base = requested.resolve()
    assert runtime in base.parents  # Never write to the product root or arbitrary locations.
base.mkdir(parents=True, exist_ok=True)
extract = base / 'clean-014'
extract.mkdir(exist_ok=True)
with zipfile.ZipFile(ZIP) as archive:
    assert archive.testzip() is None
    for member in archive.infolist():
        assert member.filename.startswith('wangbin-import-precheck/') and '..' not in Path(member.filename).parts
    archive.extractall(extract)
script = extract / 'wangbin-import-precheck/scripts/precheck.py'
assert script.is_file()

cases = [
    ('F01-map', ['编码', '名称'], [['00123', '甲客户']],
     {'customer_code': {'sources': ['编码'], 'rule_id': 'CODE', 'required': True, 'data_type': 'text'},
      'customer_name': {'sources': ['名称'], 'rule_id': 'NAME', 'required': True}}, None, {}, True),
    ('F02-strip', ['名称'], [['   ']],
     {'customer_name': {'sources': ['名称'], 'rule_id': 'NAME', 'required': True}}, None,
     {'customer_name': 'strip'}, True),
    ('F02-lower', ['地区'], [['R01']],
     {'region': {'sources': ['地区'], 'rule_id': 'REGION', 'required': True,
                 'allowed_values': ['R01'], 'reference_key': 'region'}}, [['region'], ['R01']],
     {'region': 'lower'}, True),
    ('F02-upper-resolve', ['地区'], [['r01']],
     {'region': {'sources': ['地区'], 'rule_id': 'REGION', 'required': True,
                 'allowed_values': ['R01'], 'reference_key': 'region'}}, [['region'], ['R01']],
     {'region': 'upper'}, True),
    ('F02-upper-collision', ['编码'], [['abc'], ['ABC']],
     {'customer_code': {'sources': ['编码'], 'rule_id': 'CODE', 'required': True,
                        'unique_group': 'code'}}, None, {'customer_code': 'upper'}, True),
    ('F03-reference-missing', ['地区'], [['R01']],
     {'region': {'sources': ['地区'], 'rule_id': 'REGION', 'required': True,
                 'reference_key': 'region'}}, None, {}, True),
    ('F01-rule-order', ['名称', '编码', '备注'], [['甲客户', '00007', '不应夹带']],
     {'customer_code': {'sources': ['编码'], 'rule_id': 'CODE', 'required': True, 'data_type': 'text'},
      'customer_name': {'sources': ['名称'], 'rule_id': 'NAME', 'required': True}}, None, {}, True),
    ('F01-template-order', ['customer_name', 'customer_code', 'extra'], [['乙客户', '00008', '不应夹带']],
     {'customer_code': {}, 'customer_name': {}}, None, {}, True),
]

def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as fh:
        csv.writer(fh).writerows(rows)

def snapshot(path):
    if not path:
        return None
    wb = load_workbook(path, read_only=True, data_only=False)
    try:
        return {ws.title: [[str(v) if v is not None else None for v in row] for row in ws.values]
                for ws in wb.worksheets}
    finally:
        wb.close()

results = {'zip_sha256': EXPECTED_SHA, 'python': sys.version, 'script': str(script), 'cases': {}}
for case_id, headers, rows, fields, ref_rows, transforms, split in cases:
    case = base / case_id
    case.mkdir(exist_ok=True)
    inp = case / 'source.csv'
    rules = case / 'rules.json'
    out = case / 'output'
    out.mkdir(exist_ok=True)
    write_csv(inp, [headers, *rows])
    rules.write_text(json.dumps({'fields': fields}, ensure_ascii=False), encoding='utf-8')
    command = [sys.executable, str(script), '--input', str(inp), '--output-dir', str(out),
               '--authorization', '独立基线探针：仅在隔离目录生成分流副本', '--split']
    if case_id == 'F01-template-order':
        template = case / 'template.csv'
        write_csv(template, [['customer_code', 'customer_name']])
        command.extend(['--template', str(template)])
    else:
        command.extend(['--rules', str(rules)])
    ref = None
    if ref_rows:
        ref = case / 'reference.csv'
        write_csv(ref, ref_rows)
        command.extend(['--reference', str(ref)])
    if transforms:
        command.extend(['--transforms', json.dumps(transforms, ensure_ascii=False)])
    run = subprocess.run(command, cwd=extract, capture_output=True, text=True)
    try:
        receipt = json.loads(run.stdout) if run.stdout else json.loads(run.stderr)
    except json.JSONDecodeError:
        receipt = None
    actual = {'command': command, 'cwd': str(extract), 'exit_code': run.returncode,
              'stdout': run.stdout, 'stderr': run.stderr, 'input_sha256': hashlib.sha256(inp.read_bytes()).hexdigest(),
              'input': str(inp), 'rules': str(rules), 'reference': str(ref) if ref_rows else None,
              'receipt': receipt, 'workbooks': {}}
    for label, path in (receipt or {}).get('outputs', {}).items():
        actual['workbooks'][label] = {'path': path, 'sheets': snapshot(path)}
    results['cases'][case_id] = actual

member = extract / 'wangbin-import-precheck/README.md'
results['F04'] = {'readme_first_line': member.read_text(encoding='utf-8').splitlines()[0],
                  'skill_version_line': next(line for line in (extract / 'wangbin-import-precheck/SKILL.md').read_text(encoding='utf-8').splitlines() if line.startswith('version:')),
                  'readme_sha256': hashlib.sha256(member.read_bytes()).hexdigest()}
evidence = Path(os.environ.get('WANGBIN_Q01_PROBE_EVIDENCE', str(Path(__file__).with_name('audit-r1-baseline-results.json'))))
evidence.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'evidence': str(evidence), 'cases': {k: {'exit_code': v['exit_code'],
      'receipt_status': (v['receipt'] or {}).get('status'), 'findings': (v['receipt'] or {}).get('finding_details'),
      'unchecked': (v['receipt'] or {}).get('unchecked'),
      'candidate': v['workbooks'].get('candidate', {}).get('sheets'),
      'quarantine': v['workbooks'].get('quarantine', {}).get('sheets'),
      'changes': v['workbooks'].get('report', {}).get('sheets', {}).get('变更记录')}
      for k, v in results['cases'].items()}, 'F04': results['F04']}, ensure_ascii=False, indent=2))
