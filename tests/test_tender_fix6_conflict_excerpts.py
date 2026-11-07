"""R1-D PRE-QA: a material contradiction must retain both redacted source excerpts."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'packages/skills/wangbin-tender-analyzer/scripts/check_response.py'
spec = importlib.util.spec_from_file_location('tender_conflict_excerpt', SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize('reverse', [False, True], ids=['affirmative-first', 'negative-first'])
def test_conflict_propagates_both_source_excerpts(tmp_path, reverse):
    positive = '营业执照正文：名称为虚构青川公司；统一社会信用代码为虚构示例编号。'
    negative = '该营业执照当前只有封面，证照正文并未随文件附入。'
    lines = [negative, positive] if reverse else [positive, negative]
    (tmp_path / 'tender.txt').write_text('1. 必须提供营业执照。', encoding='utf-8')
    (tmp_path / 'response.md').write_text('1. 营业执照见附件。', encoding='utf-8')
    (tmp_path / '营业执照.txt').write_text('\n'.join(lines), encoding='utf-8')
    out = tmp_path / 'out'
    out.mkdir()
    command = [sys.executable, str(SCRIPT), '--tender', str(tmp_path / 'tender.txt'),
               '--response', str(tmp_path / 'response.md'), '--evidence-file',
               str(tmp_path / '营业执照.txt'), '--mode', 'check', '--project', 'conflict',
               '--output-dir', str(out)]
    proc = subprocess.run(command, text=True, encoding='utf-8', capture_output=True, timeout=45)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    wb = load_workbook(out / 'conflict-投标响应检查.xlsx', read_only=True)
    matrix = dict(zip(next(wb['要求响应矩阵'].values), list(wb['要求响应矩阵'].values)[1]))
    attachment = list(wb['附件核对'].values)[1]
    pending = list(wb['待确认事项'].values)[1]
    md = (out / 'conflict-提交前核对清单.md').read_text(encoding='utf-8')
    assert [matrix[k] for k in module.DIMENSIONS] == ['已定位', '待确认', '已提供（可读文本）', '待确认']
    assert matrix['缺口'] is None
    assert '1:1:1' in md.split('## 需要人工确认', 1)[1].split('## ', 1)[0]
    for explanation in [matrix['建议'], attachment[7], pending[1], md]:
        assert f'肯定 营业执照.txt:{lines.index(positive)+1}「{positive}」' in explanation
        assert f'否定 营业执照.txt:{lines.index(negative)+1}「{negative}」' in explanation
    assert attachment[4:6] == ('已提供（可读文本）', '待确认')
    assert matrix['证据位置'] == '营业执照.txt:1；营业执照.txt:2'
    wb.close()


def test_excerpt_is_bounded_and_redacted_but_preserves_source(tmp_path):
    positive = '营业执照正文：名称为虚构青川公司；联系邮箱 legal@example.com；' + '说明' * 180
    negative = '营业执照正文未附；联系电话 13812345678；' + '注释' * 180
    requirement = {'raw': '必须提供营业执照', 'duty': ['营业执照']}
    status, reason, sources = module.material_assessment(requirement, [('甲证.txt', '\n'.join([positive, negative]))])
    assert status == '待确认'
    assert sources == ['甲证.txt:1', '甲证.txt:2']
    assert '肯定 甲证.txt:1「' in reason and '否定 甲证.txt:2「' in reason
    assert 'legal@example.com' not in reason and '13812345678' not in reason
    assert '[已脱敏' in reason
    assert module.quote(positive) in reason and module.quote(negative) in reason
    assert len(module.quote(positive)) <= module.legacy.MAX_EVIDENCE_CHARS
    assert len(module.quote(negative)) <= module.legacy.MAX_EVIDENCE_CHARS


def test_no_conflict_does_not_invent_opposite_side():
    requirement = {'raw': '必须提供营业执照', 'duty': ['营业执照']}
    positive = '营业执照正文：名称为虚构青川公司；统一社会信用代码为虚构示例编号。'
    negative = '该营业执照当前只有封面，证照正文并未随文件附入。'
    for line in (positive, negative):
        status, reason, sources = module.material_assessment(requirement, [('营业执照.txt', line)])
        assert status != '待确认'
        assert '正反冲突' not in reason
        assert sources == ['营业执照.txt:1']
