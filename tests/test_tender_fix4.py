"""FIX-4 developer controls: source-bound certainty, never certificate authentication."""
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from openpyxl import load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-tender-analyzer/scripts/check_response.py'
P = ('已定位', '已覆盖（文本层面）', '不适用', '不适用')
N = ('已定位', '可能不充分', '不适用', '不适用')
U = ('已定位', '待确认', '不适用', '不适用')
EP = ('已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）')
EN = ('已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）')
EU = ('已定位', '待确认', '已提供（可读文本）', '待确认')
EM = ('已定位', '可能不充分', '未提供（限已提供材料）', '未核验')


@pytest.mark.parametrize('tender,reply,evidence,expected', [
    ('1. 必须支持自动备份。', '1. 自动备份功能是否已经上线尚待核实。', {}, [U]),
    ('1. 必须支持自动备份。', '1. 自动备份能否启用仍待确认。', {}, [U]),
    ('1. 必须支持自动备份。', '1. 自动备份已上线并可正常使用。', {}, [P]),
    ('1. 必须支持自动备份。', '1. 我方不支持自动备份。', {}, [N]),
    ('1. 必须支持自动备份。', '1. 自动备份尚未上线。', {}, [N]),
    ('1. 必须支持自动备份。', '1. 自动备份拟于下一阶段上线。', {}, [N]),
    ('1. 必须支持自动备份。', '1. 自动备份仅提供设计方案。', {}, [N]),
    ('1. 必须支持备份。\n2. 必须支持离线查询。', '1. 备份是否启用尚待核实。\n2. 离线查询现已支持。', {}, [U, P]),
    ('1. 必须支持备份。\n2. 必须支持离线查询。', '1. 备份不支持。\n2. 离线查询是否上线尚待核实。', {}, [N, U]),
    ('1. 必须提供营业执照。', '1. 营业执照见附件。', {'营业执照.txt':'本件仅为登记信息，是否构成正式营业执照尚待核实。'}, [EU]),
    ('1. 必须提供营业执照。', '1. 营业执照见附件。', {'营业执照.txt':'营业执照文本：统一社会信用代码为虚构编号。'}, [EP]),
    ('1. 必须提供营业执照。', '1. 营业执照见附件。', {'营业执照.txt':'仅登记信息，尚未取得营业执照。'}, [EN]),
    ('1. 必须提供营业执照。', '1. 营业执照见附件。', {'营业执照.txt':'营业执照名称登记。'}, [EU]),
    ('1. 必须提供营业执照。', '1. 营业执照见附件。', {'营业执照.txt':''}, [EU]),
    ('1. 必须提供营业执照。', '1. 营业执照见附件。', {'营业执照.txt':'正在申请营业执照，此件为申请表。'}, [EN]),
    ('1. 必须提供营业执照。', '1. 营业执照见附件。', {}, [EM]),
    ('1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。', '1. 甲类证明已提交。\n2. 乙类证明已提交。', {'甲类.txt':'甲类证明文本：甲类有效。','乙类.txt':'乙类证明是否构成正式证明待确认。'}, [EP, EU]),
    ('1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。', '1. 甲类证明已提交。\n2. 乙类证明已提交。', {'乙类.txt':'乙类证明文本：乙类有效。'}, [EM, EP]),
    ('1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。', '1. 甲类证明已提交。\n2. 乙类证明已提交。', {'甲类.txt':'甲类证明尚未取得。','乙类.txt':'乙类证明文本：乙类有效。'}, [EN, EP]),
])
def test_fix4_matrix_and_markdown(tmp_path, tender, reply, evidence, expected):
    (tmp_path/'tender.txt').write_text(tender, encoding='utf-8')
    (tmp_path/'response.md').write_text(reply, encoding='utf-8')
    cmd = [sys.executable, str(SCRIPT), '--tender', str(tmp_path/'tender.txt'), '--response', str(tmp_path/'response.md'), '--mode', 'check', '--output-dir', str(tmp_path), '--project', 'fix4']
    for name, text in evidence.items():
        (tmp_path/name).write_text(text, encoding='utf-8')
        cmd.extend(('--evidence-file', str(tmp_path/name)))
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    workbook = load_workbook(tmp_path/'fix4-投标响应检查.xlsx', read_only=True)
    assert workbook.sheetnames == ['核查概览','要求响应矩阵','附件核对','补遗与版本','待确认事项']
    grid = list(workbook['要求响应矩阵'].values)
    rows = [dict(zip(grid[0], values)) for values in grid[1:]]
    dims = ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态')
    assert [tuple(row[dim] for dim in dims) for row in rows] == expected, rows
    md = (tmp_path/'fix4-提交前核对清单.md').read_text(encoding='utf-8')
    covered = md.split('## 已覆盖范围（仅文本层面）')[1].split('## 未覆盖范围')[0]
    for i, row in enumerate(rows, 1):
        assert row['来源'] == f'tender.txt:{i}'
        assert row['响应位置'] == f'response.md:{i}'
        assert row['唯一ID'] in md
        if row['条件覆盖状态'] != '已覆盖（文本层面）':
            assert row['唯一ID'] not in covered
        if row['条件覆盖状态'] == '可能不充分':
            assert row['缺口']
        if row['条件覆盖状态'] == '待确认':
            assert any(a[0] == row['唯一ID'] for a in list(workbook['待确认事项'].values)[1:])
        if row['附件实际提供状态'] == '已提供（可读文本）':
            if any(evidence.values()):
                assert row['证据位置'] and str(row['证据位置']).split(':')[0] in evidence
            else:
                assert not row['证据位置']  # empty file has no fictitious paragraph
            assert any(a[0] == row['唯一ID'] and a[5] == row['内容支持状态'] for a in list(workbook['附件核对'].values)[1:])
    for dim in dims:
        counts = Counter(row[dim] for row in rows)
        overview = {values[1]:values[2] for values in workbook['核查概览'].values if values[0] == dim and values[1] != '状态'}
        assert dict(counts) == overview
    workbook.close()
