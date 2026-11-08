"""R2 developer replay of precommitted fictional requirements (not independent QA)."""
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
import pytest

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / 'tests/fixtures/contract-return.r2.expected.json'
DATA = json.loads(FROZEN.read_text(encoding='utf-8'))['cases']
SCRIPT = Path(os.environ['CONTRACT_R2_SCRIPT']) if 'CONTRACT_R2_SCRIPT' in os.environ else ROOT / 'packages/skills/wangbin-contract-return-check/scripts/compare_contracts.py'
SHEETS = ['检查概览', '逐项差异', '关键商务变化', '待确认与未覆盖']


def create_pair(spec, directory):
    directory.mkdir(parents=True, exist_ok=False)
    if 'generator' in spec:
        opts = spec['generator']
        assert opts['kind'] == 'identical_random_chinese_text'
        rng = random.Random(opts['seed'])
        alphabet = '甲乙丙丁戊己庚辛壬癸天地玄黄宇宙洪荒春夏秋冬山川河海金木水火土'
        text = ''.join(rng.choice(alphabet) for _ in range(opts['chars_per_document']))
        original = returned = [text]
        assert len(text) == opts['chars_per_document']
    else:
        original, returned = spec['original'], spec['returned']
    result = {}
    for role, paragraphs in [('original', original), ('returned', returned)]:
        doc = Document()
        for paragraph in paragraphs:
            doc.add_paragraph(paragraph)
        path = directory / f'{role}.docx'
        assert not path.exists()
        doc.save(path)
        result[role] = (path, hashlib.sha256(path.read_bytes()).hexdigest())
    return result


def rows(sheet):
    return [tuple(cell.value for cell in row) for row in sheet.iter_rows(min_row=2)]


@pytest.mark.parametrize('case', DATA)
def test_r2_frozen(case, tmp_path):
    spec = DATA[case]
    expected = spec['expected']
    files = create_pair(spec, tmp_path / 'inputs')
    output = tmp_path / 'output'
    output.mkdir()
    args = [sys.executable, str(SCRIPT), '--authorized-root', str(tmp_path),
            '--original', str(files['original'][0]), '--returned', str(files['returned'][0]),
            '--output-dir', str(output)]
    proc = subprocess.run(args, capture_output=True, text=True, timeout=180)
    assert proc.stdout, (case, proc.returncode, proc.stderr)
    actual = json.loads(proc.stdout)
    evidence = os.environ.get('CONTRACT_R2_EVIDENCE_DIR')
    if evidence:
        directory = Path(evidence)
        directory.mkdir(parents=True, exist_ok=True)
        output_hashes = {kind: hashlib.sha256(Path(actual[kind]).read_bytes()).hexdigest()
                         for kind in ('xlsx', 'docx') if actual.get(kind) and Path(actual[kind]).is_file()}
        (directory / f'{case}.json').write_text(json.dumps({
            'case': case, 'command': args, 'rc': proc.returncode, 'stderr': proc.stderr,
            'actual': actual, 'source_sha256': {role: value for role, (_, value) in files.items()},
            'output_sha256': output_hashes
        }, ensure_ascii=False, indent=2), encoding='utf-8')
    assert proc.returncode == expected['rc'], (case, proc.returncode, actual)
    assert actual['status'] == expected['status'], (case, actual)
    assert actual.get('reason') == expected.get('reason'), (case, actual)
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == before for path, before in files.values())
    if expected['status'] == 'ERROR':
        assert expected['no_success_artifacts'] and not list(output.iterdir())
        return
    assert actual['source_sha256'] == {role: before for role, (_, before) in files.items()}
    assert Path(actual['xlsx']).is_file() and Path(actual['docx']).is_file()
    book = load_workbook(actual['xlsx'])
    assert book.sheetnames == SHEETS
    word = '\n'.join(p.text for p in Document(actual['docx']).paragraphs)
    assert word
    if 'confirmed_count' in expected:
        assert len(actual['changes']) == expected['confirmed_count']
        assert not actual['uncertainty']
        assert rows(book['逐项差异']) == []
    if 'types' in expected:
        assert [change['type'] for change in actual['changes']] == expected['types']
    if 'literal_original' in expected:
        values = [cell for sheet in book for row in sheet for cell in row]
        assert any(c.value == expected['literal_original'] and c.data_type == 's' for c in values)
        assert any(c.value == expected['literal_returned'] and c.data_type == 's' for c in values)
        assert all(c.data_type != 'f' for c in values)
        assert all(c.value not in ('2', 2) for c in values)
    if 'confirmed' in expected:
        assert [{key: change[key] for key in ('type', 'topic', 'old_text', 'new_text', 'old_locator', 'new_locator')}
                for change in actual['changes']] == expected['confirmed'], (case, actual)
        assert all(change['topic'] != '付款' for change in actual['changes'])
        assert all(change['old_text'] != '附录培训一次。' or change['new_text'] == 'N/A (不存在)'
                   for change in actual['changes'])
        assert all(change['new_text'] != '验收7日内书面反馈。' or change['old_text'] == 'N/A (不存在)'
                   for change in actual['changes'])
        candidates_old = [c for w in actual['uncertainty'] for c in w.get('candidate_old', [])]
        candidates_new = [c for w in actual['uncertainty'] for c in w.get('candidate_new', [])]
        assert candidates_old == expected['unconfirmed_old'], (case, candidates_old)
        assert candidates_new == expected['unconfirmed_new'], (case, candidates_new)
        assert len(rows(book['逐项差异'])) == len(expected['confirmed'])
        assert len(rows(book['关键商务变化'])) == len(expected['confirmed'])
        uncovered = str(rows(book['待确认与未覆盖'])) + word
        for item in candidates_old + candidates_new:
            assert item['text'] in uncovered and item['locator'] in uncovered
        for change in actual['changes']:
            assert change['change_id'] in word
