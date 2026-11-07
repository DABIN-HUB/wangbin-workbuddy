"""Read-only verification of genuine Hermes three-turn run against extracted ZIP outputs."""
import hashlib
import json
from pathlib import Path
from openpyxl import load_workbook
base = Path.home() / 'AppData/Local/hermes/profiles/wb-quality/cache/scratch/q01-015-independent-t_c8518a89'
out = base / 'l4-output'
source = base / 'regression/source.csv'
expected_source = hashlib.sha256(source.read_bytes()).hexdigest()
result = {'source_sha256': expected_source, 'reference_new_sha256': hashlib.sha256((base/'l4-reference-updated.csv').read_bytes()).hexdigest(),'runs':{},'assertions':[]}
def check(condition, label):
    result['assertions'].append({'check':label,'pass':bool(condition)})
for postfix in ('','-run1'):
    paths = {part:out/f'source-{label}{postfix}.xlsx' for part,label in [('report','导入预检'),('candidate','候选导入'),('quarantine','隔离记录')]}
    data = {'files':{},'tables':{}}
    for part,path in paths.items():
        check(path.is_file(),f'{postfix} {part} present')
        if path.is_file():
            data['files'][part] = {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            wb = load_workbook(path,read_only=True,data_only=False)
            data['tables'][part] = {ws.title:list(ws.values) for ws in wb.worksheets}
            wb.close()
    result['runs'][postfix or 'first'] = data
    report = data['tables'].get('report',{})
    overview = dict(report.get('检查概览',[])[1:])
    check(overview.get('源SHA256') == expected_source, f'{postfix} report source SHA')
    check(overview.get('问题条数') == ('3' if postfix else '4'),f'{postfix} finding count')
    check(len(data['tables'].get('candidate',{}).get('候选数据',[])) == 2,f'{postfix} candidate one row')
    check(len(data['tables'].get('quarantine',{}).get('隔离记录',[])) == 4,f'{postfix} quarantine three rows')
    categories = [(str(r[4]),r[8]) for r in report.get('问题明细',[])[1:]]
    check(('3','NOT_IN_REFERENCE') in categories if not postfix else ('3','NOT_IN_REFERENCE') not in categories,f'{postfix} R99 reference finding transition')
    if postfix:
        check(overview.get('已解决问题数') == '1' and overview.get('持续问题数') == '3' and overview.get('新增问题数') == '0','old/new finding comparison')
        check(overview.get('旧报告SHA256') == result['runs']['first']['files']['report']['sha256'],'old report immutable hash referenced')
EVIDENCE = Path(__file__).with_name('audit-r1-015-l4-reopen.json')
EVIDENCE.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print(json.dumps({'evidence':str(EVIDENCE),'assertions':len(result['assertions']),'failed':[x['check'] for x in result['assertions'] if not x['pass']]},ensure_ascii=False))
raise SystemExit(1 if any(not x['pass'] for x in result['assertions']) else 0)
