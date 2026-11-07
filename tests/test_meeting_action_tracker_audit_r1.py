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
