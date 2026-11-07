"""Developer PRE-QA: replay independent FIX-6 frozen fixtures without changing them."""
import json
import hashlib
from collections import Counter
from pathlib import Path
import subprocess
import sys

import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/products/wangbin-tender-analyzer'
SCRIPT = ROOT / 'packages/skills/wangbin-tender-analyzer/scripts/check_response.py'
FROZEN = json.loads((DOC / 'qa-fix6-prefreeze-cases.json').read_text(encoding='utf-8'))
SHA_MANIFEST = json.loads((DOC / 'qa-fix6-prefreeze-sha.json').read_text(encoding='utf-8'))
DIM = FROZEN['dimension_order']


@pytest.mark.parametrize('case', FROZEN['cases'], ids=lambda c: c['id'])
def test_frozen_case(tmp_path, case):
    fixture = DOC / 'qa-fix6-prefreeze-fixtures' / case['id']
    assert hashlib.sha256((DOC / 'qa-fix6-prefreeze-cases.json').read_bytes()).hexdigest() == SHA_MANIFEST['case_file_sha256']
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture.iterdir()} == SHA_MANIFEST['inputs'][case['id']]
    out = tmp_path / 'out'
    out.mkdir()
    cmd = [sys.executable, str(SCRIPT), '--tender', str(fixture / 'tender.txt'),
           '--response', str(fixture / 'response.md'), '--mode', 'check',
           '--project', 'fix6', '--output-dir', str(out)]
    for name in case['inputs']:
        if name not in ('tender.txt', 'response.md'):
            cmd.extend(('--evidence-file', str(fixture / name)))
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=45)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert sorted(p.suffix for p in out.iterdir()) == ['.md', '.xlsx']
    book = load_workbook(out / 'fix6-投标响应检查.xlsx', read_only=True)
    assert book.sheetnames == FROZEN['sheet_order']
    grid = list(book['要求响应矩阵'].values)
    rows = [dict(zip(grid[0], line)) for line in grid[1:]]
    assert len(rows) == len(case['rows'])
    md = (out / 'fix6-提交前核对清单.md').read_text(encoding='utf-8')
    for actual, expected in zip(rows, case['rows']):
        assert actual['来源'] == expected['source']
        assert list(actual[dim] for dim in DIM) == expected['expected'], (case['id'], actual)
        for source in expected['response_sources']:
            assert source in actual['响应位置'], (case['id'], actual)
        for source in expected.get('excluded_sources', []):
            assert source not in actual['响应位置']
        for source in expected.get('evidence_sources', []):
            assert source in actual['证据位置']
        assert bool(actual['缺口']) == (expected['gap'] is not None), (case['id'], actual)
        section = md.split('## ' + expected['md_section'], 1)[1].split('## ', 1)[0]
        assert actual['唯一ID'] in section
        if expected['pending'] is not None:
            assert actual['唯一ID'] in md.split('## 需要人工确认', 1)[1].split('## ', 1)[0]
            assert not actual['缺口']
        elif expected['gap'] is not None:
            assert actual['唯一ID'] in md.split('## 确定需要补资料', 1)[1].split('## ', 1)[0]
            assert actual['唯一ID'] not in md.split('## 已覆盖范围', 1)[1].split('## ', 1)[0]
        if case['id'] in ('V05-conflict-negative-first-renumber', 'V06-conflict-positive-first-renumber'):
            assert '冲突' in str(actual['建议'])
            assert all(source in str(actual['建议']) for source in expected['response_sources'])
            assert '不能运行' in str(actual['响应内容']) and '启用' in str(actual['响应内容'])
        if case['id'] == 'V14-positive-negative-body-conflict':
            assert all(source in str(actual['建议']) for source in expected['evidence_sources'])
        if expected.get('evidence_sources') and actual['附件实际提供状态'] == '已提供（可读文本）':
            attached = [line for line in list(book['附件核对'].values)[1:] if line[0] == actual['唯一ID']]
            assert attached and all(line[4] == actual['附件实际提供状态'] and
                                    line[5] == actual['内容支持状态'] for line in attached)
    for dim in DIM:
        count = Counter(row[dim] for row in rows)
        overview = {line[1]: line[2] for line in book['核查概览'].values if line[0] == dim and line[1] != '状态'}
        assert dict(count) == overview
    book.close()
