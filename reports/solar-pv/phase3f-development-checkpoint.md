# Phase 3F 多方案与敏感性 — 开发检查点

范围：仅独立工作树 `solar/phase3e-forward`；冻结依据 `docs/solar-pv/17-phase3-implementation-plan.md` 97–105 行。**SYNTHETIC 验证不代表真实封存项目验收。** 没有更改冻结字段、公式或正式结果 Schema。

## 实际入口

- `calculation/scenario_runner.py`：`prepare_scenarios` 要求恰好 BASE、PESSIMISTIC、OPTIMISTIC 三份显式配置。`prepare_scenario` 锁定原 Phase 2 输入/来源、D2 方法哈希，克隆独立候选，用 `field_id + row_id + field_instance_id + 原子哈希` 定位；候选重新通过 `validate_export`/`MethodConfig`。无默认扰动；失败不发布项目结果。
- `calculation/sensitivity.py`：八因素的**实际输入/方法消费白名单**，不缩放已算 NPV、IRR、回收期；`scenario_calculation_graph` 给出 3B→3C→3D→3E 的阶段依赖。
- `run_scenario`：命中 3B 的变化调用既有发电生产者；命中 3C 的变化复制并重新绑定 D3 数据后调用既有结算生产者；只改 3D 的变化在核验原 3C 身份后复用其只读结算，真实重新计算 3D 账簿及 3E 部分结果。结果 SHA 与来源/场景身份在独立回执中校验；未具备可计算来源的 3E 指标继续 `BLOCKED_MISSING_INPUT`。输出 hash 排除 `elapsed_seconds`，可对回执剩余字段重新 `digest()` 复核。

## 八因素当前状态（相对于生产执行而非参数准备）

| 因素 | 指向的真实入口 | 当前范围/门禁 |
|---|---|---|
| 投资金额 | `capex.items.amount`、`unit_price` → 3D `_capex`、资产折旧及融资 | **BLOCKED**：金额/单价、付款、折旧和提款联动缺显式一致的新事实；禁止单字段无约束变化 |
| 发电量 | D2 `energy.pr` → 3B POA_PR | **BLOCKED**：3C 的 `GenerationEvidence` 只接收 INTERVAL_DC_AC 逐时物理轨迹；不能把 POA_PR 当逐时输入 |
| 售电价格 | `tariff.periods.sale_price` 或合法 `tariff.ppa_price` → 3C 结算 → 3D 税/现金 → 3E 部分结果 | SYNTHETIC 一年期固定售电价 0.4→0.6 已走真实 3C/3D/3E；负价需原规则和 D2 负价方法，其他来源/价格方法 **NOT_TESTED** |
| 自用比例 | `load.proposed_self_use_ratio` 不被 3C 当作实际负荷 | **BLOCKED**：没有匹配负荷时序的来源和按行扰动，不得乘自用最终指标 |
| 弃光比例 | `system.losses.value` 的 `curtailment` 原 row_id → 3B 物理 → 3C/3D/3E | 已有场景输入与重算入口；须证明上游未扣该损失；真实全链专项 **NOT_TESTED** |
| 运营维护成本 | `opex.items.base_amount`，维护/清洗/运营类 row_id → 3D `_opex` → 3E | SYNTHETIC 一年期维护原子 100→200 已走真实 3D/3E；其他 OPEX 分支 **NOT_TESTED** |
| 贷款利率 | `finance.loan_rate` 且真实债务比例及提款方法存在 → 3D `_debt`/利息/税 → 3E | SYNTHETIC 一年期 0.1→0.2 已走真实 3D/3E；其他贷款合同形态 **NOT_TESTED** |
| 项目折现率 | `finance.project_discount_rate` → 3E 项目 NPV | 候选输入可准备；**BLOCKED**：现有 3E 源证明仅支持特定单电价终期来源，不能以旧 3D/终期数据为新折现率计算 NPV |

**统一限制：** F-BREAK-EVEN-PRICE、EVENTS、股东真实收付、DATED-NPV、CFADS/DSCR、LCOE 和缺事实的其余财务公式均不因场景运行而解锁。即便已有 3D 账簿，缺终期现金来源的 3E 项目 NPV/IRR/回收指标仍保持 `value=null`。不把 SYNTHETIC、假设或一次场景运行称为真实项目审核。

## 验证与下一关

- 阶段 A、B 开发期快速检查分别 **4 passed**、**7 passed**（同一场景测试逐步扩充，不能相加作为新通过项）。最终 C/D 代码的三次相互独立范围调用：`test_phase3f_scenario_runner.py + test_calculation_graph.py` **11 passed，69.45 秒**；`test_calculation_contracts.py + test_calculation_review_regressions.py` **56 passed，46.35 秒**；`test_phase3f_real_scenario.py` **1 passed，815.58 秒**。这三次合计 **68 passed、0 failed、0 errors、0 skipped**，只代表各自定点范围，绝非完整 L3。编译及差异检查通过。
- 独立一年 SYNTHETIC 专项在不同的私有 `TMPDIR` 和 pytest `--basetemp` 路径执行；JUnit 声明 1 项，与枚举的 1 项一致，0 失败/错误/跳过。价格场景复算 3C→3D→3E **290.48 秒**；复用同源结算后的运维与贷款场景分别 **7.94 秒**和 **6.62 秒**。完整 pytest **815.58 秒**包含一次性 SYNTHETIC 准备及原始全链；三次场景耗时不能相加当作整个测试耗时。场景构建成本偏高，留作集中验收时的性能风险，**本轮不启动额外大规模性能工程**。
- 独立 Decimal 校验：一年期出口电量 **87600.00 kWh**，原价 0.4 的售电额 **35040.0**，新价 0.6 的售电额 **52560.0**；`87600.00 × (0.6−0.4) = 17520.000`，与观测差额 **17520.0** 一致。维护净额从 100 改到 200，3D `opex.net` 为 200，13% 口径的计提值 **226**；债务本金 565、利率 0.2 的独立利息 `565 × 0.2 = 113.0`，3D 观测 **113.00**（原 56.50）。三份 3E 项目 NPV 均为 `BLOCKED_MISSING_INPUT`，`value=null`，未复制基准 NPV。两个财务专用场景的 3C 复用 hash 与原结果一致，价格场景 3C 则重算。三份场景回执按排除 `elapsed_seconds` 和 `result_hash` 的字段重新 digest 均匹配。
- 原始 JUnit、三份小型独立回执及数值/原始结果文件 SHA-256 提取保存在 `reports/solar-pv/phase3f-synthetic/`；这不是原始 3C/3D/3E 全文件的长期归档。SYNTHETIC 全链仅验证上述价格、运维及贷款变化，不代表弃光、其他项目类型、其他价格方法或 25 年项目。
- 当前分支完整 L3、两个封存项目、WorkBuddy 上传实测：**NOT_TESTED**；原 `main` 工作树的 P2-5 L3 不能用于本分支。
- 3G 前需关闭：八因素中留阻断项的真实输入/方法及跨模型依赖；3E 的项目终期资产现金与折现口径绑定；股东收付与日期事件、EVENTS 排重；各合法场景的完整复核和身份回执；集中 L3 与平台上传/导出验证。缺项不自动补零，不改变冻结目录来赶进度。
