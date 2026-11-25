"""Explicit preparation and offline identity checks for the Consultant regression.

Only standard library imports: preparation can run before pytest/PyYAML exist.
Checks never fetch, install, rebuild or recover an original automatically.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import zipfile

NAME = 'wangbin-software-consultant'
SOURCE = f'packages/experts/{NAME}'
LEGACY_COMMIT = '67d0fe8cfa5d71b53cc46d79bbaec620638dd1e0'
PRICE_COMMIT = '5a3de264eb84a4aac66e8d8f390b8ab7255f3d8b'
SEALED_COMMIT = 'e376395df4e09267ef494f4e421fc49d4fbdb6dd'
LEGACY_MEMBERS = ('.codebuddy-plugin/plugin.json', f'agents/{NAME}.md',
                  'avatars/expert.png', 'README.md', 'LICENSE')
ESTIMATOR = 'skills/wangbin-estimate-calculator/scripts/estimator.py'
CANDIDATE_MEMBERS = LEGACY_MEMBERS + (
    'skills/wangbin-estimate-calculator/SKILL.md', ESTIMATOR,
    'skills/wangbin-estimate-calculator/references/input-output-contract.md',
    'skills/wangbin-estimate-calculator/LICENSE',
)
CANDIDATE_NAME = f'{NAME}-1.2.0-expert-candidate.zip'
ORIGINAL_IDENTITIES = {
    CANDIDATE_NAME: (164569, 'd42eaa2090eb07660cbb6f712ae506a2f731e5fd62035d5ccd58fec0f236bd47'),
    CANDIDATE_NAME + '.manifest.json': (2546, '59a7f5001637a0ba1d3537e7aa3c61d9e891d26f0ea557e31a8badb9e672c318'),
    CANDIDATE_NAME + '.sha256': (121, '95407556349acc880f29cb7ee6f0992730e0d4c7799ac689eea9e400992cd1dd'),
}
PINS = {'pytest': '8.4.2', 'PyYAML': '6.0.3', 'colorama': '0.4.6',
        'iniconfig': '2.3.1', 'packaging': '26.3', 'pluggy': '1.7.0', 'Pygments': '2.21.0'}
ORIGIN = 'https://github.com/DABIN-HUB/wangbin-workbuddy.git'
REF = 'refs/heads/expert/software-consultant'


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _status(*states: str) -> str:
    return 'FAIL' if 'FAIL' in states else 'BLOCKED' if 'BLOCKED' in states else 'PASS'


def _safe(path: Path, *, directory: bool = False, missing: bool = False) -> Path:
    path = Path(path)
    if '..' in path.parts:
        raise ValueError('parent traversal is forbidden')
    path = path.absolute()
    for part in reversed((path, *path.parents)):
        try:
            info = part.lstat()
        except FileNotFoundError:
            if missing:
                continue
            raise
        if (stat.S_ISLNK(info.st_mode) or
                getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError('linked or reparse-point path is forbidden')
        expected_directory = part != path or directory
        if not (stat.S_ISDIR(info.st_mode) if expected_directory else stat.S_ISREG(info.st_mode)):
            raise ValueError('non-regular file or directory')
    return path


def _env() -> dict[str, str]:
    # Avoid inherited Git source overrides, pip target overrides and Python paths.
    return {k: v for k, v in os.environ.items()
            if not k.upper().startswith(('GIT_', 'PIP_', 'PYTHON'))}


def _git(root: Path, *args: str, timeout: int = 60, explicit_fetch: bool = False) -> subprocess.CompletedProcess:
    env = _env()
    env.update(GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    offline = []
    if not explicit_fetch:
        # The empty allowlist overrides even per-protocol repository settings;
        # protocol.allow=never alone is only the default for unlisted protocols.
        env['GIT_ALLOW_PROTOCOL'] = ''
        offline = ['-c', 'protocol.allow=never']
    return subprocess.run(['git', '--no-replace-objects', '-c', 'core.longpaths=true',
                           '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', *offline, *args],
                          cwd=root, env=env, capture_output=True, timeout=timeout)


def _repo(root: Path) -> Path:
    root = _safe(root, directory=True)
    result = _git(root, 'rev-parse', '--show-toplevel')
    if result.returncode or Path(result.stdout.decode('utf-8').strip()).resolve() != root.resolve():
        raise ValueError('explicit repository top level required')
    return root


def _history_payload(root: Path, commit: str, members: tuple[str, ...]) -> tuple[dict, dict[str, bytes]]:
    result = {'commit': commit, 'status': 'PASS', 'missing': [], 'reason': '', 'blobs': {}}
    payload = {}
    try:
        root = _repo(root)
        obj = _git(root, 'cat-file', '-t', commit)
        if obj.returncode:
            result.update(status='BLOCKED', reason='commit object unavailable', missing=[commit])
            return result, payload
        if obj.stdout.strip() != b'commit':
            result.update(status='FAIL', reason='expected an actual commit object')
            return result, payload
        content = _git(root, 'cat-file', 'commit', commit)
        if content.returncode:
            result.update(status='BLOCKED', reason='commit bytes unavailable', missing=[commit])
            return result, payload
        if hashlib.sha1(f'commit {len(content.stdout)}\0'.encode() + content.stdout).hexdigest() != commit:
            result.update(status='FAIL', reason='commit object identity mismatch')
            return result, payload
        paths = [f'{SOURCE}/{rel}' for rel in members]
        tree = _git(root, 'ls-tree', '-z', '--full-tree', commit, '--', *paths)
        if tree.returncode:
            result.update(status='BLOCKED', reason='required tree objects unavailable', missing=paths)
            return result, payload
        rows = {}
        for row in tree.stdout.split(b'\0'):
            if row:
                desc, path = row.split(b'\t', 1)
                rows[path.decode('utf-8')] = desc.decode('ascii').split()
        for path, rel in zip(paths, members):
            if path not in rows:
                result['status'] = 'FAIL'
                result['missing'].append(path)
                continue
            mode, kind, oid = rows[path]
            if kind != 'blob' or mode not in ('100644', '100755'):
                result['status'] = 'FAIL'
                result['reason'] = 'required object is not a regular file blob'
                continue
            blob = _git(root, 'cat-file', 'blob', oid)
            if blob.returncode:
                result['status'] = _status(result['status'], 'BLOCKED')
                result['missing'].append(path)
                continue
            raw = blob.stdout
            if hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest() != oid:
                result.update(status='FAIL', reason='Git blob object identity mismatch')
                continue
            payload[f'{NAME}/{rel}'] = raw
            result['blobs'][path] = {'oid': oid, 'size': len(raw), 'sha256': _sha(raw)}
        if result['status'] != 'PASS' and not result['reason']:
            result['reason'] = 'required path absent from commit' if result['status'] == 'FAIL' else 'required blob unavailable'
    except (OSError, subprocess.SubprocessError) as exc:
        result.update(status='BLOCKED', reason=type(exc).__name__)
    except ValueError:
        result.update(status='FAIL', reason='invalid repository or object structure')
    return result, payload


def inspect_history(root: Path) -> dict[str, dict]:
    return {key: _history_payload(root, commit, members)[0] for key, commit, members in (
        ('legacy', LEGACY_COMMIT, LEGACY_MEMBERS), ('price', PRICE_COMMIT, (ESTIMATOR,)),
        ('sealed', SEALED_COMMIT, CANDIDATE_MEMBERS))}


def prepare_history(root: Path) -> dict:
    """Explicit, ref-limited fetch; no repo refs, FETCH_HEAD or working tree updates."""
    history = inspect_history(root)
    state = _status(*(v['status'] for v in history.values()))
    if state != 'BLOCKED':
        return {'status': state, 'history': history, 'fetched': False}
    try:
        root = _repo(root)
        stored = _git(root, 'config', '--get-all', 'remote.origin.url')
        effective = _git(root, 'remote', 'get-url', '--all', 'origin')
        # Both must identify exactly the approved credential-free URL, without rewrites.
        if any(r.returncode or r.stdout.decode('utf-8').splitlines() != [ORIGIN]
               for r in (stored, effective)):
            return {'status': 'FAIL', 'history': history, 'fetched': False, 'reason': 'origin is not the authorized repository'}
        shallow = _git(root, 'rev-parse', '--is-shallow-repository')
        if shallow.returncode or shallow.stdout.strip() not in (b'true', b'false'):
            return {'status': 'BLOCKED', 'history': history, 'fetched': False, 'reason': 'cannot determine shallow history'}
        # A source-only refspec, empty refmap and no FETCH_HEAD avoid ref updates.
        args = ['-c', 'fetch.writeCommitGraph=false', '-c', 'fetch.prune=false',
                'fetch', '--no-tags', '--no-prune', '--no-prune-tags', '--no-write-fetch-head',
                '--no-recurse-submodules', '--no-auto-maintenance', '--no-filter', '--refmap=']
        if shallow.stdout.strip() == b'true':
            args.append('--unshallow')
        else:
            # Missing blobs can coexist with already-known commit tips. Normal
            # negotiation may then transfer nothing; refetch only the approved ref.
            args.append('--refetch')
        run = _git(root, *args, 'origin', REF, timeout=300, explicit_fetch=True)
        after = inspect_history(root)
        status = _status(*(v['status'] for v in after.values()))
        if run.returncode:
            status = _status(status, 'BLOCKED')
        return {'status': status, 'history': after, 'fetched': run.returncode == 0,
                'fetch_exit_code': run.returncode, 'ref': REF,
                'reason': '' if status == 'PASS' else 'required historical objects not fully verified'}
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return {'status': 'BLOCKED', 'history': history, 'fetched': False, 'reason': type(exc).__name__}


def _read_original(directory: Path) -> tuple[dict, dict[str, bytes]]:
    result = {'status': 'PASS', 'files': {}, 'missing': [], 'reason': ''}
    raw = {}
    try:
        directory = _safe(directory, directory=True, missing=True)
        for name, (size, sha) in ORIGINAL_IDENTITIES.items():
            path = _safe(directory / name, missing=True)
            try:
                info = path.stat()
            except FileNotFoundError:
                result['status'] = _status(result['status'], 'BLOCKED')
                result['missing'].append(name)
                continue
            if info.st_size != size:
                result['files'][name] = {'size': info.st_size, 'expected_sha256': sha, 'status': 'FAIL'}
                result['status'] = 'FAIL'
                continue
            data = path.read_bytes()
            actual = _sha(data)
            match = len(data) == size and actual == sha
            result['files'][name] = {'size': len(data), 'sha256': actual, 'expected_sha256': sha,
                                     'status': 'PASS' if match else 'FAIL'}
            if match:
                raw[name] = data
            else:
                result['status'] = 'FAIL'
        if result['status'] == 'FAIL':
            result['reason'] = 'original artifact identity conflict'
        elif result['status'] == 'BLOCKED':
            result['reason'] = 'original artifact set incomplete'
    except (OSError, ValueError) as exc:
        result.update(status='FAIL', reason=f'unsafe or unreadable artifact path: {type(exc).__name__}')
    return result, raw


def _inspect_original(root: Path, directory: Path) -> tuple[dict, dict[str, bytes]]:
    result, files = _read_original(directory)
    integrity = result['status']
    sealed, expected = _history_payload(root, SEALED_COMMIT, CANDIDATE_MEMBERS)
    binding = _status(integrity, sealed['status'])
    if integrity == 'PASS':
        try:
            sha = ORIGINAL_IDENTITIES[CANDIDATE_NAME][1]
            if files[CANDIDATE_NAME + '.sha256'] != f'{sha}  {CANDIDATE_NAME}\n'.encode('ascii'):
                raise ValueError('sidecar mismatch')
            manifest = json.loads(files[CANDIDATE_NAME + '.manifest.json'])
            required = {'id': NAME, 'name': NAME, 'version': '1.2.0', 'source': SOURCE,
                        'source_commit': SEALED_COMMIT, 'source_byte_basis': 'verified_git_blob_bytes',
                        'archive': f'dist/{CANDIDATE_NAME}', 'sha256': sha, 'status': 'PASS',
                        'status_scope': 'local_schema_and_archive_integrity_only', 'scope': 'local archive integrity only',
                        'platform': 'BLOCKED', 'workbuddy_install': 'NOT_TESTED', 'workbuddy_dialogue': 'NOT_TESTED'}
            if any(manifest.get(k) != v for k, v in required.items()):
                raise ValueError('manifest identity mismatch')
            names = sorted(f'{NAME}/{rel}' for rel in CANDIDATE_MEMBERS)
            with zipfile.ZipFile(io.BytesIO(files[CANDIDATE_NAME])) as archive:
                if archive.namelist() != names or archive.testzip() is not None:
                    raise ValueError('ZIP member set or CRC mismatch')
                payload = {member: archive.read(member) for member in names}
            rows = [{'path': name, 'size': len(raw), 'sha256': _sha(raw)} for name, raw in payload.items()]
            index = (json.dumps({'members': rows}, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()
            if manifest.get('members') != rows or manifest.get('payload_snapshot_sha256') != _sha(index):
                raise ValueError('manifest member size/hash mismatch')
            result['members'] = rows
            if sealed['status'] == 'PASS' and payload != expected:
                binding = 'FAIL'
                result['reason'] = 'original members differ from sealed Git blobs'
        except (ValueError, TypeError, AttributeError, KeyError, OSError, zipfile.BadZipFile, RuntimeError) as exc:
            integrity = binding = 'FAIL'
            result['reason'] = f'original ZIP/manifest/sidecar relationship invalid: {type(exc).__name__}'
    if binding == 'BLOCKED' and not result['reason']:
        result['reason'] = 'sealed historical objects unavailable'
    result.update(status=_status(integrity, binding), integrity=integrity, source_binding=binding,
                  seal=sealed, source_commit=SEALED_COMMIT, sha256=ORIGINAL_IDENTITIES[CANDIDATE_NAME][1])
    return result, files


def inspect_candidate(root: Path) -> dict:
    return _inspect_original(root, Path(root) / 'dist')[0]


def _file_identity(info: os.stat_result) -> dict:
    return {'device': info.st_dev, 'inode': info.st_ino}


def _rollback_created(created: list[tuple[Path, os.stat_result | None]]) -> dict:
    """Best-effort cleanup of our exclusive creations, with actual readback.

    Do not follow an unsafe path or remove a file whose ownership is uncertain.
    The identity check is not an atomic compare-and-unlink against concurrent
    external writers; a changed or inaccessible target requires manual review.
    """
    rows = {}
    for path, identity in reversed(created):
        entry = {'created_identity': _file_identity(identity) if identity is not None else None,
                 'status': 'UNVERIFIED', 'remaining': {'status': 'UNVERIFIED'}}
        rows[path.name] = entry
        removed = False
        try:
            current = _safe(path).lstat()
            if identity is not None and identity.st_ino and os.path.samestat(current, identity):
                try:
                    path.unlink()
                    removed = True
                except FileNotFoundError:
                    pass
                except OSError as exc:
                    entry['error'] = type(exc).__name__
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            entry['error'] = type(exc).__name__

        # Recheck the named target; successful unlink alone is not evidence of
        # absence, and a cleanup exception must not hide a residual file.
        try:
            current = _safe(path).lstat()
            entry['remaining'] = {'identity': _file_identity(current), 'size': current.st_size}
            if identity is None or not identity.st_ino:
                entry['status'] = 'UNVERIFIED'
            elif not os.path.samestat(current, identity):
                entry['status'] = 'NOT_OWNED'
            else:
                entry['status'] = 'RETAINED'
                # Only read a verified owned regular file, within its pinned
                # size bound. Never read bytes of someone else's replacement.
                if current.st_size <= ORIGINAL_IDENTITIES[path.name][0]:
                    with path.open('rb') as stream:
                        if os.path.samestat(os.fstat(stream.fileno()), identity):
                            data = stream.read(ORIGINAL_IDENTITIES[path.name][0] + 1)
                            after = os.fstat(stream.fileno())
                            if len(data) == after.st_size <= ORIGINAL_IDENTITIES[path.name][0]:
                                entry['remaining']['sha256'] = _sha(data)
                                entry['remaining']['size'] = len(data)
        except FileNotFoundError:
            entry.update(status='REMOVED' if removed else 'ABSENT', remaining=None)
        except (OSError, ValueError) as exc:
            entry.update(status='UNVERIFIED', readback_error=type(exc).__name__)
    complete = all(row['status'] in ('REMOVED', 'ABSENT') and 'error' not in row for row in rows.values())
    return {'status': 'PASS' if complete else 'FAIL', 'files': rows}


def restore_candidate(root: Path, source_dir: Path) -> dict:
    """Preflight all exact source and destination files before any exclusive write."""
    source, files = _inspect_original(root, source_dir)
    target, existing = _read_original(Path(root) / 'dist')
    if source['status'] != 'PASS' or target['status'] == 'FAIL':
        return {'status': _status(source['status'], 'FAIL' if target['status'] == 'FAIL' else 'PASS'),
                'source': source, 'target': target, 'restored': [], 'reason': 'restore preflight did not pass'}
    created = []
    readback = None
    stage, current_name = 'directory', None
    try:
        dist = _safe(_safe(root, directory=True) / 'dist', directory=True, missing=True)
        dist.mkdir(exist_ok=True)
        for name, data in files.items():
            stage, current_name = 'write', name
            path = _safe(dist / name, missing=True)
            if name in existing:
                if path.read_bytes() != data:
                    raise ValueError('target changed after preflight')
                continue
            with path.open('xb') as stream:
                # Record the creation even if obtaining its identity fails.
                created.append((path, None))
                created[-1] = (path, os.fstat(stream.fileno()))
                if stream.write(data) != len(data):
                    raise OSError('incomplete write')
        stage, current_name = 'readback', None
        readback = inspect_candidate(root)
        if readback['status'] != 'PASS':
            raise ValueError('restoration readback failed')
        return {**readback, 'restored': [p.name for p, _ in created], 'preserved': list(existing)}
    except (OSError, ValueError) as exc:
        return {'status': 'FAIL', 'restored': [], 'source': source, 'target': target,
                'readback': readback, 'rollback': _rollback_created(created),
                'failure': {'stage': stage, 'file': current_name, 'error': type(exc).__name__},
                'reason': f'exclusive restore failed: {type(exc).__name__}'}


_PROBE = '''import importlib.metadata as m, json, sys, pathlib
pins = json.loads(sys.argv[1])
versions = {}; locations = {}; errors = []; import_locations = []
for name in pins:
    try:
        dist = m.distribution(name)
        versions[name] = dist.version
        locations[name] = str(pathlib.Path(dist.locate_file('')).resolve())
    except m.PackageNotFoundError:
        versions[name] = None
try:
    import pytest, yaml
    imports = [pytest.__version__, yaml.__version__]
    import_locations = [str(pathlib.Path(module.__file__).resolve()) for module in (pytest, yaml)]
except Exception as exc:
    errors.append(type(exc).__name__); imports = []
print(json.dumps(dict(executable=sys.executable, platform=sys.platform, version=list(sys.version_info[:3]),
    prefix=sys.prefix, base_prefix=sys.base_prefix, dependencies=versions, locations=locations,
    imports=imports, import_locations=import_locations, errors=errors)))'''


def _probe(python: Path) -> dict:
    python = _safe(python)
    run = subprocess.run([str(python), '-I', '-B', '-c', _PROBE, json.dumps(PINS)],
                         env=_env(), capture_output=True, timeout=60)
    if run.returncode:
        raise OSError('interpreter probe failed')
    data = json.loads(run.stdout)
    if Path(data['executable']).absolute() != python:
        raise ValueError('interpreter executable mismatch')
    return data


def inspect_environment(python: Path) -> dict:
    """Read-only inspection, no pip invocation, installation or host changes."""
    try:
        data = _probe(python)
        result = {**data, 'interpreter': data['executable'], 'required_dependencies': dict(PINS)}
        prefix = Path(data['prefix']).resolve()
        isolated = (prefix != Path(data['base_prefix']).resolve()
                    and Path(data['executable']).parent.parent.resolve() == prefix)
        cfg = _safe(prefix / 'pyvenv.cfg', missing=True)
        isolated = isolated and cfg.is_file() and [
            line.partition('=')[2].strip().lower()
            for line in cfg.read_text(encoding='utf-8').splitlines()
            if line.partition('=')[0].strip().lower() == 'include-system-site-packages'] == ['false']
        valid = (data['platform'] == 'win32' and data['version'][:2] == [3, 12] and isolated
                 and data['dependencies'] == PINS and not data['errors']
                 and data['imports'] == [PINS['pytest'], PINS['PyYAML']]
                 and all(Path(p).is_relative_to(prefix)
                         for p in (*data['locations'].values(), *data['import_locations'])))
        result.update(status='PASS' if valid else 'BLOCKED', reason='' if valid else 'reference runtime or pinned isolated dependencies unavailable')
        return result
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        return {'status': 'BLOCKED', 'interpreter': str(python), 'reason': type(exc).__name__}


def prepare_environment(root: Path, python: Path) -> dict:
    """Explicitly create only the dedicated venv and install exact pinned wheels."""
    try:
        root = _safe(root, directory=True)
        python = _safe(python)
        data = _probe(python)
        if data['platform'] != 'win32' or data['version'][:2] != [3, 12]:
            return {'status': 'BLOCKED', 'interpreter': str(python), 'reason': 'Windows Python 3.12 required'}
        target = _safe(root / '.runtime' / NAME / 'venv', directory=True, missing=True)
        executable = target / 'Scripts' / 'python.exe'
        if target.exists():
            # Do not repair/reinstall/overwrite an existing environment implicitly.
            return inspect_environment(executable)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir()
        env = _env()
        create = subprocess.run([str(python), '-I', '-B', '-m', 'venv', str(target)],
                                env=env, capture_output=True, timeout=300)
        if create.returncode:
            return {'status': 'BLOCKED', 'interpreter': str(executable), 'reason': 'venv creation failed', 'exit_code': create.returncode}
        _safe(executable)
        # No external pip configuration, dependency resolution or source builds.
        env['PIP_CONFIG_FILE'] = os.devnull
        install = subprocess.run([str(executable), '-I', '-B', '-m', 'pip', '--isolated',
                                  '--disable-pip-version-check', '--no-input', 'install', '--no-deps',
                                  '--only-binary=:all:', '--index-url', 'https://pypi.org/simple',
                                  *(f'{name}=={version}' for name, version in PINS.items())],
                                 env=env, capture_output=True, timeout=300)
        result = inspect_environment(executable)
        result['install_exit_code'] = install.returncode
        if install.returncode:
            result.update(status='BLOCKED', reason='explicit fixed dependency installation failed')
        return result
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        return {'status': 'BLOCKED', 'interpreter': str(python), 'reason': type(exc).__name__}
