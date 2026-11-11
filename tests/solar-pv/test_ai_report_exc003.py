"""A-class omissions remain inside frozen IDs and calculation boundaries."""
from test_ai_report_spec import SPEC


def test_conditional_table_contracts():
    sections = {s['section_id']: s for c in SPEC['chapters'] for s in c['sections']}
    targets = ['CH06.04', 'CH06.05', 'CH13.02', 'CH17.01', 'CH17.02', 'CH17.03', 'CH18.04']
    for sid in targets:
        table = sections[sid]['tables'][0]
        assert table['table_id'] == sid + '-T01'
        assert table['sort_rule'] and table['source_binding'] and table['applicability']
        assert len({c['key'] for c in table['columns']}) == len(table['columns'])
    for sid in ['CH06.04', 'CH06.05', 'CH17.01', 'CH17.02']:
        assert sections[sid]['scenario_bindings']['minimum_for_comparison'] == 2
        assert sections[sid]['tables'][0]['source_binding']['executed_bundle']
    assert sections['CH17.03']['metric_ids'] == ['financial.phase3e.break-even-price', 'financial.phase3e.investment-hurdle-gap']
    assert {c['key'] for c in sections['CH13.02']['tables'][0]['columns']} >= {'start', 'finish', 'duration', 'predecessors'}
    assert {c['key'] for c in sections['CH18.04']['tables'][0]['columns']} >= {'condition', 'materials', 'owner', 'completion'}


def test_financial_distinctions_and_no_scope_expansion():
    assert SPEC['prompt_version'] == '2.0.0-exc003'
    assert SPEC['report_spec_version'] == 'SOLAR-PV-AI-REPORT-ENGINE-2.0.0'
    sections = {s['section_id']: s for c in SPEC['chapters'] for s in c['sections']}
    for sid in ['CH16.02', 'CH16.03', 'CH16.04', 'CH16.05']:
        assert len(sections[sid]['analysis_tasks']) == 3
    assert len({s['research_objective'] for s in sections.values()}) == 100
