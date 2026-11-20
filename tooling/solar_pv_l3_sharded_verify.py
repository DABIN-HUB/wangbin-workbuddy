"""Independent R8 sharded-evidence verifier. Never imports the scheduler or its parser.

Checks artifacts for internal consistency; receipts are not cryptographic attestations
against an adversary able to replace *all* original artifacts and their hashes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

from .solar_pv_regression import GateError, ROOT

SCHEMA = 'solar-pv-l3-sharded/1'
PROCESS_SCHEMA = 'solar-pv-l3-sharded-process/1'
LIMIT = 512 * 1024 * 1024
ID = re.compile(r'tests/solar-pv/test_[^\s:]+\.py(?:::[^\s:]+)+\Z')
COUNT = re.compile(r'(?m)^([0-9]+) tests? collected(?: in |\s*$)')
MAX_XML = 20_000_000
MAX_COLLECTION = 5_000_000


def _current_identity() -> dict:
    """Recompute input bytes independently of the scheduler's identity helper."""
    prefixes = ('services/', 'tests/', 'tooling/', 'packages/', 'products/', 'docs/solar-pv/')
    allowed = {'pyproject.toml', 'requirements.txt', 'assets/config.yaml'}
    names = set()
    for args in (('ls-files', '-z'), ('ls-files', '--others', '--exclude-standard', '-z')):
        result = subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True)
        names.update(os.fsdecode(x) for x in result.stdout.split(b'\0') if x)
    def digest(name):
        path = ROOT
        for part in Path(name).parts:
            path = path / part
            if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
                raise GateError('linked input or parent')
        if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
            raise GateError('missing or escaped input')
        return _hash(path.read_bytes())
    inputs = {name: digest(name) for name in sorted(names)
              if name in allowed or name.startswith(prefixes)}
    reports_raw = subprocess.run(['git', 'ls-files', '-z', 'reports/solar-pv'], cwd=ROOT,
                                 check=True, capture_output=True).stdout
    reports = {name: digest(name) for name in sorted(os.fsdecode(x) for x in reports_raw.split(b'\0') if x)}
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                          capture_output=True).stdout.strip().decode()
    historical = 'r2-client-552-20261113-132354/workspaces'
    fixture_names = (
        f'.runtime/solar-pv/{historical}/industrial_rooftop/roof-primary/CH08-1-request.json',
        f'.runtime/solar-pv/{historical}/utility_scale_ground/ground-primary/CH08-1-request.json',
    )
    fixtures = {name: digest(name) for name in fixture_names}
    return {'head': head, 'inputs': inputs, 'input_count': len(inputs),
            'input_sha256': _hash(json.dumps(inputs, sort_keys=True, separators=(',', ':')).encode()),
            'report_inputs': reports,
            'report_sha256': _hash(json.dumps(reports, sort_keys=True, separators=(',', ':')).encode()),
            'ignored_fixture_inputs': fixtures,
            'ignored_fixture_sha256': _hash(json.dumps(fixtures, sort_keys=True,
                                                       separators=(',', ':')).encode())}


def _current_conditions() -> dict:
    packages = sorted((d.metadata['Name'].lower(), d.version)
                      for d in importlib.metadata.distributions() if d.metadata.get('Name'))
    keys = ('PYTHONHASHSEED', 'PYTEST_ADDOPTS', 'PYTEST_PLUGINS',
            'PYTEST_DISABLE_PLUGIN_AUTOLOAD', 'CI', 'TZ', 'LANG', 'LC_ALL', 'LC_CTYPE', 'PATH')
    return {'platform': platform.platform(), 'python': sys.executable,
            'python_version': sys.version, 'pytest': importlib.metadata.version('pytest'),
            'packages_sha256': _hash(json.dumps(packages).encode()),
            'env_sha256': {key: _hash(os.environ[key].encode()) if key in os.environ else None for key in keys},
            'pythonpath': os.pathsep.join(str(ROOT / p) for p in
                          ('services/solar-pv-engine/src', 'services/document-engine/src', '')),
            'temp_policy': 'distinct_sibling_roots_under_private_evidence_directory'}


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_COLLECTION:
        raise GateError(f'missing, linked or oversized evidence: {path}')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise GateError('evidence is not an object')
    return value


def _raw(path: Path, digest: str, limit: int) -> bytes:
    if (path.is_symlink() or not path.is_file() or path.stat().st_size > limit
            or not isinstance(digest, str)):
        raise GateError(f'missing, linked or oversized raw artifact: {path}')
    raw = path.read_bytes()
    if _hash(raw) != digest:
        raise GateError(f'raw artifact hash mismatch: {path}')
    return raw


def _collection(raw: bytes) -> list[str]:
    text = raw.decode('utf-8', errors='strict')
    if re.search(r'\bdeselected\b', text, re.I):
        raise GateError('collection deselected nodes')
    ids = [line for line in text.splitlines() if line.startswith('tests/solar-pv/')]
    counts = COUNT.findall(text)
    if (len(counts) != 1 or not ids or len(ids) != int(counts[0])
            or len(set(ids)) != len(ids) or any(not ID.fullmatch(node) for node in ids)):
        raise GateError('incomplete, duplicate or invalid collection')
    return ids


def _xml(raw: bytes) -> dict[str, str]:
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise GateError('DTD/entity forbidden')
    tree = ET.fromstring(raw)
    if tree.tag not in {'testsuite', 'testsuites'}:
        raise GateError('invalid JUnit root')
    if tree.tag == 'testsuites' and set(tree.attrib) - {'name', 'tests', 'failures', 'errors', 'skipped', 'time'}:
        raise GateError('unknown JUnit root attribute')
    suites = [tree] if tree.tag == 'testsuite' else list(tree)
    if not suites or any(s.tag != 'testsuite' for s in suites):
        raise GateError('invalid JUnit suites')
    nodes = {}
    totals = Counter()
    for suite in suites:
        if set(suite.attrib) - {'name', 'tests', 'failures', 'errors', 'skipped', 'time', 'timestamp', 'hostname', 'id'}:
            raise GateError('unknown JUnit suite attribute')
        cases = list(suite)
        if len(cases) > 15000 or int(suite.get('tests', '-1')) != len(cases):
            raise GateError('unrepresented subtest or suite count mismatch')
        counts = Counter()
        for case in cases:
            if case.tag != 'testcase' or not case.get('classname') or not case.get('name'):
                raise GateError('invalid JUnit testcase')
            if set(case.attrib) - {'classname', 'name', 'time', 'file', 'line'}:
                raise GateError('unknown JUnit testcase attribute')
            match = re.fullmatch(r'tests\.solar-pv\.(test_[^.]+)(?:\.(.+))?', case.get('classname'))
            if not match:
                raise GateError('foreign JUnit testcase')
            name = 'tests/solar-pv/' + match[1] + '.py::'
            if match[2]:
                name += match[2].replace('.', '::') + '::'
            name += case.get('name')
            if not ID.fullmatch(name) or name in nodes:
                raise GateError('duplicate or invalid normalized node')
            outcome = 'passed'
            for child in case:
                if child.tag == 'properties':
                    if child.attrib or any(p.tag != 'property' or len(p)
                                           or set(p.attrib) - {'name', 'value'} or not p.get('name')
                                           for p in child):
                        raise GateError('nested JUnit property')
                elif child.tag in {'system-out', 'system-err'}:
                    if child.attrib or len(child):
                        raise GateError('nested JUnit output')
                elif child.tag in {'failure', 'error', 'skipped'}:
                    if set(child.attrib) - {'message', 'type'} or len(child):
                        raise GateError('nested JUnit outcome')
                    if outcome != 'passed':
                        raise GateError('mixed or multiple JUnit outcome')
                    outcome = child.tag
                    counts[child.tag + 's' if child.tag != 'skipped' else 'skipped'] += 1
                else:
                    raise GateError('unknown JUnit child')
            nodes[name] = outcome
        for key in ('failures', 'errors', 'skipped'):
            if int(suite.get(key, '-1')) != counts[key]:
                raise GateError('JUnit suite outcome mismatch')
        totals.update({'tests': len(cases), **{key: counts[key] for key in ('failures', 'errors', 'skipped')}})
    if tree.tag == 'testsuites':
        for key in ('tests', 'failures', 'errors', 'skipped'):
            if tree.get(key) is not None and int(tree.get(key)) != totals[key]:
                raise GateError('JUnit root outcome mismatch')
    if any(value != 'passed' for value in nodes.values()):
        raise GateError('failure, error or unexpected skip in shard')
    return nodes


def _process(root: Path, folder: str, kind: str, file: str | None,
             collection_files: list[str] | None,
             identity: dict, conditions: dict, pandoc: dict, timeout: int) -> bytes:
    path = root / folder
    if path.is_symlink() or not path.is_dir():
        raise GateError('missing or linked process directory')
    receipt = _json(path / 'receipt.json')
    tmp, base = path / 'workspace-tmp', path / 'pytest-basetemp'
    command = [conditions['python'], '-m', 'pytest', *(collection_files or [file or 'tests/solar-pv']), '-q', '-ra',
               '-p', 'no:cacheprovider', f'--basetemp={base}',
               '--collect-only' if kind == 'collect' else f'--junitxml={path / "junit.xml"}']
    if (receipt.get('schema') != PROCESS_SCHEMA or receipt.get('kind') != kind
            or receipt.get('command') != command
            or receipt.get('scratch') != {'TMPDIR': str(tmp), 'basetemp': str(base)}
            or receipt.get('exit_code') != 0 or receipt.get('timed_out') is not False
            or receipt.get('identity_before') != identity or receipt.get('identity_after') != identity
            or receipt.get('conditions_before') != conditions or receipt.get('conditions_after') != conditions
            or receipt.get('pandoc') != pandoc or receipt.get('error') or receipt.get('evidence_error')):
        raise GateError(f'process identity, exit, timeout, command or scratch mismatch: {folder}')
    if not (tmp != base and tmp.parent == path and base.parent == path):
        raise GateError('overlapping scratch')
    try:
        start = datetime.fromisoformat(receipt['started_utc'])
        end = datetime.fromisoformat(receipt['finished_utc'])
        if (start.tzinfo is None or end.tzinfo is None or end < start
                or (end - start).total_seconds() > timeout + 5):
            raise ValueError('invalid timing')
    except (KeyError, TypeError, ValueError) as exc:
        raise GateError('missing or invalid process timing') from exc
    for log in ('stdout', 'stderr'):
        _raw(path / f'{log}.log', receipt.get(f'{log}_sha256'), MAX_COLLECTION)
    resource = receipt.get('resource')
    if (not isinstance(resource, dict) or resource.get('enforcement') != 'OS_JOB_MEMORY_HARD_LIMIT'
            or resource.get('limit_bytes') != LIMIT or resource.get('actual_child_observed') is not True
            or resource.get('complete_tree_accounting') is not True or resource.get('guard_error') is not None
            or type(resource.get('max_current_bytes')) is not int
            or type(resource.get('max_lifetime_peak_bytes')) is not int
            or type(resource.get('total_job_processes')) is not int
            or resource['total_job_processes'] < 2
            or type(resource.get('peak_job_private_commit_bytes')) is not int
            or not 0 < resource['peak_job_private_commit_bytes'] <= LIMIT
            or not 1024 * 1024 <= resource['max_current_bytes'] <= LIMIT
            or not resource['max_current_bytes'] <= resource['max_lifetime_peak_bytes'] <= LIMIT):
        raise GateError('OS-enforced child resource proof absent or exceeded')
    if kind == 'collect':
        if (path / 'junit.xml').exists() or 'junit_sha256' in receipt:
            raise GateError('collection unexpectedly has JUnit')
        return (path / 'stdout.log').read_bytes()
    return _raw(path / 'junit.xml', receipt.get('junit_sha256'), MAX_XML)


def verify(root: Path, *, check_current: bool = True) -> dict:
    root = root.resolve(strict=True)
    if root == ROOT or ROOT in root.parents:
        raise GateError('evidence inside repository')
    summary = _json(root / 'summary.json')
    mode = summary.get('mode')
    if summary.get('schema') != SCHEMA or mode not in {'full', 'smoke'}:
        raise GateError('wrong schema or mode')
    if mode == 'full' and not check_current:
        raise GateError('archived-only evidence cannot certify current full gate')
    files = summary.get('files')
    if (not isinstance(files, list) or not files or files != sorted(set(files))
            or any(not re.fullmatch(r'tests/solar-pv/test_[^/]+\.py', name) for name in files)):
        raise GateError('invalid file inventory')
    if mode == 'full':
        actual = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / 'tests/solar-pv').glob('test_*.py'))
        if files != actual:
            raise GateError('full file inventory differs from checkout')
    if mode == 'smoke' and (len(files) < 2 or len(files) > 3 or summary.get('verdict') != 'SMOKE_ONLY'):
        raise GateError('invalid smoke scope/verdict')
    if mode == 'full' and summary.get('verdict') != 'FULL_ALL_PASSED':
        raise GateError('invalid full verdict')
    if summary.get('error'):
        raise GateError('failed or interrupted summary')
    timeout = summary.get('process_timeout_seconds')
    if type(timeout) is not int or not 10 <= timeout <= 14400:
        raise GateError('invalid process timeout')
    identity, conditions, pandoc = (summary.get(key) for key in ('identity', 'conditions', 'pandoc'))
    if (not isinstance(identity, dict) or not isinstance(conditions, dict) or not isinstance(pandoc, dict)
            or not isinstance(identity.get('inputs'), dict)
            or not isinstance(conditions.get('python'), str)
            or not isinstance(pandoc.get('path'), str)
            or not isinstance(pandoc.get('sha256'), str)
            or not isinstance(pandoc.get('version'), str)):
        raise GateError('invalid identity or Pandoc')
    if check_current:
        if identity != _current_identity() or conditions != _current_conditions():
            raise GateError('current source or environment drift')
        executable = Path(pandoc['path'])
        if (not executable.is_absolute() or not executable.is_file()
                or _hash(executable.read_bytes()) != pandoc['sha256']):
            raise GateError('Pandoc executable drift')
    collected = _collection(_process(root, 'collect', 'collect', None,
                                     files if mode == 'smoke' else None, identity, conditions, pandoc, timeout))
    if (summary.get('collected_ids') != collected or summary.get('collection_sha256') != _hash('\n'.join(collected).encode())
            or sorted({node.split('::')[0] for node in collected}) != files):
        raise GateError('collection differs from receipt/files')
    shards = summary.get('shards')
    if shards != [f'shard-{i:03d}' for i in range(len(files))]:
        raise GateError('missing, duplicate or unexpected shard')
    executed = []
    for index, file in enumerate(files):
        parsed = _xml(_process(root, shards[index], 'shard', file, None, identity, conditions, pandoc, timeout))
        expected = [node for node in collected if node.split('::')[0] == file]
        if list(parsed) != expected:
            raise GateError(f'shard node mismatch: {file}')
        executed.extend(parsed)
    if executed != collected and set(executed) != set(collected):
        raise GateError('missing/duplicate execution')
    if len(executed) != len(set(executed)) or set(executed) != set(collected):
        raise GateError('missing/duplicate execution')
    return {'schema': 'solar-pv-l3-sharded-verification/1',
            'verdict': 'FULL_ALL_PASSED' if mode == 'full' else 'SMOKE_ONLY',
            'covered_count': len(collected), 'shard_count': len(files), 'identity': identity,
            'source': str(root), 'independent_artifacts_reparsed': True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--archived-only', action='store_true', help='internal consistency only; never certify full')
    args = parser.parse_args(argv)
    try:
        result = verify(args.evidence, check_current=not args.archived_only)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (GateError, OSError, ValueError, KeyError, ET.ParseError) as exc:
        print(f'BLOCKED: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
