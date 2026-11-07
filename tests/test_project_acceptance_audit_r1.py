"""AUDIT-R1: independent expectations on real source files and reopened outputs."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from docx import Document
from openpyxl import load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-project-acceptance-check/scripts/check_acceptance.py'


def run(tmp_path, requirement, material, *, delivery=False, colon=False, extra=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / 'scope.md').write_text('R01：' + requirement + '\n' + (extra or ''), encoding='utf-8')
    (tmp_path / 'material.md').write_text(('R01：' if colon else 'R01 ') + material, encoding='utf-8')
    out = tmp_path / 'out'
    out.mkdir()
    cmd = [sys.executable, str(SCRIPT), '--project-name', '虚构项目', '--authorized-input-root', str(tmp_path),
           '--output-dir', str(out), '--scope-source', 'scope.md', '--effective-version-ref', 'scope.md',
           '--delivery-source' if delivery else '--evidence-source', 'material.md']
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
    snap = json.loads((out / '虚构项目-核查快照.json').read_text(encoding='utf-8'))
    book = load_workbook(out / '虚构项目-验收资料核对.xlsx', read_only=True)
    doc = Document(out / '虚构项目-验收准备报告.docx')
    assert len(book.sheetnames) == 6
    req = snap['requirements'][0]
    assert book['要求追踪']['H2'].value == req['status']
    assert req['status'] in '\n'.join(p.text for p in doc.paragraphs)
    assert '已验收通过' not in '\n'.join(p.text for p in doc.paragraphs)
    book.close()
    return snap


@pytest.mark.parametrize('actual,expected', [(10, 'NONCONFORMING'), (9999, 'NONCONFORMING'),
                                             (10000, 'EVIDENCE_FOUND'), (10001, 'EVIDENCE_FOUND'), (12000, 'EVIDENCE_FOUND')])
@pytest.mark.parametrize('colon', [False, True])
def test_concurrent_comparison(tmp_path, actual, expected, colon):
    snap = run(tmp_path, '同一测试场景下至少支持10000个并发登录。',
               f'同一测试场景下实测最大支持{actual}个并发登录。', colon=colon)
    req = snap['requirements'][0]
    assert req['status'] == expected
    compared = req['results'][0]['comparisons']
    assert str(actual) in compared[0]['reason'] and '10000' in compared[0]['reason']
    assert compared[0]['source'] == 'material.md/行1'
    assert (req['results'][0]['negative'] if expected == 'NONCONFORMING' else req['results'][0]['support'])


@pytest.mark.parametrize('material,expected', [
    ('数据库备份已完成。', 'NO_EVIDENCE_FOUND'),
    ('同一测试场景下已测试并发登录。', 'PENDING_CONFIRMATION'),
    ('同一测试场景下支持12000次每日登录。', 'PENDING_CONFIRMATION'),
])
def test_id_not_sufficient(tmp_path, material, expected):
    snap = run(tmp_path, '同一测试场景下至少支持10000个并发登录。', material)
    assert snap['requirements'][0]['status'] == expected
    assert snap['coverage'] == '0/1'


@pytest.mark.parametrize('requirement,material,expected', [
    ('同一压测场景同时并发登录的人数不得低于8000人。', '同一压测场景实测7999人同时并发登录。', 'NONCONFORMING'),
    ('同一压测场景同时并发登录的人数不得低于8000人。', '同一压测场景实测8000人同时并发登录。', 'EVIDENCE_FOUND'),
    ('同一压测场景同时并发登录的人数高于8000人。', '同一压测场景实测8000人同时并发登录。', 'NONCONFORMING'),
    ('同一压测场景同时并发登录的人数高于8000人。', '同一压测场景实测8001人同时并发登录。', 'EVIDENCE_FOUND'),
])
def test_comparator_paraphrases(tmp_path, requirement, material, expected):
    snap = run(tmp_path, requirement, material)
    assert snap['requirements'][0]['status'] == expected


@pytest.mark.parametrize('material,expected,actual', [
    ('同一压测场景不支持74人并发登录，最大仅支持72人并发登录。', 'NONCONFORMING', '72'),
    ('同一压测场景无法支持74人并发登录。', 'PENDING_CONFIRMATION', None),
    ('同一压测场景不能达到74人并发登录。', 'PENDING_CONFIRMATION', None),
    ('同一压测场景最大只能支持72人并发登录；无法支持74人并发登录。', 'NONCONFORMING', '72'),
    ('同一压测场景无法支持74人并发登录；实测支持73人并发登录。', 'EVIDENCE_FOUND', '73'),
    ('同一压测场景支持74人并发登录；但不支持74人并发登录。', 'PENDING_CONFIRMATION', None),
    ('同一压测场景实测最大支持72人并发登录。', 'NONCONFORMING', '72'),
    ('同一压测场景实测最大支持73人并发登录。', 'EVIDENCE_FOUND', '73'),
    ('同一压测场景实测最大支持74人并发登录。', 'EVIDENCE_FOUND', '74'),
    ('同一压测场景支持74人并发登录。', 'EVIDENCE_FOUND', '74'),
])
def test_negated_capacity_and_number_roles(tmp_path, material, expected, actual):
    snap = run(tmp_path, '同一测试场景下并发登录人数不得低于73人。', material)
    req = snap['requirements'][0]
    assert req['status'] == expected
    assert snap['coverage'] == ('1/1' if expected == 'EVIDENCE_FOUND' else '0/1')
    comparisons = req['results'][0]['comparisons']
    assert comparisons and comparisons[0]['source'] == 'material.md/行1'
    if actual:
        assert f'实际 {actual} 人' in comparisons[0]['reason']
    else:
        assert not req['results'][0]['support']


@pytest.mark.parametrize('material,expected', [
    ('共执行41项登录用例，成功41项，失败0项，但高并发登录用例没有执行。', 'PENDING_CONFIRMATION'),
    ('共执行41项登录用例，成功41项，失败0项；高并发登录测试尚未覆盖。', 'PENDING_CONFIRMATION'),
    ('共执行41项登录用例，成功41项，失败0项，但登录压测用例未执行。', 'PENDING_CONFIRMATION'),
    ('共执行41项登录用例，成功41项，失败0项；高并发登录用例未纳入测试。', 'PENDING_CONFIRMATION'),
    ('共执行41项登录用例，成功41项，失败0项；尚未对高并发登录测试用例进行测试。', 'PENDING_CONFIRMATION'),
    ('共执行41项登录用例，成功41项，失败0项。', 'EVIDENCE_FOUND'),
    ('共执行41项登录用例，成功40项，失败1项。', 'NONCONFORMING'),
])
def test_unexecuted_login_subset(tmp_path, material, expected):
    snap = run(tmp_path, '全部登录测试用例通过。', material)
    req = snap['requirements'][0]
    assert req['status'] == expected
    assert snap['coverage'] == ('1/1' if expected == 'EVIDENCE_FOUND' else '0/1')
    assert req['results'][0]['comparisons'][0]['source'] == 'material.md/行1'
    assert bool(req['results'][0]['pending']) == (expected == 'PENDING_CONFIRMATION')


@pytest.mark.parametrize('os_name,other', [('Windows Server 2022', 'Ubuntu 22.04'),
                                           ('Debian 12', 'Ubuntu 22.04'), ('Debian 13', 'Debian 12')])
def test_environment_difference_not_product_failure(tmp_path, os_name, other):
    snap = run(tmp_path, f'提供 {os_name} 部署说明。', f'{other} 部署说明：安装软件、配置端口、启动服务、验证服务。', delivery=True)
    assert snap['requirements'][0]['status'] == 'NO_EVIDENCE_FOUND'
    assert not any(g['type'] == 'NONCONFORMING' for g in snap['findings'])


@pytest.mark.parametrize('os_name', ['Windows Server 2022', 'Windows Server 2025', 'Debian 12', 'Fedora 40'])
def test_deployment_support_and_missing_step(tmp_path, os_name):
    snap = run(tmp_path / 'full', f'提供 {os_name} 部署说明。',
               f'{os_name} 部署说明：安装软件，配置端口，启动服务，验证健康状态。', delivery=True)
    assert snap['requirements'][0]['status'] == 'EVIDENCE_FOUND'
    partial = run(tmp_path / 'partial', f'提供 {os_name} 部署说明。',
                  f'{os_name} 部署说明：安装软件。', delivery=True)
    assert partial['requirements'][0]['status'] == 'PENDING_CONFIRMATION'


def test_explicit_document_gap(tmp_path):
    snap = run(tmp_path, '提供 Windows Server 2022 部署说明。',
               '仅覆盖Ubuntu，未提供Windows Server 2022步骤。', delivery=True)
    assert snap['requirements'][0]['status'] == 'NONCONFORMING'
    assert {g['type'] for g in snap['findings']} == {'MISSING', 'NONCONFORMING'}


@pytest.mark.parametrize('material,expected', [
    ('共执行100项登录用例，成功100项，失败次数为0。', 'EVIDENCE_FOUND'),
    ('共执行100项登录用例，成功99项，失败1项。', 'NONCONFORMING'),
    ('共执行37项登录用例，成功37项，失败0项。', 'EVIDENCE_FOUND'),
    ('未发现失败。', 'PENDING_CONFIRMATION'),
])
def test_test_counts_and_scope(tmp_path, material, expected):
    snap = run(tmp_path, '全部登录测试用例通过。', material)
    assert snap['requirements'][0]['status'] == expected


def test_compound_incremental_and_conflict(tmp_path):
    base = tmp_path / 'base'
    first = run(base, '提供接口文档和部署说明。', '接口文档：端点 /sample。', delivery=True,
                extra='R02：提供培训记录。\n')
    assert [r['status'] for r in first['requirements']] == ['PARTIAL_EVIDENCE', 'NO_EVIDENCE_FOUND']
    (base / 'old.json').write_text(json.dumps(first, ensure_ascii=False), encoding='utf-8')
    (base / 'deploy.md').write_text('R01 部署说明：安装、配置、启动、验证。', encoding='utf-8')
    (base / 'out2').mkdir()
    cmd = [sys.executable, str(SCRIPT), '--project-name', '虚构项目', '--authorized-input-root', str(base),
           '--output-dir', str(base / 'out2'), '--previous-snapshot', 'old.json', '--delivery-source', 'deploy.md',
           '--effective-version-ref', 'scope.md']
    done = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stderr
    second = json.loads((base / 'out2/虚构项目-核查快照.json').read_text(encoding='utf-8'))
    assert [r['status'] for r in second['requirements']] == ['EVIDENCE_FOUND', 'NO_EVIDENCE_FOUND']
    assert second['requirements'][1]['requirement_id'] == first['requirements'][1]['requirement_id']
    assert any(u['type'] == 'RESOLVED' and u['evidence'] for u in second['updates'])
    assert any(u['type'] == 'UNCHANGED' for u in second['updates'])
    book = load_workbook(base / 'out2/虚构项目-验收资料核对.xlsx', read_only=True)
    assert book['要求追踪']['H2'].value == 'EVIDENCE_FOUND'
    assert book['要求追踪']['H3'].value == 'NO_EVIDENCE_FOUND'
    book.close()
    doc = Document(base / 'out2/虚构项目-验收准备报告.docx')
    assert 'EVIDENCE_FOUND' in ' '.join(c.text for row in doc.tables[0].rows for c in row.cells)

    conflicting = tmp_path / 'conflicting'
    conflicting.mkdir()
    (conflicting / 'scope.md').write_text('R01：全部登录测试用例通过。', encoding='utf-8')
    (conflicting / 'pass.md').write_text('R01 共执行100项登录用例，成功100项，失败0项。', encoding='utf-8')
    (conflicting / 'fail.md').write_text('R01 共执行100项登录用例，成功99项，失败1项。', encoding='utf-8')
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location('audit_module', SCRIPT)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    snap = module.analyze('虚构项目', conflicting,
                          {'scope': ['scope.md'], 'evidence': ['pass.md', 'fail.md'], 'delivery': [], 'change': []},
                          effective_version_ref='scope.md')
    assert snap['requirements'][0]['status'] == 'CONFLICT'
    assert snap['requirements'][0]['results'][0]['support'] and snap['requirements'][0]['results'][0]['negative']
    assert len(snap['requirements'][0]['results'][0]['sources']) == 2


@pytest.mark.parametrize('subset,omission,expected', [
    ('登录异常路径', '尚未执行', 'PENDING_CONFIRMATION'),
    ('登录边界场景', '没测', 'PENDING_CONFIRMATION'),
    ('登录安全流程', '未覆盖', 'PENDING_CONFIRMATION'),
    ('高并发登录分支', '没有测试', 'PENDING_CONFIRMATION'),
    ('登录测试用例', '尚未纳入', 'PENDING_CONFIRMATION'),
    ('注册异常路径', '尚未执行', 'EVIDENCE_FOUND'),
    ('', '', 'EVIDENCE_FOUND'),
])
def test_login_exception_scope_reopened_reports(tmp_path, subset, omission, expected):
    material = '共执行57项登录用例，成功57项，失败0项' + (f'；但是{subset}{omission}' if subset else '') + '。'
    snap = run(tmp_path, '全部登录测试用例通过。', material)
    req = snap['requirements'][0]
    assert req['status'] == expected
    assert snap['coverage'] == ('0/1' if omission and expected == 'PENDING_CONFIRMATION' else '1/1')
    comparison = req['results'][0]['comparisons'][0]
    assert comparison['source'] == 'material.md/行1'
    book = load_workbook(tmp_path / 'out/虚构项目-验收资料核对.xlsx', read_only=True)
    doc = Document(tmp_path / 'out/虚构项目-验收准备报告.docx')
    doc_text = '\n'.join(p.text for p in doc.paragraphs) + '\n' + '\n'.join(
        c.text for table in doc.tables for row in table.rows for c in row.cells)
    assert book['核查概览']['B2'].value == snap['coverage']
    assert book['要求追踪']['H2'].value == expected
    if expected == 'PENDING_CONFIRMATION':
        assert subset in comparison['reason']
        assert req['results'][0]['pending'] and not req['results'][0]['support']
        assert any(subset in gap['text'] and 'material.md/行1' in gap['sources'] for gap in snap['findings'])
        assert subset in book['要求追踪']['K2'].value
        assert 'material.md/行1' in book['要求追踪']['M2'].value
        assert subset in doc_text and 'material.md/行1' in doc_text
    else:
        assert req['results'][0]['support'] and not req['results'][0]['pending']
        assert not snap['findings']
    book.close()
