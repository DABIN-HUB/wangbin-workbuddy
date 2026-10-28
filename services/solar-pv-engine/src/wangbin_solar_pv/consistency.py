"""Cross-record data-quality audits; never fills missing values or forecasts outcomes."""
from __future__ import annotations

import calendar
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction

from .errors import Issue


def _number(value):
    return not isinstance(value,bool) and isinstance(value,(int,float,Decimal))


def validate_input_relations(project,catalog):
    from .validation import _value,_rows,row_value,compatible_economic_basis,iter_records
    result=[]
    def issue(code,fid,message,severity="ERROR"):
        result.append(Issue(code,fid,message,severity))
    # Calculated cost amounts must point to the same item, not merely like-named fields.
    contexts={}
    for group in ("capex.items",):
        for row in _rows(project,group):
            for record in row.get("fields",{}).values():
                contexts[record.get("field_instance_id")]=(group,row.get("row_id"))
    for record,_ in iter_records(project.values,catalog):
        fid=record.get("field_id","")
        if fid=="capex.items.amount" and record.get("provenance_kind")=="C":
            here=contexts.get(record.get("field_instance_id"))
            if any(contexts.get(upstream)!=here for upstream in record.get("upstream_instance_ids",[])):
                issue("AMOUNT_LINEAGE_ROW_MISMATCH",fid,"数量和单价必须属于该金额所在明细行")
        if record.get("status")=="VERIFIED" and record.get("effective_to"):
            evaluation=_value(project,"project.evaluation_date")
            if isinstance(evaluation,str) and record["effective_to"]<evaluation:
                issue("EVIDENCE_EXPIRED",fid,"证据在评价基准日已失效，须重新核实","WARNING")
        if fid.startswith("tariff.") and _number(record.get("value")) and record["value"]<0:
            rule=_value(project,"tariff.negative_price_rule")
            contract=_value(project,"tariff.contract_id")
            if not rule or not contract:
                issue("NEGATIVE_PRICE_REQUIRES_RULE",fid,"负电价需合法结算规则及合同依据，不取绝对值")
    for row in _rows(project,"capex.items"):
        fields=row.get("fields",{})
        prices=[fields.get("capex.items."+name,{}) for name in ("unit_price","amount")]
        if all(p.get("economic_basis") for p in prices) and not compatible_economic_basis(prices[0]["economic_basis"],prices[1]["economic_basis"]):
            issue("ECONOMIC_BASIS_CONFLICT","capex.items","报价年份/币种/含税/名实口径不同，不能直接比较或相加")
        quantity,price,amount=[row_value(row,"capex.items."+name) for name in ("quantity","unit_price","amount")]
        # This checks supplied quote arithmetic, not project CAPEX forecasting.
        if all(_number(v) for v in (quantity,price,amount)):
            if Fraction(str(quantity))*Fraction(str(price))!=Fraction(str(amount)):
                issue("QUOTE_AMOUNT_MISMATCH","capex.items.amount","给定数量单价与报价金额不符，保留原数值待复核","WARNING")
        currency=row_value(row,"capex.items.currency")
        if currency and _value(project,"project.currency") and currency!=_value(project,"project.currency"):
            if row_value(row,"capex.items.fx_rate") is None:
                issue("FX_EVIDENCE_REQUIRED","capex.items.fx_rate","跨币种成本缺汇率及日期证据")
        tax=row_value(row,"capex.items.tax_included")
        for price_record in prices:
            basis=price_record.get("economic_basis")
            if basis and isinstance(tax,bool) and basis.get("tax_basis")!=("inclusive" if tax else "exclusive"):
                issue("ECONOMIC_BASIS_CONFLICT","capex.items","行税含声明与金额口径冲突")
        quote_day,expiry=row_value(row,"capex.items.quote_date"),row_value(row,"capex.items.quote_valid_until")
        if quote_day and expiry and quote_day>expiry:
            issue("QUOTE_PERIOD_ORDER","capex.items.quote_valid_until","报价有效期不能早于报价日")
    for row in _rows(project,"assets.depreciation"):
        basis,residual=row_value(row,"assets.depreciation.depreciable_basis"),row_value(row,"assets.depreciation.residual_value")
        if _number(basis) and _number(residual) and residual>basis:
            issue("RESIDUAL_EXCEEDS_BASIS","assets.depreciation.residual_value","残值不能超过原始折旧基数")
    years=_value(project,"project.evaluation_years")
    for group,start_key,end_key in (("opex.items","from_year","to_year"),("system.degradation_segments","from_year","to_year")):
        intervals=[]
        for row in _rows(project,group):
            start,end=row_value(row,group+"."+start_key),row_value(row,group+"."+end_key)
            if isinstance(start,int) and isinstance(end,int):
                if start>end or (isinstance(years,int) and end>years):
                    issue("YEAR_RANGE_INVALID",group,"年度起止倒置或超出评价期")
                intervals.append((start,end))
        if group=="system.degradation_segments" and intervals:
            intervals.sort()
            if any(b[0]<=a[1] for a,b in zip(intervals,intervals[1:])):
                issue("DEGRADATION_SEGMENT_OVERLAP",group,"衰减分段年序不能重叠")
            if any(b[0]!=a[1]+1 for a,b in zip(intervals,intervals[1:])):
                issue("DEGRADATION_SEGMENT_GAP",group,"衰减分段缺口不得自动补造","WARNING")
    months=[]
    period_start=_value(project,"resource.period_start")
    resource_year=None
    if isinstance(period_start,str):
        try: resource_year=date.fromisoformat(period_start).year
        except ValueError: pass
    for row in _rows(project,"resource.monthly"):
        month,days=row_value(row,"resource.monthly.month"),row_value(row,"resource.monthly.days")
        if isinstance(month,int) and 1<=month<=12:
            months.append(month)
            if resource_year and isinstance(days,int) and days!=calendar.monthrange(resource_year,month)[1]:
                issue("MONTH_DAYS_MISMATCH","resource.monthly.days","月份天数与明确数据年份不符；TMY需另行边界核实")
    if len(months)!=len(set(months)):
        issue("RESOURCE_MONTH_DUPLICATE","resource.monthly.month","资源月份不能重复")
    if months and set(months)!=set(range(1,13)):
        issue("RESOURCE_MONTHS_INCOMPLETE","resource.monthly","12月资料未齐，不补均值或零","WARNING")
    for row in _rows(project,"load.series"):
        power,energy,minutes=[row_value(row,"load.series."+name) for name in ("power","energy","interval_minutes")]
        if all(_number(v) for v in (power,energy,minutes)) and Fraction(str(power))*Fraction(str(minutes))/60!=Fraction(str(energy)):
            issue("LOAD_POWER_ENERGY_MISMATCH","load.series","同一时段给定功率、电量、时长不相符，平均功率边界需核实","WARNING")
    evaluation=_value(project,"project.evaluation_date")
    for row in _rows(project,"policy.applicability"):
        status=row_value(row,"policy.applicability.applicability_status")
        expiry=row_value(row,"policy.applicability.effective_to")
        replaced=row_value(row,"policy.applicability.superseded_by")
        if status=="applicable" and ((isinstance(evaluation,str) and isinstance(expiry,str) and expiry<evaluation) or replaced):
            issue("POLICY_APPLICABILITY_CONFLICT","policy.applicability","过期/被替代政策不可仍当本站现行依据")
    for row in _rows(project,"scenarios.options"):
        changed=row_value(row,"scenarios.options.changed_field_id")
        if changed is not None and changed not in catalog.fields:
            issue("SCENARIO_UNKNOWN_FIELD","scenarios.options.changed_field_id","方案变更只能引用冻结字段")
    low,high,initial,terminal=[_value(project,"storage."+name) for name in ("soc_min","soc_max","soc_initial","soc_terminal")]
    if all(_number(v) for v in (low,high,initial,terminal)) and not (low<=initial<=high and low<=terminal<=high):
        issue("SOC_BOUND_ORDER","storage.soc_min","初始/终端SOC须在已声明上下界内，不执行调度")
    return result
