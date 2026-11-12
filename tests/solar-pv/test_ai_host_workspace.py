"""Host-only crash lock and wrapper regressions; no model calls."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.reporting.host_workspace import HostWorkspace


@pytest.mark.parametrize('target', ['host-authorization.json', 'host-operation.json', 'state.json', 'CH08-1-result.json'])
def test_kernel_lock_released_after_real_process_timeout(tmp_path, target):
    script = ('import sys,time;from wangbin_solar_pv.reporting.host_workspace import HostWorkspace;'
              's=HostWorkspace(sys.argv[1]);lock=s.lock(sys.argv[2]);lock.__enter__();'
              'print("LOCK_ACQUIRED",flush=True);time.sleep(30)')
    with pytest.raises(subprocess.TimeoutExpired) as failed:
        subprocess.run([sys.executable, '-c', script, str(tmp_path), target],
                       capture_output=True, timeout=3)
    assert b'LOCK_ACQUIRED' in failed.value.stdout
    assert (tmp_path / (target + '.host-lock')).exists()
    with HostWorkspace(tmp_path).lock(target):
        pass


def test_active_lock_not_stolen_and_unknown_legacy_lock_retained(tmp_path):
    workspace = HostWorkspace(tmp_path)
    with workspace.lock('state.json'):
        with pytest.raises(ContractError, match='STATE_LOCKED'):
            with HostWorkspace(tmp_path).lock('state.json'):
                pytest.fail('stole an active lock')
    (tmp_path / 'state.json.lock').write_bytes(b'unknown-owner')
    with pytest.raises(ContractError, match='HOST_LEGACY_LOCK_REQUIRES_REVIEW'):
        with workspace.lock('state.json'):
            pytest.fail('reclaimed a legacy lock')
    assert (tmp_path / 'state.json.lock').read_bytes() == b'unknown-owner'


@pytest.fixture
def wrapper():
    path = Path(__file__).resolve().parents[2] / 'packages/skills/wangbin-solar-pv-prestudy/scripts/run_ai_chapter.py'
    spec = importlib.util.spec_from_file_location('solar_host_wrapper', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('root_arg', ['relative-project', 'project with spaces'])
def test_wrapper_binds_relative_workspace_before_child_cwd(wrapper, tmp_path, monkeypatch, root_arg):
    monkeypatch.chdir(tmp_path)
    captured = {}
    def fake_run(command, **kwargs):
        captured.update(command=command, **kwargs)
        return SimpleNamespace(returncode=3, stdout='{"status":"MODEL_INTEGRATION_BLOCKED"}')
    monkeypatch.setattr(wrapper.subprocess, 'run', fake_run)
    assert wrapper.main(['status', '--workspace', root_arg]) == 3
    command = captured['command']
    assert command[command.index('--workspace') + 1] == str(tmp_path / root_arg)
    assert '-I' in command
    assert 'PYTHONPATH' not in captured['env'] and 'PYTHONHOME' not in captured['env']
    assert captured['timeout'] == 180


def test_wrapper_traversal_not_normalized(wrapper, monkeypatch, capsys):
    monkeypatch.setattr(wrapper.subprocess, 'run', lambda *a, **k: pytest.fail('must not spawn'))
    assert wrapper.main(['prepare', '--workspace', '../outside']) == 2
    assert json.loads(capsys.readouterr().out)['code'] == 'PATH_TRAVERSAL'


def test_wrapper_reports_real_command_timeout_without_remote_cancellation(wrapper, monkeypatch, capsys):
    def timed_out(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs['timeout'])
    monkeypatch.setattr(wrapper.subprocess, 'run', timed_out)
    assert wrapper.main(['status', '--command-timeout', '1']) == 2
    result = json.loads(capsys.readouterr().out)
    assert result['code'] == 'HOST_COMMAND_TIMEOUT'
    assert result['remote_model_cancelled'] == 'NOT_EXPOSED_BY_HOST'
