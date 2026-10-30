# Phase 3D 限定范围财务账簿修复与前置验收（2026-10-30）

**判定：账簿算术已独立对平；前置整体状态 BLOCKED。** 本记录不代表 Phase 3E、真实项目税务或替换设备资金来源验收通过。仅修复 Phase 3D 已确认的三类财务账簿缺陷，并用既有输入与 D2 方法补齐两个 SYNTHETIC 案例的受控配置；冻结字段、公式、绑定、分类与 Phase 3B/3C 内核未改。原 `reports/solar-pv/phase3d-cases/` 整目录及原 Phase 3D 验收报告保持不变；修复后案例另存于 `reports/solar-pv/phase3d-repaired-cases/`。先前 `phase3e-review-and-acceptance.md` 是独立、未提交的阻断审计文件，不纳入本轮提交。

## 修复原因与账簿边界

1. **F-CASH-RECEIPTS**：旧实现把屋顶自发自用的避免购电支出作为 `other_cash` 收入，却只把外售开票作为应收借方，因此第 1 年开票 350,400、所谓到账 1,956,400，形成 −1,606,000 元虚假应收。新实现把 `self_use_avoided_expenditure` 和上游应计收益独立保留；在 `OWNER_AVOIDED_COST`、`INCREMENTAL_AVOIDED_EXPENDITURE` 情景下，只以外售发票及同一应收账簿的实际到账滚动期初/期末应收。合同 PPA 情景按其独立的开票边界处理。按 D2 `cash.collection_fractions` 和 `cash.terminal_collection_fraction` 分别预测当期及期末收款；自用节省**不**被登记为客户/电网到账，也不凭空填入后续项目实体现金。对账：期初应收 + 本期开票 − 同一账簿实收 = 期末应收，含第 25 年终期回收。
2. **F-CAPEX-ITEM-AMOUNT、F-CAPEX-TOTAL、F-CAPEX-PAYMENT-BALANCE、F-ASSET-BOOK-VALUE**：旧资产更换记录导致第 12 年逆变器 190,000、第 15 年组件 720,000 元资本化，但 `capex.items` 中不存在对应付款凭证。旧账把两案例的 910,000 元资产加入了折旧基础，却没有本金应付/付现桥。新合成输入按原资产 ID、金额及更换年份逐项增加明确标记 SYNTHETIC 的现有 `capex.items` 支付行，含付款日、币种、来源和输入哈希；生产账簿先在生效年计提应付，再按**付款日期**结算，禁止从资本化自动推出付现；缺失或不唯一的支付来源报错，不当作已付或免费。第 12、15 年付款假设分别为 190,000、720,000 元；跨年付款的独立用例验证应付在支付前不归零。
3. **F-TAXABLE-INCOME-PROJECT、F-TAXABLE-INCOME-EQUITY、F-INCOME-TAX-ACCRUAL、F-TAX-LOSS-BALANCE、F-TAX-CASH-BRIDGE、F-CASH-TAX-TOTAL**：旧结果虽有两种税基，`income_tax_accrual`/`income_tax_cash_paid` 却直接使用无杠杆项目税基。新结果分别滚动项目反事实情景、融资后情景的亏损、计提、预测实付、应缴余额和现金税，融资后利息只扣一次，资本化利息不作为当期费用；`income_tax_cash_paid` 和 `cash_tax_total` 只代表融资后主体**单份合成预测付款**，`*_project` 是项目评价反事实、不是第二份法定付款。账面计提与预测付现按 D2 `cash.tax_payment_fractions` 独立滚动。不存在真实税务申报/法定实缴证据，不得宣称两份真实义务。

以上数据血缘：Phase 3C 封存 `settlement.json` 的各年 `revenue.year.N.details.ledger` → 原 `input.json`/修复后输入中的 `capex.items`、`assets.replacements`、`opex.items`、税率、折旧和融资字段 → `methods.json` 的受控方法 → Phase 3D 新 `result.json`。未更改 89 条冻结公式的数学定义、281 个绑定或 469 字段 Schema。两个原始 `settlement.json` 的 result hash 与新财务结果中 `upstream_settlement_result_hash` 一致。

## 两案例生命周期逐期核对（单位：CNY）

| 项目 | 屋顶案例修复前 → 后 | 地面案例修复前 → 后 |
| --- | ---: | ---: |
| 首年开票 / 实收 | 350,400 / 1,956,400 → 350,400 / 350,400 | 784,750 / 784,750 → 784,750 / 784,750 |
| 首年末应收 | −1,606,000 → 0 | 0 → 0 |
| 首年自用节省（非客户到账） | 错计入收款 1,606,000 → 独立 1,606,000 | 0 → 0 |
| 第 12 年更换资产 / 当年付现 | 190,000 / 0 → 190,000 / 190,000 | 190,000 / 0 → 190,000 / 190,000 |
| 第 15 年更换资产 / 当年付现 | 720,000 / 0 → 720,000 / 720,000 | 720,000 / 0 → 720,000 / 720,000 |
| 建设期付款 / 生命周期总 CAPEX 付款 | 1,660,000 / 1,660,000 → 1,660,000 / 2,570,000 | 2,510,000 / 2,510,000 → 2,510,000 / 3,420,000 |
| 首年项目税基 / 融资后税基 | 1,793,241.88679245 / 1,743,441.88679245（旧未分账）→ 各自分账 | 569,676.88679245 / 513,201.88679245（旧未分账）→ 各自分账 |
| 首年所得税计提及预测实付（单份主体） | 448,310.47169811 → 435,860.47169811 | 142,419.22169811 → 128,300.47169811 |
| 生命周期所得税预测实付（单份主体） | 7,511,006.18550264 → 7,417,631.18550264 | 1,980,799.97211585 → 1,797,256.22211585 |
| 反事实项目口径所得税付现（仅情景） | 原主体付款错误使用该值 → 7,511,006.18550264 | 原主体付款错误使用该值 → 1,980,799.97211585 |
| 第 25 年应收 / CAPEX 应付 / 主体所得税应付 / 债务 | 原屋顶应收 −32,606,396.19980696；其余账簿各自存档 → 0 / 0 / 0 / 0 | 原应收 0；其余账簿各自存档 → 0 / 0 / 0 / 0 |

修复后两个案例均为建设期＋25 年，共 26 期；屋顶/地面运营现金 OPEX 分别为 4,033,191.91698555 / 4,033,191.91698555 元，生命周期折旧 1,101,420 / 1,578,420 元，第 25 年资产账面价值 468,880 / 521,880 元，期末 VAT 留抵 142,695.46591705 / 0 元，生命周期单份主体现金税（含 VAT 和原定义的其他现金税）8,307,746.92776296 / 3,118,143.63255797 元。原始逐期账簿保存在旧 `result.json`，修复后逐期账簿保存在新 `result.json`；两者的逐年货币差额以独立参考文件为准，不以此处截断显示的十进制小数作为机器校验值。

逐年**全部 25 年**的修复前后开票/到账、应收、应付、CAPEX 付款、两种税基/税额均记录在两个 `independent-reference.json` 的 `annual_comparison`。该文件的 `changed_columns` 给出每项变动的期数与**生命周期合计增量**（注意应收余额属于存量，其逐年数值之和不应解释为现金）；屋顶收款全生命周期减少 32,606,396.19980696，恰为以前错计的自用节省。两个案例 CAPEX 付款各增加 910,000；主体所得税各下降 93,375 和 183,543.75；其他现金税按既有 12% 场景跟随变化，各下降 11,205 和 22,025.25。上游收入及折旧金额未因本修复重新计算。

独立参考以 `Decimal` 从**输入 CAPEX 行与日期**、原更换资产事件、原 OPEX 行与 VAT、Phase 3C 封存逐年收益计算对应值，没有调用 Phase 3D 公式内核；每案例 610 项逐期对账通过，比较容差 1e−9 CNY。核查含全生命周期开票＝客户到账、终期应收＝0、建设期及更换期 CAPEX 资本化＝实际付款＋应付变动、每期 `capex_payment_residual=0`、两份税基与亏损/计提/付款/应缴的各自滚动、单份主体实缴，及原更换资产 `depreciation.records` 对应新增资产入账。对应的原/新结果 hash、原始收入结果 hash 和输入/方法 hash 已写入各自参考文件。均为 SYNTHETIC 数值证据，不是实际电站的资金或税务凭证。

## 受控配置与仍未满足的资金来源

新 `input.json` 中的已有字段：`finance.project_discount_rate=0.08`、`finance.equity_discount_rate=0.08`（仅复用本案例原 `finance.shareholder_cost=0.08` 做一致的合成情景比较，不表示已核验 WACC）；`project.price_basis=nominal` 与上游结算同口径；`project.cashflow_tax_basis=both`；原 `project.evaluation_date=2026-10-29` 是既有折现基准记录，不做静默替换；`finance.cfads_definition=OPERATING_CASH_AFTER_TAX_MANDATORY_CAPEX` 只定义方法，不是计算结果。原 D2 `time.cashflow_timing=YEAR_END`、`time.day_count=ACT_365F` 保持原值。方法新增 `equity.distribution_fractions` 逐年 1、`equity.minimum_cash_reserve=0`、`cfads.method=OPERATING_CASH_AFTER_TAX_MANDATORY_CAPEX`；IRR 采用已注册有理根隔离方法、搜索域 [−0.5,1]、根精度 1e−8、最高次数 25；盈亏电价采用已注册分段仿射全根搜索方法、搜索域 [0,2] CNY/kWh、精度 1e−8 CNY/kWh、256 次预算。以上边界值均是**明确选择的 SYNTHETIC 计算域/资源预算，不是行业默认值，也不保证真实项目根一定落在域内**；实际找根/完整性/残差验收留在未启动的 Phase 3E。每项方法记录含注册单位、适用类别、来源、版本、status=ASSUMED，整体 `MethodConfig.from_dict` 已校验 Schema；输入经 `validate_export`，`calculate_financial_ledger` 输出经 `validate_result`。输入和方法内容 hash：屋顶 `cb71039535b28cf25d512dd5d3179e02ae32c6e0f20ac22e0b8708ad264f44ed` / `c1c51510d8678b4a4ce22950af5ec2e16381c98c1789244c9a6092e7ed241153`；地面 `fcfffc8d01385e97580faf7778258423ce5481324dfd866bfc5283fb3c5d2843` / `9429bf5612e1d41e8c1383f38d3601956e93ef16e3ba6e6e8a223afd48fd07dd`。

**资金来源仍 BLOCKED：** 更换付款是有哈希的合成支付日/金额假设，并不构成资金到位证明。原 `debt.drawdown_basis=CAPEX_PROPORTIONAL_SCENARIO` 只生成建设期借款，不能冒充后续设备更换贷款；Phase 3D 无完整主体现金余额/股东注资账簿，也不能以自用节省充当收到的替换资金。尤其分配比例为 1 的情景不预留内部现金，不可据此断言更换年度已有足额可用资金。没有用户已核实的新增出资或其他来源，**资金覆盖率/支付可行性不通过**；本报告只确认付现假设在账簿内的数学一致性。Phase 3E 不得把该缺口当作已解除；需获得现有契约范围内可核验的资金依据或后续批准，不能自行新增融资字段、模型或填入“运营现金”默认值。

## 回归和工作区门禁

- 新增限定范围定向用例：开票/自用隔离、应收全生命周期、更换资产入账与日期付款、跨期应付未付、项目/融资后所得税和实付分账；缺少支付来源时阻断，而不伪造付款。
- 光伏项目全量回归（包含 Phase 3D 新增 10 个定向用例及 Phase 3C 上游兼容测试）：`PYTHONPATH=services/solar-pv-engine/src;services/document-engine/src python -m pytest tests/solar-pv -q --disable-warnings --tb=short`，同一次最终进程退出码 0，**4069 passed、6 skipped**，耗时 5529.38 秒。跳过项仅为当前 Windows 符号链接权限限制，不与本轮变更相关。旧 WorkBuddy 产品及 Expert 完整根目录回归（排除已单独覆盖的 `tests/solar-pv`）：`python -m pytest tests --ignore=tests/solar-pv -q --disable-warnings --tb=short`，退出码 0，**109 passed、5 skipped**，耗时 70.98 秒；5 个跳过同样为 Windows 符号链接不可用。不以历史 `4059 passed, 6 skipped` 代替本轮验证。两次运行的输出保存在 Hermes scratch，源代码在这两次运行期间没有后续修改；本记录是随后补写的报告。
- 六个既有差异文件始终不修改、不暂存：`packages/skills/wangbin-receivable-analyzer/SKILL.md` `8a5ee4eb54a4f6a08d3ab7cccf792c12d5f01ab3fb4ab0de8dc926149087a945`；同目录 `manifest.json` `0a9459ab33f0f3bbc1c538535b994218e6ad92792901a39c3e4e94eaf777762b`；`products/catalog.json` `d74f3fa9f00184ee64f8452862958c3ef11f7848378ed42657e4b5fbc91def27`；`reports/workbuddy-upload-list.md` `6d0df16f21a4cf7a3a87eef1b90fb2f7d26fd1457f124066707281f9ff0ec586`；`reports/validate.json` `42765dae553254369311f3d4e7d2d3ab6f3cf0f8858a1c0e587debfea809d1ba`；`reports/validate.md` `2c3f7cd41671f2af1cd9f5688ae4e3779d92390260cdb43299457bcedb2060e3`。这六个 SHA-256 与 Phase 3E 审计结束/本轮启动核对值相同；终检仍须确认。288 个保护文件中仅两个既有 `validate` 差异，其余与原基线一致；这不表示工作区干净。
- Git 只允许显式暂存本轮生产代码、定向测试、两个新案例和本记录；不纳入前述六个文件、独立旧版案例或 `phase3e-review-and-acceptance.md`。本地 commit SHA 在门禁完成后填写到**仓库外**的提交回执，避免在被提交报告中循环引用自身哈希。不 push、不部署、不进入 Phase 3E。
