# Phase 3E P2-3A — 候选售价至真实 Phase 3D 账簿接线复核

## 结论和边界

**接线的独立 SYNTHETIC 验证通过；不能签收“分离 TMPDIR／pytest basetemp 下的光伏全量回归”，更不能宣称 Phase 3E 项目级通过。** 候选售价经已有受控选择器和真实 Phase 3C 重算后，分别以原件、候选输入及对应结算结果调用既有 `calculate_financial_ledger`。Phase 3D 原／候选结果通过身份、方法、来源和落盘校验；没有修改正式结果 Schema、冻结输入/公式/绑定、封存项目或 3B 算法；没有第二套收入、税费或融资计算器，也没有写入最终 NPV、盈亏平衡根或终期现金。

本轮代码的两个本地提交：`22fee0b75002dd30153e6b43ed4a6b43d818189a`（接线与独立夹具），`47f31d97ca824cc7441773d172c86ea6ade1b08c`（规范化财务身份与失败清理）。报告及证据位于本文件和同目录 `phase3e-p2-3a-financial-replay-evidence.json`；后者保存**完整** JUnit 测试 ID、计数、哈希、原／派生输入和结果哈希以及逐年财务指标。此报告不将 SYNTHETIC 数值外推到两个封存项目。

## 真正的计算链和隔离

1. 在独立 `SYNTHETIC` 工程中先经原有输入校验建立财务事实，生成只读 3B 物理结果及含完整原始资源/负荷数据的 D3 bundle；候选原子由 P2-1 选择器指定，重放调用既有 P2-2 路径，分别重算原／候选 3C，未修改 3B 物理结果。
2. 新增 `services/solar-pv-engine/src/wangbin_solar_pv/calculation/break_even_financial_replay.py`：核对各自的 Phase 2 输入、原子/情景来源、项目/方法、D3 和上游 3C 哈希，分别调用既有真实 3D 生产入口；复核规范化财务输入、完整方法及来源快照，验证结果后再发布到受界私有工作区；失败清理仅删除自有新建目录。
3. `tests/solar-pv/test_phase3e_financial_candidate_replay.py` 的独立 Decimal 预期从 `87600 kWh × 单价`、75% 收款、25% 应收、资产/费用、税率、期初亏损、融资条款推导，并回读已发布的原／候选 3D JSON 及结果哈希。负例覆盖混合候选、错误 3B/结算/方法、篡改规范化财务输入和不完整方法的无有效结果清理。夹具明确为 `SYNTHETIC/ASSUMED`；原来源 `SYNTHETIC-settlement`，候选价覆盖来源 `SYNTHETIC:p2-3a`，两者没有被混同。

## 独立数值证据（SYNTHETIC，金额 CNY）

| 指标（运行年 1，除另注） | 原价 0.4 | 候选 0.6 | 候选 0.8 |
| --- | ---: | ---: | ---: |
| 真实开票 | 35040.0 | 52560.0 | 70080.0 |
| 预计真实收款 | 26280.000 | 39420.000 | 52560.000 |
| 期末应收 | 8760.000 | 13140.000 | 17520.000 |
| 项目所得税税基 | 33940.0 | 51460.0 | 68980.0 |
| 权益所得税税基 | 33883.50 | 51403.50 | 68923.50 |
| 项目/权益结转亏损 | 60.0 / 116.50 | 0 / 0 | 0 / 0 |
| 项目/权益所得税计提 | 0 / 0 | 4365.000 / 4350.8750 | 8745.000 / 8730.8750 |
| 权益所得税付现 | 0 | 2175.43750 | 4365.43750 |
| 销项 VAT | 4031.15044247787610619469027 | 6046.72566371681415929203540 | 8062.30088495575221238938053 |
| 现金税合计（既有账簿） | 3888.15044247787610619469027 | 8079.16316371681415929203540 | 12284.73838495575221238938053 |

3D 冻结年度结果没有单独 `vat_cash_paid` 键；VAT 实付由原有 `cash_tax_total - income_tax_cash_paid` 桥接复核，不添加字段。进项 VAT 均为 143；建设期真实 capex 计提/付现 1130、债务提款 565、营运资金增加 200；运行年 1 利息计提/付现均为 56.50、本金应付/实付 565、营运资金回收 200。这些未被候选价格虚构或重复计入。运行年 1 `phase3e_cashflow` 仍为 `null`，并非求根或折现现金流。

原 Phase 2 输入哈希 `211edac7e893cd2fc801abb7dcb51343f65028843ccad79f59bcb2c510645a5d`；候选 0.6 与 0.8 分别为 `4da2ab157ccc0085d0d3849f65a17399fa2233d899d55974856884fcd0982190`、`3bc3fc9576b5e009b5f3d02cab4ab3c0b70dedc231040d9d13b1f5325bd54336`。原/候选 3C 哈希分别 `ac47f61449b164b37027c47e93c211d7ebe9d57f9105d4ebcd66c9e277c1a8cc`、`f088b629adb1964f1ff4340ac4188d03c45c858a8ec48112b973f9fbcb479cdb`（0.6）或 `ee24f8dbd773e8ac732f2c01424af505485851133e86f007815997405b873a35`（0.8）。原 3D `b4b312633e2501b14d73953e93fbcbb7572f245b7774dafe586f8703526e5d61`、候选 3D `b95c2e08ac60b8a5ecda39562230052f3de59cd8f49412ad842c274b8b6dd1f3`（0.6）/`36b4eb66f7db92923d63e11ce8a9a405ccc444f2a0dfcdb5c3ea6b053a57dac2`（0.8）。重复 0.6 的候选 3C/3D 身份和结果一致，不同价格不同；原 3D 不变。

## 各次真实回归与目录例外

| 归档 JUnit（`reports/solar-pv/phase3e-p2-3a-evidence/`） | 结果 | 退出码 |
| --- | --- | ---: |
| `focused-initial-error.xml` | 1 error：财务字段在生成 3B 后才补入，物理输入守卫拒绝；改为先生成合法输入 | 1 |
| `focused-vat-assertion-failed.xml` | 1 passed、1 failed：测试期待不存在的 `vat_cash_paid`；改核已冻结现金税桥 | 1 |
| `focused-first-pass.xml` / `focused-pre-review-pass.xml` | 各 4 passed；后一轮增补身份负例 | 0 / 0 |
| `focused-final.xml` | **5 passed**（最终代码，含已发布结果回读及失败清理） | 0 |
| `legacy-pre-review-pass.xml` / `legacy-separated-final.xml` | 各 **109 passed、5 skipped**；后者最终代码且 `TMPDIR` 与 `basetemp` 分离 | 0 / 0 |
| `solar-separated-failed.xml` | **4130 passed、2 failed、6 skipped**；最终代码，`TMPDIR=p2-3a-solar-final-workspace`、`basetemp=p2-3a-solar-final-temp` | **1** |
| `solar-compatible-final.xml` | **4132 passed、6 skipped**；最终代码，`TMPDIR` 和 `basetemp` **同为** `p2-3a-solar-compatible` | 0 |

分离目录全量的两个失败均为**既有 P2-2** `test_phase3e_candidate_replay.py` 中的 `test_real_replay_changes_only_one_atom_and_runs_both_3c_calculations`、`test_future_price_row_with_no_settled_energy_does_not_publish_candidate`：前者实际 `BREAK_EVEN_SCRATCH_OUTSIDE_WORKSPACE`，后者期待 `BREAK_EVEN_PRICE_NOT_CONSUMED`、实际先抛 `BREAK_EVEN_SCRATCH_OUTSIDE_WORKSPACE`。没有删除、跳过、改写测试或掩盖红色 JUnit。兼容布局仅表明该原有 P2-2 守卫依赖 pytest 临时目录的相对布局；**它不符合分离目录要求，不可冒充严格布局全绿**。另外有一次光伏全量中途停止，无完成 JUnit，不计入成功回归。Windows 符号链接权限导致兼容光伏全量 6 skipped，旧产品最终 5 skipped；完整测试 ID、跳过原因与每个归档 SHA-256 在证据 JSON。

## 独立财务来源审核及未闭合门禁

- **`finance.cash_flow_basis` 未闭合**：两个封存 SYNTHETIC 项目的 `project.cashflow_tax_basis=both`，折现率来源 `UNVERIFIED`；P2-3A 的控制选择器 `basis=项目税后` 及真实 3D 哈希仅证明账簿重算和控制身份，不能证明封存项目已选定唯一项目/权益、税前/税后、可折现的 Phase 3E 现金流口径。
- **`finance.project_terminal_cash` 未闭合**：缺实际资产处置净收款金额/时点、税务现金事实以及排重来源。账面折旧残值和更新 salvage 不等于已收到处置款；屋顶和地面封存账簿末年已分别回收营运资金 50000、120000 元，不能再次当终期现金。未新增任意现金注入接口，也未修改两封存项目。
- 两封存项目级门禁维持 **`PARTIAL/BLOCKED_MISSING_INPUT`**；报告中的 `BLOCKED_MISSING_TERMINAL_CASH_SOURCE` 仅为审计描述、不是生产结果枚举。未经完整财务来源校验，不做 NPV 或盈亏平衡售价求根、不声称价格残差 PASS，也不进入 P2-3B/P2-4/P2-5/3F/3G。

## 完整性、版本与交付

开工时六个已有用户差异文件的 SHA-256 与前轮 P2 机器证据一致，收口复核时六个 SHA-256 仍一致；文件名及始末值见证据 JSON。288 项旧基线核对为 **286 匹配、2 项既有差异（`reports/validate.json`、`reports/validate.md`）、0 缺失**。暂存区在代码阶段为空；报告归档仅增加本轮文件，不触碰用户文件、原始导出、原始 D3 bundle 和只读 3B。未 push、部署或发布；报告提交的自身 SHA 无法在同一提交中自引用，以交付时 `git rev-parse HEAD` 为准。
