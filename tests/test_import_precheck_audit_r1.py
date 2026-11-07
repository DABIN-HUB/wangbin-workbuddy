"""Audit R1: actual CSV/XLSX inputs and reopened business outputs."""
import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-import-precheck/scripts/precheck.py'
spec = importlib.util.spec_from_file_location('audit_import', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture(tmp_path, header, rows, xlsx=False):
    path = tmp_path / ('input.xlsx' if xlsx else 'input.csv')
    if xlsx:
        wb = Workbook()
        for row in [header, *rows]:
            wb.active.append(row)
        wb.save(path)
    else:
        with path.open('w', encoding='utf-8', newline='') as stream:
            csv.writer(stream).writerows([header, *rows])
    out = tmp_path / 'out'
    out.mkdir()
    return path, out


def cells(result, key, sheet=None):
    wb = load_workbook(result['outputs'][key], data_only=False)
    try:
        ws = wb[sheet] if sheet else wb.active
        return list(ws.values)
    finally:
        wb.close()


@pytest.mark.parametrize('xlsx', [False, True])
def test_mapped_order_leading_zero_and_unmapped(tmp_path, xlsx):
    src, out = fixture(tmp_path, ['名称', '备注', '编码'], [['甲客户', 'discard', '00000000000000000123']], xlsx)
    rules = {'fields': {'customer_code': {'sources': ['编码'], 'required': True, 'data_type': 'text'},
                        'customer_name': {'sources': ['名称'], 'required': True}}}
    result = mod.analyze(src, out, rules, split=True, authorization='confirmed split')
    assert result['status'] == 'COMPLETED'
    assert result['candidate_records'] == 1 and result['quarantine_records'] == 0
    assert cells(result, 'candidate') == [('customer_code', 'customer_name'), ('00000000000000000123', '甲客户')]
    assert 'confirmed rules insertion order' in str(cells(result, 'report', '检查概览'))


def test_template_order(tmp_path):
    src, out = fixture(tmp_path, ['customer_name', 'extra', 'customer_code'], [['乙客户', 'exclude', '00008']])
    template = tmp_path / 'template.csv'
    template.write_text('customer_code,customer_name\n', encoding='utf-8')
    result = mod.analyze(src, out, mod.rules_from_template(template), split=True, authorization='split')
    assert result['status'] == 'PARTIAL'
    assert cells(result, 'candidate') == [('customer_code', 'customer_name'), ('00008', '乙客户')]
    assert 'template' in str(cells(result, 'report', '检查概览'))


@pytest.mark.parametrize('action,raw,expected,findings,qualified', [
    ('strip', '   ', None, ['MISSING_REQUIRED_FIELD'], 0),
    ('lower', 'Z09', 'z09', ['INVALID_VALUE', 'NOT_IN_REFERENCE'], 0),
    ('upper', 'z09', 'Z09', [], 1),
])
def test_full_final_recheck(tmp_path, action, raw, expected, findings, qualified):
    src, out = fixture(tmp_path, ['地区'], [[raw]])
    ref = tmp_path / 'ref.csv'
    ref.write_text('region\nZ09\n', encoding='utf-8')
    rules = {'fields': {'region': {'sources': ['地区'], 'required': True, 'allowed_values': ['Z09'],
                                   'reference_key': 'region'}}}
    result = mod.analyze(src, out, rules, ref, split=True, authorization='transform and split',
                         transformations={'region': action})
    assert [item['category'] for item in result['finding_details']] == findings
    assert (result['candidate_records'], result['quarantine_records']) == (qualified, 1-qualified)
    workbook = cells(result, 'candidate' if qualified else 'quarantine')
    assert workbook[1][0 if qualified else 2] == expected
    assert cells(result, 'report', '变更记录')[1][2:5] == (raw, expected, action)


def test_length_after_strip_and_unique_after_upper(tmp_path):
    src, out = fixture(tmp_path, ['code'], [[' ab ']])
    rules = {'fields': {'code': {'required': True, 'min_length': 3}}}
    result = mod.analyze(src, out, rules, split=True, authorization='strip and split', transformations={'code': 'strip'})
    assert (result['candidate_records'], result['quarantine_records']) == (0, 1)
    assert [f['category'] for f in result['finding_details']] == ['LENGTH_VIOLATION']
    src.write_text('code\nabc\nABC\n', encoding='utf-8')
    rules['fields']['code']['unique_group'] = 'key'
    result = mod.analyze(src, out, rules, split=True, authorization='upper and split', transformations={'code': 'upper'})
    assert (result['candidate_records'], result['quarantine_records'], result['duplicate_groups']) == (0, 2, 1)
    assert [f['category'] for f in result['finding_details']] == ['DUPLICATE_KEY', 'DUPLICATE_KEY']
    assert {row[0] for row in cells(result, 'quarantine')[1:]} == {row['row_id'] for row in result['rows']}


def test_reference_missing_ambiguous_and_mixed(tmp_path):
    src, out = fixture(tmp_path, ['地区', '名称'], [['R01', 'a'], ['R01', '']])
    rules = {'fields': {'region': {'sources': ['地区'], 'reference_key': 'region'},
                        'name': {'sources': ['名称'], 'required': True}}}
    partial = mod.analyze(src, out, rules, split=True, authorization='split')
    assert (partial['status'], partial['candidate_records'], partial['quarantine_records']) == ('PARTIAL', 0, 2)
    assert [row[-2] for row in cells(partial, 'quarantine')[1:]] == ['PENDING_VERIFICATION', 'VIOLATION+PENDING_VERIFICATION']
    assert not any(f['category'] == 'NOT_IN_REFERENCE' for f in partial['finding_details'])
    ref = tmp_path / 'reference.csv'
    ref.write_text('region,label\nR01,first\nR01,second\n', encoding='utf-8')
    ambiguous = mod.analyze(src, out, rules, ref, split=True, authorization='split')
    assert (ambiguous['candidate_records'], ambiguous['quarantine_records']) == (0, 2)
    assert 'REFERENCE_AMBIGUITY' in [f['category'] for f in ambiguous['finding_details']]
    ref.write_text('region\nR01\n', encoding='utf-8')
    verified = mod.analyze(src, out, rules, ref, split=True, authorization='split')
    assert (verified['candidate_records'], verified['quarantine_records']) == (1, 1)
    assert cells(verified, 'candidate')[1] == ('R01', 'a')
    assert Path(partial['outputs']['report']).exists()


def test_unresolved_mapping_no_candidate_and_full_copy_audit(tmp_path):
    src, out = fixture(tmp_path, ['客户名称', '名称'], [['甲', '乙']])
    rules = {'fields': {'name': {'sources': ['客户名称', '名称'], 'required': True}}}
    rules_file = tmp_path / 'rules.json'
    rules_file.write_text(json.dumps(rules, ensure_ascii=False), encoding='utf-8')
    run = subprocess.run([sys.executable, str(SCRIPT), '--input', str(src), '--output-dir', str(out),
                          '--rules', str(rules_file), '--split', '--authorization', 'split'],
                         capture_output=True, text=True)
    assert run.returncode == 0 and json.loads(run.stdout)['status'] == 'NEEDS_INPUT'
    assert not list(out.iterdir())
    rules['fields']['name']['sources'] = ['名称']
    rules['fields']['name']['reference_key'] = 'region'
    copy = mod.analyze(src, out, rules, candidate=True, authorization='full copy only')
    assert copy['candidate_records'] == 1 and copy['pending_records'] == 1
    assert cells(copy, 'candidate') == [('name',), ('乙',)]
    assert cells(copy, 'candidate', '资格追踪_不可直接导入')[1][2] == 'PENDING_VERIFICATION'
