"""Real SYNTHETIC whole-table D3 acceptance; deliberately not a fake probe.

Run with scratch --basetemp and D3_METRICS_DIR. Writes/fully validates/reads and
sums EVERY row. Windows GetProcessMemoryInfo measures real working-set/HWM.
No psutil/new dependency, no network, no guessed throughput figures.
"""
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import time

import pytest
from test_timeseries_bundle import api, base, catalog, header, rows
from wangbin_solar_pv.timeseries_private import memory_usage


@pytest.mark.parametrize('n,minutes', [(8760,60), (35040,15)], ids=['8760-hour', '35040-quarter-hour'])
def test_real_whole_table_capacity(tmp_path, catalog, n, minutes):
    mod = api()
    from wangbin_solar_pv import __version__
    source_root=Path(mod.__file__).parent
    names=('timeseries_bundle.py','timeseries_private.py','timeseries_tokens.py','validation.py','serialization.py','schemas.py','provenance.py','intake.py')
    source_hashes={name:hashlib.sha256((source_root/name).read_bytes()).hexdigest() for name in names}
    budget = mod.BundleBudget(max_input_bytes=1024**3, max_disk_bytes=2*1024**3,
        max_rows=100000, max_seconds=1800, max_memory_bytes=512*1024**2)
    target = tmp_path/'whole-table'
    start_ws, start_hwm = memory_usage()
    t0 = time.perf_counter()
    manifest = mod.write_bundle(target, base_export=base(catalog),
        datasets={'load.series':{'header':header(catalog,n=n,minutes=minutes),
                                'rows':rows(catalog,n=n,minutes=minutes)}},
        catalog=catalog,budget=budget)
    written = time.perf_counter()-t0
    t1 = time.perf_counter()
    with mod.read_bundle(target,catalog=catalog,budget=budget) as bundle:
        validated = time.perf_counter()-t1
        stats = bundle.stats
        assert stats['rows_validated'] == n
        assert stats['atoms_validated'] == n*6
        assert bundle.manifest['datasets']['load.series']['metadata']['end'] == '2026-01-01T00:00:00+08:00'
        t2 = time.perf_counter()
        count = 0; total = Decimal(0)
        for row in bundle.rows('load.series'):
            count += 1; total += row['fields']['load.series.energy']['value']
        summed = time.perf_counter()-t2
        assert count == n
        assert total == Decimal('2.50')*8760
    end_ws,end_hwm = memory_usage()
    disk = sum(p.stat().st_size for p in target.iterdir())
    assert disk > 32*1024**2
    assert end_hwm <= budget.max_memory_bytes
    assert source_hashes=={name:hashlib.sha256((source_root/name).read_bytes()).hexdigest() for name in names}
    measured = {'synthetic':True,'source_hashes':source_hashes,'input_module_version':__version__,
        'rows':n,'atoms_validated_each_write_and_read':n*6,
        'interval_minutes':minutes,'sum_kWh':str(total),'disk_bytes':disk,
        'write_seconds':written,'full_read_validation_seconds':validated,'iteration_sum_seconds':summed,
        'write_rows_per_second':n/written,'validated_read_rows_per_second':n/validated,
        'write_MiB_per_second':disk/(1024**2)/written,
        'validated_read_MiB_per_second':disk/(1024**2)/validated,
        'start_working_set_bytes':start_ws,'end_working_set_bytes':end_ws,
        'start_os_peak_bytes':start_hwm,'actual_os_peak_bytes':end_hwm,
        'read_stats':stats,'content_hash':manifest['content_hash']}
    root = Path(os.environ.get('D3_METRICS_DIR',str(tmp_path)))
    root.mkdir(parents=True,exist_ok=True)
    (root/f'capacity-{n}.json').write_text(json.dumps(measured,indent=2),encoding='utf-8')
    print(json.dumps(measured))
