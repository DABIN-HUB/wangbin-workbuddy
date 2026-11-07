"""Developer-only replay of independent Q04 fixture against the new immutable candidate.

The 0.1.2 independent QA evidence is never modified. This is not independent QA.
"""
import importlib.util
from pathlib import Path
from typing import Any, cast

qa = Path(__file__).with_name('qa') / 'audit_r1_q04_candidate.py'
spec = importlib.util.spec_from_file_location('q04_original', qa)
assert spec is not None and spec.loader is not None
probe = cast(Any, importlib.util.module_from_spec(spec))
spec.loader.exec_module(probe)
probe.ZIP = probe.ROOT / 'dist/wangbin-meeting-action-tracker-0.1.3-skill-candidate.zip'
probe.SHA = '7a336890accd132e69deff91a60b4e4cd30b7d7ce144862f778fa6e5023b2a6d'
probe.SCRATCH = Path.home() / 'AppData/Local/hermes/profiles/wb-developer/cache/scratch'
probe.REPORT = probe.SCRATCH / 'mtg-fix-r1-26.json'
# The original archive metadata assertions pin the old version; use a separate
# check on the newly packaged archive before invoking its existing business cases.
def assert_new_zip(base):
    import hashlib
    import json
    import zipfile
    assert hashlib.sha256(probe.ZIP.read_bytes()).hexdigest() == probe.SHA
    manifest = json.loads(probe.ZIP.with_suffix('.zip.manifest.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '0.1.3' and manifest['sha256'] == probe.SHA
    assert probe.ZIP.with_suffix('.zip.sha256').read_text(encoding='utf-8').split()[0] == probe.SHA
    with zipfile.ZipFile(probe.ZIP) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names)) == len(manifest['members']) == 4
        for member in manifest['members']:
            payload = archive.read(member['path'])
            assert hashlib.sha256(payload).hexdigest() == member['sha256']
            assert hashlib.sha256((probe.ROOT / 'packages/skills' / member['path']).read_bytes()).hexdigest() == member['sha256']
        archive.extractall(base / 'clean')
    return names, manifest

probe.assert_zip = assert_new_zip
if __name__ == '__main__':
    probe.main()
    import json
    result = json.loads(probe.REPORT.read_text(encoding='utf-8'))
    assert result['pass_count'] == result['total_count'] == 26, [(x['id'], x.get('failure')) for x in result['cases'] if not x.get('pass')]
