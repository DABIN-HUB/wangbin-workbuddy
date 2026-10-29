"""D3 adversarial local synthetic boundaries; no legacy file is edited."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import hashlib
import os
from pathlib import Path
import subprocess
import time

import pytest
from test_timeseries_bundle import api, atom, base, catalog, header, rows, write
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import dumps, loads


def read(path, catalog, budget=None):
    return api().read_bundle(path,catalog=catalog,budget=budget or api().BundleBudget())


def manifest_save(path, value):
    (path/'manifest.json').write_bytes(dumps(value).encode())


def test_negative_decimal_price_requires_contract_rule(tmp_path,catalog):
    fid = 'tariff.market_series'
    data = list(rows(catalog,fid=fid))
    data[0]['fields'][fid+'.sale_price']['value'] = Decimal('-0.50')
    with pytest.raises(ContractError,match='BUNDLE_NEGATIVE_PRICE_RULE'):
        write(tmp_path,catalog,datasets={fid:{'header':header(catalog,fid),'rows':data}})
    assert not (tmp_path/'bundle').exists()


def test_valid_negative_price_retains_original_with_explicit_rule(tmp_path,catalog):
    from wangbin_solar_pv.intake import IntakeSession
    fid = 'tariff.market_series'
    s = IntakeSession.from_dict(base(catalog)['project'],catalog)
    for key,value in [('tariff.negative_price_rule','SYNTHETIC signed settlement rule'),('tariff.contract_id','SYNTHETIC contract')]:
        s.project.values[key] = atom(catalog,key,value)
    data = list(rows(catalog,fid=fid))
    data[0]['fields'][fid+'.sale_price'] = atom(catalog,fid+'.sale_price',Decimal('-0.50'),fid+':r0:sale_price')
    path,_=write(tmp_path,catalog,base_export=s.export(),datasets={fid:{'header':header(catalog,fid),'rows':data}})
    with read(path,catalog) as b:
        assert list(b.rows(fid)) == data


def test_iteration_rechecks_changed_base_file(tmp_path,catalog):
    path,_=write(tmp_path,catalog)
    with read(path,catalog) as bundle:
        with (path/'base.json').open('ab') as f:
            f.write(b' ')
        with pytest.raises(ContractError,match='BUNDLE_FILE_HASH'):
            list(bundle.rows('load.series'))


@pytest.mark.parametrize('change',[
    'missing_source','bad_source_kind','unit','negative_energy','numeric_string','boolean',
    'row_id','duplicate_row','duplicate_instance','duplicate_time','gap','order',
    'offset','no_timezone','interval','missing_timestamp','power_energy','extra_atom',
    'wrong_key','bad_original_conversion','verified_without_evidence','header_fake_value',
    'header_verified','header_zone','period_end','period_start','empty','unknown_time',
],ids=str)
def test_strict_atom_sequence_rejection(tmp_path,catalog,change):
    data=list(rows(catalog)); h=header(catalog); f=data[1]['fields']; e=f['load.series.energy']
    if change=='missing_source': e['source_id']=None
    elif change=='bad_source_kind': e['provenance_kind']='AI'
    elif change=='unit': e['unit']='MWh'
    elif change=='negative_energy': e['value']=-1
    elif change=='numeric_string': e['value']='1.0'
    elif change=='boolean': e['value']=True
    elif change=='row_id': data[1]['row_id']='wrong'
    elif change=='duplicate_row': data[1]['row_id']='r0'; f['load.series.row_id']['value']='r0'
    elif change=='duplicate_instance': e['field_instance_id']=data[0]['fields']['load.series.energy']['field_instance_id']
    elif change=='duplicate_time': f['load.series.timestamp']['value']='2025-01-01T00:00:00+08:00'
    elif change=='gap': f['load.series.timestamp']['value']='2025-01-01T03:00:00+08:00'
    elif change=='order': data.reverse()
    elif change=='offset': f['load.series.timestamp']['value']='2024-12-31T17:00:00Z'
    elif change=='no_timezone': f['load.series.timestamp']['value']='2025-01-01T01:00:00'
    elif change=='interval': f['load.series.interval_minutes']['value']=30
    elif change=='missing_timestamp': del f['load.series.timestamp']
    elif change=='power_energy': e['value']=10
    elif change=='extra_atom': f['site.total_area']=atom(catalog,'site.total_area',1)
    elif change=='wrong_key': e['field_id']='load.series.power'
    elif change=='bad_original_conversion': e.update(original_unit='MWh',normalization=None)
    elif change=='verified_without_evidence': e['status']='VERIFIED'
    elif change=='header_fake_value': h['value']=[]
    elif change=='header_verified': h['status']='VERIFIED'
    elif change=='header_zone': h['measurement_period']['timezone']='UTC'
    elif change=='period_end': h['measurement_period']['end']='2025-01-01T04:00:00+08:00'
    elif change=='period_start': h['measurement_period']['start']='2024-12-31T23:00:00+08:00'
    elif change=='empty': data=[]
    elif change=='unknown_time': f['load.series.timestamp'].update(status='UNKNOWN',value=None)
    with pytest.raises(ContractError) as err:
        write(tmp_path,catalog,datasets={'load.series':{'header':h,'rows':data}})
    assert err.value.field_id is None
    assert str(err.value).startswith('BUNDLE_')
    assert not (tmp_path/'bundle').exists()


@pytest.mark.parametrize('property', ['input_hash','source_snapshot_id','normalized_inputs','provenance_records','extra','schema_version','project'])
def test_entire_phase2_export_revalidated(tmp_path,catalog,property):
    b=base(catalog)
    if property=='extra': b['SYNTHETIC_SECRET']='SYNTHETIC_SECRET'
    elif property=='project': b['project']['values']['site.timezone']['source_id']=None
    else: b[property]='SYNTHETIC_SECRET'
    with pytest.raises(ContractError) as e:
        write(tmp_path,catalog,base_export=b)
    assert 'SYNTHETIC_SECRET' not in str(e.value)
    assert not (tmp_path/'bundle').exists()


def test_never_replace_existing_base_dataset_even_empty(tmp_path,catalog):
    from wangbin_solar_pv.intake import IntakeSession
    s=IntakeSession.from_dict(base(catalog)['project'],catalog)
    s.project.values['load.series']=atom(catalog,'load.series',[])
    with pytest.raises(ContractError,match='BUNDLE_DATASET_ALREADY_IN_BASE'):
        write(tmp_path,catalog,base_export=s.export())


@pytest.mark.parametrize('field,low', [('max_input_bytes',1),('max_disk_bytes',1),('max_rows',2),('max_seconds',1e-12),('max_memory_bytes',1)])
def test_all_five_budgets_actually_abort_without_publish(tmp_path,catalog,field,low):
    budget=replace(api().BundleBudget(),**{field:low})
    with pytest.raises(ContractError,match='BUNDLE_'):
        write(tmp_path,catalog,budget=budget)
    assert not (tmp_path/'bundle').exists()


@pytest.mark.parametrize('field,ceiling', [('max_input_bytes',2*1024**3),('max_disk_bytes',4*1024**3),('max_rows',1000000),('max_seconds',3600),('max_memory_bytes',2*1024**3)])
@pytest.mark.parametrize('kind',['zero','negative','bool','over','infinity'])
def test_budget_hard_limits(field,ceiling,kind):
    value={'zero':0,'negative':-1,'bool':True,'over':ceiling+1,'infinity':float('inf')}[kind]
    with pytest.raises(ContractError,match='BUNDLE_BUDGET'):
        api().BundleBudget(**{field:value})


@pytest.mark.parametrize('kind',['block_bytes','base_bytes','extra','missing','traversal','absolute','duplicate','incomplete','future','array_hash','content_hash','rows','atoms','metadata','unknown_root'])
def test_manifest_and_file_tampering_rejected(tmp_path,catalog,kind):
    path,m=write(tmp_path,catalog,rows_per_chunk=1)
    ds=m['datasets']['load.series']; c=ds['chunks'][0]
    if kind=='block_bytes':
        with (path/c['file']).open('ab') as f: f.write(b' ')
    elif kind=='base_bytes':
        with (path/'base.json').open('ab') as f: f.write(b' ')
    elif kind=='extra': (path/'extra.jsonl').write_bytes(b'{}')
    elif kind=='missing': (path/c['file']).unlink()
    else:
        if kind=='traversal': c['file']='../private.jsonl'
        elif kind=='absolute': c['file']='C:/private.jsonl'
        elif kind=='duplicate': ds['chunks'].append(deepcopy(c))
        elif kind=='incomplete': m['complete']=False
        elif kind=='future': m['schema_version']='solar-pv-timeseries-bundle/9.0.0'
        elif kind=='array_hash': ds['canonical_array_hash']='0'*64; m['content_hash']=api()._content_hash(m)
        elif kind=='content_hash': m['content_hash']='0'*64
        elif kind=='rows': ds['row_count']+=1; m['content_hash']=api()._content_hash(m)
        elif kind=='atoms': ds['atom_count']+=1; m['content_hash']=api()._content_hash(m)
        elif kind=='metadata': ds['metadata']['interval_minutes']=15; m['content_hash']=api()._content_hash(m)
        elif kind=='unknown_root': m['SYNTHETIC_SECRET']='SYNTHETIC_SECRET'
        manifest_save(path,m)
    with pytest.raises(ContractError) as e: read(path,catalog)
    assert e.value.field_id is None
    assert str(tmp_path) not in str(e.value)


def test_rehashing_malformed_atom_does_not_bypass_read_validation(tmp_path,catalog):
    path,m=write(tmp_path,catalog)
    ds=m['datasets']['load.series']; c=ds['chunks'][0]
    data=list(rows(catalog)); data[1]['fields']['load.series.energy']['source_id']=None
    raw=b''.join(dumps(r).encode()+b'\n' for r in data)
    (path/c['file']).write_bytes(raw)
    c.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    ds['canonical_array_hash']=api().canonical_array_hash(data)
    m['content_hash']=api()._content_hash(m); manifest_save(path,m)
    with pytest.raises(ContractError,match='BUNDLE_ATOM_INVALID'): read(path,catalog)


def test_midstream_failure_is_sanitized_and_atomic(tmp_path,catalog):
    target=tmp_path/'bundle'
    def failing():
        for r in rows(catalog):
            assert not (target/'manifest.json').exists()
            yield r
        raise RuntimeError('SYNTHETIC_SECRET C:/private/secret')
    with pytest.raises(ContractError) as e:
        write(tmp_path,catalog,datasets={'load.series':{'header':header(catalog),'rows':failing()}},rows_per_chunk=1)
    assert str(e.value)=='BUNDLE_INVALID'
    assert not target.exists()


def test_no_clobber_exact_bytes(tmp_path,catalog):
    path,_=write(tmp_path,catalog)
    old={p.name:p.read_bytes() for p in path.iterdir()}
    with pytest.raises(ContractError,match='BUNDLE_OUTPUT_EXISTS'): write(tmp_path,catalog)
    assert {p.name:p.read_bytes() for p in path.iterdir()}==old


def test_hardlink_chunk_rejected(tmp_path,catalog):
    path,m=write(tmp_path,catalog)
    chunk=path/m['datasets']['load.series']['chunks'][0]['file']
    os.link(chunk,tmp_path/'hardlink')
    with pytest.raises(ContractError): read(path,catalog)


def test_symlink_bundle_rejected_when_privileged(tmp_path,catalog):
    path,_=write(tmp_path,catalog)
    link=tmp_path/'link'
    try: link.symlink_to(path,target_is_directory=True)
    except OSError: pytest.skip('Windows symlink privilege unavailable; junction separately exercised')
    with pytest.raises(ContractError): read(link,catalog)


@pytest.mark.skipif(os.name!='nt',reason='NTFS junction acceptance')
def test_real_ntfs_junction_rejected(tmp_path,catalog):
    path,_=write(tmp_path,catalog); link=tmp_path/'junction'
    result=subprocess.run(['cmd.exe','/c','mklink','/J',str(link),str(path)],capture_output=True)
    assert result.returncode==0
    try:
        with pytest.raises(ContractError): read(link,catalog)
    finally:
        os.rmdir(link)


def test_unknown_dataset_sanitized_and_traversal_output_rejected(tmp_path,catalog):
    with pytest.raises(ContractError):
        write(tmp_path,catalog,datasets={'SYNTHETIC_SECRET':{'header':{},'rows':[]}})
    with pytest.raises(ContractError):
        api().write_bundle(tmp_path/'..'/'bad',base_export=base(catalog),datasets={},catalog=catalog,budget=api().BundleBudget())


def test_load_declared_zone_cannot_disagree_with_site(tmp_path,catalog):
    from wangbin_solar_pv.intake import IntakeSession
    s=IntakeSession.from_dict(base(catalog)['project'],catalog)
    s.project.values['load.timezone']=atom(catalog,'load.timezone','America/New_York')
    with pytest.raises(ContractError,match='BUNDLE_SITE_TIMEZONE'):
        write(tmp_path,catalog,base_export=s.export())


def test_dst_fall_fold_is_two_different_continuous_instants(tmp_path,catalog):
    zone='America/New_York'
    stamps=['2025-11-02T00:00:00-04:00','2025-11-02T01:00:00-04:00',
            '2025-11-02T01:00:00-05:00','2025-11-02T02:00:00-05:00']
    data=list(rows(catalog,n=4))
    for r,stamp in zip(data,stamps):
        r['fields']['load.series.timestamp']=atom(catalog,'load.series.timestamp',stamp,'load.series:'+r['row_id']+':timestamp')
    h=header(catalog,n=4,start=stamps[0],zone=zone)
    h['measurement_period']['end']='2025-11-02T03:00:00-05:00'
    path,_=write(tmp_path,catalog,base_export=base(catalog,zone),datasets={'load.series':{'header':h,'rows':data}})
    with read(path,catalog) as bundle: assert list(bundle.rows('load.series'))==data


@pytest.mark.parametrize('bad_stamp',['2025-03-09T02:00:00-05:00','2025-03-09T02:00:00-04:00'])
def test_dst_nonexistent_local_time_rejected(tmp_path,catalog,bad_stamp):
    zone='America/New_York'
    data=list(rows(catalog,n=1)); data[0]['fields']['load.series.timestamp']['value']=bad_stamp
    h=header(catalog,n=1,start='2025-03-09T01:00:00-05:00',zone=zone)
    h['measurement_period']['end']='2025-03-09T03:00:00-04:00'
    with pytest.raises(ContractError,match='BUNDLE_SITE_TIMEZONE'):
        write(tmp_path,catalog,base_export=base(catalog,zone),datasets={'load.series':{'header':h,'rows':data}})


def test_leap_day_midnight_continuity(tmp_path,catalog):
    start='2024-02-28T23:00:00+08:00'
    path,_=write(tmp_path,catalog,datasets={'load.series':{'header':header(catalog,start=start),'rows':rows(catalog,start=start)}})
    with read(path,catalog) as bundle:
        assert list(bundle.rows('load.series'))[1]['fields']['load.series.timestamp']['value']=='2024-02-29T00:00:00+08:00'


def test_oversized_value_rejected_before_unbounded_encoding_allocation():
    import tracemalloc
    payload={'SYNTHETIC': 'x'*(3*1024**2)}
    tracemalloc.start()
    try:
        with pytest.raises(ContractError): api()._encode(payload,1024)
        _,peak=tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 1024**2


@pytest.mark.parametrize('module_version',['0.2.0','0.3.0'])
def test_explicit_old_and_new_module_exports_preserve_original_identity(tmp_path,catalog,module_version):
    exported=base(catalog); exported['input_module_version']=module_version
    original_hash=exported['input_hash']
    path,_=write(tmp_path,catalog,base_export=exported)
    with read(path,catalog) as bundle:
        assert bundle.base_export==exported
        assert bundle.base_export['input_hash']==original_hash
        assert bundle.base_export['input_module_version']==module_version


@pytest.mark.parametrize('module_version',['0.1.0','0.4.0','9.0.0',None])
def test_unknown_module_export_version_rejected(tmp_path,catalog,module_version):
    exported=base(catalog); exported['input_module_version']=module_version
    with pytest.raises(ContractError,match='BUNDLE_BASE_VERSION'):
        write(tmp_path,catalog,base_export=exported)


def test_complete_phase2_base_with_original_nested_array_is_not_truncated(tmp_path,catalog):
    from wangbin_solar_pv.intake import IntakeSession
    s=IntakeSession.from_dict(base(catalog)['project'],catalog)
    original=list(rows(catalog,fid='resource.timeseries'))
    s.project.values['resource.timeseries']=atom(catalog,'resource.timeseries',original)
    exported=s.export()
    path,_=write(tmp_path,catalog,base_export=exported)
    with read(path,catalog) as bundle:
        assert bundle.base_export==exported
        assert bundle.base_export['project']['values']['resource.timeseries']['value']==original
        assert len(list(bundle.rows('load.series')))==3


@pytest.mark.parametrize('kind',['conflict_without_candidates','currency_mismatch'])
def test_project_level_atom_context_is_not_bypassed(tmp_path,catalog,kind):
    from wangbin_solar_pv.intake import IntakeSession
    fid='tariff.market_series'; data=list(rows(catalog,fid=fid))
    s=IntakeSession.from_dict(base(catalog)['project'],catalog)
    s.project.values['project.currency']=atom(catalog,'project.currency','CNY')
    a=data[1]['fields'][fid+'.sale_price']
    if kind=='conflict_without_candidates': a.update(status='CONFLICT',value=None,candidate_ids=[])
    else: a['economic_basis']={'currency':'USD','price_year':2025,'tax_basis':'inclusive','price_basis':'nominal'}
    with pytest.raises(ContractError,match='BUNDLE_ATOM_CONTEXT'):
        write(tmp_path,catalog,base_export=s.export(),datasets={fid:{'header':header(catalog,fid),'rows':data}})


def test_callback_cannot_smuggle_private_values_as_bundle_error_code(tmp_path,catalog):
    def failing():
        yield from rows(catalog)
        raise ContractError('BUNDLE_SYNTHETIC_SECRET_C:/private/secret','SYNTHETIC_SECRET')
    with pytest.raises(ContractError) as e:
        write(tmp_path,catalog,datasets={'load.series':{'header':header(catalog),'rows':failing()}})
    assert str(e.value)=='BUNDLE_INVALID'
    assert e.value.field_id is None
    assert not (tmp_path/'bundle').exists()


def test_native_scientific_float_tokens_keep_legacy_array_digest(tmp_path,catalog):
    data=list(rows(catalog))
    for row in data:
        row['fields']['load.series.power']['value']=1e-5
        row['fields']['load.series.power']['original_value']=1e-5
        row['fields']['load.series.energy']['value']=1e-5
        row['fields']['load.series.energy']['original_value']=1e-5
    path,m=write(tmp_path,catalog,datasets={'load.series':{'header':header(catalog),'rows':data}})
    assert m['datasets']['load.series']['canonical_array_hash']==api().canonical_array_hash(data)
    with read(path,catalog) as bundle:
        # Exact tokens survive decoding/encoding; no float -> Decimal lexical drift.
        assert api().canonical_array_hash(bundle.rows('load.series'))==m['datasets']['load.series']['canonical_array_hash']


def test_all_three_allowed_datasets_independent_metadata(tmp_path,catalog):
    datasets={fid:{'header':header(catalog,fid),'rows':rows(catalog,fid=fid)} for fid in api().DATASET_IDS}
    path,_=write(tmp_path,catalog,datasets=datasets)
    with read(path,catalog) as bundle:
        assert len(bundle.dataset_ids)==3
        assert bundle.stats['rows_validated']==9
        assert bundle.stats['atoms_validated']==63
        for fid in bundle.dataset_ids: assert len(list(bundle.rows(fid)))==3
