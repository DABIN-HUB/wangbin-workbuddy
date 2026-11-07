"""Focused audit-R1 file-backed contract checks for the new response CLI."""
import csv
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-tender-analyzer/scripts/check_response.py'


def invoke(tmp_path, tender, response=None, catalog=None, material=None):
    case = tmp_path
    case.mkdir()
    inputs = []
    for name, content in [('tender.txt', tender), ('response.md', response), ('certificate.txt', material)]:
        if content is not None:
            (case / name).write_text(content + '\n', encoding='utf-8')
    command = [sys.executable, str(SCRIPT), '--tender', str(case / 'tender.txt'),
               '--output-dir', str(case), '--project', 'audit']
    if response is not None:
        command += ['--response', str(case / 'response.md'), '--mode', 'check']
    if catalog:
        path = case / catalog
        if catalog.endswith('.csv'):
            with path.open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows([['附件名称', '关联要求编号'], ['certificate.txt', '1']])
        else:
            book = Workbook()
            book.active.append(['附件名称', '关联要求编号'])
            book.active.append(['certificate.txt', '1'])
            book.save(path)
        command += ['--attachment-catalog', str(path)]
    if material is not None:
        command += ['--evidence-file', str(case / 'certificate.txt')]
    done = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    assert done.returncode == 0, done.stderr
    book = load_workbook(case / 'audit-投标响应检查.xlsx', data_only=True)
    assert book.sheetnames == ['核查概览', '要求响应矩阵', '附件核对', '补遗与版本', '待确认事项']
    header = [cell.value for cell in book.worksheets[1][1]]
    matrix = [dict(zip(header, (cell.value for cell in row))) for row in book.worksheets[1].iter_rows(min_row=2)]
    attachment = list(book.worksheets[2].values)
    summary = list(book.worksheets[0].values)
    md = (case / 'audit-提交前核对清单.md').read_text(encoding='utf-8')
    book.close()
    return matrix, attachment, summary, md


@pytest.mark.parametrize('year', [2028, 2033])
def test_expired_and_shifted_interval(tmp_path, year):
    earlier = year - 1
    tender = f'1. 甲类资质须有效覆盖{year}-01-01至{year}-12-31，附甲类证明 certificate.txt。'
    response = '1. 甲类有效期覆盖该期，见certificate.txt。'
    cert = f'甲类证明：{earlier}-01-01生效，有效截止{earlier}-12-31。'
    matrix, attachments, summary, md = invoke(tmp_path / str(year), tender, response, 'attachments.csv', cert)
    row = matrix[0]
    assert row['响应存在状态'] == '已定位'
    assert row['条件覆盖状态'] == '可能不充分', (row['内容支持状态'], row['缺口'], row['建议'], row['证据位置'])
    assert row['附件实际提供状态'] == '已提供（可读文本）'
    assert row['内容支持状态'] == '不支持（文本层面）'
    assert f'{earlier}-12-31' in row['缺口'] and 'certificate.txt:1' in row['缺口']
    assert '已覆盖范围（仅文本层面）\n- ' + row['唯一ID'] not in md
    assert row['唯一ID'] in md and 'certificate.txt:1' in md
    assert any(entry[0] == row['唯一ID'] and entry[5] == row['内容支持状态'] for entry in attachments[1:])
    assert ('内容支持状态', '不支持（文本层面）', 1) in summary


def test_boundary_issue_date_and_missing_expiry(tmp_path):
    tender = '1. 甲类资质须覆盖2027-01-01至2027-12-31，附certificate.txt。'
    response = '1. 甲类资质覆盖期间，见certificate.txt。'
    good = '甲类证明签发于2026-04-03，2027-01-01生效，2027-12-31失效。'
    row = invoke(tmp_path / 'good', tender, response, 'attachments.xlsx', good)[0][0]
    assert row['内容支持状态'] == '支持（文本层面）', row
    assert row['条件覆盖状态'] == '已覆盖（文本层面）', row
    missing = invoke(tmp_path / 'missing', tender, response, 'attachments.csv', '甲类证明签发于2026-04-03。')
    assert missing[0][0]['内容支持状态'] == '待确认'
    assert '签发日期' in missing[3]


@pytest.mark.parametrize('reply,expected', [
    ('1. 我方不支持自动备份。', '可能不充分'),
    ('1. 我方支持自动备份。', '已覆盖（文本层面）'),
    ('1. 若另行购买模块，我方才支持自动备份。', '可能不充分'),
    ('1. 我方拟于交付后支持自动备份，当前尚未实现。', '可能不充分'),
])
def test_response_polarity_and_condition(tmp_path, reply, expected):
    row, _, _, md = invoke(tmp_path / str(len(list(tmp_path.iterdir()))), '1. 必须支持自动备份。', reply)
    assert row[0]['条件覆盖状态'] == expected, row
    assert row[0]['附件实际提供状态'] == '不适用'
    if expected == '可能不充分':
        assert row[0]['缺口'] and '未覆盖范围' in md


def test_double_negative(tmp_path):
    row, _, _, md = invoke(tmp_path / 'double', '1. 不使用外部云存储。', '1. 本方案不使用外部云存储。')
    assert row[0]['条件覆盖状态'] == '已覆盖（文本层面）', row
    assert row[0]['唯一ID'] in md


def test_unnamed_material_duty(tmp_path):
    row, attachments, _, md = invoke(tmp_path / 'license', '1. 必须提供营业执照。', '1. 我方提供营业执照。')
    assert row[0]['附件实际提供状态'] == '未提供（限已提供材料）', row
    assert row[0]['内容支持状态'] == '未核验'
    assert row[0]['条件覆盖状态'] == '可能不充分'
    assert attachments[1][0] == row[0]['唯一ID']
    assert '营业执照' in str(attachments[1]) and row[0]['唯一ID'] in md


def test_directory_is_not_material_and_empty_condition_is_not_support(tmp_path):
    tender = '1. 须提供certificate.txt资质证明。'
    response = '1. 证书见certificate.txt。'
    listed = invoke(tmp_path / 'listed', tender, response, 'attachments.csv')
    assert listed[0][0]['附件实际提供状态'] == '仅目录登记'
    actual = invoke(tmp_path / 'actual', tender, response, 'attachments.csv', 'certificate.txt：仅为目录占位，不含证书。')
    row = actual[0][0]
    assert row['内容支持状态'] == '不支持（文本层面）', row
    assert row['条件覆盖状态'] == '可能不充分'
    assert row['缺口'] and row['唯一ID'] in actual[3]


def test_start_boundary_and_multiple_certificates(tmp_path):
    tender = '1. 甲类资质须有效覆盖2028-01-01至2028-12-31，附甲类证明 certificate.txt。'
    response = '1. 甲类有效期覆盖该期，见certificate.txt。'
    late = '甲类证明：2028-01-02生效，有效截止2029-12-31。'
    row = invoke(tmp_path / 'late', tender, response, 'attachments.csv', late)[0][0]
    assert row['内容支持状态'] == '不支持（文本层面）', row
    assert '2028-01-02' in row['缺口'] and '生效' in row['缺口']
    multiple = '乙类证明有效期2026-01-01至2035-12-31。\n甲类证明有效期2027-01-01至2027-12-31。'
    row = invoke(tmp_path / 'multiple', tender, response, 'attachments.csv', multiple)[0][0]
    assert row['内容支持状态'] == '不支持（文本层面）', row
    assert 'certificate.txt:2' in row['缺口']


def test_missing_named_material_still_reported_without_catalog(tmp_path):
    row, attachments, summary, md = invoke(tmp_path / 'missing_named',
        '1. 须提供certificate.txt资质证明。', '1. 证书见certificate.txt。')
    assert row[0]['附件实际提供状态'] == '未提供（限已提供材料）'
    assert row[0]['内容支持状态'] == '未核验'
    assert row[0]['唯一ID'] in md and attachments[1][0] == row[0]['唯一ID']
    assert ('附件实际提供状态', '未提供（限已提供材料）', 1) in summary


@pytest.mark.parametrize('reply,covered_expected', [
    ('1. 本产品无法支持自动备份。', False),
    ('1. 当前不能支持自动备份。', False),
    ('1. 我们尚未实现自动备份，仅有设计说明。', False),
    ('1. 只提供自动备份设计文档，功能未上线。', False),
    ('1. 已支持自动备份，功能现已上线。', True),
])
def test_capability_action_status_and_limitation(tmp_path, reply, covered_expected):
    rows, _, summary, md = invoke(tmp_path / 'capability', '1. 必须支持自动备份。', reply)
    row = rows[0]
    assert row['响应存在状态'] == '已定位'
    assert row['条件覆盖状态'] == ('已覆盖（文本层面）' if covered_expected else '可能不充分'), row
    assert bool(row['缺口']) != covered_expected
    assert ('已覆盖范围（仅文本层面）\n- ' + row['唯一ID'] in md) == covered_expected
    assert ('条件覆盖状态', row['条件覆盖状态'], 1) in summary


def test_explicit_named_evidence_without_catalog_is_not_missing_or_certified(tmp_path):
    rows, attachment, summary, md = invoke(tmp_path / 'named',
        '1. 须提供certificate.txt资质证明。', '1. 证书见certificate.txt。',
        material='certificate.txt：仅为目录占位，不含证书。')
    row = rows[0]
    assert row['附件实际提供状态'] == '已提供（可读文本）', row
    assert row['内容支持状态'] == '不支持（文本层面）', row
    assert row['条件覆盖状态'] == '可能不充分'
    assert 'certificate.txt:1' in row['证据位置'] and '未找到实际文件' not in row['缺口']
    assert attachment[1][3] == 'certificate.txt' and attachment[1][5] == '不支持（文本层面）'
    assert ('附件实际提供状态', '已提供（可读文本）', 1) in summary
    assert row['唯一ID'] not in md.split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]


def test_unnamed_license_catalog_csv_xlsx_and_real_text(tmp_path):
    tender = '1. 必须提供营业执照。'
    reply = '1. 我方提供营业执照。'
    for suffix in ('csv', 'xlsx'):
        folder = tmp_path / suffix
        folder.mkdir()
        (folder / 'tender.txt').write_text(tender, encoding='utf-8')
        (folder / 'response.md').write_text(reply, encoding='utf-8')
        catalog = folder / ('attachments.' + suffix)
        if suffix == 'csv':
            catalog.write_text('附件名称,关联要求编号\n营业执照.txt,1\n', encoding='utf-8')
        else:
            book = Workbook()
            book.active.append(['附件名称', '关联要求编号'])
            book.active.append(['营业执照.txt', '1'])
            book.save(catalog)
        command = [sys.executable, str(SCRIPT), '--tender', str(folder / 'tender.txt'), '--response', str(folder / 'response.md'), '--mode', 'check', '--attachment-catalog', str(catalog), '--project', 'audit', '--output-dir', str(folder)]
        done = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        assert done.returncode == 0, done.stderr
        book = load_workbook(folder / 'audit-投标响应检查.xlsx', read_only=True)
        header = [c.value for c in book.worksheets[1][1]]
        row = dict(zip(header, [c.value for c in book.worksheets[1][2]]))
        assert row['附件实际提供状态'] == '仅目录登记', row
        assert row['内容支持状态'] == '未核验'
        assert row['条件覆盖状态'] == '可能不充分'
        book.close()


def test_missing_response_nonzero_no_artifact(tmp_path):
    tender = tmp_path / 'tender.txt'
    tender.write_text('1. 必须支持自动备份。', encoding='utf-8')
    done = subprocess.run([sys.executable, str(SCRIPT), '--tender', str(tender), '--mode', 'check', '--output-dir', str(tmp_path)], capture_output=True, text=True, encoding='utf-8')
    assert done.returncode == 2 and 'MISSING_RESPONSE' in done.stderr
    assert not list(tmp_path.glob('*.xlsx')) and not list(tmp_path.glob('*.md'))


def test_cross_requirement_incremental_material_does_not_cover_other_duty(tmp_path):
    folder = tmp_path / 'cross'
    folder.mkdir()
    (folder / 'tender.txt').write_text('1. 必须提供甲类资质证明。\n2. 必须提供乙类资质证明。', encoding='utf-8')
    (folder / 'response.md').write_text('1. 甲类证明已提交。\n2. 乙类证明已提交。', encoding='utf-8')
    (folder / 'attachments.csv').write_text('附件名称,关联要求编号\n甲类.txt,1\n乙类.txt,2\n', encoding='utf-8')
    (folder / '甲类.txt').write_text('甲类证明文本：甲类有效。', encoding='utf-8')
    for phase in ('catalog', 'actual'):
        target = folder / phase
        target.mkdir()
        command = [sys.executable, str(SCRIPT), '--tender', str(folder / 'tender.txt'), '--response', str(folder / 'response.md'), '--mode', 'check', '--attachment-catalog', str(folder / 'attachments.csv'), '--project', 'cross', '--output-dir', str(target)]
        if phase == 'actual':
            command += ['--evidence-file', str(folder / '甲类.txt')]
        done = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        assert done.returncode == 0, done.stderr
        book = load_workbook(target / 'cross-投标响应检查.xlsx', read_only=True)
        header = [c.value for c in book.worksheets[1][1]]
        first, second = [dict(zip(header, [c.value for c in book.worksheets[1][i]])) for i in (2, 3)]
        if phase == 'catalog':
            assert first['附件实际提供状态'] == second['附件实际提供状态'] == '仅目录登记'
            second_before = second
        else:
            assert first['附件实际提供状态'] == '已提供（可读文本）', first
            assert first['内容支持状态'] == '支持（文本层面）', (first['建议'], first['缺口'], first['证据位置'])
            assert second['附件实际提供状态'] == '仅目录登记'
            assert second['内容支持状态'] == '未核验'
            assert second['唯一ID'] == second_before['唯一ID']
        book.close()


def test_final_zip_clean_extract_formal_cli_and_legacy_json(tmp_path):
    root = SCRIPT.parents[4]
    archive = root / 'dist/wangbin-tender-analyzer-0.2.6-skill-candidate.zip'
    if not archive.is_file():
        pytest.skip('package-only test: final 0.2.6 archive not built yet')
    extract = tmp_path / 'clean'
    extract.mkdir()
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        bundle.extractall(extract)
    packaged = extract / 'wangbin-tender-analyzer'
    scenario = tmp_path / 'input'
    scenario.mkdir()
    (scenario / 'tender.txt').write_text('1. 甲类资质须有效覆盖2035-01-01至2035-12-31，附certificate.txt。', encoding='utf-8')
    (scenario / 'response.md').write_text('1. 甲类资质覆盖该期，见certificate.txt。', encoding='utf-8')
    (scenario / 'certificate.txt').write_text('甲类证明：2034-01-01生效，有效截止2034-12-31。', encoding='utf-8')
    (scenario / 'attachments.csv').write_text('附件名称,关联要求编号\ncertificate.txt,1\n', encoding='utf-8')
    target = tmp_path / 'output'
    target.mkdir()
    clean_env = dict(os.environ)
    clean_env.pop('PYTHONPATH', None)
    done = subprocess.run([sys.executable, str(packaged / 'scripts/check_response.py'), '--tender', str(scenario / 'tender.txt'), '--response', str(scenario / 'response.md'), '--mode', 'check', '--attachment-catalog', str(scenario / 'attachments.csv'), '--evidence-file', str(scenario / 'certificate.txt'), '--output-dir', str(target), '--project', 'zip-proof'], cwd=target, env=clean_env, capture_output=True, text=True, encoding='utf-8')
    assert done.returncode == 0, done.stderr
    book = load_workbook(target / 'zip-proof-投标响应检查.xlsx', read_only=True)
    assert book.sheetnames == ['核查概览', '要求响应矩阵', '附件核对', '补遗与版本', '待确认事项']
    header = [c.value for c in book.worksheets[1][1]]
    row = dict(zip(header, [c.value for c in book.worksheets[1][2]]))
    assert row['条件覆盖状态'] == '可能不充分' and row['内容支持状态'] == '不支持（文本层面）'
    assert 'certificate.txt:1' in str(row['缺口'])
    book.close()
    md = (target / 'zip-proof-提交前核对清单.md').read_text(encoding='utf-8')
    assert row['唯一ID'] in md and 'certificate.txt:1' in md
    legacy = subprocess.run([sys.executable, str(packaged / 'scripts/analyze_tender.py'), '--input', str(packaged / 'examples/fictional-tender.txt')], cwd=target, env=clean_env, capture_output=True, text=True, encoding='utf-8')
    assert legacy.returncode == 0, legacy.stderr
    assert json.loads(legacy.stdout) == json.loads((packaged / 'examples/fictional-tender.expected.json').read_text(encoding='utf-8'))
