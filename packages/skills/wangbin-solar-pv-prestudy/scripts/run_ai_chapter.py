#!/usr/bin/env python3
"""Run the installed host protocol with a bounded local command lifetime."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('--command-timeout', type=int, default=180)
    parser.add_argument('--workspace')
    args, forwarded = parser.parse_known_args(argv)
    if not 1 <= args.command_timeout <= 180:
        print(json.dumps({'status': 'BLOCKED', 'code': 'HOST_COMMAND_BUDGET'}))
        return 2
    env = os.environ.copy()
    # User-facing execution must resolve installed packages, not a developer tree.
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    if args.workspace:
        if '..' in Path(args.workspace).parts:
            print(json.dumps({'status': 'BLOCKED', 'code': 'PATH_TRAVERSAL'}))
            return 2
        # Bind relative roots to the caller's cwd before changing child cwd.
        forwarded += ['--workspace', os.path.abspath(args.workspace)]
    baseline = Path(__file__).resolve().parents[1] / 'references' / 'baseline'
    command = [sys.executable, '-I', '-m', 'wangbin_solar_pv.reporting.host_session',
               *forwarded, '--baseline-dir', str(baseline)]
    try:
        result = subprocess.run(command, cwd=baseline, env=env, capture_output=True,
                                text=True, encoding='utf8', timeout=args.command_timeout)
    except subprocess.TimeoutExpired:
        print(json.dumps({'status': 'BLOCKED', 'code': 'HOST_COMMAND_TIMEOUT',
                          'remote_model_cancelled': 'NOT_EXPOSED_BY_HOST'}))
        return 2
    except OSError:
        print(json.dumps({'status': 'BLOCKED', 'code': 'INSTALLED_ENGINE_UNAVAILABLE'}))
        return 2
    if '--help' in forwarded and result.returncode == 0:
        print(result.stdout)
        return 0
    try:
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise ValueError()
    except (ValueError, TypeError):
        print(json.dumps({'status': 'BLOCKED', 'code': 'INSTALLED_ENGINE_UNAVAILABLE_OR_INVALID_RESPONSE'}))
        return 2
    # Do not leak arbitrary interpreter/provider errors to the host transcript.
    print(json.dumps(payload, ensure_ascii=False))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
