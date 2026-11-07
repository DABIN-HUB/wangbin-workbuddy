"""Independent historical 0.1.1 ZIP probe: real files, subprocess CLI, reopened four-sheet XLSX."""
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

ROOT = Path(__file__).resolve().parents[4]
ZIP = ROOT / 'dist/wangbin-meeting-action-tracker-0.1.1-skill-candidate.zip'
EXPECTED_SHA = '5f5f0bc86ca469c89d758010194d8768e27badc96584791495e4b71c8ef745ae'
SHEETS = ['当前任务', '本次新增与变化', '待确认事项', '状态历史']
RESULT = ROOT / 'docs/products/wangbin-meeting-action-tracker/qa/audit-r1-q04-baseline-results.json'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    assert sha(ZIP) == EXPECTED_SHA
    scratch = Path.home() / 'AppData/Local/hermes/profiles/wb-quality/cache/scratch'
    assert scratch.is_dir(), f'Profile scratch missing: {scratch}'
    with tempfile.TemporaryDirectory(prefix='q04-baseline-', dir=scratch) as temp:
        base = Path(temp)
        with zipfile.ZipFile(ZIP) as z:
            assert z.testzip() is None
            members = z.namelist()
            assert len(members) == len(set(members)) and all(not Path(m).is_absolute() and '..' not in Path(m).parts for m in members)
            z.extractall(base / 'clean')
        script = base / 'clean/wangbin-meeting-action-tracker/scripts/track.py'
        assert sha(script) == sha(ROOT / 'packages/skills/wangbin-meeting-action-tracker/scripts/track.py')
        fixtures = base / 'fixtures'; fixtures.mkdir()
        previous = fixtures / 'previous.csv'
        with previous.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id','任务内容','负责人','负责人确认状态','截止时间','截止时间确认状态','执行状态','来源'])
            writer.writeheader()
            writer.writerow({'task_id':'T01','任务内容':'接口联调','负责人':'王工','负责人确认状态':'已确认','截止时间':'2026-11-05','截止时间确认状态':'已确认','执行状态':'进行中','来源':'old:1'})
            writer.writerow({'task_id':'T02','任务内容':'准备演练培训','负责人':'李工','负责人确认状态':'已确认','执行状态':'待执行','来源':'old:2'})
        input_hash = sha(previous)
        cases = [
            ('f01_not_cancel','T01不取消，继续进行中。','T01','进行中','no_cancel'),
            ('f01_not_cancel_spaced','T01 不取消，继续进行中。','T01','进行中','no_cancel'),
            ('f01_not_completed_spaced','T01 不是已完成，仍在进行中。','T01','进行中','no_complete'),
            ('f01_suggest_spaced','建议取消 T01，尚未形成决定。','T01','进行中','proposal'),
            ('f01_decide_spaced','明确决定取消 T01。','T01','取消','cancel'),
            ('f01_prior_spaced','取消此前取消 T01 的决定，T01 继续执行。','T01','进行中','no_cancel'),
            ('f01_scoped_spaced','T01 未完成，但 T02 已经完成。','T01','进行中','scoped'),
            ('f01_not_completed','T01不是已完成，仍在进行中。','T01','进行中','no_complete'),
            ('f01_suggest','建议取消T01，尚未形成决定。','T01','进行中','proposal'),
            ('f01_decide','明确决定取消T01。','T01','取消','cancel'),
            ('f01_cancel_prior','取消此前取消T01的决定，T01继续执行。','T01','进行中','no_cancel'),
            ('f01_scoped','T01未完成，但T02已经完成。','T01','进行中','scoped'),
            ('f01_positive_complete','T01已经完成。','T01','报告完成','complete'),
            ('f02_zhang','新增任务：接口测试，由张三确认负责，截止2026-11-10。',None,'待执行','owner_张三'),
            ('f02_li','新增任务：接口测试，由李工确认负责，截止2026-11-10。',None,'待执行','owner_李工'),
            ('f02_zhao','新增任务：接口测试，由赵敏确认负责，截止2026-11-10。',None,'待执行','owner_赵敏'),
            ('f02_xiao','新增任务：接口测试，由小王确认负责，截止2026-11-10。',None,'待执行','owner_小王'),
            ('f02_alex','新增任务：接口测试，由Alex确认负责，截止2026-11-10。',None,'待执行','owner_Alex'),
            ('f02_tentative','新增任务：接口测试，建议由张三负责，尚未确认，截止2026-11-10。',None,'待执行','tentative'),
            ('f03_label','会议日期：2026-11-06。T01截止明天。','T01','进行中','due_2026-11-07'),
            ('f03_label_spaced','会议日期：2026-11-06。T01 截止明天。','T01','进行中','due_2026-11-07'),
            ('f03_prefix_spaced','2026-11-06项目例会。T01 截止明天。','T01','进行中','due_2026-11-07'),
            ('f03_missing_spaced','项目例会。T01 截止明天。','T01','进行中','due_missing'),
            ('f03_conflict_spaced','会议日期：2026-11-06。会议日期：2026-11-08。T01 截止明天。','T01','进行中','due_missing'),
            ('f03_prefix','2026-11-06项目例会。T01截止明天。','T01','进行中','due_2026-11-07'),
            ('f03_missing','项目例会。T01截止明天。','T01','进行中','due_missing'),
            ('f03_conflict','会议日期：2026-11-06。会议日期：2026-11-08。T01截止明天。','T01','进行中','due_missing'),
            ('f04_direct','张三负责接口测试，截止2026-11-10。',None,'待执行','direct'),
            ('f04_discussion','讨论接口测试，尚未决定由谁负责。',None,None,'discussion'),
            ('f05_untouched','T01继续进行中。','T01','进行中','untouched'),
        ]
        evidence = []
        env = dict(os.environ); env.pop('PYTHONPATH', None)
        def run(label, text, old=previous, corrections=(), extras=()):
            folder = base / label; folder.mkdir()
            suffix = '.md' if label.endswith(('prefix','direct','conflict')) else '.txt'
            meeting = folder / ('meeting' + suffix); meeting.write_text(text, encoding='utf-8')
            out = folder / 'output'; out.mkdir()
            cmd = [sys.executable, str(script), '--meeting-file', str(meeting), '--project-name','蓝桥演练','--output-dir',str(out)]
            if old: cmd += ['--previous-tasks',str(old)]
            for c in corrections: cmd += ['--correction',c]
            cmd += list(extras)
            proc = subprocess.run(cmd, cwd=folder, env=env, capture_output=True, text=True, timeout=30)
            workbooks = list(out.glob('*.xlsx')); summaries = list(out.glob('*.md'))
            sheets = {}
            if len(workbooks) == 1:
                wb = load_workbook(workbooks[0], read_only=True, data_only=True)
                sheets = {name: [dict(zip([c.value for c in ws[1]], row)) for row in ws.iter_rows(min_row=2, values_only=True)] for name, ws in [(n, wb[n]) for n in wb.sheetnames]}
                wb.close()
            record = {'id':label, 'meeting_text':text, 'meeting_sha256':sha(meeting),'previous_sha256':sha(old) if old else None, 'command':cmd,'cwd':str(folder),'exit':proc.returncode,'stdout':proc.stdout.strip(),'stderr':proc.stderr.strip(),'xlsx':str(workbooks[0]) if workbooks else None,'xlsx_sha256':sha(workbooks[0]) if workbooks else None,'summary_sha256':sha(summaries[0]) if summaries else None,'sheets':sheets,'sheet_names':list(sheets)}
            evidence.append(record)
            return record
        for label,text,tid,expected,kind in cases:
            old = None if label.startswith('f02') or label.startswith('f04') else previous
            r = run(label,text,old)
            rows = r['sheets'].get('当前任务',[]); tasks={t['task_id']:t for t in rows}
            target = (tasks.get(tid) if tid else (rows[0] if rows else {})) or {}
            history = r['sheets'].get('状态历史',[])
            questions = r['sheets'].get('待确认事项',[])
            change = r['sheets'].get('本次新增与变化',[])
            verdict = r['exit']==0 and r['sheet_names']==SHEETS and (not expected or target.get('执行状态') == expected)
            if kind=='no_cancel': verdict &= not any(x.get('事件类型')=='取消' for x in history)
            if kind=='no_complete': verdict &= not any('完成' in str(x.get('事件类型')) for x in history)
            if kind in {'no_cancel','no_complete','proposal','cancel','scoped','complete'} or kind.startswith('due_'):
                verdict &= not any(x.get('待确认字段')=='任务关联' for x in questions)
            if kind=='proposal': verdict &= bool(questions) and not any(x.get('事件类型')=='取消' for x in history)
            if kind=='cancel': verdict &= any(x.get('事件类型')=='取消' and x.get('来源') for x in history)
            if kind=='scoped': verdict &= tasks.get('T02',{}).get('执行状态')=='报告完成'
            if kind.startswith('owner_'):
                name = kind.split('_',1)[1]
                verdict &= len(rows)==1 and target.get('负责人')==name and target.get('负责人确认状态')=='已确认' and target.get('截止时间')=='2026-11-10'
            if kind=='tentative': verdict &= len(rows)==1 and target.get('负责人确认状态')!='已确认' and bool(questions)
            if kind.startswith('due_'):
                due = kind[4:]
                verdict &= target.get('截止时间')==('2026-11-05' if due=='missing' else due) and (due!='missing' or (bool(questions) and target.get('截止时间确认状态')=='已确认'))
            if kind=='direct': verdict &= len(rows)==1 and target.get('负责人')=='张三' and target.get('截止时间')=='2026-11-10'
            if kind=='discussion': verdict &= not rows and bool(questions)
            if kind=='untouched': verdict &= tasks['T02']['执行状态']=='待执行' and tasks['T02']['最近变更']=='无新增进展'
            r['expected']={'task_id':tid,'status':expected,'rule':kind}
            r['pass']=bool(verdict)
        first = run('f05_first','2026-11-06项目例会。新增任务：编写演练纪要，由李工确认负责，截止2026-11-10。',None)
        again = run('f05_repeat','2026-11-06项目例会。新增任务：编写演练纪要，由李工确认负责，截止2026-11-10。',Path(first['xlsx']))
        a,b=first['sheets'],again['sheets']
        first['expected']='one new task and its assignment/due date'
        first['pass']=first['exit']==0 and first['sheet_names']==SHEETS and len(a['当前任务'])==1 and a['当前任务'][0].get('负责人')=='李工' and a['当前任务'][0].get('截止时间')=='2026-11-10'
        again['expected']='repeat same task_id and event_id sets; no new change rows'
        again['pass']=first['exit']==again['exit']==0 and {x['task_id'] for x in a['当前任务']}=={x['task_id'] for x in b['当前任务']} and {x['event_id'] for x in a['状态历史']}=={x['event_id'] for x in b['状态历史']} and not b['本次新增与变化']
        correction = run('f05_correction','项目例会：T01进行中。',previous,('将T01截止日更正为2026-11-10','T01明确改由赵敏确认负责'))
        corr=correction['sheets']; t={x['task_id']:x for x in corr.get('当前任务',[])}
        correction['expected']='T01 date 2026-11-10 owner 赵敏; T02 retained; history original/new/source; four sheets'
        correction['pass']=correction['exit']==0 and correction['sheet_names']==SHEETS and t.get('T01',{}).get('截止时间')=='2026-11-10' and t.get('T01',{}).get('负责人')=='赵敏' and t.get('T02',{}).get('执行状态')=='待执行' and any(x.get('原值')=='2026-11-05' and x.get('新值')=='2026-11-10' and x.get('来源') for x in corr['状态历史'])
        assert sha(previous)==input_hash, 'old input modified'
        report={'product_id':'wangbin-meeting-action-tracker','task_id':'t_5a7e06e6','baseline_sha256':EXPECTED_SHA,'zip_members':members,'archive_testzip':None,'script_sha256':sha(script),'python':sys.version,'openpyxl':__import__('openpyxl').__version__,'scratch_root':str(base),'fixture_previous_csv':previous.read_text(encoding='utf-8-sig'),'fixture_previous_sha256':input_hash,'input_unchanged':True,'cases':evidence,'pass_count':sum(r.get('pass',False) for r in evidence),'total_count':len(evidence)}
        RESULT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'result':str(RESULT),'pass':report['pass_count'],'total':report['total_count'],'failed_ids':[r['id'] for r in evidence if not r.get('pass')]},ensure_ascii=False))
if __name__=='__main__': main()
