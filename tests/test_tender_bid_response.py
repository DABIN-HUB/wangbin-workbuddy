"""Developer-focused fictional BID cases; legacy regression is a separate unchanged file."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'packages/skills/wangbin-tender-analyzer/scripts/check_response.py'
SHEETS = ['核查概览', '要求响应矩阵', '附件核对', '补遗与版本', '待确认事项']


def run(tmp_path, tender, response=None, catalog=None, evidence=None, amendments=None, mode='auto', project='fictional'):
    files = tmp_path / 'inputs'
    files.mkdir(parents=True, exist_ok=True)
    dest = tmp_path / 'results'
    dest.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, str(SCRIPT), '--tender', str(files / 'tender.txt'), '--output-dir', str(dest), '--project', project, '--mode', mode]
    (files / 'tender.txt').write_text(tender, encoding='utf-8')
    if response is not None:
        (files / 'response.txt').write_text(response, encoding='utf-8')
        args += ['--response', str(files / 'response.txt')]
    if catalog is not None:
        if isinstance(catalog, str):
            (files / 'attachments.csv').write_text(catalog, encoding='utf-8')
            path = files / 'attachments.csv'
        else:
            path = files / 'attachments.xlsx'
            catalog.save(path)
        args += ['--attachment-catalog', str(path)]
    for name, content in (evidence or {}).items():
        (files / name).write_text(content, encoding='utf-8')
        args += ['--evidence-file', str(files / name)]
    for index, text in enumerate(amendments or [], 1):
        name = f'amendment-{index}.txt'
        (files / name).write_text(text, encoding='utf-8')
        args += ['--amendment', str(files / name)]
    cp = subprocess.run(args, cwd=ROOT, text=True, encoding='utf-8', capture_output=True)
    if cp.returncode:
        return cp, None, None
    book = load_workbook(dest / f'{project}-投标响应检查.xlsx', data_only=False)
    assert book.sheetnames == SHEETS
    assert all(cell.data_type != 'f' for sheet in book for row in sheet for cell in row)
    md = (dest / f'{project}-提交前核对清单.md').read_text(encoding='utf-8')
    return cp, book, md


def matrix(book):
    return list(book['要求响应矩阵'].values)[1:]


def test_core_catalog_is_not_actual_evidence(tmp_path):
    cp, book, md = run(tmp_path, '1. 必须提供指定资质证明 qualification.txt。', '1. 我方具备该资质。', '附件名称\nqualification.txt\n')
    assert cp.returncode == 0, cp.stderr
    row = matrix(book)[0]
    assert row[5] == 'response.txt:1'
    assert row[9] == '已定位'
    assert row[10] != '已覆盖（文本层面）'
    assert row[11:13] == ('仅目录登记', '未核验')
    assert 'attachments.csv:2' in str(list(book['附件核对'].values))
    assert row[0] in md and '仅目录登记' in md


@pytest.mark.parametrize('tender,response,expected', [
    ('2. 须说明运维响应时间。', '1. 我方具备资质。', '未找到（限已提供响应）'),
    ('3. 技术方案必须同时说明备份周期和恢复时间。', '3. 每日备份。', '已定位'),
    ('7. 系统须支持离线查询。', '7a. 系统支持离线查询。', '候选待确认'),
    ('8. 提供同城双活灾备方案。', '8. 我方提供异地冷备方案。\n9. 我方提供同城双活机房简介。', '已定位'),
])
def test_response_matching_and_conditions(tmp_path, tender, response, expected):
    cp, book, _ = run(tmp_path, tender, response)
    assert cp.returncode == 0, cp.stderr
    row = matrix(book)[0]
    assert row[9] == expected
    assert row[10] != '已覆盖（文本层面）'
    if '7a.' in response:
        assert 'response.txt:1' in row[5]
    if '9.' in response:
        assert 'response.txt:2' in row[5]


def test_actual_material_does_not_automatically_support_claim(tmp_path):
    cp, book, _ = run(tmp_path, '4. 提供有效期覆盖2027年的资质证明 certificate.txt。',
                      '4. 资质有效期覆盖2027年，见 certificate.txt。', '附件名称\ncertificate.txt\n',
                      {'certificate.txt': '本证明有效期至2026年12月31日。'})
    assert cp.returncode == 0, cp.stderr
    row = matrix(book)[0]
    assert row[11] == '已提供（可读文本)'.replace(')', '）')
    assert row[12] == '不支持（文本层面）'
    assert 'certificate.txt:1' in row[8]


def test_formal_amendment_and_conflicting_amendments(tmp_path):
    cp, book, _ = run(tmp_path, '5. 交付期为30日。', '5. 交付期30日。',
                      amendments=['正式补遗第1号：原第5条交付期30日替换为45日。'])
    assert cp.returncode == 0, cp.stderr
    assert len(matrix(book)) == 2
    assert matrix(book)[0][15] == '已替换/撤销（不适用）'
    assert 'amendment-1.txt:1' in str(list(book['补遗与版本'].values))
    cp, book, _ = run(tmp_path / 'other', '6. 提供纸质两份。', '6. 提供纸质一份。', amendments=[
        '正式补遗A：原第6条改为纸质一份。', '正式补遗B：原第6条改为纸质三份。'])
    assert cp.returncode == 0, cp.stderr
    assert len(list(book['补遗与版本'].values)) == 3
    assert '待确认' in str(list(book['补遗与版本'].values))


def test_prepare_mode_and_missing_response(tmp_path):
    cp, book, md = run(tmp_path, '9. 必须附报价函。')
    assert cp.returncode == 0, cp.stderr
    assert matrix(book)[0][9:11] == ('未核查', '未核查')
    assert '响应未核查' in md
    cp, _, _ = run(tmp_path / 'missing', '9. 必须附报价函。', mode='check')
    assert cp.returncode == 2 and 'MISSING_RESPONSE' in cp.stderr


def test_catalog_xlsx_duplicate_and_formula_rejected(tmp_path):
    wb = Workbook(); wb.active.append(['附件名称']); wb.active.append(['proof.txt']); wb.active.append(['proof.txt'])
    cp, book, _ = run(tmp_path, '1. 提供 proof.txt。', '1. 提供 proof.txt。', wb)
    assert cp.returncode == 0, cp.stderr
    assert len(list(book['附件核对'].values)) == 3
    wb.active['A2'] = '=HYPERLINK("http://example.invalid")'
    cp, _, _ = run(tmp_path / 'formula', '1. 提供 proof.txt。', '1. 提供 proof.txt。', wb)
    assert cp.returncode == 2 and 'CATALOG_SCHEMA_INVALID' in cp.stderr


def test_errors_and_output_safety(tmp_path):
    cp, _, _ = run(tmp_path, '10. 须附有效资质与近三年案例，投标截止日期另行通知。', '10. 我方正在准备材料。')
    assert cp.returncode == 0
    cp, _, _ = run(tmp_path / 'bad-name', '1. 提供A。', project='../escape')
    assert cp.returncode == 2 and 'OUTPUT_PATH_INVALID' in cp.stderr
    cp, _, _ = run(tmp_path / 'repeat', '1. 提供A。')
    assert cp.returncode == 0
    cp, _, _ = run(tmp_path / 'repeat', '1. 提供A。')
    assert cp.returncode == 2 and 'OUTPUT_EXISTS' in cp.stderr
    folder = tmp_path / 'invalid'
    folder.mkdir()
    (folder / 'tender.txt').write_text('1. 提供A。', encoding='utf-8')
    (folder / 'response.pdf').write_text('private-secret', encoding='utf-8')
    args = [sys.executable, str(SCRIPT), '--tender', str(folder / 'tender.txt'), '--response', str(folder / 'response.pdf'), '--output-dir', str(folder)]
    cp = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert cp.returncode == 2 and 'INPUT_TYPE_UNSUPPORTED' in cp.stderr and 'private-secret' not in cp.stderr
    (folder / 'response.pdf').write_bytes(b'bad')
    (folder / 'response.txt').write_bytes(b'\xff')
    args[args.index(str(folder / 'response.pdf'))] = str(folder / 'response.txt')
    cp = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert cp.returncode == 2 and 'INVALID_UTF8' in cp.stderr
    (folder / 'response.txt').write_text('1. 提供A。', encoding='utf-8')
    (folder / 'attachments.xlsx').write_bytes(b'bad')
    cp = subprocess.run(args + ['--attachment-catalog', str(folder / 'attachments.xlsx')], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert cp.returncode == 2 and 'CATALOG_READ_FAILED' in cp.stderr
    assert not list(folder.glob('*.md'))


def test_added_material_recomputes_only_its_requirement(tmp_path):
    tender = '1. 必须提供指定资质证明 qualification.txt。\n2. 须说明运维响应时间。'
    response = '1. 我方具备该资质。\n2. 运维响应时间24小时。'
    catalog = '附件名称\nqualification.txt\n'
    cp, first, _ = run(tmp_path / 'first', tender, response, catalog)
    cp2, second, _ = run(tmp_path / 'second', tender, response, catalog,
                         {'qualification.txt': '仅说明拟申请资质，尚未取得。'})
    assert cp.returncode == cp2.returncode == 0
    a, b = matrix(first), matrix(second)
    assert a[0][11:13] == ('仅目录登记', '未核验')
    assert b[0][11:13] == ('已提供（可读文本）', '不支持（文本层面）')
    assert a[1] == b[1]


def test_duplicate_number_and_unproven_amendment(tmp_path):
    cp, book, md = run(tmp_path, '1. 须提交A证明。\n第二章 1. 须提交B证明。',
                       '1. 我方准备A证明。', amendments=['最终版：请提交三份。'])
    assert cp.returncode == 0, cp.stderr
    rows = matrix(book)
    assert len(rows) == 3
    assert len({r[0] for r in rows}) == 3
    assert rows[0][9] == '候选待确认'
    assert '待确认' in rows[2][15]
    assert rows[2][0] in md


def test_overview_counts_and_no_invented_qualifications(tmp_path):
    cp, book, md = run(tmp_path, '10. 须附有效资质与近三年案例，投标截止日期另行通知。\n2. 须说明运维响应时间。',
                       '10. 我方正在准备材料。', catalog='附件名称\nproof.txt\n')
    assert cp.returncode == 0, cp.stderr
    rows = matrix(book)
    overview = list(book['核查概览'].values)
    for col, title in [(9, '响应存在状态'), (10, '条件覆盖状态'), (11, '附件实际提供状态'), (12, '内容支持状态')]:
        for state in set(r[col] for r in rows):
            assert (title, state, sum(r[col] == state for r in rows)) in overview
    for forbidden in ('证书号码：', '必然废标', '中标率：', '保证金已到账'):
        assert forbidden not in md
    assert all(r[0] in md for r in rows if r[13] or r[14] != '按源文件行核对，不能推断投标结果')
