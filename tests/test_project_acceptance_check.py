"""Focused fictional V2 acceptance evidence checks (not platform QA)."""
import importlib.util
import json
from pathlib import Path

import pytest
from docx import Document
from openpyxl import load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-project-acceptance-check/scripts/check_acceptance.py'
spec = importlib.util.spec_from_file_location('acceptance_check', SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
SCOPE = 'R01：提供包含端点、请求参数和返回字段的接口文档。\nR02：提供 Windows Server 2019 部署说明。\nR03：提供本项目培训记录。\n'


def run_case(tmp_path, scope=SCOPE, delivery=None, evidence=None, change=None, previous=None):
    out = tmp_path / ('out2' if previous else 'out')
    out.mkdir()
    groups = {'scope': [], 'delivery': [], 'evidence': [], 'change': []}
    if scope is not None:
        (tmp_path / 'scope.md').write_text(scope, encoding='utf-8')
        groups['scope'].append('scope.md')
    for group, materials in [('delivery', delivery or {}), ('evidence', evidence or {}), ('change', change or {})]:
        for name, text in materials.items():
            (tmp_path / name).write_text(text, encoding='utf-8')
            groups[group].append(name)
    result = app.analyze('星桥演示平台', tmp_path, groups, previous, 'scope.md' if scope else '')
    paths = app.report(result, out)
    book = load_workbook(paths[0], read_only=True)
    doc = Document(paths[1])
    assert book.sheetnames == app.SHEETS
    assert all(title in '\n'.join(p.text for p in doc.paragraphs) for title in app.SECTIONS)
    assert len(doc.tables) >= 2
    assert json.loads(Path(paths[2]).read_text(encoding='utf-8'))['schema_version'] == 1
    book.close()
    return result, doc


def test_r01_r02_r03_real_docx_and_six_sheets(tmp_path):
    result, doc = run_case(tmp_path, delivery={'interface.md': 'D01：R01 接口文档，端点 /demo/items，请求参数：item_id，返回字段：name。',
                                              'deploy.md': 'D02：R02 仅 Ubuntu 部署步骤，未提供 Windows Server 2019 步骤。'})
    assert [r['status'] for r in result['requirements']] == ['EVIDENCE_FOUND', 'NONCONFORMING', 'NO_EVIDENCE_FOUND']
    assert [(g['type'], g['text']) for g in result['findings'] if g['requirement_id'] == result['requirements'][1]['requirement_id']] == [('NONCONFORMING', result['requirements'][1]['conditions'][0]), ('MISSING', result['requirements'][1]['conditions'][0])]
    assert '验收准备报告' in doc.paragraphs[0].text
    assert '已通过验收' not in '\n'.join(p.text for p in doc.paragraphs)
    assert '/demo/items' in result['records'][3]['text']


def test_a02_composite_and_a05_listed_only(tmp_path):
    result, _ = run_case(tmp_path, scope='R01：提供接口文档和部署说明。', delivery={'interface.md': 'R01 接口文档：端点 /demo/items', 'catalog.csv': '名称\n接口说明.docx\n'})
    assert result['requirements'][0]['status'] == 'PARTIAL_EVIDENCE'
    assert any(g['text'] == '部署说明' for g in result['findings'])
    assert any(e['listed_only'] for e in result['evidence'])


def test_a03_version_conflict(tmp_path):
    result, _ = run_case(tmp_path, scope='R01：提供部署说明。', delivery={'deliverables.csv': '名称,版本,内容\n部署说明,v1,仅 Ubuntu 部署步骤\n部署说明,v2,Windows Server 2019 部署步骤\n'})
    # Explicit scope reference is not evidence that either delivery version is effective.
    assert any(c['type'] == 'VERSION_CONFLICT' for c in result['conflicts'])
    assert result['coverage'] == 'N/A'
    assert result['requirements'][0]['status'] == 'CONFLICT'


def test_a04_duplicate_numbers(tmp_path):
    (tmp_path / 'a.csv').write_text('编号,要求原文\nR01,提供接口文档\n', encoding='utf-8')
    (tmp_path / 'b.csv').write_text('编号,要求原文\nR01,提供培训记录\n', encoding='utf-8')
    result = app.analyze('虚构项目', tmp_path, {'scope': ['a.csv', 'b.csv'], 'delivery': [], 'evidence': [], 'change': []})
    assert len({r['requirement_id'] for r in result['requirements']}) == 2
    assert any(c['type'] == 'DUPLICATE_ID' for c in result['conflicts'])


def test_a06_developer_claim_and_a08_unconfirmed_change(tmp_path):
    result, _ = run_case(tmp_path, delivery={'dev.md': 'R03 开发完成'}, change={'new.md': '新增离线模式'})
    assert result['requirements'][2]['status'] == 'NO_EVIDENCE_FOUND'
    assert any(e['claim_only'] for e in result['evidence'])
    assert any(c['type'] == 'UNCONFIRMED_CHANGE' for c in result['conflicts'])
    assert len(result['requirements']) == 3


def test_a09_incremental_preserves_ids_and_resolves(tmp_path):
    before, _ = run_case(tmp_path, delivery={'interface.md': 'R01 接口文档，端点 /demo/items，请求参数：item_id，返回字段：name。',
                                             'deploy.md': 'R02 仅 Ubuntu 部署步骤，未提供 Windows Server 2019 步骤。'})
    after, _ = run_case(tmp_path, delivery={'training.md': '星桥演示平台 R03 培训记录：培训议程及签到说明。'}, previous=before)
    assert [r['requirement_id'] for r in before['requirements']] == [r['requirement_id'] for r in after['requirements']]
    assert [r['status'] for r in after['requirements']] == ['EVIDENCE_FOUND', 'NONCONFORMING', 'EVIDENCE_FOUND']
    assert any(u['type'] == 'RESOLVED' and u['evidence'] for u in after['updates'])
    assert any(u['type'] == 'UNCHANGED' for u in after['updates'])


def test_a10_conflicting_tests(tmp_path):
    result, _ = run_case(tmp_path, evidence={'pass.md': 'R01 测试通过：端点 /demo/items 请求参数：item_id 返回字段：name',
                                               'fail.md': 'R01 测试失败：端点 /demo/items 请求参数：item_id 返回字段：name'})
    assert result['requirements'][0]['status'] == 'CONFLICT'
    assert any(c['type'] == 'EVIDENCE_CONFLICT' for c in result['conflicts'])
    assert all(c['sources'] for c in result['conflicts'])


def test_a11_docx_table_location(tmp_path):
    doc = Document()
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = '编号', '要求原文'
    table.cell(1, 0).text, table.cell(1, 1).text = 'R03', '提供本项目培训记录'
    doc.save(tmp_path / 'scope.docx')
    result = app.analyze('虚构项目', tmp_path, {'scope': ['scope.docx'], 'delivery': [], 'evidence': [], 'change': []})
    assert any('表1/行2/列2' in r['source'] and r['status'] == 'NO_EVIDENCE_FOUND' for r in result['requirements'])


def test_a12_invalid_files_partial_and_all_invalid(tmp_path):
    (tmp_path / 'ok.md').write_text('R01：提供培训记录。', encoding='utf-8')
    (tmp_path / 'broken.docx').write_bytes(b'PK\x03\x04bad')
    (tmp_path / 'fake.docx').write_text('plain text', encoding='utf-8')
    (tmp_path / 'diagram.pdf').write_bytes(b'%PDF-1.7')
    groups = {'scope': ['ok.md'], 'delivery': ['broken.docx', 'fake.docx', 'diagram.pdf'], 'evidence': [], 'change': []}
    result = app.analyze('虚构项目', tmp_path, groups)
    assert result['result'] == 'PARTIAL' and len(result['limitations']) == 3
    with pytest.raises(ValueError, match='no readable material'):
        app.analyze('虚构项目', tmp_path, {'scope': ['broken.docx'], 'delivery': [], 'evidence': [], 'change': []})


def test_a07_candidate_no_binding(tmp_path):
    result, _ = run_case(tmp_path, scope='R01：提供用户登录测试。\nR02：提供登录验证。', evidence={'x.md': '用户登录测试记录', 'y.md': '用户登录检查记录'})
    assert result['requirements'][0]['status'] == 'PENDING_CONFIRMATION'
    assert any(c['type'] == 'MAPPING_CANDIDATE' for c in result['conflicts'])
    assert not any(x['support'] for r in result['requirements'] for x in r['results'])


def test_no_scope_formula_and_path_safety(tmp_path):
    result, _ = run_case(tmp_path, scope=None, delivery={'catalog.csv': '名称\n接口说明.docx\n'})
    assert result['coverage'] == 'N/A' and any('NO_SCOPE_SOURCE' in s for s in result['limitations'])
    assert app.safe_cell('=HYPERLINK("x")').startswith("'=")
    with pytest.raises(ValueError, match='INVALID_INPUT'):
        app.source_path(tmp_path, '../other.md')
    (tmp_path / 'formula.csv').write_text('要求原文\n=HYPERLINK("x")\n', encoding='utf-8')
    with pytest.raises(ValueError, match='UNSUPPORTED_FORMAT'):
        app.read_source(tmp_path, 'formula.csv')


def test_boundary_and_existing_outputs(tmp_path):
    huge = tmp_path / 'huge.md'
    huge.write_bytes(b'x' * (app.MAX_BYTES + 1))
    with pytest.raises(ValueError, match='RESOURCE_LIMIT'):
        app.read_source(tmp_path, 'huge.md')
    result, _ = run_case(tmp_path)
    with pytest.raises(ValueError, match='OUTPUT_FAILED'):
        app.report(result, tmp_path / 'out')


def test_a13_a14_output_references_and_formula_cells(tmp_path):
    result, doc = run_case(tmp_path, scope='R01：提供接口文档和部署说明。',
                           delivery={'interface.md': 'R01 接口文档：端点 /demo/items'})
    worksheet = load_workbook(tmp_path / 'out/星桥演示平台-验收资料核对.xlsx', read_only=True)
    matrix = worksheet['要求追踪']
    assert matrix['H2'].value == 'PARTIAL_EVIDENCE'
    assert 'scope.md/行1' in matrix['D2'].value
    assert 'interface.md/行1' in matrix['G2'].value
    assert any(result['requirements'][0]['requirement_id'] in c.text for row in doc.tables[0].rows for c in row.cells)
    assert any('scope.md/行1' in c.text for row in doc.tables[1].rows for c in row.cells)
    worksheet.close()
    assert all(s['source_id'] in {x['source_id'] for x in result['sources']} for s in result['records'])
    assert all(g['sources'] for g in result['findings'])
    assert app.safe_cell('-2') == "'-2"


def test_changed_source_retains_both_provenance_versions(tmp_path):
    (tmp_path / 'scope.md').write_text('R01：提供培训记录。', encoding='utf-8')
    groups = {'scope': ['scope.md'], 'delivery': [], 'evidence': [], 'change': []}
    old = app.analyze('虚构项目', tmp_path, groups)
    (tmp_path / 'scope.md').write_text('R01：提供培训记录和交接说明。', encoding='utf-8')
    new = app.analyze('虚构项目', tmp_path, groups, previous=old)
    assert new['result'] == 'PARTIAL'
    assert any('IDENTITY_REVIEW' in line for line in new['limitations'])
    assert len(new['sources']) == 2
    assert {x['source_id'] for x in new['records']} == {x['source_id'] for x in new['sources']}


def test_symlink_and_size_boundary_and_cli_codes(tmp_path):
    (tmp_path / 'scope.md').write_text(SCOPE, encoding='utf-8')
    (tmp_path / 'out').mkdir()
    args = ['--project-name', '星桥演示平台', '--authorized-input-root', str(tmp_path), '--output-dir', str(tmp_path / 'out'), '--scope-source', 'scope.md']
    assert app.main(args) == 0
    assert app.main(args) == 4  # overwrite forbidden
    (tmp_path / 'broken.docx').write_bytes(b'not a zip')
    (tmp_path / 'out2').mkdir()
    args[args.index(str(tmp_path / 'out'))] = str(tmp_path / 'out2')
    assert app.main(args + ['--delivery-source', 'broken.docx']) == 3
    assert app.main(['--project-name', '../secret', '--authorized-input-root', str(tmp_path), '--output-dir', str(tmp_path / 'out')]) == 2
    if hasattr(Path, 'symlink_to'):
        link = tmp_path / 'linked.md'
        try:
            link.symlink_to(tmp_path / 'scope.md')
        except OSError:
            pytest.skip('symlink creation unavailable')
        with pytest.raises(ValueError, match='symlink'):
            app.source_path(tmp_path, 'linked.md')
