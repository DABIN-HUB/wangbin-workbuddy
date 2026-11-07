"""Developer-only replay of preserved QA 35 cases against a new immutable ZIP.

Never modifies the independent QA probe/report; outputs remain in developer scratch.
"""
import json
import os
import csv
import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from openpyxl import load_workbook

qa = Path(__file__).with_name('qa') / 'audit_r1_q04_rerun_013.py'
source = qa.read_text(encoding='utf-8')
source = source.replace("0.1.3-skill-candidate.zip'", "0.1.4-skill-candidate.zip'")
source = source.replace("SHA = '7a336890accd132e69deff91a60b4e4cd30b7d7ce144862f778fa6e5023b2a6d'", "SHA = '8b45ac776227db6128f6e6c60e2f345604e63fbb52e693b4bd3dadccb2a45193'")
source = source.replace("manifest['version'] == '0.1.3'", "manifest['version'] == '0.1.4'")
source = source.replace("meta['version'] == '0.1.3'", "meta['version'] == '0.1.4'")
source = source.replace("REPORT = Path(__file__).with_name('audit-r1-q04-rerun-013-results.json')", "REPORT = Path(os.environ['TMPDIR']) / 'mtg-fix-r2-35.json'")
source = source.replace("SCRATCH = Path.home() / 'AppData/Local/hermes/profiles/wb-quality/cache/scratch'", "SCRATCH = Path(os.environ['TMPDIR'])")
source = source.replace("if __name__=='__main__': main()", "")
namespace = {'__file__': str(qa), '__name__': 'development_replay'}
exec(compile(source, str(qa), 'exec'), namespace)
main = namespace['main']
assert callable(main)
main()
report = json.loads((Path(os.environ['TMPDIR']) / 'mtg-fix-r2-35.json').read_text(encoding='utf-8'))
assert report['total_count'] == report['pass_count'] == 35, [(r['id'], r.get('failure')) for r in report['cases'] if not r.get('pass')]

# Additional developer counterexamples, run only from the clean extracted CLI.
archive = Path(__file__).resolve().parents[3] / 'dist/wangbin-meeting-action-tracker-0.1.4-skill-candidate.zip'
with tempfile.TemporaryDirectory(prefix='mtg-r2-extra-', dir=os.environ['TMPDIR']) as directory:
    base = Path(directory)
    with zipfile.ZipFile(archive) as zipped:
        zipped.extractall(base / 'clean')
    script = base / 'clean/wangbin-meeting-action-tracker/scripts/track.py'
    old = base / 'old.csv'
    with old.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['task_id', '任务内容', '执行状态'])
        writer.writeheader()
        writer.writerows([{'task_id': 'T01', '任务内容': '接口联调', '执行状态': '进行中'},
                          {'task_id': 'T02', '任务内容': '培训', '执行状态': '待执行'}])
    original = hashlib.sha256(old.read_bytes()).hexdigest()
    records = []

    def run(label, text, prior=old, supplement=None, correction=None):
        folder = base / label
        folder.mkdir()
        note = folder / 'meeting.md'
        note.write_text(text, encoding='utf-8')
        note_hash = hashlib.sha256(note.read_bytes()).hexdigest()
        out = folder / 'out'
        out.mkdir()
        command = [sys.executable, str(script), '--meeting-file', str(note), '--previous-tasks', str(prior),
                   '--project-name', '演练', '--output-dir', str(out)]
        if supplement:
            command.extend(['--supplemental-evidence', str(supplement)])
        if correction:
            command.extend(['--correction', correction])
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        result = subprocess.run(command, cwd=folder, env=env, text=True, capture_output=True, timeout=30)
        assert result.returncode == 0, (label, result.stderr)
        xlsx = out / '演练-任务跟踪.xlsx'
        book = load_workbook(xlsx, read_only=True)
        try:
            assert book.sheetnames == ['当前任务', '本次新增与变化', '待确认事项', '状态历史']
            sheets = {name: [dict(zip([cell.value for cell in book[name][1]], row))
                             for row in book[name].values if row[0] not in ('task_id', 'event_id')]
                      for name in book.sheetnames}
        finally:
            book.close()
        summary = (out / '演练-会议决议摘要.md').read_text(encoding='utf-8')
        assert hashlib.sha256(note.read_bytes()).hexdigest() == note_hash
        records.append({'case': label, 'command': command, 'exit': result.returncode, 'sheets': sheets, 'summary': summary})
        return xlsx, sheets, summary

    for i, text in enumerate(['T01的取消事项仍在讨论，尚无最终决定。', 'T01取消方案正在商议，尚未拍板。',
                              '关于取消T01仍在评估，有待确认。', '建议取消T01，目前没有形成决议。']):
        _, sheets, summary = run(f'pending_{i}', text)
        tasks = {row['task_id']: row for row in sheets['当前任务']}
        assert (tasks['T01']['执行状态'], tasks['T02']['执行状态']) == ('进行中', '待执行')
        assert sheets['待确认事项'] and not sheets['状态历史'] and '确定变化：' not in summary
    for label, extra in [('supplement', 'supplemental-evidence'), ('correction', 'correction')]:
        if label == 'supplement':
            supplement = base / 'evidence.txt'
            supplement.write_text('T01的取消事项仍在讨论，尚无最终决定。', encoding='utf-8')
            _, sheets, _ = run(label, '例会无新决定。', supplement=supplement)
        else:
            _, sheets, _ = run(label, '例会无新决定。', correction='T01的取消事项仍在讨论，尚无最终决定。')
        assert sheets['待确认事项'] and not sheets['状态历史']
    first, sheets, _ = run('scope', 'T01的取消事项仍在讨论，尚无最终决定，但T02明确决定取消。')
    assert {r['task_id'] for r in sheets['状态历史'] if r['事件类型'] == '取消'} == {'T02'}
    pending, sheets, _ = run('round1', 'T01的取消事项仍在讨论，尚无最终决定。')
    _, sheets, summary = run('round2', '本次会议正式决定取消T01。', prior=pending)
    assert {r['task_id'] for r in sheets['状态历史'] if r['事件类型'] == '取消'} == {'T01'}
    assert not sheets['待确认事项'] and '确定变化：' in summary
    assert hashlib.sha256(old.read_bytes()).hexdigest() == original
    evidence_path = Path(os.environ['TMPDIR']) / 'mtg-fix-r2-extra.json'
    evidence_path.write_text(json.dumps({'old_sha256': original, 'cases': records}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'extra_passed': len(records), 'evidence': str(evidence_path)}, ensure_ascii=False))
