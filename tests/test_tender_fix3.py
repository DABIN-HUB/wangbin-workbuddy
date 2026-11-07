"""FIX-3 developer controls: distinct current, future, evidence and peer objects."""
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-tender-analyzer/scripts/check_response.py'


@pytest.mark.parametrize('tender,response,evidence,expected', [
    ('1. 必须支持自动备份。', '1. 自动备份还未投入使用。', {}, ['可能不充分']),
    ('1. 必须支持自动备份。', '1. 自动备份尚未投入使用。', {}, ['可能不充分']),
    ('1. 必须支持自动备份。', '1. 自动备份已经部署启用，并可执行每日备份。', {}, ['已覆盖（文本层面）']),
    ('1. 必须支持自动备份。', '1. 自动备份目前正在评估是否上线。', {}, ['待确认']),
    ('1. 必须支持自动备份。\n2. 必须支持离线查询。', '1. 自动备份还未投入使用。\n2. 离线查询现已投入使用。', {}, ['可能不充分', '已覆盖（文本层面）']),
    ('1. 必须支持自动备份。', '1. 自动备份已纳入后续研发计划，现阶段无法提供。', {}, ['可能不充分']),
    ('1. 必须支持自动备份。', '1. 自动备份计划后续上线，目前不能提供。', {}, ['可能不充分']),
    ('1. 必须支持自动备份。', '1. 自动备份已投入使用。', {}, ['已覆盖（文本层面）']),
    ('1. 必须支持自动备份。', '1. 自动备份预计交付时提供，具体时间待定。', {}, ['待确认']),
    ('1. 必须支持自动备份。\n2. 必须支持离线查询。', '1. 自动备份已纳入后续研发计划，现阶段无法提供。\n2. 离线查询已经投入使用。', {}, ['可能不充分', '已覆盖（文本层面）']),
    ('1. 必须支持自动备份。\n2. 必须支持离线查询。', '1. 目前尚无法提供自动备份。\n2. 离线查询现已投入使用。', {}, ['可能不充分', '已覆盖（文本层面）']),
    ('1. 必须支持自动备份。\n2. 必须支持离线查询。', '1. 自动备份当前不能提供。\n2. 离线查询功能已上线，我方支持离线查询。', {}, ['可能不充分', '已覆盖（文本层面）']),
    ('1. 必须提供营业执照。', '1. 营业执照已递交。', {'营业执照.txt': '营业执照尚未颁发；此为申请材料，不是营业执照。'}, ['可能不充分']),
    ('1. 必须提供营业执照。', '1. 营业执照已递交。', {'营业执照.txt': '营业执照仍在申请中，尚未核发。'}, ['可能不充分']),
    ('1. 必须提供营业执照。', '1. 营业执照已递交。', {'营业执照.txt': '营业执照文本：统一社会信用代码为虚构示例编号。'}, ['已覆盖（文本层面）']),
    ('1. 必须提供营业执照。', '1. 营业执照已递交。', {'营业执照.txt': '申请材料已收到；发证信息未说明。'}, ['待确认']),
    ('1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。', '1. 甲类证明已提交。\n2. 乙类证明已提交。', {'乙类.txt': '乙类证明尚在申请；本文件不是乙类证明。'}, ['可能不充分', '可能不充分']),
    ('1. 须提供certificate.txt资质证明。', '1. 附件certificate.txt为资质证明。', {'certificate.txt': 'certificate.txt：此文件仅作为示意，不包含任何证照正文。'}, ['可能不充分']),
    ('1. 须提供certificate.txt资质证明。', '1. 附件certificate.txt为资质证明。', {'certificate.txt': '此件仅供展示，不含证明内容。'}, ['可能不充分']),
    ('1. 须提供certificate.txt资质证明。', '1. 附件certificate.txt为资质证明。', {'certificate.txt': '资质证明文本有效，编号为虚构样本。'}, ['待确认']),
    ('1. 须提供certificate.txt资质证明。', '1. 附件certificate.txt为资质证明。', {'certificate.txt': '文件名称为certificate.txt；内容待填写。'}, ['待确认']),
    ('1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。', '1. 甲类证明已提交。\n2. 乙类证明已提交。', {'甲类.txt': '甲类证明文本：甲类有效。', '乙类.txt': '乙类证明尚在申请；本文件不是乙类证明。'}, ['已覆盖（文本层面）', '可能不充分']),
    ('1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。', '1. 甲类证明已提交。\n2. 乙类证明已提交。', {'乙类.txt': '乙类证明仍在申请，尚未取得。'}, ['可能不充分', '可能不充分']),
    ('1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。', '1. 甲类证明已提交。\n2. 乙类证明已提交。', {'乙类.txt': '乙类证明文本：乙类有效。'}, ['可能不充分', '已覆盖（文本层面）']),
    ('1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。', '1. 甲类证明已提交。\n2. 乙类证明已提交。', {'乙类.txt': '乙类证明办理状态未说明。'}, ['可能不充分', '待确认']),
])
def test_fix3_four_dimensions_and_md(tmp_path, tender, response, evidence, expected):
    (tmp_path / 'tender.txt').write_text(tender, encoding='utf-8')
    (tmp_path / 'response.md').write_text(response, encoding='utf-8')
    cmd = [sys.executable, str(SCRIPT), '--tender', str(tmp_path / 'tender.txt'), '--response', str(tmp_path / 'response.md'), '--mode', 'check', '--output-dir', str(tmp_path), '--project', 'fix3']
    for name, content in evidence.items():
        (tmp_path / name).write_text(content, encoding='utf-8')
        cmd += ['--evidence-file', str(tmp_path / name)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    book = load_workbook(tmp_path / 'fix3-投标响应检查.xlsx', read_only=True)
    assert book.sheetnames == ['核查概览', '要求响应矩阵', '附件核对', '补遗与版本', '待确认事项']
    grid = list(book['要求响应矩阵'].values)
    rows = [dict(zip(grid[0], row)) for row in grid[1:]]
    md = (tmp_path / 'fix3-提交前核对清单.md').read_text(encoding='utf-8')
    assert [row['条件覆盖状态'] for row in rows] == expected, rows
    for index, row in enumerate(rows, 1):
        assert row['响应存在状态'] == '已定位'
        assert f'response.md:{index}' in str(row['响应位置'])
        assert f'tender.txt:{index}' in str(row['来源'])
        assert row['唯一ID'] in md
        if len(rows) > 1:
            assert f'response.md:{3-index}' not in str(row['响应位置'])
        if expected[index - 1] == '可能不充分':
            assert row['缺口'] and row['唯一ID'] not in md.split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]
        if index == 1 and not evidence:
            assert (row['附件实际提供状态'], row['内容支持状态']) == ('不适用', '不适用')
        if row['附件实际提供状态'] == '已提供（可读文本）':
            assert any(a[0] == row['唯一ID'] and a[5] == row['内容支持状态'] for a in list(book['附件核对'].values)[1:])
    book.close()
