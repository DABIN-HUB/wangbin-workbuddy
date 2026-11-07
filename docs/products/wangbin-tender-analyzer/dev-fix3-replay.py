"""Replay frozen QA 53-case definitions, not QA's old 0.2.7 package or outputs.

Developer-only. Use `python dev-fix3-replay.py <absolute-final-zip> <new-scratch>`.
The original QA probe remains byte-for-byte unchanged. Never reuse an output root.
"""
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
original = (Path(__file__).with_name('qa-audit-r1-new-027-probe.py')).read_text(encoding='utf-8')
source_mode = sys.argv[1] == 'source'
archive = (root / 'dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip' if source_mode
           else Path(sys.argv[1]).resolve())
scratch = Path(sys.argv[2]).resolve()
assert archive.is_file() and archive.parent == root / 'dist'
assert not scratch.exists(), 'refuse to overwrite evidence'
assert scratch.is_relative_to(Path.home() / 'AppData/Local/hermes/profiles/wb-developer/cache/scratch'), 'scratch must be inside authorized developer scratch'
manifest = json.loads(Path(str(archive) + '.manifest.json').read_text(encoding='utf-8'))
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
assert manifest['sha256'] == digest and digest in Path(str(archive) + '.sha256').read_text(encoding='utf-8')
assert manifest['version'] == archive.name.split('-skill-candidate.zip')[0].split('analyzer-')[-1]
assert len(manifest['members']) == len({m['path'] for m in manifest['members']})
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and set(z.namelist()) == {m['path'] for m in manifest['members']}
    for item in manifest['members']:
        assert '..' not in Path(item['path']).parts
        raw = z.read(item['path'])
        assert len(raw) == item['size'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    scratch.mkdir(parents=True)
    z.extractall(scratch / 'extract')
source = (root / 'packages/skills/wangbin-tender-analyzer' if source_mode else
          scratch / 'extract/wangbin-tender-analyzer')
script = source / 'scripts/check_response.py'
script_sha = next(m['sha256'] for m in manifest['members'] if m['path'].endswith('/scripts/check_response.py'))
if not source_mode:
    assert hashlib.sha256(script.read_bytes()).hexdigest() == script_sha
# The original probe defines exactly 53 cases and their original expectations.
# Only its setup/packaging lines are substituted; all case definitions/assertions stay untouched.
preamble = """import csv, hashlib, json, os, shutil, subprocess, sys, zipfile
from collections import Counter
from pathlib import Path
from openpyxl import Workbook, load_workbook
ROOT=Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check')
SCR=Path(%r)
ZIP=Path(%r)
manifest=json.loads(Path(str(ZIP)+'.manifest.json').read_text(encoding='utf-8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
BASE=Path(%r)
SCRIPT=BASE/'scripts/check_response.py'
""" % (str(scratch), str(archive), str(source))
marker = '# Each case has its own physical inputs and dedicated empty output directory.'
assert original.count(marker) == 1 and 'assert len(cases)==53' in original
program = preamble + original.split(marker, 1)[1]
exec(compile(program, str(Path(__file__).with_name('qa-audit-r1-new-027-probe.py')), 'exec'), {'__name__': '__main__'})
results = json.loads((scratch / 'results.json').read_text(encoding='utf-8'))
failures = [(r['id'], r['issues']) for r in results['cases'] if r['issues']]
print('DEV_REPLAY', len(results['cases']) - len(failures), '/', len(results['cases']), 'FAILURES', failures, 'LEGACY', results['legacy']['match'], 'SHA256', digest)
if failures or not results['legacy']['match']:
    raise SystemExit(1)
