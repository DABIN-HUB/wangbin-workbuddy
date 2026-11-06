"""Independent fictional black-box QA of immutable 0.1.0 ZIP; never import product source."""
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from openpyxl import load_workbook, Workbook
from docx import Document

ROOT = Path(__file__).resolve().parents[4]
DIST = ROOT / 'dist/wangbin-meeting-action-tracker-0.1.0-skill-candidate.zip'
SIDECAR = Path(str(DIST) + '.sha256')
MANIFEST = Path(str(DIST) + '.manifest.json')
SHEETS = ['当前任务', '本次新增与变化', '待确认事项', '状态历史']
HEADERS = [
    'task_id,任务内容,负责人,负责人确认状态,截止时间,截止时间确认状态,执行状态,完成证据,是否逾期,逾期判断依据,来源,最近变更'.split(','),
    'task_id,关联原任务,变化类型,原值,新值,确认状态,来源,event_id'.split(','),
    'task_id,待确认字段,候选值或问题,原因,候选来源,建议用户确认内容'.split(','),
    'event_id,task_id,事件类型,原值,新值,来源,会议或用户确认时间,是否存在冲突'.split(',')]
records = []
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name, observed, expected, passed):
    records.append(dict(case=name, expected=expected, actual=observed, verdict='PASS' if passed else 'FAIL'))
def file(path, text):
    path.write_text(text, encoding='utf-8')
    return path
def rows(path):
    wb = load_workbook(path, read_only=True, data_only=False)
    result = {n: [dict(zip([c.value for c in wb[n][1]], r)) for r in list(wb[n].values)[1:]] for n in wb.sheetnames}
    headers = {n: [c.value for c in wb[n][1]] for n in wb.sheetnames}
    values = {n: list(wb[n].values) for n in wb.sheetnames}
    wb.close()
    return result, headers, values

def main():
    meta = json.loads(MANIFEST.read_text(encoding='utf-8'))
    raw = DIST.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    check('ZIP integrity', actual_sha, meta['sha256'], actual_sha == meta['sha256'] and actual_sha in SIDECAR.read_text())
    with zipfile.ZipFile(DIST) as z:
        bad = z.testzip()
        names = z.namelist()
        check('ZIP members', {'bad':bad,'names':names}, [m['path'] for m in meta['members']], bad is None and set(names)==set(m['path'] for m in meta['members']))
        for m in meta['members']:
            source = ROOT/'packages/skills'/m['path']
            data = z.read(m['path'])
            check('member '+m['path'], hashlib.sha256(data).hexdigest(), m['sha256'], len(data)==m['size'] and hashlib.sha256(data).hexdigest()==m['sha256'] and data==source.read_bytes())
    with tempfile.TemporaryDirectory(prefix='meeting-qa-', dir=os.environ.get('TMPDIR')) as td:
        d=Path(td)
        with zipfile.ZipFile(DIST) as z: z.extractall(d/'package')
        script=d/'package/wangbin-meeting-action-tracker/scripts/track.py'
        check('clean extraction', str(script), 'script present', script.is_file())
        counter=[0]
        def run(label, meeting, previous=None, supplement=None, correction=None, date=None, mode='export', draft=False, ext='md', out=None):
            counter[0]+=1
            case=d/('case'+str(counter[0]));case.mkdir()
            if isinstance(meeting, Path): mf=meeting
            else: mf=file(case/('meeting.'+ext),meeting)
            output=out or case/'out'
            if out is None: output.mkdir()
            cmd=[sys.executable,str(script),'--meeting-file',str(mf),'--project-name','蓝桥演练','--response-mode',mode,'--output-dir',str(output)]
            if previous: cmd+=['--previous-tasks',str(previous)]
            for s in supplement or []: cmd+=['--supplemental-evidence',str(s)]
            for s in correction or []: cmd+=['--correction',s]
            if date: cmd+=['--check-date',date]
            if draft: cmd+=['--draft-followup']
            p=subprocess.run(cmd,capture_output=True,text=True)
            try: obj=json.loads(p.stdout if p.returncode==0 else p.stderr)
            except ValueError: obj={'raw_stdout':p.stdout[-1000:],'raw_stderr':p.stderr[-1000:]}
            obj['exit']=p.returncode
            obj['command']=cmd
            if p.returncode==0 and mode=='export' and 'xlsx' in obj:
                obj['sheets'],obj['headers'],obj['values']=rows(obj['xlsx'])
            return obj,mf,output
        def task(r,tid): return next((t for t in r.get('sheets',{}).get('当前任务',[]) if t['task_id']==tid),{})
        def history(r): return r.get('sheets',{}).get('状态历史',[])
        base='2026-11-06 蓝桥演练例会。T02 经会议明确取消，原因：模拟需求撤回。新增事项：检查演练接口 T03；建议由李工负责，尚未获其接受。'
        old=d/'old.csv'
        with old.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f);w.writerow(HEADERS[0]);w.writerow(['T01','整理演练清单','王工','已确认','2026-11-05','已确认','进行中','','','','old.csv:行2','']);w.writerow(['T02','准备演练培训','','','','','待执行','','','','old.csv:行3',''])
        oldhash=sha(old)
        r,mf,_=run('CORE',base,old)
        check('CORE sheets/open', {'exit':r['exit'],'names':list(r.get('sheets',{})),'headers':r.get('headers')}, 'four exact ordered sheets and headers',r['exit']==0 and list(r['sheets'])==SHEETS and list(r['headers'].values())==HEADERS)
        new=[t for t in r['sheets']['当前任务'] if t['task_id'] not in ('T01','T02')]
        check('CORE old/new proposal', {'T01':task(r,'T01'),'T02':task(r,'T02'),'new':new,'history':history(r),'questions':r['sheets']['待确认事项']}, 'T01 unchanged, T02 canceled, one new not confirmed owner',task(r,'T01').get('执行状态')=='进行中' and task(r,'T01').get('最近变更')=='无新增进展' and task(r,'T02').get('执行状态')=='取消' and len(new)==1 and all(t.get('负责人确认状态')!='已确认' for t in new))
        check('A11 missing check date and canceled',{'T01':task(r,'T01').get('是否逾期'),'T02':task(r,'T02').get('是否逾期')},'T01 unknown, T02 not overdue',task(r,'T01').get('是否逾期')=='无法判断' and task(r,'T02').get('是否逾期')=='否')
        rdate,_,_=run('A11 date',base,old,date='2026-11-06')
        check('A11 explicit date',task(rdate,'T01'),'overdue yes with due and check dates',task(rdate,'T01').get('是否逾期')=='是' and all(s in task(rdate,'T01').get('逾期判断依据','') for s in ['2026-11-05','2026-11-06']))
        a02='2026-11-06 蓝桥演练例会。决定新增：编写演练纪要，由周工确认负责。'
        first,_,_=run('A02',a02)
        born=first.get('sheets',{}).get('当前任务',[])
        check('A02 first confirmed owner', born,'one new task and confirmed 周工, sourced new event',first['exit']==0 and len(born)==1 and born[0].get('负责人')=='周工' and born[0].get('负责人确认状态')=='已确认' and any(e['事件类型']=='新增' for e in history(first)))
        second,_,_=run('A03 duplicate',a02,Path(first['xlsx']))
        check('A03 repeated import',{'ids':[t['task_id'] for t in second.get('sheets',{}).get('当前任务',[])],'events':[e['event_id'] for e in history(second)]},'identical IDs and event IDs/count',second['exit']==0 and {t['task_id'] for t in born}=={t['task_id'] for t in second['sheets']['当前任务']} and {e['event_id'] for e in history(first)}=={e['event_id'] for e in history(second)} and len(history(first))==len(history(second)))
        reorder_a,_,_=run('A03 initial order','2026-11-06 蓝桥演练例会。新增事项：检查演练接口 A。新增事项：检查演练接口 B。')
        reorder_b,_,_=run('A03 reordered','2026-11-06 蓝桥演练例会。新增事项：检查演练接口 B。新增事项：检查演练接口 A。',Path(reorder_a['xlsx']))
        check('A03 reordered IDs/events',{'initial_ids':[t['task_id'] for t in reorder_a['sheets']['当前任务']],'reordered_ids':[t['task_id'] for t in reorder_b['sheets']['当前任务']],'initial_events':[e['event_id'] for e in history(reorder_a)],'reordered_events':[e['event_id'] for e in history(reorder_b)]},'same two IDs/events after reordered import', {t['task_id'] for t in reorder_a['sheets']['当前任务']}=={t['task_id'] for t in reorder_b['sheets']['当前任务']} and {e['event_id'] for e in history(reorder_a)}=={e['event_id'] for e in history(reorder_b)})
        a04,_,_=run('A04','2026-11-06 蓝桥演练例会。新增事项：检查演练接口 A。新增事项：检查演练接口 B。',old)
        check('A04 distinct similar', [t['任务内容'] for t in a04.get('sheets',{}).get('当前任务',[])], 'A and B separate', a04['exit']==0 and len(a04['sheets']['当前任务'])==4)
        a05,_,_=run('A05','2026-11-06 蓝桥演练例会。T01 现改由周工负责，周工确认接受 T01。',old)
        check('A05 owner handover',{'task':task(a05,'T01'),'events':history(a05)},'周工 confirmed; event 王工→周工',task(a05,'T01').get('负责人')=='周工' and task(a05,'T01').get('负责人确认状态')=='已确认' and any(e['原值']=='王工' and e['新值']=='周工' for e in history(a05)))
        a06,_,_=run('A06','2026-11-06 蓝桥演练例会。T01 明天交。',old)
        check('A06 tomorrow', task(a06,'T01'),'2026-11-07 and source baseline 2026-11-06',task(a06,'T01').get('截止时间')=='2026-11-07' and '2026-11-06' in str(history(a06)))
        a07,_,_=run('A07','T01 明天交。',old)
        check('A07 no baseline',{'task':task(a07,'T01'),'questions':a07.get('sheets',{}).get('待确认事项')},'old due unchanged; pending no meeting date',task(a07,'T01').get('截止时间')=='2026-11-05' and bool(a07.get('sheets',{}).get('待确认事项')))
        a08,_,_=run('A08 report','2026-11-06 蓝桥演练例会。T01 已完成。',old)
        check('A08 report alone',task(a08,'T01'),'report complete, no evidence',task(a08,'T01').get('执行状态')=='报告完成' and not task(a08,'T01').get('完成证据'))
        a08b,_,_=run('A08 evidence','2026-11-07 蓝桥演练例会。T01 验收单 E-7 已签收。',Path(a08['xlsx']))
        check('A08 evidence later',{'task':task(a08b,'T01'),'events':history(a08b)},'evidence complete with both events and caveat',task(a08b,'T01').get('执行状态')=='证据确认完成' and '未独立核验' in str(task(a08b,'T01').get('完成证据')) and any(e['事件类型']=='报告完成' for e in history(a08b)))
        for seq in (['T01 进行中','T01 取消'],['T01 取消','T01 进行中']):
            rr,_,_=run('A09','2026-11-06 蓝桥演练例会。',old,supplement=seq)
            check('A09 conflict '+str(seq),{'task':task(rr,'T01'),'history':history(rr),'questions':rr.get('sheets',{}).get('待确认事项')},'original 进行中, conflict and pending both sources',task(rr,'T01').get('执行状态')=='进行中' and any(e['事件类型']=='冲突' for e in history(rr)) and bool(rr.get('sheets',{}).get('待确认事项')))
        cancel,_,_=run('A10 cancel','2026-11-06 蓝桥演练例会。T02 经会议明确取消。',old)
        reopen,_,_=run('A10 reopen','2026-11-07 蓝桥演练例会。会议决定重新开启 T02。',Path(cancel['xlsx']))
        check('A10 reopen',{'T02':task(reopen,'T02'),'events':history(reopen)},'cancel and reopen events with original values',task(reopen,'T02').get('执行状态')=='待执行' and any(e['事件类型']=='取消' for e in history(reopen)) and any(e['事件类型']=='重新开启' for e in history(reopen)))
        proposal,_,_=run('A10 proposed reopen','2026-11-07 蓝桥演练例会。考虑重开 T02。',Path(cancel['xlsx']))
        check('A10 proposed',task(proposal,'T02'),'still canceled',task(proposal,'T02').get('执行状态')=='取消')
        one,_,_=run('A12 one sentence',base,old,mode='one_sentence')
        check('A12 one sentence',one,'one short sentence, no files, no claimed send',one['exit']==0 and one['summary'].count('。')==1 and len(one['summary'])<100 and not (one.get('xlsx') or one.get('followup_draft')))
        ev,_,_=run('A13 scoped evidence','2026-11-06 蓝桥演练例会。',old,supplement=['T02 交付确认记录 E-9 已签收'])
        check('A13 scoped evidence',{'T01':task(ev,'T01'),'T02':task(ev,'T02')},'T01 unchanged and evidence scoped to T02',task(ev,'T01').get('执行状态')=='进行中' and task(ev,'T01').get('最近变更')=='无新增进展' and 'E-9' in str(task(ev,'T02').get('完成证据')))
        follow,_,_=run('E07 draft explicit','2026-11-06 蓝桥演练例会。',old,draft=True)
        check('E07 draft',follow.get('followup_draft'),'labeled unsent draft only on request','草稿' in follow.get('followup_draft','') and '未发送' in follow.get('followup_draft','') and not r.get('followup_draft'))
        doc=d/'fictional.docx';Document().save(doc)
        dc=Document(doc);dc.add_paragraph('2026-11-06 蓝桥演练例会。决定新增：编写演练纪要，由周工确认负责。');dc.save(doc)
        docr,_,_=run('DOCX input',doc)
        check('DOCX read',docr.get('exit'),'zero with one task',docr['exit']==0 and len(docr['sheets']['当前任务'])==1)
        csvhash=sha(old)
        invalid=d/'fake.docx';file(invalid,'not a zip')
        for label,meeting,prev,expected in [('fake DOCX',invalid,old,'CORRUPT_INPUT'),('invalid extension',file(d/'bad.pdf','bad'),old,'INVALID_FORMAT'),('invalid CSV',file(d/'valid-for-csv.md','2026-11-06 蓝桥演练例会。'),file(d/'invalid.csv','bad,head\na,b\n'),'INVALID_PREVIOUS_SCHEMA'),('blank meeting',file(d/'empty.txt',' \n'),old,'EMPTY_MEETING')]:
            rr,_,_=run(label,meeting,prev if prev else (d/'invalid.csv' if label=='invalid CSV' else old))
            check('A14 '+label,{'exit':rr['exit'],'status':rr.get('status'),'old_sha':sha(old)},expected+' exit 2, old unchanged',rr['exit']==2 and rr.get('status')==expected and sha(old)==csvhash)
        formula,_,_=run('E05 formula','2026-11-06 蓝桥演练例会。决定新增：=HYPERLINK("https://invalid.test", "click")。决定新增：+1。决定新增：@网络。')
        cells=[c for vals in formula.get('values',{}).values() for row in vals[1:] for c in row]
        wb=load_workbook(formula['xlsx'],read_only=True,data_only=False)
        types=[c.data_type for ws in wb for row in ws.iter_rows() for c in row]
        wb.close()
        check('E05 formula',{'types':set(types),'leading':[str(c)[:30] for c in cells if isinstance(c,str) and c.startswith("'")]},'no formula cells',formula['exit']==0 and 'f' not in types and any(str(c).startswith("'=") for c in cells))
        suggestion,_,_=run('E01 proposal','2026-11-06 蓝桥演练例会。建议周工负责 T01。',old)
        check('E01 owner proposed',{'task':task(suggestion,'T01'),'pending':suggestion['sheets']['待确认事项']},'王工 remains confirmed; 周工 pending',task(suggestion,'T01').get('负责人')=='王工' and bool(suggestion['sheets']['待确认事项']))
        corrected,_,_=run('E02 correction','2026-11-06 蓝桥演练例会。',old,correction=['将 T01 截止日更正为 2026-11-10'])
        check('E02 explicit correction',{'task':task(corrected,'T01'),'history':history(corrected)},'new due, old/new event',task(corrected,'T01').get('截止时间')=='2026-11-10' and any(e['原值']=='2026-11-05' and e['新值']=='2026-11-10' for e in history(corrected)))
        duplicate=d/'duplicate.csv'
        with duplicate.open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f);w.writerow(HEADERS[0]);w.writerow(['T01','事项甲','','','','','待执行']);w.writerow(['T01','事项乙','','','','','待执行'])
        dup,_,_=run('E06 duplicate','2026-11-06 蓝桥演练例会。',duplicate)
        check('E06 duplicate ID',{'exit':dup['exit'],'status':dup.get('status')},'DUPLICATE_TASK_ID exit 2',dup['exit']==2 and dup.get('status')=='DUPLICATE_TASK_ID')
        already,_,_=run('E06 existing output',base,old,out=Path(r['xlsx']).parent)
        check('E06 existing output protected',{'exit':already['exit'],'status':already.get('status'),'original_sha':sha(r['xlsx'])},'OUTPUT_FAILED, original workbook intact',already['exit']==2 and already.get('status')=='OUTPUT_FAILED' and Path(r['xlsx']).is_file())
        skill=(d/'package/wangbin-meeting-action-tracker/SKILL.md').read_text(encoding='utf-8')
        requirements=(ROOT/'docs/products/wangbin-meeting-action-tracker/requirements.md').read_text(encoding='utf-8')
        prompts=['对照上次任务表和这次会议记录，更新任务进展，没有提到的任务不要自动算完成。','把这次会议新增的决议、负责人和截止时间整理出来，不明确的地方单独标记。','这些是补充的完成记录，请更新任务表，并帮我写一段下一次例会前的跟进消息。','Update the previous action list using these meeting notes. Do not mark unmentioned tasks as completed.','Extract new decisions, owners, and deadlines, clearly marking anything not yet confirmed.','Use these completion records to update the action list and draft a follow-up message before the next meeting.']
        check('E08 six literal prompts',{'present_skill':[p in skill for p in prompts],'present_requirements':[p in requirements for p in prompts]},'six exact both',all(p in skill and p in requirements for p in prompts))
        check('old input immutable',sha(old),oldhash,sha(old)==oldhash)
    return records
if __name__=='__main__':
    out=main()
    destination=Path(__file__).with_name('qa-evidence-0.1.0.json')
    destination.write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps({'cases':len(out),'failed':[r['case'] for r in out if r['verdict']=='FAIL'],'evidence':str(destination)},ensure_ascii=False))
    sys.exit(1 if any(r['verdict']=='FAIL' for r in out) else 0)
