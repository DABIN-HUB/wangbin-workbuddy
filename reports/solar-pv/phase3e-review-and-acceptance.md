# Phase 3E 启动审计、实施矩阵与阻断差异报告

**历史启动审计结论保留：`BLOCKED`，不是 Phase 3E 验收通过。** 以下第 1—5 节保留启动时的阻断事实；本轮恢复开发的追加结果见文末第 6 节。当前仍为 `PARTIAL/BLOCKED`，不是发布凭据。

## 1. 范围、起点及依据

- 启动分支 `main`；启动和本报告生成时 HEAD 均为 `20c48b4c14cf14362c89556288f5bd6de2482f24`；本轮 **无本地提交、无 push**。仅新增本阻断审计报告，未改生产代码、测试、冻结定义或两个既有合成案例。
- 已读取 `docs/solar-pv/README.md`、`03-input-fields.json`、`05-formulas.json`、`05-formula-extensions.json`、`05-field-bindings.json`、`07-category-boundaries.md`、`08-requirement-traceability.csv`、`15-phase3-input-interface.md`、`17-phase3-implementation-plan.md`、`17-phase3-formula-execution-inventory.json`、`18-phase3-preimplementation-review.md`、`19-phase3-approved-implementation-contract.md`、`25-phase3b-runtime-and-phase3c-handoff.md`、`27-phase3c-runtime-and-phase3d-handoff.md`、Phase 3C/3D 报告、Phase 3D 代码、D2 注册表及两个合成项目的输入/方法/结果。**没有找到已提交的 Phase 3D→3E 专门交接文档**；以 Phase 3D 验收报告第 7 节及实际封存账簿为交接证据。
- 冻结公式总数 89；Phase 8 储能 7；原计划 Phase 3B/3C 已验收 36；Phase 3D 报告列出 22；Phase 3F 专属 3。按冻结计划及公式标识相减，本阶段归属 **21 条**（下表）。不能通过改变阶段归属补齐实现率。`F-DEBT-SERVICE`、`F-CASH-RECEIPTS`、`F-CASH-TAX-TOTAL` 等属于 3D 先决账簿，不重复记为 3E。
- **额外发现**：当前 `execution_inventory(Catalog())` 实际返回 Phase 3 仅 36 条 `IMPLEMENTED_TESTED`，另 46 条 `NOT_IMPLEMENTED`，其中含 3D 报告所列 22 条。3D 运行公式 kernel 和案例结果确实存在，但执行证据登记与报告声称的 22 条验收没有同步；本轮不得悄悄将其登记为 3E 已验证。

## 2. Phase 3E 冻结需求—公式—输入—输出—独立验证矩阵

需求主线：`R-S06-L121`（现金流）、`R-S06-L122`（NPV）、`R-S06-L123`（IRR）、`R-S06-L124`（回收期）、`R-S06-L125`（LCOE）、`R-S06-L126`（DSCR）、`R-S06-L127`（盈亏价、最差年）；对应交付约束 `R-CH16-02..08`。后者在需求矩阵中标为 Phase 5 **报告章节**，不擅自将其改写为 Phase 3E 功能阶段。类别：公式定义没有独立列举九类适用集合；按 `07-category-boundaries.md` 和各公式边界逐项目判定，不把工业屋顶自用套到地面全售电。以下 `屋/地` 仅指本轮两个 SYNTHETIC 案例可审计的适用入口，其余七类未经逐类验收，不声称通过。`债` 表示存在合同债务才适用，`股` 表示有可核验股东收付。所有行当前状态为 **NOT_IMPLEMENTED；下游因第 3 节阻断而不能验收**。

| 需求 ID | 冻结公式 ID | 案例适用性 | 输入与 Phase 3C/3D 来源 | 已批准配置/需具备数据 | 输出 | 独立参考方式 | 当前状态与证据 |
|---|---|---|---|---|---|---|---|
| L121 | F-PROJECT-CASH-FLOW | 屋/地 | 3C 净收益、3D 收付/OPEX/项目税/投资/营运资金、实际处置 | cash.method、收付期、项目税口径 | finance.project_cash_flow | 手工逐期六项加减、收付余额勾稽 | 未实现；B1/B2/B3 |
| L121 | F-PROJECT-PRETAX-CASH-FLOW | 屋/地 | 项目税后现金流＋仅实际所得税现金支付 | tax.project_income_cash_paid | finance.project_pretax_cash_flow | 税前/税后差额逐年复算 | 未实现；依赖 B3 |
| L121 | F-EQUITY-AVAILABLE-CASH-FLOW | 股，屋/地 | 3C 净收益、3D 融资后税/本息费/资产收付 | equity.distribution_fractions、资金储备及债务付现 | finance.equity_available_cash_flow | 不含股东分配的融资本息现金桥 | 未实现；B2/B3/B4 |
| L121 | F-EQUITY-INVESTOR-CASH-FLOW | 股，屋/地 | 股东真实投入、分配、退出凭据 | 出资、分配、退出及留存边界 | finance.equity_investor_cash_flow | DIV＋EXIT－EQ、对照现金账户 | 未实现；B4 |
| L121 | F-CASH-FUNDING-BALANCE | 股，屋/地 | 3D 债务＋权益可用现金、投入和分配 | equity.minimum_cash_reserve、期初现金 | checks.cash_closing | OPEN＋可用流＋投入－分配 | 未实现；B4 |
| L122 | F-NPV | 屋/地，项目/股 | 上述年度现金流 | 原字段项目/权益折现率、time.cashflow_timing | finance.npv | 每年用独立 Decimal 求和 | 未实现；B1–B5 |
| L122 | F-DATED-NPV | 有实际日期时 | 上述按日现金事件 | time.day_count、共同估值基准、显式折现率 | finance.dated_npv | 年分数及逐事件折现表 | 未实现；B4/B5 |
| L122 | F-NOMINAL-REAL-RATE | 名实转换适用时 | 原折现率与一般通胀 | 同税/风险币种，原一般通胀率 | finance.nominal_discount_rate | (1＋r_real)(1＋π)－1 | 未实现；B5 |
| L123 | F-IRR-PROJECT | 屋/地 | 真实税前/税后无杠杆现金流 | irr.* 已注册参数，实际案例未给 | finance.project_irr_root_set | 有理多项式隔离＋根回代 | 未实现；B1/B2/B5 |
| L123 | F-IRR-EQUITY | 股，屋/地 | 真实股东收付 | irr.*、明确日期及边界 | finance.equity_irr_root_set | 独立根隔离＋残差及多根检查 | 未实现；B3/B4/B5 |
| L124 | F-CUMULATIVE-CASH-FLOW | 屋/地，项目/股 | 已审计现金流数组 | 建设期为累计起点 | finance.cumulative_cash_flow | 逐期独立前缀和 | 未实现；B1–B4 |
| L124 | F-STATIC-PAYBACK | 屋/地，项目/股 | 未折现累计与首个回收期 | time.financial_end_year、插值口径 | finance.static_payback_years | 首次负转非负、手算年内插值 | 未实现；B1–B4 |
| L124 | F-DISCOUNTED-CUMULATIVE-CASH | 屋/地，项目/股 | 同口径已折现现金流 | 项目/股东各自折现率 | finance.discounted_cumulative_cash | 逐期折现前缀和 | 未实现；B1–B5 |
| L124 | F-DYNAMIC-PAYBACK | 屋/地，项目/股 | 折现累计与首个回收期 | 同 NPV 折现时点 | finance.dynamic_payback_years | 首次交叉＋折现年度插值 | 未实现；B1–B5 |
| L125 | F-LIFECYCLE-COST | 屋/地 | 3D 无杠杆投资、更新、OPEX、非所得税/营运、实收处置 | 原税前所得税 LCOE 边界 | lcoe.project_cost_annual | 逐期成本加减独立复核 | 未实现；B2/B3 |
| L125 | F-LCOE | 屋/地 | 3B/3C 同边界年度交付量、上行生命周期成本 | lcoe.discount_rate | finance.lcoe | 同年分别折现成本和交付 kWh | 未实现；B2/B5 |
| L126 | F-CFADS | 债，屋/地 | 3C 现金收益、3D 融资后税/运营付现/强制更新 | cfads.method、贷款协议范围 | debt.cfads | 偿债前逐项桥接、无提款 | 未实现；B2/B3/B4 |
| L126 | F-DSCR | 债，屋/地 | CFADS 与 3D F-DEBT-SERVICE 应付账簿 | cfads.method、服务期 | debt.dscr | 同期逐笔应付合计后作比 | 未实现；B3/B4 |
| L127 | F-BREAK-EVEN-PRICE | 有可调整价格的屋/地 | 候选价→3C→3D→3E 整链 | break_even.*、唯一选中单价及来源 | sensitivity.break_even_price_roots | 独立价格域隔离＋每候选全链重算 | 未实现；B1–B5 |
| L127 | F-WORST-CASH-YEAR | 屋/地，项目/股 | 完整逐期现金流 | risk.cash_year_scope、建设/运营范围 | risk.worst_cash_years | 独立 argmin；保留并列 | 未实现；B1–B4 |
| L127 | F-INVESTMENT-HURDLE-GAP | 有审批门槛才适用 | 已算评价指标与明确目标 | 决策目标原输入及口径 | decision.metric_gap | 算值－目标；方向按指标 | 未实现；指标及目标均未验收 |

上表中的 `L121..L127` 是 `R-S06-L121..R-S06-L127` 的缩写；`B1..B5` 为下节阻断。每个公式的**完整数学式、所有符号/下标、单位、版本**只能以 `05-formulas.json` 和有效扩展定义为准；本矩阵不替换 89 条冻结定义。验收证据列目前只有失败的上游证据，**不存在可标为 PASS 的 Phase 3E 公式数值参考**。

## 3. 启动复核中的关键差异及下游影响

### B1 — 屋顶应收余额为负，收款桥重复把节省记入发票应收

`financial_ledger.py:209` 在 `cash.self_use_treatment=INCREMENTAL_AVOIDED_EXPENDITURE` 时把自用节省加进 `other_cash` 形成 `revenue_cash_receipts`，但以 **开票额减整个收款额** 滚动 `accounts_receivable_closing`。屋顶案例运营年 1：到账桥 `1,956,400 CNY`，推算对应开票外售 `350,400 CNY`，差额恰为自用节省 `1,606,000 CNY`；应收余额为 **`−1,606,000 CNY`**，第 25 年为 **`−32,606,396.19980696429791600065 CNY`**。0 期应收非负；在全额当期收款设置下不能由应收结清解释该负债。冻结 `F-CASH-RECEIPTS` 明示自用避免购电不是伪造发票。3E 如照搬该“应收变动”求 `ΔW` 会严重双计。需确定与批准的收款/营运资金账簿一致的修正路径；不能在 3E 私下截零或篡改 3D 历史结果。

### B2 — 两案例资产更新已资本化，但上游现金投资账簿均未记更新付款

`financial_ledger.py:120-143` 将更换成本入资产并重启折旧，`financial_ledger.py:195` 的各年 `capex_cash_paid` 却仅来自原始 `capex.total × cash.capex_payment_fractions[y]`。每个案例原始更换计划第 12 年逆变器 `190,000 CNY`、第 15 年组件 `720,000 CNY`；这两年的 3D `capex_cash_paid` **均为 0**，投资付款余额也为 0。资本化原值不是付现凭证；原 `assets.replacements.cost` 也没有可推断的实际付款日期。冻结束期的项目流、LCOE、CFADS 和盈利电价都要求正确处理这些现金时点。若 3E 把成本直接视作当年已付，违反“严格复用 3D 收付账簿”；若不记又漏掉合计 `910,000 CNY/案例` 的潜在资本现金支出。需要授权明确上游收付账簿的处理，而不是在 3E 复制投资算法。

### B3 — 已算融资后税基，但唯一所得税现金账簿仍按无杠杆项目税基计算

`financial_ledger.py:203-208` 同时计算 `taxable_income_project` 和 `taxable_income_equity`，却只用 `project_base` 求 `income_tax_accrual`、税损滚动、`income_tax_cash_paid` 和 `cash_tax_total`。屋顶案例运营年 1 的两税基分别为 `1,793,241.8867924528301886792453` 和 `1,743,441.8867924528301886792453 CNY`；地面分别为 `569,676.8867924528301886792453` 和 `513,201.8867924528301886792453 CNY`。当前税额分别为 `448,310.471698113207547169811325` 与 `142,419.221698113207547169811325 CNY`，均是项目税基衍生；没有独立的融资后实付所得税。按案例声明 25% 税率作**纯诊断差额**分别为 `12,450`、`14,118.75 CNY`（非实际应缴税、未处理跨年税损）。冻结 `F-EQUITY-AVAILABLE-CASH-FLOW`、`F-CFADS` 要求融资后税款，不能把项目税款复用后称为股东税款或擅自重算第二份 3D 税务账簿。项目所得税前后口径也需可证的独立账簿。

### B4 — 没有可验证的股东分配及 CFADS 协议控制

两个 3D 案例的方法配置均缺 `equity.distribution_fractions`、`equity.minimum_cash_reserve`、`cfads.method`；输入 `finance.cfads_definition=PHASE3E_DEFERRED`。3D 年账有债务提款、本息应付/实付，却没有股东逐期投入、实际分配、受限储备和退出收付。`finance.debt_ratio` 不能代替股东入资事件；`F-CASH-FUNDING-BALANCE` 不能凭“剩余资金全分红”自动平账。缺协议边界时股东 IRR 与 DSCR 不能以仿真数值冒充验收值。

### B5 — 两案例没有已批准的折现、求根与价格搜索实参

两份原输入均缺 `finance.project_discount_rate`、`finance.equity_discount_rate`；现有 `finance.shareholder_cost=0.08` 不是自动映射为所有项目/股东/实际/名义折现率的许可。两份方法配置均缺 `irr.minimum_rate`、`irr.maximum_rate`、`irr.root_tolerance`、`irr.method`、`irr.maximum_degree` 与 `break_even.minimum_price`、`break_even.maximum_price`、`break_even.price_tolerance`、`break_even.method`、`break_even.maximum_iterations`。这些名称在已经批准的 D2 `method_config.py:106-118` 注册过，但案例 **没有提供经校验的值及来源**。不能填一个惯常 8% 或自选搜索域取得 NPV、IRR、LCOE、动态回收期和盈亏电价 PASS；价格变量的权属与税/结算重算也未获本案例输入证据。

## 4. 已执行的只读数值与保护验证

- Python `Decimal` 对两个已封存 `result.json` 调用现有 `validate_result(result, Catalog())`，**2/2 哈希和统一契约可验证**。按原输入 `assets.replacements` 独立求和，各为 `190,000＋720,000＝910,000 CNY`，对照年 12、15 现金付款均为 0；独立按明确 25% 税率比较首年两个税基，仅作差异诊断，未声明为真实税务结果。屋顶应收为负的断言得到确认。此前脚本曾因读取嵌套字段方式及 Decimal 精度过严失败，调整读取结构和 `1e-20` 比较容差后通过；未修改生产结果或预期。
- 两项目的 3D `result_hash`：屋顶 `c4c14ffb9c426e8744863c2c06d5a47975c3de0681b697b1f344d8682584fb96`；地面 `407f04f94adeebd5fe1d65dfa6a99c3a6ec955d87aa592ac4f15760ac63f8af5`。内含的 3C 封存结果 hash 分别为 `7eee9f80f9633a4e93905f2df7bafa9896658020c67069b5276e16f259534a50`、`6f070c327912973efd79f5cb50a705d4422990132aa28701b1e6fe2a5e6ae616`。这只证明引用/哈希有效，不证明财务现金流正确。
- 只读基线保护：`phase3c-startup-state.json` 中 288 条路径重算 SHA-256，**286 匹配、2 不匹配**，不匹配的仅 `reports/validate.json` 和 `reports/validate.md`，属于本轮启动前已有工作区差异。未调用可能改写它们的生成器。
- 六个既有工作区文件本轮起始 SHA-256（按文件顺序）：`packages/skills/wangbin-receivable-analyzer/SKILL.md` = `8a5ee4eb54a4f6a08d3ab7cccf792c12d5f01ab3fb4ab0de8dc926149087a945`；`manifest.json` = `0a9459ab33f0f3bbc1c538535b994218e6ad92792901a39c3e4e94eaf777762b`；`products/catalog.json` = `d74f3fa9f00184ee64f8452862958c3ef11f7848378ed42657e4b5fbc91def27`；`reports/workbuddy-upload-list.md` = `6d0df16f21a4cf7a3a87eef1b90fb2f7d26fd1457f124066707281f9ff0ec586`；`reports/validate.json` = `42765dae553254369311f3d4e7d2d3ab6f3cf0f8858a1c0e587debfea809d1ba`；`reports/validate.md` = `2c3f7cd41671f2af1cd9f5688ae4e3779d92390260cdb43299457bcedb2060e3`。本轮结束前须再次核对。启动暂存区为空；六文件已有工作区差异，不应称工作区 clean。

## 5. 尚未交付与授权请求

**未交付：21 条 3E 公式生产 kernel、两个案例逐期项目/股东现金流、真实 NPV/IRR 根及残差、LCOE、CFADS/DSCR、回收期、盈亏电价、独立参考矩阵、CLI/API 整链运行、3E 综合回归和提交。** 因此无法生成任何财务数值或宣布 `PHASE3E_*_PASS`；原正式发布/四文件/平台门禁不变，3F、3G 和 Phase 4+ 均未开始。不存在可据以形成数字化的 Phase 3F 输入接口，当前只能提供上游 3C/3D 的原封存身份与账簿字段。

需用户批准的前置决定：**是否允许在 Phase 3E 之前重新打开 Phase 3D 上游，以修正自用应收桥、资产更换的收付/时点和项目/融资后所得税分账，并补充具有来源的现有 D2 股东/CFADS/IRR/盈亏价配置及原冻结折现输入？** 这不是提出新产品需求；但它超出本轮“不得重新实现 Phase 3D 已验收算法”的权限。在明确批准及重新验收之前，保持 `BLOCKED`，不作隐式修复、不制作替代案例、不提交假 PASS。

## 6. 本轮恢复开发追加记录（2026-10-31）

### 6.1 起点、范围与实现

- 实际起点：分支 `main`，HEAD `6823f740b9d34647a13c5cdc874d90a23e0bcd7e`；启动时暂存区为空。六个既有工作区差异文件未纳入本轮修改或暂存。
- 新增 `calculation/financial_metrics.py`：严格按 Catalog 的 21 个 Phase 3E ID 提供 Decimal value-only kernel；缺输入返回 `BLOCKED_MISSING_INPUT`，不补零、不制造日期、股东收付、目标、终期现金或银行事件。
- 新增 `calculation/phase3e.py`：消费已验收 Phase 3D financial ledger，写回同一结果契约；输出 26 个期间；CFADS 在已有合成账簿输入下可计算，DSCR 遇任一期零债务服务返回 `UNDEFINED/ZERO_DEBT_SERVICE`；项目终期现金、权益现金流、日期事件、投资目标等缺口逐公式阻断。
- `cli.py` 增加 `phase3e` 命令，实际运行路径为 Phase 2 input + D2 methods + Phase 3C settlement → Phase 3D ledger → Phase 3E result bundle；没有覆盖既有结果目录。
- `execution_registry.py` 已发现 `financial_metrics` kernel；注册本身不改变“独立数值证据”要求。

### 6.2 21 条公式逐项状态

| 公式 | 引擎独立数值校核 | 两个既有项目结果 | 项目级原因 |
|---|---|---|---|
| F-PROJECT-CASH-FLOW | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺明确终期项目现金 |
| F-PROJECT-PRETAX-CASH-FLOW | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW` | 依赖项目现金流 |
| F-EQUITY-AVAILABLE-CASH-FLOW | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺终期权益现金 |
| F-EQUITY-INVESTOR-CASH-FLOW | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺真实出资、分配、退出事件 |
| F-CASH-FUNDING-BALANCE | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺期初主体资金和合法股东事件 |
| F-NPV | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW` | 项目现金流未确定 |
| F-DATED-NPV | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺完整有日期现金事件 |
| F-NOMINAL-REAL-RATE | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 案例缺受控折现/通胀字段，不补默认值 |
| F-IRR-PROJECT | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW` | 项目现金流未确定 |
| F-IRR-EQUITY | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺真实股东现金流 |
| F-CUMULATIVE-CASH-FLOW | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW` | 项目现金流未确定 |
| F-STATIC-PAYBACK | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW` | 项目现金流未确定 |
| F-DISCOUNTED-CUMULATIVE-CASH | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW` | 项目现金流未确定 |
| F-DYNAMIC-PAYBACK | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW` | 项目现金流未确定 |
| F-LIFECYCLE-COST | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺终期现金边界 |
| F-LCOE | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺完整生命周期成本边界 |
| F-CFADS | `IMPLEMENTED_NUMERICALLY_TESTED` | `CALCULATED`（合成条件） | 不代表真实合同核验 |
| F-DSCR | `IMPLEMENTED_NUMERICALLY_TESTED` | `UNDEFINED/ZERO_DEBT_SERVICE` | 账簿偿债服务期为零 |
| F-BREAK-EVEN-PRICE | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺全链价格重算输入 |
| F-WORST-CASH-YEAR | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW` | 项目现金流未确定 |
| F-INVESTMENT-HURDLE-GAP | `IMPLEMENTED_NUMERICALLY_TESTED` | `BLOCKED_MISSING_INPUT` | 缺用户投资目标 |

引擎校核文件：`tests/solar-pv/test_phase3e_financial_metrics.py`。该文件对 21 个 ID 覆盖正常 Decimal 算例，并覆盖缺失输入、IRR 无根、零交付、零偿债、价格求根、IRR 残差及边界行为；预期值由独立算术表达式给出，不调用生产 kernel 生成预期值。

### 6.3 两个 SYNTHETIC 项目实际结果

两项目均实际运行 API 编排并通过 `validate_result`：各 26 个期间、21 个 Phase 3E metric；结果均为 `PARTIAL`，不是 PASS。当前直接 API 运行得到：

| 项目 | 结果状态 | 21 条项目状态计数 | 结果哈希 |
|---|---|---|---|
| `industrial_rooftop` | `PARTIAL` | `CALCULATED=1`、`UNDEFINED=1`、`BLOCKED_MISSING_INPUT=19` | `13d96b5b77a57c063b2745407bd39f4fc8f66c10aaafb0ee23b83b4796d8467a` |
| `utility_scale_ground` | `PARTIAL` | `CALCULATED=1`、`UNDEFINED=1`、`BLOCKED_MISSING_INPUT=19` | `be22a49f20cbe5c15fabfac748bb926273c6ffd8d04ebfd5b2f9b3bf25cba224` |

CLI 实际运行 `industrial_rooftop` 返回 `status=PARTIAL`、`calculation_maturity=PARTIAL`、`instantaneous_payment_coverage=INDETERMINATE`，并写出 `result.json` 与 `result.sha256`。四笔 `2037-06-01/2040-06-01` 设备付款状态未被重算，仍保留 `INDETERMINATE`。

### 6.4 本轮验证回执

- `python -m pytest tests/solar-pv/test_phase3e_financial_metrics.py -q`：`10 passed in 0.11s`。
- `python -m pytest tests/solar-pv/test_calculation_contracts.py tests/solar-pv/test_calculation_review_regressions.py -q`：`56 passed in 38.59s`。
- `python -m pytest tests/solar-pv/test_financial_ledger_remediation.py -q`：`10 passed in 118.81s`；Phase 3D 账簿回归通过。
- API 两案例运行：2/2 通过统一结果契约校验；每案 26 期间、21 条公式状态已输出。
- CLI 工具运行：返回码 0；结果目录写入成功且 `result.sha256` 与 `result.json.result_hash` 一致。
- `python -m compileall -q services/solar-pv-engine/src/wangbin_solar_pv`：返回码 0。
- `python -m pytest tests/solar-pv -q` 本轮在工具时间上限内未完成（超时，未获得可靠 passed/failed 计数）；因此不宣称光伏全量回归通过。
- 288 文件基线复核：`286` 个匹配、`reports/validate.json` 与 `reports/validate.md` 两个既有偏差、0 个缺失；六个既有差异文件 SHA-256 与启动记录全部一致。
- 尚未在本轮宣称旧产品/Expert 全量回归；不得把历史 Phase 3D 回归数字拼接为本轮结果。

### 6.5 当前门禁与未完成项

当前正式门禁保持 `PARTIAL/BLOCKED`：终期资产现金、项目现金流、股东实际现金、期间主体非受限现金平衡、有日期现金事件、用户投资目标以及完整价格重算链仍缺原冻结所需输入或上游证据；DSCR 没有可用债务服务期。CFADS 仅为已声明的合成条件计算，不是融资合同核验。未修改 469 字段、89 条公式数学定义、281 条绑定、9 类边界、D2 Schema；未进入 Phase 3F/3G，未部署、未 push、未发布。

本报告追加记录不覆盖前述启动审计和原始阻断证据。提交前仍须执行：六个保护文件 SHA-256 起止核对、显式暂存本轮文件、Git diff 审查、生产源码编译及提交后真实 commit SHA 核验。

### 6.6 Git 闭环回执

- Phase 3E 实现及证据提交：`895536d60f5d6f79a8ad255073992430b3d9ff18`（本地 `main`，未 push）。
- 提交后工作区仍仅保留六个既有用户差异文件；本轮提交未包含其中任何一个。
- 提交后六个保护文件 SHA-256 与启动记录完全一致；288 文件基线仍为 286 匹配、2 个既有偏差、0 缺失。
