"""Presentation-only Chinese facts; never changes a value or financial method."""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import re

PERCENT_FIELDS = frozenset({
    'targets.project_irr', 'targets.equity_irr', 'finance.project_discount_rate',
    'finance.equity_discount_rate', 'site.shading_fraction', 'system.module_efficiency',
    'system.inverter_efficiency', 'layout.ground_coverage_ratio', 'system.first_year_degradation',
    'system.annual_degradation', 'system.unavailability', 'system.degradation_segments.rate',
    'resource.uncertainty_fraction', 'resource.monthly.coverage', 'resource.annual_comparison.coverage',
    'resource.annual_comparison.difference_from_reference', 'grid.curtailment_assumption',
    'load.proposed_self_use_ratio', 'tariff.revenue_share', 'tariff.periods.vat_rate',
    'capex.contingency_rate', 'capex.items.vat_rate', 'capex.items.recoverable_vat_share',
    'opex.items.escalation_rate', 'opex.items.vat_rate', 'opex.items.recoverable_vat_share',
    'tax.corporate_income_rate', 'tax.vat_output_rate', 'tax.surcharge_rate', 'finance.debt_ratio',
    'finance.loan_rate', 'finance.shareholder_cost', 'finance.inflation_rate',
})
PERCENT_METRICS = ('pr_observed.', 'capacity_factor.', 'consumption.self_ratio.', 'consumption.load_coverage.')
UNITS = {'CNY': '元', 'currency': '元', 'currency/kWh': '元/kWh', 'year': '年',
         'day': '天', 'hour': '小时', 'h': '小时', 'minute': '分钟', 'min': '分钟',
         '1': '', 'date': '', 'boolean': '', 'kWh/year': 'kWh/年'}


def number(value, places=2, trim=True):
    with localcontext() as ctx:
        ctx.prec = max(80, len(value.as_tuple().digits) + abs(value.adjusted()) + 10)
        rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    if rounded == 0:
        rounded = abs(rounded)
    text = f'{rounded:,.{places}f}'
    if trim and '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text


def period_label(period):
    if period == 'CONSTRUCTION':
        return '建设期'
    match = re.fullmatch(r'OPERATING_YEAR_(\d+)(?:_MONTH_(\d+))?', str(period))
    if match:
        return '运营第' + match[1] + '年' + ('第' + match[2] + '月' if match[2] else '')
    return ''


def irr_text(metric):
    """Describe only a certified complete root set; full proof stays in evidence."""
    from .compat import irr_presentation
    certified, _ = irr_presentation(metric)
    if certified == '根集待核验':
        return '尚未完成收益率解的完整性核验'
    details = metric.get('details', {})
    roots = details.get('roots', [])
    if details.get('unexhausted') is not False or details.get('root_count') != len(roots):
        return '尚未完成收益率解的完整性核验'
    if not roots:
        return '在声明的检索范围内未找到收益率解，不能按零收益率解释'
    if not (metric.get('status') == 'CALCULATED' or
            (len(roots) > 1 and metric.get('status') == 'UNDEFINED' and metric.get('reason') == 'MULTIPLE_ROOTS')):
        return '收益率结果尚不具备有效解释条件'
    rates = certified
    if len(roots) == 1:
        return rates + '（在声明检索范围内仅有一个经认证的解）'
    return '存在多个经认证的收益率解：' + rates + '；不能挑选其中一个作为项目回报率'


def fact_display(fact, currency=None, metric=None):
    """Return (reader value, reader unit), retaining raw fact/provenance unchanged."""
    if metric and metric.get('metric_id') == 'financial.phase3e.project_irr':
        return irr_text(metric), ''
    status, value = fact['status'], fact['value']
    if status == 'NOT_APPLICABLE':
        return '不适用', ''
    if status == 'UNDEFINED':
        return '当前条件下未定义', ''
    if status not in {'CALCULATED', 'ASSUMED', 'VERIFIED'} or value is None:
        return '尚无可用结果', ''
    if isinstance(value, bool):
        return ('是' if value else '否'), ''
    unit = fact.get('unit') or ''
    display_unit = UNITS.get(unit, unit)
    if unit.startswith('currency') and currency not in {'CNY', '元'}:
        display_unit = (currency or '币种待核验') + unit.removeprefix('currency')
    if isinstance(value, str):
        if unit == 'date' or re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            try:
                d = date.fromisoformat(value)
                return f'{d.year}年{d.month}月{d.day}日', ''
            except ValueError:
                return '日期无效，待核验', ''
        return value, ''
    if not isinstance(value, (int, float, Decimal)):
        return '尚无可用结果', ''
    try:
        n = Decimal(str(value))
        if not n.is_finite():
            return '尚无可用结果', ''
        fid, mid = fact.get('field_id', ''), fact.get('metric_id', '')
        if fid == 'assets.replacements.year':
            if n != n.to_integral_value() or n < 1:
                return '更换年度无效，待核验', ''
            return '运营第' + str(int(n)) + '年', ''
        if fid in PERCENT_FIELDS or mid.startswith(PERCENT_METRICS):
            return number(n * 100, 2, False), '%'
        places = 0 if unit in {'CNY', '元', 'currency', 'kWh', 'kW', 'kWp', 'kWac'} else 3 if unit in {'currency/kWh', '元/kWh'} else 2
        return number(n, places), display_unit
    except (InvalidOperation, ValueError):
        return '尚无可用结果', ''


def inline(fact):
    unit = fact.get('display_unit', fact.get('unit')) or ''
    return fact['display'] + unit
