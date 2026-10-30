# Phase 3D 财务基础账簿开发与验收报告

**报告状态：`PHASE3D_FINANCIAL_LEDGER_PASS`**
**Phase 3D 门禁：`PHASE3D_FINANCIAL_LEDGER_PASS = PASS`**
**范围：仅 Phase 3D；没有实现 Phase 3E 现金流评价、NPV、IRR、LCOE、DSCR、CFADS、回收期或敏感性分析。**

## 1. 执行边界与 Git 状态

- 仓库：`F:\ideaWorkSpace\wangbin-workbuddy`
- 起始 HEAD：`0e52ee7d58b8de84bd165426796adcdb295cc54f`
- 当前报告生成时 HEAD（提交前）：`0e52ee7d58b8de84bd165426796adcdb295cc54f`
- 本轮提交：最终验收文件完成后显式暂存并本地提交；不 push。
- Phase 3E/3F/3G/Phase 4+：未开始。
- 四个用户保留文件的既有工作区修改保留；未编辑、未暂存、未恢复、未清理。
- 机器证据：`reports/solar-pv/phase3d-blocking-evidence.json`。

## 2. 冻结需求与公式范围

需求追溯范围：`R-S06-L119`、`R-S06-L120`、`R-S04-L078`、`R-S04-L079`、`R-CH14-01..06`、`R-CH15-01..05`、`R-CH16-01..03`。其中 `R-CH16-04..08` 的 NPV/IRR/回收期/LCOE/现金流评价边界不在本轮实现。

本轮实现的 22 条 Phase 3D 基础公式：

`F-TAX-EXCLUSIVE-AMOUNT`、`F-CAPEX-ITEM-AMOUNT`、`F-CAPEX-TOTAL`、`F-UNIT-INVESTMENT`、`F-ANNUAL-OPEX`、`F-OPEX-ESCALATION`、`F-STRAIGHT-LINE-DEPRECIATION`、`F-ASSET-BOOK-VALUE`、`F-TAXABLE-INCOME-PROJECT`、`F-TAXABLE-INCOME-EQUITY`、`F-INCOME-TAX-ACCRUAL`、`F-TAX-LOSS-BALANCE`、`F-TAX-CASH-BRIDGE`、`F-VAT-CREDIT-BALANCE`、`F-OTHER-CASH-TAXES`、`F-CASH-TAX-TOTAL`、`F-DEBT-BALANCE`、`F-DEBT-INTEREST`、`F-INTEREST-BALANCE`、`F-CASH-RECEIPTS`、`F-DEBT-SERVICE`、`F-CAPEX-PAYMENT-BALANCE`。

`F-CASH-FUNDING-BALANCE` 保持 `NOT_IMPLEMENTED_PHASE3E_UPSTREAM_CASHFLOW_REQUIRED`；不能在 Phase 3D 凭空构造项目/股东现金流来源。

## 3. 实现内容

### 3.1 CAPEX / OPEX

- 新增冻结公式 kernel：数量×单价、含税转未税、分项汇总、单位投资、年度 OPEX 和逐年 escalation。
- 每个 CAPEX row 校验 row ID、币种/汇率、数量×单价与声明金额勾稽、含税状态、VAT 可抵扣份额、支付年份和资产关联。
- 运营成本保留现金 OPEX 与未税可扣除 OPEX 的分离口径；资产更换不进入 OPEX。
- CAPEX 付款余额按建设期/运营期分期桥接，残余余额非零或超付会阻断。

### 3.2 资产与折旧

- 支持冻结的 `straight_line` 方法、原值、残值、折旧年限、启用年度、累计折旧和期末账面价值。
- 更换资产作为新的资本化增加、处置旧资产账面价值，并按新资产寿命生成折旧。
- 折旧不作为现金 OPEX；生成逐资产逐年明细。

### 3.3 融资与税费

- 支持冻结输入中的 `equal_principal`、`annuity`、`bullet`、`custom_schedule` 分支；逐期输出提款、应还本金、实付本金、应计利息、实付利息、资本化利息、费用、债务服务和期末债务。
- 现金支付比例、税损使用、折旧起算、VAT 退税等均从已经存在的 D2 方法参数读取；没有新增方法参数、默认值或行业规则。
- 所得税、税损、VAT 留抵/抵扣/现金支付、附加税和税收现金桥按独立账簿保存。
- 浮点舍入造成的极小 Decimal 负零仅在 `1e-18` 内归零；实质性负留抵会阻断。

### 3.4 Phase 3C 衔接与统一契约

- `financial` CLI/API 只消费已封存 Phase 3C `result.json`，校验 `project_id`、项目类别、上游结果哈希、上游非财务输入一致性和年度收益 ledger 完整性。
- 不重算发电、消纳、收入或交易费；Phase 3C 结果原始指标保留，Phase 3D 财务指标追加到同一 `solar-pv-calculation-result/1.0.0` 契约。
- 结果包含方法哈希、输入身份、来源快照、上游 settlement hash、公式快照、年度账簿、结果 hash 和 Phase 3E deferred 状态。
- 新 CLI：`financial --input --methods --settlement --output`；API `calculate_financial_ledger()` 与 CLI 结果 hash 一致。

## 4. 两个完整 SYNTHETIC 案例

案例文件位于 `reports/solar-pv/phase3d-cases/`，每个案例包含原始输入、方法配置、Phase 3C settlement、Phase 3D result、hash、独立参考和 acceptance。

| 案例 | 真实运行 | 账簿期间 | CAPEX 总额 | 独立参考 | 结果 hash |
|---|---|---:|---:|---|---|
| `industrial_rooftop` | API + CLI PASS | 26（建设期+25运营年） | 1,660,000 CNY | PASS | `c4c14ffb9c426e8744863c2c06d5a47975c3de0681b697b1f344d8682584fb96` |
| `utility_scale_ground` | API + CLI PASS | 26（建设期+25运营年） | 2,510,000 CNY | PASS | `407f04f94adeebd5fe1d65dfa6a99c3a6ec955d87aa592ac4f15760ac63f8af5` |

两例均明确标记 `SYNTHETIC`，不代表真实项目预测。独立参考未调用生产 ledger 函数，校核了 CAPEX 数量×单价和汇总、首年/第25年 OPEX escalation、26 个期间、CAPEX 付款余额归零、期末债务归零和上游 settlement hash 一致性。

## 5. 验证结果

- 生产源码编译：`PASS`（`costs.py`、`accounting_ledger.py`、`financial_ledger.py`、`cli.py`）。
- 回归阻断修复：`units.py` 明确拒绝 `24:00` 小时值；`test_units.py` 全部通过。
- 结果契约和方法配置校验：两个案例均 `PASS`。
- Phase 3D API 运行：2/2 `CALCULATED_SYNTHETIC`。
- Phase 3D CLI 运行：2/2 `CALCULATED_SYNTHETIC`；API/CLI hash 一致。
- 独立数值参考：2/2 `PASS`。
- 定向计算/契约回归：`89 passed`。
- Phase 3B 发电回归：`36 passed`。
- 旧 WorkBuddy 产品回归：`34 passed, 2 skipped`；跳过原因为 Windows 符号链接不可用。
- 全部太阳能回归：`4059 passed, 6 skipped`；跳过均为 Windows 符号链接权限不可用，未计入通过。
- `uv run --project services/solar-pv-engine` 无法建立完整项目环境，因为配置索引没有 `wangbin-document-cli==1.2.0`；未修改仓库依赖。
- 默认 Hermes Python 缺 pytest；pytest 仅安装到隔离运行环境，未修改 `pyproject.toml`、`requirements.txt` 或测试代码。

## 6. 保护检查与敏感信息

四个用户文件 SHA-256（起止核验值保持一致）：

| 文件 | SHA-256 |
|---|---|
| `packages/skills/wangbin-receivable-analyzer/SKILL.md` | `8a5ee4eb54a4f6a08d3ab7cccf792c12d5f01ab3fb4ab0de8dc926149087a945` |
| `packages/skills/wangbin-receivable-analyzer/manifest.json` | `0a9459ab33f0f3bbc1c538535b994218e6ad92792901a39c3e4e94eaf777762b` |
| `products/catalog.json` | `d74f3fa9f00184ee64f8452862958c3ef11f7848378ed42657e4b5fbc91def27` |
| `reports/workbuddy-upload-list.md` | `6d0df16f21a4cf7a3a87eef1b90fb2f7d26fd1457f124066707281f9ff0ec586` |

288 个基线保护文件中有 2 个当前工作区差异：`reports/validate.json`、`reports/validate.md`。二者位于 Phase 3D 文件集之外，本轮未编辑、未暂存、未恢复、未清理；其余保护文件 SHA-256 一致。四个用户保留文件的 SHA-256 起止一致。保护文件和本轮财务 artifacts 已做敏感信息检查，未发现凭据值。

## 7. 未实现项、边界与 Phase 3E 交接

- `F-CASH-FUNDING-BALANCE`、项目现金流、股东现金流、NPV、IRR、LCOE、DSCR、CFADS、回收期、敏感性全部明确 deferred；没有输出伪造数值。
- 真实项目税率、优惠、退税资格、融资合同和付款日期仍需真实来源；本轮案例假设不能作为生产默认规则。
- Phase 3E 接收本报告案例中年度 CAPEX/OPEX/税费/债务/营运资金和 Phase 3C 收益引用，不应再次计算收入或能源。
- 正式发布门禁仍不能替代真实项目证据、税法适用核验或 WorkBuddy 产品发布门禁。

## 8. 当前门禁

实现、独立数值校核、专项验证、完整太阳能回归和旧产品回归均通过，当前门禁为：

`PHASE3D_FINANCIAL_LEDGER_PASS = PASS`

提交时仅显式暂存 Phase 3D 生产代码、案例、证据和报告；不得暂存四个用户保留文件、`reports/validate.*` 或 `uv.lock`，不得 push。
