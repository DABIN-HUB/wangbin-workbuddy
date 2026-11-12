"""Reader display is typed, bounded and separate from canonical calculation."""
from copy import deepcopy
from decimal import Decimal

import pytest

from test_ai_report_engine import catalog, registry, model, protocol_fixture
from wangbin_solar_pv.reporting.reader_display import fact_display, inline, irr_text
from wangbin_solar_pv.reporting.evidence_pack_builder import build_pack, source_ids
from wangbin_solar_pv.report_equations import convert_equations
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.reporting.chapter_writer import prepare, accept
from wangbin_solar_pv.reporting.llm_provider import ModelConfig
from wangbin_solar_pv.reporting.report_assembler import assemble_chapter
from docx import Document


@pytest.mark.parametrize('value,unit,fid,expected', [
    (13, 'year', 'assets.replacements.year', '运营第13年'),
    (6, 'day', '', '6天'), (72000, 'currency', '', '72,000元'),
    (Decimal('157635.6498'), 'CNY', '', '157,636元'),
    (Decimal('0.075'), '1', 'finance.project_discount_rate', '7.50%'),
    (Decimal('1.2'), '1', 'system.dc_ac_ratio', '1.2'),
    (Decimal('0.98'), '1', 'grid.power_factor', '0.98'),
    (Decimal('0.012'), 'currency/kWh', '', '0.012元/kWh'),
    (0, 'currency', '', '0元'), (Decimal('-1234.5'), 'currency', '', '-1,235元'),
    ('2026-11-12', 'date', '', '2026年11月12日'),
    ('2026-02-30', 'date', '', '日期无效，待核验'),
    (None, 'currency', '', '尚无可用结果'),
    (Decimal('NaN'), 'currency', '', '尚无可用结果'),
    (Decimal('Infinity'), '1', '', '尚无可用结果'),
    (False, 'boolean', '', '否'),
])
def test_typed_display(value, unit, fid, expected):
    fact = {'value': value, 'unit': unit, 'field_id': fid, 'status': 'CALCULATED'}
    before = deepcopy(fact)
    text, display_unit = fact_display(fact, 'CNY')
    assert inline({**fact, 'display': text, 'display_unit': display_unit}) == expected
    assert str(fact) == str(before)


@pytest.mark.parametrize('status,text', [('BLOCKED_MISSING_INPUT', '尚无可用结果'),
                                        ('NOT_APPLICABLE', '不适用'), ('UNDEFINED', '当前条件下未定义')])
def test_nonvalue_never_renders_stale_zero(status, text):
    assert fact_display({'value': 0, 'unit': 'currency', 'status': status}, 'CNY') == (text, '')


@pytest.mark.parametrize('mid', ['pr_observed.year.1', 'capacity_factor.year.1'])
def test_metric_percent(mid):
    assert fact_display({'value': Decimal('0.8416'), 'unit': '1', 'metric_id': mid,
                         'status': 'CALCULATED'}) == ('84.16', '%')


def test_foreign_currency_not_relabelled_yuan():
    assert fact_display({'value': 12, 'unit': 'currency', 'status': 'CALCULATED'}, 'USD') == ('12', 'USD')


def test_certified_root_semantics():
    m = {'status': 'CALCULATED', 'value': Decimal('.2'), 'details': {'roots': [Decimal('.2')], 'root_count': 1, 'unexhausted': False, 'domain': {'minimum': -.9, 'maximum': 5}}}
    assert irr_text(m).startswith('20.00%')
    m['details']['unexhausted'] = True
    assert '完整性' in irr_text(m)
    m = {'status': 'UNDEFINED', 'reason': 'MULTIPLE_ROOTS', 'value': None,
         'details': {'roots': [Decimal('.1'), Decimal('.2')], 'root_count': 2, 'unexhausted': False, 'domain': {'minimum': -.9, 'maximum': 5}}}
    assert '根1≈10.00%、根2≈20.00%' in irr_text(m)
    m['details'].update(roots=[], root_count=0)
    m['reason'] = 'NO_ROOT'
    assert '检索范围内未找到' in irr_text(m)


def test_pack_display_does_not_change_value_or_identity(model, registry):
    before = deepcopy(model.result)
    pack = build_pack(model, registry, 'CH08', source_ids(model.result))
    f = pack['facts']['metric:pr_observed.year.1']
    assert f['value'] == model.metric('pr_observed.year.1')['value']
    assert f['display_unit'] == '%'
    assert model.result == before
    assert pack['identity'] == model.identity


def test_selected_formula_converter(catalog):
    result = convert_equations(list(catalog.formulas.values()), formula_ids={'F-NPV'})
    assert set(result) == {'F-NPV'}
    assert result['F-NPV'].xpath('.//*[local-name()="nary"]/*[local-name()="e"]')
    with pytest.raises(ContractError):
        convert_equations(list(catalog.formulas.values()), formula_ids={'invented'})


def test_formula_stays_in_its_section(tmp_path, model, registry):
    cfg = ModelConfig('protocol-fixture-only')
    req = prepare(Workspace(tmp_path), 'formula', model, registry, 'CH08', cfg, source_ids(model.result))
    output = protocol_fixture(req['evidence_pack'])
    output['sections'][1]['formula_refs'] = ['F-ENERGY-AGGREGATION']
    store = Workspace(tmp_path / 'formula')
    accept(store, req['request_id'], {'request_hash': req['request_hash'], 'model_id': cfg.model_id,
           'host_call_id': 'FORMULA_PROTOCOL_ONLY', 'output': output}, model, registry, cfg)
    receipt = assemble_chapter(store, req['request_id'], model, registry, cfg, 'formula.docx')
    doc = Document(store.root / receipt['artifact'])
    section, owners = None, []
    for p in doc.paragraphs:
        if p.style.name == 'Heading 2':
            section = p.text
        if p._p.xpath('.//m:oMath'):
            owners.append(section)
    assert len(owners) == 1 and '月度与首年电量' in owners[0]
    assert any('符号' in table.rows[0].cells[0].text for table in doc.tables)
    assert receipt['formula_sections']['CH08.02'] == ['F-ENERGY-AGGREGATION']
