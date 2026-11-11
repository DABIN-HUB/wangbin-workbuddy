"""Typed projections of existing atoms and producer ledgers; no raw-series upload."""
from copy import deepcopy
from datetime import date
from decimal import Decimal
import re

from ..errors import ContractError
from ..report_claims import _sourced_rows, _source_value
from ..report_display_numbers import decision_number

GROUPS = frozenset({'resource.monthly', 'capex.items', 'opex.items', 'assets.depreciation',
                    'assets.replacements', 'finance.debt_schedule', 'schedule.tasks',
                    'risk.items', 'attachments.register', 'tariff.periods', 'revenue.other_items',
                    'system.losses', 'system.degradation_segments', 'scenarios.options'})
RAW_SERIES = frozenset({'resource.timeseries', 'load.series', 'tariff.market_series'})


def group_for(field):
    return next((g for g in GROUPS if field == g or field.startswith(g + '.')), None)


def input_facts(model, field, allowed, safe):
    """Return (facts, reason). Each child is matched to its original flat atom."""
    group = group_for(field)
    if group is None:
        return {}, 'STRUCTURED_SOURCE_REQUIRES_TYPED_ADAPTER'
    normalized = model.result['inputs']['normalized']
    records = model.result['source_snapshot']['phase2']['records']
    value = normalized.get(group)
    parents = [r for r in records if r.get('field_id') == group]
    if len(parents) != 1:
        return {}, 'SOURCE_OR_INSTANCE_UNAVAILABLE'
    parent = parents[0]
    if parent.get('source_id') not in allowed or parent.get('license_status') != 'AUTHORIZED':
        return {}, 'SOURCE_NOT_AUTHORIZED'
    if value == [] and parent.get('value') == [] and parent.get('status') in {'ASSUMED', 'VERIFIED'}:
        return {}, 'EXPLICIT_EMPTY_INPUT_NOT_MISSING'
    rows = (_source_value(normalized, records, group) if group in {'resource.monthly', 'schedule.tasks'}
            else _sourced_rows(value, records, group))
    if rows is None:
        return {}, 'STRUCTURED_ATOM_BINDING_INVALID'
    if len(rows) > 600:
        return {}, 'STRUCTURED_INPUT_BUDGET_EXCEEDED'
    flat = {r['field_instance_id']: r for r in records if r.get('field_instance_id')}
    facts = {}
    for row in rows:
        for fid, item in row['fields'].items():
            if field != group and fid != field:
                continue
            instance = group + ':' + row['row_id'] + ':' + fid.removeprefix(group + '.')
            atom = flat.get(instance)
            if not atom or fid not in model.catalog.fields:
                return {}, 'STRUCTURED_FIELD_OR_INSTANCE_INVALID'
            if atom.get('unit') != model.catalog.fields[fid]['unit']:
                return {}, 'UNIT_MISMATCH'
            atoms = atom['value'] if isinstance(item, list) and group == 'schedule.tasks' else [atom]
            if not atoms:
                # Preserve the actual empty relationship; do not invent a predecessor.
                atoms = [{**atom, 'value': '无前置任务（原始空列表）'}]
            for child in atoms:
                v = child.get('value') if isinstance(child, dict) else None
                if (not isinstance(child, dict) or child.get('source_id') not in allowed
                        or child.get('license_status') != 'AUTHORIZED'
                        or child.get('status') not in {'ASSUMED', 'VERIFIED'}
                        or isinstance(v, (list, dict)) or v is None):
                    return {}, 'STRUCTURED_CHILD_NOT_AUTHORIZED_OR_UNSUPPORTED'
                key = 'input:' + child['field_instance_id']
                if key in facts:
                    raise ContractError('EVIDENCE_DUPLICATE_INSTANCE')
                unit = child['unit']
                display = decision_number(v, unit or '') if type(v) in (int, float, Decimal) else safe(v)
                period = deepcopy(child.get('measurement_period'))
                if group == 'resource.monthly':
                    period = {k: normalized[k] for k in ('resource.period_start', 'resource.period_end', 'resource.dataset_id', 'resource.version', 'site.timezone')}
                    period['month'] = row['fields']['resource.monthly.month']
                facts[key] = {'kind': 'input', 'field_id': fid, 'label': model.catalog.fields[fid]['label_zh'],
                              'value': v, 'display': display, 'unit': unit, 'status': child['status'],
                              'source_ids': [child['source_id']], 'source_location': safe(child['source_section_or_cell']),
                              'period': period, 'boundary': 'SOURCE_INPUT_NOT_APPROVAL',
                              'provenance': {'business_object': group, 'field_instance_id': child['field_instance_id'],
                                             'row_id': row['row_id'], 'array_index': rows.index(row),
                                             'source_kind': child['source_kind'], 'synthetic_or_assumed': child['status'] == 'ASSUMED',
                                             'result_identity': model.identity}}
    return facts, None


def series_periods(model, metric):
    """Index labels come from the producer contract, not fabricated business IDs."""
    values, period = metric['value'], metric['period']
    monthly = re.fullmatch(r'OPERATING_YEAR_(\d+)_MONTHS_1_TO_12', period)
    if monthly and len(values) == 12:
        return [f'OPERATING_YEAR_{monthly[1]}_MONTH_{m}' for m in range(1, 13)]
    for metadata in ('phase3e-financial', 'financial-ledger'):
        periods = model.result.get('evidence', {}).get(metadata, {}).get('periods', [])
        if len(periods) == len(values) and period == str(len(values)) + '_PERIODS':
            return periods
    if metric['metric_id'] == 'energy.annual_array':
        periods = model.result.get('evidence', {}).get('phase3e-financial', {}).get('operating_periods', [])
        if len(periods) == len(values):
            return periods
    return None


def controlled_table(definition, facts, scoped):
    """Store per-cell fact IDs and safe display; model-authored rows never enter."""
    renderer = definition['renderer']
    result = {'definition': deepcopy(definition), 'fact_ids': list(scoped), 'rows': [], 'status': 'AVAILABLE'}
    if renderer == 'scenario_comparison':
        result['status'] = 'NO_EXECUTED_COMPARISON'
        return result
    if renderer == 'evidence_rows':
        return result
    group = 'schedule.tasks' if renderer == 'schedule_rows' else 'risk.items'
    by_row = {}
    for key in scoped:
        fact = facts[key]
        provenance = fact.get('provenance', {})
        if provenance.get('business_object') == group:
            by_row.setdefault(provenance['row_id'], {}).setdefault(fact['field_id'], []).append(key)
    for row_id, fields in by_row.items():
        cells, bindings = {}, {}
        for column in definition['columns']:
            key, fid = column['key'], column.get('field_id')
            refs = fields.get(fid, [])
            bindings[key] = refs
            cells[key] = '；'.join(facts[r]['display'] for r in refs) if refs else '未登记，待核验'
        if renderer == 'schedule_rows':
            refs = fields.get('schedule.tasks.start_date', []) + fields.get('schedule.tasks.finish_date', [])
            bindings['duration'] = refs
            if len(refs) == 2:
                try:
                    span = (date.fromisoformat(facts[refs[1]]['value']) - date.fromisoformat(facts[refs[0]]['value'])).days
                    cells['duration'] = str(span) if span >= 0 else '日期顺序冲突'
                except (TypeError, ValueError):
                    cells['duration'] = '日期无效'
        result['rows'].append({'row_id': row_id, 'cells': cells, 'bindings': bindings})
    if not result['rows']:
        result['status'] = 'NO_AUTHORIZED_ROWS'
    return result


LEDGER_FIELDS = {
    'CH14.02': ('capex_accrued', 'capex_cash_paid', 'replacement_cash_paid'),
    'CH14.05': ('debt_drawdown', 'interest_accrued', 'interest_paid', 'finance_fees_paid'),
    'CH15.01': ('opex_accrued', 'opex_cash_paid'),
    'CH15.02': ('depreciation', 'asset_book_value_closing'),
    'CH15.03': ('replacement_capex_accrued', 'replacement_cash_paid'),
    'CH15.04': ('taxable_income_project', 'income_tax_accrual_project', 'income_tax_cash_paid_project', 'cash_tax_total_project'),
    'CH15.05': ('opex_accrued', 'opex_cash_paid', 'depreciation'),
    'CH16.02': ('revenue_cash_receipts', 'self_use_avoided_expenditure', 'opex_cash_paid', 'cash_tax_total_project', 'working_capital_increase', 'working_capital_release'),
    'CH16.03': ('debt_drawdown', 'principal_paid', 'interest_paid', 'finance_fees_paid'),
}
SETTLEMENT_FIELDS = ('load_kwh', 'self_kwh', 'export_kwh', 'curtailed_kwh', 'delivered_kwh',
                     'self_value', 'export_sales_revenue', 'transaction_cost')


def producer_facts(model, sid, allowed):
    """Project ledger and first-year settlement summaries, never hourly raw data."""
    facts = {}
    if sid in LEDGER_FIELDS:
        ledger = model.result.get('evidence', {}).get('financial-ledger', {})
        periods = ledger.get('periods', [])
        rows = ledger.get('annual', [])
        sources = sorted({s for m in model.metrics if m['metric_id'].startswith('financial.') for s in m['source_ids']})
        if not sources or not set(sources) <= allowed:
            return {}, 'LEDGER_SOURCES_NOT_AUTHORIZED'
        if [r.get('period') for r in rows] != periods or len(set(periods)) != len(periods):
            return {}, 'LEDGER_PERIOD_IDENTITY_INVALID'
        selected = [(r['period'], key, r[key], 'currency', 'evidence/financial-ledger/annual')
                    for r in rows for key in LEDGER_FIELDS[sid] if key in r and r[key] is not None]
    elif sid in {'CH10.01', 'CH10.02', 'CH10.03', 'CH10.04', 'CH10.05'}:
        metric = model.metric('revenue.year.1')
        if not metric or metric['status'] != 'CALCULATED':
            return {}, 'SETTLEMENT_NOT_CALCULATED'
        sources = metric['source_ids']
        if not sources or not set(sources) <= allowed:
            return {}, 'SETTLEMENT_SOURCES_NOT_AUTHORIZED'
        monthly = metric.get('details', {}).get('monthly', [])
        if len(monthly) != 12:
            return {}, 'MONTHLY_SETTLEMENT_NOT_SUPPLIED'
        keys = SETTLEMENT_FIELDS
        if model.result['pv_type'] == 'utility_scale_ground':
            keys = tuple(k for k in keys if k not in {'load_kwh', 'self_kwh', 'self_value'})
        selected = [(f'OPERATING_YEAR_1_MONTH_{i}', key, row[key], 'kWh' if key.endswith('_kwh') else 'currency',
                     'results/metrics/revenue.year.1/details/monthly')
                    for i, row in enumerate(monthly, 1) for key in keys if key in row]
    else:
        return {}, None
    for period, key, value, unit, pointer in selected:
        if type(value) not in (int, float, Decimal):
            raise ContractError('LEDGER_VALUE_TYPE')
        fid = 'ledger:' + pointer.replace('/', ':') + ':' + period + ':' + key
        facts[fid] = {'kind': 'ledger', 'label': key, 'value': value,
                      'display': decision_number(value, unit), 'unit': unit,
                      'status': 'CALCULATED', 'source_ids': sources, 'period': period,
                      'boundary': 'PRODUCER_LEDGER_NOT_ACCOUNTING_PROFIT_OR_APPROVAL',
                      'provenance': {'result_identity': model.identity, 'result_pointer': pointer,
                                     'row_id': period, 'business_object': key,
                                     'synthetic_or_assumed': model.result['source_snapshot'].get('methods', {}).get('data_mode') == 'SYNTHETIC'}}
    return facts, None
