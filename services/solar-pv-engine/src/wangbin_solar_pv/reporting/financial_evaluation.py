"""Six distinct financial evaluations over validated canonical producer results.

This layer selects/explains existing results. It does not introduce accounting,
operating-cash or shareholder-recovery methods to fill an unavailable metric.
"""
from copy import deepcopy
from decimal import Decimal

from ..serialization import digest
from .compat import ReportModel, source_value

METRICS = {
    'static_payback': ('financial.phase3e.static_payback', 'financial.phase3e.cumulative_cash_flow'),
    'dynamic_payback': ('financial.phase3e.dynamic_payback', 'financial.phase3e.discounted_cumulative_cash'),
    'project_return': ('financial.phase3e.project_npv', 'financial.phase3e.project_irr'),
    'shareholder_recovery': ('financial.phase3e.equity-investor-cash-flow', 'financial.phase3e.irr-equity'),
}


def _indicator(model, mid):
    metric = model.metric(mid)
    if metric is None:
        return {'metric_id': mid, 'status': 'NOT_IMPLEMENTED', 'value': None,
                'reason': 'NO_VERIFIED_PRODUCER_IN_CANONICAL'}
    return deepcopy(metric)


def _target(model, fid):
    records = model.result['source_snapshot']['phase2']['records']
    value = source_value(model.result['inputs']['normalized'], records, fid)
    matches = [r for r in records if r.get('field_id') == fid]
    if value is None or len(matches) != 1 or matches[0].get('status') not in {'ASSUMED', 'VERIFIED'} or matches[0].get('license_status') != 'AUTHORIZED':
        return {'field_id': fid, 'status': 'TARGET_NOT_VERIFIED_OR_NOT_PROVIDED', 'value': None}
    record = matches[0]
    return {'field_id': fid, 'status': record['status'], 'value': value,
            'source_id': record['source_id'], 'field_instance_id': record['field_instance_id'],
            'location': record['source_section_or_cell']}


def evaluate_financial(model):
    model = ReportModel.from_result(model.result, model.catalog)
    result = model.result
    financial = result.get('evidence', {}).get('phase3e-financial', {})
    ledger = result.get('evidence', {}).get('financial-ledger', {})
    basis = {'currency': result['currency'], 'evaluation_date': result['evaluation_date'],
             'periods': deepcopy(financial.get('periods', ledger.get('periods', []))),
             'cash_flow_basis': financial.get('selected_basis'),
             'price_basis': result['inputs']['normalized'].get('project.price_basis'),
             'project_discount_rate': financial.get('project_discount_rate'),
             'source_snapshot_id': result['source_snapshot_id'],
             'synthetic_or_assumed': result['source_snapshot'].get('methods', {}).get('data_mode') == 'SYNTHETIC'}
    evaluations = {
        'accounting_profit': {
            'basis': '会计净利润，不是应税所得、销售额或项目现金流',
            'status': 'NOT_CALCULABLE', 'value': None, 'annual_profit_year': None,
            'reason': 'ACCOUNTING_NET_PROFIT_PRODUCER_AND_RECOGNITION_POLICY_NOT_BOUND',
            'required': ['权责发生制收入与费用确认', '会计折旧及税费口径', '经核验的逐年净利润结果'],
            'source_available': ['financial-ledger/depreciation', 'financial-ledger/taxable_income_project'],
            'prohibition': '现有税基及税务折旧不能证明会计净利润；不更改冻结会计方法'},
        'operating_cash_positive': {
            'basis': '经营活动现金净流量；年度为正和累计转正分别评价，不含项目投资回收',
            'status': 'NOT_CALCULABLE', 'value': None, 'annual_positive_period': None,
            'cumulative_positive_period': None,
            'reason': 'INDEPENDENT_OPERATING_CASH_BOUNDARY_NOT_BOUND',
            'required': ['经营现金分类及税费/营运资金边界', '独立年度经营现金流生产者'],
            'source_available': ['financial-ledger/revenue_cash_receipts', 'financial-ledger/opex_cash_paid', 'financial-ledger/cash_tax_total_project'],
            'prohibition': '屋顶节费是避免支出，不直接改称销售回款；不能拿项目净现金流替代经营现金流'},
    }
    for key, mids in METRICS.items():
        indicators = [_indicator(model, mid) for mid in mids]
        evaluations[key] = {
            'status': indicators[0]['status'], 'value': indicators[0]['value'],
            'indicators': indicators, 'discounted': key in {'dynamic_payback', 'project_return'},
            'periods': basis['periods'], 'tax_and_replacement': '按原生产者税费及更换现金边界，未从指标剔除',
            'decision_use': '只评价该口径；不证明工程准入、真实投资可行或股东已回本'}
    evaluations['static_payback']['basis'] = '无杠杆项目净现金流累计回收，保留建设期和更换事件'
    evaluations['dynamic_payback']['basis'] = '原项目折现率下累计折现现金回收，年度插值非精确日历日期'
    evaluations['project_return']['basis'] = '项目税后NPV与完整IRR根集，禁止混用股东回报或择优取根'
    equity = evaluations['shareholder_recovery']
    equity.update(basis='独立股东出资、分配和退出；不使用项目净现金替代',
                  status='NOT_CALCULABLE', value=None,
                  reason='SHAREHOLDER_RECOVERY_NOT_PRODUCED; original investor metric status retained',
                  owner_event_status=financial.get('owner_cash_events', 'UNKNOWN'),
                  required=['独立股东出资、分配及退出现金事件', '股东累计回收结果与日期口径'])
    targets = {name: _target(model, field) for name, field in (
        ('project_irr', 'targets.project_irr'), ('payback_years', 'targets.payback_years'),
        ('payback_basis', 'targets.payback_basis'), ('budget', 'targets.budget_ceiling'))}
    # Expose comparison operands; a target/method gap is not silently treated as passed.
    target_status = 'PENDING_SAME_BASIS_REVIEW' if any(t['value'] is not None for t in targets.values()) else 'TARGETS_NOT_PROVIDED'
    cash = model.metric('financial.phase3e.project_cash_flow')
    first_project_positive = None
    if cash and cash['status'] == 'CALCULATED' and isinstance(cash['value'], list) and len(cash['value']) == len(basis['periods']):
        first_project_positive = next((p for p, v in zip(basis['periods'], cash['value']) if v > 0), None)
    checks = {}
    irr = model.metric('financial.phase3e.project_irr')
    target = targets['project_irr']['value']
    checks['project_irr'] = 'NOT_EVALUATED'
    if (type(target) in (int, float, Decimal) and irr and irr['status'] == 'CALCULATED'
            and irr.get('details', {}).get('root_count') == 1
            and irr.get('details', {}).get('unexhausted') is False):
        checks['project_irr'] = 'MET_UNDER_MODEL_ASSUMPTIONS' if irr['value'] >= target else 'NOT_MET'
    payback_basis = targets['payback_basis']['value']
    target = targets['payback_years']['value']
    checks['payback'] = 'NOT_EVALUATED_OR_TEMPORAL_BASIS_UNMATCHED'
    if payback_basis in {'static_from_investment', 'dynamic_from_investment'} and type(target) in (int, float, Decimal):
        key = 'static_payback' if payback_basis == 'static_from_investment' else 'dynamic_payback'
        indicator = evaluations[key]['indicators'][0]
        if indicator['status'] == 'CALCULATED':
            checks['payback'] = 'MET_UNDER_MODEL_ASSUMPTIONS' if indicator['value'] <= target else 'NOT_MET'
    for key in ('accounting_profit', 'operating_cash_positive'):
        evaluations[key]['source_available'] = [p for p in evaluations[key]['source_available']
                                                if any(p.rsplit('/', 1)[1] in row for row in ledger.get('annual', []))]
    output = {'schema_version': 'financial-evaluation/2.0', 'identity': model.identity,
              'project_id': result['project_id'], 'pv_type': result['pv_type'], 'basis': basis,
              'evaluations': evaluations, 'targets': targets, 'target_status': target_status, 'target_checks': checks,
              'first_positive_project_net_cash_period': first_project_positive,
              'project_positive_is_not_operating_cash_or_profit': True,
              'professional_review': 'PENDING_REVIEW', 'investment_approval': 'NOT_ESTABLISHED'}
    output['evaluation_hash'] = digest(output)
    return output
