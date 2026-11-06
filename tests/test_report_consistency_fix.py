"""Developer regressions for the 0.1.2 QA findings; old tests remain untouched."""
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from docx import Document
from openpyxl import Workbook
from test_report_consistency_check import checker, exercise, matrix


@pytest.mark.parametrize('headers,expected', [
    (['收入/CNY/元', '收入/USD/元'], 'NOT_COMPARABLE'),
    (['收入/USD/元', '收入/CNY/元'], 'NOT_COMPARABLE'),
    (['青禾6月实际未税收入/CNY/元', '云杉6月实际未税收入/CNY/元'], 'NOT_COMPARABLE'),
    (['青禾6月实际未税收入/CNY/元', '青禾7月实际未税收入/CNY/元'], 'NOT_COMPARABLE'),
    (['青禾6月实际未税收入/CNY/元', '青禾6月预算未税收入/CNY/元'], 'NOT_COMPARABLE'),
    (['青禾6月实际未税收入/CNY/元', '青禾6月实际含税收入/CNY/元'], 'NOT_COMPARABLE'),
    (['收入/CNY/元', '收入/元'], 'PENDING_CONFIRMATION'),
    (['收入/CNY/元', '收入/%'], 'NOT_COMPARABLE'),
])
def test_all_sum_operands_checked(tmp_path, headers, expected):
    wb, _ = exercise(tmp_path, headers, [100, 100], ['收入200元人民币'],
                     {'rules': {'收入': {'op': 'sum', 'cells': ['数据!A2', '数据!B2'], 'unit': '元'}}, 'exact': True})
    pending = matrix(wb, '待确认口径')[1]
    assert pending[6] == expected and pending[7] is None
    assert len(matrix(wb, '差异明细')) == 1


def test_compatible_unit_scale_still_sums(tmp_path):
    wb, _ = exercise(tmp_path, ['收入/CNY/万元', '收入/CNY/元'], [1, 100], ['收入10100元人民币'],
                     {'rules': {'收入': {'op': 'sum', 'cells': ['数据!A2', '数据!B2'], 'unit': '元'}}, 'exact': True})
    assert matrix(wb, '差异明细')[1][19] == 'MATCH'


@pytest.mark.parametrize('payload,expected', [
    (b'not xlsx', 'UNSUPPORTED_OR_SPOOFED'),
    (b'PK\x03\x04corrupt ZIP container', 'UNREADABLE_OR_ENCRYPTED'),
])
def test_spoof_versus_damaged_ooxml(tmp_path, capsys, payload, expected):
    inputs = tmp_path / 'in'
    inputs.mkdir()
    out = tmp_path / 'out'
    out.mkdir()
    (inputs / 'source.xlsx').write_bytes(payload)
    Document().save(inputs / 'report.docx')
    assert checker.main(['--input-root', str(inputs), '--source-xlsx', str(inputs / 'source.xlsx'),
                         '--report-docx', str(inputs / 'report.docx'), '--output-dir', str(out)]) == 2
    assert json.loads(capsys.readouterr().err)['error'] == expected
    assert not list(out.iterdir())


def test_valid_zip_without_ooxml_is_spoof(tmp_path, capsys):
    inputs = tmp_path / 'in'
    inputs.mkdir()
    out = tmp_path / 'out'
    out.mkdir()
    with zipfile.ZipFile(inputs / 'source.xlsx', 'w') as z:
        z.writestr('unrelated.txt', 'hello')
    Document().save(inputs / 'report.docx')
    assert checker.main(['--input-root', str(inputs), '--source-xlsx', str(inputs / 'source.xlsx'),
                         '--report-docx', str(inputs / 'report.docx'), '--output-dir', str(out)]) == 2
    assert json.loads(capsys.readouterr().err)['error'] == 'UNSUPPORTED_OR_SPOOFED'


def test_packaged_qa_failures(tmp_path):
    candidate = os.environ.get('REPORT_CANDIDATE_ZIP')
    if not candidate:
        pytest.skip('set REPORT_CANDIDATE_ZIP after immutable factory package')
    with zipfile.ZipFile(candidate) as z:
        z.extractall(tmp_path / 'extracted')
    script = tmp_path / 'extracted/wangbin-report-consistency-check/scripts/check_report.py'
    inputs = tmp_path / 'in'
    inputs.mkdir()
    doc = Document()
    doc.add_paragraph('收入200元人民币')
    doc.save(inputs / 'report.docx')
    (inputs / 'context.json').write_text(json.dumps({'exact': True, 'rules': {'收入': {
        'op': 'sum', 'cells': ['数据!A2', '数据!B2'], 'unit': '元'}}}), encoding='utf-8')
    for i, headers in enumerate((['收入/CNY/元', '收入/USD/元'], ['收入/USD/元', '收入/CNY/元'])):
        wb = Workbook()
        ws = wb.active
        ws.title = '数据'
        for j, header in enumerate(headers, 1):
            ws.cell(1, j, header)
            ws.cell(2, j, 100)
        wb.save(inputs / 'source.xlsx')
        output = tmp_path / f'out{i}'
        output.mkdir()
        args = [sys.executable, str(script), '--input-root', str(inputs), '--source-xlsx',
                str(inputs / 'source.xlsx'), '--report-docx', str(inputs / 'report.docx'),
                '--output-dir', str(output), '--context', str(inputs / 'context.json')]
        result = subprocess.run(args, capture_output=True, text=True, timeout=45)
        assert result.returncode == 0, result.stderr
        from openpyxl import load_workbook
        rendered = load_workbook(output / 'report-数字一致性检查.xlsx')
        assert rendered.sheetnames == list(checker.SHEETS)
        assert matrix(rendered, '待确认口径')[1][6] == 'NOT_COMPARABLE'
        assert len(matrix(rendered, '差异明细')) == 1
        assert matrix(rendered, '待确认口径')[1][7] is None
    (inputs / 'source.xlsx').write_bytes(b'not xlsx')
    spoof = subprocess.run(args, capture_output=True, text=True, timeout=45)
    assert spoof.returncode == 2
    assert json.loads(spoof.stderr)['error'] == 'UNSUPPORTED_OR_SPOOFED'
