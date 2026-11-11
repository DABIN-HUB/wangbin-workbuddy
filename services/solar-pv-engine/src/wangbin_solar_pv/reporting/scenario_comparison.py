"""Verify actual scenario producer receipts before any candidate comparison."""
from copy import deepcopy

from ..calculation.scenario_runner import prepare_scenario, seal_scenario_run, PreparedScenario
from ..errors import ContractError
from ..calculation.input_contract import validate_export
from ..serialization import digest
from .compat import ReportModel

RETURN_METRICS = {'npv': 'financial.phase3e.project_npv', 'irr': 'financial.phase3e.project_irr',
                  'static_payback': 'financial.phase3e.static_payback',
                  'dynamic_payback': 'financial.phase3e.dynamic_payback'}


def _basis(model):
    n = model.result['inputs']['normalized']
    return {k: deepcopy(n.get(k)) for k in ('project.currency', 'project.price_basis',
            'project.cashflow_tax_basis', 'project.evaluation_date', 'project.evaluation_years',
            'finance.project_discount_rate', 'finance.cashflow_timing', 'system.capacity_boundary')}


def _row(model, scenario_id, control=None):
    metrics = {key: deepcopy(model.metric(mid)) for key, mid in RETURN_METRICS.items()}
    cash = model.metric('financial.phase3e.project_cash_flow')
    first_cash = (cash['value'][0] if cash and cash['status'] == 'CALCULATED'
                  and isinstance(cash['value'], list) and cash['value'] else None)
    reasons = []
    for key, metric in metrics.items():
        if not metric or metric['status'] != 'CALCULATED':
            reasons.append(key + ': ' + (metric['reason'] or metric['status'] if metric else 'NO_PRODUCER'))
    if any(v is None for v in _basis(model).values()) or _basis(model).get('project.cashflow_tax_basis') != 'post_tax':
        reasons.append('POST_TAX_COMPARISON_BASIS_NOT_VERIFIED')
    irr = metrics['irr']
    if irr and (irr.get('details', {}).get('root_count') != 1 or irr.get('details', {}).get('unexhausted') is not False):
        reasons.append('IRR_ROOT_SET_NOT_UNIQUE_AND_CERTIFIED')
    return {'scenario_id': scenario_id, 'identity': model.identity, 'project_id': model.result['project_id'],
            'pv_type': model.result['pv_type'], 'metrics': metrics,
            'initial_project_net_cash': first_cash, 'capital_basis': '建设期原项目净现金流，不等于CAPEX总额',
            'source_ids': sorted({s for m in model.metrics for s in m['source_ids']}),
            'basis': _basis(model), 'control': deepcopy(control),
            'reasons': reasons, 'engineering_constraints': 'NOT_INDEPENDENTLY_VERIFIED',
            'status': 'METRICS_AVAILABLE_ENGINEERING_PENDING' if not reasons else 'NOT_COMPARABLE'}


def _source_semantics(value):
    # Intake timestamps and candidate IDs are newly authored by prepare_scenario.
    # Compare all values/provenance/permissions, but use the ORIGINAL validated
    # prepared export for sealing; never replace its hash with a regenerated one.
    if isinstance(value, dict):
        return {k: _source_semantics(v) for k, v in value.items() if k not in {'last_updated', 'candidate_ids'}}
    if isinstance(value, list):
        return [_source_semantics(v) for v in value]
    return value


def compare_scenarios(model, bundle=None):
    model = ReportModel.from_result(model.result, model.catalog)
    rows = [_row(model, 'BASE')]
    if bundle is not None:
        if not isinstance(bundle, dict) or set(bundle) != {'original_export', 'methods', 'entries'}:
            raise ContractError('SCENARIO_EVIDENCE_SHAPE')
        original = bundle['original_export']
        payload = model.result['inputs']['identity_payload']
        if (payload.get('phase2_input_hash') != original.get('input_hash')
                or payload.get('phase2_source_snapshot_id') != original.get('source_snapshot_id')):
            raise ContractError('SCENARIO_BASELINE_IDENTITY')
        entries = bundle['entries']
        if not isinstance(entries, list) or len(entries) > 8:
            raise ContractError('SCENARIO_COMPARISON_BUDGET')
        seen_runs, seen_results = set(), {model.result['result_hash']}
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {'control', 'prepared_export', 'results', 'receipt'}:
                raise ContractError('SCENARIO_EVIDENCE_SHAPE')
            prepared = prepare_scenario(entry['control'], original, bundle['methods'], model.catalog)
            actual = validate_export(entry['prepared_export'], model.catalog).export
            if (actual['normalized_inputs'] != prepared.input_export['normalized_inputs']
                    or _source_semantics(actual['source_snapshot']['records']) != _source_semantics(prepared.input_export['source_snapshot']['records'])
                    or actual['project']['project_id'] != original['project']['project_id']
                    or actual['project']['pv_type'] != original['project']['pv_type']):
                raise ContractError('SCENARIO_PREPARED_INPUT_DRIFT')
            prepared = PreparedScenario(prepared.scenario_id, prepared.run_id, actual, prepared.methods,
                                        prepared.original_input_hash, prepared.original_source_snapshot_id,
                                        prepared.scenario_hash, prepared.changed_field_ids, prepared.changed_method_ids)
            results, receipt = entry['results'], entry['receipt']
            if not {'3D', '3E'} <= results.keys():
                raise ContractError('SCENARIO_FINANCIAL_RESULTS_REQUIRED')
            sealed = seal_scenario_run(prepared, results, model.catalog)
            if (any(receipt.get(k) != v for k, v in sealed.items() if k != 'result_hash')
                    or receipt.get('result_hash') != digest({k: v for k, v in receipt.items() if k not in {'result_hash', 'elapsed_seconds'}})):
                raise ContractError('SCENARIO_RECEIPT_MISMATCH')
            candidate = ReportModel.from_result(results['3E'], model.catalog)
            if prepared.run_id in seen_runs or candidate.result['result_hash'] in seen_results:
                raise ContractError('SCENARIO_DUPLICATE_RUN')
            seen_runs.add(prepared.run_id)
            seen_results.add(candidate.result['result_hash'])
            if candidate.result['project_id'] != model.result['project_id'] or candidate.result['pv_type'] != model.result['pv_type']:
                raise ContractError('SCENARIO_PROJECT_TYPE_MISMATCH')
            row = _row(candidate, prepared.scenario_id, entry['control'])
            row['execution_run_id'] = prepared.run_id
            row['receipt_hash'] = receipt['result_hash']
            row['single_factor'] = len(entry['control']['changes']) == 1
            if row['basis'] != rows[0]['basis'] or any(v is None for v in row['basis'].values()):
                row['reasons'].append('COMPARISON_BASIS_INCOMPLETE_OR_DIFFERENT')
                row['status'] = 'NOT_COMPARABLE'
            rows.append(row)
    eligible = [r for r in rows if r['status'] == 'METRICS_AVAILABLE_ENGINEERING_PENDING']
    ranking = []
    if len(eligible) >= 2:
        ranking = [r['identity']['result_hash'] for r in sorted(eligible, key=lambda r: r['metrics']['npv']['value'], reverse=True)]
    output = {'schema_version': 'scenario-comparison/2.0', 'baseline_identity': model.identity,
              'rows': rows, 'ranking_by_same_basis_post_tax_npv': ranking,
              'status': 'CONDITIONAL_NUMERIC_COMPARISON_ONLY' if ranking else 'NO_VALID_MULTI_CANDIDATE_COMPARISON',
              'recommendation': 'NOT_ESTABLISHED', 'global_optimum': False,
              'limitations': ['只比较已执行同口径有效集合；工程、资金及风险须另核',
                              '单基准或候选缺NPV/IRR/回本不称收益优化完成',
                              '现有scenario_runner通用3E终期绑定未闭合时不借用基准NPV']}
    output['comparison_hash'] = digest(output)
    return output
