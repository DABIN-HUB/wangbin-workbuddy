"""Developer replay of independently frozen fictional cases; not a substitute for QA."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from docx import Document
from openpyxl import load_workbook
import pytest

from generate_contract_fixtures import MATRIX, generate

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'packages/skills/wangbin-contract-return-check/scripts/compare_contracts.py'
DATA = json.loads(MATRIX.read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', DATA['cases'])
def test_frozen_case(case, tmp_path):
    spec = DATA['cases'][case]
    files = generate(case, tmp_path / 'inputs')
    old, new = (Path(files[role]['path']) for role in ('original', 'returned'))
    before = {role: item['sha256'] for role, item in files.items()}
    mode = spec.get('cli_mode', '')
    output = tmp_path / 'output'
    original = old
    returned = new
    if mode == 'same_file':
        returned = old
    if mode == 'output_is_source':
        output = old
    if mode == 'new_directory':
        output = tmp_path / 'new' / 'reports'
    if mode.endswith('_symlink'):
        if mode == 'input_symlink':
            original = tmp_path / 'input-link.docx'
            target, is_dir = old, False
        elif mode == 'parent_symlink':
            parent = tmp_path / 'parent-link'
            original = parent / old.name
            target, is_dir = old.parent, True
            original = parent / old.name
        else:
            output = tmp_path / 'output-link'
            target, is_dir = tmp_path / 'actual-output', True
            target.mkdir()
        link = original if mode == 'input_symlink' else (original.parent if mode == 'parent_symlink' else output)
        try:
            link.symlink_to(target, target_is_directory=is_dir)
        except OSError as exc:
            pytest.skip(f'real symlink NOT_TESTED: {exc}')
    if mode.endswith('_junction'):
        if os.name != 'nt':
            pytest.skip('real Windows junction NOT_TESTED outside Windows')
        target = old.parent if mode == 'parent_junction' else tmp_path / 'actual-output'
        target.mkdir(exist_ok=True)
        link = tmp_path / 'junction'
        created = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True)
        if created.returncode:
            pytest.skip(f'real junction NOT_TESTED: rc={created.returncode} {created.stderr!r}')
        if mode == 'parent_junction':
            original = link / old.name
        else:
            output = link
    args = [sys.executable, str(SCRIPT), '--authorized-root', str(tmp_path), '--output-dir', str(output)]
    if mode != 'omit_roles':
        args += ['--original', str(original), '--returned', str(returned)]
    args += spec.get('cli_options', [])
    results = []
    for _ in range(2 if mode == 'run_twice' else 1):
        proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
        assert proc.stdout, (case, proc.returncode, proc.stderr)
        results.append((proc.returncode, json.loads(proc.stdout)))
    expected = spec['expected']
    rc, actual = results[-1]
    assert {role: hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() for role, item in files.items()} == before
    if 'status' in expected:
        assert actual['status'] == expected['status'], (case, rc, actual)
    if 'reason' in expected:
        assert actual['reason'] == expected['reason'], (case, rc, actual)
    if actual['status'] in ('ERROR', 'NEEDS_INPUT'):
        assert rc != 0 and not list(tmp_path.rglob('*.xlsx'))
        return
    assert rc == 0, (case, actual)
    assert actual['source_sha256'] == before
    if 'types' in expected:
        assert sorted(c['type'] for c in actual['changes']) == sorted(expected['types']), (case, actual)
    if 'confirmed_ids' in expected:
        assert len({c['change_id'] for c in actual['changes']}) == expected['confirmed_ids']
    for name in ('old_locator', 'new_locator'):
        if name in expected:
            assert expected[name] in [c[name] for c in actual['changes']]
    if 'confirmed_topic' in expected:
        assert all(c['topic'] == expected['confirmed_topic'] for c in actual['changes'])
    for text in expected.get('uncertain_texts', []):
        assert text in str(actual['uncertainty'])
    if 'uncertainty_contains' in expected:
        assert expected['uncertainty_contains'] in str(actual['uncertainty'])
    for text in expected.get('uncertain_locators', []):
        assert text in str(actual['uncertainty'])
    if 'delta_contains' in expected:
        assert expected['delta_contains'] in str(actual['changes'])
    if 'locator_contains' in expected:
        assert all(expected['locator_contains'] in c['old_locator'] for c in actual['changes'])
    workbook = load_workbook(actual['xlsx'])
    assert workbook.sheetnames == DATA['common_assertions']['success_sheets']
    note = Document(actual['docx'])
    note_text = '\n'.join(p.text for p in note.paragraphs)
    assert note_text
    if 'xlsx_literal' in expected:
        matching = [cell for row in workbook['逐项差异'] for cell in row if cell.value == expected['xlsx_literal']]
        assert matching and all(cell.data_type == 's' for cell in matching)
    if expected.get('no_formula'):
        assert all(cell.data_type != 'f' for sheet in workbook for row in sheet for cell in row)
    if expected.get('unique_cross_output_ids') or expected.get('draft_only_confirmed_ids'):
        assert all(c['change_id'] in note_text for c in actual['changes'])
    if expected.get('distinct_output_names'):
        assert results[0][1]['xlsx'] != actual['xlsx']
        assert Path(results[0][1]['xlsx']).is_file()
    if expected.get('no_send'):
        assert '未发送' in note_text
    if expected.get('draft_no_invented_change'):
        assert '没有足够的已核实变化可起草' in note_text
    if 'preserve_literals' in expected:
        evidence = str(actual['changes']) + note_text
        assert all(word in evidence for word in expected['preserve_literals'])
