"""Isolated support contracts; synthetic artifacts never represent the real 1.2.0 original."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from tooling import consultant_regression_support as support


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', *args], cwd=repo, env=env).strip()


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    repo.mkdir()
    _git(repo, 'init', '-q')
    _git(repo, 'config', 'user.name', 'Synthetic')
    _git(repo, 'config', 'user.email', 'synthetic@example.invalid')
    _git(repo, 'config', 'core.autocrlf', 'false')
    paths = ('.codebuddy-plugin/plugin.json', 'agents/wangbin-software-consultant.md',
             'avatars/expert.png', 'README.md', 'LICENSE',
             'skills/wangbin-estimate-calculator/SKILL.md',
             'skills/wangbin-estimate-calculator/scripts/estimator.py',
             'skills/wangbin-estimate-calculator/references/input-output-contract.md',
             'skills/wangbin-estimate-calculator/LICENSE')
    expected = {}
    for rel in paths:
        data = ('SYNTHETIC ' + rel + '\n').encode()
        path = repo / support.SOURCE / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        expected[f'{support.NAME}/{rel}'] = data
    _git(repo, 'add', '--', support.SOURCE)
    _git(repo, 'commit', '-qm', 'synthetic fixture only')
    commit = _git(repo, 'rev-parse', 'HEAD').decode()
    monkeypatch.setattr(support, 'LEGACY_COMMIT', commit)
    monkeypatch.setattr(support, 'PRICE_COMMIT', commit)
    monkeypatch.setattr(support, 'SEALED_COMMIT', commit)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as z:
        for member, data in sorted(expected.items()):
            z.writestr(member, data)
    raw = archive.getvalue()
    rows = [{'path': member, 'size': len(data), 'sha256': _sha(data)}
            for member, data in sorted(expected.items())]
    def dump(data):
        return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()
    manifest = dump({'id': support.NAME, 'name': support.NAME, 'version': '1.2.0',
                     'source': support.SOURCE, 'source_commit': commit,
                     'source_byte_basis': 'verified_git_blob_bytes',
                     'archive': f'dist/{support.CANDIDATE_NAME}',
                     'status': 'PASS', 'status_scope': 'local_schema_and_archive_integrity_only',
                     'scope': 'local archive integrity only', 'platform': 'BLOCKED',
                     'workbuddy_install': 'NOT_TESTED', 'workbuddy_dialogue': 'NOT_TESTED',
                     'sha256': _sha(raw), 'members': rows,
                     'payload_snapshot_sha256': _sha(dump({'members': rows}))})
    sidecar = f'{_sha(raw)}  {support.CANDIDATE_NAME}\n'.encode('ascii')
    artifacts = {support.CANDIDATE_NAME: raw, support.CANDIDATE_NAME + '.manifest.json': manifest,
                 support.CANDIDATE_NAME + '.sha256': sidecar}
    monkeypatch.setattr(support, 'ORIGINAL_IDENTITIES', {n: (len(b), _sha(b)) for n, b in artifacts.items()})
    source = tmp_path / 'trusted'
    source.mkdir()
    for n, b in artifacts.items():
        (source / n).write_bytes(b)
    return repo, source, artifacts


def test_history_requires_actual_commit_and_all_regular_blobs(synthetic, monkeypatch):
    repo, _, _ = synthetic
    result = support.inspect_history(repo)
    assert {k: v['status'] for k, v in result.items()} == {'legacy': 'PASS', 'price': 'PASS', 'sealed': 'PASS'}
    # Worktree changes cannot hide or substitute historical Git bytes.
    (repo / support.SOURCE / 'README.md').unlink()
    assert support.inspect_history(repo)['sealed']['status'] == 'PASS'
    monkeypatch.setattr(support, 'LEGACY_COMMIT', '0' * 40)
    monkeypatch.setattr(support, 'PRICE_COMMIT', _git(repo, 'rev-parse', 'HEAD:' + support.SOURCE + '/LICENSE').decode())
    states = support.inspect_history(repo)
    assert states['legacy']['status'] == 'BLOCKED'
    assert states['price']['status'] == 'FAIL'
    assert states['sealed']['status'] == 'PASS'


def test_missing_historical_blob_detected_without_worktree_substitution(synthetic):
    repo, _, _ = synthetic
    oid = _git(repo, 'rev-parse', 'HEAD:' + support.SOURCE + '/README.md').decode()
    obj = repo / '.git' / 'objects' / oid[:2] / oid[2:]
    obj.chmod(0o600)  # Git loose objects are read-only on Windows.
    obj.unlink()
    result = support.inspect_history(repo)
    assert result['legacy']['status'] == 'BLOCKED'
    assert result['sealed']['status'] == 'BLOCKED'
    assert result['price']['status'] == 'PASS'


def test_history_inspection_disables_git_transports(synthetic, monkeypatch):
    repo, _, _ = synthetic
    _git(repo, 'config', 'protocol.file.allow', 'always')
    monkeypatch.setenv('GIT_ALLOW_PROTOCOL', 'file')
    monkeypatch.setenv('GIT_NO_LAZY_FETCH', '0')
    real_run = subprocess.run
    calls = []

    def observe(argv, **kwargs):
        calls.append((argv, kwargs['env']))
        return real_run(argv, **kwargs)

    monkeypatch.setattr(support.subprocess, 'run', observe)
    assert support.inspect_history(repo)['sealed']['status'] == 'PASS'
    assert support.inspect_candidate(repo)['status'] == 'BLOCKED'
    assert calls
    for argv, env in calls:
        assert env['GIT_NO_LAZY_FETCH'] == '1'
        assert 'protocol.allow=never' in argv
        assert env.get('GIT_ALLOW_PROTOCOL') == ''
    # Exercise the same read-only runner against a harmless local transport:
    # the per-protocol repository config cannot override the offline policy.
    attempt = support._git(repo, 'ls-remote', repo.as_posix())
    assert attempt.returncode != 0


def test_original_missing_partial_corrupt_and_restore(synthetic):
    repo, source, artifacts = synthetic
    dist = repo / 'dist'
    assert support.inspect_candidate(repo)['status'] == 'BLOCKED'
    assert not dist.exists()
    dist.mkdir()
    first = dist / support.CANDIDATE_NAME
    first.write_bytes(artifacts[first.name])
    before = first.stat().st_mtime_ns
    assert support.inspect_candidate(repo)['status'] == 'BLOCKED'
    assert support.restore_candidate(repo, source)['status'] == 'PASS'
    assert first.stat().st_mtime_ns == before
    assert {p.name: p.read_bytes() for p in dist.iterdir()} == artifacts
    assert support.restore_candidate(repo, source)['status'] == 'PASS'
    assert support.inspect_candidate(repo)['source_binding'] == 'PASS'
    first.write_bytes(b'wrong')
    assert support.inspect_candidate(repo)['status'] == 'FAIL'
    assert support.restore_candidate(repo, source)['status'] == 'FAIL'
    assert first.read_bytes() == b'wrong'


@pytest.mark.parametrize('rollback_fault', ['none', 'unlink', 'replaced'])
def test_restore_failed_readback_reports_actual_rollback(synthetic, monkeypatch, rollback_fault):
    repo, source, artifacts = synthetic
    dist = repo / 'dist'
    dist.mkdir()
    first = dist / support.CANDIDATE_NAME
    first.write_bytes(artifacts[first.name])
    before = first.stat()
    failed = dist / (support.CANDIDATE_NAME + '.manifest.json')
    sidecar = dist / (support.CANDIDATE_NAME + '.sha256')
    real_unlink = Path.unlink
    replacement = b'SYNTHETIC independent replacement'

    def failed_readback(root):
        assert failed.read_bytes() == artifacts[failed.name]
        assert sidecar.read_bytes() == artifacts[sidecar.name]
        if rollback_fault == 'replaced':
            # Move the original inode aside, then install an unrelated file.
            # The rollback must not remove either of those files.
            failed.rename(dist / 'moved-by-other-writer')
            failed.write_bytes(replacement)
        return {'status': 'FAIL', 'reason': 'synthetic readback failure'}

    def unlink(path, *args, **kwargs):
        if rollback_fault == 'unlink' and path == failed:
            raise PermissionError('synthetic cleanup error')
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(support, 'inspect_candidate', failed_readback)
    monkeypatch.setattr(Path, 'unlink', unlink)
    result = support.restore_candidate(repo, source)
    assert result['status'] == 'FAIL' and result['restored'] == []
    assert result['readback']['reason'] == 'synthetic readback failure'
    assert result['rollback']['files'][sidecar.name]['status'] == 'REMOVED'
    assert not sidecar.exists()
    assert first.read_bytes() == artifacts[first.name]
    assert os.path.samestat(first.stat(), before) and first.stat().st_mtime_ns == before.st_mtime_ns
    entry = result['rollback']['files'][failed.name]
    if rollback_fault == 'none':
        assert result['rollback']['status'] == 'PASS'
        assert entry['status'] == 'REMOVED' and not failed.exists()
    elif rollback_fault == 'unlink':
        assert result['rollback']['status'] == 'FAIL'
        assert entry['status'] == 'RETAINED' and entry['error'] == 'PermissionError'
        assert entry['remaining']['sha256'] == _sha(artifacts[failed.name])
        assert failed.read_bytes() == artifacts[failed.name]
    else:
        assert result['rollback']['status'] == 'FAIL'
        assert entry['status'] == 'NOT_OWNED' and entry['remaining']['identity'] != entry['created_identity']
        assert failed.read_bytes() == replacement
        assert (dist / 'moved-by-other-writer').read_bytes() == artifacts[failed.name]


def test_restore_exclusive_write_collision_rolls_back_only_own_files(synthetic, monkeypatch):
    repo, source, artifacts = synthetic
    dist = repo / 'dist'
    original = dist / support.CANDIDATE_NAME
    dist.mkdir()
    original.write_bytes(artifacts[original.name])
    manifest = dist / (support.CANDIDATE_NAME + '.manifest.json')
    sidecar = dist / (support.CANDIDATE_NAME + '.sha256')
    real_open = Path.open

    def collide(path, mode='r', *args, **kwargs):
        if path == sidecar and mode == 'xb':
            # Another writer claims the target after preflight. The genuine
            # exclusive open must fail without overwriting that writer's data.
            assert manifest.read_bytes() == artifacts[manifest.name]
            with real_open(path, 'xb') as stream:
                stream.write(b'SYNTHETIC concurrent file')
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', collide)
    result = support.restore_candidate(repo, source)
    assert result['status'] == 'FAIL' and result['restored'] == []
    assert result['readback'] is None
    assert result['failure'] == {'stage': 'write', 'file': sidecar.name, 'error': 'FileExistsError'}
    assert result['rollback']['status'] == 'PASS'
    assert set(result['rollback']['files']) == {manifest.name}
    assert result['rollback']['files'][manifest.name]['status'] == 'REMOVED'
    assert not manifest.exists()
    assert original.read_bytes() == artifacts[original.name]
    assert sidecar.read_bytes() == b'SYNTHETIC concurrent file'


@pytest.mark.parametrize('bad', ['source', 'target'])
def test_restore_preflights_entire_set_before_writing(synthetic, bad):
    repo, source, artifacts = synthetic
    dist = repo / 'dist'
    dist.mkdir()
    name = support.CANDIDATE_NAME + '.sha256'
    chosen = source if bad == 'source' else dist
    (chosen / name).write_bytes(b'bad sidecar')
    expected = {p.name: p.read_bytes() for p in dist.iterdir()}
    assert support.restore_candidate(repo, source)['status'] == 'FAIL'
    assert {p.name: p.read_bytes() for p in dist.iterdir()} == expected


def test_integrity_independent_from_missing_seal(synthetic):
    repo, source, _ = synthetic
    assert support.restore_candidate(repo, source)['status'] == 'PASS'
    oid = support.SEALED_COMMIT
    obj = repo / '.git' / 'objects' / oid[:2] / oid[2:]
    obj.chmod(0o600)
    obj.unlink()
    result = support.inspect_candidate(repo)
    assert result['integrity'] == 'PASS'
    assert result['source_binding'] == 'BLOCKED'
    assert result['status'] == 'BLOCKED'


def test_manifest_member_relationship_checked_not_just_file_hash(synthetic, monkeypatch):
    repo, source, _ = synthetic
    filename = support.CANDIDATE_NAME + '.manifest.json'
    path = source / filename
    manifest = json.loads(path.read_bytes())
    manifest['members'][0]['size'] += 1
    raw = json.dumps(manifest).encode()
    path.write_bytes(raw)
    # Synthetic test only: pin the modified manifest so relationship validation must catch it.
    monkeypatch.setitem(support.ORIGINAL_IDENTITIES, filename, (len(raw), _sha(raw)))
    assert support.restore_candidate(repo, source)['status'] == 'FAIL'
    assert not (repo / 'dist').exists()


def test_wrong_remote_refuses_preparation_without_fetch(synthetic, monkeypatch):
    repo, _, _ = synthetic
    monkeypatch.setattr(support, 'LEGACY_COMMIT', '0' * 40)
    _git(repo, 'remote', 'add', 'origin', 'https://example.invalid/not-authorized.git')
    result = support.prepare_history(repo)
    assert result['status'] == 'FAIL'
    assert not (repo / '.git' / 'FETCH_HEAD').exists()
    assert _git(repo, 'remote', 'get-url', 'origin') == b'https://example.invalid/not-authorized.git'


def test_explicit_fetch_of_synthetic_authorized_branch_preserves_refs(synthetic, tmp_path, monkeypatch):
    upstream, _, _ = synthetic
    _git(upstream, 'branch', 'expert/software-consultant')
    _git(upstream, 'checkout', 'expert/software-consultant')
    _git(upstream, 'commit', '--allow-empty', '-qm', 'synthetic tip')
    origin = upstream.as_posix()
    monkeypatch.setattr(support, 'ORIGIN', origin)
    clone = tmp_path / 'shallow'
    _git(tmp_path, 'clone', '--no-local', '--depth=1', '--branch', 'expert/software-consultant', origin, str(clone))
    before = _git(clone, 'show-ref')
    head = _git(clone, 'rev-parse', 'HEAD')
    assert support.inspect_history(clone)['sealed']['status'] == 'BLOCKED'
    assert _git(clone, 'show-ref') == before
    result = support.prepare_history(clone)
    assert result['status'] == 'PASS', result
    assert result['fetched'] is True
    assert _git(clone, 'show-ref') == before
    assert _git(clone, 'rev-parse', 'HEAD') == head
    assert not (clone / '.git' / 'FETCH_HEAD').exists()
    assert not _git(clone, 'status', '--porcelain')


def test_missing_interpreter_readonly_and_preparation(synthetic):
    repo, _, _ = synthetic
    missing = repo / 'missing-python.exe'
    assert support.inspect_environment(missing)['status'] == 'BLOCKED'
    assert support.prepare_environment(repo, missing)['status'] == 'BLOCKED'
    assert not (repo / '.runtime').exists()


def test_inspection_does_not_accept_global_environment():
    # Even when the base interpreter itself has the right dependency versions,
    # absence of an isolated venv must block reference-environment acceptance.
    assert support.inspect_environment(Path(sys._base_executable))['status'] == 'BLOCKED'


def test_explicit_environment_prepare_uses_only_new_venv_and_pinned_install(synthetic, monkeypatch):
    repo, _, _ = synthetic
    base = Path(sys._base_executable)
    target = repo / '.runtime' / support.NAME / 'venv'
    actual_run = subprocess.run
    installs = []

    def offline_install_boundary(argv, **kwargs):
        if '-m' in argv and argv[argv.index('-m') + 1] == 'pip':
            installs.append(argv)
            # Simulate the external package server unavailable. Do not install
            # or fabricate dependencies: the actual fresh venv must be BLOCKED.
            return subprocess.CompletedProcess(argv, 1, b'', b'SYNTHETIC offline')
        return actual_run(argv, **kwargs)

    monkeypatch.setattr(support.subprocess, 'run', offline_install_boundary)
    result = support.prepare_environment(repo, base)
    if sys.platform != 'win32' or sys.version_info[:2] != (3, 12):
        assert result['status'] == 'BLOCKED' and not target.exists() and not installs
        return
    python = target / 'Scripts' / 'python.exe'
    assert result['status'] == 'BLOCKED' and result['install_exit_code'] == 1
    assert python.is_file() and Path(result['interpreter']) == python
    assert len(installs) == 1
    args = installs[0]
    assert Path(args[0]) == python
    assert '--no-deps' in args and '--only-binary=:all:' in args
    assert set(arg for arg in args if '==' in arg) == {
        'pytest==8.4.2', 'PyYAML==6.0.3', 'colorama==0.4.6', 'iniconfig==2.3.1',
        'packaging==26.3', 'pluggy==1.7.0', 'Pygments==2.21.0'}
    assert support.inspect_environment(python)['status'] == 'BLOCKED'
    assert support.prepare_environment(repo, base)['status'] == 'BLOCKED'
    assert len(installs) == 1  # Existing partial venv is not silently repaired.
    assert not (repo / '.venv').exists()


def test_restore_rejects_target_directory_link(synthetic, tmp_path):
    repo, source, _ = synthetic
    other = tmp_path / 'outside'
    other.mkdir()
    link = repo / 'dist'
    if sys.platform == 'win32':
        # Junctions can be created without admin symlink privileges.
        run = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(other)], capture_output=True)
        assert run.returncode == 0, run.stderr
    else:
        link.symlink_to(other, target_is_directory=True)
    try:
        assert support.restore_candidate(repo, source)['status'] == 'FAIL'
        assert not list(other.iterdir())
    finally:
        link.rmdir() if sys.platform == 'win32' else link.unlink()
