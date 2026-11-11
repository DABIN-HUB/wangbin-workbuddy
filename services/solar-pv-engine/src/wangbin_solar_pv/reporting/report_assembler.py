"""Partial review DOCX from a validated host result, preserving existing styles."""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import os

from docx import Document

from ..errors import ContractError
from ..report_equations import convert_equations
from .compat import add_table as _add_table
from ..report_numbering import add_numbered_heading, heading_number
from ..report_word_styles import configure, equation_paragraph
from ..serialization import digest
from .chapter_writer import resume
from .claim_validator import render_text


def assemble_chapter(store, request_id, model, registry, config, output_name):
    accepted, pack = resume(store, request_id, model, registry, config)
    target = store.path(output_name, json_only=False)
    if target.suffix.lower() != '.docx':
        raise ContractError('CHAPTER_DOCX_REQUIRED')
    if target.exists() or store.path(target.name + '.json').exists():
        raise ContractError('OUTPUT_EXISTS')
    chapter = registry.chapter(accepted['chapter_id'])
    output = accepted['output']
    used_formulas = {fid for sec in output['sections'] for fid in sec['formula_refs']}
    math = convert_equations(list(model.catalog.formulas.values())) if used_formulas else {}
    document = Document()
    configure(document)
    document.core_properties.title = chapter['chapter_title'] + '（局部待审稿）'
    document.core_properties.subject = '项目资料性质与专业结论须复核；非完整预可研报告'
    document.core_properties.comments = digest(accepted)
    document.sections[0].header.paragraphs[0].text = '光伏预可研 · 局部待审稿'
    document.sections[0].header.paragraphs[0].style = 'Solar Header'
    add_numbered_heading(document, heading_number(chapter['chapter_id'], chapter['chapter_title']), 1)
    document.add_paragraph(render_text(output['chapter_intro'], pack))
    for ordinal, (section, rule) in enumerate(zip(output['sections'], chapter['sections']), start=2):
        add_numbered_heading(document, heading_number(rule['section_id'], rule['section_title'],
                             parent_stable_id=chapter['chapter_id'], parent_level=1), ordinal)
        for text in [*section['paragraphs'], section['decision_impact']]:
            document.add_paragraph(render_text(text, pack))
        for tid in section['table_refs']:
            table = pack['tables'][tid]
            definition = table['definition']
            rows = []
            for fid in table['fact_ids'] if definition['renderer'] == 'evidence_rows' else []:
                fact = pack['facts'][fid]
                row = {'label': fact['label'], 'value': fact['display'], 'unit': fact.get('display_unit', fact['unit']) or '—',
                       'status': {'CALCULATED': '已计算，来源性质另核', 'ASSUMED': '登记假设',
                                  'VERIFIED': '输入已核验', 'NOT_APPLICABLE': '不适用'}.get(fact['status'], '尚无可用结果')}
                rows.append([row[col['key']] for col in definition['columns']])
            if definition['renderer'] != 'evidence_rows':
                rows = [[row['cells'][col['key']] for col in definition['columns']] for row in table['rows']]
            if not rows:
                rows = [['暂无获授权的可用结果；不填零'] + ['待核验'] * (len(definition['columns']) - 1)]
            _add_table(document, [c['title'] for c in definition['columns']], rows,
                       caption=definition['purpose'])
        for fid in section['formula_refs']:
            definition = pack['formulas'][fid]
            document.add_paragraph(definition['chinese_name'], style='Solar Formula Title')
            equation_paragraph(document, deepcopy(math[fid]), fid)
        for text in section['missing_evidence']:
            document.add_paragraph(render_text(text, pack))
    for text in [*output['chapter_findings'], *output['decision_implications']]:
        document.add_paragraph(render_text(text, pack))
    document.add_paragraph('本报告内容仅供参考，正式使用时需根据实际情况调整。')
    payload = BytesIO()
    document.save(payload)
    data = payload.getvalue()
    with target.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    receipt = {'artifact': target.name, 'sha256': sha256(data).hexdigest(), 'bytes': len(data),
               'identity': model.identity, 'generation_run_id': accepted['generation_run_id'],
               'chapter_output_hash': accepted['chapter_output_hash'], 'evidence_hash': pack['evidence_hash'],
               'spec_hash': registry.hash, 'scope': 'PARTIAL_CHAPTER_REVIEW_ONLY',
               'professional_review': 'PENDING_REVIEW', 'visual_review': 'NOT_TESTED',
               'llm_integration': accepted['llm_integration'], 'four_files': 'NOT_GENERATED'}
    store.create(target.name + '.json', receipt)
    return receipt
