"""Local candidate/evaluation integrity and fictional clean-extraction smoke; not WorkBuddy validation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from docx import Document
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
PRODUCT = 'wangbin-project-acceptance-check'
EVAL = Path(__file__).resolve().parent / 'evaluation'
ZIP = ROOT / 'dist' / f'{PRODUCT}-0.1.2-skill-candidate.zip'
META = json.loads(Path(str(ZIP) + '.manifest.json').read_text(encoding='utf-8'))
SHA = hashlib.sha256(ZIP.read_bytes()).hexdigest()
assert SHA == META['sha256'] == Path(str(ZIP) + '.sha256').read_text(encoding='utf-8').split()[0]
assert SHA == '5117bd7202cd6a322c3aae8246dad79edeb4cd9a876cbcae800ee78ad2a9df57'
assert META['status'] == 'PASS' and META['platform'] == 'BLOCKED' and META['version'] == '0.1.2'
assert META['scope'] == 'local archive integrity only'
skill = (ROOT / 'packages' / 'skills' / PRODUCT / 'SKILL.md').read_text(encoding='utf-8')
product_meta = json.loads((ROOT / 'packages' / 'skills' / PRODUCT / 'manifest.json').read_text(encoding='utf-8'))
assert product_meta['version'] == '0.1.2' and 'version: 0.1.2' in skill
assert product_meta['description_zh'] in skill and product_meta['description_en'] in skill
assert 'display_name: 软件项目验收资料核对' in skill
assert 'display_name_en: Software Project Acceptance Evidence Check' in skill
zh_prompts = (
    '这是合同、需求清单和交付资料，帮我检查准备验收还缺什么，并指出每项要求对应的证据。',
    '这次又补了测试报告和培训记录，请更新核对结果，说明哪些缺口已经补上。',
    '根据现有核对结果生成一份验收准备报告，未确认事项单独列出来，不要写成已经验收通过。',
)
en_prompts = (
    'Review this contract, requirements list, and delivery material to identify acceptance gaps and the evidence for each requirement.',
    'I have added test and training records. Update the findings and explain which gaps are now covered.',
    'Prepare an acceptance-readiness report from the verified findings, keeping unresolved items separate from confirmed evidence.',
)
assert all(prompt in skill for prompt in zh_prompts + en_prompts)
with zipfile.ZipFile(ZIP) as archive:
    names = archive.namelist()
    assert archive.testzip() is None and len(names) == len(set(names)) == 9
    assert set(names) == {m['path'] for m in META['members']}
    for member in META['members']:
        name = member['path']
        assert name.startswith(PRODUCT + '/') and not any(p in ('..', '') for p in name.split('/'))
        data = archive.read(name)
        assert hashlib.sha256(data).hexdigest() == member['sha256'] and len(data) == member['size']
        assert (ROOT / 'packages' / 'skills' / name).read_bytes() == data

header = json.loads((EVAL / 'header.json').read_text(encoding='utf-8'))
cases = [json.loads(line) for line in (EVAL / 'cases.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
assert len(cases) == 8 and len({c['case_name'] for c in cases}) == 8
assert header['dataset_name'] and len(header['profile']['dimensions']) == 4
keys = {d['key'] for d in header['profile']['dimensions']}
assert keys == {'task_completion', 'instruction_follow', 'factuality', 'rule_compliance'}
assert sum(d['weight'] for d in header['profile']['dimensions']) == 1
for case in cases:
    assert {'case_name', 'user_question', 'expected', 'checklist_by_dim'} <= case.keys()
    assert set(case['checklist_by_dim']) == keys
    assert all(case['checklist_by_dim'][key] for key in keys)
    for item in case.get('input_files', []):
        rel = item['rel']
        assert rel.startswith('workspace/case_') and '..' not in Path(rel).parts
        assert (EVAL / rel).is_file(), rel
assert len(list((EVAL / 'workspace').glob('case_*/*'))) == 5

with tempfile.TemporaryDirectory(prefix='q02-t04-', dir=os.environ.get('TMPDIR') or None) as temp:
    base = Path(temp)
    clean = base / 'extract'
    clean.mkdir()
    with zipfile.ZipFile(ZIP) as archive:
        archive.extractall(clean)
    authorized = base / 'authorized'
    authorized.mkdir()
    output = authorized / 'out'
    output.mkdir()
    for name in ('scope.md', 'interface.md', 'deploy.md'):
        (authorized / name).write_bytes((EVAL / 'workspace' / 'case_001' / name).read_bytes())
    proc = subprocess.run([
        sys.executable, str(clean / PRODUCT / 'scripts' / 'check_acceptance.py'),
        '--project-name', '星桥演示平台', '--authorized-input-root', str(authorized),
        '--output-dir', str(output), '--scope-source', 'scope.md',
        '--delivery-source', 'interface.md', '--delivery-source', 'deploy.md',
        '--effective-version-ref', 'scope.md'
    ], capture_output=True, text=True, encoding='utf-8')
    assert proc.returncode == 0, proc.stderr
    snapshot = json.loads((output / '星桥演示平台-核查快照.json').read_text(encoding='utf-8'))
    assert [r['status'] for r in snapshot['requirements']] == [
        'EVIDENCE_FOUND', 'NONCONFORMING', 'NO_EVIDENCE_FOUND'
    ]
    assert snapshot['coverage'] == '3/5'
    book = load_workbook(output / '星桥演示平台-验收资料核对.xlsx', data_only=False)
    sheets = [s.title for s in book.worksheets]
    assert sheets == ['核查概览', '要求追踪', '证据索引', '缺口与不符合', '冲突与待确认', '本次更新']
    rows = [[cell.value for row in sheet for cell in row] for sheet in book.worksheets]
    assert not any(cell.data_type == 'f' for sheet in book.worksheets for row in sheet for cell in row)
    book.close()
    doc = Document(str(output / '星桥演示平台-验收准备报告.docx'))
    words = ' '.join(p.text for p in doc.paragraphs) + ' ' + ' '.join(
        cell.text for table in doc.tables for row in table.rows for cell in row.cells)
    assert len(doc.tables) >= 2 and '草稿' in words and '项目已通过验收' not in words
    for r in snapshot['requirements']:
        assert r['requirement_id'] in words and r['status'] in words
        assert any(r['requirement_id'] in str(row) and r['status'] in str(row) for row in rows)
    print(json.dumps({'zip_sha256': SHA, 'zip_members': len(names), 'evaluation_cases': len(cases),
                      'evaluation_files': 5, 'smoke_exit': proc.returncode, 'coverage': snapshot['coverage'],
                      'statuses': [r['status'] for r in snapshot['requirements']],
                      'sheets': sheets, 'docx_tables': len(doc.tables), 'platform': 'NOT_TESTED'}, ensure_ascii=False))
