"""R1 Q05 developer regressions using real fictional OOXML inputs and reopened output."""
import json
from decimal import Decimal
from docx import Document
from openpyxl import Workbook, load_workbook
import pytest
from test_report_consistency_check import checker, matrix


def run(tmp_path, headers, values, paragraphs=(), table=None, context=None, percent=False):
    inputs = tmp_path / 'input'
    inputs.mkdir(parents=True)
    out = tmp_path / 'out'
    out.mkdir()
    wb = Workbook()
    ws = wb.active
    ws.title = '数据'
    for index, (header, value) in enumerate(zip(headers, values), 1):
        ws.cell(1, index, header)
        cell = ws.cell(2, index, value)
        if percent and '完成率' in header:
            cell.number_format = '0%'
    source = inputs / 'source.xlsx'
    wb.save(source)
    doc = Document()
    for paragraph in paragraphs:
        doc.add_paragraph(paragraph)
    if table:
        tab = doc.add_table(rows=0, cols=len(table[0]))
        for values_row in table:
            row = tab.add_row()
            for cell, value in zip(row.cells, values_row):
                cell.text = value
    report = inputs / 'report.docx'
    doc.save(report)
    if context is not None:
        (inputs / 'context.json').write_text(json.dumps(context, ensure_ascii=False), encoding='utf-8')
    hashes = checker.digest(source), checker.digest(report)
    args = ['--input-root', str(inputs), '--source-xlsx', str(source), '--report-docx', str(report), '--output-dir', str(out)]
    if context is not None:
        args += ['--context', str(inputs / 'context.json')]
    assert checker.main(args) == 0
    assert hashes == (checker.digest(source), checker.digest(report))
    result = load_workbook(out / 'report-数字一致性检查.xlsx')
    assert result.sheetnames == list(checker.SHEETS)
    snapshot = json.loads((out / 'report-数字一致性检查.json').read_text(encoding='utf-8'))
    return snapshot['results'], result


@pytest.mark.parametrize('raw,headers,percent,expected,relative', [
    ((.1, .12), ('上期完成率', '本期完成率'), True, 'MATCH', '20.0%'),
    ((10, 12), ('上期完成率(%)', '本期完成率(%)'), False, 'MATCH', '20.0%'),
    ((0, 12), ('上期完成率(%)', '本期完成率(%)'), False, 'MATCH', '相对增幅未计算'),
    ((.1, .12), ('上期完成率', '本期完成率'), False, 'PENDING_CONFIRMATION', None),
    ((.12, .10), ('上期完成率', '本期完成率'), True, 'MISMATCH', '下降'),
])
def test_rate_units_and_direction(tmp_path, raw, headers, percent, expected, relative):
    report = '完成率由12%提高至10%' if expected == 'MISMATCH' else f'完成率由{0 if raw[0] == 0 else 10}%提高至12%'
    results, wb = run(tmp_path, headers, raw, [report], percent=percent)
    assert len(results) == 1
    row = results[0]
    assert row['status'] == expected
    assert row['candidates'] == ['数据!A2', '数据!B2']
    if expected == 'PENDING_CONFIRMATION':
        assert row['delta'] is None and matrix(wb, '待确认口径')[1][6] == expected
    else:
        assert relative in row['explanation']
        assert Decimal(row['source_value']) == Decimal('12' if raw[0] == 0 else '-2' if expected == 'MISMATCH' else '2')


def test_formula_rate_never_verified(tmp_path):
    results, wb = run(tmp_path, ['上期完成率(%)','本期完成率(%)'], ['=1/10','=12/100'], ['完成率由10%提高至12%'], percent=True)
    result = results[0]
    assert result['status'] == 'UNVERIFIED_FORMULA_CACHE'
    assert '=1/10' in result['formula'] and '=12/100' in result['formula']
    assert result['delta'] is None and result['source_value'] is None
    assert result['provenance'] != 'DIRECT_CELLS'
    assert matrix(wb, '待确认口径')[1][6] == 'UNVERIFIED_FORMULA_CACHE'


def test_independent_rule_does_not_validate_workbook_formula(tmp_path):
    headers = ['基数','收入/CNY/元']
    values = [50,'=A2*2']
    first, _ = run(tmp_path / 'initial', headers, values, ['收入100元'])
    assert first[0]['status'] == 'UNVERIFIED_FORMULA_CACHE'
    result, _ = run(tmp_path / 'confirmed', headers, values, ['收入100元'],
                    context={'rules':{'收入':{'op':'multiply','cells':['数据!A2'], 'constants':['2'], 'unit':'元'}}})
    assert result[0]['status'] == 'MATCH' and result[0]['provenance'] == 'INDEPENDENT_RULE_RESULT'
    assert '=A2*2' in result[0]['formula'] and 'freshness=UNKNOWN' in result[0]['formula']


@pytest.mark.parametrize('value,expected', [('128万元','MATCH'), ('0元','MISMATCH'), ('','MISSING_OPERAND')])
def test_table_label_value_cells(tmp_path, value, expected):
    results, wb = run(tmp_path, ['收入/CNY/元'], [1280000], table=[['指标','数值'],['收入',value]], context={'exact':True})
    assert len(results) == 1
    result = results[0]
    assert result['status'] == expected
    assert '表格1!R2C1' in result['where'] and '表格1!R2C2' in result['where']
    if not value:
        assert result['delta'] is None and matrix(wb, '待确认口径')[1][6] == expected


def test_table_zero_positive_and_multiple_columns(tmp_path):
    results, _ = run(tmp_path / 'zero', ['收入/CNY/元'], [0], table=[['指标','数值'],['收入','0元']])
    assert results[0]['status'] == 'MATCH' and results[0]['delta'] == '0'
    results, _ = run(tmp_path / 'periods', ['本月收入/CNY/元','累计收入/CNY/元'], [1280000,3000000],
                     table=[['指标','本月(万元)','累计(万元)'],['收入','128','300']])
    assert [r['status'] for r in results] == ['MATCH','MATCH']
    assert results[0]['identity']['period'] != results[1]['identity']['period']


def test_dynamic_profit_and_mixed_branches(tmp_path):
    results, wb = run(tmp_path / 'profit', ['青禾公司6月实际未税净利润/CNY/元'], [1280000],
                      ['青禾公司6月实际未税净利润为128万元'], context={'mappings': {'净利润':'数据!A2'}})
    assert results[0]['status'] == 'MATCH' and results[0]['metric'] == '净利润'
    results, wb = run(tmp_path / 'mixed', ['青禾公司6月实际未税收入/CNY/元', '青禾公司6月实际未税成本/CNY/元',
                                         '上期完成率(%)', '本期完成率(%)'], [1280000,500000,10,12],
                      ['青禾公司6月实际未税收入128万元', '青禾公司6月实际未税成本50万元', '完成率由10%提高至12%'])
    assert [r['status'] for r in results] == ['MATCH'] * 3
    assert [r['metric'] for r in results] == ['收入','成本','完成率变化']
    assert len(matrix(wb, '指标对应')) == 4


def test_no_metrics_is_not_approval(tmp_path):
    results, wb = run(tmp_path, ['收入/元'], [100], ['第3.2节 2026-06'])
    assert results == []
    assert any('本次未形成可核查指标' in str(row) for row in matrix(wb, '核查概览'))


def test_unknown_derived_metric_is_pending_not_invented(tmp_path):
    results, wb = run(tmp_path, ['收入/元','成本/元'], [100,70], ['毛利30元'])
    assert len(results) == 1 and results[0]['status'] == 'PENDING_CONFIRMATION'
    assert results[0]['metric'] == '毛利' and results[0]['delta'] is None
    assert matrix(wb, '待确认口径')[1][6] == 'PENDING_CONFIRMATION'
