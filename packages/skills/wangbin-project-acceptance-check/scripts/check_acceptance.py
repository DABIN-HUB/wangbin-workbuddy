"""Authorized, conservative evidence-to-requirement trace; not a formal acceptance decision.

Requires python-docx and openpyxl. No network, macros, OCR or document commands.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentType
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import MergedCell

MAX_BYTES = 4_000_000
MAX_ROWS = 2000
MAX_FILES = 40
MAX_ZIP_ENTRIES = 500
MAX_UNCOMPRESSED = 12_000_000
SHEETS = ['核查概览', '要求追踪', '证据索引', '缺口与不符合', '冲突与待确认', '本次更新']
SECTIONS = ['项目及核查范围', '本次资料与有效版本', '主要发现', '要求与证据概况', '资料缺口和明确不符合', '冲突及未确认变更', '验收准备建议', '来源和限制']
ALIASES = {'text': ('要求原文', '证据原文', '内容', '原文', '需求', 'text'), 'number': ('原始编号', '要求编号', '编号', 'number', 'requirement_id'),
           'reference': ('关联要求', '要求引用', '引用', 'reference'), 'version': ('版本', 'version'),
           'basis': ('生效依据', '确认依据', 'basis'), 'name': ('名称', '交付物名称', 'name'),
           'condition': ('子条件', '验收条件', 'condition'), 'result': ('结果', '测试结果', 'result')}


def stable(prefix, *parts):
    return prefix + '-' + hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:12]


def source_path(root, rel):
    path = Path(rel)
    if path.is_absolute() or not path.parts or any(p in ('..', '.') for p in path.parts):
        raise ValueError('INVALID_INPUT: source must be a relative path within authorized root')
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('INVALID_INPUT: symlink input')
    if not current.resolve().is_relative_to(root.resolve()) or not current.is_file():
        raise ValueError('INVALID_INPUT: source absent or outside authorized root')
    return current


def safe_output(root, dest):
    if not dest.is_absolute() or not dest.resolve().is_relative_to(root.resolve()):
        raise ValueError('INVALID_INPUT: output must be under authorized root')
    current = root
    for part in dest.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('INVALID_INPUT: symlink output')
    if not dest.is_dir():
        raise ValueError('INVALID_INPUT: output directory must already exist')
    return dest


def first(row, key):
    return next((str(row[x]).strip() for x in ALIASES[key] if row.get(x) is not None and str(row[x]).strip()), '')


def read_source(root, rel):
    path = source_path(root, rel)
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise ValueError('RESOURCE_LIMIT: file exceeds 4000000 bytes')
    if size == 0:
        raise ValueError('UNREADABLE_SOURCE: empty file')
    raw = path.read_bytes()
    suffix = path.suffix.lower()
    rows = []
    if suffix in ('.txt', '.md'):
        if b'\x00' in raw:
            raise ValueError('UNREADABLE_SOURCE: binary text')
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeError as exc:
            raise ValueError('UNREADABLE_SOURCE: text is not UTF-8') from exc
        for number, line in enumerate(text.splitlines(), 1):
            line = line.strip().lstrip('#*- ').strip()
            if line:
                match = re.match(r'^([A-Za-z]+\d+)\s*[：:]\s*(.*)$', line)
                rows.append({'text': match.group(2) if match else line, 'number': match.group(1) if match else '', 'location': f'行{number}'})
    elif suffix in ('.csv', '.xlsx'):
        if suffix == '.xlsx':
            if not zipfile.is_zipfile(io.BytesIO(raw)):
                raise ValueError('UNREADABLE_SOURCE: corrupt xlsx archive' if raw.startswith(b'PK\x03\x04') else 'UNSUPPORTED_FORMAT: fake xlsx')
            check_zip(raw)
            try:
                book = load_workbook(io.BytesIO(raw), read_only=True, data_only=False)
                if len(book.sheetnames) != 1:
                    raise ValueError('UNSUPPORTED_FORMAT: specify a single-sheet list')
                sheet = book.active
                cells = list(sheet.iter_rows(max_row=MAX_ROWS + 2))
                if sheet.max_row > MAX_ROWS + 1:
                    raise ValueError('RESOURCE_LIMIT: spreadsheet rows')
                if not cells:
                    raise ValueError('UNREADABLE_SOURCE: empty worksheet')
                header = [str(c.value or '').strip() for c in cells[0]]
                if len(set(header)) != len(header):
                    raise ValueError('UNSUPPORTED_FORMAT: duplicate header')
                for row in cells[1:]:
                    values = {header[i]: c.value for i, c in enumerate(row) if i < len(header) and not isinstance(c, MergedCell)}
                    if any(c.data_type == 'f' for c in row):
                        raise ValueError('UNSUPPORTED_FORMAT: formula cell cannot be evidence')
                    if any(v is not None and str(v).strip() for v in values.values()):
                        values['location'] = f'{sheet.title}/行{row[0].row}/列1-{len(header)}'
                        rows.append(values)
                book.close()
            except (zipfile.BadZipFile, KeyError, OSError) as exc:
                raise ValueError('UNREADABLE_SOURCE: invalid xlsx') from exc
        else:
            if b'\x00' in raw:
                raise ValueError('UNSUPPORTED_FORMAT: fake csv')
            try:
                data = raw.decode('utf-8-sig')
                reader = csv.DictReader(io.StringIO(data))
                if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
                    raise ValueError('UNSUPPORTED_FORMAT: missing/duplicate header')
                for n, row in enumerate(reader, 2):
                    if n > MAX_ROWS + 1:
                        raise ValueError('RESOURCE_LIMIT: csv rows')
                    if any(v and str(v).lstrip().startswith(('=', '+', '@')) for v in row.values() if isinstance(v, str)):
                        raise ValueError('UNSUPPORTED_FORMAT: formula-like CSV data is not evidence')
                    row['location'] = f'行{n}/列1-{len(reader.fieldnames)}'
                    rows.append(row)
            except UnicodeError as exc:
                raise ValueError('UNREADABLE_SOURCE: CSV is not UTF-8') from exc
    elif suffix == '.docx':
        if not zipfile.is_zipfile(io.BytesIO(raw)):
            raise ValueError('UNREADABLE_SOURCE: corrupt docx archive' if raw.startswith(b'PK\x03\x04') else 'UNSUPPORTED_FORMAT: fake docx')
        check_zip(raw)
        try:
            doc = Document(io.BytesIO(raw))
            table_no = paragraph_no = 0
            for child in doc.element.body.iterchildren():
                if child.tag == qn('w:p'):
                    paragraph_no += 1
                    text = Paragraph(child, doc).text.strip()
                    if text:
                        match = re.match(r'^([A-Za-z]+\d+)\s*[：:]\s*(.*)$', text)
                        rows.append({'text': match.group(2) if match else text, 'number': match.group(1) if match else '', 'location': f'段{paragraph_no}'})
                elif child.tag == qn('w:tbl'):
                    table_no += 1
                    table = Table(child, doc)
                    seen = set()
                    for r, row in enumerate(table.rows, 1):
                        if r == 1 and row.cells[0].text.strip() in ('编号', '原始编号'):
                            continue
                        if len(row.cells) >= 2 and re.fullmatch(r'[A-Za-z]+\d+', row.cells[0].text.strip()):
                            rows.append({'text': row.cells[1].text.strip(), 'number': row.cells[0].text.strip(), 'location': f'表{table_no}/行{r}/列2'})
                            continue
                        for c, cell in enumerate(row.cells, 1):
                            if cell._tc in seen:
                                continue
                            seen.add(cell._tc)
                            text = cell.text.strip()
                            if text:
                                rows.append({'text': text, 'location': f'表{table_no}/行{r}/列{c}'})
        except (KeyError, ValueError, zipfile.BadZipFile) as exc:
            raise ValueError('UNREADABLE_SOURCE: invalid docx') from exc
    else:
        raise ValueError('UNSUPPORTED_FORMAT: only txt/md/docx/csv/xlsx')
    if not rows:
        raise ValueError('UNREADABLE_SOURCE: no readable content')
    source = {'source_id': stable('SRC', rel), 'path': rel, 'sha256': hashlib.sha256(raw).hexdigest(), 'type': suffix,
              'unsupported_content': suffix == '.docx' and (b'<w:drawing' in raw or any('media/' in n for n in zipfile.ZipFile(io.BytesIO(raw)).namelist()))}
    for i, row in enumerate(rows):
        row['source_id'] = source['source_id']
        row['source'] = f"{rel}/{row['location']}"
        row['record_id'] = stable('REC', source['source_id'], row['location'], i)
    return source, rows


def check_zip(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ZIP_ENTRIES or sum(x.file_size for x in entries) > MAX_UNCOMPRESSED:
            raise ValueError('RESOURCE_LIMIT: OOXML archive exceeds limits')
        if any('vbaProject.bin' in x.filename or x.filename.endswith('.rels') and x.file_size > MAX_BYTES for x in entries):
            raise ValueError('UNSUPPORTED_FORMAT: macro or oversized relations')


def conditions(text, explicit=''):
    if explicit:
        return [s.strip() for s in re.split(r'[；;]', explicit) if s.strip()]
    if '端点' in text and '请求参数' in text and '返回字段' in text:
        return ['端点', '请求参数', '返回字段']
    if '接口文档和部署说明' in text:
        return ['接口文档', '部署说明']
    # Split only recognized, independently checkable delivery obligations.
    # Keep the required deployment environment attached to its own condition.
    deploy = r'(?:Windows Server 2019\s*)?部署(?:说明|步骤|文档)'
    composite = re.search(rf'({deploy})\s*[和与及]\s*(培训记录)|'
                          rf'(培训记录)\s*[和与及]\s*({deploy})', text)
    if composite:
        return [part for part in composite.groups() if part]
    return [text]


def evaluate_condition(cond, req, records):
    """Only literal explicit references or highly constrained document-content matches are bindings."""
    matches = []
    for ev in records:
        text = ev['text']
        reference = ev.get('reference', '')
        explicit = bool(req['number'] and (reference == req['number'] or re.search(r'(?<!\w)' + re.escape(req['number']) + r'(?!\w)', text)))
        keywords = ('培训记录', '接口文档', '部署说明', '端点', '请求参数', '返回字段')
        deploy_related = '部署' in cond and bool(re.search(r'部署说明|部署步骤|部署文档', text))
        relevant = explicit or (ev['role'] == 'delivery' and
                                (deploy_related or any(k in cond and k in text for k in keywords)))
        if not relevant or ('部署说明' in cond and not re.search(r'部署说明|部署步骤|部署文档', text)) or ('接口文档' in cond and not re.search(r'接口文档|接口说明', text)):
            continue
        if ev['role'] == 'change' or ev.get('listed_only') or ev.get('claim_only'):
            continue
        if '培训记录' in cond and '培训记录' not in text:
            continue
        if 'Windows Server 2019' in cond and 'Windows Server 2019' not in text:
            continue
        if any(k in cond for k in ('端点', '请求参数', '返回字段')):
            if '端点' in cond and not re.search(r'/[\w/-]+', text):
                continue
            if '请求参数' in cond and not re.search(r'请求参数\s*[：:]\s*\S+', text):
                continue
            if '返回字段' in cond and not re.search(r'返回字段\s*[：:]\s*\S+', text):
                continue
        negative = bool(re.search(r'未提供|没有|失败|不通过|仅\s*Ubuntu|only Ubuntu', text, re.I) or ev.get('result') in ('失败', '不通过', 'FAIL'))
        matches.append((ev, 'NONCONFORMING' if negative else 'SUPPORT'))
    return matches


def analyze(project, root, groups, previous=None, effective_version_ref=''):
    old = previous or {}
    sources = {s['source_id']: s for s in old.get('sources', [])}
    records = {r['record_id']: r for r in old.get('records', [])}
    diagnostics = []
    if sum(len(v) for v in groups.values()) > MAX_FILES:
        raise ValueError('RESOURCE_LIMIT: more than 40 sources')
    for role, paths in groups.items():
        for rel in paths:
            try:
                src, rows = read_source(root, rel)
                previous_src = next((s for s in sources.values() if s['path'] == rel and s['sha256'] != src['sha256']), None)
                if previous_src:
                    diagnostics.append({'source': rel, 'code': 'IDENTITY_REVIEW', 'reason': 'changed source; old and new records retained'})
                    src['source_id'] = stable('SRC', rel, src['sha256'])
                    for row in rows:
                        row['source_id'] = src['source_id']
                        row['record_id'] = stable('REC', row['source_id'], row['location'])
                sources[src['source_id']] = src
                if src['unsupported_content']:
                    diagnostics.append({'source': rel, 'code': 'UNSUPPORTED_CONTENT', 'reason': 'embedded images/objects were not examined'})
                for row in rows:
                    text = first(row, 'text') or (row['text'] if 'text' in row else '')
                    if role == 'delivery' and not text:
                        text = first(row, 'name')
                    if not text:
                        diagnostics.append({'source': row['source'], 'code': 'INVALID_INPUT', 'reason': 'empty required text'})
                        continue
                    if role == 'scope' and ('text' not in row and not first(row, 'text')):
                        diagnostics.append({'source': row['source'], 'code': 'INVALID_INPUT', 'reason': 'missing requirement text'})
                        continue
                    row.update(text=text, number=first(row, 'number'), reference=first(row, 'reference'), version=first(row, 'version'),
                               basis=first(row, 'basis'), condition=first(row, 'condition'), result=first(row, 'result'), role=role,
                               listed_only=role == 'delivery' and not (first(row, 'text') or 'text' in row),
                               claim_only=role == 'delivery' and bool(re.search('开发完成|已完成', text)) and not re.search('培训记录.*议程|端点.*请求参数', text))
                    records[row['record_id']] = row
            except (ValueError, OSError, UnicodeError, zipfile.BadZipFile) as exc:
                code, _, message = str(exc).partition(': ')
                diagnostics.append({'source': rel, 'code': code if message else 'UNREADABLE_SOURCE', 'reason': message or 'unreadable'})
    items = list(records.values())
    reqs = []
    for row in items:
        if row['role'] != 'scope':
            continue
        reqs.append({'requirement_id': stable('REQ', row['record_id']), 'number': row['number'], 'text': row['text'], 'source': row['source'],
                     'source_id': row['source_id'], 'version': row['version'], 'basis': row['basis'], 'conditions': conditions(row['text'], row['condition'])})
    if not items:
        raise ValueError('INVALID_INPUT: no readable material')
    evidence = []
    for row in items:
        if row['role'] in ('delivery', 'evidence'):
            evidence.append({'evidence_id': stable('EVD', row['record_id']), 'source_id': row['source_id'], 'source': row['source'],
                             'text': row['text'], 'role': row['role'], 'listed_only': row['listed_only'], 'claim_only': row['claim_only']})
    numbers = Counter(r['number'] for r in reqs if r['number'])
    conflicts = []
    duplicate = {n for n, count in numbers.items() if count > 1}
    for n in duplicate:
        conflicts.append({'type': 'DUPLICATE_ID', 'text': n, 'sources': [r['source'] for r in reqs if r['number'] == n]})
    versions = {}
    for row in items:
        if row['role'] == 'delivery' and row['version']:
            versions.setdefault(first(row, 'name') or row['text'].split('：')[0], []).append(row)
    version_conflict = set()
    for name, rows in versions.items():
        if len({r['version'] for r in rows}) > 1 and not any(
            r['source'].startswith(effective_version_ref + '/') and r['basis'] and r['version'] in {x['version'] for x in rows}
            for r in items if r['role'] == 'change'
        ):
            version_conflict.add(name)
            conflicts.append({'type': 'VERSION_CONFLICT', 'text': name, 'sources': [r['source'] for r in rows]})
    for row in items:
        if row['role'] == 'change' and not row['basis']:
            conflicts.append({'type': 'UNCONFIRMED_CHANGE', 'text': row['text'], 'sources': [row['source']]})
    findings = []
    for req in reqs:
        results = []
        pending = False
        relevant_version = any(name in req['text'] or name in ' '.join(req['conditions']) for name in version_conflict)
        for i, cond in enumerate(req['conditions'], 1):
            cid = stable('COND', req['requirement_id'], i)
            matches = evaluate_condition(cond, req, [r for r in items if r['role'] in ('delivery', 'evidence')])
            if req['number'] in duplicate:
                matches = []
                pending = True
            positives = [m[0] for m in matches if m[1] == 'SUPPORT']
            negatives = [m[0] for m in matches if m[1] == 'NONCONFORMING']
            if relevant_version:
                pending = True
            if not matches and not relevant_version:
                candidates = [r for r in items if r['role'] == 'evidence' and not r['reference'] and any(k in r['text'] and k in cond for k in ('登录', '培训', '接口'))]
                if candidates:
                    pending = True
                    conflicts.append({'type': 'MAPPING_CANDIDATE', 'text': cond, 'sources': [r['source'] for r in candidates] + [req['source']]})
            status = 'CONFLICT' if positives and negatives else 'NONCONFORMING' if negatives else 'EVIDENCE_FOUND' if positives and not relevant_version else 'PENDING_CONFIRMATION' if pending else 'NO_EVIDENCE_FOUND'
            results.append({'condition_id': cid, 'text': cond, 'status': status, 'support': [stable('EVD', r['record_id']) for r in positives],
                            'negative': [stable('EVD', r['record_id']) for r in negatives], 'sources': [r['source'] for r, _ in matches]})
            if positives and negatives:
                conflicts.append({'type': 'EVIDENCE_CONFLICT', 'text': cond, 'sources': [r['source'] for r, _ in matches]})
            if negatives:
                findings.append({'id': stable('GAP', cid, 'NONCONFORMING'), 'requirement_id': req['requirement_id'], 'condition_id': cid,
                                 'type': 'NONCONFORMING', 'text': cond, 'sources': [r['source'] for r in negatives], 'status': 'OPEN'})
            if not positives or negatives:
                findings.append({'id': stable('GAP', cid, 'MISSING'), 'requirement_id': req['requirement_id'], 'condition_id': cid,
                                 'type': 'MISSING', 'text': cond, 'sources': [req['source']], 'status': 'OPEN'})
        statuses = [r['status'] for r in results]
        req['status'] = ('CONFLICT' if 'CONFLICT' in statuses or relevant_version else 'NONCONFORMING' if 'NONCONFORMING' in statuses else
                         'PENDING_CONFIRMATION' if pending else 'PARTIAL_EVIDENCE' if 'EVIDENCE_FOUND' in statuses and len(set(statuses)) > 1 else
                         'EVIDENCE_FOUND' if statuses and all(s == 'EVIDENCE_FOUND' for s in statuses) else 'NO_EVIDENCE_FOUND')
        req['results'] = results
    old_gaps = {g['id']: g for g in old.get('findings', [])}
    now = {g['id']: g for g in findings}
    updates = []
    for fid, g in now.items():
        updates.append({'old_id': fid if fid in old_gaps else '', 'new_id': fid, 'type': 'UNCHANGED' if fid in old_gaps else 'NEW', 'evidence': ''})
    for fid, g in old_gaps.items():
        if fid not in now:
            result = next((r for req in reqs for r in req['results'] if r['condition_id'] == g['condition_id']), None)
            updates.append({'old_id': fid, 'new_id': '', 'type': 'RESOLVED' if result and result['support'] and not result['negative'] else 'REVIEW_REQUIRED',
                            'evidence': ', '.join(result['support']) if result else ''})
    for g in findings:
        if g['id'] in old_gaps:
            g['status'] = old_gaps[g['id']].get('status', 'OPEN')
    supported = sum(r['status'] == 'EVIDENCE_FOUND' for req in reqs for r in req['results'])
    total = sum(len(req['results']) for req in reqs)
    coverage = f'{supported}/{total}' if reqs and total and not version_conflict and not duplicate and all(r['basis'] or effective_version_ref for r in reqs) else 'N/A'
    limitations = [f"{d['source']}: {d['code']} ({d['reason']})" for d in diagnostics]
    if not reqs:
        limitations.append('NO_SCOPE_SOURCE: no readable scope; coverage N/A')
    if version_conflict:
        limitations.append('VERSION_CONFLICT: effective version requires explicit evidence; coverage N/A')
    return {'schema_version': 1, 'project': project, 'sources': list(sources.values()), 'records': items, 'requirements': reqs,
            'evidence': evidence, 'findings': findings, 'conflicts': conflicts, 'updates': updates,
            'coverage': coverage, 'effective_version_ref': effective_version_ref or 'NOT_SPECIFIED', 'limitations': limitations,
            'result': 'PARTIAL' if diagnostics else 'OK'}


def safe_cell(value):
    text = str(value if value is not None else '')
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text


def report(snapshot, dest):
    project = snapshot['project']
    paths = [dest / f'{project}-验收资料核对.xlsx', dest / f'{project}-验收准备报告.docx', dest / f'{project}-核查快照.json']
    if any(p.exists() or p.is_symlink() for p in paths):
        raise ValueError('OUTPUT_FAILED: refusing to overwrite existing report')
    wb = Workbook()
    wb.active.title = SHEETS[0]
    for name in SHEETS[1:]:
        wb.create_sheet(name)
    def rows(name, header, values):
        ws = wb[name]
        ws.append(header)
        for row in values:
            ws.append([safe_cell(v) for v in row])
    reqs = snapshot['requirements']
    gaps = snapshot['findings']
    rows(SHEETS[0], ['项目', '覆盖率', '有效版本/依据', '材料数', '状态数量', '限制'], [[project, snapshot['coverage'], snapshot['effective_version_ref'], len(snapshot['sources']), str(dict(Counter(r['status'] for r in reqs))), '; '.join(snapshot['limitations'])]])
    rows(SHEETS[1], ['requirement_id', '原始编号', '要求原文', '来源', '验收条件', '对应交付物', '证据位置', '核查结论', '已覆盖子条件', '未覆盖子条件', '缺口', '下一步确认事项'],
         [[r['requirement_id'], r['number'] or 'MISSING_ORIGINAL_ID', r['text'], r['source'], '; '.join(r['conditions']),
           ', '.join(e['evidence_id'] for e in snapshot['evidence'] if any(e['evidence_id'] in x['support'] + x['negative'] for x in r['results'])),
           '; '.join(s for x in r['results'] for s in x['sources']), r['status'], '; '.join(x['text'] for x in r['results'] if x['status'] == 'EVIDENCE_FOUND'),
           '; '.join(x['text'] for x in r['results'] if x['status'] != 'EVIDENCE_FOUND'), '; '.join(g['type'] + ': ' + g['text'] for g in gaps if g['requirement_id'] == r['requirement_id']),
           '确认候选或有效版本' if r['status'] in ('CONFLICT', 'PENDING_CONFIRMATION') else '按缺口补充材料'] for r in reqs])
    rows(SHEETS[2], ['evidence_id', '来源位置', '原文', '证明范围', '关联 requirement_id/condition_id', '确认状态'],
         [[e['evidence_id'], e['source'], e['text'], 'LISTED_ONLY' if e['listed_only'] else 'CLAIM_ONLY' if e['claim_only'] else 'CONTENT',
           '; '.join(r['requirement_id'] + '/' + x['condition_id'] for r in reqs for x in r['results'] if e['evidence_id'] in x['support'] + x['negative']), 'NOT_CONFIRMED'] for e in snapshot['evidence']])
    rows(SHEETS[3], ['发现 ID', '要求/子条件', '类型', '原文及来源', '是否解决', '下一步'],
         [[g['id'], g['requirement_id'] + '/' + g['condition_id'], g['type'], g['text'] + ' | ' + '; '.join(g['sources']), g['status'], '补充或确认可追溯证据'] for g in gaps])
    rows(SHEETS[4], ['类型', '候选/原文', '来源', '所需确认'], [[c['type'], c['text'], '; '.join(c['sources']), '提供可追溯确认依据'] for c in snapshot['conflicts']])
    rows(SHEETS[5], ['旧发现 ID', '新发现 ID', '变化', '解决证据 ID'], [[u['old_id'], u['new_id'], u['type'], u['evidence']] for u in snapshot['updates']])
    doc = Document()
    doc.add_heading(project + ' — 验收准备报告／草稿', 0)
    doc.add_paragraph('本报告仅描述本次资料的证据追踪，不构成正式验收结论或签字。')
    for title in SECTIONS:
        doc.add_heading(title, level=1)
        if title == SECTIONS[0]:
            doc.add_paragraph(project + '；有效范围依据：' + snapshot['effective_version_ref'] + '；覆盖：' + snapshot['coverage'])
        elif title == SECTIONS[1]:
            doc.add_paragraph('；'.join(s['path'] + ' [' + s['source_id'] + ']' for s in snapshot['sources']) or '未提供')
        elif title == SECTIONS[2]:
            doc.add_paragraph('；'.join(r['number'] + ' ' + r['status'] + ' ' + r['source'] for r in reqs) or '无可核查范围')
        elif title == SECTIONS[3]:
            table = doc.add_table(rows=1, cols=4)
            for c, text in zip(table.rows[0].cells, ['要求 ID', '条件/状态', '来源', '证据来源']): c.text = text
            for r in reqs:
                for x in r['results']:
                    cells = table.add_row().cells
                    for c, text in zip(cells, [r['requirement_id'] + '/' + x['condition_id'], x['text'] + ' ' + x['status'], r['source'],
                                                      '; '.join(x['support'] + x['negative']) + ' | ' + '; '.join(x['sources'])]): c.text = text
        elif title == SECTIONS[4]:
            table = doc.add_table(rows=1, cols=3)
            for c, text in zip(table.rows[0].cells, ['发现 ID/类型', '子条件', '来源']): c.text = text
            for g in gaps:
                for c, text in zip(table.add_row().cells, [g['id'] + ' ' + g['type'], g['text'], '; '.join(g['sources'])]): c.text = text
        elif title == SECTIONS[5]:
            doc.add_paragraph('；'.join(c['type'] + ' ' + c['text'] + ' ' + '; '.join(c['sources']) for c in snapshot['conflicts']) or '本次未识别到冲突')
        elif title == SECTIONS[6]:
            doc.add_paragraph('仅就本次材料核查，逐项补齐缺口并由有权人员确认版本/候选关系。不得把缺少材料推定为软件未开发。')
        else:
            doc.add_paragraph('；'.join(snapshot['limitations']) or '仅支持用户授权的可读内容；不判定正式验收。')
    stages = []
    try:
        for suffix in ('.xlsx', '.docx', '.json'):
            with tempfile.NamedTemporaryFile(dir=dest, prefix='.accept-', suffix=suffix, delete=False) as fh:
                stages.append(Path(fh.name))
        wb.save(stages[0])
        doc.save(stages[1])
        stages[2].write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # Verify real Office files before publishing any output.
        check = load_workbook(stages[0], read_only=True)
        assert check.sheetnames == SHEETS
        check.close()
        assert len(Document(stages[1]).tables) >= 2
        for stage, path in zip(stages, paths):
            stage.replace(path)
    except Exception:
        for path in paths:
            path.unlink(missing_ok=True)
        raise
    finally:
        for stage in stages:
            stage.unlink(missing_ok=True)
    return [str(p) for p in paths]


def main(argv=None):
    parser = argparse.ArgumentParser(description='Local acceptance-evidence preparation (not formal signoff)')
    parser.add_argument('--project-name', required=True)
    parser.add_argument('--authorized-input-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--scope-source', action='append', default=[])
    parser.add_argument('--delivery-source', action='append', default=[])
    parser.add_argument('--evidence-source', action='append', default=[])
    parser.add_argument('--change-source', action='append', default=[])
    parser.add_argument('--effective-version-ref', default='')
    parser.add_argument('--previous-snapshot', default='')
    args = parser.parse_args(argv)
    try:
        root = args.authorized_input_root.resolve(strict=True)
        if not root.is_dir() or args.authorized_input_root.is_symlink() or not args.project_name.strip() or re.search(r'[\\/:*?"<>|\x00-\x1f]', args.project_name) or args.project_name in ('.', '..') or len(args.project_name) > 80:
            raise ValueError('INVALID_INPUT: invalid root or project name')
        dest = safe_output(root, args.output_dir)
        groups = {'scope': args.scope_source, 'delivery': args.delivery_source, 'evidence': args.evidence_source, 'change': args.change_source}
        if args.effective_version_ref and args.effective_version_ref not in groups['scope'] + groups['change']:
            raise ValueError('INVALID_INPUT: effective version reference must be a supplied scope or confirmation source')
        old = None
        if args.previous_snapshot:
            path = source_path(root, args.previous_snapshot)
            if path.stat().st_size > MAX_BYTES:
                raise ValueError('RESOURCE_LIMIT: snapshot exceeds limit')
            old = json.loads(path.read_text(encoding='utf-8'))
            if old.get('schema_version') != 1 or old.get('project') != args.project_name:
                raise ValueError('INVALID_INPUT: snapshot project/schema mismatch')
        if not old and not any(groups.values()):
            raise ValueError('INVALID_INPUT: provide authorized materials or previous snapshot')
        result = analyze(args.project_name, root, groups, old, args.effective_version_ref)
        result['outputs'] = report(result, dest)
        print(json.dumps({'result': result['result'], 'outputs': result['outputs'], 'coverage': result['coverage'],
                          'requirements': [{'number': x['number'], 'status': x['status']} for x in result['requirements']],
                          'limitations': result['limitations']}, ensure_ascii=False))
        return 3 if result['result'] == 'PARTIAL' else 0
    except (ValueError, OSError, json.JSONDecodeError, AssertionError) as exc:
        message = str(exc)
        code = message.split(':', 1)[0] if ':' in message else 'OUTPUT_FAILED'
        print(json.dumps({'result': code, 'reason': message.split(': ', 1)[-1]}, ensure_ascii=False), file=sys.stderr)
        return 4 if code == 'OUTPUT_FAILED' else 2


if __name__ == '__main__':
    sys.exit(main())
