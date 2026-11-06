"""Product-only synthetic raw file tests; no solar regression."""
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-import-precheck/scripts/precheck.py'
spec = importlib.util.spec_from_file_location('import_precheck', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

RULES = {'fields': {
    'customer_code': {'sources':['customer_code'], 'rule_id':'CODE', 'required':True, 'data_type':'text', 'unique_group':'code'},
    'customer_name': {'sources':['customer_name'], 'rule_id':'NAME', 'required':True},
    'region': {'sources':['region'], 'rule_id':'REGION', 'reference_key':'region'},
}}

def sample(tmp_path, xlsx=False):
    rows = [['customer_code','customer_name','region'],['00123','甲客户','R01'], ['00123','乙客户','R99'],['123','丙客户','R02'],['00007','','R01']]
    path = tmp_path / ('source.xlsx' if xlsx else 'source.csv')
    if xlsx:
        wb = Workbook()
        for row in rows:
            wb.active.append(row)
        wb.save(path)
    else:
        with path.open('w',encoding='utf-8',newline='') as out:
            csv.writer(out).writerows(rows)
    ref = tmp_path / 'region.csv'
    with ref.open('w',encoding='utf-8',newline='') as out:
        csv.writer(out).writerows([['region'],['R01'],['R02']])
    output = tmp_path / 'output'
    output.mkdir()
    return path,ref,output

@pytest.mark.parametrize('xlsx',[False,True])
def test_core_real_raw_files(tmp_path,xlsx):
    source,ref,out = sample(tmp_path,xlsx)
    initial = hashlib.sha256(source.read_bytes()).hexdigest()
    result = module.analyze(source,out,RULES,ref)
    assert (result['input_records'],result['findings'],result['affected_records'],result['duplicate_groups']) == (4,4,3,1)
    assert [r['category'] for r in result['finding_details']].count('DUPLICATE_KEY') == 2
    assert [r['value'] for r in result['finding_details'] if r['category']=='DUPLICATE_KEY'] == ['00123','00123']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == initial
    wb = load_workbook(result['outputs']['report'])
    assert wb.sheetnames == list(module.HEADINGS)
    assert wb['问题明细'].max_row == 5
    assert wb['变更记录'].max_row == 1
    assert wb['检查概览']['A1'].value == '项目'
    assert wb['问题明细'].auto_filter.ref
    assert all(wb['问题明细'].cell(i,8).data_type != 'f' for i in range(2,6))

@pytest.mark.parametrize('xlsx',[False,True])
def test_split_and_reference_rerun(tmp_path,xlsx):
    src,ref,out = sample(tmp_path,xlsx)
    old = module.analyze(src,out,RULES,ref,split=True,authorization='user asks passing subset')
    accepted = load_workbook(old['outputs']['candidate']).active
    isolated = load_workbook(old['outputs']['quarantine']).active
    assert accepted.max_row == 2 and isolated.max_row == 4
    assert accepted['C2'].value == '123'
    assert {accepted['A2'].value}.isdisjoint({isolated.cell(i,1).value for i in range(2,5)})
    assert Path(old['outputs']['report']).exists()
    with ref.open('a',encoding='utf-8') as stream:
        stream.write('R99\n')
    new = module.analyze(src,out,RULES,ref)
    assert new['findings'] == 3 and new['duplicate_groups'] == 1
    assert old['outputs']['report'] != new['outputs']['report']
    assert load_workbook(old['outputs']['report'])['问题明细'].max_row == 5

@pytest.mark.parametrize('prefix',['=1+1','+SUM(1,2)','-1+2','@SUM(1,2)'])
def test_injection_as_text(tmp_path,prefix):
    src,ref,out = sample(tmp_path)
    with src.open('a',encoding='utf-8') as stream:
        csv.writer(stream).writerow(['SAFE',prefix,'R01'])
    result = module.analyze(src,out,RULES,ref,candidate=True,authorization='candidate for all rows')
    ws = load_workbook(result['outputs']['candidate']).active
    cell = ws.cell(6,4)
    assert cell.value == prefix and cell.data_type == 's'

def test_missing_ref_and_mapping(tmp_path):
    src,ref,out=sample(tmp_path)
    result=module.analyze(src,out,RULES)
    assert result['findings']==3 and any('reference' in r[1] for r in result['unchecked'])
    partial=module.analyze(src,out)
    assert partial['status']=='PARTIAL' and partial['findings']==0
    conflict={'fields': {'name': {'sources':['customer_name','region'],'required':True}}}
    result=module.analyze(src,out,conflict)
    assert result['status']=='PARTIAL' and len(result['unchecked'])>0

def test_composite_and_zero(tmp_path):
    src,ref,out=sample(tmp_path)
    src.write_text('country,code\n,A\n,A\n0,B\nNULL,C\n',encoding='utf-8')
    rules={'fields':{'country':{'required':True,'unique_group':'pair'},'code':{'unique_group':'pair'}}}
    result=module.analyze(src,out,rules)
    assert result['duplicate_groups']==0 and result['findings']==2
    assert len([u for u in result['unchecked'] if 'comparison key' in u[1]])==2

def test_date_precision_multisheet_and_fake(tmp_path):
    src,ref,out=sample(tmp_path,True)
    wb=load_workbook(src)
    wb.active['A2']=123
    wb.active['A2'].number_format='00000'
    wb.active['A3']=12345678901234567890
    wb.active['D1']='day'
    wb.active['D2']='03/04/2026'
    wb.create_sheet('backup')
    wb.save(src)
    with pytest.raises(module.InputError,match='SHEET_SELECTION_REQUIRED'):
        module.analyze(src,out,RULES)
    rules={'fields':{'customer_code':{'data_type':'text'},'day':{'data_type':'date'}}}
    result=module.analyze(src,out,rules,sheet='Sheet')
    assert 'TEXT_ENCODING_RISK' in {f['category'] for f in result['finding_details']}
    assert 'PRECISION_RISK' in {f['category'] for f in result['finding_details']}
    assert any('date format ambiguous' in u[1] for u in result['unchecked'])
    src.write_bytes(b'not xlsx')
    with pytest.raises(module.InputError,match='FAKE_OR_CORRUPT'):
        module.analyze(src,out,rules)

def test_reference_ambiguity_and_repeat(tmp_path):
    src,ref,out=sample(tmp_path)
    with ref.open('a',encoding='utf-8') as stream:
        stream.write('R01\n')
    first=module.analyze(src,out,RULES,ref)
    second=module.analyze(src,out,RULES,ref)
    assert [f['category'] for f in first['finding_details']] == [f['category'] for f in second['finding_details']]
    assert first['findings']==second['findings']
    assert 'REFERENCE_AMBIGUITY' in [f['category'] for f in first['finding_details']]
    assert first['outputs']['report']!=second['outputs']['report']

def test_authorization_and_cli(tmp_path):
    src,ref,out=sample(tmp_path)
    with pytest.raises(module.InputError,match='AUTHORIZATION_REQUIRED'):
        module.analyze(src,out,RULES,ref,split=True)
    rules=tmp_path/'rules.json'
    rules.write_text(json.dumps(RULES),encoding='utf-8')
    run=subprocess.run([sys.executable,str(SCRIPT),'--input',str(src),'--output-dir',str(out),'--rules',str(rules),'--reference',str(ref)],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    assert json.loads(run.stdout)['findings']==4

def test_raw_template_and_multiline_source(tmp_path):
    src,ref,out=sample(tmp_path)
    template=tmp_path/'target.csv'
    template.write_text('customer_code,customer_name,region\n',encoding='utf-8')
    with src.open('a',encoding='utf-8',newline='') as stream:
        csv.writer(stream).writerow(['00999','line 1\nline 2','R01'])
    with src.open('a',encoding='utf-8',newline='') as stream:
        csv.writer(stream).writerow(['01000','next','R01'])
    meta,records=module.read_table(src)
    assert records[-2]['line']==6 and records[-1]['line']==8
    run=subprocess.run([sys.executable,str(SCRIPT),'--input',str(src),'--output-dir',str(out),'--template',str(template)],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    receipt=json.loads(run.stdout)
    assert receipt['input_records']==6 and receipt['status']=='PARTIAL'
    assert any('required unknown' in item[1] for item in receipt['unchecked'])

def test_confirmed_transform_is_audited(tmp_path):
    src,ref,out=sample(tmp_path)
    rules={'fields':{'customer_name':{'sources':['customer_name'],'required':True}}}
    with src.open('a',encoding='utf-8',newline='') as stream:
        csv.writer(stream).writerow(['xyz','  FOO  ','R01'])
    receipt=module.analyze(src,out,rules,candidate=True,authorization='user asks strip name for current run',transformations={'customer_name':'strip'})
    changes=load_workbook(receipt['outputs']['report'])['变更记录']
    assert changes.max_row==2 and changes['D2'].value=='FOO' and changes['F2'].value
    candidate=load_workbook(receipt['outputs']['candidate']).active
    assert candidate.cell(candidate.max_row,4).value=='FOO'
