"""D3 local SYNTHETIC fixtures; never verified real-site observations."""
from decimal import Decimal
import importlib
from datetime import datetime, timedelta

import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.errors import ContractError


@pytest.fixture(scope='module')
def catalog():
    return Catalog()


def atom(catalog, fid, value, instance=None):
    return make_record(catalog, fid, value, source_kind='USER_PROVIDED',
        field_instance_id=instance or fid, source_id='SYNTHETIC-local',
        source_url_or_attachment='SYNTHETIC:local', source_section_or_cell=instance or fid,
        confidence_basis='SYNTHETIC generated test; not a real observation',
        last_updated='2026-10-29T00:00:00Z', retrieved_at='2026-10-29T00:00:00Z')


def base(catalog, zone='Asia/Shanghai'):
    s = IntakeSession.new('SYNTHETIC-d3', 'industrial_rooftop', catalog)
    s.project.values['site.timezone'] = atom(catalog, 'site.timezone', zone)
    return s.export()


def header(catalog, fid='load.series', n=3, minutes=60, start='2025-01-01T00:00:00+08:00', zone='Asia/Shanghai'):
    # Metadata is independent: no fake [] or truncated root array in the header.
    r = atom(catalog, fid, None)
    del r['value']; del r['original_value']
    r['measurement_period'] = {'start': start,
        'end': (datetime.fromisoformat(start) + timedelta(minutes=n*minutes)).isoformat(),
        'timezone': zone, 'interval_minutes': minutes, 'coverage': 1}
    return r


def rows(catalog, n=3, minutes=60, fid='load.series', start='2025-01-01T00:00:00+08:00'):
    for i in range(n):
        values = {'timestamp': (datetime.fromisoformat(start)+timedelta(minutes=i*minutes)).isoformat(),
            'interval_minutes': minutes, 'row_id': f'r{i}'}
        if fid == 'load.series':
            values.update(energy=Decimal('2.50')*minutes/60, power=Decimal('2.50'), quality_flag='valid')
        elif fid == 'resource.timeseries':
            values.update(ghi=100, dni=100, dhi=0, poa=100, ambient_temperature=20, wind_speed=1, quality_flag='valid')
        else:
            values.update(sale_price=Decimal('0.50'), transaction_fee=Decimal('0.01'))
        yield {'row_id': f'r{i}', 'fields': {fid+'.'+k: atom(catalog, fid+'.'+k, v, fid+f':r{i}:'+k) for k,v in values.items()}}


def write(tmp_path, catalog, **kwargs):
    mod = api()
    target = tmp_path / 'bundle'
    result = mod.write_bundle(target, base_export=kwargs.pop('base_export', base(catalog)),
        datasets=kwargs.pop('datasets', {'load.series': {'header': header(catalog), 'rows': rows(catalog)}}),
        catalog=catalog, budget=kwargs.pop('budget', mod.BundleBudget()), **kwargs)
    return target, result


def test_roundtrip_preserves_all_envelopes_and_layout_independent_identity(tmp_path, catalog):
    mod = api()
    original = list(rows(catalog))
    b = base(catalog)
    datasets = {'load.series': {'header': header(catalog), 'rows': original}}
    a = tmp_path/'a'; c = tmp_path/'c'
    m = mod.write_bundle(a, base_export=b, datasets=datasets, catalog=catalog, budget=mod.BundleBudget(), rows_per_chunk=1)
    mod.write_bundle(c, base_export=b, datasets=datasets, catalog=catalog, budget=mod.BundleBudget(), rows_per_chunk=2)
    with mod.read_bundle(a, catalog=catalog, budget=mod.BundleBudget()) as bundle:
        assert bundle.base_export == b
        assert bundle.dataset_ids == ('load.series',)
        assert list(bundle.rows('load.series')) == original
        assert bundle.manifest == m
        assert bundle.stats['rows_validated'] == 3
        assert bundle.stats['atoms_validated'] == 18
        assert bundle.manifest['datasets']['load.series']['metadata']['end'] == '2025-01-01T03:00:00+08:00'
        with mod.read_bundle(c, catalog=catalog, budget=mod.BundleBudget()) as other:
            assert other.content_hash == bundle.content_hash
    with pytest.raises(ContractError, match='BUNDLE_CLOSED'):
        list(bundle.rows('load.series'))

from wangbin_solar_pv.serialization import digest, MAX_JSON_BYTES


def api():
    return importlib.import_module('wangbin_solar_pv.timeseries_bundle')


def test_versioned_bundle_api_is_available():
    assert callable(getattr(api(), 'write_bundle', None))
    assert callable(getattr(api(), 'read_bundle', None))


def test_budget_is_explicit_and_strictly_positive():
    mod = api()
    assert mod.BundleBudget().max_rows > 0
    for invalid in (0, -1, True, float('inf')):
        with pytest.raises(ContractError, match='BUNDLE_BUDGET'):
            mod.BundleBudget(max_rows=invalid)


def test_canonical_array_hash_is_exact_legacy_digest():
    rows = [{'z': Decimal('1.2300'), '中文': ['a', None, True]}, {'a': Decimal('1E-8')}]
    assert api().canonical_array_hash(iter(rows)) == digest(rows)
    assert api().canonical_array_hash(iter([])) == digest([])
    assert MAX_JSON_BYTES == 32 * 1024 * 1024
