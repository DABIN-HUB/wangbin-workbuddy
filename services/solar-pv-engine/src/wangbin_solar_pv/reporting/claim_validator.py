"""Deterministic identity/reference checks, not a professional semantic verdict."""
import re

from ..errors import ContractError
from ..serialization import digest
from .chapter_result_schema import validate_schema
from .evidence_pack_builder import safe_text

SLOT = re.compile(r'\[\[fact:([^\[\]\s]+)\]\]')
FORBIDDEN = re.compile(r'<[^>]+>|(?:https?|file)://|```|[\x00-\x08\x0b\x0c\x0e-\x1f]')
REF_KEYS = ('metric_refs', 'formula_refs', 'table_refs', 'figure_refs', 'claim_ids', 'fact_refs', 'source_refs')


def check_text(text, allowed):
    safe_text(text)
    refs = SLOT.findall(text)
    if set(refs) - set(allowed):
        raise ContractError('CHAPTER_FACT_REFERENCE')
    remainder = SLOT.sub('', text)
    if '[[' in remainder or ']]' in remainder or FORBIDDEN.search(remainder):
        raise ContractError('CHAPTER_UNSAFE_MARKUP')
    if any(ch.isdigit() for ch in remainder):
        raise ContractError('CHAPTER_UNBOUND_NUMBER')
    return set(refs)


def validate_chapter(output, pack, chapter):
    validate_schema(output)
    if pack.get('evidence_hash') != digest({k: v for k, v in pack.items() if k != 'evidence_hash'}):
        raise ContractError('EVIDENCE_HASH_MISMATCH')
    if output['chapter_id'] != pack['chapter_id'] or output['chapter_id'] != chapter['chapter_id']:
        raise ContractError('CHAPTER_IDENTITY')
    expected = [s['section_id'] for s in chapter['sections']]
    if [s['section_id'] for s in output['sections']] != expected:
        raise ContractError('CHAPTER_SECTION_COVERAGE')
    global_texts = [output['chapter_intro'], *output['chapter_findings'], *output['decision_implications']]
    used = set()
    for text in global_texts:
        used |= check_text(text, pack['facts'])
    for sec in output['sections']:
        scope = pack['sections'][sec['section_id']]
        for key in REF_KEYS:
            if set(sec[key]) - set(scope[key]):
                raise ContractError('CHAPTER_SCOPED_REFERENCE', key)
        if set(sec['table_refs']) != set(scope['table_refs']):
            raise ContractError('CHAPTER_REQUIRED_TABLE_MISSING')
        if not sec['claim_ids']:
            raise ContractError('CHAPTER_CLAIM_REQUIRED')
        scoped_used = set()
        for text in [*sec['paragraphs'], sec['decision_impact'], *sec['missing_evidence']]:
            scoped_used |= check_text(text, scope['fact_refs'])
        if scoped_used - set(sec['fact_refs']):
            raise ContractError('CHAPTER_UNDECLARED_FACT')
        used |= scoped_used
        sources = {sid for f in sec['fact_refs'] for sid in pack['facts'][f]['source_ids']}
        metrics = {pack['facts'][f]['metric_id'] for f in sec['fact_refs'] if pack['facts'][f]['kind'] == 'metric'}
        if sources - set(sec['source_refs']) or metrics - set(sec['metric_refs']):
            raise ContractError('CHAPTER_UNDECLARED_LINEAGE')
        if scope['missing_evidence'] and not sec['missing_evidence']:
            raise ContractError('CHAPTER_MISSING_EVIDENCE_HIDDEN')
        if scope['not_applicable_reason'] and not sec['missing_evidence']:
            raise ContractError('CHAPTER_APPLICABILITY_REASON_REQUIRED')
    # A chapter with usable facts must actually refer to project evidence.
    if pack['facts'] and not used:
        raise ContractError('CHAPTER_PROJECT_EVIDENCE_REQUIRED')
    paragraphs = [p for s in output['sections'] for p in s['paragraphs']]
    duplicates = sorted({p for p in paragraphs if paragraphs.count(p) > 1})
    return {'validation_status': 'STRUCTURE_AND_REFERENCES_VALID',
            'professional_review': 'PENDING_REVIEW', 'duplicate_paragraphs': duplicates,
            'chapter_output_hash': digest(output), 'evidence_hash': pack['evidence_hash'],
            'numerical_rule': 'BOUND_FACT_SLOTS_ONLY', 'semantic_gate': 'NOT_VERIFIED'}


def render_text(text, pack):
    check_text(text, pack['facts'])
    def replace(match):
        fact = pack['facts'][match.group(1)]
        # UNKNOWN/BLOCKED display never uses a numeric default.
        value = fact['display']
        unit = fact.get('display_unit', fact.get('unit'))
        return str(value) + (' ' + unit if unit and fact['value'] is not None else '')
    return SLOT.sub(replace, text)
