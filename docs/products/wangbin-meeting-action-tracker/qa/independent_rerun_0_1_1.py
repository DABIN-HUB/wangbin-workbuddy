"""Independent immutable 0.1.1 ZIP regression; keep historical 0.1.0 evidence untouched."""
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from typing import Any

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ARCHIVE = ROOT / 'dist/wangbin-meeting-action-tracker-0.1.1-skill-candidate.zip'
OLD = ROOT / 'dist/wangbin-meeting-action-tracker-0.1.0-skill-candidate.zip'
EXPECTED = '5f5f0bc86ca469c89d758010194d8768e27badc96584791495e4b71c8ef745ae'
OLD_EXPECTED = 'e9ce10c7979bdd510e08b20e1bb877fc28f7e66ef437c05b5e1a19117c0eac20'
EVIDENCE = HERE / 'qa-evidence-0.1.1.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    spec = importlib.util.spec_from_file_location('original_independent_probe', HERE / 'independent_probe.py')
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    setattr(probe, 'DIST', ARCHIVE)
    setattr(probe, 'SIDECAR', Path(str(ARCHIVE) + '.sha256'))
    setattr(probe, 'MANIFEST', Path(str(ARCHIVE) + '.manifest.json'))
    probe.records.clear()
    records = probe.main()  # 38 original independent checks, on fresh 0.1.1 extraction
    def check(case, expected, actual, passed):
        records.append({'case': case, 'expected': expected, 'actual': actual, 'verdict': 'PASS' if passed else 'FAIL'})
    manifest = json.loads(probe.MANIFEST.read_text(encoding='utf-8'))
    sidecar = probe.SIDECAR.read_text(encoding='utf-8').strip()
    check('0.1.1 exact archive and manifest', {'archive_sha256': EXPECTED, 'id': 'wangbin-meeting-action-tracker', 'version': '0.1.1', 'member_count': 3}, {'archive_sha256': sha(ARCHIVE), 'manifest': manifest}, sha(ARCHIVE) == EXPECTED and manifest['sha256'] == EXPECTED and manifest['id'] == 'wangbin-meeting-action-tracker' and manifest['version'] == '0.1.1' and len(manifest['members']) == 3)
    check('0.1.1 exact sidecar', EXPECTED + '  ' + ARCHIVE.name, sidecar, sidecar == EXPECTED + '  ' + ARCHIVE.name)
    check('historical 0.1.0 archive immutable', OLD_EXPECTED, sha(OLD), sha(OLD) == OLD_EXPECTED)
    with tempfile.TemporaryDirectory(prefix='meeting-rerun-', dir=os.environ.get('TMPDIR')) as tmp:
        d = Path(tmp)
        with zipfile.ZipFile(ARCHIVE) as archive:
            bad = archive.testzip()
            archive.extractall(d / 'clean')
        check('0.1.1 ZipFile testzip', None, bad, bad is None)
        script = d / 'clean/wangbin-meeting-action-tracker/scripts/track.py'
        headers = probe.HEADERS[0]
        old = d / 'previous.csv'
        with old.open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerow(['T01','整理演练清单','王工','已确认','2026-11-05','已确认','进行中','','','','old.csv:行2',''])
            w.writerow(['T02','准备演练培训','','','','','待执行','','','','old.csv:行3',''])
        before = sha(old)
        def run(label: str, text: str, previous: Path = old) -> dict[str, Any]:
            folder = d / label
            folder.mkdir()
            meeting = folder / 'meeting.md'
            meeting.write_text(text, encoding='utf-8')
            output = folder / 'output'
            output.mkdir()
            command = [sys.executable, str(script), '--meeting-file', str(meeting), '--previous-tasks', str(previous), '--project-name', '蓝桥演练', '--response-mode', 'export', '--output-dir', str(output)]
            p = subprocess.run(command, capture_output=True, text=True)
            data: dict[str, Any]
            try:
                data = json.loads(p.stdout if p.returncode == 0 else p.stderr)
            except json.JSONDecodeError:
                data = {'stdout': p.stdout[-1000:], 'stderr': p.stderr[-1000:]}
            data['exit'] = p.returncode
            data['command'] = command
            if p.returncode == 0 and data.get('xlsx'):
                wb = load_workbook(data['xlsx'], read_only=True, data_only=False)
                data['sheets'] = {n: [dict(zip([v.value for v in wb[n][1]], row)) for row in list(wb[n].values)[1:]] for n in wb.sheetnames}
                data['headers'] = {n: [v.value for v in wb[n][1]] for n in wb.sheetnames}
                wb.close()
            return data
        base = '2026-11-06 蓝桥演练例会。T02 经会议明确取消，原因：模拟需求撤回。新增事项：检查演练接口 T03；建议由李工负责，尚未获其接受。'
        core = run('core-cancel-simulation', base)
        tasks = {t['task_id']: t for t in core.get('sheets', {}).get('当前任务', [])}
        history = core.get('sheets', {}).get('状态历史', [])
        cancellations = [event for event in history if event.get('task_id') == 'T02' and event.get('事件类型') == '取消']
        actual = {'exit': core['exit'], 'T02': tasks.get('T02'), 'cancellation_events': cancellations, 'pending': core.get('sheets', {}).get('待确认事项'), 'meeting': base, 'command': core['command']}
        check('D1 explicit cancel with 模拟 reason', 'T02 取消; event 原值待执行→新值取消 with source; no overdue', actual, core['exit'] == 0 and tasks.get('T02', {}).get('执行状态') == '取消' and tasks.get('T02', {}).get('是否逾期') == '否' and any(e.get('原值') == '待执行' and e.get('新值') == '取消' and e.get('来源') for e in cancellations))
        for index, word in enumerate(('拟取消', '考虑取消', '建议取消')):
            control = run('proposal-' + str(index), '2026-11-06 蓝桥演练例会。T02 ' + word + '，尚未最终决定。')
            t = next((t for t in control.get('sheets', {}).get('当前任务', []) if t['task_id'] == 'T02'), {})
            events = [e for e in control.get('sheets', {}).get('状态历史', []) if e.get('task_id') == 'T02' and e.get('事件类型') == '取消']
            check('D1 proposal control ' + word, 'T02 remains 待执行; no cancellation event; pending confirmation', {'exit':control['exit'], 'T02':t, 'cancel_events':events, 'pending':control.get('sheets', {}).get('待确认事项'), 'command':control['command']}, control['exit'] == 0 and t.get('执行状态') == '待执行' and not events and bool(control.get('sheets', {}).get('待确认事项')))
        check('supplemental source CSV immutable', before, sha(old), before == sha(old))
    EVIDENCE.write_text(json.dumps(records, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    print(json.dumps({'cases': len(records), 'passed': sum(x['verdict'] == 'PASS' for x in records), 'failed': [x['case'] for x in records if x['verdict'] == 'FAIL'], 'evidence': str(EVIDENCE)}, ensure_ascii=False))
    return 1 if any(x['verdict'] == 'FAIL' for x in records) else 0

if __name__ == '__main__':
    sys.exit(main())
