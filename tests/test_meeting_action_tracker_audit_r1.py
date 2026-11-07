"""Frozen audit R1 meeting semantics; all inputs are fictional local files."""
import csv
import importlib.util
from pathlib import Path

import pytest
from openpyxl import load_workbook

SOURCE = Path(__file__).resolve().parents[1] / 'packages/skills/wangbin-meeting-action-tracker/scripts/track.py'
spec = importlib.util.spec_from_file_location('audit_tracker', SOURCE)
tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker)


def case(tmp_path, text, rows=None, **kwargs):
    m = tmp_path / 'meeting.md'
    m.write_text(text, encoding='utf-8')
    p = None
    if rows is not None:
        p = tmp_path / 'previous.csv'
        with p.open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['task_id', '任务内容', '负责人', '执行状态', '截止时间', '截止时间确认状态'])
            w.writeheader()
            w.writerows(rows)
    return tracker.reconcile(m, p, project_name='虚构演练', response_mode='summary', **kwargs)


OLD = [dict(task_id='T01', 任务内容='接口联调', 负责人='王工', 执行状态='进行中', 截止时间='2026-11-05', 截止时间确认状态='已确认'),
       dict(task_id='T02', 任务内容='演练培训', 负责人='李工', 执行状态='待执行', 截止时间='', 截止时间确认状态='未提供')]


@pytest.mark.parametrize('text,expected', [
    ('T01不取消，继续进行中。', '进行中'),
    ('T01不是已完成，仍在进行中。', '进行中'),
    ('建议取消T01，尚未形成决定。', '进行中'),
    ('明确决定取消T01。', '取消'),
    ('T01未完成，但T02已经完成。', '进行中'),
])
def test_scoped_status(tmp_path, text, expected):
    r = case(tmp_path, text, OLD)
    assert r['tasks']['T01']['执行状态'] == expected
    if 'T02已经完成' in text:
        assert r['tasks']['T02']['执行状态'] == '报告完成'
    if '建议' in text:
        assert r['questions'] and not r['history']


def test_reversal_and_id_boundary(tmp_path):
    rows = [dict(OLD[0], 执行状态='取消'), dict(OLD[1]), dict(task_id='T010', 任务内容='额外任务', 负责人='', 执行状态='进行中', 截止时间='', 截止时间确认状态='未提供')]
    r = case(tmp_path, '取消此前取消T01的决定，T01继续执行。T010明确决定取消。', rows)
    assert r['tasks']['T01']['执行状态'] == '进行中'
    assert r['tasks']['T010']['执行状态'] == '取消'
    assert {h['事件类型'] for h in r['history']} == {'重新开启', '取消'}


@pytest.mark.parametrize('name', ['张三', '赵敏', '小王', 'Alex', '李工'])
def test_new_owner(tmp_path, name):
    r = case(tmp_path, f'新增任务：接口测试，由{name}确认负责，截止2026-11-10。')
    assert len(r['tasks']) == 1
    t = next(iter(r['tasks'].values()))
    assert (t['负责人'], t['截止时间'], t['负责人确认状态']) == (name, '2026-11-10', '已确认')
    assert not r['questions']


def test_action_without_prefix_and_candidate(tmp_path):
    r = case(tmp_path, '张三负责接口测试，截止2026-11-10。')
    assert len(r['tasks']) == 1 and next(iter(r['tasks'].values()))['任务内容'] == '接口测试'
    r = case(tmp_path, '可以讨论接口测试，尚未指定负责人和期限。')
    assert not r['tasks'] and r['questions']
    r = case(tmp_path, '建议由张三负责T01，尚未确认。', OLD)
    assert r['tasks']['T01']['负责人'] == '王工' and r['questions']


@pytest.mark.parametrize('text,name', [
    ('接口测试负责人为赵敏，截止2026-11-10。', '赵敏'),
    ('由小王接手接口测试，截止2026-11-10。', '小王'),
    ('Alex负责接口测试，截止2026-11-10。', 'Alex'),
])
def test_varied_assignment(tmp_path, text, name):
    r = case(tmp_path, text)
    assert len(r['tasks']) == 1
    t = next(iter(r['tasks'].values()))
    assert (t['任务内容'], t['负责人'], t['截止时间']) == ('接口测试', name, '2026-11-10')


@pytest.mark.parametrize('prefix,day', [('会议日期：2026-11-06。', '2026-11-07'), ('2026-11-06项目例会。', '2026-11-07'), ('会议日期：2027-02-28。', '2027-03-01')])
def test_dates(tmp_path, prefix, day):
    r = case(tmp_path, prefix + 'T01截止明天。', OLD)
    assert r['tasks']['T01']['截止时间'] == day
    assert r['tasks']['T02']['执行状态'] == '待执行'


@pytest.mark.parametrize('prefix', ['', '会议日期：2026-11-06。会议日期：2026-11-08。'])
def test_missing_or_conflicting_meeting_date_keeps_old(tmp_path, prefix):
    r = case(tmp_path, prefix + 'T01截止明天。', OLD)
    assert (r['tasks']['T01']['截止时间'], r['tasks']['T01']['截止时间确认状态']) == ('2026-11-05', '已确认')
    assert r['questions'] and r['changes']


def test_roundtrip_correction_and_four_sheets(tmp_path):
    m = tmp_path / 'meeting.md'
    m.write_text('张三负责接口测试A，截止2026-11-10。赵敏负责接口测试B，截止2026-11-11。', encoding='utf-8')
    first = tmp_path / 'round1'
    first.mkdir()
    a = tracker.reconcile(m, project_name='虚构演练', output_dir=first)
    wb = load_workbook(a['xlsx'])
    assert wb.sheetnames == list(tracker.SHEETS)
    assert [wb[s].max_row for s in wb.sheetnames] == [3, 7, 1, 7]
    wb.close()
    m.write_text('赵敏负责接口测试B，截止2026-11-11。张三负责接口测试A，截止2026-11-10。', encoding='utf-8')
    b = tracker.reconcile(m, a['xlsx'], project_name='虚构演练', response_mode='summary')
    assert set(a['tasks']) == set(b['tasks'])
    assert {h['event_id'] for h in a['history']} == {h['event_id'] for h in b['history']}
    assert not b['changes']
    m.write_text('例会记录，无新的任务决定。', encoding='utf-8')
    r = case(tmp_path, m.read_text(encoding='utf-8'), OLD, corrections=['将T01截止日更正为2026-11-10', 'T01明确改由赵敏确认负责'])
    assert (r['tasks']['T01']['负责人'], r['tasks']['T01']['截止时间']) == ('赵敏', '2026-11-10')
    assert r['tasks']['T02']['执行状态'] == '待执行'


def test_report_evidence_three_rounds(tmp_path):
    m = tmp_path / 'meeting.md'
    p = tmp_path / 'previous.csv'
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(OLD[0]))
        w.writeheader()
        w.writerows(OLD)
    m.write_text('T01已经完成。', encoding='utf-8')
    first = tmp_path / 'a'
    first.mkdir()
    a = tracker.reconcile(m, p, output_dir=first)
    assert a['tasks']['T01']['执行状态'] == '报告完成'
    proof = tmp_path / 'completion.txt'
    proof.write_text('T01 验收单 E-7 已签收。', encoding='utf-8')
    second = tmp_path / 'b'
    second.mkdir()
    b = tracker.reconcile(m, a['xlsx'], supplemental_evidence=[proof], output_dir=second)
    assert b['tasks']['T01']['执行状态'] == '证据确认完成'
    third = tracker.reconcile(m, b['xlsx'], supplemental_evidence=[proof], response_mode='summary')
    assert third['tasks']['T01']['执行状态'] == '证据确认完成'
    assert not third['changes']
    assert {h['event_id'] for h in b['history']} == {h['event_id'] for h in third['history']}
    assert b['tasks']['T02'] == third['tasks']['T02']


@pytest.mark.parametrize('text,pending', [
    ('T01不会取消，仍在进行中。', False),
    ('T01不能取消，仍在进行中。', False),
    ('T01不得取消，仍在进行中。', False),
    ('提议取消T01，目前还未拍板。', True),
    ('计划取消T01，尚未决定。', True),
])
@pytest.mark.parametrize('entry', ['meeting', 'evidence', 'correction'])
def test_no_false_cancellation_across_entries(tmp_path, text, pending, entry):
    note = text if entry == 'meeting' else '本次例会无其他决定。'
    extra = {'supplemental_evidence': [text]} if entry == 'evidence' else {'corrections': [text]} if entry == 'correction' else {}
    r = case(tmp_path, note, OLD, **extra)
    assert r['tasks']['T01']['执行状态'] == '进行中'
    assert r['tasks']['T02']['执行状态'] == '待执行'
    assert not any(h['task_id'] == 'T01' and h['事件类型'] == '取消' for h in r['history'])
    if pending:
        assert any(q['task_id'] == 'T01' and q['待确认字段'] == '执行状态' for q in r['questions'])


def test_scoped_two_ids_with_negation(tmp_path):
    r = case(tmp_path, 'T01不会取消，仍在进行中，但T02明确决定取消。', OLD)
    assert r['tasks']['T01']['执行状态'] == '进行中'
    assert r['tasks']['T02']['执行状态'] == '取消'
    assert {h['task_id'] for h in r['history'] if h['事件类型'] == '取消'} == {'T02'}


def test_distinct_similar_new_actions_repeat_and_reorder(tmp_path):
    m = tmp_path / 'meeting.md'
    first_text = '新增任务：系统接口检查A，由Maya确认负责，截止2027-03-06。\n新增任务：系统接口检查B，由陈琳确认负责，截止2027-03-07。'
    m.write_text(first_text, encoding='utf-8')
    out = tmp_path / 'first'
    out.mkdir()
    a = tracker.reconcile(m, project_name='虚构演练', output_dir=out)
    assert {t['任务内容']: (tid, t['负责人'], t['截止时间']) for tid, t in a['tasks'].items()} == {
        '系统接口检查A': (next(tid for tid, t in a['tasks'].items() if t['任务内容'] == '系统接口检查A'), 'Maya', '2027-03-06'),
        '系统接口检查B': (next(tid for tid, t in a['tasks'].items() if t['任务内容'] == '系统接口检查B'), '陈琳', '2027-03-07'),
    }
    assert len(a['tasks']) == 2 and len({h['task_id'] for h in a['history'] if h['事件类型'] == '新增'}) == 2
    for text in (first_text, '\n'.join(reversed(first_text.splitlines()))):
        m.write_text(text, encoding='utf-8')
        b = tracker.reconcile(m, a['xlsx'], project_name='虚构演练', response_mode='summary')
        assert set(b['tasks']) == set(a['tasks'])
        assert not b['changes']
        assert {h['event_id'] for h in b['history']} == {h['event_id'] for h in a['history']}
        assert {(t['任务内容'], t['负责人'], t['截止时间']) for t in b['tasks'].values()} == {
            ('系统接口检查A', 'Maya', '2027-03-06'), ('系统接口检查B', '陈琳', '2027-03-07')}

@pytest.mark.parametrize('text', [
    'T01的取消事项仍在讨论，尚无最终决定。',
    'T01取消方案正在商议，尚未拍板。',
    '关于取消T01仍在评估，有待确认。',
    '考虑取消T01，目前没有形成决议。',
])
@pytest.mark.parametrize('entry', ['meeting', 'evidence', 'correction'])
def test_unresolved_cancellation_is_pending_at_every_entry(tmp_path, text, entry):
    note = text if entry == 'meeting' else '本次例会无其他决定。'
    extras = {'supplemental_evidence': [text]} if entry == 'evidence' else {'corrections': [text]} if entry == 'correction' else {}
    r = case(tmp_path, note, OLD, **extras)
    assert (r['tasks']['T01']['执行状态'], r['tasks']['T02']['执行状态']) == ('进行中', '待执行')
    assert not any(h['事件类型'] == '取消' for h in r['history'])
    assert any(q['task_id'] == 'T01' and q['待确认字段'] == '执行状态' for q in r['questions'])
    assert not any(c['变化类型'] == '取消' and c['确认状态'] == '已确认' for c in r['changes'])
    assert '确定变化：' not in r['summary']

def test_unresolved_then_explicit_decision_and_two_task_scope(tmp_path):
    r = case(tmp_path, 'T01的取消事项仍在讨论，尚无最终决定，但T02明确决定取消。', OLD)
    assert (r['tasks']['T01']['执行状态'], r['tasks']['T02']['执行状态']) == ('进行中', '取消')
    assert {h['task_id'] for h in r['history'] if h['事件类型'] == '取消'} == {'T02'}
    assert any(q['task_id'] == 'T01' for q in r['questions'])
    m = tmp_path / 'meeting.md'
    m.write_text('T01的取消事项仍在讨论，尚无最终决定。', encoding='utf-8')
    old = tmp_path / 'previous.csv'
    with old.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(OLD[0]))
        writer.writeheader()
        writer.writerows(OLD)
    first = tmp_path / 'round1'
    first.mkdir()
    a = tracker.reconcile(m, old, output_dir=first)
    assert a['tasks']['T01']['执行状态'] == '进行中' and a['questions']
    m.write_text('本次会议正式决定取消T01。', encoding='utf-8')
    second = tmp_path / 'round2'
    second.mkdir()
    b = tracker.reconcile(m, a['xlsx'], output_dir=second)
    assert b['tasks']['T01']['执行状态'] == '取消' and b['tasks']['T02']['执行状态'] == '待执行'
    assert [h['事件类型'] for h in b['history']] == ['取消']
    assert not b['questions'] and '确定变化：' in b['summary']
