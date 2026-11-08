"""Local, evidence-first DOCX return comparison. No network or document mutation."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import zipfile

from defusedxml import ElementTree as SafeET
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from openpyxl import Workbook

MAX_BYTES = 10 * 1024 * 1024
MAX_UNITS = 2000
MAX_CHARS = 100000
NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
REVISIONS = {'ins', 'del', 'moveFrom', 'moveTo', 'moveFromRangeStart', 'moveFromRangeEnd',
             'moveToRangeStart', 'moveToRangeEnd', 'delText', 'cellIns', 'cellDel',
             'cellMerge', 'numberingChange', 'pPrChange', 'rPrChange', 'tblPrChange',
             'trPrChange', 'tcPrChange', 'sectPrChange', 'customXmlInsRangeStart',
             'customXmlDelRangeStart'}
TOPICS = ('付款', '金额', '交付', '验收', '服务范围', '期限', '其他')
NUMBER = re.compile(r'^\s*(第[一二三四五六七八九十百千零〇0-9]+条[、，,.：:]?\s*)')
SHEETS = ('检查概览', '逐项差异', '关键商务变化', '待确认与未覆盖')


class ContractError(Exception):
    def __init__(self, status: str, reason: str, message: str):
        self.status, self.reason, self.message = status, reason, message
        super().__init__(message)


@dataclass(frozen=True)
class Unit:
    locator: str
    text: str
    kind: str
    key: str = ''


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def read_docx(path: Path) -> tuple[list[Unit], list[dict]]:
    if path.suffix.lower() != '.docx' or not path.is_file():
        raise ContractError('ERROR', 'INVALID_DOCX', '需要可读取的 .docx 文件，不支持旧 .doc。')
    if path.stat().st_size > MAX_BYTES:
        raise ContractError('ERROR', 'LIMIT_EXCEEDED', '单份 DOCX 超过 10 MiB。')
    warnings = []
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > 2000 or not any(i.filename == 'word/document.xml' for i in members):
                raise ValueError('missing document or too many members')
            for item in members:
                name = item.filename.replace('\\', '/')
                if (name.startswith('/') or re.match(r'^[A-Za-z]:', name) or
                    '..' in name.split('/') or item.file_size > 12 * 1024 * 1024 or
                    (item.compress_size and item.file_size > max(item.compress_size * 200, 1024 * 1024))):
                    raise ValueError('unsafe OOXML member')
            for item in members:
                if item.filename.startswith('word/') and item.filename.endswith('.xml'):
                    xml = archive.read(item)
                    root = SafeET.fromstring(xml)
                    for node in root.iter():
                        tag = node.tag.rsplit('}', 1)[-1]
                        if tag in REVISIONS or (tag.endswith('Change') and node.tag.startswith(NS)):
                            raise ContractError('NEEDS_INPUT', 'REVISION_STATE',
                                                '检测到未解决的 Word 修订；请提供明确接受修订后的比较副本。')
                        if item.filename == 'word/document.xml' and tag in {'txbxContent', 'pict', 'drawing', 'object'}:
                            warnings.append({'locator': 'word/document.xml', 'reason': '未支持载体：文本框/图片或对象',
                                             'question': '请人工核查该载体中的条款；图片未做 OCR。'})
        doc = Document(path)
        units = []
        body_index = table_index = 0
        for child in doc.element.body.iterchildren():
            if child.tag == qn('w:p'):
                body_index += 1
                text = Paragraph(child, doc).text
                if text.strip():
                    units.append(Unit(f'正文段落{body_index}', text, 'body_paragraph'))
            elif child.tag == qn('w:tbl'):
                table_index += 1
                table = Table(child, doc)
                if child.xpath('.//w:tbl/w:tr/w:tc/w:tbl'):
                    warnings.append({'locator': f'表格{table_index}', 'reason': '嵌套表格未比较',
                                     'question': '请人工核查嵌套表格。'})
                for ri, row in enumerate(table.rows, 1):
                    key = row.cells[0].text.strip() if len(row.cells) > 1 else ''
                    for ci, cell in enumerate(row.cells, 1):
                        if cell.text.strip():
                            units.append(Unit(f'表格{table_index}/行{ri}/列{ci}', cell.text,
                                              'table_cell', key))
        if len(units) > MAX_UNITS or sum(len(u.text) for u in units) > MAX_CHARS:
            raise ContractError('ERROR', 'LIMIT_EXCEEDED', '可比较单元或文本超过上限；请缩减文档。')
        return units, warnings
    except ContractError:
        raise
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, SafeET.ParseError) as exc:
        raise ContractError('ERROR', 'INVALID_DOCX', f'DOCX 损坏、加密或不安全：{type(exc).__name__}') from exc


def split_number(text: str) -> tuple[str, str]:
    match = NUMBER.match(text)
    return (match.group(1).strip(), text[match.end():]) if match else ('', text)


def topic(text: str) -> str:
    for name, words in [('付款', ('付款', '支付', '结算')), ('金额', ('金额', '单价', '价格', '元', '含税')),
                        ('交付', ('交付', '交货')), ('验收', ('验收',)),
                        ('服务范围', ('服务', '培训', '质保')), ('期限', ('期限', '服务期', '延期'))]:
        if any(word in text for word in words):
            return name
    return '其他'


def delta(old: str, new: str) -> str:
    old_nums = re.findall(r'\d+(?:\.\d+)?', old)
    new_nums = re.findall(r'\d+(?:\.\d+)?', new)
    changed = [(a, b) for a, b in zip(old_nums, new_nums) if a != b]
    if len(old_nums) == len(new_nums) and len(changed) == 1 and re.search(r'(?<!\d)' + re.escape(changed[0][0]) + r'\s*天', old) and re.search(r'(?<!\d)' + re.escape(changed[0][1]) + r'\s*天', new):
        a, b = changed[0]
        if a.isdigit() and b.isdigit():
            return f'{a}→{b}天，明确{("延长" if int(b) > int(a) else "缩短")}{abs(int(b)-int(a))}天；其他数字保持原文'
    return f'{old} → {new}'


def obligation_evidence(a: Unit, b: Unit) -> str:
    """Require shared business action and compatible language, not a slot or number."""
    if a.kind != b.kind:
        return ''
    if a.kind == 'table_cell':
        return (f'唯一表格业务键 {a.key} / 同列' if a.key and a.key == b.key
                and a.locator.split('/')[-1] == b.locator.split('/')[-1] else '')
    old, new = split_number(a.text)[1], split_number(b.text)[1]
    # Identical nonempty clause bodies are direct evidence even when no action
    # appears in the commercial vocabulary. Require two explicit clause numbers;
    # the caller still checks reciprocal uniqueness before pairing candidates.
    old_number, _ = split_number(a.text)
    new_number, _ = split_number(b.text)
    if old_number and new_number and old_number != new_number and old.strip() and old == new:
        return '双方编号不同、去编号后的完整条款原文相同且无竞争候选'
    actions = ('付款', '支付', '结算', '交付', '交货', '验收', '服务期', '质保', '延期', '价格', '金额', '保密')
    shared = [word for word in actions if word in old and word in new]
    if not shared:
        return ''
    normalized = lambda s: re.sub(r'[\d\s，。,.：:；;、第条]', '', s)
    if SequenceMatcher(None, normalized(old), normalized(new), autojunk=False).ratio() < .55:
        return ''
    return f'双方共有业务动作 {"/".join(shared)}，去数字正文相容且无竞争候选'


def compare(original: list[Unit], returned: list[Unit]) -> tuple[list[dict], list[dict]]:
    changes: list[dict] = []
    uncertainty: list[dict] = []
    used_o: set[int] = set()
    used_r: set[int] = set()

    def emit(kind: str, a: Unit | None, b: Unit | None, old: str | None = None, new: str | None = None,
             basis: str = ''):
        old = a.text if old is None and a else old
        new = b.text if new is None and b else new
        old = old if old is not None else 'N/A (不存在)'
        new = new if new is not None else 'N/A (不存在)'
        changes.append({'type': kind, 'topic': topic((old if old != 'N/A (不存在)' else '') + (new if new != 'N/A (不存在)' else '')),
                        'old_locator': a.locator if a else 'N/A (不存在)',
                        'new_locator': b.locator if b else 'N/A (不存在)', 'old_text': old,
                        'new_text': new, 'explicit_delta': delta(old, new) if kind == 'MODIFY' else f'{old} → {new}',
                        'alignment_confidence': '确定', 'alignment_basis': basis or ('独立单边增删' if not a or not b else '双方原文相同'),
                        'possible_impact': '原文条件变化，需人工确认' if kind in {'MODIFY', 'ADD', 'DELETE'} else '仅位置或编号变化',
                        'confirmation_question': '请核实双方原文和该变化是否符合约定。'})

    def paired(i: int, j: int, basis: str = ''):
        used_o.add(i); used_r.add(j)
        a, b = original[i], returned[j]
        an, ac = split_number(a.text)
        bn, bc = split_number(b.text)
        if an != bn and (an or bn):
            emit('NUMBER', a, b, basis=basis)
            changes[-1]['explicit_delta'] = f'{an or "N/A (不存在)"} → {bn or "N/A (不存在)"}'
        if ac != bc:
            emit('MODIFY', a, b, ac, bc, basis)
        elif a.locator != b.locator and not (an != bn):
            emit('MOVE', a, b, basis)

    # Unique table business keys identify corresponding cells even after row relocation.
    def table_key(u: Unit):
        return (u.locator.split('/')[0], u.key, u.locator.split('/')[-1]) if u.kind == 'table_cell' and u.key else None
    for i, a in enumerate(original):
        key = table_key(a)
        if key and a.locator.endswith('列1'):
            continue
        if key:
            oi = [x for x, u in enumerate(original) if table_key(u) == key]
            rj = [x for x, u in enumerate(returned) if table_key(u) == key]
            if len(oi) == len(rj) == 1 and i not in used_o and rj[0] not in used_r:
                paired(i, rj[0])
    # Stable exact sequence anchors: shifting a paragraph for a single move does not move all neighbors.
    anchors = SequenceMatcher(None, [(u.kind, u.text) for u in original],
                              [(u.kind, u.text) for u in returned], autojunk=False)
    for block in anchors.get_matching_blocks():
        for offset in range(block.size):
            i, j = block.a + offset, block.b + offset
            if i not in used_o and j not in used_r:
                used_o.add(i); used_r.add(j)
    # Exact unique text first, including relocated clauses. Duplicate evidence stays uncertain.
    for i, a in enumerate(original):
        if i in used_o: continue
        oi = [x for x, u in enumerate(original) if u.kind == a.kind and u.text == a.text and x not in used_o]
        rj = [x for x, u in enumerate(returned) if u.kind == a.kind and u.text == a.text and x not in used_r]
        if len(oi) == len(rj) == 1:
            paired(i, rj[0])
    # Unique shared commercial action plus compatible language; topic/slot alone is insufficient.
    for i, a in enumerate(original):
        if i in used_o or a.kind != 'body_paragraph': continue
        subject = topic(a.text)
        if subject == '其他': continue
        oi = [x for x, u in enumerate(original) if x not in used_o and u.kind == a.kind and topic(u.text) == subject]
        rj = [x for x, u in enumerate(returned) if x not in used_r and u.kind == a.kind and topic(u.text) == subject]
        if len(oi) == len(rj) == 1:
            basis = obligation_evidence(a, returned[rj[0]])
            if basis:
                paired(i, rj[0], basis)
    for i, a in enumerate(original):
        if i in used_o: continue
        candidates = []
        for j, b in enumerate(returned):
            if j in used_r or not obligation_evidence(a, b): continue
            candidates.append(j)
        if len(candidates) == 1:
            j = candidates[0]
            reverse = [x for x, u in enumerate(original) if x not in used_o and obligation_evidence(u, returned[j])]
            if len(reverse) == 1:
                paired(i, j, obligation_evidence(a, returned[j]))
    remaining_o = [i for i in range(len(original)) if i not in used_o]
    remaining_r = [j for j in range(len(returned)) if j not in used_r]
    # Sole remaining items and stable neighbors only establish a textual slot, not a duty.
    if len(remaining_o) == len(remaining_r) == 1:
        i, j = remaining_o[0], remaining_r[0]
        basis = obligation_evidence(original[i], returned[j])
        if basis:
            paired(i, j, basis)
            remaining_o = remaining_r = []
    # Keep an unresolved replacement conservative, but do not let a *separate*
    # competing obligation consume unrelated one-sided changes. An isolated
    # endpoint is independent only if its topic has no counterpart at all;
    # without a competing group, two unmatched sides remain an uncertain pair.
    competing = any(sum(obligation_evidence(original[i], returned[j]) != ''
                        for j in remaining_r) > 1 for i in remaining_o) or any(
        sum(obligation_evidence(original[i], returned[j]) != '' for i in remaining_o) > 1
        for j in remaining_r)
    if competing:
        old_topics = {topic(original[i].text) for i in remaining_o}
        new_topics = {topic(returned[j].text) for j in remaining_r}
        independent_o = [i for i in remaining_o if topic(original[i].text) not in new_topics
                         and topic(original[i].text) != '其他'
                         and not any(obligation_evidence(original[i], returned[j]) for j in remaining_r)]
        independent_r = [j for j in remaining_r if topic(returned[j].text) not in old_topics
                         and topic(returned[j].text) != '其他'
                         and not any(obligation_evidence(original[i], returned[j]) for i in remaining_o)]
        for i in independent_o: emit('DELETE', original[i], None)
        for j in independent_r: emit('ADD', None, returned[j])
        remaining_o = [i for i in remaining_o if i not in independent_o]
        remaining_r = [j for j in remaining_r if j not in independent_r]
    if remaining_o and remaining_r:
        uncertainty.append({'locator': ' / '.join(original[i].locator for i in remaining_o) + ' → ' +
                            ' / '.join(returned[j].locator for j in remaining_r),
                            'reason': '对应证据不足或多个候选；原稿：' + ' | '.join(original[i].text for i in remaining_o) +
                            '；回传稿：' + ' | '.join(returned[j].text for j in remaining_r) + '；不计入确定变化',
                            'question': '请人工核实双方原文、位置及是否同一义务。',
                            'candidate_old': [{'locator': original[i].locator, 'text': original[i].text} for i in remaining_o],
                            'candidate_new': [{'locator': returned[j].locator, 'text': returned[j].text} for j in remaining_r]})
    else:
        for i in remaining_o: emit('DELETE', original[i], None)
        for j in remaining_r: emit('ADD', None, returned[j])
    for index, change in enumerate(changes, 1):
        change['change_id'] = f'CHG-{index:03d}'
    return changes, uncertainty


def safe_cell(value: object):
    return '' if value is None else str(value)


def put(ws, row):
    ws.append([safe_cell(v) for v in row])
    for cell in ws[ws.max_row]:
        cell.data_type = 's'  # Force literal text even for =, +, -, @ or whitespace/control prefix.


def outputs(original: Path, returned: Path, changes: list[dict], warnings: list[dict],
            output_dir: Path, contract_name: str, focus: list[str], draft: bool, hashes: dict,
            root: Path | None = None) -> dict:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', contract_name).strip(' .')[:60] or '合同'
    if not output_dir.is_dir():
        raise ContractError('ERROR', 'IO_FAILURE', '输出目录不存在或不可写。')
    visible = [c for c in changes if not focus or c['topic'] in focus or c['type'] == 'NUMBER']
    omitted = sorted({c['topic'] for c in changes if c not in visible})
    status = 'PARTIAL' if warnings else 'COMPLETE'
    files = []
    try:
        for n in range(1000):
            stem = name + (f'-{n}' if n else '')
            xlsx = output_dir / f'{stem}-版本差异.xlsx'
            docx = output_dir / f'{stem}-商务变化说明.docx'
            checked_path(str(output_dir), root)
            if any(p == original or p == returned or p.exists() for p in (xlsx, docx)):
                continue
            with xlsx.open('xb'): pass
            files.append(xlsx)
            checked_path(str(output_dir), root)
            with docx.open('xb'): pass
            files.append(docx)
            break
        else:
            raise OSError('no unique output filename')
        book = Workbook()
        overview = book.active
        overview.title = SHEETS[0]
        detail, business, uncovered = (book.create_sheet(s) for s in SHEETS[1:])
        for row in [('状态', status), ('方向', '发出稿 → 回传稿'), ('发出稿', original.name), ('发出稿 SHA-256', hashes['original']),
                    ('回传稿', returned.name), ('回传稿 SHA-256', hashes['returned']),
                    ('检查范围', 'DOCX 正文段落与普通表格；不覆盖图片/文本框/嵌套表格'),
                    ('重点筛选', ', '.join(focus) if focus else '全部'),
                    ('确认变化 ID 总数（筛选前）', len(changes)), ('显示变化 ID 数', len(visible)),
                    ('未展示主题', ', '.join(omitted) or '无'), ('不确定/未覆盖数', len(warnings))]: put(overview, row)
        for kind in ('ADD', 'DELETE', 'MODIFY', 'MOVE', 'NUMBER'):
            put(overview, (kind, sum(c['type'] == kind for c in changes)))
        if not changes:
            put(overview, ('说明', '已检查范围内未发现已确认变化；如有未覆盖，不代表整份无变化。'))
        put(detail, ('change_id', '主题', '原稿位置', '回传稿位置', '原文', '新文', '变化类型', '明确变化', '确定程度', '可能影响', '确认问题', '原稿SHA-256', '回传稿SHA-256'))
        put(business, ('change_id', '主题', '原稿位置', '回传稿位置', '原文', '新文', '明确变化', '确认问题'))
        for c in visible:
            put(detail, tuple(c[k] for k in ('change_id', 'topic', 'old_locator', 'new_locator', 'old_text', 'new_text', 'type', 'explicit_delta', 'alignment_confidence', 'possible_impact', 'confirmation_question')) + (hashes['original'], hashes['returned']))
            if c['type'] in {'MODIFY', 'ADD', 'DELETE'}:
                put(business, tuple(c[k] for k in ('change_id', 'topic', 'old_locator', 'new_locator', 'old_text', 'new_text', 'explicit_delta', 'confirmation_question')))
        put(uncovered, ('来源位置/候选', '原因/影响', '待确认问题'))
        for w in warnings:
            put(uncovered, (w['locator'], w['reason'], w['question']))
        if omitted:
            put(uncovered, ('主题筛选', '已核实但未展示：' + ', '.join(omitted), '需要时取消筛选并复核所有主题。'))
        checked_path(str(output_dir), root)
        book.save(xlsx)
        note = Document()
        note.add_heading(name + '｜商务变化说明', 0)
        note.add_paragraph(f'状态：{status}；方向：发出稿 → 回传稿；范围：正文段落和普通表格。非法律结论。')
        note.add_paragraph(f'发出稿：{original.name} SHA-256 {hashes["original"]}')
        note.add_paragraph(f'回传稿：{returned.name} SHA-256 {hashes["returned"]}')
        note.add_paragraph(f'确认变化（全量 {len(changes)}，显示 {len(visible)}）；筛选：{", ".join(focus) if focus else "全部"}。未展示：{", ".join(omitted) or "无"}。')
        if not changes:
            note.add_paragraph('在已检查范围内未发现已确认变化；如有未覆盖，不代表整份无变化。')
        for c in visible:
            note.add_heading(f'{c["change_id"]} {c["type"]} / {c["topic"]}', level=2)
            note.add_paragraph(f'原稿 {c["old_locator"]}：{c["old_text"]}')
            note.add_paragraph(f'回传稿 {c["new_locator"]}：{c["new_text"]}')
            note.add_paragraph(f'明确变化：{c["explicit_delta"]}；{c["confirmation_question"]}')
        note.add_heading('待确认与未覆盖', level=1)
        for w in warnings:
            note.add_paragraph(f'{w["locator"]}：{w["reason"]}；{w["question"]}')
        if omitted: note.add_paragraph('筛选未展示：' + ', '.join(omitted))
        if draft:
            note.add_heading('沟通草稿（未发送，不代表接受修改）', level=1)
            if visible:
                note.add_paragraph('您好，关于回传稿，烦请核实以下事项：' + '；'.join(
                    f'{c["change_id"]} {c["old_text"]} → {c["new_text"]}' for c in visible) + '。谢谢！本草稿仅供人工审核，未表态接受。')
            else: note.add_paragraph('没有足够的已核实变化可起草，请先核实待确认内容。')
        checked_path(str(output_dir), root)
        note.save(docx)
        checked_path(str(output_dir), root)
        return {'status': status, 'changes': changes, 'uncertainty': warnings, 'xlsx': str(xlsx), 'docx': str(docx), 'source_sha256': hashes}
    except (OSError, ValueError, PermissionError) as exc:
        try:
            checked_path(str(output_dir), root)
        except ContractError:
            raise ContractError('ERROR', 'UNSAFE_PATH', '输出目录在写出期间被重解析；停止清理以免触碰目标。') from exc
        for path in files: path.unlink(missing_ok=True)
        raise ContractError('ERROR', 'IO_FAILURE', f'写出失败：{type(exc).__name__}') from exc


def checked_path(value: str, root: Path | None = None) -> Path:
    """Inspect the *spelled* path before resolution (including Windows junctions)."""
    raw = Path(os.path.abspath(value))
    for part in (raw, *raw.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ContractError('ERROR', 'UNSAFE_PATH', f'路径组件无法验证：{type(exc).__name__}') from exc
        if (stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)
                or (hasattr(part, 'is_junction') and part.is_junction())):
            raise ContractError('ERROR', 'UNSAFE_PATH', '原始路径包含链接或 Windows 重解析组件；请使用真实授权路径。')
    try:
        resolved = raw.resolve(strict=False)
        if root is not None and not resolved.is_relative_to(root):
            raise ContractError('ERROR', 'UNSAFE_PATH', '路径位于授权根之外。')
    except (OSError, RuntimeError) as exc:
        raise ContractError('ERROR', 'UNSAFE_PATH', f'无法验证实际路径：{type(exc).__name__}') from exc
    if resolved != raw:
        raise ContractError('ERROR', 'UNSAFE_PATH', '路径重解析结果与原始路径不一致。')
    return resolved


def run(original: str | None, returned: str | None, output_dir: str | None = None,
        focus_topics: list[str] | None = None, draft_message: bool = False,
        contract_name: str = '合同', authorized_root: str | None = None) -> dict:
    if not original or not returned:
        raise ContractError('NEEDS_INPUT', 'ROLE_AMBIGUOUS', '请明确哪份是发出稿 original、哪份是回传稿 returned。')
    root = checked_path(authorized_root) if authorized_root else None
    a, b = checked_path(original, root), checked_path(returned, root)
    target = checked_path(output_dir or 'outputs', root)
    if a == b or (a.exists() and b.exists() and os.path.samefile(a, b)):
        raise ContractError('NEEDS_INPUT', 'ROLE_AMBIGUOUS', '原稿和回传稿不能是同一文件对象；两份独立相同文件可以。')
    focus = focus_topics or []
    if any(x not in TOPICS for x in focus):
        raise ContractError('NEEDS_INPUT', 'ROLE_AMBIGUOUS', '主题不明确；请从付款、金额、交付、验收、服务范围、期限、其他中选择。')
    if target.exists() and not target.is_dir():
        raise ContractError('ERROR', 'IO_FAILURE', '输出位置不是目录。')
    before = {'original': digest(a) if a.is_file() else '', 'returned': digest(b) if b.is_file() else ''}
    au, aw = read_docx(a); bu, bw = read_docx(b)
    changes, uncertain = compare(au, bu)
    checked_path(original, root); checked_path(returned, root)
    if not target.exists():
        try:
            target.mkdir(parents=True)
        except OSError as exc:
            raise ContractError('ERROR', 'IO_FAILURE', f'不能创建输出目录：{type(exc).__name__}') from exc
    checked_path(str(target), root)
    result = outputs(a, b, changes, aw + bw + uncertain, target,
                     contract_name, focus, draft_message, before, root)
    if {k: digest(p) for k, p in [('original', a), ('returned', b)]} != before:
        for key in ('xlsx', 'docx'):
            Path(result[key]).unlink(missing_ok=True)
        raise ContractError('ERROR', 'IO_FAILURE', '源文件运行期间发生变化；请重新比较。')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description='Explicit-direction DOCX return comparison; local files only')
    parser.add_argument('--original')
    parser.add_argument('--returned')
    parser.add_argument('--output-dir')
    parser.add_argument('--authorized-root', help='受控/明确授权的共同目录；三条路径均须在其下')
    parser.add_argument('--focus-topics', nargs='*', default=[])
    parser.add_argument('--draft-message', action='store_true')
    parser.add_argument('--contract-name', default='合同')
    args = parser.parse_args()
    try:
        result = run(args.original, args.returned, args.output_dir, args.focus_topics, args.draft_message, args.contract_name, args.authorized_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ContractError as exc:
        print(json.dumps({'status': exc.status, 'reason': exc.reason, 'message': exc.message}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
