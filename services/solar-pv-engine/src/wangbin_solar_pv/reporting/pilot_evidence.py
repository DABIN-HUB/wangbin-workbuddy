"""Read-only, section-scoped projections for the six-chapter content pilot."""
from decimal import Decimal

from ..errors import ContractError
from ..serialization import digest
from .reader_display import period_label

SETTLEMENT = {
    'available_kwh': '结算入口可利用电量', 'delivered_kwh': '交付电量',
    'load_kwh': '用电负荷', 'self_kwh': '厂内自用电量', 'export_kwh': '上网电量',
    'curtailed_kwh': '结算环节限发电量', 'self_value': '可避免购电支出',
    'export_sales_revenue': '对外售电收入', 'gross_benefit': '综合经济收益（扣交易费前）',
    'transaction_cost': '交易费计提', 'benefit_after_transaction_cost': '扣交易费后经济收益',
    'other_benefit': '其他经济收益',
}
CASH = {'revenue_cash_receipts': '预计售电回款', 'self_use_avoided_expenditure': '自用避免支出',
        'transaction_cost_cash_paid': '预计交易费付款', 'replacement_cash_paid': '更换资本支出',
        'opex_cash_paid': '运营现金支出', 'cash_tax_total_project': '项目现金税费',
        'working_capital_increase': '营运资金增加', 'working_capital_release': '营运资金释放'}
METHOD_NAMES = {'settlement.price_source': '收入采用的价格路径', 'settlement.fee_treatment': '交易费入账方式',
                'settlement.revenue_method': '收入计算方式'}
METHOD_TEXT = {'PERIOD_TABLE': '分时价格表', 'MARKET_SERIES': '逐时市场价格时序',
               'SEPARATE_LEDGER': '交易费独立计提', 'EMBEDDED_IN_PRICE': '交易费已含价格',
               'OWNER_AVOIDED_COST': '自用避免支出与上网售电分别计量', 'EXPORT_ONLY': '全额上网售电'}
TERMINAL_TEXT = {'NO_DISPOSITION': '声明终期不处置资产、不另行取得处置回款',
                 'LEDGER_ALREADY_RECOVERED': '声明营运资金已在原台账回收，不另行重复计入',
                 'SOURCE_AND_LEDGER_RECONCILED': '基准已有同身份终期调节记录，非真实回款证明'}


def terminal_declaration(model, allowed):
    """Project the sealed baseline declaration, never calculate terminal cash."""
    result = model.result
    snapshot = result['source_snapshot'].get('phase3e_terminal')
    if not snapshot:
        return {}, ['终期声明未提供，不能以账面残值替代处置现金。']
    source, binding = snapshot['source'], snapshot['binding']
    if source.get('mode') != 'NO_DISPOSITION':
        return {}, ['当前终期声明模式没有只读展示适配，不能补算处置现金。']
    atom = source['no_disposition']['source']
    if (atom.get('license_status') != 'AUTHORIZED' or
            atom.get('source_status') not in {'ASSUMED', 'VERIFIED'} or
            not atom.get('source_section_or_cell') or atom.get('source_id') not in allowed):
        return {}, ['终期声明来源未获授权或未核验。']
    cash = model.metric('financial.phase3e.project_cash_flow')
    if not cash:
        return {}, ['同身份项目现金结果未提供，终期声明不代替现金结果。']
    boundary = result['boundaries'].get(cash['boundary_id'], {})
    normalized = result['inputs']['normalized']
    identity = {'project_id': result['project_id'], 'pv_type': result['pv_type'],
                'scenario_id': result['scenario_id'], 'currency': normalized['project.currency'],
                'evaluation_date': normalized['project.evaluation_date']}
    if (snapshot.get('source_content_hash') != digest(source) or
            snapshot.get('binding_hash') != digest(binding) or
            any(binding.get(k) != v for k, v in identity.items()) or
            any(source.get(k) != v for k, v in identity.items() if k != 'scenario_id') or
            binding.get('phase3d_result_hash') != snapshot.get('phase3d_result_hash') or
            binding.get('phase3d_result_hash') != boundary.get('upstream_financial_result_hash')):
        raise ContractError('PILOT_TERMINAL_IDENTITY')
    values = {'mode': source['mode'],
              'working_capital_treatment': source['no_disposition']['working_capital_treatment']}
    reconciliation = result['evidence'].get('phase3e-terminal-reconciliation', {})
    if (cash['status'] == 'CALCULATED' and
            boundary.get('terminal_cash_policy') == 'SOURCE_AND_LEDGER_RECONCILED' and
            reconciliation.get('binding_hash') == snapshot['binding_hash'] and
            reconciliation.get('source_content_hash') == snapshot['source_content_hash'] and
            reconciliation.get('periods') == result['evidence'].get('financial-ledger', {}).get('periods')):
        values['availability'] = boundary['terminal_cash_policy']
    return {key: {'value': value, 'source': atom} for key, value in values.items()}, (
        [] if 'availability' in values else ['同身份终期调节记录未核验，不得填零或借用其他情景金额。'])


def pilot_facts(model, sid, allowed):
    if sid[:4] not in {'CH08', 'CH10', 'CH16'}:
        return {}, []
    facts, missing = {}, []
    def add(key, label, value, unit, sources, pointer, period='OPERATING_YEAR_1', status='CALCULATED', **extra):
        if not sources or not set(sources) <= allowed:
            missing.append(key + ': SOURCE_NOT_AUTHORIZED')
            return
        if value is not None and type(value) not in (int, float, Decimal, str, bool):
            raise ContractError('PILOT_FACT_VALUE_TYPE')
        facts['pilot:' + key] = {'kind': 'ledger', 'label': label, 'value': value, 'display': '',
            'unit': unit, 'status': status if value is not None else 'UNKNOWN',
            'source_ids': list(sources), 'period': period,
            'boundary': 'READ_ONLY_EXISTING_PRODUCER_NOT_NEW_CALCULATION',
            'provenance': {'result_identity': model.identity, 'result_pointer': pointer,
                           'business_object': key, 'synthetic_or_assumed':
                           model.result['source_snapshot']['methods'].get('data_mode') == 'SYNTHETIC'}, **extra}
    rev = model.metric('revenue.year.1')
    if sid in {'CH10.01', 'CH10.02', 'CH10.03', 'CH10.04', 'CH10.05', 'CH16.01'} and rev and rev['status'] == 'CALCULATED':
        ledger = rev.get('details', {}).get('ledger', {})
        for key, label in SETTLEMENT.items():
            if model.result['pv_type'] == 'utility_scale_ground' and key in {'load_kwh', 'self_kwh', 'self_value'}:
                continue
            add('settlement.' + key, '首年' + label, ledger.get(key), 'kWh' if key.endswith('_kwh') else 'currency',
                rev['source_ids'], 'results/metrics/revenue.year.1/details/ledger/' + key)
        if model.result['pv_type'] == 'industrial_rooftop':
            for name in ('self_ratio', 'load_coverage'):
                metric = model.metric('consumption.' + name + '.year.1')
                if metric:
                    add('settlement.' + name, '首年自用电量占交付电量比例' if name == 'self_ratio' else '首年负荷覆盖率',
                        metric['value'], metric['unit'], metric['source_ids'], 'results/metrics/' + metric['metric_id'],
                        status=metric['status'], metric_id=metric['metric_id'])
        for key, label in METHOD_NAMES.items():
            atom = model.result['source_snapshot']['methods']['parameters'].get(key, {})
            if atom.get('license_status') == 'AUTHORIZED' and atom.get('status') in {'ASSUMED', 'VERIFIED'}:
                add('method.' + key, label, atom['value'], '', [atom['source_id']],
                    'source_snapshot/methods/parameters/' + key, status=atom['status'])
        intervals = model.result['evidence'].get('consumption-intervals', {})
        if intervals.get('status') == 'CALCULATED':
            add('settlement.interval_count', '首年同粒度结算时段数', intervals.get('row_count'), '个', rev['source_ids'],
                'evidence/consumption-intervals/row_count')
    if sid in {'CH08.05', 'CH10.02'}:
        energy = model.metric('energy.year.1')
        if energy and energy['status'] == 'CALCULATED':
            for key, label in [('availability', '不可利用损失'), ('curtailment', '发电侧限发损失'), ('export_line', '送出线路损失')]:
                add('energy.loss.' + key, '首年' + label, energy['details']['losses_kwh'].get(key), 'kWh',
                    energy['source_ids'], 'results/metrics/energy.year.1/details/losses_kwh/' + key)
        available = model.metric('available_kwh.year.1')
        if available:
            add('energy.available', '首年发电侧限发前可利用电量', available['value'], available['unit'], available['source_ids'],
                'results/metrics/available_kwh.year.1/value', status=available['status'])
    if sid in {'CH10.04', 'CH16.01', 'CH16.02'}:
        ledger = model.result['evidence'].get('financial-ledger', {})
        rows = ledger.get('annual', [])
        if [r.get('period') for r in rows] != ledger.get('periods') or len({r['period'] for r in rows}) != len(rows):
            raise ContractError('PILOT_LEDGER_PERIOD_IDENTITY')
        cash = model.metric('financial.phase3e.project_cash_flow')
        if cash:
            for i, row in enumerate(rows):
                if sid != 'CH16.02' and row['period'] != 'OPERATING_YEAR_1':
                    continue
                for key, label in CASH.items():
                    if model.result['pv_type'] == 'utility_scale_ground' and key == 'self_use_avoided_expenditure':
                        continue
                    add('cash.' + row['period'] + '.' + key, period_label(row['period']) + label, row.get(key), 'currency',
                        cash['source_ids'], f'evidence/financial-ledger/annual/{i}/{key}', period=row['period'])
                    if key == 'transaction_cost_cash_paid' and row.get(key) is None:
                        missing.append('交易费预计支付尚未在当前基准台账独立绑定，不能按零或按计提金额替代。')
    if sid == 'CH16.01':
        declarations, reasons = terminal_declaration(model, allowed)
        missing.extend(reasons)
        for key, item in declarations.items():
            atom = item['source']
            label, pointer = {
                'mode': ('终期处置政策声明', 'source_snapshot/phase3e_terminal/source/mode'),
                'working_capital_treatment': ('营运资金回收声明',
                    'source_snapshot/phase3e_terminal/source/no_disposition/working_capital_treatment'),
                'availability': ('基准终期记录可用性', 'boundaries/' +
                    model.metric('financial.phase3e.project_cash_flow')['boundary_id'] + '/terminal_cash_policy'),
            }[key]
            add('terminal.' + key, label, item['value'], '',
                [atom['source_id']], pointer, period='TERMINAL',
                status=atom['source_status'], boundary='DECLARATION_AND_EXISTING_RECORD_NOT_ACTUAL_RECEIPT')
    return facts, sorted(set(missing))


def pilot_table_facts(sid, facts, scoped):
    """Bound body tables to their business purpose; complete evidence stays in JSON."""
    if sid == 'CH08.02':
        return [k for k in scoped if k.startswith('metric:energy.monthly.')]
    if sid == 'CH08.03':
        return [k for k in scoped if k.startswith('metric:energy.annual_array:')]
    if sid == 'CH08.04':
        return [k for k in scoped if k.startswith('metric:')]
    if sid in {'CH08.05', 'CH10.02'}:
        return [k for k in scoped if k.startswith(('pilot:energy.', 'pilot:settlement.')) and
                not k.endswith(('self_value', 'export_sales_revenue', 'gross_benefit', 'transaction_cost',
                                'benefit_after_transaction_cost', 'other_benefit', 'interval_count'))]
    if sid == 'CH10.04':
        return [k for k in scoped if k.startswith('pilot:cash.') or k in {'pilot:settlement.transaction_cost', 'pilot:method.settlement.fee_treatment'}]
    if sid == 'CH16.02':
        return [k for k in scoped if k.startswith('metric:financial.phase3e.project_cash_flow:')]
    if sid.startswith('CH16.'):
        return [k for k in scoped if k.startswith('metric:')]
    return scoped
