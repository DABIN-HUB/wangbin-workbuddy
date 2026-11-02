# Phase 3E-P2-4：盈亏平衡电价全链求解审查（部分交付）

**结论：P2-4A 候选 NPV(p) 全链回调已验收并本地提交；F-BREAK-EVEN-PRICE 正式求根保持 BLOCKED，P2-4B/C 的根集合证明及独立有根项目未实施。** 本报告不能作为盈亏平衡电价 PASS、无根结论或两份封存项目的财务结论。P2-4D 仅完成当前**部分交付**的最终回归与证据归档。起始 HEAD `89b69df1b5b67063b85f3294fbce274aa4bddffb`；P2-4A 提交 `50fb9e71f155c01e972a6980bb6cd67a1d29f528`。未 push、部署或发布。

## 1. 实施边界

- 新增 `services/solar-pv-engine/src/wangbin_solar_pv/calculation/break_even_project_npv.py`：对一个**非原价**、在 D2 范围内的合法候选，调用既有单原子 Phase 2/D3 派生、复用只读 3B、分别重算原价和候选价的 3C/3D，验证原始终期声明及字节，按真实候选身份重新绑定同一 `NO_DISPOSITION` 来源，分别运行既有 `calculate_sourced_project_npv()`；检查两份 canonical 3E 的 F-NPV、来源与结果哈希。3E 两份结果及执行回执先写入私有待发布目录，再将整个目录重命名；失败清理本次拥有的运行目录。不改原始输入或已发布结果。
- `calculate_sourced_project_npv()` 已有 SYNTHETIC 适用门禁；EVENTS 缺交易级对账仍由 `terminal_binding.py` 拒绝。此回调没有根搜索、根集证书或跨价缓存。候选恰等于原价时现有 replay 入口拒绝；本回调不将其伪造成邻近价格。正式结果仍遵循既有 `seal_result()`、`result_hash()`、`validate_result()`。
- 旧 `financial_metrics.py:381–412` 的 `_break_even()` 用**分段仿射样本现金流插值**，并非真实项目候选重算；本回调**不调用**它，受来源约束的 3E 指标继续非数值。但旧数学 `evaluate("F-BREAK-EVEN-PRICE", …)` API **仍可独立调用**，尚未提供全系统强制隔离；因此绝不将旧 API 的标量／样本结果认作正式根集合。未修改旧数学测试与冻结合同。

## 2. 根集门禁与数值

冻结定义是整个批准价格域内 NPV=0 的**集合（元素元/kWh）**，不是一个求得的价格。当前独立 SYNTHETIC 案例选 `tariff.periods.sale_price:flat`，结算 CNY、2025 价年、含税名义价格、项目税后、年末折现率 0.1；D2 声明域 `[0,2]` 元/kWh、价格区间容差 `0.000001` 元/kWh、最大 256 次、方法 `CERTIFIED_MONOTONE_RECALCULATION`。这些只是方法**声明及预算**，不是证明或已执行的搜索。完整候选搜索次数 **0**，货币 NPV 根残差容差尚未核准，故两个收敛残差均**未测得**。

真实重算的三个 SYNTHETIC 正 NPV 点（元）：0.4 → `146523.499597747385358004827…`，0.6 → `154652.522123893805309734513…`，0.8 → `162774.726468222043443282381…`。三个点不是全域无根证明。3C 价格影响须逐时段确认，3D 应税收益、收款比例、增值税留抵及所得税损失递推具有分段与跨期依赖；未经覆盖**整个闭区间**的合法性、连续性、严格单调性及税／结算跳变证明，不能排除多根、零平台或不可定义点。即使未来得到变号区间，也不能直接声称完整根集合。**没有独立有根 SYNTHETIC 案例；没有根区间、价格宽度残差、货币 NPV 根残差或独立求根参考。**保持正式 `BLOCKED_MISSING_INPUT / BLOCKED_MISSING_FULL_CHAIN_PRICE_RECALCULATION`，不返回 `NO_ROOT` 或成功单根；不得未经批准扩展状态枚举。独立 Decimal 对单次 0.6 候选 NPV 的误差断言 `<1e-55 元`，**不是求根残差**。

已归档的一次 L3 受控候选回执：0.4 原价 → 0.6 候选价；一次 replay，原价及候选价的 3C／3D／3E 各执行两次，回调 **647.6643597001676 秒**。候选输入、D3、3B、3C、3D、3E、终期来源 SHA 和两份 NPV 均在 `phase3e-p2-4-break-even-evidence/synthetic-price-0.6-execution.json` 以及机器证据中。不同独立生成的 SYNTHETIC 案例有不同来源及结果哈希，不跨案复用缓存。

## 3. 实际验收

| 门禁 | 当前最终代码的结果 | 证据 |
| --- | --- | --- |
| L1 新回调及无效来源 | **2 passed** | `phase3e-p2-4-break-even-evidence/l1.xml` |
| L2 选价／3C／3D／终期／NPV | **53 passed、1 skipped**（Windows 符号链接权限） | `phase3e-p2-4-break-even-evidence/l2.xml` |
| L3 光伏完整 | **4173 passed、7 skipped** | `phase3e-p2-4-break-even-evidence/solar-l3.xml` |
| L3 WorkBuddy/Expert 完整 | **109 passed、5 skipped** | `phase3e-p2-4-break-even-evidence/workbuddy-l3.xml` |

最终 L3 共 **4294 个唯一测试 ID**，见 `phase3e-p2-4-break-even-evidence/all-test-ids.txt`；L1/L2 是其聚焦子集，不重复相加。两个完整 L3 均为本地 A 提交后的同一生产代码，仅执行一次最终候选全量光伏。各次运行的 `TMPDIR` 与 `pytest --basetemp` 分离；原始完整 JUnit、命令、退出码和 SHA 在 `phase3e-p2-4-break-even-evidence.json`。早期单位校验错误的 **1 passed、1 failed** JUnit 以 `l1-superseded-unit-check-failure.xml` 保留，原因是把公式单位“元”误比作币种 `CNY`，修正后重跑，**不计入最终通过**。更早主动停止的运行没有通过结论。

## 4. 最终十二项答复

1. **真实全链重算？** 是，但仅限已验收的单次 0.6 候选及专项／关联案例，不是价格域全搜索。
2. **沿用旧插值？** 新回调没有；旧 `_break_even()` 仍是可调用的样本数学 API，未完成全系统形式隔离，正式受来源约束的 3E 指标未用它生成根。
3. **独立有根项目？** 无；不能把既有一期正 NPV 项目或改造后的现金流当作有根证明。
4. **根集完整性？** 未证明；P2-4B 保持阻断。
5. **仅有采样而未证明无根？** 是；0.4／0.6／0.8 均正，未返回 NO_ROOT。
6. **价格／NPV 残差？** 两者均未测得（不是零）；单价 NPV 的独立 Decimal 误差界另记为 `<1e-55 元`。
7. **税费随价重算？** 是，沿已有 3D 完整重算；没有复制原价税款。L1 及 L2 的独立 VAT、所得税核对属于候选证据。
8. **EVENTS？** 仍按缺交易级对账证明阻断，不作为现金流零值。
9. **两份封存项目？** 未修改也未解锁；原唯一项目口径、折现率及终期事实门禁维持。不能从一期 SYNTHETIC 外推其 25 年结果。
10. **完整回归？** 光伏 4173/7、WorkBuddy 109/5（passed/skipped），零失败；不等于正式根求解 PASS。
11. **越界修改？** A 提交仅新增一个生产回调及一个明确要求的专项测试文件。469 字段、89 公式、281 绑定、D2/D3、结果 Schema、3B/3C/3D、IRR 和两封存项目均未修改。原六份用户差异 SHA 未变；288 项保护基线 286 匹配、2 项既有差异（`reports/validate.json`、`reports/validate.md`）、0 缺失。
12. **剩余 Phase 3E 门禁？** 正式盈亏平衡根集证书及有根／异常数值验收；EVENTS 交易级排重；股东真实收付、DATED-NPV、IRR、累计与回收期等未接通指标，以及原有真实项目来源／终期与动态资金覆盖门禁，均不得因本轮回调升级。

**停止条件生效：** 不进入 P2-5、3F、4；不补造终期金额、税款或现金事件。等待审查是否授权可审计的全域模型证书及独立有根项目方案。机器证据：`reports/solar-pv/phase3e-p2-4-break-even-evidence.json`。文档／证据本地提交的 SHA 不内嵌在自身文件中，以提交后的 HEAD 和外部提交回读为准。
