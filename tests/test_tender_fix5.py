"""FIX-5 scoped fact and submitted-body table; fictional text only, PRE-QA."""
from pathlib import Path
import subprocess
import sys

import pytest
from openpyxl import load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-tender-analyzer/scripts/check_response.py'
DIMS = ('响应存在状态', '条件覆盖状态', '附件实际提供状态', '内容支持状态')
P = ('已定位', '已覆盖（文本层面）', '不适用', '不适用')
N = ('已定位', '可能不充分', '不适用', '不适用')
U = ('已定位', '待确认', '不适用', '不适用')
EP = ('已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）')
EN = ('已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）')
EU = ('已定位', '待确认', '已提供（可读文本）', '待确认')


@pytest.mark.parametrize('object_,reply,want', [
    ('离线查询', '离线查询的实际运行状态暂时不能确认。', U),
    ('自动备份', '自动备份投入运行与否仍待确认。', U),
    ('离线查询', '离线查询尚未启用。', N),
    ('离线查询', '离线查询已部署启用，可以正常使用。', P),
    ('自动备份', '自动备份已启用，自动备份尚未启用。', U),
    ('自动备份', '自动备份尚未启用，自动备份已启用。', U),
])
def test_scoped_capability(tmp_path, object_, reply, want):
    run_case(tmp_path, f'1. 必须支持{object_}。', f'1. {reply}', {}, [want])


@pytest.mark.parametrize('body,want,marker', [
    ('营业执照\n仅有标题，无登记内容。', EN, '营业执照.txt:2'),
    ('营业执照仅有封面，正文未附。', EN, '营业执照.txt:1'),
    ('营业执照\n本件只剩封面，没有证照正文。', EN, '营业执照.txt:2'),
    ('营业执照', EU, '营业执照.txt:1'),
    ('营业执照文本：统一社会信用代码为虚构编号。', EP, '营业执照.txt:1'),
    ('营业执照仅登记摘要；正式效力待核实。', EU, '营业执照.txt:1'),
    ('营业执照文本：统一社会信用代码为虚构编号。\n此件只有封面，无证照正文。', EU, '营业执照.txt:2'),
])
def test_body_provenance(tmp_path, body, want, marker):
    rows, book, md = run_case(tmp_path, '1. 必须提供营业执照。', '1. 营业执照见附件。', {'营业执照.txt': body}, [want])
    row = rows[0]
    assert marker in row['证据位置']
    attachment = list(book['附件核对'].values)[1]
    assert attachment[4] == want[2] and attachment[5] == want[3] and marker in attachment[6]
    if want == EN:
        assert '正文' in str(row['缺口']) and '营业执照.txt:' in str(row['缺口'])
        assert '仅此文件' in str(row['缺口']) and row['唯一ID'] in md.split('## 确定需要补资料')[1].split('## 需要人工确认')[0]
        assert row['唯一ID'] in md.split('## 未覆盖范围')[1]
    if want == EU and '营业执照文本：' in body:
        assert '正反冲突' in str(attachment[7])
        assert '营业执照.txt:1' in str(attachment[7]) and '营业执照.txt:2' in str(attachment[7])
    book.close()


def test_no_cross_object_borrow(tmp_path):
    run_case(tmp_path, '1. 必须支持自动备份。\n2. 必须支持离线查询。',
             '1. 自动备份的投用状态无法确认。\n2. 离线查询已启用。', {}, [U, P])


def run_case(tmp_path, tender, response, evidence, expected):
    (tmp_path / 'tender.txt').write_text(tender, encoding='utf-8')
    (tmp_path / 'response.md').write_text(response, encoding='utf-8')
    cmd = [sys.executable, str(SCRIPT), '--tender', str(tmp_path/'tender.txt'), '--response', str(tmp_path/'response.md'),
           '--mode', 'check', '--output-dir', str(tmp_path), '--project', 'fix5']
    for name, text in evidence.items():
        path = tmp_path / name
        path.write_text(text, encoding='utf-8')
        cmd += ['--evidence-file', str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=45)
    assert result.returncode == 0, result.stderr
    book = load_workbook(tmp_path / 'fix5-投标响应检查.xlsx', read_only=True)
    assert book.sheetnames == ['核查概览', '要求响应矩阵', '附件核对', '补遗与版本', '待确认事项']
    grid = list(book['要求响应矩阵'].values)
    rows = [dict(zip(grid[0], line)) for line in grid[1:]]
    assert [tuple(row[k] for k in DIMS) for row in rows] == expected, rows
    md = (tmp_path / 'fix5-提交前核对清单.md').read_text(encoding='utf-8')
    for row in rows:
        assert row['唯一ID'] in md if row['条件覆盖状态'] != '已覆盖（文本层面）' else True
        assert row['来源'] and row['响应位置']
    for dim in DIMS:
        tally = {x: sum(row[dim] == x for row in rows) for x in [row[dim] for row in rows]}
        overview = {r[1]:r[2] for r in book['核查概览'].values if r[0] == dim and len(r)>2 and r[1]!='状态'}
        assert tally == overview
    return rows, book, md
