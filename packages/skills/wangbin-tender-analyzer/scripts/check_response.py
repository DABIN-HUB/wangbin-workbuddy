#!/usr/bin/env python3
"""Local, source-scoped bid response comparison; never authenticates qualifications."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import re
import stat
import sys
import tempfile
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

spec = importlib.util.spec_from_file_location("legacy_tender", Path(__file__).with_name("analyze_tender.py"))
assert spec and spec.loader
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
SHEETS = ("核查概览", "要求响应矩阵", "附件核对", "补遗与版本", "待确认事项")
DIMENSIONS = ("响应存在状态", "条件覆盖状态", "附件实际提供状态", "内容支持状态")
NUMBER = re.compile(r"^\s*(?:第(?:\S+章\s*)?)(\d+[a-zA-Z]?)\s*[.、．:]|^\s*(\d+[a-zA-Z]?)\s*[.、．:]")
MATERIAL = re.compile(r"[\w\u4e00-\u9fff.-]+\.(?:txt|md)\b", re.I)
WORD = re.compile(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}|\d+(?:\.\d+)?")


class InputError(Exception):
    def __init__(self, code: str, role: str):
        super().__init__(code)
        self.code, self.role = code, role


def read_text(path: Path, role: str, suffixes=('.txt', '.md')) -> str:
    if path.is_symlink():
        raise InputError('INPUT_SYMLINK', role)
    if path.suffix.lower() not in suffixes:
        raise InputError('INPUT_TYPE_UNSUPPORTED', role)
    try:
        st = path.stat()
        if not stat.S_ISREG(st.st_mode):
            raise InputError('INPUT_NOT_REGULAR', role)
        if st.st_size > 1_048_576:
            raise InputError('INPUT_TOO_LARGE', role)
        data = path.read_bytes()
        if len(data) > 1_048_576:
            raise InputError('INPUT_TOO_LARGE', role)
        return data.decode('utf-8-sig')
    except FileNotFoundError as exc:
        raise InputError('INPUT_NOT_FOUND', role) from exc
    except UnicodeDecodeError as exc:
        raise InputError('INVALID_UTF8', role) from exc
    except OSError as exc:
        raise InputError('INPUT_READ_FAILED', role) from exc


def quote(text: str) -> str:
    return legacy._evidence('', 1, text)['quote'].replace('|', '｜').replace('\n', ' ')


def loc(name: str, line: int) -> str:
    return f'{quote(name)}:{line}'


def number(text: str) -> str | None:
    m = NUMBER.search(text)
    return (m.group(1) or m.group(2)) if m else None


def body(text: str) -> str:
    return NUMBER.sub('', text, count=1).strip(' ：。.,')


def tokens(text: str) -> set[str]:
    # Bigrams permit advisory semantic candidates across changed wording, never authoritative coverage.
    cleaned = re.sub(r'我方|必须|须|应|提供|说明|支持|具备|要求|方案|附件|系统|原第|条|正式补遗|改为', ' ', text)
    found = set(WORD.findall(cleaned))
    return {piece for token in found for piece in ([token[i:i+2] for i in range(len(token)-1)] if re.fullmatch(r'[\u4e00-\u9fff]+', token) else [token])}


def covered(condition: str, reply: str) -> bool:
    terms = tokens(condition)
    if not terms:
        return False
    if '证明' in condition and not (MATERIAL.search(reply) or '证明' in reply and '提供' in reply):
        return False
    if '方案' in condition and '方案' not in reply and '简介' in reply:
        return False
    return all(term in reply for term in terms)


def conditions(text: str) -> list[str]:
    b = body(text)
    # Explicit conjuncts must each be supported. Never treat the mere mention of a topic as coverage.
    parts = re.split(r'[，,；;]|和|以及|同时', b)
    return [p.strip(' 。') for p in parts if p.strip(' 。') and not p.strip(' 。').startswith('另行通知')]


def requirements(sources: list[tuple[str, str]]) -> list[dict]:
    rows = []
    for source_index, (name, text) in enumerate(sources, 1):
        for n, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            num = number(line)
            is_amendment = source_index > 1
            rows.append({'id': f'{source_index}:{n}:{num or "无编号"}', 'number': num,
                         'text': quote(line), 'raw': line, 'source': loc(name, n),
                         'conditions': conditions(line), 'materials': MATERIAL.findall(line),
                         'version': '待确认（补遗关系未证实）' if is_amendment else '适用', 'candidates': [],
                         'pending': ['补遗与旧条款关系未证实，不能按文件名或上传顺序替换'] if is_amendment else []})
    return rows


def catalog_rows(path: Path | None) -> list[dict]:
    if path is None:
        return []
    text = read_text(path, 'attachment_catalog', ('.csv', '.xlsx')) if path.suffix.lower() == '.csv' else None
    try:
        if text is not None:
            records = list(csv.reader(text.splitlines()))
            source = path.name
        else:
            if path.is_symlink():
                raise InputError('INPUT_SYMLINK', 'attachment_catalog')
            try:
                if not path.is_file():
                    raise InputError('INPUT_NOT_REGULAR', 'attachment_catalog')
                if path.stat().st_size > 1_048_576:
                    raise InputError('INPUT_TOO_LARGE', 'attachment_catalog')
            except FileNotFoundError as exc:
                raise InputError('INPUT_NOT_FOUND', 'attachment_catalog') from exc
            records = []
            source = path.name
    except InputError:
        raise
    if path.suffix.lower() == '.xlsx':
        try:
            book = load_workbook(path, read_only=True, data_only=False, keep_links=False)
            sheet = book.active
            source = f'{path.name}/{sheet.title}'
            records = []
            for cells in sheet.iter_rows():
                if any(c.data_type == 'f' for c in cells):
                    raise InputError('CATALOG_SCHEMA_INVALID', 'attachment_catalog')
                records.append([str(c.value or '') for c in cells])
            book.close()
        except InputError:
            raise
        except Exception as exc:
            raise InputError('CATALOG_READ_FAILED', 'attachment_catalog') from exc
    if not records or '附件名称' not in records[0]:
        raise InputError('CATALOG_SCHEMA_INVALID', 'attachment_catalog')
    col = records[0].index('附件名称')
    return [{'name': quote(row[col]), 'source': loc(source, i), 'number': quote(row[records[0].index('关联要求编号')]) if '关联要求编号' in records[0] and len(row) > records[0].index('关联要求编号') else ''}
            for i, row in enumerate(records[1:], 2) if len(row) > col and row[col].strip()]


def relation_rows(reqs: list[dict], amendments: list[tuple[str, str]]) -> list[dict]:
    edges = []
    for row in reqs:
        if not row['id'].split(':')[0] == '1':
            continue
        for name, text in amendments:
            for n, line in enumerate(text.splitlines(), 1):
                if not re.search(r'正式补遗', line) or not re.search(r'替换为|改为|撤销|补充', line):
                    continue
                m = re.search(r'原第(\d+)条', line)
                if not m or m.group(1) != row['number']:
                    continue
                typ = '撤销' if '撤销' in line else '补充' if '补充' in line else '替换'
                new = [r for r in reqs if r['source'] == loc(name, n)]
                if new:
                    edges.append({'old': row, 'new': new[0], 'type': typ, 'source': loc(name, n), 'text': quote(line)})
    by_old = Counter(e['old']['id'] for e in edges if e['type'] in ('撤销', '替换'))
    for e in edges:
        old, new = e['old'], e['new']
        new['pending'] = [p for p in new['pending'] if '关系未证实' not in p]
        new['supersedes'] = old['number']
        revised = re.search(r'(?:替换为|改为)(\d+日|纸质[一二三四五六七八九十\d]+份)', new['raw'])
        new['revised_value'] = revised.group(1) if revised else None
        if by_old[old['id']] > 1:
            old['version'] = new['version'] = '待确认（冲突补遗）'
            old['pending'].append('多个正式补遗针对同一旧条款，需书面确定相互优先依据')
            new['pending'].append('多个正式补遗冲突，不能据上传顺序选择')
        elif e['type'] in ('撤销', '替换'):
            old['version'] = '已替换/撤销（不适用）'
            new['version'] = '适用（正式补遗）'
        else:
            new['version'] = '适用（补充）'
    return edges


def compare(reqs: list[dict], response: str | None, response_name: str | None,
            catalog: list[dict], evidence: list[tuple[str, str]]) -> list[dict]:
    replies = [(n, line, number(line)) for n, line in enumerate((response or '').splitlines(), 1) if line.strip()]
    results = []
    # A filename is evidence only if a unique requirement anchors it, not merely
    # because a similarly named file happened to be supplied by the user.
    numbered = Counter(r['number'] for r in reqs if r['number'])
    evidence_names = Counter(name for name, _ in evidence)
    catalog_names = Counter(c['name'] for c in catalog)
    material_owners = {}
    reply_refs = {}
    for _, line, num in replies:
        for material in MATERIAL.findall(line):
            reply_refs.setdefault(material, set()).add(num)
    for owner in reqs:
        for material in owner['materials']:
            material_owners.setdefault(material, set()).add(owner['id'])
    for r in reqs:
        candidates = []
        for n, line, num in replies:
            exact = bool(r['number'] and num == r['number'])
            similar = bool(tokens(body(r['raw'])) & tokens(body(line)))
            if exact or similar:
                candidates.append((n, line, exact))
        exacts = [c for c in candidates if c[2]]
        # Repeated source numbers do not uniquely identify a response; keep every candidate.
        duplicate_number = sum(x['number'] == r['number'] for x in reqs) > 1
        selected = exacts[0] if len(exacts) == 1 and not duplicate_number else None
        unique = selected is not None
        ambiguous = response is not None and not unique and bool(candidates)
        positions = [loc(response_name or '', n) for n, _, _ in candidates]
        reply = selected[1] if selected else ''
        cond = r['conditions']
        uncovered = [p for p in cond if not covered(p, reply)] if selected else cond
        existence = '未核查' if response is None else '已定位' if unique else '候选待确认' if ambiguous else '未找到（限已提供响应）'
        condition_state = '未核查' if response is None else '待确认' if ambiguous else '可能不充分' if not unique or uncovered else '已覆盖（文本层面）'
        materials = r['materials'][:]
        # A response-only reference is usable only with an unambiguous numbered
        # reply and an explicit material requirement. Never scan arbitrary files.
        response_only = [name for name in MATERIAL.findall(reply) if name not in materials]
        if unique and re.search(r'附件|证明|证书|材料|资质', r['raw']):
            materials += response_only
        listed = [c for c in catalog if c['name'] in materials or
                  (r['number'] and numbered[r['number']] == 1 and c['number'] == r['number'])]
        names = set(materials) | {c['name'] for c in listed}
        conflicting = {name for name in names if
                       evidence_names[name] > 1 or catalog_names[name] > 1 or
                       len(reply_refs.get(name, set())) > 1 or
                       (name in response_only and not (tokens(body(r['raw'])) & tokens(body(reply)))) or
                       material_owners.get(name, {r['id']}) - {r['id']} or
                       any(c['name'] == name and c['number'] and
                           (c['number'] != r['number'] or numbered[c['number']] != 1)
                           for c in catalog)}
        # Candidate response references and repeated original numbers are not
        # strong enough to attribute a material to one requirement.
        if not unique and not r['materials']:
            conflicting.update(MATERIAL.findall(' '.join(line for _, line, _ in candidates)))
        present = [(name, txt) for name, txt in evidence if name in names and name not in conflicting]
        if conflicting:
            attachment, support = '待确认', '待确认'
        elif not names:
            attachment, support = '不适用', '不适用'
        elif present:
            attachment = '已提供（可读文本）'
            relevant = [loc(name, i) for name, txt in present for i, line in enumerate(txt.splitlines(), 1) if any(t in line for t in tokens(r['raw']))]
            contradictory = any(('尚未取得' in txt or '拟申请' in txt or ('2027' in r['raw'] and '2026' in txt)) for _, txt in present)
            supported = any(all(covered(p, line) for p in r['conditions'] if not MATERIAL.search(p))
                            for _, txt in present for line in txt.splitlines() if line.strip()) and bool(relevant)
            support = '不支持（文本层面）' if contradictory else '支持（文本层面）' if supported else '待确认'
        elif listed:
            attachment, support = '仅目录登记', '未核验'
        elif catalog:
            attachment, support = '未提供（限已提供材料）', '未核验'
        else:
            attachment, support = '待确认', '未核验'
        evidence_loc = [loc(name, i) for name, txt in present for i, line in enumerate(txt.splitlines(), 1) if line.strip()][:12]
        gaps = []
        if existence == '未找到（限已提供响应）':
            gaps.append('在已提供响应中未找到')
        if condition_state == '可能不充分':
            gaps.append('明确条件未获得完整文本支持：' + '、'.join(quote(p) for p in uncovered))
        if attachment == '仅目录登记':
            gaps.append('附件仅目录登记，需补实际材料并核内容')
        if support == '不支持（文本层面）':
            gaps.append('实际材料内容与声明矛盾或未支持；需人工核验')
        revised = r.get('revised_value')
        obsolete = [(n, line) for n, line, num in replies if num == r.get('supersedes') and revised and revised not in line]
        if r['version'] == '适用（正式补遗）' and obsolete:
            gaps.append('版本冲突：响应仍沿用旧要求，正式补遗新值 ' + quote(revised) + '；响应 ' + '、'.join(loc(response_name or '', n) for n, _ in obsolete))
            for n, _ in obsolete:
                if loc(response_name or '', n) not in positions:
                    positions.append(loc(response_name or '', n))
            if existence == '未找到（限已提供响应）':
                existence = '候选待确认'
                gaps = [g for g in gaps if g != '在已提供响应中未找到']
            condition_state = '可能不充分'
        pending = r['pending'][:]
        if ambiguous:
            pending.append('响应候选歧义或编号改变；逐一核对双向原句')
        if conflicting:
            pending.append('材料候选重复、编号冲突或响应配对歧义；逐一核对文件与要求关联')
        elif attachment == '待确认' and materials:
            pending.append('未提供完整附件集合/目录，无法判定实际缺失')
        if support == '待确认' and not conflicting:
            pending.append('材料文本关联不足或真实性需人工确认')
        results.append({**r, 'locations': positions, 'response': quote(reply) if reply else '',
                        'existence': existence, 'coverage': condition_state, 'attachment': attachment,
                        'support': support, 'listed': listed, 'present': present, 'conflicting': sorted(conflicting),
                        'evidence_locations': evidence_loc, 'gaps': gaps, 'pending': pending})
    return results


def safe_cell(value) -> str:
    text = str(value if value is not None else '')
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text


def write_outputs(rows: list[dict], catalog: list[dict], edges: list[dict], args) -> tuple[Path, Path]:
    project = args.project or '未命名项目'
    if project in ('.', '..') or '..' in project or re.search(r'[/\\\x00-\x1f<>:"|?*]', project):
        raise InputError('OUTPUT_PATH_INVALID', 'project')
    folder = args.output_dir
    if folder.is_symlink() or not folder.is_dir():
        raise InputError('OUTPUT_PATH_INVALID', 'output_dir')
    xlsx = folder / f'{project}-投标响应检查.xlsx'
    md = folder / f'{project}-提交前核对清单.md'
    if xlsx.exists() or md.exists() or xlsx.is_symlink() or md.is_symlink():
        raise InputError('OUTPUT_EXISTS', 'output_dir')
    wb = Workbook()
    overview = wb.active
    overview.title = SHEETS[0]
    matrix, attachments, amendments, pending = [wb.create_sheet(s) for s in SHEETS[1:]]
    mode = '核查模式' if args.response else '准备模式；响应未核查'
    overview.append(['模式', mode]); overview.append(['项目', project if args.project else '未提供项目名称'])
    overview.append(['范围', '仅用户明确给出的有限文本和材料，不认证证书真伪/投标结果'])
    overview.append(['来源', ', '.join(p.name for p in [args.tender, *(args.amendment or []), *([args.response] if args.response else [])])])
    for title, key in zip(DIMENSIONS, ('existence', 'coverage', 'attachment', 'support')):
        overview.append([title, '状态', '计数'])
        for status, count in sorted(Counter(r[key] for r in rows).items()):
            overview.append([title, status, count])
    overview.append(['局限', '限长脱敏摘录；回原件复核。未输入材料不等于已确认不存在；无资质/保证金/法律效力认证。'])
    matrix.append(['唯一ID', '要求编号', '要求原文', '来源', '明确条件', '响应位置', '响应内容', '支持材料', '证据位置', *DIMENSIONS, '缺口', '建议', '适用版本', '候选及理由'])
    for r in rows:
        matrix.append([r['id'], r['number'], r['text'], r['source'], '；'.join(map(quote, r['conditions'])),
                       '；'.join(r['locations']), r['response'], '；'.join(r['materials']), '；'.join(r['evidence_locations']),
                       r['existence'], r['coverage'], r['attachment'], r['support'], '；'.join(r['gaps']),
                       '；'.join(r['pending'] or ['按源文件行核对，不能推断投标结果']), r['version'],
                       '；'.join(r['locations']) + ('；编号变化/文本近似仅候选，需人工确认' if r['existence'] == '候选待确认' else '')])
    attachments.append(['唯一ID', '附件名称', '目录位置', '实际文件', '是否实际提供', '内容支持状态', '材料行证据', '未核验理由'])
    for r in rows:
        for item in r['listed']:
            attachments.append([r['id'], item['name'], item['source'], '；'.join(name for name, _ in r['present']), r['attachment'], r['support'], '；'.join(r['evidence_locations']), '仅目录不证明文件存在' if not r['present'] else '文本支持不认证真伪'])
        if r['present'] and not r['listed']:
            for name, _ in r['present']:
                attachments.append([r['id'], '', '', name, r['attachment'], r['support'], '；'.join(r['evidence_locations']), '文本支持不认证真伪'])
        for name in r['conflicting']:
            if not any(item['name'] == name for item in r['listed']):
                attachments.append([r['id'], '', '', name, '待确认', '待确认', '', '文件与要求关联歧义，不能确认为已提供'])
    amendments.append(['原唯一ID', '新唯一ID', '关系', '原要求来源', '新要求来源', '依据位置', '依据原句', '适用/冲突'])
    for e in edges:
        amendments.append([e['old']['id'], e['new']['id'], e['type'], e['old']['source'], e['new']['source'], e['source'], e['text'], e['old']['version']])
    if not edges:
        amendments.append(['无已证明正式替换关系', '', '', '', '', '', '', '未提供或依据不足'])
    pending.append(['唯一ID', '问题', '触发位置', '人工动作', '影响维度'])
    for r in rows:
        for question in r['pending']:
            pending.append([r['id'], question, r['source'], '回源文件及材料原件确认', '条件/附件/内容/版本'])
    for sheet in wb:
        sheet.freeze_panes = 'A2'
        for cells in sheet:
            for cell in cells:
                if cell.data_type == 'f':
                    cell.value = safe_cell(cell.value)
                if cell.row == 1:
                    cell.font = Font(bold=True)
    md_lines = [f'# {quote(project)} · 提交前核对清单', '', mode, '', '仅核对已提供范围；文本证据不认证资质真伪、保证金到账、结果或法律效力。', '摘录已限长脱敏，脱敏非完备；回原件核查。', '']
    for heading, selector in [('确定需要补资料（已提供范围）', lambda r: r['gaps']), ('需要人工确认', lambda r: r['pending']),
                              ('已覆盖范围（仅文本层面）', lambda r: [r['existence']] if r['coverage'] == '已覆盖（文本层面）' else []),
                              ('未覆盖范围（仅已提供材料）', lambda r: [r['coverage']] if r['coverage'] == '可能不充分' else [])]:
        md_lines += ['## ' + heading]
        for r in rows:
            for note in selector(r):
                evidence_position = ('；材料 ' + '、'.join(r['evidence_locations'])) if r['evidence_locations'] else ''
                md_lines.append(f"- {r['id']} (原编号 {r['number'] or '无'}；{r['source']}；响应 {', '.join(r['locations']) or '未定位'}{evidence_position})：{note}。四维：{r['existence']} / {r['coverage']} / {r['attachment']} / {r['support']}。")
        md_lines.append('')
    temp_x = temp_m = None
    try:
        with tempfile.NamedTemporaryFile(dir=folder, prefix='.bid-', suffix='.xlsx', delete=False) as f:
            temp_x = Path(f.name)
        with tempfile.NamedTemporaryFile(dir=folder, prefix='.bid-', suffix='.md', delete=False) as f:
            temp_m = Path(f.name)
        wb.save(temp_x)
        temp_m.write_text('\n'.join(md_lines) + '\n', encoding='utf-8')
        if xlsx.exists() or md.exists():
            raise InputError('OUTPUT_EXISTS', 'output_dir')
        temp_x.replace(xlsx)
        try:
            temp_m.replace(md)
        except OSError:
            xlsx.unlink(missing_ok=True)
            raise
    except InputError:
        raise
    except OSError as exc:
        raise InputError('OUTPUT_WRITE_FAILED', 'output_dir') from exc
    finally:
        for temp in (temp_x, temp_m):
            if temp:
                temp.unlink(missing_ok=True)
    return xlsx, md


def run(args) -> tuple[Path, Path]:
    if args.tender is None:
        raise InputError('MISSING_TENDER', 'tender')
    if args.mode == 'check' and args.response is None:
        raise InputError('MISSING_RESPONSE', 'response')
    if args.mode == 'prepare' and args.response is not None:
        raise InputError('OUTPUT_PATH_INVALID', 'mode')
    inputs = [('tender', args.tender), ('response', args.response), *[('amendment', p) for p in args.amendment],
              ('attachment_catalog', args.attachment_catalog), *[('evidence_files', p) for p in args.evidence_file]]
    seen = set()
    for role, path in inputs:
        if path is None:
            continue
        resolved = path.resolve()
        if resolved in seen:
            raise InputError('INPUT_NOT_REGULAR', role)
        seen.add(resolved)
    tender = read_text(args.tender, 'tender')
    response = read_text(args.response, 'response') if args.response else None
    amendments = [(p.name, read_text(p, 'amendment')) for p in args.amendment]
    evidence = [(p.name, read_text(p, 'evidence_files')) for p in args.evidence_file]
    catalog = catalog_rows(args.attachment_catalog)
    reqs = requirements([(args.tender.name, tender), *amendments])
    edges = relation_rows(reqs, amendments)
    rows = compare(reqs, response, args.response.name if args.response else None, catalog, evidence)
    return write_outputs(rows, catalog, edges, args)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Local bid response comparison; text evidence is not certification.')
    parser.add_argument('--tender', type=Path)
    parser.add_argument('--response', type=Path)
    parser.add_argument('--mode', choices=('auto', 'prepare', 'check'), default='auto')
    parser.add_argument('--amendment', action='append', default=[], type=Path)
    parser.add_argument('--attachment-catalog', type=Path)
    parser.add_argument('--evidence-file', action='append', default=[], type=Path)
    parser.add_argument('--project')
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        xlsx, md = run(args)
    except InputError as exc:
        print(f'ERROR {exc.code} role={exc.role}', file=sys.stderr)
        return 2
    print(f'CREATED {xlsx.name} {md.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
