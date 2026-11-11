"""Full specification coverage, not a claim that model content is accepted."""
import hashlib
import json
from pathlib import Path

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.report_export import CHAPTERS, APPENDICES
from wangbin_solar_pv.report_claims import APPENDIX_TITLES

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / 'services/solar-pv-engine/src/wangbin_solar_pv/reporting/specs/report-spec.json'
SPEC = json.loads(SPEC_PATH.read_text(encoding='utf-8'))
SECTIONS = [(ch, sec) for ch in SPEC['chapters'] for sec in ch['sections']]


def test_full_identity_and_order():
    catalog = Catalog()
    assert [(c['chapter_id'], c['chapter_title'], tuple(s['section_title'] for s in c['sections']))
            for c in SPEC['chapters']] == list(CHAPTERS)
    assert [(a['appendix_id'], a['title']) for a in SPEC['appendices']] == list(APPENDICES)
    assert {s['section_id']: s['title'] for a in SPEC['appendices'] for s in a['sections']} == APPENDIX_TITLES
    assert len(SECTIONS) == 100
    assert (len(catalog.fields), len(catalog.formulas), len(catalog.bindings)) == (469, 89, 281)
    assert len({s['research_objective'] for _, s in SECTIONS}) == 100
    assert SPEC['generation_order'][-1] == 'CH01'
    seen = set()
    for cid in SPEC['generation_order']:
        chapter = next(ch for ch in SPEC['chapters'] if ch['chapter_id'] == cid)
        assert set(chapter['dependencies']) <= seen
        seen.add(cid)
    assert len(seen) == 18


@pytest.mark.parametrize('chapter,section', SECTIONS, ids=[s['section_id'] for _, s in SECTIONS])
def test_each_section_contract(chapter, section):
    catalog = Catalog()
    assert section['section_id'].startswith(chapter['chapter_id'] + '.')
    assert set(section['input_fields']) <= catalog.fields.keys()
    assert set(section['formula_ids']) <= catalog.formulas.keys()
    for key in ('research_objective', 'professional_questions', 'source_requirements',
                'analysis_tasks', 'professional_meaning', 'decision_contribution',
                'missing_evidence_behavior', 'not_applicable_behavior', 'output_acceptance'):
        assert section[key]
    for table in section['tables']:
        assert table['table_id'].startswith(section['section_id'])
        assert table['purpose'] and table['row_granularity'] and table['applicability']
        assert all({'key', 'title', 'unit'} <= col.keys() for col in table['columns'])
    assert set(section['project_type_fields']) == set(SPEC['project_types'])


def test_matrix_and_frozen_hashes():
    directory = ROOT / 'docs/solar-pv/ai-report-engine-v2'
    matrix = json.loads((directory / 'acceptance-matrix.json').read_text(encoding='utf-8'))
    expected = {s['section_id'] for _, s in SECTIONS} | set(APPENDIX_TITLES)
    assert len(matrix) == 126 and {r['section_id'] for r in matrix} == expected
    manifest = json.loads((directory / 'freeze-manifest.json').read_text(encoding='utf-8'))
    for path, expected_hash in manifest['files'].items():
        text = (ROOT / path).read_text(encoding='utf-8-sig').replace('\r\n', '\n')
        assert hashlib.sha256(text.encode('utf-8')).hexdigest() == expected_hash
