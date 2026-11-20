"""ATTACKER tests for R8 evidence; synthetic receipts do not prove OS enforcement."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from tooling.solar_pv_regression import GateError
from tooling import solar_pv_l3_sharded_verify as audit
from tooling import solar_pv_l3_sharded as runner

A = 'tests/solar-pv/test_alpha.py::test_a'
B = 'tests/solar-pv/test_beta.py::Case::test_b[param]'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixture(tmp_path):
    root = tmp_path / 'fresh-evidence'
    root.mkdir()
    files = [A.split('::')[0], B.split('::')[0]]
    nodes = [A, B]
    identity = {'head': 'a' * 40, 'input_sha256': 'b' * 64, 'inputs': {'tests/solar-pv/test_alpha.py': 'c' * 64}}
    conditions = {'python': 'C:/python.exe', 'pytest': '9.2.0', 'packages_sha256': 'd' * 64}
    pandoc = {'path': 'C:/pandoc.exe', 'sha256': 'e' * 64, 'version': 'pandoc 3.14'}
    def entry(directory, kind, name=None):
        directory.mkdir()
        tmp = directory / 'workspace-tmp'
        base = directory / 'pytest-basetemp'
        command = [conditions['python'], '-m', 'pytest', *(files if kind == 'collect' else [name]), '-q', '-ra', '-p', 'no:cacheprovider', f'--basetemp={base}']
        command.append('--collect-only' if kind == 'collect' else f'--junitxml={directory / "junit.xml"}')
        data = {'schema': 'solar-pv-l3-sharded-process/1', 'kind': kind, 'command': command,
                'exit_code': 0, 'timed_out': False, 'identity_before': identity,
                'identity_after': identity, 'conditions_before': conditions,
                'conditions_after': conditions, 'pandoc': pandoc,
                'scratch': {'TMPDIR': str(tmp), 'basetemp': str(base)},
                'started_utc': '2026-11-20T00:00:00+00:00',
                'finished_utc': '2026-11-20T00:00:01+00:00'}
        stdout = ('\n'.join(nodes) + '\n2 tests collected in 0.01s\n').encode() if kind == 'collect' else b'2 passed in 1s\n'
        (directory / 'stdout.log').write_bytes(stdout)
        (directory / 'stderr.log').write_bytes(b'')
        data['stdout_sha256'] = sha(stdout)
        data['stderr_sha256'] = sha(b'')
        if name:
            node = A if name == files[0] else B
            classname = 'tests.solar-pv.test_alpha' if node == A else 'tests.solar-pv.test_beta.Case'
            testname = node.rsplit('::', 1)[1]
            xml = (f'<testsuites tests="1" failures="0" errors="0" skipped="0">'
                   f'<testsuite tests="1" failures="0" errors="0" skipped="0">'
                   f'<testcase classname="{classname}" name="{testname}"/>'
                   f'</testsuite></testsuites>').encode()
            (directory / 'junit.xml').write_bytes(xml)
            data['junit_sha256'] = sha(xml)
            data['resource'] = {'enforcement': 'OS_JOB_MEMORY_HARD_LIMIT',
                                'limit_bytes': 536870912, 'max_current_bytes': 33554432,
                                'max_lifetime_peak_bytes': 37748736, 'actual_child_observed': True,
                                'complete_tree_accounting': True, 'guard_error': None,
                                'total_job_processes': 2, 'peak_job_private_commit_bytes': 20971520}
        (directory / 'receipt.json').write_text(json.dumps(data), encoding='utf-8')
        return data
    collect = entry(root / 'collect', 'collect')
    collect['resource'] = {'enforcement': 'OS_JOB_MEMORY_HARD_LIMIT', 'limit_bytes': 536870912,
                           'max_current_bytes': 33554432, 'max_lifetime_peak_bytes': 37748736,
                           'actual_child_observed': True, 'complete_tree_accounting': True, 'guard_error': None,
                           'total_job_processes': 2, 'peak_job_private_commit_bytes': 20971520}
    (root / 'collect' / 'receipt.json').write_text(json.dumps(collect), encoding='utf-8')
    for index, file in enumerate(files):
        entry(root / f'shard-{index:03d}', 'shard', file)
    summary = {'schema': 'solar-pv-l3-sharded/1', 'mode': 'smoke', 'verdict': 'SMOKE_ONLY',
               'identity': identity, 'conditions': conditions, 'pandoc': pandoc,
               'files': files, 'collected_ids': nodes, 'collection_sha256': sha('\n'.join(nodes).encode()),
               'shards': [f'shard-{index:03d}' for index in range(2)],
               'process_timeout_seconds': 10000}
    (root / 'summary.json').write_text(json.dumps(summary), encoding='utf-8')
    return root


def rewrite(root, relative, mutate):
    path = root / relative
    data = json.loads(path.read_text(encoding='utf-8'))
    mutate(data)
    path.write_text(json.dumps(data), encoding='utf-8')


def test_attacker_baseline_smoke_is_not_full(tmp_path):
    root = fixture(tmp_path)
    result = audit.verify(root, check_current=False)
    assert result['verdict'] == 'SMOKE_ONLY'
    assert result['covered_count'] == 2


@pytest.mark.parametrize('tamper', [
    lambda d: d['collected_ids'].pop(),
    lambda d: d['collected_ids'].append(A),
    lambda d: d['shards'].append('shard-000'),
    lambda d: d.update(verdict='FULL_ALL_PASSED'),
    lambda d: d.update(mode='full'),
    lambda d: d.update(collection_sha256='0' * 64),
    lambda d: d['identity'].update(head='f' * 40),
    lambda d: d['pandoc'].update(sha256='f' * 64),
    lambda d: d.update(process_timeout_seconds=1),
])
def test_attacker_summary_forgery_rejected(tmp_path, tamper):
    root = fixture(tmp_path)
    rewrite(root, 'summary.json', tamper)
    with pytest.raises(GateError):
        audit.verify(root, check_current=False)


@pytest.mark.parametrize('relative,change', [
    ('collect/stdout.log', lambda p: p.write_bytes(p.read_bytes() + b'1 deselected\n')),
    ('shard-000/stdout.log', lambda p: p.write_bytes(b'pretend PASS')),
    ('shard-000/stderr.log', lambda p: p.write_bytes(b'failure')),
    ('shard-000/junit.xml', lambda p: p.write_bytes(p.read_bytes().replace(b'test_a', b'test_fake'))),
    ('shard-001/junit.xml', lambda p: p.write_bytes(p.read_bytes().replace(b'test_b[param]', b'test_b[other]'))),
])
def test_attacker_raw_artifact_tamper_rejected(tmp_path, relative, change):
    root = fixture(tmp_path)
    change(root / relative)
    with pytest.raises(GateError):
        audit.verify(root, check_current=False)


@pytest.mark.parametrize('change', [
    lambda d: d.update(exit_code=1),
    lambda d: d.update(timed_out=True),
    lambda d: d.update(junit_sha256='0' * 64),
    lambda d: d['resource'].update(max_lifetime_peak_bytes=536870913),
    lambda d: d['resource'].update(enforcement='psutil sampling'),
    lambda d: d['resource'].update(actual_child_observed=False),
    lambda d: d['resource'].update(complete_tree_accounting=False),
    lambda d: d['resource'].update(total_job_processes=1),
    lambda d: d['resource'].update(max_current_bytes=1234, max_lifetime_peak_bytes=1234),
    lambda d: d['resource'].update(max_current_bytes=40000000, max_lifetime_peak_bytes=33000000),
    lambda d: d.update(finished_utc='2026-11-20T04:00:00+00:00'),
    lambda d: d['identity_after'].update(head='f' * 40),
    lambda d: d['conditions_after'].update(pytest='0'),
    lambda d: d['pandoc'].update(path='C:/other.exe'),
    lambda d: d['command'].append('-k=passed'),
])
def test_attacker_receipt_mutation_rejected(tmp_path, change):
    root = fixture(tmp_path)
    rewrite(root, 'shard-000/receipt.json', change)
    with pytest.raises(GateError):
        audit.verify(root, check_current=False)


def test_attacker_rehashed_skip_and_nested_xml_rejected(tmp_path):
    root = fixture(tmp_path)
    path = root / 'shard-000/junit.xml'
    data = path.read_bytes().replace(b'name="test_a"/>', b'name="test_a"><properties><property><failure/></property></properties></testcase>')
    path.write_bytes(data)
    rewrite(root, 'shard-000/receipt.json', lambda d: d.update(junit_sha256=sha(data)))
    with pytest.raises(GateError):
        audit.verify(root, check_current=False)
    data = data.replace(b'<properties><property><failure/></property></properties>', b'<skipped message="unexpected"/>').replace(b'skipped="0"', b'skipped="1"')
    path.write_bytes(data)
    rewrite(root, 'shard-000/receipt.json', lambda d: d.update(junit_sha256=sha(data)))
    with pytest.raises(GateError):
        audit.verify(root, check_current=False)


def test_attacker_rehashed_missing_and_duplicate_nodes_rejected(tmp_path):
    root = fixture(tmp_path)
    path = root / 'shard-001/junit.xml'
    data = path.read_bytes().replace(b'test_b[param]', b'test_a').replace(b'test_beta.Case', b'test_alpha')
    path.write_bytes(data)
    rewrite(root, 'shard-001/receipt.json', lambda d: d.update(junit_sha256=sha(data)))
    with pytest.raises(GateError):
        audit.verify(root, check_current=False)


def test_attacker_rehashed_deselection_rejected(tmp_path):
    root = fixture(tmp_path)
    path = root / 'collect/stdout.log'
    data = path.read_bytes() + b'1 deselected\n'
    path.write_bytes(data)
    rewrite(root, 'collect/receipt.json', lambda d: d.update(stdout_sha256=sha(data)))
    with pytest.raises(GateError, match='deselected'):
        audit.verify(root, check_current=False)


def test_attacker_interrupted_run_cannot_pass(tmp_path):
    root = fixture(tmp_path)
    (root / 'shard-001/receipt.json').unlink()
    with pytest.raises(GateError):
        audit.verify(root, check_current=False)


def test_attacker_mixed_failure_labels_rejected_even_when_rehashed(tmp_path):
    root = fixture(tmp_path)
    path = root / 'shard-000/junit.xml'
    data = path.read_bytes().replace(b'name="test_a"/>', b'name="test_a"><failure/><error/></testcase>')
    data = data.replace(b'failures="0"', b'failures="1"').replace(b'errors="0"', b'errors="1"')
    path.write_bytes(data)
    rewrite(root, 'shard-000/receipt.json', lambda d: d.update(junit_sha256=sha(data)))
    with pytest.raises(GateError):
        audit.verify(root, check_current=False)


def test_full_mode_rejects_nonexistent_pandoc_before_collection(tmp_path):
    with pytest.raises(GateError):
        runner._formal_prerequisites(Path('C:/absent-pandoc-r8.exe'))


@pytest.mark.parametrize('before,after', [
    (b'<testsuites tests=', b'<testsuites unexplained="1" tests='),
    (b'<testsuite tests=', b'<testsuite unexplained="1" tests='),
    (b'name="test_a"/>', b'name="test_a" status="failed"/>'),
    (b'name="test_a"/>', b'name="test_a"><properties><property name="case" hidden="failed"/></properties></testcase>'),
])
def test_attacker_rehashed_unknown_xml_metadata_rejected(tmp_path, before, after):
    root = fixture(tmp_path)
    path = root / 'shard-000/junit.xml'
    data = path.read_bytes().replace(before, after)
    assert data != path.read_bytes()
    path.write_bytes(data)
    rewrite(root, 'shard-000/receipt.json', lambda d: d.update(junit_sha256=sha(data)))
    with pytest.raises(GateError):
        audit.verify(root, check_current=False)
