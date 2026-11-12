"""Deterministic identity/reference checks, not a professional semantic verdict."""
import re

from ..errors import ContractError
from ..serialization import digest
from .chapter_result_schema import validate_schema
from .evidence_pack_builder import safe_text
from .reader_display import inline

SLOT = re.compile(r'\[\[fact:([^\[\]\s]+)\]\]')
TERM = re.compile(r'\[\[term:([^\[\]\s]+)\]\]')
FORBIDDEN = re.compile(r'<[^>]+>|(?:https?|file)://|```|[\x00-\x08\x0b\x0c\x0e-\x1f]')
REF_KEYS = ('metric_refs', 'formula_refs', 'table_refs', 'figure_refs', 'claim_ids', 'fact_refs', 'source_refs')


def check_text(text, allowed, terms=()):
    safe_text(text)
    refs = SLOT.findall(text)
    if set(refs) - set(allowed):
        raise ContractError('CHAPTER_FACT_REFERENCE')
    if set(TERM.findall(text)) - set(terms):
        raise ContractError('CHAPTER_TERM_REFERENCE')
    remainder = TERM.sub('', SLOT.sub('', text))
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
    if output['chapter_id'] in {'CH01', 'CH18'} and output['decision_state'] != 'DEFER':
        raise ContractError('CHAPTER_DECISION_REQUIRES_REVIEW')
    global_texts = [output['chapter_intro'], *output['chapter_findings'], *output['decision_implications']]
    used = set()
    for text in global_texts:
        used |= check_text(text, pack['facts'], pack['terms'])
    for sec in output['sections']:
        scope = pack['sections'][sec['section_id']]
        for key in REF_KEYS:
            if set(sec[key]) - set(scope[key]):
                raise ContractError('CHAPTER_SCOPED_REFERENCE', key)
        if set(sec['table_refs']) != set(scope['table_refs']):
            raise ContractError('CHAPTER_REQUIRED_TABLE_MISSING')
        if not sec['claim_ids']:
            raise ContractError('CHAPTER_CLAIM_REQUIRED')
        claims = sec['claims']
        if [c['claim_id'] for c in claims] != sec['claim_ids']:
            raise ContractError('CHAPTER_CLAIM_IDENTITY')
        covered = set()
        for claim in claims:
            refs = set(claim['fact_refs'])
            if refs - set(sec['fact_refs']) or set(claim['source_refs']) - set(sec['source_refs']):
                raise ContractError('CHAPTER_CLAIM_LINEAGE')
            if {s for f in refs for s in pack['facts'][f]['source_ids']} - set(claim['source_refs']):
                raise ContractError('CHAPTER_CLAIM_LINEAGE')
            if claim['kind'] in {'INPUT_FACT', 'CALCULATED_METRIC'}:
                kinds = {'input'} if claim['kind'] == 'INPUT_FACT' else {'metric', 'ledger'}
                if not refs or any(pack['facts'][f]['kind'] not in kinds for f in refs):
                    raise ContractError('CHAPTER_CLAIM_BASIS')
                if claim['kind'] == 'CALCULATED_METRIC' and any(pack['facts'][f]['status'] != 'CALCULATED' for f in refs):
                    raise ContractError('CHAPTER_CLAIM_BASIS')
            if claim['kind'] in {'CONDITIONAL_JUDGMENT', 'RECOMMENDATION'} and not claim['conditions']:
                raise ContractError('CHAPTER_CLAIM_CONDITIONS')
            # No engineering/target pass or causal benefit is established by a legal reference alone.
            if claim['effect'] != 'DESCRIPTIVE':
                raise ContractError('CHAPTER_CLAIM_DETERMINATION_NOT_VERIFIED')
            if claim['basis_status'] == 'SUPPORTED' and (not refs or any(pack['facts'][f]['status'] not in {'CALCULATED', 'VERIFIED'} for f in refs)):
                raise ContractError('CHAPTER_CLAIM_SUPPORT_STATE')
            if check_text(claim['text'], refs, pack['terms']) - refs:
                raise ContractError('CHAPTER_CLAIM_LINEAGE')
            for condition in claim['conditions']:
                check_text(condition, refs, pack['terms'])
            if any(i >= len(sec['paragraphs']) for i in claim['paragraph_indexes']):
                raise ContractError('CHAPTER_CLAIM_PARAGRAPH')
            for i in claim['paragraph_indexes']:
                if set(SLOT.findall(sec['paragraphs'][i])) - refs:
                    raise ContractError('CHAPTER_CLAIM_PARAGRAPH_LINEAGE')
            covered.update(claim['paragraph_indexes'])
        if covered != set(range(len(sec['paragraphs']))):
            raise ContractError('CHAPTER_CLAIM_COVERAGE')
        scoped_used = set()
        for text in [*sec['paragraphs'], sec['decision_impact'], *sec['missing_evidence']]:
            scoped_used |= check_text(text, scope['fact_refs'], pack['terms'])
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
    check_text(text, pack['facts'], pack['terms'])
    def replace(match):
        fact = pack['facts'][match.group(1)]
        # A single controlled formatter owns both body and table presentation.
        return inline(fact)
    return SLOT.sub(replace, TERM.sub(lambda match: pack['terms'][match.group(1)], text))
