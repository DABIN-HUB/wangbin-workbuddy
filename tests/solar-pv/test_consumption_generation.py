"""Whole-year public API/CLI acceptance using actual Phase 3B generation.

Fraction expectations consume ONLY the pinned 3B energy input, never Phase 3C
outputs or kernels. No alternate irradiance/generation model is constructed.
"""
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal as D
from fractions import Fraction as F
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from consumption_case_support import case,extend,axis,series_header,load_rows,session_from_export,atom,inline_series
from energy_case_support import resource_header,resource_rows,atom as generation_atom
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.serialization import loads,dumps
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.timeseries_bundle import BundleBudget,write_bundle,read_bundle
from wangbin_solar_pv.timeseries_private import Meter
from wangbin_solar_pv.calculation.energy_inputs import EnergyInputs
from wangbin_solar_pv.calculation.energy_yield import calculate_rooftop as generate_roof,calculate_ground as generate_ground
from wangbin_solar_pv.calculation.revenue import calculate_rooftop,calculate_ground
from wangbin_solar_pv.calculation.generation_evidence import GenerationEvidence
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.calculation.result_contract import validate_result

ROOT=Path(__file__).resolve().parents[2]


def independent_reference(directory,category,years):
    keys=("available_kwh","load_kwh","self_kwh","export_kwh","curtailed_kwh","delivered_kwh","self_value","export_sales_revenue","transaction_cost","gross_benefit","benefit_after_transaction_cost")
    totals=[{k:F(0) for k in keys} for _ in range(years)]
    receipt=loads((directory/'receipt.json').read_bytes())
    for chunk in receipt['chunks']:
        with (directory/chunk['file']).open('rb') as stream:
            for line in stream:
                row=loads(line);h=F(row['hours'])
                for c in row['calculations']:
                    e=F(c['state']['output_kw'])*h
                    load=F(40)*h if category=='industrial_rooftop' else None
                    used=min(e,load) if load is not None else F(0)
                    sold=min(e-used,F(20)*h);curt=e-used-sold
                    self_value=used*F(4,5);sales=sold*F(2,5);fee=sold*F(1,100)
                    values=(e,load,used,sold,curt,used+sold,self_value,sales,fee,self_value+sales,self_value+sales-fee)
                    for k,value in zip(keys,values):
                        if value is not None:
                            totals[c['operating_year']-1][k]+=value
    return totals


@pytest.fixture(scope='module',params=['industrial_rooftop','utility_scale_ground'])
def full_case(request,tmp_path_factory):
    catalog=Catalog();category=request.param
    w=tmp_path_factory.mktemp('consumption-'+category)
    budget=BundleBudget(max_seconds=1800)
    s,m=case(catalog,category,years=2)
    original=s.export()
    write_bundle(w/'resource',base_export=original,datasets={'resource.timeseries':{'header':resource_header(catalog),'rows':resource_rows(catalog)}},catalog=catalog,budget=budget)
    with read_bundle(w/'resource',catalog=catalog,budget=budget) as b:
        g=(generate_roof if category=='industrial_rooftop' else generate_ground)(original,m,catalog=catalog,output_dir=w/'generation',budget=budget,bundle=b)
    s,cm=extend(session_from_export(original,catalog),m)
    exported=s.export();a=axis()
    datasets={}
    if category=='industrial_rooftop':
        # Same resource content/header but a different base export. Comparing a
        # whole-bundle hash would incorrectly reject this valid source reuse.
        datasets={'resource.timeseries':{'header':resource_header(catalog),'rows':resource_rows(catalog)},
                  'load.series':{'header':series_header(catalog,'load.series',a),'rows':load_rows(catalog,a)}}
        write_bundle(w/'settlement',base_export=exported,datasets=datasets,catalog=catalog,budget=budget)
    calc=calculate_rooftop if category=='industrial_rooftop' else calculate_ground
    kwargs=dict(catalog=catalog,output_dir=w/'api',budget=budget,generation_dir=w/'generation',generation_result_hash=g['result_hash'])
    if datasets:
        with read_bundle(w/'settlement',catalog=catalog,budget=budget) as b:
            result=calc(exported,cm,bundle=b,**kwargs)
    else:
        result=calc(exported,cm,**kwargs)
    for name,obj in [('input.json',exported),('methods.json',cm.to_dict()),('budget.json',{'max_seconds':1800})]:
        (w/name).write_text(dumps(obj),encoding='utf-8')
    return dict(catalog=catalog,category=category,work=w,budget=budget,methods=cm,exported=exported,generation=g,
                result=result,calc=calc,has_bundle=bool(datasets))


def calculate_variant(c,output,*,methods=None,exported=None,bundle_path=None,budget=None,generation_dir=None,expected_hash=None):
    w=c['work'];kw=dict(catalog=c['catalog'],budget=budget or c['budget'],output_dir=output,
        generation_dir=generation_dir or w/'generation',generation_result_hash=expected_hash or c['generation']['result_hash'])
    selected=bundle_path or (w/'settlement' if c['has_bundle'] else None)
    if selected:
        with read_bundle(selected,catalog=c['catalog'],budget=c['budget']) as b:
            return c['calc'](exported or c['exported'],methods or c['methods'],bundle=b,**kw)
    return c['calc'](exported or c['exported'],methods or c['methods'],**kw)


def test_whole_year_and_lifecycle_match_independent_fraction_reference(full_case):
    c=full_case;r=c['result'];metrics={m['metric_id']:m for m in r['results']['metrics']}
    references=independent_reference(c['work']/'generation',c['category'],2)
    generation_metrics={m['metric_id']:m for m in c['generation']['results']['metrics']}
    for y,expected in enumerate(references,1):
        actual=metrics[f'consumption.year.{y}']['details']['ledger']
        for k,value in expected.items():
            if k=='load_kwh' and c['category']=='utility_scale_ground':
                assert actual[k] is None
            else:
                assert abs(F(actual[k])-value)<=F(1,10**9),k
        months=metrics[f'consumption.year.{y}']['details']['monthly']
        for key,value in actual.items():
            if value is not None:
                assert abs(sum(F(m[key]) for m in months)-F(value))<=F(1,10**9)
        assert abs(F(actual['available_kwh'])-F(generation_metrics[f'energy.year.{y}']['value']))<=F(1,10**9)
    for key,value in metrics['consumption']['details']['ledger'].items():
        if value is not None:
            assert abs(F(value)-sum(F(metrics[f'consumption.year.{y}']['details']['ledger'][key]) for y in (1,2)))<=F(1,10**9)
    assert metrics['npv']['status']=='NOT_IMPLEMENTED' and metrics['npv']['value'] is None
    assert r['maturity']['real_project']=='NOT_VERIFIED'
    assert r['status']=='PARTIAL'
    assert r['evidence']['consumption-intervals']['row_count']==8760
    assert r['inputs']['generation_result_hash']==c['generation']['result_hash']
    if c['category']=='industrial_rooftop':
        assert 'load.series.energy' in metrics['consumption']['input_field_ids']
    validate_result(r,c['catalog'])


def test_actual_cli_json_roundtrip_matches_api_hash_and_rejects_generation_escape(full_case):
    c=full_case;w=c['work']
    cmd=[sys.executable,'-B',str(ROOT/'services/solar-pv-engine/solar_pv.py'),'--workspace',str(w),'consumption',
        '--input','input.json','--methods','methods.json','--budget','budget.json','--generation','generation',
        '--generation-hash',c['generation']['result_hash'],'--output','cli']
    if c['has_bundle']:cmd+=['--bundle','settlement']
    p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=1800)
    assert p.returncode==0,p.stderr
    assert loads((w/'cli/result.json').read_bytes())['result_hash']==c['result']['result_hash']
    bad=cmd.copy();bad[bad.index('--generation')+1]='../outside'
    bad[bad.index('--output')+1]='escape-result'
    p=subprocess.run(bad,capture_output=True,text=True,encoding='utf-8',timeout=1800)
    assert p.returncode==2
    assert not (w/'escape-result').exists()
    assert 'outside' not in p.stderr


def test_price_recalculation_does_not_change_physical_energy_or_allocation(full_case):
    c=full_case;methods=c['methods'].to_dict();methods['parameters']['prices.escalation_fraction']['value']=D('0.1')
    result=calculate_variant(c,c['work']/'changed-price',methods=MethodConfig.from_dict(methods))
    old={m['metric_id']:m for m in c['result']['results']['metrics']};new={m['metric_id']:m for m in result['results']['metrics']}
    for y in (1,2):
        assert new[f'energy.year.{y}']['value']==old[f'energy.year.{y}']['value']
        for key in ('self_kwh','export_kwh','curtailed_kwh'):
            assert new[f'consumption.year.{y}']['details']['ledger'][key]==old[f'consumption.year.{y}']['details']['ledger'][key]
    assert abs(new['revenue.year.2']['value']-old['revenue.year.2']['value']*D('1.1'))<D('0.000000001')
    assert result['input_hash']!=c['result']['input_hash']
    assert result['result_hash']!=c['result']['result_hash']


def test_repeated_electrical_losses_or_wrong_pinned_source_are_rejected(full_case):
    c=full_case
    methods=c['methods'].to_dict();methods['parameters']['energy.upstream_included_losses']['value']=['ac_cable']
    target=c['work']/'double-loss'
    with pytest.raises(ContractError,match='GENERATION_PHYSICAL_METHOD_CHANGED'):
        calculate_variant(c,target,methods=MethodConfig.from_dict(methods))
    assert not target.exists()
    target=c['work']/'wrong-hash'
    with pytest.raises(ContractError,match='GENERATION_RESULT_HASH_MISMATCH'):
        calculate_variant(c,target,expected_hash='0'*64)
    assert not target.exists()


def test_source_chunk_corruption_and_row_budget_fail_without_publishing(full_case):
    c=full_case;w=c['work']
    shutil.copytree(w/'generation',w/'corrupt-generation')
    receipt=loads((w/'corrupt-generation/receipt.json').read_bytes());file=w/'corrupt-generation'/receipt['chunks'][0]['file']
    data=file.read_bytes();file.write_bytes(b' '+data[1:])
    target=w/'corrupt-result'
    with pytest.raises(ContractError,match='GENERATION_TRACE_FILE_HASH'):
        calculate_variant(c,target,generation_dir=w/'corrupt-generation')
    assert not target.exists()
    target=w/'row-limit'
    with pytest.raises(ContractError,match='BUNDLE_ROW_LIMIT|GENERATION_TRACE_MANIFEST'):
        calculate_variant(c,target,budget=BundleBudget(max_rows=1,max_seconds=1800))
    assert not target.exists()


def test_conflicting_new_inline_resource_is_rejected_at_real_3b_ingress(full_case):
    c=full_case;s=session_from_export(c['exported'],c['catalog']);a=axis(days=1)
    rows=[]
    for i,row in enumerate(resource_rows(c['catalog'])):
        if i==24:break
        rows.append(row)
    record=generation_atom(c['catalog'],'resource.timeseries',rows);record['measurement_period']=a.period
    s.project.values['resource.timeseries']=record
    with pytest.raises(ContractError,match='GENERATION_RESOURCE_INPUT_CONFLICT'):
        GenerationEvidence(c['work']/'generation',c['generation']['result_hash'],EnergyInputs(s.export(),c['methods'],c['catalog']),Meter(c['budget']))


def test_existing_output_is_not_removed(full_case):
    c=full_case;target=c['work']/'existing';target.mkdir();(target/'keep.txt').write_text('preserve',encoding='utf-8')
    with pytest.raises(ContractError,match='CONSUMPTION_OUTPUT_EXISTS'):
        calculate_variant(c,target)
    assert (target/'keep.txt').read_text(encoding='utf-8')=='preserve'


def test_changed_load_recalculates_rooftop_and_cannot_enter_ground_model(full_case):
    c=full_case;w=c['work']
    if c['category']=='utility_scale_ground':
        s=session_from_export(c['exported'],c['catalog']);a=axis(days=1)
        inline_series(s,'load.series',a,load_rows(c['catalog'],a))
        with pytest.raises(ContractError,match='INPUT_VALIDATION_FAILED') as rejected:
            calculate_variant(c,w/'invalid-ground-load',exported=s.export())
        assert any(i['code']=='CATEGORY_FIELD_NOT_ALLOWED' and i['field_id'].startswith('load.') for i in rejected.value.issues)
        assert not (w/'invalid-ground-load').exists()
    else:
        a=axis()
        write_bundle(w/'changed-load-input',base_export=c['exported'],datasets={'load.series':{
            'header':series_header(c['catalog'],'load.series',a),'rows':load_rows(c['catalog'],a,power=D(80))}},catalog=c['catalog'],budget=c['budget'])
        result=calculate_variant(c,w/'changed-load',bundle_path=w/'changed-load-input')
        old={m['metric_id']:m for m in c['result']['results']['metrics']};new={m['metric_id']:m for m in result['results']['metrics']}
        assert new['consumption']['value']>old['consumption']['value']
        for y in (1,2):
            assert new[f'energy.year.{y}']['value']==old[f'energy.year.{y}']['value']
            assert new[f'consumption.year.{y}']['details']['ledger']['self_kwh']>=old[f'consumption.year.{y}']['details']['ledger']['self_kwh']
        assert result['input_hash']!=c['result']['input_hash']


def test_embedded_transaction_fee_is_disclosed_but_not_deducted_twice(full_case):
    c=full_case;methods=c['methods'].to_dict()
    methods['parameters']['settlement.fee_treatment']['value']='ALREADY_IN_PRICE'
    result=calculate_variant(c,c['work']/'embedded-fee',methods=MethodConfig.from_dict(methods))
    before=next(m for m in c['result']['results']['metrics'] if m['metric_id']=='revenue')['details']['ledger']
    after=next(m for m in result['results']['metrics'] if m['metric_id']=='revenue')['details']['ledger']
    assert after['gross_benefit']==before['gross_benefit']
    assert after['transaction_cost']==0
    assert after['embedded_transaction_cost']==before['transaction_cost']
    assert after['benefit_after_transaction_cost']==after['gross_benefit']


def test_ppa_project_income_is_not_added_to_host_avoided_purchase(full_case):
    c=full_case;w=c['work']
    if c['category']=='utility_scale_ground':
        methods=c['methods'].to_dict();methods['parameters']['settlement.revenue_method']['value']='PPA_FIXED'
        with pytest.raises(ContractError,match='CONSUMPTION_GROUND_SALES_MODEL'):
            calculate_variant(c,w/'invalid-ground-ppa',methods=MethodConfig.from_dict(methods))
        assert not (w/'invalid-ground-ppa').exists()
    else:
        old=next(m for m in c['result']['results']['metrics'] if m['metric_id']=='revenue')['details']['ledger']
        for method,price in [('PPA_FIXED',F(1,2)),('PPA_DISCOUNT',F(3,5))]:
            s,m=extend(session_from_export(c['exported'],c['catalog']),c['methods'],ppa=method)
            exported=s.export();a=axis()
            write_bundle(w/(method+'-input'),base_export=exported,datasets={'load.series':{
                'header':series_header(c['catalog'],'load.series',a),'rows':load_rows(c['catalog'],a)}},catalog=c['catalog'],budget=c['budget'])
            result=calculate_variant(c,w/method,exported=exported,methods=m,bundle_path=w/(method+'-input'))
            revenue=next(x for x in result['results']['metrics'] if x['metric_id']=='revenue')
            expected=F(old['self_kwh'])*price+F(old['export_sales_revenue'])
            assert abs(F(revenue['value'])-expected)<=F(1,10**9)
            assert revenue['formula_id']=='F-PPA-REVENUE'
