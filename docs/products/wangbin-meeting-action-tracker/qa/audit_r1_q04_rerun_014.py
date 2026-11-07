"""Independent 0.1.4 immutable archive probe; fixture expectations written before execution."""
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from openpyxl import load_workbook
import yaml

ROOT = Path(__file__).resolve().parents[4]
PRODUCT = 'wangbin-meeting-action-tracker'
ZIP = ROOT / 'dist' / f'{PRODUCT}-0.1.4-skill-candidate.zip'
SHA = '8b45ac776227db6128f6e6c60e2f345604e63fbb52e693b4bd3dadccb2a45193'
REPORT = Path(__file__).with_name('audit-r1-q04-rerun-014-results.json')
SHEETS = ['当前任务', '本次新增与变化', '待确认事项', '状态历史']
SCRATCH = Path.home() / 'AppData/Local/hermes/profiles/wb-quality/cache/scratch'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def assert_zip(base):
    assert sha(ZIP) == SHA
    sidecar = ZIP.with_suffix('.zip.sha256').read_text(encoding='utf-8').split()[0]
    assert sidecar == SHA
    manifest = json.loads(ZIP.with_suffix('.zip.manifest.json').read_text(encoding='utf-8'))
    assert manifest['sha256'] == SHA and manifest['version'] == '0.1.4'
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert len(names) == len(set(names)) == len(manifest['members'])
        assert all(n.startswith(PRODUCT + '/') and not n.startswith('/') and '..' not in Path(n).parts and '\\' not in n for n in names)
        assert set(names) == {m['path'] for m in manifest['members']}
        for m in manifest['members']:
            payload = z.read(m['path'])
            assert hashlib.sha256(payload).hexdigest() == m['sha256'] and len(payload) == m['size']
            assert sha(ROOT / 'packages/skills' / m['path']) == m['sha256']
        skill = z.read(PRODUCT + '/SKILL.md').decode('utf-8')
        meta = yaml.safe_load(skill.split('---', 2)[1])
        assert meta['name'] == PRODUCT and meta['version'] == '0.1.4'
        assert meta['display_name'] == '会议决议与任务跟踪'
        assert meta['display_name_en'] == 'Meeting Decisions and Action Tracker'
        assert len(meta['examples_zh']) == len(meta['examples_en']) == 3
        assert 'references/usage-and-contract.md' in skill and 'scripts/track.py' in skill
        assert json.loads(z.read(PRODUCT + '/manifest.json'))['dependencies'] == ['openpyxl>=3.1,<4', 'python-docx>=1.1,<2']
        z.extractall(base / 'clean')
    return names, manifest

def rows(path):
    wb = load_workbook(path, read_only=True, data_only=False)
    assert wb.sheetnames == SHEETS, wb.sheetnames
    result = {}
    for sheet in SHEETS:
        ws = wb[sheet]; values = list(ws.values)
        result[sheet] = [dict(zip(values[0], row)) for row in values[1:]]
    wb.close()
    return result

def main():
    assert SCRATCH.is_dir()
    with tempfile.TemporaryDirectory(prefix='q04-new-independent-', dir=SCRATCH) as directory:
        base = Path(directory); members, manifest = assert_zip(base)
        script = base / 'clean' / PRODUCT / 'scripts/track.py'
        fixture = base / 'fixture'; fixture.mkdir()
        previous = fixture / 'old.csv'
        with previous.open('w', encoding='utf-8-sig', newline='') as f:
            w=csv.DictWriter(f, fieldnames=['task_id','任务内容','负责人','负责人确认状态','截止时间','截止时间确认状态','执行状态','来源'])
            w.writeheader()
            w.writerows([
                dict(task_id='T01',任务内容='接口联调',负责人='王工',负责人确认状态='已确认',截止时间='2026-11-05',截止时间确认状态='已确认',执行状态='进行中',来源='old:1'),
                dict(task_id='T02',任务内容='演练培训',负责人='李工',负责人确认状态='已确认',截止时间='',截止时间确认状态='未提供',执行状态='待执行',来源='old:2')])
        old_sha = sha(previous)
        env=os.environ.copy(); env.pop('PYTHONPATH', None)
        records=[]
        def run(label,text,old=previous,ext='.md',supp=(),corr=()):
            folder=base/label; folder.mkdir()
            meeting=folder/('meeting'+ext); meeting.write_text(text,encoding='utf-8')
            output=folder/'out'; output.mkdir()
            command=[sys.executable,str(script),'--meeting-file',str(meeting),'--project-name','蓝桥演练','--output-dir',str(output)]
            if old: command.extend(['--previous-tasks',str(old)])
            for s in supp: command.extend(['--supplemental-evidence',str(s)])
            for c in corr: command.extend(['--correction',c])
            p=subprocess.run(command,cwd=folder,env=env,text=True,capture_output=True,timeout=35)
            x=output/'蓝桥演练-任务跟踪.xlsx'; s=output/'蓝桥演练-会议决议摘要.md'
            sheet=rows(x) if x.exists() else {}
            r=dict(id=label,meeting_text=text,meeting_sha256=sha(meeting),previous_sha256=sha(old) if old else None,supplemental=[dict(path=str(v),text=v.read_text(encoding='utf-8'),sha256=sha(v)) for v in supp],corrections=list(corr),command=command,cwd=str(folder),exit=p.returncode,stdout=p.stdout.strip(),stderr=p.stderr.strip(),xlsx_sha256=sha(x) if x.exists() else None,summary_sha256=sha(s) if s.exists() else None,summary=s.read_text(encoding='utf-8') if s.exists() else None,sheets=sheet)
            records.append(r)
            return r,x
        def check(r, expectation, test):
            r['expected']=expectation
            try: test(r)
            except (AssertionError,KeyError,IndexError,ValueError,TypeError) as e: r['pass']=False; r['failure']=repr(e)
            else: r['pass']=True
        def ok(r): assert r['exit']==0 and list(r['sheets'])==SHEETS, (r['exit'],r['stderr'])
        def task(r,tid): return next(t for t in r['sheets']['当前任务'] if t['task_id']==tid)
        def new(r): return r['sheets']['当前任务']
        def hist(r): return r['sheets']['状态历史']
        def changed(r): return r['sheets']['本次新增与变化']
        def questions(r): return r['sheets']['待确认事项']
        def scoped(r):
            ok(r); assert task(r,'T01')['执行状态']=='进行中' and task(r,'T02')['执行状态']=='报告完成'
            assert not any(h['task_id']=='T01' and '完成' in h['事件类型'] for h in hist(r))
            assert any(h['task_id']=='T02' and h['事件类型']=='报告完成' and h['来源'] for h in hist(r))
        def no_cancel(r):
            ok(r); assert task(r,'T01')['执行状态']=='进行中'
            assert not any(h['task_id']=='T01' and h['事件类型']=='取消' for h in hist(r))
        def decided(r):
            ok(r); assert task(r,'T01')['执行状态']=='取消'
            assert any(h['task_id']=='T01' and h['事件类型']=='取消' and h['原值']=='进行中' and h['来源'] for h in hist(r))
        def proposed(r):
            no_cancel(r); assert questions(r) and any('取消' in str(q['候选值或问题']) for q in questions(r))
        def due(r,expect):
            ok(r); assert task(r,'T01')['截止时间']==expect and task(r,'T02')['执行状态']=='待执行'
            assert any(h['task_id']=='T01' and h['新值']==expect and h['来源'] for h in hist(r))
        def retain_due(r):
            ok(r); assert task(r,'T01')['截止时间']=='2026-11-05' and task(r,'T01')['截止时间确认状态']=='已确认'
            assert questions(r) and not any(h['task_id']=='T01' and h['事件类型']=='期限变更' for h in hist(r))
        def assert_conflict_dates(r):
            values={q['候选值或问题'] for q in questions(r) if q['待确认字段']=='会议日期'}
            assert values == {'2027-02-28','2027-03-02'},values
        cases=[
          ('scoped_unspaced','T01还没完成，但T02已经完成。','T01 must stay active, T02 report completed',scoped),
          ('not_cancel_paraphrase','T01不会取消，仍在进行中。','T01 remains active, no cancellation event',no_cancel),
          ('decision_variant','经会议决定取消T01。','T01 cancellation confirmed and sourced',decided),
          ('proposal_variant','提议取消T01，目前还未拍板。','T01 remains active; proposed cancellation retained',proposed),
          ('date_label_shift','会议时间：2027-02-28。T01明天截止。','T01 due 2027-03-01, T02 retained',lambda r: due(r,'2027-03-01')),
          ('date_prefix_shift','2027-02-28项目例会。T01截止明天。','T01 due 2027-03-01, T02 retained',lambda r: due(r,'2027-03-01')),
          ('date_missing','T01明天截止。','Prior confirmed date unchanged; ask for meeting day',retain_due),
          ('date_conflict','会议日期：2027-02-28。会议日期：2027-03-02。T01截止明天。','Prior date unchanged and both meeting dates surfaced',lambda r: (retain_due(r),assert_conflict_dates(r))),
          ('owner_change','现由孙丽接手T01，截止2027-03-05。','T01 owner Sun Li confirmed and due changes',lambda r: (ok(r),task(r,'T01')['负责人']=='孙丽' or (_ for _ in ()).throw(AssertionError(task(r,'T01'))))),
          ('owner_proposal','建议由陈琳负责T01，尚未确认。','T01 original 王工 retained and candidate surfaced',lambda r: (ok(r),task(r,'T01')['负责人']=='王工' or (_ for _ in ()).throw(AssertionError(task(r,'T01'))),any('陈琳' in str(q) for q in questions(r)) or (_ for _ in ()).throw(AssertionError(questions(r))))),
        ]
        for label,text,expect,assertion in cases:
            r,_=run(label,text)
            check(r,expect,assertion)
        for label,text,name in [
          ('new_latin','新增任务：系统接口检查，由Maya确认负责，截止2027-03-06。','Maya'),
          ('new_chinese','新增任务：系统接口检查，由陈琳确认负责，截止2027-03-06。','陈琳'),
          ('direct_action','孙丽负责接口检查，截止2027-03-06。','孙丽'),
          ('discussion','讨论接口检查，尚未指定负责人和期限。',None)]:
            r,_=run(label,text,None,ext='.txt')
            if name:
                def verify(r,name=name):
                    ok(r); assert len(new(r))==1 and new(r)[0]['负责人']==name and new(r)[0]['截止时间']=='2027-03-06',new(r)
                    assert any(h['事件类型']=='新增' and h['来源'] for h in hist(r))
                check(r,'One new sourced task owner '+name+' deadline 2027-03-06',verify)
            else:
                def verify(r): ok(r); assert not new(r) and questions(r)
                check(r,'No confirmed task but pending discussion retained',verify)
        first,x1=run('multi_first','新增任务：系统接口检查A，由Maya确认负责，截止2027-03-06。\n新增任务：系统接口检查B，由陈琳确认负责，截止2027-03-07。',None)
        def verify_first(r):
            ok(r); assert len(new(r))==2 and len({t['task_id'] for t in new(r)})==2 and len(hist(r))>=2
        check(first,'Two distinct A/B tasks and events',verify_first)
        repeat,x2=run('multi_repeat','新增任务：系统接口检查A，由Maya确认负责，截止2027-03-06。\n新增任务：系统接口检查B，由陈琳确认负责，截止2027-03-07。',x1)
        def verify_repeat(r):
            ok(r); assert {t['task_id'] for t in new(r)}=={t['task_id'] for t in new(first)}
            assert {h['event_id'] for h in hist(r)}=={h['event_id'] for h in hist(first)} and not changed(r)
        check(repeat,'Reimport unchanged task/event sets and zero changes',verify_repeat)
        reordered,_=run('multi_reordered','新增任务：系统接口检查B，由陈琳确认负责，截止2027-03-07。\n新增任务：系统接口检查A，由Maya确认负责，截止2027-03-06。',x2)
        check(reordered,'Reorder keeps two IDs and zero duplicate events',verify_repeat)
        report,x3=run('reported','T01已完成。')
        def verify_report(r):
            ok(r); assert task(r,'T01')['执行状态']=='报告完成' and not task(r,'T01')['完成证据']
            assert task(r,'T02')['执行状态']=='待执行'
        check(report,'T01 reported only, T02 untouched',verify_report)
        evidence=fixture/'completion.txt'; evidence.write_text('T01 验收单 E-83 已签收。',encoding='utf-8'); evidence_sha=sha(evidence)
        proof,x4=run('proof','例会无新增决议。',x3,supp=(evidence,))
        def verify_proof(r):
            ok(r); assert task(r,'T01')['执行状态']=='证据确认完成' and 'E-83' in task(r,'T01')['完成证据']
            assert task(r,'T02')['执行状态']=='待执行' and any(h['事件类型']=='报告完成' for h in hist(r))
            assert '未独立核验' in task(r,'T01')['完成证据']
        check(proof,'Only T01 evidence-backed, submitted evidence unverified, old report retained',verify_proof)
        replay,_=run('proof_replay','例会无新增决议。',x4,supp=(evidence,))
        def verify_replay(r):
            verify_proof(r); assert {h['event_id'] for h in hist(r)}=={h['event_id'] for h in hist(proof)} and not changed(r)
        check(replay,'Same proof creates no duplicate history or changes',verify_replay)
        corrected,x5=run('corrected','例会无新增决议。',previous,corr=('将T01截止日更正为2027-03-09','T01明确改由陈琳确认负责'))
        def verify_corrected(r):
            ok(r); t=task(r,'T01'); assert t['截止时间']=='2027-03-09' and t['负责人']=='陈琳' and task(r,'T02')['负责人']=='李工'
            assert any(h['原值']=='2026-11-05' and h['新值']=='2027-03-09' and h['来源'] for h in hist(r))
        check(corrected,'Correction changes deadline/owner and retains T02 and old source',verify_corrected)
        corrected_repeat,_=run('corrected_repeat','例会无新增决议。',x5,corr=('将T01截止日更正为2027-03-09','T01明确改由陈琳确认负责'))
        def verify_corrected_repeat(r):
            verify_corrected(r); assert {h['event_id'] for h in hist(r)}=={h['event_id'] for h in hist(corrected)} and not changed(r)
        check(corrected_repeat,'Repeat correction adds zero duplicate events',verify_corrected_repeat)
        a=fixture/'a.txt'; b=fixture/'b.md'; a.write_text('T01继续进行中。',encoding='utf-8'); b.write_text('明确决定取消T01。',encoding='utf-8')
        for label,supp in [('conflict_ab',(a,b)),('conflict_ba',(b,a))]:
            r,_=run(label,'例会无新增决议。',previous,supp=supp)
            def verify_conflict(r):
                ok(r); assert task(r,'T01')['执行状态']=='进行中' and task(r,'T02')['执行状态']=='待执行'
                assert any(h['事件类型']=='冲突' and h['是否存在冲突']=='是' for h in hist(r)) and questions(r)
            check(r,'Equal-authority contradictions preserved, old status unchanged regardless order',verify_conflict)
        blank,_=run('empty_meeting','   ')
        def verify_empty(r):
            assert r['exit']==2 and 'EMPTY_MEETING' in r['stderr'] and not r['sheets']
        check(blank,'Blank meeting rejected with EMPTY_MEETING and no workbook',verify_empty)
        bad=fixture/'invalid.csv'; bad.write_text('wrong,header\nX,x\n',encoding='utf-8')
        invalid,_=run('invalid_previous','T01继续进行中。',bad)
        def verify_invalid(r):
            assert r['exit']==2 and 'INVALID_PREVIOUS_SCHEMA' in r['stderr'] and not r['sheets']
        check(invalid,'Invalid previous schema rejected; no workbook',verify_invalid)
        # Post-fix independent semantic, owner, leap-date, and reverse-order variations.
        extra_cases=[
          ('negation_modal','T01不能被取消，仍在进行中。','Modal negation must not cancel T01',no_cancel),
          ('proposal_deliberation','T01的取消事项仍在讨论，尚无最终决定。','Discussion without final decision cannot cancel T01; pending must be visible',lambda r: (no_cancel(r), any('取消' in str(q) for q in questions(r)) or (_ for _ in ()).throw(AssertionError('Missing pending cancellation')))),
          ('positive_cancel_later','本次会议正式决定取消T01。','Positive cancellation must take effect with source',decided),
          ('not_completed_scope','T01并未完成，但T02已经完成。','Only T02 completed; T01 stays in progress',scoped),
          ('date_leap_shift','会议日期：2028-02-28。T01明天截止。','Leap date resolves to February 29',lambda r: due(r,'2028-02-29')),
          ('owner_alex','新增任务：验收回访，由Alex确认负责，截止2028-04-17。','New English owner/date',None),
          ('owner_zh','新增任务：验收回访，由赵敏确认负责，截止2028-04-17。','New Chinese owner/date',None),
        ]
        for label,text,expect,assertion in extra_cases:
            is_new=label.startswith('owner_')
            r,_=run(label,text,None if is_new else previous,ext='.txt' if is_new else '.md')
            if is_new:
                owner='Alex' if label=='owner_alex' else '赵敏'
                def assertion(r,owner=owner):
                    ok(r); assert len(new(r))==1,new(r)
                    t=new(r)[0]; assert t['负责人']==owner and t['截止时间']=='2028-04-17',t
                    assert any(h['事件类型']=='新增' and h['来源'] for h in hist(r))
            check(r,expect,assertion)
        pair='新增任务：上线准备A，由Alex确认负责，截止2028-04-17。\n新增任务：上线准备B，由赵敏确认负责，截止2028-04-18。'
        pair_back='新增任务：上线准备B，由赵敏确认负责，截止2028-04-18。\n新增任务：上线准备A，由Alex确认负责，截止2028-04-17。'
        pa,px=run('variant_pair_first',pair,None)
        def distinct_pair(r):
            ok(r); assert len(new(r))==2,new(r)
            mapped={t['任务内容'][-1]:t for t in new(r)}
            assert set(mapped)=={'A','B'},mapped
            assert mapped['A']['负责人']=='Alex' and mapped['A']['截止时间']=='2028-04-17',mapped
            assert mapped['B']['负责人']=='赵敏' and mapped['B']['截止时间']=='2028-04-18',mapped
            assert len({t['task_id'] for t in new(r)})==2
            assert len([h for h in hist(r) if h['事件类型']=='新增' and h['来源']])==2
        check(pa,'Distinct A/B own IDs, owner, date, source',distinct_pair)
        pb,_=run('variant_pair_reverse',pair_back,px)
        def stable_pair(r):
            distinct_pair(r)
            assert {t['task_id'] for t in new(r)}=={t['task_id'] for t in new(pa)}
            assert {h['event_id'] for h in hist(r)}=={h['event_id'] for h in hist(pa)} and not changed(r)
        check(pb,'Reverse input keeps IDs and events, zero duplicate changes',stable_pair)
        # Additional independently selected semantic boundaries, predeclared before running.
        def unresolved(r):
            no_cancel(r)
            assert task(r,'T02')['执行状态']=='待执行',task(r,'T02')
            assert not any(h['task_id']=='T01' and h['事件类型']=='取消' for h in hist(r))
            assert not any(c['task_id']=='T01' and c['确认状态']=='已确认' and '取消' in str(c['新值']) for c in changed(r))
            assert any('取消' in str(q['候选值或问题']) for q in questions(r)),questions(r)
            assert '确定变化：T01 取消' not in r['summary'],r['summary']
        def mixed(r):
            ok(r)
            assert task(r,'T01')['执行状态']=='进行中',task(r,'T01')
            assert task(r,'T02')['执行状态']=='报告完成',task(r,'T02')
            assert not any(h['task_id']=='T01' and h['事件类型']=='取消' for h in hist(r)),hist(r)
            assert any('取消' in str(q['候选值或问题']) for q in questions(r)),questions(r)
            assert '确定变化：T01 取消' not in r['summary'],r['summary']
        fresh=[
            ('unresolved_synonym','T01取消的议题尚在商议，至今没有达成决议。','Unresolved cancellation discussion retained; T01/T02 unchanged',unresolved),
            ('unresolved_continuing','关于取消T01仍在讨论中，最终方案尚未确定。','Non-decision cancellation stays pending',unresolved),
            ('unresolved_exact_variant','取消T01的事项仍在讨论，尚无最终决定。','Unresolved cancellation without possessive marker remains pending',unresolved),
            ('scoped_mixed','T01的取消事项仍在讨论，尚无最终决定；T02已经完成。','T01 remains active and pending while T02 reports completion',mixed),
            ('negated_cancel_control','T01不能取消，继续进行中。','Explicit negation keeps T01 active',no_cancel),
            ('proposed_cancel_control','有人提议取消T01，但会议尚未形成决议。','Proposal visible only as pending',proposed),
            ('positive_cancel_control','经会议表决，正式决定取消T01。','Actual decision cancels only T01',decided),
        ]
        for label,text,expect,check_fn in fresh:
            r,_=run(label,text)
            check(r,expect,check_fn)
        assert sha(previous)==old_sha and sha(evidence)==evidence_sha
        catalog=json.loads((ROOT/'products/catalog.json').read_text(encoding='utf-8'))
        entry=next(p for p in catalog['products'] if p['id']==PRODUCT)
        assert entry['active_version']=='0.1.4'
        assert any(v['version']=='0.1.4' and v['sha256']==SHA and v['candidate']==str(ZIP.relative_to(ROOT)).replace('\\','/') for v in entry['versions'])
        result=dict(product_id=PRODUCT,task_id='t_1f081465',sha256=SHA,archive_members=members,manifest=manifest,python=sys.version,openpyxl=__import__('openpyxl').__version__,docx=__import__('docx').__version__,old_csv_sha256=old_sha,old_csv_text=previous.read_text(encoding='utf-8-sig'),inputs_unchanged=True,cases=records,pass_count=sum(r.get('pass',False) for r in records),total_count=len(records))
        REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(dict(report=str(REPORT),archive_sha256=SHA,passed=result['pass_count'],total=result['total_count'],failed=[r['id'] for r in records if not r.get('pass')]),ensure_ascii=False))
if __name__=='__main__': main()
