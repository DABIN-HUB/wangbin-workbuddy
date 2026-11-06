"""Focused regression for response-scoped evidence and ambiguous material identity."""
from openpyxl import Workbook

from test_tender_bid_response import matrix, run


def test_a04_response_reference_without_catalog(tmp_path):
    cp, book, md = run(tmp_path, '4. 提供有效期覆盖2027年的资质证明。',
                       '4. 资质有效期覆盖2027年，见 certificate.txt。',
                       evidence={'certificate.txt': '本证明有效期至2026年12月31日。'})
    assert cp.returncode == 0, cp.stderr
    row = matrix(book)[0]
    assert row[11:13] == ('已提供（可读文本）', '不支持（文本层面）')
    assert 'certificate.txt:1' in row[8]
    assert 'response.txt:1' in row[5]
    assert 'certificate.txt' in str(list(book['附件核对'].values))
    assert '不支持（文本层面）' in md
    assert isinstance(md, str)
    relevant = [line for line in md.splitlines() if line.startswith('- ' + str(row[0]) + ' ')]
    assert len(relevant) == 3
    assert all('响应 response.txt:1；材料 certificate.txt:1' in line for line in relevant)
    assert all('已提供（可读文本） / 不支持（文本层面）' in line for line in relevant)
    assert '不认证资质真伪' in md


def test_core_unrelated_file_not_bound_and_a11_added_material(tmp_path):
    tender = '1. 必须提供指定资质证明 qualification.txt。\n2. 须说明运维响应时间。'
    response = '1. 我方具备该资质。\n2. 运维响应时间24小时。'
    catalog = '附件名称\nqualification.txt\n'
    cp, first, _ = run(tmp_path / 'before', tender, response, catalog,
                       {'unrelated.txt': '资质有效期至2027年。'})
    cp2, second, _ = run(tmp_path / 'after', tender, response, catalog,
                         {'qualification.txt': '拟申请资质，尚未取得。', 'unrelated.txt': '资质有效期至2027年。'})
    assert cp.returncode == cp2.returncode == 0
    assert matrix(first)[0][11:13] == ('仅目录登记', '未核验')
    assert matrix(second)[0][11:13] == ('已提供（可读文本）', '不支持（文本层面）')
    assert matrix(first)[1] == matrix(second)[1]


def test_no_cross_requirement_or_bare_candidate_binding(tmp_path):
    cp, book, md = run(tmp_path / 'cross',
                      '1. 提交甲资格证明。\n2. 提交乙资格证明。',
                      '1. 见 certificate.txt。\n2. 见 another.txt。',
                      '附件名称,关联要求编号\ncertificate.txt,2\nanother.txt,2\n',
                      {'certificate.txt': '有效期至2026年。', 'another.txt': '有效期至2027年。'})
    assert cp.returncode == 0, cp.stderr
    assert matrix(book)[0][11:13] == ('待确认', '待确认')
    assert 'certificate.txt:1' not in str(matrix(book)[0][8])
    assert isinstance(md, str)
    first_id = str(matrix(book)[0][0])
    assert all('材料 certificate.txt:1' not in line for line in md.splitlines()
               if line.startswith('- ' + first_id + ' '))
    cp, book, _ = run(tmp_path / 'candidate', '7. 提交甲资格证明。',
                      '7a. 见 certificate.txt，提交甲资格证明。', evidence={'certificate.txt': '有效期至2026年。'})
    assert cp.returncode == 0, cp.stderr
    assert matrix(book)[0][11:13] == ('待确认', '待确认')


def test_csv_xlsx_duplicate_candidates_are_not_verified(tmp_path):
    for kind in ('csv', 'xlsx'):
        if kind == 'csv':
            catalog = '附件名称,关联要求编号\ncertificate.txt,4\ncertificate.txt,4\n'
        else:
            catalog = Workbook()
            catalog.active.append(['附件名称', '关联要求编号'])
            catalog.active.append(['certificate.txt', '4'])
            catalog.active.append(['certificate.txt', '4'])
        cp, book, _ = run(tmp_path / kind,
                          '4. 提供有效期覆盖2027年的资质证明。',
                          '4. 见 certificate.txt，资质有效期覆盖2027年。',
                          catalog, {'certificate.txt': '本证明有效期至2026年。'})
        assert cp.returncode == 0, cp.stderr
        assert matrix(book)[0][11:13] == ('待确认', '待确认')
        assert len(list(book['附件核对'].values)) == 3
        assert '关联' in str(list(book['待确认事项'].values))
