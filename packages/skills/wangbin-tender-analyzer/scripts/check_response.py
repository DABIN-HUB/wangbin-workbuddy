#!/usr/bin/env python3
"""Local, source-scoped bid response comparison; never authenticates qualifications."""
from __future__ import annotations

import argparse
import csv
import importlib.util
from datetime import date
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
MATERIAL = re.compile(r'[\w\u4e00-\u9fff.-]+\.(?:txt|md)\b', re.I)
WORD = re.compile(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}|\d+(?:\.\d+)?')


def material_names(text: str) -> list[str]:
    """Extract file basenames without swallowing adjacent Chinese instructions."""
    names = []
    for match in MATERIAL.finditer(text):
        name = re.split(r'必须|提交|提供|参见|见|附|须|应', match.group())[-1]
        if name and name not in names:
            names.append(name)
    return names


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


DATE = re.compile(r'(?<!\d)(\d{4})[-年/.](\d{1,2})[-月/.](\d{1,2})日?')
YEAR = re.compile(r'(?<!\d)(\d{4})年')
DUTY = re.compile(r'营业执照|(?:甲类|乙类|[\u4e00-\u9fff]{1,8})?(?:资质证明|资格证明|证书|证明材料)|报价函|承诺函')
NEGATIVE_EVIDENCE = re.compile(
    r'尚?未(?:取得|颁发|签发|核发)|(?:正在|尚在|仍在|拟|待)(?:办理|申请)|'
    r'仅为目录占位|(?:示例|样例|模板|测试)(?:用)?占位|'
    r'(?:仅(?:作为|供|为|用于)?(?:示意|展示|演示)|不(?:包含|含|提供)任何?(?:证照|证书|证明|执照)(?:的)?(?:正文|内容)?)|'
    r'并非(?:真正|实际)?(?:的)?(?:资质|证书|证明|执照)|'
    r'不含(?:证照|证书|证明|执照)|不是(?:真正)?(?:[甲乙丙丁\w]{0,8})?(?:资质|证书|证明|执照)|未取得')


def dated(text: str) -> list[tuple[date, int, int]]:
    found = []
    for match in DATE.finditer(text):
        try:
            found.append((date(*map(int, match.groups())), match.start(), match.end()))
        except ValueError:
            continue
    return found


def target_dates(text: str):
    dates = dated(text)
    if len(dates) >= 2 and re.search(r'覆盖|有效期|有效覆盖', text):
        return dates[0][0], dates[1][0], True
    if len(dates) == 1 and re.search(r'覆盖|有效期', text):
        return dates[0][0], dates[0][0], True
    if re.search(r'覆盖|有效期', text) and YEAR.search(text):
        # An unqualified year does not define whether the entire calendar year is intended.
        return None, None, False
    return None, None, True


def certificate_dates(text: str):
    dates = dated(text)
    effective = expiry = None
    for value, start, end in dates:
        before = text[max(0, start-5):start]
        after = text[end:end+5]
        if re.search(r'签发|颁发', before):
            continue
        if re.search(r'截止|失效|到期|至|期满', before) or re.search(r'失效|到期|截止', after):
            expiry = value
        elif re.search(r'生效|起始|起止|自|从', before) or re.search(r'起|生效', after):
            effective = value
    if len(dates) >= 2 and re.search(r'有效期', text) and re.search(r'至|到|—|~', text):
        nonissue = [d[0] for d in dates if not re.search(r'签发|颁发', text[max(0, d[1]-8):d[1]])]
        if len(nonissue) >= 2:
            effective = effective or nonissue[0]
            expiry = expiry or nonissue[-1]
    return effective, expiry


def object_name(text: str) -> str | None:
    match = re.search(r'([甲乙丙丁戊己庚辛壬癸ABC]类)(?=资质|证明|证书)', text)
    return match.group(1) if match else None


def action_fact(text: str, term: str) -> tuple[int, str] | None:
    """Bind polarity and current availability to the requested action and object.

    A mention of the object in a design document is not an assertion that the
    requested *function* works. Evaluate one clause at a time; unrelated clauses
    cannot donate their positive verb to a negative capability statement.
    """
    action = re.search(r'(不)?(支持|使用|提供|具备)([\u4e00-\u9fff\w/]+)', term)
    if not action:
        return None
    _, verb, obj = action.groups()
    stem = obj[:min(len(obj), 4)]
    clauses = re.split(r'[，。；,;]', text)
    for index, clause in enumerate(clauses):
        if stem not in clause:
            continue
        # Status predicates describe the requested object even without a
        # repeated verb ("自动备份尚未启用", "对自动备份，目前做不到").
        # Inspect the next clause only if it explicitly refers back to this
        # capability; a different object's status cannot negate this one.
        context = clause
        if index + 1 < len(clauses):
            following = clauses[index + 1]
            if (re.search(r'该(?:功能|能力|服务)|此(?:功能|能力)|' + re.escape(stem), following)
                    or (re.search(r'^(?:我们|我方|目前|当前)', following.strip())
                        and not re.search(r'[^\s，,。；;]{2,}(?:功能|查询|备份|存储)', following))):
                context += '，' + following
        if re.search(r'做不到|(?:无法|不能|不可)(?:实现|交付|做到|提供|使用)|尚?未具备(?:该|此)?(?:项)?能力|不具备(?:该|此)?(?:项)?能力|(?:功能|服务|能力).{0,8}(?:尚?未启用|尚?未上线|未投产|尚?未实现|尚?未开发|不可用|无法使用)|(?:尚?未启用|尚?未上线|未投产|尚?未实现|尚?未开发|尚?未投入使用|还未投入使用|未投入使用|尚无法提供|尚不能提供)', context):
            return -1, '当前不具备或尚未启用所需功能'
        if re.search(r'仅(?:处于|在).{0,12}(?:设计|规划|研发)(?:阶段)?|仅(?:提供|有).{0,20}(?:设计|文档|方案)|(?:已纳入|列入|计划|拟于|将在).{0,16}(?:后续|未来|研发|计划|上线|开发)', context):
            return -1, '仅有设计材料或仍在规划'
        # A document about X is not X itself. Restrict the object to the
        # requested verb's own phrase rather than searching anywhere nearby.
        hit = re.search(r'(无法|不能|不可|未能|不|未|无)?' + verb +
                        r'([^，。；,;]{0,20})', clause)
        if hit and stem in hit.group(2):
            return (-1 if hit.group(1) else 1, '明确肯否')
        if re.search(r'(无法|不能|不可|未能|不|未|无)(?:实际)?' + verb +
                     r'[^，。；,;]{0,20}' + re.escape(stem), clause):
            return -1, '明确肯否'
        # Status/limitations apply to the same object, even if the sentence
        # only offers a design or promises a future implementation.
        if re.search(r'未上线|未投产|尚未实现|尚未开发|未实现|无法使用|不能使用|暂不支持', clause):
            return -1, '功能未实现或仅有设计材料'
    return None


def polarity(text: str, term: str) -> int | None:
    fact = action_fact(text, term)
    return fact[0] if fact else None


def response_conflict(condition: str, reply: str) -> str | None:
    target = polarity(condition, condition)
    fact = action_fact(reply, condition)
    actual = fact[0] if fact else None
    if target is not None and actual is not None and target != actual:
        return '回应' + fact[1] + '与招标义务冲突'
    if re.search(r'若|只有|才支持|方可|另行购买|拟于|尚未实现|交付后|仅提供|只提供|未上线|未投产', reply) and re.search(r'必须|须|应', condition):
        return '回应附带前提或尚未实现，不能证明无条件义务'
    return None


def uncertain_capability(condition: str, reply: str) -> bool:
    """An undecided rollout is neither an operational claim nor a denial."""
    if not re.search(r'支持|使用|具备', condition) or not reply:
        return False
    return bool(re.search(r'正在评估是否|尚待确定|具体时间待定|预计.{0,12}(?:交付|上线).{0,12}(?:待定|未定)', reply))


def covered(condition: str, reply: str) -> bool:
    if not reply or response_conflict(condition, reply) or uncertain_capability(condition, reply):
        return False
    expected, actual = polarity(condition, condition), polarity(reply, condition)
    if expected is not None and actual == expected:
        return True
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
                         'conditions': conditions(line), 'materials': material_names(line),
                         'duty': DUTY.findall(MATERIAL.sub(' ', line)) if re.search(r'须|必须|应|附|提供', line) else [],
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


def material_assessment(requirement: dict, present: list[tuple[str, str]]):
    target_start, target_end, target_known = target_dates(requirement['raw'])
    cert_object = object_name(requirement['raw'])
    evidence_lines = [(name, i, line) for name, text in present
                      for i, line in enumerate(text.splitlines(), 1) if line.strip()]
    if cert_object:
        relevant = [(name, i, line) for name, i, line in evidence_lines if cert_object in line]
        if not relevant:
            return '待确认', '材料未明确对应' + cert_object + '，不得借其他对象的期限判断', []
    else:
        relevant = evidence_lines
    if not relevant:
        return '待确认', '实际材料无可读正文，须人工确认', []
    locations = [loc(name, i) for name, i, _ in relevant][:12]
    for name, i, line in relevant:
        if NEGATIVE_EVIDENCE.search(line):
            return '不支持（文本层面）', f'材料 {loc(name, i)} 明确否认已具备要求的证件/证明正文：{quote(line)}；可读文件不等于已颁发证件', locations
    if target_start or target_end or not target_known:
        if not target_known:
            year_match = YEAR.search(requirement['raw'])
            if year_match is None:
                return '待确认', '目标年份边界或要求来源未明确', locations
            year = int(year_match.group(1))
            for name, i, line in relevant:
                _, end = certificate_dates(line)
                if end and end < date(year, 1, 1):
                    return '不支持（文本层面）', f'材料 {loc(name, i)} 截止 {end} 早于要求年份 {year}，即使年份边界未明也不能覆盖', locations
            return '待确认', '招标年份未明示全年边界，须确认目标起止日', locations
        # Each line belongs to a single certificate. Never borrow endpoints from
        # another certificate or use issue date as its effective date.
        uncertain = []
        for name, i, line in relevant:
            start, end = certificate_dates(line)
            if end and target_end and end < target_end:
                return '不支持（文本层面）', f'材料 {loc(name, i)} 有效截止 {end} 早于要求 {target_end}', locations
            if start and target_start and start > target_start:
                return '不支持（文本层面）', f'材料 {loc(name, i)} 生效 {start} 晚于要求 {target_start}', locations
            if start and end and target_start and target_end and start <= target_start <= target_end <= end:
                return '支持（文本层面）', f'材料 {loc(name, i)} 有效区间 {start} 至 {end} 覆盖目标 {target_start} 至 {target_end}（仅文本）', locations
            uncertain.append(f'{loc(name, i)} 缺有效起止或期限；签发日期不可作为生效日期')
        return '待确认', '；'.join(uncertain), locations
    if re.search(r'营业执照', requirement['raw']) and any('营业执照' in line for _, _, line in relevant):
        return '支持（文本层面）', '材料正文包含所要求营业执照文本，不认证真实有效', locations
    if cert_object and any(cert_object in line and re.search(r'证明文本|证明材料|资质证明', line) and '有效' in line for _, _, line in relevant):
        return '支持（文本层面）', f'材料仅包含{cert_object}证明文本及有效声明，不认证真实性或期限', locations
    if any(any(t in line for t in tokens(requirement['raw'])) for _, _, line in relevant):
        return '待确认', '材料提及相近对象，但缺完整可核对声明', locations
    return '待确认', '材料内容未明确关联要求，须人工确认', locations


def explicit_material_match(requirement: dict, filename: str, text: str) -> bool:
    """Bind a submitted unnamed material to its specific duty, never to a peer.

    Only an explicit object in the filename AND corresponding body may anchor
    a filename-free obligation. Generic documents remain candidates, not proof.
    """
    obj = object_name(requirement['raw'])
    if obj:
        return filename.startswith(obj + '.') and any(obj in line for line in text.splitlines())
    return any(duty in filename and duty in text for duty in requirement['duty'])


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
        for material in material_names(line):
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
        # Retain advisory candidates unless their number belongs to another
        # requirement; a peer's response is not this requirement's provenance.
        positions = [loc(response_name or '', n) for n, line, _ in candidates
                     if number(line) == r['number'] or number(line) not in numbered]
        reply = selected[1] if selected else ''
        cond = r['conditions']
        uncovered = [p for p in cond if not covered(p, reply)] if selected else cond
        existence = '未核查' if response is None else '已定位' if unique else '候选待确认' if ambiguous else '未找到（限已提供响应）'
        condition_state = '未核查' if response is None else '待确认' if ambiguous else '可能不充分' if not unique or uncovered else '已覆盖（文本层面）'
        materials = r['materials'][:]
        # A response-only reference is usable only with an unambiguous numbered
        # reply and an explicit material requirement. Never scan arbitrary files.
        response_only = [name for name in material_names(reply) if name not in materials]
        if unique and (r['duty'] or re.search(r'附件|证明|证书|材料|资质', r['raw'])):
            materials += response_only
        # The tender's exact filename and a uniquely numbered response supply
        # the attribution even without a catalog; they do not certify its text.
        if unique and r['materials']:
            materials += [name for name, _ in evidence if name in r['materials'] and name not in materials]
        listed = [c for c in catalog if c['name'] in materials or
                  (r['number'] and numbered[r['number']] == 1 and c['number'] == r['number'])]
        if r['duty'] and not materials and not listed:
            anchored = [name for name, text in evidence if explicit_material_match(r, name, text)]
            if len(anchored) == 1:
                materials.append(anchored[0])
            elif len(evidence) == 1 and len(reqs) == 1:
                # For a sole unnamed duty, inspect the sole explicitly
                # submitted candidate's text instead of claiming it is absent.
                materials.append(evidence[0][0])
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
            conflicting.update(material_names(' '.join(line for _, line, _ in candidates)))
        present = [(name, txt) for name, txt in evidence if name in names and name not in conflicting]
        assessment_reason = ''
        evidence_loc = []
        if conflicting:
            attachment, support = '待确认', '待确认'
        elif not names and not r['duty']:
            attachment, support = '不适用', '不适用'
        elif present:
            attachment = '已提供（可读文本）'
            support, assessment_reason, evidence_loc = material_assessment(r, present)
        elif listed:
            attachment, support = '仅目录登记', '未核验'
        elif r['duty'] or materials:
            attachment, support = '未提供（限已提供材料）', '未核验'
        else:
            attachment, support = '待确认', '未核验'
        if not evidence_loc and present:
            evidence_loc = [loc(name, i) for name, txt in present for i, line in enumerate(txt.splitlines(), 1) if line.strip()][:12]
        # A duty to submit evidence is separate from a claim to possess it.
        # Without actual material, the submission condition cannot be covered.
        if r['duty'] and attachment in ('未提供（限已提供材料）', '仅目录登记') and unique:
            condition_state = '可能不充分'
        if support == '不支持（文本层面）' and unique:
            condition_state = '可能不充分'
        required_object = object_name(r['raw'])
        explicit_submission = (bool(r['duty']) and required_object is not None and
                               required_object in reply and
                               bool(re.search(r'已提交|已提供|已附|提交|提供', reply)) and
                               not target_dates(r['raw'])[0])
        if support == '支持（文本层面）' and unique and (not uncovered or
                explicit_submission or
                (target_dates(r['raw'])[0] and '覆盖' in reply and
                 (object_name(r['raw']) is None or (object_name(r['raw']) or '') in reply))):
            uncovered = []
            condition_state = '已覆盖（文本层面）'
        if assessment_reason and support == '待确认' and unique:
            condition_state = '待确认'
        if unique and any(uncertain_capability(p, reply) for p in cond) and not r['duty']:
            condition_state = '待确认'
        gaps = []
        if existence == '未找到（限已提供响应）':
            gaps.append('在已提供响应中未找到')
        if condition_state == '可能不充分':
            conflicts = [response_conflict(p, reply) for p in cond if reply]
            explanation = '；'.join(x for x in conflicts if x)
            gaps.append('明确条件未获得完整文本支持：' + ('、'.join(quote(p) for p in uncovered) or quote(r['raw'])) + (f'；{explanation}' if explanation else ''))
        if attachment == '未提供（限已提供材料）':
            gaps.append('要求 ' + '、'.join(map(quote, r['duty'] or materials)) + '；在已提供材料中未找到实际文件，需补交或明确关联')
        if attachment == '仅目录登记':
            gaps.append('附件仅目录登记，需补实际材料并核内容')
        if support == '不支持（文本层面）':
            gaps.append(assessment_reason + '；需补正或人工核验')
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
        if unique and any(uncertain_capability(p, reply) for p in cond):
            pending.append('功能当前可用性或交付时点尚未确定，须核实该要求与响应原句')
        if conflicting:
            pending.append('材料候选重复、编号冲突或响应配对歧义；逐一核对文件与要求关联')
        elif attachment == '待确认' and (materials or r['duty']):
            pending.append('材料关联冲突或给定材料范围不完整，需核对要求 ' + '、'.join(r['duty'] or materials))
        if assessment_reason and support == '待确认':
            pending.append(assessment_reason)
        elif support == '待确认' and not conflicting:
            pending.append('材料文本关联不足或真实性需人工确认')
        results.append({**r, 'locations': positions, 'response': quote(reply) if reply else '',
                        'existence': existence, 'coverage': condition_state, 'attachment': attachment,
                        'support': support, 'listed': listed, 'present': present, 'conflicting': sorted(conflicting),
                        'evidence_locations': evidence_loc, 'gaps': gaps, 'pending': pending,
                        'assessment_reason': assessment_reason})
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
                       '；'.join(r['locations']), r['response'], '；'.join(r['materials'] or r['duty']), '；'.join(r['evidence_locations']),
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
        if r['duty'] and not r['listed'] and not r['present'] and not r['conflicting']:
            attachments.append([r['id'], '；'.join(r['duty']), '', '', r['attachment'], r['support'], '',
                                '要求 ' + r['source'] + '；仅限已提供材料，正文未核验'])
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
                              ('已覆盖范围（仅文本层面）', lambda r: [r['existence']] if r['existence'] == '已定位' and r['coverage'] == '已覆盖（文本层面）' and not r['gaps'] and r['attachment'] in ('不适用', '已提供（可读文本）') and r['support'] in ('不适用', '支持（文本层面）') else []),
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
