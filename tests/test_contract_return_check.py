"""Focused fictional contract acceptance checks (developer self-test, not independent QA)."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import zipfile

from docx import Document
from openpyxl import load_workbook
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-contract-return-check/scripts/compare_contracts.py'
spec = importlib.util.spec_from_file_location('compare_contracts', SCRIPT)
mod = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def fixture(tmp_path, old, new, old_table=None, new_table=None):
    paths = []
    for label, paragraphs, rows in [('original', old, old_table), ('returned', new, new_table)]:
        file = tmp_path / f'{label}.docx'
        doc = Document()
        for text in paragraphs: doc.add_paragraph(text)
        if rows:
            table = doc.add_table(rows=0, cols=len(rows[0]))
            for values in rows:
                cells = table.add_row().cells
                for cell, value in zip(cells, values): cell.text = value
        doc.save(file)
        paths.append(file)
    return paths


def run(tmp_path, old, new, old_table=None, new_table=None, **options):
    a, b = fixture(tmp_path, old, new, old_table, new_table)
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (a, b)]
    result = mod.run(str(a), str(b), str(tmp_path), **options)
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in (a, b)] == before
    book = load_workbook(result['xlsx'])
    assert book.sheetnames == list(mod.SHEETS)
    note = Document(result['docx'])
    assert note.paragraphs and note.paragraphs[0].text
    assert result['source_sha256'] == dict(zip(('original', 'returned'), before))
    return result, book, '\n'.join(p.text for p in note.paragraphs)


def types(result):
    return [c['type'] for c in result['changes']]


def test_core_number_and_payment_not_amount(tmp_path):
    result, book, note = run(tmp_path, ['第六条，验收后30天付款，金额100000元。'],
                              ['第七条，验收后60天付款，金额100000元。'], draft_message=True)
    assert result['status'] == 'COMPLETE'
    assert sorted(types(result)) == ['MODIFY', 'NUMBER']
    assert '延长30天' in str(result['changes'])
    assert len({c['change_id'] for c in result['changes']}) == 2
    assert all(c['change_id'] in note for c in result['changes'])
    assert book['检查概览']['B9'].value == '2'
    assert '未发送' in note


def test_a02_identical_independent_files(tmp_path):
    result, book, note = run(tmp_path, ['交付后10天验收。'], ['交付后10天验收。'],
                             [['项目A', '100元']], [['项目A', '100元']])
    assert result['status'] == 'COMPLETE' and not result['changes']
    assert book['逐项差异'].max_row == 1
    assert '已检查范围内未发现' in note


def test_a03_add_and_delete(tmp_path):
    added, _, _ = run(tmp_path, ['交付到A地。'], ['交付到A地。', '验收7日内书面反馈。'])
    assert types(added) == ['ADD'] and added['changes'][0]['old_locator'] == 'N/A (不存在)'
    deleted, _, _ = run(tmp_path, ['附录培训一次。'], [])
    assert types(deleted) == ['DELETE'] and deleted['changes'][0]['new_locator'] == 'N/A (不存在)'


def test_a04_move(tmp_path):
    r, _, _ = run(tmp_path, ['服务期12个月。', '付款7天。', '交付到A地。'],
                  ['付款7天。', '交付到A地。', '服务期12个月。'])
    assert types(r) == ['MOVE']
    assert r['changes'][0]['old_locator'] == '正文段落1'
    assert r['changes'][0]['new_locator'] == '正文段落3'


def test_a05_number_only(tmp_path):
    r, _, _ = run(tmp_path, ['第六条 质保一年。'], ['第七条 质保一年。'])
    assert types(r) == ['NUMBER']

def test_a05_number_only_without_action_vocabulary_cli_readback(tmp_path):
    old = '第十一条，质量保证一年。'
    new = '第十二条，质量保证一年。'
    a, b = fixture(tmp_path, [old], [new])
    original_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (a, b)]
    proc = subprocess.run([sys.executable, str(SCRIPT), '--authorized-root', str(tmp_path),
                           '--original', str(a), '--returned', str(b), '--output-dir', str(tmp_path / 'out')],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    import json
    result = json.loads(proc.stdout)
    assert result['status'] == 'COMPLETE' and not result['uncertainty']
    assert types(result) == ['NUMBER']
    change = result['changes'][0]
    assert (change['old_text'], change['new_text'], change['old_locator'], change['new_locator']) == (
        old, new, '正文段落1', '正文段落1')
    assert '第十一条' in change['explicit_delta'] and '第十二条' in change['explicit_delta']
    book = load_workbook(result['xlsx'])
    assert book.sheetnames == list(mod.SHEETS)
    assert (book['逐项差异']['E2'].value, book['逐项差异']['F2'].value,
            book['逐项差异']['G2'].value) == (old, new, 'NUMBER')
    assert book['逐项差异'].max_row == 2
    note = '\n'.join(p.text for p in Document(result['docx']).paragraphs)
    assert old in note and new in note and 'NUMBER' in note
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in (a, b)] == original_hashes

def test_number_only_reverse_unique_and_duplicate_candidates(tmp_path):
    body = '质量保证一年。'
    reverse, _, _ = run(tmp_path, ['第十二条，' + body], ['第十一条，' + body])
    assert reverse['status'] == 'COMPLETE' and types(reverse) == ['NUMBER']
    old = ['第十一条，' + body, '第十三条，' + body]
    new = ['第十二条，' + body, '第十四条，' + body]
    ambiguous, _, _ = run(tmp_path, old, new)
    assert ambiguous['status'] == 'PARTIAL' and not ambiguous['changes']
    assert all(text in str(ambiguous['uncertainty']) for text in old + new)
    unrelated, _, _ = run(tmp_path, ['第十一条，质量保证一年。'], ['第十二条，发生地震双方协商。'])
    assert unrelated['status'] == 'PARTIAL' and not unrelated['changes']


def test_a06_table_two_modifications(tmp_path):
    rows1 = [['商品', '单价', '比例'], ['SKU-X', '单价10元', '付款比例30%']]
    rows2 = [['商品', '单价', '比例'], ['SKU-X', '单价12元', '付款比例40%']]
    r, _, _ = run(tmp_path, [], [], rows1, rows2)
    assert types(r).count('MODIFY') == 2
    assert all('表格1/行2/列' in c['old_locator'] for c in r['changes'])


def test_a07_ambiguous_with_determined_delivery(tmp_path):
    r, _, note = run(tmp_path, ['付款条件', '付款30天', '付款条件', '付款45天', '交付7天'],
                     ['付款条件', '付款40天', '付款条件', '付款50天', '交付9天'])
    assert r['status'] == 'PARTIAL' and r['uncertainty']
    assert any(c['topic'] == '交付' for c in r['changes'])
    assert not any(c['topic'] == '付款' for c in r['changes'])
    assert '待确认与未覆盖' in note


def test_a07_duplicate_payment_does_not_swallow_unique_delivery(tmp_path):
    old = ['付款条件', '付款30天。', '付款条件', '付款30天。', '交付7天。']
    new = ['付款条件', '付款60天。', '付款条件', '付款60天。', '交付9天。']
    r, book, note = run(tmp_path, old, new)
    assert r['status'] == 'PARTIAL'
    assert len(r['changes']) == 1
    change = r['changes'][0]
    assert (change['type'], change['topic'], change['old_locator'], change['new_locator']) == (
        'MODIFY', '交付', '正文段落5', '正文段落5')
    assert change['old_text'] == '交付7天。' and change['new_text'] == '交付9天。'
    assert book['逐项差异'].max_row == 2 and book['关键商务变化'].max_row == 2
    assert change['change_id'] in note
    assert r['uncertainty'] and all('正文段落5' not in str(item) for item in r['uncertainty'])
    assert '正文段落2' in str(r['uncertainty']) and '正文段落4' in str(r['uncertainty'])


def test_a07_no_forced_payment_pair_when_delivery_not_comparable(tmp_path):
    r, _, _ = run(tmp_path, ['付款条件', '付款30天。', '付款条件', '付款30天。', '交付7天。'],
                  ['付款条件', '付款60天。', '付款条件', '付款60天。', '交付地点彻底变更。'])
    assert r['status'] == 'PARTIAL' and r['uncertainty']
    assert not any(c['topic'] == '付款' for c in r['changes'])


def test_competing_payment_with_independent_one_sided_changes(tmp_path):
    old = ['付款条件', '付款30天。', '付款条件', '付款30天。', '附录培训一次。']
    new = ['付款条件', '付款60天。', '付款条件', '付款60天。', '验收7日内书面反馈。']
    result, book, word = run(tmp_path, old, new)
    assert result['status'] == 'PARTIAL'
    assert [(c['type'], c['old_locator'], c['new_locator']) for c in result['changes']] == [
        ('DELETE', '正文段落5', 'N/A (不存在)'),
        ('ADD', 'N/A (不存在)', '正文段落5')]
    assert len(result['uncertainty']) == 1
    assert [c['locator'] for c in result['uncertainty'][0]['candidate_old']] == ['正文段落2', '正文段落4']
    assert [c['locator'] for c in result['uncertainty'][0]['candidate_new']] == ['正文段落2', '正文段落4']
    assert book['检查概览']['B9'].value == '2'
    assert book['逐项差异'].max_row == book['关键商务变化'].max_row == 3
    assert book['待确认与未覆盖'].max_row == 2
    assert all(c['change_id'] in word for c in result['changes'])


def test_competing_payment_same_topic_unmatched_stays_uncertain(tmp_path):
    old = ['付款条件', '付款30天。', '付款条件', '付款30天。', '付款特别安排。']
    new = ['付款条件', '付款60天。', '付款条件', '付款60天。', '付款另外规则。']
    result, _, _ = run(tmp_path, old, new)
    assert result['status'] == 'PARTIAL' and not result['changes']
    assert '正文段落5' in str(result['uncertainty'])


def test_a08_reversed_direction(tmp_path):
    r, _, _ = run(tmp_path, ['第七条，验收后60天付款，金额100000元。'],
                  ['第六条，验收后30天付款，金额100000元。'])
    assert sorted(types(r)) == ['MODIFY', 'NUMBER']
    assert '缩短30天' in str(r['changes'])


def test_a09_negations(tmp_path):
    r, _, _ = run(tmp_path, ['可以延期，价格含税。'], ['必须延期，价格不含税。'])
    assert types(r) == ['MODIFY'] and '不含税' in str(r['changes'])


def test_a10_revision(tmp_path):
    a, b = fixture(tmp_path, ['付款30天。'], ['付款60天。'])
    with zipfile.ZipFile(a) as z:
        parts = {item.filename: z.read(item.filename) for item in z.infolist()}
    parts['word/document.xml'] = parts['word/document.xml'].replace(b'</w:p>', b'<w:ins w:id="1"/></w:p>', 1)
    with zipfile.ZipFile(a, 'w') as z:
        for name, payload in parts.items(): z.writestr(name, payload)
    with pytest.raises(mod.ContractError) as error:
        mod.run(str(a), str(b), str(tmp_path))
    assert error.value.reason == 'REVISION_STATE'


def test_a11_unsupported_drawing(tmp_path):
    a, b = fixture(tmp_path, ['相同。'], ['相同。'])
    with zipfile.ZipFile(b) as z:
        parts = {item.filename: z.read(item.filename) for item in z.infolist()}
    parts['word/document.xml'] = parts['word/document.xml'].replace(b'</w:p>', b'<w:drawing/></w:p>', 1)
    with zipfile.ZipFile(b, 'w') as z:
        for name, payload in parts.items(): z.writestr(name, payload)
    r = mod.run(str(a), str(b), str(tmp_path))
    assert r['status'] == 'PARTIAL' and '未支持载体' in str(r['uncertainty'])


def test_a12_no_invented_draft(tmp_path):
    r, _, note = run(tmp_path, ['相同。'], ['相同。'], draft_message=True)
    assert '没有足够的已核实变化可起草' in note


def test_a13_bad_input_source_unchanged(tmp_path):
    a = tmp_path / 'bad.docx'; a.write_bytes(b'not a zip')
    b, _ = fixture(tmp_path, ['相同。'], ['相同。'])
    before = a.read_bytes()
    with pytest.raises(mod.ContractError) as error:
        mod.run(str(a), str(b), str(tmp_path))
    assert error.value.reason == 'INVALID_DOCX' and a.read_bytes() == before


def test_a14_add_and_core_counts(tmp_path):
    r, book, note = run(tmp_path, ['第六条，验收后30天付款，金额100000元。'],
                         ['第七条，验收后60天付款，金额100000元。', '交付到A地。'])
    assert sorted(types(r)) == ['ADD', 'MODIFY', 'NUMBER']
    assert book['检查概览']['B9'].value == '3'
    assert book['逐项差异'].max_row == 4
    assert all(c['change_id'] in note for c in r['changes'])


def test_focus_and_formula_literal(tmp_path):
    r, book, _ = run(tmp_path, ['付款30天。', '交付A地。', '=1+1'],
                     ['付款60天。', '交付B地。', '@SUM(A1)'], focus_topics=['付款'])
    assert r['status'] == 'PARTIAL'  # Unrelated formula-looking text is a candidate, not a certain modification.
    assert book['逐项差异'].max_row == 2
    assert '交付' in str(r['changes'])
    assert '=1+1' in str(r['uncertainty'])
    result2, book2, _ = run(tmp_path, ['=1+1付款30天。'], ['=1+1付款60天。'])
    assert book2['逐项差异']['E2'].data_type == 's'
    assert book2['逐项差异']['E2'].value == '=1+1付款30天。'


def test_output_collision_and_limit(tmp_path):
    a, b = fixture(tmp_path, ['付款30天。'], ['付款60天。'])
    first = mod.run(str(a), str(b), str(tmp_path), contract_name='合同')
    saved = Path(first['xlsx']).read_bytes()
    second = mod.run(str(a), str(b), str(tmp_path), contract_name='合同')
    assert first['xlsx'] != second['xlsx'] and Path(first['xlsx']).read_bytes() == saved
    huge = tmp_path / 'oversized.docx'
    huge.write_bytes(b'x' * (mod.MAX_BYTES + 1))
    with pytest.raises(mod.ContractError) as error:
        mod.run(str(huge), str(b), str(tmp_path))
    assert error.value.reason == 'LIMIT_EXCEEDED'


def test_changed_price_not_day_delta_and_leading_formula(tmp_path):
    r, book, _ = run(tmp_path, ['-100元，付款30天。'], ['-200元，付款30天。'])
    assert types(r) == ['MODIFY']
    assert '延长' not in r['changes'][0]['explicit_delta']
    assert book['逐项差异']['E2'].value == '-100元，付款30天。'
    assert book['逐项差异']['E2'].data_type == 's'


def test_missing_role_and_unsafe_zip(tmp_path):
    with pytest.raises(mod.ContractError) as error:
        mod.run(None, None, str(tmp_path))
    assert error.value.reason == 'ROLE_AMBIGUOUS'
    a, b = fixture(tmp_path, ['A'], ['B'])
    with zipfile.ZipFile(a, 'a') as z: z.writestr('../escape', b'bad')
    with pytest.raises(mod.ContractError) as error:
        mod.run(str(a), str(b), str(tmp_path))
    assert error.value.reason == 'INVALID_DOCX'


def test_unrelated_sole_and_anchored_are_candidates(tmp_path):
    for prefix, suffix in [([], []), (['共同前言。'], ['共同末尾。'])]:
        r, book, note = run(tmp_path, prefix + ['双方不得泄露商业秘密。'] + suffix,
                            prefix + ['发生地震时由双方协商履行。'] + suffix, draft_message=True)
        assert r['status'] == 'PARTIAL' and not r['changes']
        assert book['逐项差异'].max_row == 1
        assert all(text in str(r['uncertainty']) and text in note for text in
                   ('双方不得泄露商业秘密。', '发生地震时由双方协商履行。'))
        assert '没有足够的已核实变化可起草' in note


def test_same_number_different_obligation_and_unique_payment(tmp_path):
    r, _, _ = run(tmp_path, ['第八条 保密义务。', '验收后30天付款。'],
                  ['第八条 地震协商。', '验收后60天付款。'])
    assert r['status'] == 'PARTIAL' and len(r['changes']) == 1
    assert r['changes'][0]['type'] == 'MODIFY' and '付款' in r['changes'][0]['new_text']
    assert '保密' in str(r['uncertainty']) and '地震' in str(r['uncertainty'])


def test_path_positive_new_directory_and_non_directory(tmp_path):
    a, b = fixture(tmp_path, ['付款30天。'], ['付款60天。'])
    out = tmp_path / 'new' / 'reports'
    result = mod.run(str(a), str(b), str(out), authorized_root=str(tmp_path))
    assert out.is_dir() and Path(result['xlsx']).is_file()
    with pytest.raises(mod.ContractError) as err:
        mod.run(str(a), str(b), str(a), authorized_root=str(tmp_path))
    assert err.value.reason == 'IO_FAILURE'
    with pytest.raises(mod.ContractError) as err:
        mod.run(str(a), str(b), str(out), authorized_root=str(tmp_path / 'new'))
    assert err.value.reason == 'UNSAFE_PATH'


def test_real_symlinks_rejected_when_supported(tmp_path):
    a, b = fixture(tmp_path, ['付款30天。'], ['付款60天。'])
    real_dir = tmp_path / 'real'; real_dir.mkdir()
    original_link = tmp_path / 'input.docx'
    try:
        original_link.symlink_to(a)
    except OSError as exc:
        pytest.skip(f'Windows real symlink NOT_TESTED: {exc}')
    parent_link = tmp_path / 'parent'; parent_link.symlink_to(tmp_path, target_is_directory=True)
    output_link = tmp_path / 'outlink'; output_link.symlink_to(real_dir, target_is_directory=True)
    for inp, out in [(original_link, real_dir), (parent_link / a.name, real_dir), (a, output_link)]:
        with pytest.raises(mod.ContractError) as err:
            mod.run(str(inp), str(b), str(out), authorized_root=str(tmp_path))
        assert err.value.reason == 'UNSAFE_PATH'
    assert not list(real_dir.iterdir())


@pytest.mark.skipif(os.name != 'nt', reason='real Windows junction requires Windows')
def test_real_windows_junction_input_and_output(tmp_path):
    a, b = fixture(tmp_path, ['付款30天。'], ['付款60天。'])
    out = tmp_path / 'real_out'; out.mkdir()
    for name, target in [('parent_junction', tmp_path), ('output_junction', out)]:
        link = tmp_path / name
        command = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)],
                                 capture_output=True)
        assert command.returncode == 0, command.stderr
        assert link.is_junction()
        with pytest.raises(mod.ContractError) as err:
            mod.run(str(link / a.name if name == 'parent_junction' else a), str(b),
                    str(link if name == 'output_junction' else out), authorized_root=str(tmp_path))
        assert err.value.reason == 'UNSAFE_PATH'
    assert not list(out.iterdir())
