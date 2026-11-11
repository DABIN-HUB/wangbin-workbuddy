"""Financial distinctions and comparison rejection; no generated AI content."""
from copy import deepcopy
import pytest

from test_ai_report_engine import catalog, model
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import digest
from wangbin_solar_pv.reporting.financial_evaluation import evaluate_financial
from wangbin_solar_pv.reporting.scenario_comparison import compare_scenarios, _source_semantics


def test_six_boundaries_preserve_producers(model):
    before = digest(model.result)
    evaluation = evaluate_financial(model)
    values = evaluation['evaluations']
    assert set(values) == {'accounting_profit', 'operating_cash_positive', 'static_payback',
                           'dynamic_payback', 'project_return', 'shareholder_recovery'}
    for key in ('accounting_profit', 'operating_cash_positive', 'shareholder_recovery'):
        assert values[key]['status'] == 'NOT_CALCULABLE'
        assert values[key]['value'] is None and values[key]['reason']
    for key, mid in [('static_payback', 'financial.phase3e.static_payback'),
                     ('dynamic_payback', 'financial.phase3e.dynamic_payback'),
                     ('project_return', 'financial.phase3e.project_npv')]:
        assert values[key]['value'] == model.metric(mid)['value']
        assert values[key]['indicators'][0] == model.metric(mid)
    assert evaluation['investment_approval'] == 'NOT_ESTABLISHED'
    assert evaluation['project_positive_is_not_operating_cash_or_profit'] is True
    assert digest(model.result) == before
    assert evaluation['evaluation_hash'] == digest({k: v for k, v in evaluation.items() if k != 'evaluation_hash'})


def test_baseline_is_not_multi_candidate_optimization(model):
    comparison = compare_scenarios(model)
    assert len(comparison['rows']) == 1
    assert comparison['rows'][0]['identity'] == model.identity
    assert comparison['ranking_by_same_basis_post_tax_npv'] == []
    assert comparison['status'] == 'NO_VALID_MULTI_CANDIDATE_COMPARISON'
    assert comparison['global_optimum'] is False
    assert comparison['rows'][0]['initial_project_net_cash'] < 0


@pytest.mark.parametrize('bundle', [[], {}, {'entries': []}])
def test_unsealed_comparison_bundle_rejected(model, bundle):
    with pytest.raises(ContractError, match='SCENARIO_EVIDENCE_SHAPE'):
        compare_scenarios(model, bundle)


def test_wrong_baseline_identity_rejected(model):
    bundle = {'original_export': {'input_hash': 'wrong'}, 'methods': {}, 'entries': []}
    with pytest.raises(ContractError, match='SCENARIO_BASELINE_IDENTITY'):
        compare_scenarios(model, bundle)


def test_source_semantics_preserve_economics_and_permissions():
    record = {'value': 0, 'unit': 'currency', 'license_status': 'AUTHORIZED',
              'last_updated': 'old', 'candidate_ids': ['old-id']}
    dated = deepcopy(record)
    dated.update(last_updated='new', candidate_ids=['new-id'])
    assert _source_semantics(record) == _source_semantics(dated)
    for key, value in [('value', None), ('unit', 'year'), ('license_status', 'UNKNOWN')]:
        changed = deepcopy(dated)
        changed[key] = value
        assert _source_semantics(record) != _source_semantics(changed)
