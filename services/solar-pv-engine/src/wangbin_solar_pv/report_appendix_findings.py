"""Bounded, per-object appendix findings; calculated arrays remain in trace tables."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable


def appendix_finding(model: Any, item_id: str, fmt: Callable[[Any], str], source_value: Callable) -> str:
    result = model.result
    n = result['inputs'].get('normalized', {})
    records = result.get('source_snapshot', {}).get('phase2', {}).get('records', ())
    get = lambda fid: source_value(n, records, fid)
    def metric(mid):
        row = model.metric(mid)
        return row.get('value') if row and row.get('status') == 'CALCULATED' else None
    def amount(value, unit):
        return f'{fmt(value)}{unit}' if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool) else '未形成有效计算值'
    ground = result.get('pv_type') == 'utility_scale_ground'
    annual = result.get('evidence', {}).get('financial-ledger', {}).get('annual', ())
    build = annual[0] if annual and annual[0].get('period') == 'CONSTRUCTION' else {}
    first = annual[1] if len(annual) > 1 and annual[1].get('period') == 'OPERATING_YEAR_1' else {}
    flows = metric('financial.phase3e.project_cash_flow')
    break_even = model.metric('financial.phase3e.break-even-price')
    scenario_id = result.get('scenario_id')
    has_scenario_evidence = scenario_id != 'BASE' or any(
        row.get('status') == 'CALCULATED' and row.get('metric_id', '').startswith('sensitivity.')
        for row in result.get('results', {}).get('metrics', ()))
    months = metric('energy.monthly.year.1')
    daily = get('resource.monthly')
    if (isinstance(months, list) and len(months) == 12
            and all(isinstance(x, (int, float, Decimal)) and not isinstance(x, bool) for x in months)):
        month_total = sum(Decimal(str(x)) for x in months)
        annual_total = metric('energy.year.1')
        if isinstance(annual_total, (int, float, Decimal)) and not isinstance(annual_total, bool):
            displayed_total = sum(Decimal(fmt(x).replace(',', '')) for x in months)
            month_note = (f'月度显示值合计{fmt(displayed_total)}kWh，年度指标列示{fmt(annual_total)}kWh；'
                          '逐月与年度独立取整，按未取整值核对'
                          if abs(month_total - Decimal(str(annual_total))) < Decimal('0.01') else
                          '原始月度与年度指标不一致，先核查月序列及年度边界')
        else:
            month_note = '年度指标未计算，不推断月年闭合'
    else:
        month_total, month_note = None, '缺少可对账的十二个月发电指标'
    return {
        'APP01.01': f'Phase 2字段原子记录中有{len({r.get("source_id") for r in records if r.get("source_id")})}个来源标识；'
                       '时序数据和交易费等独立来源另见配套来源清单，不能把此计数当作全报告来源总数；'
                       '来源编号不证明原件授权或可读性，须逐份取回核对。',
        'APP01.02': f'字段来源快照登记{len(records)}条原子记录；须逐实例核对取值、原件位置和来源身份，数量不证明全部已核验。',
        'APP02.01': (f'绑定的合成月度气象输入共{len(daily)}个月；须逐月核对GHI/DNI/DHI/POA的kWh/㎡、气温℃、风速m/s及年份时区。'
                      if isinstance(daily, list) else '月度气象未完成原子来源核对；不能从月发电结果倒推辐照分量。'),
        'APP02.02': (f'首年12个月发电原值求和{amount(month_total, "kWh")}，'
                      f'年度发电{amount(metric("energy.year.1"), "kWh")}；{month_note}；'
                      + ('屋面自用、余电及交付须逐月在同一计量边界对账。' if not ground else '地面交付与集中上网须逐月对账，不引入自用账。')
                      if month_total is not None else '月度发电与年度指标未同时闭合；不把发电代替交付结算。'),
        'APP03.01': f'设备额定直流{amount(metric("dc_capacity"), "kWp")}、交流{amount(metric("ac_capacity"), "kWac")}；须与组件和逆变器型号数据表、行距逐项复核。',
        'APP03.02': f'首年发电{amount(metric("energy.year.1"), "kWh")}；年度曲线须逐年核查衰减与更换停机，损失不得重复扣减。',
        'APP04.01': f'评价期CAPEX{amount(metric("financial.capex.total"), "元")}包含计划更换；专项工程量与税价口径须逐项对账。',
        'APP04.02': f'建设期账簿计划支付{amount(build.get("capex_cash_paid"), "元")}，评价期CAPEX{amount(metric("financial.capex.total"), "元")}；报价、应付与实付分别核验。',
        'APP05.01': f'全期现金运维{amount(metric("financial.opex.cash_lifecycle"), "元")}；首年折旧{amount(first.get("depreciation"), "元")}为非现金，更换与交易费预计支付另列。',
        'APP05.02': f'首年项目现金税费{amount(first.get("cash_tax_total_project"), "元")}；须逐年勾稽税基、应计、应付和现金支付，不以税率替代税单。',
        'APP06.01': (f'项目建设期年度净流量{amount(flows[0], "元")}、第1年{amount(flows[1], "元")}；'
                      '全期还须逐年核对更换、营运资金与终期收付，合成预计付款不等于银行凭证。'
                      if isinstance(flows, list) and len(flows) > 1 else '项目建设期与第1年现金流未同时计算，不能据收入估算投资回报。'),
        'APP06.02': ('股东出资、实际分配及退出事件未闭合，投资者现金流受阻；无债务不代表项目年度净流量就是股东回款。'
                      if metric('financial.phase3e.equity-investor-cash-flow') is None else
                      '投资者现金流已有计算值；须逐期核实股东出资、融资及实际分配与项目现金流的差异。'),
        'APP07.01': ('本次明确无债务，合同债务服务不存在，DSCR不适用；不能将零偿债额解释为已达标。'
                      if get('finance.debt_ratio') == 0 else '须逐期将合同还本付息和可供偿债现金配对后评价DSCR。'),
        'APP07.02': ('债务比例输入为零；零分母使本次DSCR未定义而非零倍，若新增融资应重建本息日程。'
                      if get('finance.debt_ratio') == 0 else '有债务项目逐期核查债务服务分母；零分母期不得填零倍。'),
        'APP08.01': (f'当前结果登记情景身份{scenario_id}；单个情景不证明单因素及组合扰动已完整执行，'
                     '须逐次核对运行身份和对照结果。' if has_scenario_evidence else
                     '本次只有基准测算，没有独立单因素及组合运行身份；资源、价格和造价扰动不得从基准值外推。'),
        'APP08.02': (f'本次保本电价已计算为{fmt(break_even["value"])}{break_even.get("unit") or ""}；'
                     '仍须逐次核对同口径目标、重算身份和方向性验收。'
                     if break_even and break_even.get('status') == 'CALCULATED' else
                     '保本电价的全链反向重算仍受阻；须以同口径目标、重算身份和单调方向测试验收。'),
        'APP09.01': '政策登记尚不能代替有文号、原文、地区及生效期的可适用条款；不得称已获项目批准。',
        'APP09.02': '政策适用及潜在冲突没有逐条外部审查意见；应分别核对权属、接网与交易的有效文件。',
        'APP10.01': ('屋顶权属与结构证明缺失会影响合法使用和安全布置；真实负荷及接网资料缺失会改变自用电量和余电收入。'
                       '须分别取得权利原件、结构防水消防图、逐时电费记录和电网答复；发现项登记不等于这些资料已关闭。'
                       if not ground else '土地权利、地勘测绘和道路排水资料缺失，会影响阵列排布、基础与总投资；'
                       '正式接网与交易文件缺失会影响可售电量和价格。须取得签署原件及工程初设逐项复核。'),
        'APP10.02': ('可先开展负荷资料收集及屋面结构初查；取得合法权利、结构消防及接网意见后，'
                       '按实际费用和消纳重新计算项目回报，再提请真实投资决策。' if not ground else
                       '可先开展场址测绘、地勘及送出沟通；取得合法用地、工程量、正式接入与交易条件后，'
                       '重新评估回报及第13年设备更换的资金安排。'),
        'APP11.01': '本次公式快照仅是正式定义与执行状态的入口；逐公式核对单位、适用条件和绑定输入，不补造计算式。',
        'APP11.02': '公式局部符号须逐个说明定义、单位和求和范围；同名字母在不同公式内不可跨式套用。',
        'APP12.01': '报告术语须分别对应中文、英文全称、缩写和首次释义；IRR根集与NPV币种均不能只列缩写。',
        'APP12.02': '直流kWp、交流kW、交付kWh与辐照kWh/㎡必须分别标注；单位投资以kWp为分母。',
        'APP13.01': '本次报告只绑定同一项目、输入和结果哈希；模型、运行及来源身份须逐文件比对，不得拼接历史导出。',
        'APP13.02': f'统一计算状态为{dict(PARTIAL="部分计算", COMPLETE="计算完成", BLOCKED="阻断").get(result.get("status"), "待核对")}，真实项目来源另有独立核验门槛；文档结构完整不等于页面审阅或可投资。',
    }[item_id]
