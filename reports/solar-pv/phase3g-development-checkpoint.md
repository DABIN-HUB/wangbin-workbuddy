# Phase 3G 统一计算入口 — 开发与有界 SYNTHETIC 核查

**结论：PARTIAL；不是 `PHASE3_CALCULATION_ENGINE_PASS`。** 本轮只在 `solar/phase3e-forward` 开发，不改变 main、冻结公式/字段/正式结果 Schema 或两个封存的 25 年项目。起点为 `9dbfa39737b56eeb0c362b284d098508986f1b69`；阶段 A、B、C 本地提交分别为 `d92d1bf`、`9f13cac`、`c2447c8`，阶段 D 证据提交 SHA 以最终 Git 回执为准。不 push、merge、部署、发布或进入 Phase 4。

## 统一生产入口与文件接口

- Python：`services/solar-pv-engine/src/wangbin_solar_pv/calculation/project_runner.py` 的 `run_project`；CLI：`python -m wangbin_solar_pv --workspace <私有目录> project --input <导出.json> --methods <方法.json> --bundle <D3目录> --budget <预算.json> --output <新目录>`。可用 `--generation` 与 `--generation-hash` 成对指定**同源且经真实 3C 消费者校验**的只读 3B 轨迹；`--scenarios` 指向恰好 BASE、PESSIMISTIC、OPTIMISTIC 三份显式控制。CLI 路径均由 `Workspace` 限定在授权工作区。
- 验证 Phase 2 导出的完整性、D2 方法及项目类别，读取并核对 D3 `base_export`，再调用**已有** 3B 发电、3C 结算、3D 账簿、3E 指标生产者；3F 通过 `prepare_scenario`/`run_scenario` 按依赖重算。无第二套发电/财务算法，不用缺失值当零；异常不发布新项目目录。屋顶和地面分别走已有独立路由。
- 每个执行目录：`3b/`（如使用外部已钉住轨迹则只引用）、`3c/`、`3d/`、`3e/`、`canonical.json`、`formula-execution.json`、`receipt.json`；场景在 `scenarios/<run_id>/` 下独立保存 canonical/公式映射/回执。`canonical.json` 是**原 3E 正式结果结构**，不是报告模型替身。包含项目/场景/输入哈希、来源快照、方法/公式快照、指标、边界、证据与中间账簿；3G 回执另外钉住 Phase 2 输入哈希、D2 方法哈希、冻结定义版本/哈希、3B–3E 结果哈希。每个公式映射都钉住对应 canonical 的结果哈希，单独 digest。运行耗时不参与结果/回执计算哈希。
- Phase 5/6 可按 `receipt.json` 定位对应项目/场景的 `canonical.json` 和 `formula-execution.json`；不得把未计算的数值或 `NOT_TESTED` 映射当成报告数值。**原 D3 块与完整 3B/3C/3D 追溯轨迹未纳入本轮长期证据包**；本轮真实运行使用隔离 scratch，可过期；未来完整复现/报告溯源须单独保留并核验它们。

## 实际运行（独立、明示 SYNTHETIC 的一年期案例）

| 项目/场景 | 真实生产者与复用边界 | 项目状态 | 公式项目状态：CALCULATED / BLOCKED_MISSING_INPUT / NOT_TESTED / NOT_IMPLEMENTED / NOT_APPLICABLE | 计算调用耗时 |
|---|---|---|---|---|
| 工商业屋顶 BASE | 同源 3B 只读轨迹、3C→3D→3E 真重算 | PARTIAL | 21 / 21 / 37 / 10 / 0 | 378.04 秒（**包含下列两场景**及包装，不是 BASE 独占耗时） |
| 工商业屋顶 PESSIMISTIC | 原 3C 身份核验后只读复用；运维 + 贷款重算 3D→3E | PARTIAL | 21 / 21 / 37 / 10 / 0 | 8.47 秒（场景计算） |
| 工商业屋顶 OPTIMISTIC | 售价 3C→3D→3E 真重算；不借用基准财务值 | PARTIAL | 21 / 21 / 37 / 10 / 0 | 277.88 秒（场景计算） |
| 集中式地面 BASE | 3B→3C→3D→3E 全部本次生产者计算 | PARTIAL | 20 / 21 / 37 / 10 / 1 | 98.48 秒（项目入口） |

- 两类项目均只是一年期、来源标记为 SYNTHETIC 的独立案例；**不是**既有两个封存 25 年项目的验收。阶段 A–C 代码提交与项目输入哈希/方法哈希/项目 ID/冻结定义绑定见 `reports/solar-pv/phase3g-synthetic/manifest.json`。17 个已列成员的文件长度和 SHA-256 全部读回一致；四份 canonical 逐份通过 `validate_result`，对应公式映射/回执的独立 `digest`、场景身份与 3E 结果哈希均复核通过。原始同步来源目录不在包中，因而不能把当前证据说成可独立重放所有时序输入。
- `numeric-evidence.json` 记录独立 Decimal 对照：两路年度出口电量均为 **87600 kWh**；屋顶**出口售电额** **35040 → 52560**，增加 **17520**（`87600 × (0.6−0.4)`），屋顶自用价值 **140160** 不变，因此总收益 **175200 → 192720**；悲观运维净额 **200**（付现口径 **226**），贷款利息 **56.50 → 113.00**；地面 BASE 售电额 **35040**、利息 **56.50**。上述数值已直接读回 canonical 指标/账簿并以 Decimal 独立复核；只针对 SYNTHETIC 来源与方法，不代表 25 年现金流。
- BASE 屋顶在统一入口运行了**项目** BASE 链，并只读复用已钉住的 3B；**未**单独运行 `run_scenario(BASE)`。相对 3F 上一阶段只准备 OPTIMISTIC 的状态，本轮屋顶 OPTIMISTIC 已实际执行一年期生产链，但仍非真实项目/封存项目全链验收。地面场景（非 BASE）、投资/发电量/自用比例/弃光/折现率的额外真实场景执行本轮 **NOT_TESTED 或 BLOCKED**，不能据此解锁。

## 冻结公式与硬依赖

`formula-execution.json` 按有效冻结公式 ID 逐项输出**产品证据状态**、数值专项证据、当前项目状态、实际 metric ID 和阻断原因，而非修改冻结定义。89 项均有映射：产品注册表为 **57 IMPLEMENTED_TESTED / 32 NOT_IMPLEMENTED**（不等于当前项目执行通过）；原计划 82 项属 Phase 3、7 项留待后续，不删后续公式。上表中每行项目状态总数均为 89。`NOT_TESTED` 表示该项目未观察到数值指标的受控分支，**不能**解释为产品验收失败或已经计算；`NOT_APPLICABLE` 仅取现有项目实际 metric 状态；旧 3B 的 `NOT_IMPLEMENTED` 占位不会掩盖同公式 3E 的真实阻断。

- `F-BREAK-EVEN-PRICE`：本例 `BLOCKED_MISSING_FULL_CHAIN_PRICE_RECALCULATION`；正式根集仍未认证。
- `F-NPV`/项目 IRR/回收：缺终期现金与完整项目流时阻断，绝不使用基准指标或补零。`F-LCOE` 缺终期成本边界；`F-CFADS`/`F-DSCR` 缺对应事实或上游 CFADS。
- 股东现金流/股东 IRR：缺实际股东收付/终期权益现金；`F-DATED-NPV` 缺具日期的现金事件。
- EVENTS：交易级排重和税务证据未闭合，未凭本轮年度结算解锁；其他缺经济口径/正式表示的指标保留原有门禁。
- 场景因素：投资需要付款/折旧/融资联动事实；D2 `energy.pr` 的 POA_PR 不等于 3C 的 INTERVAL_DC_AC 逐时消费边界；提议自用率不是实际负荷；弃光真实专项未执行；折现率缺合法终期来源绑定。无来源的组合保持阻断，不通过修改最终财务值制造结果。

## 验证边界与耗时

- 当前 HEAD 的相关**快速测试**：`test_phase3g_project_runner.py`、`test_phase3f_scenario_runner.py`、`test_calculation_graph.py`、`test_calculation_contracts.py`、`test_calculation_contract_cli.py`：**53 passed、0 failed、99.54 秒**；编译/import、CLI 帮助和 Git 差异检查通过。测试耗时不是最终 Skill 报告生成时间；上表为生产计算记录时间，且项目时间包含子场景，不能相加为独立总耗时。
- Phase 3G 完整 25 年两封存项目 E2E、完整 L2/L3、全部 82 个 Phase 3 公式逐分支数值验收、BASE 独立 `run_scenario`/地面非 BASE 场景、完整 CLI 项目运行、Word/PDF/Excel 报告及 WorkBuddy 上传/导出：**NOT_TESTED**。原 main 的 `ba3c40b` P2-5 L3（4177 passed、7 skipped、22046.115 秒）只属于 main，**不计入**当前分支验收。
- 运行性能风险：价格变化在真实 3C 时序链上仍有数分钟开销；没有降低精度或跳过来源检查，也未在本轮开展单独大规模优化。项目完整验收须留待用户下一步指令。
