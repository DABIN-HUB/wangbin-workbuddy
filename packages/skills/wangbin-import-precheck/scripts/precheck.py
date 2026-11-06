"""Local, read-only import precheck; output is not a target-system validation receipt."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.utils import get_column_letter
except ImportError:
    raise SystemExit('DEPENDENCY_MISSING: install openpyxl>=3.1,<4 (BSD-3-Clause)')

MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 50000
MAX_CELLS = 1000000
HEADINGS = {
    '检查概览': ['项目', '值'],
    '字段映射': ['原始字段', '目标字段', '映射依据', '确认状态', '转换规则'],
    '问题明细': ['finding_id', 'row_id', '文件', '工作表', '原始行号', '字段/单元格', '原值', '规则编号', '类别', '说明', '建议', '是否阻断候选导入'],
    '变更记录': ['row_id', '字段', '原值', '新值', '转换规则', '授权依据'],
    '未检查项': ['规则编号', '缺少条件', '影响范围', '需补资料'],
}

class InputError(ValueError):
    pass

def safe_path(value, *, output=False):
    p = Path(value)
    if '..' in p.parts or not p.is_absolute():
        raise InputError('PATH_SCOPE: absolute explicit path without traversal required')
    for part in (p, *p.parents):
        if part.is_symlink():
            raise InputError('PATH_SYMLINK: symlinks are not permitted')
    if output:
        if not p.is_dir():
            raise InputError('OUTPUT_DIR_REQUIRED')
    elif not p.is_file() or p.stat().st_size > MAX_BYTES:
        raise InputError('INPUT_MISSING_OR_TOO_LARGE')
    return p

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_table(path, sheet=None, header=1):
    path = safe_path(path)
    if header < 1:
        raise InputError('INVALID_HEADER_ROW')
    raw = path.read_bytes()
    if path.suffix.lower() == '.csv':
        if b'\x00' in raw or raw.startswith((b'PK\x03\x04', b'\xd0\xcf\x11\xe0')):
            raise InputError('FAKE_CSV')
        try:
            encoding = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
            text = raw.decode(encoding)
        except UnicodeDecodeError as exc:
            raise InputError('CSV_ENCODING_UNKNOWN: provide UTF-8 CSV') from exc
        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=',;\t|')
        except csv.Error as exc:
            if any(mark in text for mark in ',;\t|'):
                raise InputError('CSV_DELIMITER_UNKNOWN') from exc
            dialect = csv.excel  # A genuine single-column CSV has no delimiter to infer.
        # Preserve physical starting line; embedded line breaks belong to one record.
        reader = csv.reader(text.splitlines(keepends=True), dialect)
        rows = []
        physical_line = 0
        for values in reader:
            rows.append((physical_line + 1, values, [None] * len(values)))
            physical_line = reader.line_num
        if header > len(rows):
            raise InputError('HEADER_OUT_OF_RANGE')
        columns = rows[header - 1][1]
        body = rows[header:]
        metadata = {'encoding': encoding, 'delimiter': dialect.delimiter, 'sheet': '', 'header_row': header}
    elif path.suffix.lower() == '.xlsx':
        if not zipfile.is_zipfile(path):
            raise InputError('FAKE_OR_CORRUPT_XLSX')
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if (len(names) > 3000 or len(names) != len(set(names))
                    or any(n.startswith('/') or '..' in Path(n).parts or '\\' in n for n in names)
                    or sum(i.file_size for i in archive.infolist()) > 100 * MAX_BYTES
                    or any(n.lower().endswith(('vbaproject.bin', '.rels.bak')) for n in names)
                    or any(n.lower().startswith('xl/externallinks/') for n in names)
                    or any(archive.getinfo(n).file_size > MAX_BYTES or b'TargetMode="External"' in archive.read(n)
                           or b"TargetMode='External'" in archive.read(n)
                           for n in names if n.endswith('.rels'))
                    or 'xl/workbook.xml' not in names):
                raise InputError('UNSAFE_XLSX_CONTENT')
        try:
            wb = load_workbook(path, read_only=False, data_only=False, keep_links=False)
        except Exception as exc:
            raise InputError('UNREADABLE_XLSX') from exc
        if sheet is None and len(wb.sheetnames) != 1:
            raise InputError('SHEET_SELECTION_REQUIRED: ' + ', '.join(wb.sheetnames))
        if sheet is not None and sheet not in wb.sheetnames:
            raise InputError('SHEET_NOT_FOUND: ' + ', '.join(wb.sheetnames))
        ws = wb[sheet or wb.sheetnames[0]]
        if ws.max_row > MAX_ROWS + header or ws.max_row * ws.max_column > MAX_CELLS:
            raise InputError('RESOURCE_LIMIT')
        if any(ws.cell(header, col).coordinate in ws.merged_cells for col in range(1, ws.max_column + 1)):
            raise InputError('MERGED_HEADER')
        columns = [ws.cell(header, c).value for c in range(1, ws.max_column + 1)]
        body = [(r, [ws.cell(r, c).value for c in range(1, ws.max_column + 1)],
                 [ws.cell(r, c) for c in range(1, ws.max_column + 1)]) for r in range(header + 1, ws.max_row + 1)]
        metadata = {'sheet': ws.title, 'header_row': header}
    else:
        raise InputError('UNSUPPORTED_FORMAT: CSV/XLSX only')
    if not columns or any(not isinstance(c, str) or not c.strip() for c in columns) or len(columns) != len(set(columns)):
        raise InputError('AMBIGUOUS_HEADER: blank or duplicate headers')
    if len(body) > MAX_ROWS:
        raise InputError('RESOURCE_LIMIT')
    records = []
    blank = 0
    for line, values, cells in body:
        if all(v is None or v == '' for v in values):
            blank += 1
            continue
        record = {}
        for i, col in enumerate(columns):
            value = values[i] if i < len(values) else None
            cell = cells[i] if i < len(cells) else None
            if cell is not None and cell.data_type == 'f':
                raise InputError('FORMULA_INPUT: ' + cell.coordinate)
            record[col] = {'value': value, 'type': cell.data_type if cell else 'csv-text',
                           'coordinate': cell.coordinate if cell else f'{col}:line{line}',
                           'format': cell.number_format if cell else None}
        records.append({'line': line, 'cells': record})
    metadata.update({'columns': columns, 'blank_rows': blank, 'sha256': hashlib.sha256(raw).hexdigest(), 'file': path.name})
    return metadata, records

def safe_text(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)

def export_cell(cell, value):
    text = safe_text(value)
    if text is None:
        return
    if len(text) > 32767:
        text = text[:32760] + '…'
    cell.value = text
    cell.data_type = 's'  # Never allow a loaded =... string to become an Excel formula.
    cell.number_format = '@'

def write_book(path, tables):
    wb = Workbook()
    wb.remove(wb.active)
    for name, (headers, rows) in tables.items():
        ws = wb.create_sheet(name)
        ws.append(headers)
        for record in rows:
            ws.append([None] * len(headers))
            for i, value in enumerate(record, 1):
                export_cell(ws.cell(ws.max_row, i), value)
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = f'A1:{get_column_letter(len(headers))}{max(ws.max_row, 1)}'
        for idx, label in enumerate(headers, 1):
            ws.column_dimensions[get_column_letter(idx)].width = min(55, max(16, len(label) * 2 + 4))
    wb.save(path)

def next_path(directory, stem):
    base = re.sub(r'[^\w\-\u4e00-\u9fff]', '_', stem)[:70] or 'import'
    for i in range(10000):
        p = directory / (base + (f'-run{i}' if i else '') + '.xlsx')
        if not p.exists() and not p.is_symlink():
            return p
    raise InputError('OUTPUT_NAME_EXHAUSTED')

def rules_from_json(path):
    if path is None:
        return {}
    data = json.loads(safe_path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('fields'), dict):
        raise InputError('INVALID_RULES: fields object required')
    return data

def rules_from_template(path, sheet=None):
    meta, _ = read_table(path, sheet)
    return {'fields': {col: {'sources': [col], 'rule_id': 'TEMPLATE:' + col,
                             'rule_source': f"template {meta['file']} sha256:{meta['sha256']}"}
                       for col in meta['columns']}}

def compare_report(previous_report, source_hash, current, current_reference_hash):
    """Compare explicit immutable prior report by stable source-row evidence, not finding IDs."""
    previous = safe_path(previous_report)
    try:
        wb = load_workbook(previous, read_only=True, data_only=True)
        if not set(HEADINGS).issubset(wb.sheetnames):
            raise InputError('PREVIOUS_REPORT_INVALID: missing report sheets')
        overview = {str(k): v for k, v in wb['检查概览'].values if k is not None}
        if overview.get('源SHA256') != source_hash:
            raise InputError('PREVIOUS_SOURCE_MISMATCH: use a report from the same source bytes')
        rows = list(wb['问题明细'].values)
        if list(rows[0]) != HEADINGS['问题明细']:
            raise InputError('PREVIOUS_REPORT_INVALID: unexpected finding columns')
        prior = [dict(zip(('finding_id','row_id','file','sheet','line','field','value','rule','category','description','advice','blocking'), row)) for row in rows[1:]]
        for item in prior:
            if item['line'] is not None and str(item['line']).isdigit():
                item['line'] = int(str(item['line']))
    except InputError:
        raise
    except (ValueError, KeyError, IndexError, OSError, zipfile.BadZipFile) as exc:
        raise InputError('PREVIOUS_REPORT_INVALID: unreadable report') from exc
    finally:
        if 'wb' in locals():
            wb.close()
    def key(item):
        return tuple(str(item[k] if item[k] is not None else '') for k in ('row_id','file','sheet','line','field','value','rule','category'))
    old_keys = {key(item) for item in prior}
    new_keys = {key(item) for item in current}
    return {'previous_report': str(previous), 'previous_report_sha256': digest(previous),
            'previous_reference_sha256': overview.get('参考SHA256'), 'current_reference_sha256': current_reference_hash,
            'resolved': [f for f in prior if key(f) not in new_keys],
            'continuing': [f for f in current if key(f) in old_keys],
            'new': [f for f in current if key(f) not in old_keys]}

def analyze(source, output, rules=None, reference=None, *, sheet=None, reference_sheet=None,
            header=1, split=False, candidate=False, transformations=None, authorization=None, previous_report=None):
    source = safe_path(source)
    output = safe_path(output, output=True)
    if source.parent == output or output in source.parents:
        raise InputError('OUTPUT_INPUT_COLLISION')
    before = digest(source)
    meta, records = read_table(source, sheet, header)
    rules = rules or {}
    fields = rules.get('fields', {})
    if not isinstance(fields, dict):
        raise InputError('INVALID_RULES')
    if (candidate or split or transformations) and not authorization:
        raise InputError('AUTHORIZATION_REQUIRED: specify the authorized action and scope')
    if transformations and not candidate and not split:
        raise InputError('TRANSFORMATION_REQUIRES_CANDIDATE')
    ref_meta = None
    if reference:
        try:
            ref_meta, ref_rows = read_table(reference, reference_sheet)
        except InputError as exc:
            if str(exc).startswith('SHEET_SELECTION_REQUIRED:'):
                raise InputError('REFERENCE_SHEET_SELECTION_REQUIRED: ' + str(exc).split(': ', 1)[1]) from exc
            raise
    mappings = []
    selected = {}
    unresolved = set()
    unchecked = []
    for target, rule in fields.items():
        if not isinstance(rule, dict):
            raise InputError('INVALID_FIELD_RULE')
        proposed = rule.get('sources', [target] if target in meta['columns'] else [])
        if isinstance(proposed, str):
            proposed = [proposed]
        proposed = list(dict.fromkeys(proposed))
        present = [col for col in proposed if col in meta['columns']]
        for col in present:
            mappings.append([col, target, rule.get('rule_source', 'user/template'),
                             'CONFIRMED' if len(present) == 1 else 'PENDING_CONFLICT',
                             ','.join((transformations or {}).get(target, [])) if isinstance((transformations or {}).get(target, []), list) else ''])
        if len(present) == 1:
            selected[target] = present[0]
        else:
            unresolved.add(target)
            unchecked.append([rule.get('rule_id', target), 'mapping missing or conflicting: ' + ','.join(present or proposed), target, 'confirm one source column'])
        if 'required' not in rule or rule['required'] == 'UNKNOWN':
            unchecked.append([rule.get('rule_id', target), 'required unknown', target, 'confirm required'])
        if rule.get('data_type') == 'date' and not rule.get('date_format'):
            unchecked.append([rule.get('rule_id', target), 'date format ambiguous (day/month vs month/day)', target, 'confirm date_format'])
    if not rules.get('fields'):
        unchecked.append(['TARGET_RULES_UNKNOWN', 'no template/field description', 'target-system compliance', 'provide target rules'])
    for col in meta['columns']:
        if not any(row[0] == col for row in mappings):
            mappings.append([col, '', 'source header only', 'UNMAPPED', ''])
    for col, targets in defaultdict(list, ((c, [t for s,t,*_ in mappings if s == c and t]) for c in meta['columns'])).items():
        if len(targets) > 1:
            for t in targets:
                selected.pop(t, None)
                unchecked.append([fields[t].get('rule_id', t), 'source mapped to multiple targets', col, 'confirm mapping'])
    findings = []
    def finding(row, field, rule, kind, description, value=None, blocking=True, origin=None, origin_row=None):
        cell = row['cells'].get(field, {}) if row else {}
        if origin_row is not None:
            cell = origin_row['cells'][field]
        findings.append({'finding_id': f'F{len(findings)+1:05d}', 'row_id': row['id'] if row else '', 'file': meta['file'],
                         'sheet': meta['sheet'], 'line': row['line'] if row else '', 'field': cell.get('coordinate', field),
                         'value': safe_text(value if value is not None else cell.get('value')), 'rule': rule,
                         'category': kind, 'description': description, 'advice': 'confirm against source/rule', 'blocking': blocking})
        if origin is not None:
            findings[-1].update(file=origin['file'], sheet=origin['sheet'], line=origin_row['line'],
                                field=cell['coordinate'])
    for row in records:
        row['id'] = f"{before[:16]}:{meta['sheet'] or 'CSV'}:{row['line']}"
    checked = set()
    for target, rule in fields.items():
        if target not in selected:
            continue
        col = selected[target]
        rule_id = rule.get('rule_id', target)
        for row in records:
            cell = row['cells'][col]
            value = cell['value']
            missing = value is None or value == ''
            if rule.get('required') is True:
                checked.add(rule_id + ':required')
                if missing:
                    finding(row, col, rule_id, 'MISSING_REQUIRED_FIELD', 'required value missing')
            if missing:
                continue
            dtype = rule.get('data_type')
            if dtype == 'text':
                checked.add(rule_id + ':type')
                if cell['type'] not in ('s', 'inlineStr', 'csv-text'):
                    finding(row, col, rule_id, 'TEXT_ENCODING_RISK', 'numeric/display format is not original text', value)
            if dtype == 'date':
                fmt = rule.get('date_format')
                if fmt:
                    checked.add(rule_id + ':date')
                    try:
                        if isinstance(value, datetime):
                            datetime.strptime(value.strftime(fmt), fmt)
                        else:
                            datetime.strptime(safe_text(value), fmt)
                    except (ValueError, TypeError):
                        finding(row, col, rule_id, 'INVALID_DATE', 'does not match confirmed date format', value)
            if rule.get('max_length') is not None or rule.get('min_length') is not None:
                checked.add(rule_id + ':length')
                if not int(rule.get('min_length', 0)) <= len(safe_text(value)) <= int(rule.get('max_length', 32767)):
                    finding(row, col, rule_id, 'LENGTH_VIOLATION', 'outside confirmed length bounds', value)
            if rule.get('allowed_values') is not None:
                checked.add(rule_id + ':values')
                if value not in rule['allowed_values']:
                    finding(row, col, rule_id, 'INVALID_VALUE', 'not in allowed values', value)
            if cell['type'] == 'n' and isinstance(value, (int, float)) and len(str(value).replace('.', '').replace('-', '')) >= 15:
                finding(row, col, rule_id, 'PRECISION_RISK', 'numeric identifier may already have lost digits; cannot reconstruct', value)
    groups = defaultdict(list)
    for target, rule in fields.items():
        group = rule.get('unique_group')
        if group:
            groups[str(group)].append(target)
    duplicate_groups = 0
    for group, targets in sorted(groups.items()):
        if any(t not in selected for t in targets):
            unchecked.append([group, 'unique key mapping unresolved', ','.join(targets), 'confirm mapping'])
            continue
        checked.add(group + ':unique')
        values = defaultdict(list)
        for row in records:
            key = tuple(row['cells'][selected[t]]['value'] for t in targets)
            if any(v is None or v == '' for v in key):
                unchecked.append([group, 'missing comparison key', row['id'], 'complete key before checking uniqueness'])
                continue
            values[key].append(row)
        for key, members in values.items():
            if len(members) > 1:
                duplicate_groups += 1
                for row in members:
                    finding(row, selected[targets[0]], group, 'DUPLICATE_KEY',
                            'same key at lines ' + ','.join(str(m['line']) for m in members))
    for target, rule in fields.items():
        ref_key = rule.get('reference_key')
        if not ref_key or target not in selected:
            continue
        rule_id = rule.get('rule_id', target)
        if not ref_meta:
            unchecked.append([rule_id, 'reference snapshot missing', target, 'provide reference CSV/XLSX'])
            continue
        if ref_key not in ref_meta['columns']:
            unchecked.append([rule_id, 'reference key missing', target, 'confirm reference key'])
            continue
        checked.add(rule_id + ':reference')
        lookup = defaultdict(list)
        for r in ref_rows:
            lookup[r['cells'][ref_key]['value']].append(r)
        for key, members in lookup.items():
            if len(members) > 1:
                finding(None, ref_key, rule_id, 'REFERENCE_AMBIGUITY',
                        'duplicate reference key at lines ' + ','.join(str(r['line']) for r in members),
                        key, False, origin=ref_meta, origin_row=members[0])
        for row in records:
            val = row['cells'][selected[target]]['value']
            if val is None or val == '':
                continue
            if val in lookup and len(lookup[val]) > 1:
                unchecked.append([rule_id, 'ambiguous reference key: ' + safe_text(val), row['id'], 'deduplicate reference snapshot'])
            elif val not in lookup:
                finding(row, selected[target], rule_id, 'NOT_IN_REFERENCE', 'not found in this reference snapshot', val)
    changes = []
    transformed = {r['id']: {col: c['value'] for col,c in r['cells'].items()} for r in records}
    for target, actions in (transformations or {}).items():
        if target not in selected or actions not in ('strip', 'upper', 'lower'):
            raise InputError('TRANSFORMATION_NOT_CONFIRMED: strip/upper/lower on uniquely mapped fields only')
        for row in records:
            old = transformed[row['id']][selected[target]]
            if isinstance(old, str):
                new = getattr(old, actions)()
                if new != old:
                    transformed[row['id']][selected[target]] = new
                    changes.append([row['id'], target, old, new, actions, authorization])
    # A transformed unique key must be checked as it will actually be exported. Avoid
    # counting an already-reported source duplicate group twice.
    for group, targets in sorted(groups.items()):
        if not transformations or not any(t in transformations for t in targets) or any(t not in selected for t in targets):
            continue
        original = defaultdict(list)
        exported = defaultdict(list)
        for row in records:
            old_key = tuple(row['cells'][selected[t]]['value'] for t in targets)
            new_key = tuple(transformed[row['id']][selected[t]] for t in targets)
            if not any(v is None or v == '' for v in old_key):
                original[old_key].append(row)
            if not any(v is None or v == '' for v in new_key):
                exported[new_key].append(row)
        existing = {(group, f['row_id']) for f in findings if f['category'] == 'DUPLICATE_KEY'}
        for key, members in exported.items():
            if len(members) > 1:
                if not any(len(original[tuple(r['cells'][selected[t]]['value'] for t in targets)]) > 1 for r in members):
                    duplicate_groups += 1
                for row in members:
                    if (group, row['id']) not in existing:
                        finding(row, selected[targets[0]], group, 'DUPLICATE_KEY',
                                'authorized transformation creates same key at lines ' + ','.join(str(r['line']) for r in members), key[0])
    if digest(source) != before:
        raise InputError('SOURCE_CHANGED_DURING_RUN')
    if reference and digest(safe_path(reference)) != ref_meta['sha256']:
        raise InputError('REFERENCE_CHANGED_DURING_RUN')
    if candidate or split:
        if unresolved or not fields or any(t not in selected for t in fields):
            raise InputError('CANDIDATE_MAPPING_UNRESOLVED')
    if candidate and not split and any(f['category']=='DUPLICATE_KEY' and 'authorized transformation' in f['description'] for f in findings):
        raise InputError('TRANSFORMED_UNIQUE_COLLISION: use --split to quarantine conflicting rows')
    affected = {f['row_id'] for f in findings if f['row_id'] and f['blocking']}
    comparison = compare_report(previous_report, before, findings, ref_meta['sha256'] if ref_meta else 'NOT_PROVIDED') if previous_report else None
    report = next_path(output, source.stem + '-导入预检')
    status = 'PARTIAL' if unchecked else 'COMPLETED'
    overview = [['输入记录数', len(records)], ['完全空白行数', meta['blank_rows']], ['无阻断记录数', len(records)-len(affected)],
                ['有问题记录数', len(affected)], ['问题条数', len(findings)], ['重复组数', duplicate_groups],
                ['检查模式', '有限数据质量模式' if not fields else '已知规则预检'], ['已检查规则', ','.join(sorted(checked))],
                ['未检查规则', len(unchecked)], ['执行状态', status], ['源SHA256', before], ['参考SHA256', ref_meta['sha256'] if ref_meta else 'NOT_PROVIDED'],
                ['源编码/分隔符', json.dumps({k: meta[k] for k in ('encoding','delimiter') if k in meta}, ensure_ascii=False)]]
    if comparison:
        overview.extend([['对照旧报告', comparison['previous_report']], ['旧报告SHA256', comparison['previous_report_sha256']],
                         ['旧参考SHA256', comparison['previous_reference_sha256']], ['已解决问题数', len(comparison['resolved'])],
                         ['持续问题数', len(comparison['continuing'])], ['新增问题数', len(comparison['new'])]])
        for label, items in (('已解决', comparison['resolved']), ('持续', comparison['continuing']), ('新增', comparison['new'])):
            for item in items:
                overview.append([label + '问题', json.dumps({k: item[k] for k in ('row_id','line','field','category','value')}, ensure_ascii=False)])
    tables = {name: (headers, []) for name, headers in HEADINGS.items()}
    tables['检查概览'] = (HEADINGS['检查概览'], overview)
    tables['字段映射'] = (HEADINGS['字段映射'], mappings)
    tables['问题明细'] = (HEADINGS['问题明细'], [[f[k] for k in ('finding_id','row_id','file','sheet','line','field','value','rule','category','description','advice','blocking')] for f in findings])
    tables['变更记录'] = (HEADINGS['变更记录'], changes)
    tables['未检查项'] = (HEADINGS['未检查项'], list(dict.fromkeys(tuple(row) for row in unchecked)))
    write_book(report, tables)
    outputs = {'report': str(report)}
    if candidate or split:
        accepted = [r for r in records if r['id'] not in affected] if split else records
        isolated = [r for r in records if r['id'] in affected] if split else []
        cols = ['row_id', 'source_line', *meta['columns']]
        def rows_for(items):
            return [[r['id'], r['line'], *(transformed[r['id']][col] for col in meta['columns'])] for r in items]
        p = next_path(output, source.stem + '-候选导入')
        write_book(p, {'候选数据': (cols, rows_for(accepted))})
        outputs['candidate'] = str(p)
        if split:
            p = next_path(output, source.stem + '-隔离记录')
            write_book(p, {'隔离记录': (cols + ['原因'], [row + [','.join(f['category'] for f in findings if f['row_id'] == row[0])] for row in rows_for(isolated)])})
            outputs['quarantine'] = str(p)
            assert {r['id'] for r in accepted}.isdisjoint({r['id'] for r in isolated})
            assert len(accepted) + len(isolated) == len(records)
    return {'status': status, 'comparison': comparison, 'input_records': len(records), 'findings': len(findings), 'affected_records': len(affected),
            'duplicate_groups': duplicate_groups, 'source_sha256': before, 'reference_sha256': ref_meta['sha256'] if ref_meta else None,
            'unchecked': tables['未检查项'][1], 'checked': sorted(checked), 'outputs': outputs,
            'finding_details': findings, 'rows': [{'row_id':r['id'], 'line':r['line']} for r in records],
            'warning': 'Local snapshot precheck; unknown rules may still block import. Original untouched.'}

def main():
    parser = argparse.ArgumentParser(description='Local CSV/XLSX import precheck; no upload or original modification')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--rules', help='confirmed rule JSON, optional; see references/rules.md')
    parser.add_argument('--template', help='target CSV/XLSX template; exact header mapping, unspecified rules remain UNKNOWN')
    parser.add_argument('--template-sheet')
    parser.add_argument('--reference')
    parser.add_argument('--sheet')
    parser.add_argument('--reference-sheet')
    parser.add_argument('--previous-report', help='explicit earlier five-sheet report from same source for resolved/continuing/new comparison')
    parser.add_argument('--header', type=int, default=1)
    parser.add_argument('--candidate', action='store_true')
    parser.add_argument('--split', action='store_true', help='explicit request for passing subset and quarantine')
    parser.add_argument('--authorization', help='user instruction authorizing candidate/split/transformation scope')
    parser.add_argument('--transforms', help='JSON object target field -> strip/upper/lower; explicit authorization required')
    args = parser.parse_args()
    try:
        transforms = json.loads(args.transforms) if args.transforms else None
        if args.rules and args.template:
            raise InputError('RULES_TEMPLATE_CHOICE_REQUIRED: choose confirmed rules or template')
        rules = rules_from_json(args.rules) if args.rules else rules_from_template(args.template, args.template_sheet) if args.template else {}
        result = analyze(args.input, args.output_dir, rules, args.reference,
                         sheet=args.sheet, reference_sheet=args.reference_sheet, header=args.header,
                         candidate=args.candidate, split=args.split, transformations=transforms, authorization=args.authorization,
                         previous_report=args.previous_report)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    except (InputError, OSError, ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, InputError) and str(exc).startswith(('SHEET_SELECTION_REQUIRED:', 'REFERENCE_SHEET_SELECTION_REQUIRED:')):
            flag = '--reference-sheet' if str(exc).startswith('REFERENCE_') else '--sheet'
            print(json.dumps({'status':'NEEDS_INPUT', 'reason': str(exc),
                              'next_action':f'Select one worksheet explicitly with {flag}; no report was produced.'}, ensure_ascii=False))
            return 0
        print(json.dumps({'status': 'REJECTED' if isinstance(exc, InputError) else 'FAILED', 'reason': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
