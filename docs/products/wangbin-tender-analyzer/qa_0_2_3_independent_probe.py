"""Independent 0.2.3 ZIP rerun; old 0.2.1/0.2.2 FAIL probes/evidence stay untouched."""
import csv
import hashlib
import json
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import zipfile
from collections import Counter
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[3]
ZIP = ROOT / 'dist/wangbin-tender-analyzer-0.2.3-skill-candidate.zip'
MANIFEST = ZIP.with_name(ZIP.name + '.manifest.json')
CASES = []
SCRATCH = Path(os.environ['HERMES_HOME']) / 'cache' / 'scratch'
SCRATCH.mkdir(parents=True, exist_ok=True)


def record(name, expected, actual, passed, command=None):
    CASES.append(dict(case=name, expected=expected, actual=actual, pass_=bool(passed), command=command))


def text(path, value):
    path.write_text(value, encoding='utf-8')
    return path


def exercise(script, base, name, tender, response=None, amendments=(), catalog=None, evidence=None, mode=None, project=None):
    work = base / name
    work.mkdir()
    t = text(work / 'tender.txt', tender)
    cmd = [sys.executable, str(script), '--tender', str(t), '--output-dir', str(work)]
    if response is not None:
        cmd += ['--response', str(text(work / 'response.txt', response))]
    for i, item in enumerate(amendments):
        cmd += ['--amendment', str(text(work / ('amendment-' + str(i) + '.txt'), item))]
    if catalog is not None:
        cat = work / ('catalog.xlsx' if isinstance(catalog, list) else 'catalog.csv')
        if isinstance(catalog, list):
            book = Workbook(); book.active.title = '附件清单'
            for row in catalog: book.active.append(row)
            book.save(cat)
        else:
            text(cat, catalog)
        cmd += ['--attachment-catalog', str(cat)]
    if evidence:
        for filename, content in evidence.items():
            cmd += ['--evidence-file', str(text(work / filename, content))]
    if mode: cmd += ['--mode', mode]
    if project: cmd += ['--project', project]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    output = sorted(p.name for p in work.glob('*投标响应检查.xlsx'))
    output += sorted(p.name for p in work.glob('*提交前核对清单.md'))
    result = dict(exit=proc.returncode, stdout=proc.stdout.strip()[:400], stderr=proc.stderr.strip()[:400], files=output, command=[str(x).replace(str(base), '<QA_SCRATCH>') for x in cmd])
    if proc.returncode == 0:
        x = next(work.glob('*投标响应检查.xlsx'))
        book = load_workbook(x, data_only=False)
        result['sheets'] = book.sheetnames
        headings = [cell.value for cell in book.worksheets[1][1]]
        result['matrix'] = [dict(zip(headings, [c.value for c in line])) for line in list(book.worksheets[1])[1:]]
        result['versions'] = [[c.value for c in row] for row in list(book.worksheets[3])[1:]]
        result['overview'] = [[c.value for c in row] for row in book.worksheets[0]]
        result['attachment_rows'] = [[c.value for c in row] for row in list(book.worksheets[2])[1:]]
        result['formulas'] = [(s.title,c.coordinate) for s in book for row in s for c in row if c.data_type == 'f']
        book.close()
        result['md'] = next(work.glob('*提交前核对清单.md')).read_text(encoding='utf-8')
        result['sha256'] = hashlib.sha256(x.read_bytes()).hexdigest()
    return result


def row(r, i=0):
    return r['matrix'][i]


def check(label, r, expected, actual, condition):
    record(label, expected, actual, condition, r.get('command'))


def main():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    digest = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    side = ZIP.with_name(ZIP.name + '.sha256').read_text().split()[0]
    check('ZIP_SHA', {}, manifest['sha256'], digest, digest == manifest['sha256'] == side == '5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce')
    catalog = json.loads((ROOT / 'products/catalog.json').read_text(encoding='utf-8'))
    check('ZIP_CATALOG_VERSION', {}, '0.2.3 registered', '0.2.3' in str(catalog), '0.2.3' in str(catalog) and manifest['version'] == '0.2.3')
    with tempfile.TemporaryDirectory(prefix='bid-qa-', dir=SCRATCH) as temp:
        root = Path(temp); extraction = root / 'extract'; extraction.mkdir()
        with zipfile.ZipFile(ZIP) as z:
            check('ZIP_CRC', {}, None, z.testzip(), z.testzip() is None)
            actual_names = z.namelist()
            expected_names = [m['path'] for m in manifest['members']]
            check('ZIP_MEMBERS', {}, expected_names, actual_names, actual_names == expected_names)
            safe_unique = len(actual_names) == len(set(actual_names)) == 11 and all(not (p.startswith('/') or '..' in Path(p).parts or '\\' in p) for p in actual_names)
            check('ZIP_SAFE_UNIQUE', {}, '11 non-traversal unique members', actual_names, safe_unique)
            for m in manifest['members']:
                data = z.read(m['path'])
                check('ZIP_MEMBER_' + m['path'], {}, m['sha256'], hashlib.sha256(data).hexdigest(), hashlib.sha256(data).hexdigest() == m['sha256'] and len(data) == m['size'] and (ROOT / manifest['source'] / m['path'].split('/',1)[1]).read_bytes() == data)
            z.extractall(extraction)
        script = extraction / 'wangbin-tender-analyzer/scripts/check_response.py'
        def run(name, tender, response=None, amendments=(), catalog=None, evidence=None, mode=None, project=None):
            return exercise(script, root, name, tender, response, amendments, catalog, evidence, mode, project)
        five = ['核查概览', '要求响应矩阵', '附件核对', '补遗与版本', '待确认事项']
        core = run('core', '1. 必须提供指定资质证明 qualification.txt。\n', '1. 我方具备该资质。\n', catalog='附件名称\nqualification.txt\n')
        if core['exit'] != 0: raise RuntimeError('CORE command failed: ' + repr(core))
        check('CORE_five_sheets', core, five, core.get('sheets'), core.get('sheets') == five and not core.get('formulas'))
        check('CORE_no_fake_evidence', core, '仅目录登记 / 未核验 / 不充分', [row(core).get(k) for k in ('附件实际提供状态','内容支持状态','条件覆盖状态')], row(core).get('附件实际提供状态') == '仅目录登记' and row(core).get('内容支持状态') == '未核验' and row(core).get('条件覆盖状态') != '已覆盖（文本层面）' and 'catalog.csv:2' in str(core.get('attachment_rows')) and 'response.txt:1' in str(row(core)))
        prep = run('prepare', '9. 必须附报价函。\n')
        check('A09_prep', prep, '未核查、不报未找到', [row(prep).get('响应存在状态'), row(prep).get('条件覆盖状态')], row(prep).get('响应存在状态') == row(prep).get('条件覆盖状态') == '未核查' and '响应未核查' in prep.get('md',''))
        miss = run('missing_response', '9. 必须附报价函。\n', mode='check')
        check('A09_missing_check', miss, 'MISSING_RESPONSE exit2, no products', miss, miss['exit'] == 2 and 'MISSING_RESPONSE' in miss['stderr'] and not miss['files'])
        a02 = run('a02', '2. 须说明运维响应时间。\n', '1. 我方具备资质。\n')
        check('A02_unanswered', a02, '未找到', row(a02).get('响应存在状态'), row(a02).get('响应存在状态') == '未找到（限已提供响应）')
        a03 = run('a03', '3. 技术方案必须同时说明备份周期和恢复时间。\n', '3. 每日备份。\n')
        check('A03_partial', a03, '已定位/可能不充分/恢复时间', row(a03), row(a03).get('响应存在状态') == '已定位' and row(a03).get('条件覆盖状态') == '可能不充分' and '恢复时间' in str(row(a03).get('缺口')))
        a04 = run('a04', '4. 提供有效期覆盖2027年的资质证明。\n', '4. 资质有效期覆盖2027年，见 certificate.txt。\n', evidence={'certificate.txt':'本证明有效期至2026年12月31日。\n'})
        check('A04_conflicting_certificate', a04, '已提供/不支持', dict(states=[row(a04).get(k) for k in ('附件实际提供状态','内容支持状态')], matrix=row(a04), attachment_rows=a04.get('attachment_rows'), md=a04.get('md','')[:700], exit=a04['exit']), row(a04).get('附件实际提供状态') == '已提供（可读文本）' and row(a04).get('内容支持状态') == '不支持（文本层面）' and 'certificate.txt:1' in str(row(a04)))
        a04_md = str(a04.get('md', ''))
        a04_lines = [line for line in a04_md.splitlines() if '1:1:4' in line]
        check('A04_MD_and_provenance', a04, 'Each A04 MD checklist entry includes both source lines; status and attachment row agree', a04_md, len(a04_lines) >= 3 and all(s in a04_md for s in ('已提供（可读文本）','不支持（文本层面）','certificate.txt:1','response.txt:1')) and 'certificate.txt:1' in str(a04.get('attachment_rows')) and all('certificate.txt:1' in line and 'response.txt:1' in line for line in a04_lines))
        cross = run('cross_requirement', '1. 须提供证书。\n2. 须提供2027年有效证书。\n', '1. 资质有效期覆盖2027年，见 certificate.txt。\n', evidence={'certificate.txt':'本证明有效期至2026年12月31日。\n'})
        check('A04_no_cross_requirement_leak', cross, '证书不得无条件跨编号应用于第二条', [dict(id=r.get('唯一ID'), attachment=r.get('附件实际提供状态'), content=r.get('内容支持状态'), evidence=r.get('支持材料/证据位置')) for r in cross.get('matrix',[])], cross.get('exit') == 0 and len(cross.get('matrix',[])) == 2 and row(cross,1).get('附件实际提供状态') != '已提供（可读文本）')
        a05 = run('a05', '5. 交付期为30日。\n', '5. 交付期30日。\n', amendments=['正式补遗第1号：原第5条交付期30日替换为45日。\n'])
        check('A05_proven_supersession', a05, '旧不适用/新适用/版本冲突', [(r.get('适用版本'),r.get('缺口')) for r in a05.get('matrix',[])], len(a05.get('matrix',[])) == 2 and row(a05).get('适用版本') == '已替换/撤销（不适用）' and row(a05,1).get('适用版本') == '适用（正式补遗）' and '版本冲突' in str(row(a05,1).get('缺口')))
        a06 = run('a06', '6. 提供纸质两份。\n', '6. 提供纸质一份。\n', amendments=['正式补遗A：原第6条改为纸质一份。\n','正式补遗B：原第6条改为纸质三份。\n'])
        check('A06_conflicting_amendments', a06, '三条均待确认', [r.get('适用版本') for r in a06.get('matrix',[])], len(a06.get('matrix',[])) == 3 and all('待确认' in str(r.get('适用版本')) for r in a06['matrix']))
        a07 = run('a07', '7. 系统须支持离线查询。\n', '7a. 系统支持离线查询。\n')
        check('A07_renumber_candidate', a07, '候选待确认，双向原句', row(a07), row(a07).get('响应存在状态') == '候选待确认' and 'response.txt:1' in str(row(a07)) and 'tender.txt:1' in str(row(a07)))
        a08 = run('a08', '8. 提供同城双活灾备方案。\n', '8. 我方提供异地冷备方案。\n9. 我方提供同城双活机房简介。\n')
        check('A08_no_keyword_hijack', a08, '已定位但未覆盖', row(a08), row(a08).get('响应存在状态') == '已定位' and row(a08).get('条件覆盖状态') != '已覆盖（文本层面）')
        a11 = run('a11', '1. 必须提供指定资质证明 qualification.txt。\n2. 须说明运维响应时间。\n', '1. 我方具备该资质。\n', catalog='附件名称\nqualification.txt\n', evidence={'qualification.txt':'仅说明拟申请资质，尚未取得。\n'})
        check('A11_incremental_no_false_support', a11, '第一条实际存在但不支持；第二条不受影响', [row(a11).get('附件实际提供状态'),row(a11).get('内容支持状态'),row(a11,1).get('响应存在状态')], row(a11).get('附件实际提供状态') == '已提供（可读文本）' and row(a11).get('内容支持状态') != '支持（文本层面）' and row(a11,1).get('响应存在状态') == '未找到（限已提供响应）')
        a14 = run('a14', '10. 须附有效资质与近三年案例，投标截止日期另行通知。\n', '10. 我方正在准备材料。\n')
        check('A14_no_invented_facts', a14, '无臆造证书/日期/中标率', a14.get('md','')[:650], not any(x in a14.get('md','') for x in ('证书号：','2027年12月31日','必然废标','中标率：')))
        unofficial = run('unofficial', '1. 提供纸质两份。\n', '1. 提供纸质两份。\n', amendments=['最终版：请提交三份。\n'])
        check('BID05_no_unproven_edge', unofficial, '无已证明替换', unofficial.get('versions'), len(unofficial.get('versions',[])) == 1 and unofficial['versions'][0][0] == '无已证明正式替换关系')
        duplicates = run('duplicate_ids', '1. 须提交A证明。\n第二章 1. 须提交B证明。\n', '1. 须提交A证明。\n', amendments=['1. 请说明C材料。\n'])
        check('BID01_duplicate_ids', duplicates, '3 unique IDs, all original lines', [(r['唯一ID'],r['来源']) for r in duplicates.get('matrix',[])], len(duplicates.get('matrix',[])) == 3 and len({r['唯一ID'] for r in duplicates['matrix']}) == 3)
        xcat = run('xlsx_catalog', '1. 必须提供 qualification.txt。\n', '1. 已附 qualification.txt。\n', catalog=[['附件名称','关联要求编号'],['qualification.txt','1']])
        check('XLSX_catalog', xcat, 'five sheets + catalog.xlsx/附件清单:2', xcat.get('attachment_rows'), xcat.get('sheets') == five and 'catalog.xlsx/附件清单:2' in str(xcat.get('attachment_rows')))
        count_ok = all(Counter(r.get(d) for r in core['matrix']) == Counter({rec[1]: rec[2] for rec in core['overview'] if len(rec)>2 and rec[0]==d and isinstance(rec[2],int)}) for d in ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态'))
        check('overview_matrix_counts', core, 'counts agree with matrix', count_ok, count_ok)
        check('MD_matrix_consistency', core, 'IDs and four states present', core['md'][:750], all(str(row(core)[key]) in core['md'] for key in ('唯一ID','响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态')))
        for label, kwargs, code in [
            ('invalid_utf8', {'tender':'1. 正常。\n','response':'1. 正常。\n'}, 'INVALID_UTF8'),
            ('pdf_response', {'tender':'1. 正常。\n','response':'1. 正常。\n'}, 'INPUT_TYPE_UNSUPPORTED'),
            ('bad_xlsx', {'tender':'1. 正常。\n','response':'1. 正常。\n'}, 'CATALOG_READ_FAILED'),
            ('unsafe_project', {'tender':'1. 正常。\n','response':'1. 正常。\n','project':'../escape'}, 'OUTPUT_PATH_INVALID')]:
            r = run(label, **kwargs)
            folder = root / label
            for generated in folder.glob('*投标响应检查.xlsx'): generated.unlink()
            for generated in folder.glob('*提交前核对清单.md'): generated.unlink()
            if label == 'invalid_utf8': (folder/'response.txt').write_bytes(b'\xff\xfe')
            if label == 'pdf_response': (folder/'response.txt').rename(folder/'response.pdf')
            if label == 'bad_xlsx': (folder/'catalog.xlsx').write_bytes(b'bad spreadsheet') if (folder/'catalog.xlsx').exists() else None
            cmd = [sys.executable,str(script),'--tender',str(folder/'tender.txt'),'--response',str(folder/('response.pdf' if label=='pdf_response' else 'response.txt')),'--output-dir',str(folder)]
            if label == 'bad_xlsx':
                (folder/'catalog.xlsx').write_bytes(b'bad spreadsheet'); cmd += ['--attachment-catalog',str(folder/'catalog.xlsx')]
            if label == 'unsafe_project': cmd += ['--project','../escape']
            proc = subprocess.run(cmd, text=True, capture_output=True)
            check(label, {}, code, dict(exit=proc.returncode, stderr=proc.stderr[:300]), proc.returncode == 2 and ('ERROR '+code) in proc.stderr and not str(root) in proc.stderr)
        malicious = run('formula', '1. 必须提供 =HYPERLINK("https://invalid.example","x") 文件。\n', '1. 已处理。\n', catalog='附件名称\n=HYPERLINK("https://invalid.example","x")\n')
        check('formula_cells', malicious, 'no formulas', malicious.get('formulas'), malicious.get('formulas') == [])
        old = extraction / 'wangbin-tender-analyzer/scripts/analyze_tender.py'
        sample = extraction / 'wangbin-tender-analyzer/examples/fictional-tender.txt'
        proc = subprocess.run([sys.executable,str(old),'--input',str(sample)], text=True, capture_output=True)
        obj = json.loads(proc.stdout) if proc.returncode == 0 else {}
        expected = json.loads((extraction/'wangbin-tender-analyzer/examples/fictional-tender.expected.json').read_text(encoding='utf-8'))
        check('OLD_CLI_JSON', {}, 'exit0 JSON exact old fixture', dict(exit=proc.returncode, match=obj==expected, keys=list(obj)), proc.returncode == 0 and obj == expected)
        proc2 = subprocess.run([sys.executable,str(old),'--input',str(root/'none.txt')],text=True,capture_output=True)
        check('OLD_CLI_ERROR', {}, 'exit2 INPUT_NOT_FOUND', dict(exit=proc2.returncode, stderr=proc2.stderr[:200]), proc2.returncode == 2 and 'INPUT_NOT_FOUND' in proc2.stderr)
    destination = ROOT/'docs/products/wangbin-tender-analyzer/qa-0.2.3-evidence.json'
    destination.write_text(json.dumps({'tested_commit':'27b14faf57a77e20ffdf68034f0f028004c49d2a','archive_sha256':digest,'case_count':len(CASES),'passed':sum(c['pass_'] for c in CASES),'cases':CASES},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('cases',len(CASES),'passed',sum(c['pass_'] for c in CASES),'failed',[c['case'] for c in CASES if not c['pass_']]); print('evidence',destination)
    return 0 if all(c['pass_'] for c in CASES) else 1


if __name__ == '__main__':
    raise SystemExit(main())
