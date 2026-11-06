"""Local, bounded XLSX-to-DOCX number comparison. No network or workbook recalculation."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from xml.etree import ElementTree as ET

from docx import Document
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

SHEETS = ('核查概览', '指标对应', '差异明细', '待确认口径', '未覆盖项')
MAX_BYTES = 12 * 1024 * 1024
MAX_CELLS = 40000
MAX_PARAGRAPHS = 3000
NUMBER = re.compile(r'(?<![\d.])([+-]?\d+(?:,\d{3})*(?:\.\d+)?)(%|亿元|万元|元|人民币元|美元)?')
STATEMENT = re.compile(r'(?:收入|成本|完成率|完成量|目标量|净额|占比|合计)')
CURRENCY = {'USD': 'USD', '美元': 'USD', '人民币': 'CNY', 'CNY': 'CNY', 'RMB': 'CNY'}
SCALE = {'元': Decimal(1), '人民币元': Decimal(1), '万元': Decimal(10000), '亿元': Decimal(100000000), '%': Decimal('0.01')}
FIELDS = ('subject', 'period', 'basis', 'tax', 'currency')


class CheckError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_text(value):
    text = str(value) if value is not None else ''
    leading = text.lstrip()
    return "'" + text if leading.startswith(('=', '+', '@', '\t', '\r')) or leading.startswith('-') and not re.fullmatch(r'-\d+(?:\.\d+)?', leading) else text


def safe_file(path, suffix, root):
    p = Path(path)
    if not p.exists():
        raise CheckError('INPUT_MISSING', f'{suffix} input missing')
    if p.suffix.lower() != suffix or p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
        raise CheckError('UNSUPPORTED_OR_SPOOFED', f'{suffix} input must be a regular file under input-root')
    if p.stat().st_size > MAX_BYTES:
        raise CheckError('RESOURCE_LIMIT', f'file exceeds {MAX_BYTES} bytes')
    try:
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            required = 'xl/workbook.xml' if suffix == '.xlsx' else 'word/document.xml'
            if required not in names or len(names) > MAX_CELLS or any(n.startswith('/') or '..' in Path(n).parts or '\\' in n for n in names):
                raise CheckError('UNSUPPORTED_OR_SPOOFED', 'invalid OOXML members')
            if any('externalLink' in n or 'vbaProject' in n or n.endswith('.bin') for n in names):
                raise CheckError('UNSUPPORTED_OR_SPOOFED', 'external links/macros/embedded binary forbidden')
            if sum(x.file_size for x in z.infolist()) > 40 * MAX_BYTES:
                raise CheckError('RESOURCE_LIMIT', 'expanded archive exceeds limit')
            for n in names:
                if n.endswith('.rels'):
                    rel = ET.fromstring(z.read(n))
                    if any(x.attrib.get('TargetMode') == 'External' for x in rel):
                        raise CheckError('UNSUPPORTED_OR_SPOOFED', 'external relationship forbidden')
    except (zipfile.BadZipFile, ET.ParseError, RuntimeError, OSError) as exc:
        raise CheckError('UNREADABLE_OR_ENCRYPTED', 'cannot read OOXML container') from exc
    return p


def identity(text, context):
    result = {k: context.get(k, '') for k in FIELDS}
    for token, name in CURRENCY.items():
        if token in text:
            result['currency'] = name
            break
    if '未税' in text:
        result['tax'] = '未税'
    elif '含税' in text:
        result['tax'] = '含税'
    if '预算' in text:
        result['basis'] = '预算'
    elif '实际' in text:
        result['basis'] = '实际'
    if '累计' in text:
        result['period'] = '累计:' + (re.search(r'(\d{1,2})月', text).group(1) if re.search(r'(\d{1,2})月', text) else str(result['period']))
    elif '本月' in text or re.search(r'\d{1,2}月', text):
        result['period'] = '本月:' + (re.search(r'(\d{1,2})月', text).group(1) if re.search(r'(\d{1,2})月', text) else str(result['period']))
    for known in context.get('subjects', []):
        if known in text:
            result['subject'] = known
    if not result['subject']:
        subject_match = re.search(r'(?:^|[\s/])([\u4e00-\u9fff]{2,8}(?:公司)?)\d{1,2}月', text)
        if subject_match and subject_match.group(1) not in ('本公司', '本月', '累计'):
            result['subject'] = subject_match.group(1)
    # Without an explicit organization, "本公司" cannot resolve to one of several sources.
    return result


def label(text):
    for key in ('完成率', '完成量', '目标量', '净额', '占比', '合计', '收入', '成本'):
        if key in text:
            return key
    return ''


def extract_source(path, context):
    formula = load_workbook(path, read_only=True, data_only=False)
    cached = load_workbook(path, read_only=True, data_only=True)
    rows = []
    total = 0
    for ws in formula:
        if ws.max_row * ws.max_column > MAX_CELLS:
            raise CheckError('RESOURCE_LIMIT', 'sheet cell limit exceeded')
        headers = [str(ws.cell(1, c).value or '') for c in range(1, ws.max_column + 1)]
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                total += 1
                if total > MAX_CELLS:
                    raise CheckError('RESOURCE_LIMIT', 'workbook cell limit exceeded')
                if cell.value is None and cell.data_type != 'f':
                    continue
                header = headers[cell.column - 1] if cell.column <= len(headers) else ''
                # Single merged text header may contain all dimensions.
                combined = ' '.join((ws.title, headers[0] if headers else '', header))
                metric = label(header) or label(combined)
                value = cached[ws.title][cell.coordinate].value if cell.data_type == 'f' else cell.value
                rows.append(dict(sheet=ws.title, cell=cell.coordinate, header=combined, metric=metric,
                                 value=value, formula=cell.value if cell.data_type == 'f' else '',
                                 cache=value if cell.data_type == 'f' else None,
                                 identity=identity(combined, context), percent_format=bool(cell.number_format and '%' in cell.number_format),
                                 unit=('%' if cell.number_format and '%' in cell.number_format else unit_in(combined))))
    return rows


def unit_in(text):
    for unit in ('亿元', '万元', '人民币元', '美元', '元', '%'):
        if unit in text:
            return '元' if unit == '美元' else unit
    return ''


def report_items(path, context):
    doc = Document(path)
    result, uncovered = [], []
    blocks = []
    for i, p in enumerate(doc.paragraphs, 1):
        blocks.append((f'段落{i}', p.text))
    for t, table in enumerate(doc.tables, 1):
        for r, row in enumerate(table.rows, 1):
            for c, cell in enumerate(row.cells, 1):
                blocks.append((f'表格{t}!R{r}C{c}', cell.text))
    if len(blocks) > MAX_PARAGRAPHS:
        raise CheckError('RESOURCE_LIMIT', 'report block limit exceeded')
    for where, text in blocks:
        if re.search(r'^\s*第\s*\d+(?:\.\d+)*\s*节', text):
            continue
        for fragment in re.split(r'[，；;]|(?<!\d),(?!\d)', text):
            metric = label(fragment)
            if not metric:
                continue
            numbers = list(NUMBER.finditer(fragment))
            if not numbers:
                continue
            # Prefer number after metric; for "完成率由10%提高至12%" keep both.
            after = [n for n in numbers if n.start() >= fragment.index(metric) + len(metric)]
            if not after:
                continue
            for n in (after if metric == '完成率' and len(after) == 2 else after[:1]):
                unit = n.group(2) or unit_in(fragment[n.end():n.end()+4]) or unit_in(fragment)
                result.append(dict(where=where, quote=text, metric=metric, value=n.group(1).replace(',', ''),
                                   unit=unit, identity=identity(text, context)))
    if doc.inline_shapes or any('graphic' in p._element.xml or 'pict' in p._element.xml for p in doc.paragraphs):
        uncovered.append(('DOCX', '图片/图表', '图片或图表非正文，需人工复核'))
    uncovered.append(('DOCX', '页眉页脚/脚注/嵌入对象', '不解析这些区域；若存在请人工复核'))
    return result, uncovered


def decimal_value(value):
    try:
        if isinstance(value, bool) or value is None or value == '':
            return None, 'MISSING_OPERAND'
        return Decimal(str(value).replace(',', '')), ''
    except (InvalidOperation, ValueError):
        return None, 'NON_NUMERIC_OPERAND'


def source_rule(rule, sources):
    if not isinstance(rule, dict) or rule.get('op') not in ('direct', 'sum', 'add', 'subtract', 'multiply', 'divide', 'ratio'):
        raise CheckError('INVALID_RULE', 'only structured whitelist rules are accepted')
    addresses = rule.get('cells', [])
    if not isinstance(addresses, list) or not addresses or len(addresses) > 100 or any(not isinstance(a, str) or not re.fullmatch(r'[^!]+![A-Z]+[1-9]\d*', a) for a in addresses):
        raise CheckError('INVALID_RULE', 'explicit bounded cell list required')
    constants = rule.get('constants', [])
    if not isinstance(constants, list) or len(constants) > 10 or any(not re.fullmatch(r'-?\d+(?:\.\d+)?', str(v)) for v in constants):
        raise CheckError('INVALID_RULE', 'constants must be explicit decimal literals')
    found = []
    for address in addresses:
        hit = [s for s in sources if f"{s['sheet']}!{s['cell']}" == address]
        if not hit:
            return None, 'MISSING_OPERAND', addresses, ''
        found.append(hit[0])
    if any(s['formula'] for s in found):
        return None, 'UNVERIFIED_FORMULA_CACHE', addresses, ''
    values = []
    for source in found:
        v, err = decimal_value(source['value'])
        if err:
            return None, err, addresses, ''
        values.append(v * (Decimal(1) if source['percent_format'] else SCALE.get(source['unit'], Decimal(1))))
    values.extend(Decimal(str(v)) for v in constants)
    op = rule['op']
    if op == 'direct' and len(values) != 1 or op in ('divide', 'ratio', 'subtract') and len(values) != 2 or op == 'multiply' and len(values) != 2:
        raise CheckError('INVALID_RULE', 'operand count invalid')
    if len({s['unit'] for s in found}) > 1 and op in ('sum', 'add', 'subtract'):
        if not all(s['unit'] in ('元', '万元', '亿元') for s in found):
            return None, 'NOT_COMPARABLE', addresses, ''
    if op in ('divide', 'ratio') and values[1] == 0:
        return None, 'ZERO_DENOMINATOR', addresses, ''
    calc = {'direct': lambda: values[0], 'sum': lambda: sum(values), 'add': lambda: sum(values),
            'subtract': lambda: values[0]-values[1], 'multiply': lambda: values[0]*values[1],
            'divide': lambda: values[0]/values[1], 'ratio': lambda: values[0]/values[1]}[op]
    return calc(), '', addresses, 'INDEPENDENT_RULE_RESULT'


def compare(item, sources, context, source_path, report_path):
    metric = item['metric']
    candidates = [s for s in sources if s['metric'] == metric]
    choice = context.get('mappings', {}).get(f"{item['where']}:{metric}") or context.get('mappings', {}).get(metric)
    if choice:
        candidates = [s for s in candidates if f"{s['sheet']}!{s['cell']}" == choice]
    rule = context.get('rules', {}).get(metric)
    addresses = [f"{s['sheet']}!{s['cell']}" for s in candidates]
    status, explanation, sv, delta, compare_report = '', '', None, None, None
    provenance = ''
    selected = candidates[0] if len(candidates) == 1 else None
    if rule:
        sv, error, addresses, provenance = source_rule(rule, sources)
        status = error
        selected = next((s for s in sources if f"{s['sheet']}!{s['cell']}" == addresses[0]), None)
    elif len(candidates) > 1:
        status = 'AMBIGUOUS_MAPPING'
    elif not selected:
        status = 'PENDING_CONFIRMATION'
    elif selected['formula']:
        status = 'UNVERIFIED_FORMULA_CACHE'
        provenance = f"formula={selected['formula']}; cache={selected['cache']}; freshness=UNKNOWN"
    else:
        sv, status = decimal_value(selected['value'])
        provenance = 'DIRECT_CELL'
    if selected and not status:
        for key in FIELDS:
            a, b = item['identity'][key], selected['identity'][key]
            if a and b and a != b:
                status = 'NOT_COMPARABLE'
                explanation = f'{key}: report={a}, source={b}'
                break
        if not item['identity']['subject'] and len({s['identity']['subject'] for s in sources if s['metric'] == metric}) > 1:
            status = 'AMBIGUOUS_MAPPING'
            explanation = '报告主体未明确；多个候选主体'
    report_unit = item['unit']
    source_unit = '%' if rule and rule['op'] in ('divide', 'ratio') else (rule.get('unit', selected['unit'] if selected else '') if rule else (selected['unit'] if selected else ''))
    if not status and (report_unit not in SCALE or source_unit not in SCALE or (report_unit == '%') != (source_unit == '%')):
        status = 'PENDING_CONFIRMATION'
        explanation = '单位或量纲待确认'
    if not status:
        rv, status = decimal_value(item['value'])
        if not status:
            compare_report = rv * SCALE[report_unit]
            source_value = sv if rule else sv * (Decimal(1) if selected['percent_format'] else SCALE[source_unit])
            sv = source_value
            delta = compare_report - sv
            rounding = context.get('rounding', {}).get(metric)
            if rounding:
                if rounding.get('mode') != 'ROUND_HALF_UP' or not isinstance(rounding.get('places'), int) or not 0 <= rounding['places'] <= 8:
                    raise CheckError('INVALID_RULE', 'rounding needs ROUND_HALF_UP and places 0..8')
                normalized = (sv / SCALE[report_unit]).quantize(Decimal(1).scaleb(-rounding['places']), rounding=ROUND_HALF_UP)
                status = 'MATCH' if normalized == rv else 'MISMATCH'
                explanation = f"source raw={sv}; ROUND_HALF_UP to {rounding['places']} {report_unit}={normalized}; raw delta={delta}"
            elif delta == 0:
                status = 'MATCH'
            elif context.get('exact') is True:
                status = 'MISMATCH'
            else:
                status = 'RAW_DIFFERENCE_ROUNDING_PENDING'
                explanation = '舍入口径待确认；仅原始事实差异'
    if not explanation:
        explanation = {'AMBIGUOUS_MAPPING': '多个来源候选，需明确指定表和单元格',
                       'UNVERIFIED_FORMULA_CACHE': '公式缓存新鲜度未知，未重算',
                       'PENDING_CONFIRMATION': '来源或口径信息不足',
                       'ZERO_DENOMINATOR': '分母为零，未计算',
                       'MISSING_OPERAND': '操作数缺失，未计算',
                       'NON_NUMERIC_OPERAND': '操作数非数字，未计算',
                       'MATCH': '比较值一致', 'MISMATCH': '报告减来源不一致'}.get(status, status)
    return dict(metric_id=hashlib.sha256(f"{report_path.name}|{item['where']}|{metric}|{item['value']}".encode()).hexdigest()[:12],
                metric=metric, where=item['where'], quote=item['quote'], report_value=item['value'], report_unit=report_unit,
                identity=item['identity'], candidates=addresses, status=status, source_file=source_path.name,
                source_cell=','.join(addresses), source_raw=str(selected['value']) if selected and selected['value'] is not None else '',
                source_unit=source_unit, source_value=sv, normalized_report=compare_report, delta=delta,
                delta_unit='比例' if source_unit == '%' else '元', provenance=provenance,
                formula=str(selected['formula']) if selected else '', explanation=explanation,
                rule=json.dumps(rule, ensure_ascii=False, sort_keys=True) if rule else ('mapping='+str(choice) if choice else 'direct candidate'))


def rate_change(items, sources, source, report):
    """Only the explicit prior/current completion-rate wording permits change."""
    if len(items) != 2 or any(i['metric'] != '完成率' or i['where'] != items[0]['where'] for i in items):
        return None
    if not all(x in items[0]['quote'] for x in ('由', '提高至')):
        return None
    candidates = [s for s in sources if ('上期' in s['header'] or '本期' in s['header']) and s['value'] is not None]
    old = [s for s in candidates if '上期' in s['header']]
    new = [s for s in candidates if '本期' in s['header']]
    if len(old) != 1 or len(new) != 1:
        return None
    a, ea = decimal_value(old[0]['value'])
    b, eb = decimal_value(new[0]['value'])
    if ea or eb:
        return None
    r0, e0 = decimal_value(items[0]['value'])
    r1, e1 = decimal_value(items[1]['value'])
    if e0 or e1:
        return None
    if old[0]['unit'] == '%' or old[0]['metric'] == '完成率' and old[0]['unit'] == '' and 0 <= a <= 1:
        a *= Decimal(100)
    if new[0]['unit'] == '%' or new[0]['metric'] == '完成率' and new[0]['unit'] == '' and 0 <= b <= 1:
        b *= Decimal(100)
    pp = b - a
    relative = (pp / a * 100) if a else None
    status = 'MATCH' if r0 == a and r1 == b else 'RAW_DIFFERENCE_ROUNDING_PENDING'
    first = items[0]
    return dict(metric_id=hashlib.sha256(f'{report.name}|{first["where"]}|完成率变化'.encode()).hexdigest()[:12],
                metric='完成率变化', where=first['where'], quote=first['quote'], report_value=f'{r0}% → {r1}%',report_unit='pp',
                identity=first['identity'], candidates=[f'{s["sheet"]}!{s["cell"]}' for s in (old[0],new[0])], status=status,
                source_file=source.name, source_cell=f'{old[0]["sheet"]}!{old[0]["cell"]},{new[0]["sheet"]}!{new[0]["cell"]}',
                source_raw=f'{a}% → {b}%',source_unit='%',source_value=pp,normalized_report=r1-r0,delta=(r1-r0)-pp,
                delta_unit='pp',provenance='DIRECT_CELLS',formula='',
                explanation=f'本期−上期={pp}个百分点；相对增幅={relative}% (基数={a}%)' if relative is not None else '上期为零：相对增幅未计算',
                rule='explicit 上期/本期 completion rate')


def write_output(path, results, uncovered, source, report, context, previous):
    wb = Workbook()
    wb.remove(wb.active)
    for name in SHEETS:
        wb.create_sheet(name)
    changes = {}
    prior = {r['metric_id']: r for r in previous.get('results', [])} if previous else {}
    if previous and previous.get('report_sha256') != digest(report):
        prior = {}
    conflicts = Counter(r['metric'] for r in results if r['status'] not in ('PENDING_CONFIRMATION', 'AMBIGUOUS_MAPPING'))
    contradictory = {name for name, n in conflicts.items() if n > 1 and len({r['report_value'] for r in results if r['metric'] == name}) > 1}
    for r in results:
        if r['metric'] in contradictory:
            r['explanation'] += '；报告同指标多位置数值冲突，请复核'
    for r in results:
        old = prior.get(r['metric_id'])
        if not previous:
            changes[r['metric_id']] = 'FIRST_RUN'
        elif not old:
            changes[r['metric_id']] = 'NEW_OR_CHANGED_CONTEXT'
        elif old['status'] in ('MISMATCH', 'RAW_DIFFERENCE_ROUNDING_PENDING') and r['status'] == 'MATCH':
            changes[r['metric_id']] = 'RESOLVED'
        elif r['status'] in ('AMBIGUOUS_MAPPING', 'PENDING_CONFIRMATION', 'UNVERIFIED_FORMULA_CACHE'):
            changes[r['metric_id']] = 'STILL_PENDING' if old['status'] == r['status'] else 'CHANGED_CONTEXT'
        elif r['status'] in ('MISMATCH', 'RAW_DIFFERENCE_ROUNDING_PENDING'):
            changes[r['metric_id']] = 'STILL_OPEN' if old['status'] == r['status'] else 'NEW'
        else:
            changes[r['metric_id']] = 'UNCHANGED'
    summary = wb[SHEETS[0]]
    summary.append(['项目', '值'])
    for k, v in [('来源文件', source.name), ('来源SHA256', digest(source)), ('报告文件', report.name),
                 ('报告SHA256', digest(report)), ('覆盖', '正文段落、普通表格；只扫描可定位的指标陈述'),
                 ('限制', '非完整财务审计；未核实公式缓存；未知口径需确认'), ('未覆盖数量', len(uncovered))]:
        summary.append([k, v])
    for name, count in sorted(Counter(r['status'] for r in results).items()):
        summary.append([name, count])
    for name in sorted(contradictory):
        summary.append(['报告内部冲突', name])
    for name, count in sorted(Counter(changes.values()).items()):
        summary.append(['变化:'+name, count])
    mapping = wb[SHEETS[1]]
    mapping.append(['metric_id','指标','主体','期间','实际/预算','税口径','币种','报告文件','报告位置','报告原文','候选来源','映射/规则证据','状态','变化'])
    details = wb[SHEETS[2]]
    details.append(['metric_id','指标','主体','期间','单位','币种','实际/预算','税口径','来源文件','来源工作表/单元格','来源原值','来源单位','比较来源值','来源可信范围','报告位置','报告原文','报告值','比较报告值','换算/规则','状态','差额(报告-来源)','差额单位','解释'])
    pending = wb[SHEETS[3]]
    pending.append(['metric_id','指标','报告位置','待确认事项','候选来源','提问','状态','差额'])
    gaps = wb[SHEETS[4]]
    gaps.append(['文件','区域/位置','未覆盖类型','原因与建议'])
    for r in results:
        ident = r['identity']
        mapping.append([r['metric_id'],r['metric'],ident['subject'],ident['period'],ident['basis'],ident['tax'],ident['currency'],report.name,r['where'],r['quote'],', '.join(r['candidates']),r['rule'],r['status'],changes[r['metric_id']]])
        if r['status'] not in ('AMBIGUOUS_MAPPING','PENDING_CONFIRMATION','NOT_COMPARABLE','ZERO_DENOMINATOR','MISSING_OPERAND','NON_NUMERIC_OPERAND','UNVERIFIED_FORMULA_CACHE'):
            details.append([r['metric_id'],r['metric'],ident['subject'],ident['period'],r['report_unit'],ident['currency'],ident['basis'],ident['tax'],r['source_file'],r['source_cell'],r['source_raw'],r['source_unit'],str(r['source_value']),r['provenance'],r['where'],r['quote'],r['report_value'],str(r['normalized_report']),r['rule'],r['status'],str(r['delta']),r['delta_unit'],r['explanation']])
        else:
            pending.append([r['metric_id'],r['metric'],r['where'],r['explanation'],', '.join(r['candidates']),f"请确认{r['metric']}的来源、主体、期间和计算规则",r['status'],None])
    for file, area, reason in uncovered:
        gaps.append([file,area,area,reason])
    for sheet in wb:
        sheet.freeze_panes = 'A2'
        sheet.auto_filter.ref = sheet.dimensions
        for row in sheet:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.value = safe_text(cell.value)
    if path.exists() or path.is_symlink():
        raise CheckError('OUTPUT_REJECTED', 'refusing to overwrite existing output')
    wb.save(path)
    return changes


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('source-xlsx','report-docx','input-root','output-dir'):
        p.add_argument('--'+arg, required=True)
    p.add_argument('--context', help='explicit JSON mappings/rules/rounding and exact flag')
    p.add_argument('--prior-run', help='prior JSON snapshot under input-root')
    args = p.parse_args(argv)
    try:
        root = Path(args.input_root)
        if not root.is_dir() or root.is_symlink():
            raise CheckError('INPUT_MISSING','input-root missing')
        source = safe_file(args.source_xlsx, '.xlsx', root)
        report = safe_file(args.report_docx, '.docx', root)
        output = Path(args.output_dir)
        if not output.is_dir() or output.is_symlink() or output.resolve() == root.resolve() or output.resolve().is_relative_to(root.resolve()):
            raise CheckError('OUTPUT_REJECTED', 'output directory must be separate existing authorized directory')
        def read_json(path):
            file = Path(path)
            if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root.resolve()) or file.stat().st_size > 100000:
                raise CheckError('UNSUPPORTED_OR_SPOOFED', 'JSON must be small regular file under input-root')
            return json.loads(file.read_text(encoding='utf-8'))
        context = read_json(args.context) if args.context else {}
        previous = read_json(args.prior_run) if args.prior_run else None
        if not isinstance(context, dict) or previous is not None and not isinstance(previous, dict):
            raise CheckError('INVALID_RULE','JSON object required')
        sources = extract_source(source, context)
        items, uncovered = report_items(report, context)
        change = rate_change(items, sources, source, report)
        results = [change] if change else [compare(item, sources, context, source, report) for item in items]
        filename = re.sub(r'[^\w\u4e00-\u9fff-]+', '_', report.stem)[:80] + '-数字一致性检查.xlsx'
        path = output / filename
        snapshot = output / (path.stem + '.json')
        if snapshot.exists() or snapshot.is_symlink():
            raise CheckError('OUTPUT_REJECTED','refusing to overwrite existing snapshot')
        changes = write_output(path, results, uncovered, source, report, context, previous)
        snapshot.write_text(json.dumps(dict(report_sha256=digest(report),source_sha256=digest(source),results=[{k: str(v) if isinstance(v, Decimal) else v for k,v in r.items()} for r in results],changes=changes), ensure_ascii=False, indent=2),encoding='utf-8')
        print(json.dumps(dict(status='PARTIAL' if uncovered or any(r['status'] not in ('MATCH','MISMATCH') for r in results) else 'CHECKED',output=str(path),snapshot=str(snapshot), counts=dict(Counter(r['status'] for r in results)),changes=dict(Counter(changes.values())),uncovered=len(uncovered)),ensure_ascii=False))
        return 0
    except CheckError as exc:
        print(json.dumps(dict(error=exc.code,message=str(exc)),ensure_ascii=False),file=sys.stderr)
        return 2
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(json.dumps(dict(error='UNREADABLE_OR_ENCRYPTED',message=type(exc).__name__),ensure_ascii=False),file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
