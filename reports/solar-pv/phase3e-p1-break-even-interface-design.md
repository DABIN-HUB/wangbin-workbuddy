# Phase 3E-P1：盈亏平衡电价受控选价及全链重算接口审批稿

**状态：DESIGN_ONLY / AWAITING_APPROVAL；未实施 Phase 3E-P2。** 仓库 `F:/ideaWorkSpace/wangbin-workbuddy`，审阅起点 `main@29202e91a9b71e99ace0c8b9072617578316d4ce`。本稿引用同目录 `phase3e-p1-break-even-interface-decision.json`；示例是**未执行的技术契约草案**，不是已获批准的输入或实测财务结果。P1 不改变 469 个字段、89 个公式、281 个绑定、D2/ D3 Schema、已封存案例或生产代码。

## 1. 冻结依据与当前断点

- `docs/solar-pv/05-formula-registry.md:3290-3338`：`F-BREAK-EVEN-PRICE`，`P*={p∈P:NPV_b(CF_b(p),r_b)=0}`；输出 `sensitivity.break_even_price_roots`，单位 **元/kWh 的集合**；操作数 `sensitivity.price_search_domain`、`finance.npv`、`sensitivity.price_cash_flow_vector`、`finance.selected_discount_rate`、`finance.cash_flow_basis`。`p` 是预先指定的**一个结算电价对象**，不是月/年索引；`b` 必须保持同一项目/权益及税前/税后口径。域内合法负价可以保留；分时价格“倍率”属于需要新输出字段的**其他决策**，本方案排除。E05 勘误见 `18-phase3-preimplementation-review.md:29-38`。基线原意见 `00-original-user-baseline.md:60`；`05-formulas.json`、`05-field-bindings.json`、`03-input-fields.json` 与 `08-requirement-traceability.csv` 是不可改的冻结字典。`17-phase3-implementation-plan.md:19-28,91` 与 `19-phase3-approved-implementation-contract.md:7-9,24-46` 已批准 D1/D2/D3 的独立、带来源、严格版本化执行及结果边界，但**不等于批准新执行选择器契约**。
- 旧路径：`financial_metrics.py:381-412` 把价格—现金流样本逐段线性插值，按**价格宽度容差或货币函数值**停止；甚至可能输出错价的 `CALCULATED`，并以 `PIECEWISE_AFFINE_SAMPLE_INTERPOLATION` 标注。它没有 3C/3D 重算，也不能证明全域根集合。`phase3e.py:191-203` 当前对两个案例保持 `BLOCKED_MISSING_INPUT/BLOCKED_MISSING_FULL_CHAIN_PRICE_RECALCULATION`；且当前 `_record(..., "CNY", "PROJECT", ...)` 把此公式的结果单位标为 **CNY**，与冻结 Catalog 的“集合（元素元/kWh）”不一致。这是当前阻断值的显示缺口，未来正式结果修正单位**需先明确批准**，P1 不改。`cli.py:62-66,182-199` 只接受既有输入、D2 和已生成结算，因此**现有命令不能完成选价或 3C 重放**。`method_config.py:114-118,139-161` 已有 `[minimum_price,maximum_price]`、价格区间容差、最大完整重算次数及 `CERTIFIED_MONOTONE_RECALCULATION` / `PIECEWISE_AFFINE_ALL_ROOTS`，但无 field_id/row_id 选择器，未知 D2 参数会被拒绝。
- 历史审查 `phase3e-review-and-acceptance.md`、`phase3e-closeout-review.md` 与 `phase3e-numerical-blockers-repair.{md,json}` 的时间/候选不同；以较新修复证据记录 IRR 专项 PASS、光伏 4103/6、旧产品 109/5 为**历史回归**，不是 P1/P2 的新测试。两个封存 SYNTHETIC 案例各 26 期、`0/1/20`，未补终期现金等来源，不因本设计升级 Phase 3E 状态。

## 2. 唯一价格对象适用性矩阵

以下“可选择”仅表示**未来接口类型上允许的候选**，须通过真实项目、方法、来源、时间及完整目标现金流校验。稳定 `row_id` 属于原行对象；必须同时匹配 `field_id`、项目身份和已校验的原记录 `field_instance_id`，不使用数组位置、标签或模糊匹配。选择器只接受**一个**对象；相同价格的多行仍是多个对象。

| 精确 field_id / 选择身份 | 生效条件及作用 | 严格拒绝条件/范围 | 原案例事实 |
|---|---|---|---|
| `tariff.periods.sale_price` + `tariff.periods` 唯一 `row_id` | `settlement.price_source=PERIOD_TABLE`；只有该行日历、时段、生效日起止覆盖的结算报价变化；销售收入、后续税费/收款受影响 | 其他行不变；不得改交易费、税率、`tax_included`、`vat_rate`、价格基年或其他来源；若选中行对评价期完全未生效或无交付电量，阻断数值根声明 | 屋顶三行售电价数值都为 0.4，**不自动选一行**；地面选 `MARKET_SERIES`，其 `flat` 行 0.4 不被外售价消费 |
| `tariff.periods.avoidable_price` + 唯一 `row_id` | 仅 `OWNER_AVOIDED_COST` 或 `PPA_DISCOUNT` 的已生效自用规则；`PPA_DISCOUNT` 价格经既有折扣乘数影响合同 PPA 价 | `EXPORT_ONLY` 或无自用场景拒绝；不改变售电价格；`OWNER_AVOIDED_COST` 下节省是经济效益，**非银行到账**，以 D2 `cash.self_use_treatment` 分流，税口径由原 3D 负责 | 屋顶自用行分别 0.5/1.0/0.6；地面不使用 |
| `tariff.ppa_price` + **row_id=null** | 仅 `settlement.revenue_method=PPA_FIXED`，且已有可验证的根字段原子信封；投资方合同价进入原自用结算/收款路径 | `PPA_DISCOUNT` 互斥；不能把自用避免价当固定 PPA 价；不能从当前缺失字段中创造默认值 | 两案例均无固定 PPA 报价 |
| `tariff.market_series.sale_price` + D3 行唯一 `row_id` | 仅 `settlement.price_source=MARKET_SERIES`；选中**一个**真实时段行的外售价重放整个序列；核查 UTC 时间、时区、区间、来源与原 D3 哈希 | 不能把市场 8760 行合成一个统一单价；无完整可读原 bundle、原报价来源/变更授权或目标行不唯一时阻断；改该行不能改 `transaction_fee` | 地面 8760 行仅有仓库 manifest（35 块），首块在该案例目录中不存在；**不推断仓库外私有副本不存在**；屋顶不使用市场报价 |

`tariff.transaction_fee`、`tariff.market_series.transaction_fee`、合同折扣、债务、税率、发电量与场景倍率**都不是本公式的受控电价对象**。负候选价须经原 `tariff.negative_price_rule` 来源及 D2 `settlement.negative_price_treatment=SETTLE_SIGNED_CONTRACT_PRICE`、原子信封和适用合同复核（`tariffs.py:170-176`）；不能因数值域允许负价便自动认为真实合同允许。所有候选的价格单位 `currency/kWh`（报告元/kWh），经济基准的币种/价年/含税与名实口径须逐原子等于 `settlement.currency` / `price_year` / `tax_basis` / `price_basis`（`tariffs.py:123-176`）。价格日历时段唯一覆盖的最终决定仍由 `Tariffs.quote:208-252` 拒绝缺口/重叠；执行选择器预先检查目标行属于该项目及在评价区间生效。

## 3. 三方案比较与唯一推荐

| 维度 | A. **独立、严格的执行选择器（推荐，需批准新技术契约）** | B. D2 最小升版新增选价参数 | C. 不改现有契约 |
|---|---|---|---|
| 冻结兼容/469字段/281绑定 | 只引用既有 field_id 和 row_id；不改变原字段/绑定及公式；新接口仅承载“求解时变哪一项” | 若可溯源亦可维持业务语义；但扩已批准 D2 Schema/版本 | **不可行**：现有 D2 搜索参数及输入数值不能唯一标识三行同价中的一行 |
| 实现/复用 | 新独立严格校验和场景派生适配器；复用 3B/3C/3D 真实函数；无第二引擎 | 需要 D2 注册表、校验、兼容/迁移和全引用升级，仍需场景派生 | 仅旧插值或偷偷靠 JSON/环境变量，均违规 |
| 身份/hash | 选择器版本、源原子、方法哈希、候选 p 和派生 export/bundle 作为**计算输入身份**；旧 Phase 2/D2/D3 身份另存 | 修改已有 D2 哈希和项目身份，旧结果须隔离重算 | 无选择身份，错结果可能同 hash |
| 类别/错误拒绝 | 显式支持现有 `industrial_rooftop`/`utility_scale_ground` 的真实生效取价规则；其他七类保持 NOT_IMPLEMENTED；严格拒绝多/错/空 row_id | 可实现但方法配置承担项目记录身份，不恰当；要独立类别守卫 | 无法可靠拒绝 |
| 向后兼容/CLI | 原 D2 及旧命令不变；新增**可选的独立正式执行入口**；旧结果不迁移为新证明 | 旧 D2 需版本兼容解析、旧哈希失配审查；CLI 仍需新调用链 | 旧 CLI 保留但无新功能 |
| 后续复用/审批 | 结构可能被后续单因素情景复用；**P1 不实施 Phase 3F**；需批准执行控制接口版本、来源、派生规则和结果身份承载 | 需批准 D2 扩版、迁移、后续重算策略 | 无审批但无法达成目标 |

**决定：推荐 A，明确必须新增版本化、严格校验的“执行控制”接口，而不是现有合法 D2 参数中的默认值。无需修改 D2 Schema，**前提是用户明确批准此独立契约的字段、来源、哈希归属和结果联动；**不能把它放在未验证的旁路 JSON 中**。用户若坚持绝不新增任何接口，则 P2 必须保持 BLOCKED；B 不是本轮默认退路。

结论标识：**方案 A = 推荐**；**方案 B = 需 D2 Schema 变更，当前不授权**；**方案 C = 无法唯一选价，不可行**。

## 4. 推荐的接口（提案，不是当前 API）

**拟建模块** `calculation/break_even_execution.py`：

```text
validate_price_selector(control: dict, original_export: dict, methods: MethodConfig, original_bundle: TimeSeriesBundle | None, catalog: Catalog) -> ValidatedPriceSelector
make_candidate(original: ValidatedInput, selector: ValidatedPriceSelector, p: Decimal, original_bundle: TimeSeriesBundle | None, *, catalog: Catalog, budget: BundleBudget, private_root: Path) -> CandidateScenario
calculate_candidate_npv(candidate: CandidateScenario, *, generation_dir: Path, generation_result_hash: str, methods: MethodConfig, catalog: Catalog, budget: BundleBudget, cash_flow_evidence: SourcedCashFlowInputs) -> CandidateEvaluation
solve_break_even(original_export: dict, methods: MethodConfig, control: dict, *, original_bundle: TimeSeriesBundle | None, generation_dir: Path, generation_result_hash: str, private_root: Path, budget: BundleBudget, cash_flow_evidence: SourcedCashFlowInputs, catalog: Catalog) -> dict
```

`ValidatedPriceSelector`/`CandidateScenario`/`SourcedCashFlowInputs` 为**提案内部类型**，不是现存符号或新增原始业务字段。`cash_flow_evidence` 只接受原冻结公式所需、可校验来源的项目或权益实际现金事件及终期事项，**此输入承载方式尚未获批，现有 `calculate_phase3e()` 不能消费它**，故完整链路不仅缺选择器，也缺相应合法现金流接入；未批准前输出 BLOCKED。若需要调整 Phase 2 原字段目录或公式绑定才可承载上述事实，先停、另报审，不得在 P2 偷换输入。签名刻意没有 `default_terminal_cash=0`、隐藏倍率或任意回调式“现金流函数”。

### 4.1 控制 JSON 草案（独立版本，禁止额外属性）

以下是字段类型约束的**示意**，不是修改现行 D2/Phase 2/D3 Schema；用 JSON Schema 2020-12 表述，正式发布前须将 `source`、所有 identity 校验与项目来源协议审批。所有 `sha256` 必须是实际经验证内容摘要；示例中的占位符**不是**有效业务输入。

```json
{
  "schema_version": "solar-pv-break-even-execution/1.0.0",
  "project_id": "<经验证的现有项目ID>",
  "pv_type": "industrial_rooftop",
  "formula_id": "F-BREAK-EVEN-PRICE",
  "selector": {
    "field_id": "tariff.periods.sale_price",
    "row_id": "<经验证的现有唯一row_id>",
    "field_instance_id": "<原子信封内的现有实例ID>",
    "original_atom_hash": "<实际64位sha256>",
    "unit": "currency/kWh",
    "economic_basis": {"currency": "CNY", "price_year": 2025, "tax_basis": "inclusive", "price_basis": "nominal"}
  },
  "basis": "<已有来源中可验证的finance.cash_flow_basis取值>",
  "original_input_hash": "<原Phase2真实哈希>",
  "original_source_snapshot_id": "<原Phase2真实快照ID>",
  "original_dataset_content_hash": "<原D3真实内容哈希或null>",
  "generation_result_hash": "<真实3B结果哈希>",
  "method_config_hash": "<真实D2配置哈希>",
  "source": {"source_id": "<本次明确选价决策的来源ID>", "source_reference": "<本地安全的来源引用，非凭据URL>", "source_kind": "USER_PROVIDED", "status": "UNVERIFIED", "license_status": "AUTHORIZED"}
}
```

字段全 required（`original_dataset_content_hash` 允许 `null` **仅当没有 D3 数据集且既有计算允许无 bundle**）；对象均 `additionalProperties:false`；`schema_version`、`formula_id` 常量；`pv_type` 只接受当前已实现的两个类别且等于输入/3B；`field_id` 枚举恰为上表四项；`row_id` 为与父字段一致的原样稳定字符串或**只有 `tariff.ppa_price` 才可为空**，不得人为限制现有合法 ID 的字符集；`field_instance_id` 必须等于目标原子记录，不能代替 row_id；摘要字段为 `^[0-9a-f]{64}$` 且回读校验，`original_atom_hash` 定义为既有 `serialization.digest(original_atom_record)` 的 canonical 内容哈希（非 raw JSON 文件 SHA）；`basis` **只精确引用已可验证的 `finance.cash_flow_basis` 原值**（当前源码没有为此声明可用口径枚举，不能造 `PROJECT_AFTER_TAX` 等新类型或默认口径），来源尚未合法承载时一律阻断；`source` 的状态和授权须对应实际证据，SYNTHETIC/ASSUMED 仅用独立合成测试，不将真实项目声明 VERIFIED。价格 `p` 不放在 selector 中，而由 D2 域和求解器在每次候选中给出，必须是有限 JSON 数字/Decimal，`minimum_price ≤ p ≤ maximum_price` 且与目标原子的单位/经济基准一致。

实现草案可在**独立、经批准的版本化控制 JSON Schema**中对上述常量、类型、oneOf 条件写强校验；额外跨对象约束在 `validate_price_selector()` 实现：对原项目 `tariff.periods` 逐行遍历，精确 `row_id` 命中**恰 1**，核原子字段、`field_instance_id`、来源与摘要，时间窗交集非空且有实际用到的计价事件；对 `tariff.market_series` 在经完整 D3 校验的原始 `bundle.rows()` 中做有界流式唯一计数并校验时间区间和原子来源，禁止靠行号查找。若后续 3C 的真正覆盖/交付校验失败，则阻断，不用近零 NPV 宣称无限价格根。PPA 根字段只能在 `PPA_FIXED` 下选择。价格域 `sensitivity.price_search_domain` 与 D2 上下限的精确关系需由同一审批固定为**一致性校验**，不允许两套范围静默择一。

### 4.2 输出草案及错误语义

**不要另建结果根结构。** 最终仍输出既有 `solar-pv-calculation-result/1.0.0` 的完整结果（`result_contract.py:18-54,87-149`），公式指标 `formula_id=F-BREAK-EVEN-PRICE`、`metric_id=financial.phase3e.break-even-price`（由当前 `phase3e.py:202-203` 的 ID 构造式确认）；**推荐的正式 metric.unit=`集合（元素元/kWh）`**（实际有效 Catalog 的 `unit`）与当前阻断项目代码硬编码的 `CNY` 有差异，P2 须单独批准修正，目标电价原始字段的 `unit=currency/kWh`；数值状态只用当前 `CALCULATED/UNDEFINED/BLOCKED_MISSING_INPUT/BLOCKED_METHOD_REVIEW` 等既有枚举。现行 metric 的 `value` 只接受 number/number[]/null；严格保留“唯一根有值、多个根 `UNDEFINED/MULTIPLE_ROOTS` 且在 `details.roots` 列全集、无根 `UNDEFINED/NO_ROOT`”的既有投影，**需请用户确认该投影是否满足冻结输出“集合”的语义**；若必须以 `value` 返回多根数组，属结果语义审批，不得静默改 Schema。连续根区间更无法以离散 `details.roots` 假装枚举完毕，须阻断/报审核。

```json
{
  "schema_version": "solar-pv-calculation-result/1.0.0",
  "project_id": "<原项目ID>",
  "scenario_id": "<由审批后控制对象与根候选派生的身份>",
  "status": "PARTIAL",
  "input_hash": "<按现有input_contract的组合规则重算>",
  "source_snapshot_id": "<包含选价来源的真实可验证快照身份>",
  "results": {"metrics": [{"formula_id": "F-BREAK-EVEN-PRICE", "metric_id": "financial.phase3e.break-even-price", "status": "UNDEFINED", "reason": "MULTIPLE_ROOTS", "value": null, "unit": "集合（元素元/kWh）", "details": {"roots": ["<由Decimal编码的第一个数值>", "<第二个数值>"], "root_set_proof": "<有界完整性证据引用>", "residuals": ["<实际货币残差>"]}}]},
  "evidence": {"<既有结果证据key>": "<完整候选身份/链路证据>"},
  "result_hash": "<真实canonical结果哈希>"
}
```

**上述 JSON 是非独立的结构片段**，不是可通过现有 `result_schema()` 的完整结果；`roots` / `residuals` 在实际结果中必须是 JSON numbers/Decimal 而非占位字符串，所有其余必需根/metric 键照现行 `result_contract.py:18-54` 保留。正式 P2 应提供通过 `validate_result` 的**完整实际输出**，不可提交示意 JSON 作为运行证据。所有结果至少记录选择器版本、原始目标原子哈希、D2/定义版本、原 3B 哈希、原/派生 D3 identity、候选完整链路结果哈希、根域/隔离区间/覆盖证明、货币 NPV 残差与失败原因；不能只把选择器放在磁盘文件名中。

完整根结构在旧链路下的**未执行 BLOCKED 示例**如下；尖括号为故意不可运行的审查占位，绝不是凭空计算的哈希/来源/数值。P2 必须沿用上游 3C/3D 真正产生的 `boundaries`、`inputs`、`source_snapshot`、`formula_snapshot`、`results.metrics` 和 `evidence`，不能直接使用此最小示例生成生产结果：

```json
{
  "schema_version": "solar-pv-calculation-result/1.0.0",
  "model_version": "<现有模型版本>", "run_id": "<真实运行ID>",
  "input_hash": "<实际组合输入哈希>", "source_snapshot_id": "<实际来源快照哈希>",
  "result_hash": "<实际结果内容哈希>", "project_id": "<经验证的项目ID>",
  "pv_type": "industrial_rooftop", "scenario_id": "<已审批场景身份>",
  "created_at": "<真实UTC日期时间>", "evaluation_date": "<真实评价日>", "currency": "CNY",
  "maturity": {"calculation": "PARTIAL", "real_project": "NOT_VERIFIED", "four_files": "NOT_IMPLEMENTED", "platform": "NOT_TESTED"},
  "status": "PARTIAL", "boundaries": {"PHASE3E_FINANCIAL_EVALUATION": {"phase": "3E"}},
  "inputs": {"identity_payload": "<实际已验证组合对象>"},
  "source_snapshot": {"phase2": "<原始已验证来源>", "methods": "<原始D2>", "datasets": "<已验证D3>", "price_selector": "<审批后严格选择器>"},
  "formula_snapshot": {"definition_version": "solar-pv-formula-definitions/1.0.1", "definition_hash": "617a2e9d314c095bd2ec893939c930a2323be6fd7805da12bf6d6fdd70274808"},
  "results": {"metrics": [{
    "metric_id": "financial.phase3e.break-even-price", "value": null,
    "unit": "集合（元素元/kWh）", "status": "BLOCKED_MISSING_INPUT",
    "reason": "BLOCKED_MISSING_FULL_CHAIN_PRICE_RECALCULATION", "boundary_id": "PHASE3E_FINANCIAL_EVALUATION",
    "period": "PROJECT", "scenario_id": "<已审批场景身份>",
    "input_field_ids": [], "source_ids": [], "formula_id": "F-BREAK-EVEN-PRICE",
    "formula_version": "solar-pv-formula-definitions/1.0.1", "evidence_ids": [],
    "report_locations": [], "workbook_locations": [],
    "rounding_rule": "DECLARED_DECIMAL_NO_DISPLAY_ROUNDING",
    "method_parameter_ids": [], "upstream_metric_ids": [], "details": {"project_result": "BLOCKED_MISSING_INPUT"}
  }], "domains": {"financial_metrics": ["financial.phase3e.break-even-price"]}},
  "findings": [], "evidence": {}, "artifact_manifest": []
}
```

错误归属：选择器 JSON 类型/多余键/哈希伪造/重复行/失配 -> `ContractError` 明确编码（提案 `BREAK_EVEN_SELECTOR_INVALID`、`BREAK_EVEN_TARGET_NOT_UNIQUE`、`BREAK_EVEN_IDENTITY_MISMATCH`；**尚未实现**）；源价格或目标现金事件缺失 -> metric `BLOCKED_MISSING_INPUT`，不是求解失败；D2 方法、根全集证明或价值口径未批准 -> `BLOCKED_METHOD_REVIEW` 或上层独立审批阻断；求解预算尽而未证明全集 -> `UNDEFINED/NON_CONVERGENT` 且 `unexhausted=true`；域内无根 -> `UNDEFINED/NO_ROOT` 且记录证明；多个离散根 -> `UNDEFINED/MULTIPLE_ROOTS` 且保留全集；除法/税规则/真实收款链异常应明确拒绝候选并保持阻断，不能变为零或简单缺值。当前项目已有 `phase3e.py` 的阻断 reason 保持不变，未审批时绝不返回数值。

## 5. 原始证据与候选重放的**实际可实施性门禁**

完整候选调用顺序固定为 **3B→3C→3D→3E**：3B 仅核对物理发电原结果（不因价格变化重算物理量），3C/3D 对每个价格必须真实执行，3E 在选定唯一口径的完整现金流上重新计算 NPV。

`validate_export()` (`input_contract.py:31-77`) 重建 Phase 2 全量源快照并核对原 `input_hash/source_snapshot_id`；**直接 `deepcopy(export)` 修改 price.value 会破坏一致性**。`IntakeSession.from_dict(...).export()` (`intake.py:59,282-295`) 能创建经现有导出计算的身份，但既有 `IntakeSession.revise()` (`intake.py:152-185`) 对 `tariff.periods` 需要提交整个父数组：可能给所有行重建记录及来源，**不能未经核验用于单行覆盖**。P2 需要经批准的内部候选派生适配器：复制原已验证 `ProjectData`；仅修改指定原子信封，记录*候选来源与原原子引用*，重生成 `source_snapshot`/normalized export 并调用 `validate_export`；逐字段/逐行原子比较其余来源和值，验证候选项目 revision/candidates/resolutions 的一致性。若无法通过 `IntakeSession.export()` 和现有 `validate_export()` 而不改其它原子，停下来申请最小兼容接口授权；**不得绕过旧校验或手填 `input_hash`**。原始 export 永远不可写；候选 export 的 phase2 hash 作为派生身份，不得称原始来源发生变化。价格 `p` 在候选信封中作为**来源明确的情景假设**而非真实市场报价（真实报价只有用户/合同重新授权才可改），来源升级不可自动变 VERIFIED。

D3：`timeseries_bundle.py:391-463` 的 `write_bundle(path, base_export=候选导出, datasets=..., catalog=..., budget=...)` 可以在**独占私有目录**创建新 bundle；`read_bundle:563-596` 重新校验全部块/原子/内容身份；`TimeSeriesBundle.rows:526-544` 有界流式回读、按块哈希复核。原 bundle 的 `base_export` 必须等于原 export；**候选 3C 的 bundle.base_export 必须等于候选 export**（`tariffs.py:32-50`、`generation_evidence.py:123-147`），所以即使改的是表价，也不能把原 bundle 原样传给候选 3C；须把全部原 dataset（负荷/市场/物理资源）逐行复制到新 bundle，与候选 base export 重新绑定。若选择市场单行价格，只在该行单一 `sale_price` 原子生成带授权来源的候选替换，其他原子及来源不变；对原/派生资源数据按 `canonical_array_hash` + header/source 双重相等比较，派生市场 dataset 哈希必须变化，未改变的 load/resource dataset 内容与 provenance 必须一致。`GenerationEvidence` 保留原 3B 哈希，按 `generation_evidence.py:88-147` 核物理输入、方法和来源；若完整物理证据不能被读取或匹配则阻断，不重跑 3B、不伪造 8760 行。仓库两案只有结算 D3 manifest，缺少第一块；不能仅据此断言外部授权 bundle 不存在，也**不能用 manifest 重建原始行**。

身份关系（设计草案；不得声称现有链路已包括控制对象）：

```text
original Phase2 export/input_hash + original source_snapshot_id + original D3 content_hash + pinned 3B result_hash
  -> selector_hash = digest(严格的已校验版本化控制对象，含原子身份和选价来源)
  -> scenario_hash(p) = digest({selector_hash, 原始身份, D2 hash, 候选 p 的 Decimal canonical 数字})
  -> candidate Phase2 export identity + candidate D3 content_hash + unchanged 3B result_hash
  -> Phase3C result_hash -> Phase3D result_hash -> Phase3E NPV result_hash
  -> root-set/result evidence references every evaluated candidate, solver proof and full-chain final root recheck.
```

`calculation_identity(validated, methods, catalog, datasets=..., scenario=...)` 已提供 `scenario` 参数及 canonical payload (`input_contract.py:80-132`)，但现有 `revenue._calculate:248-261`、`financial_ledger.calculate_financial_ledger:254-255` **没有从 CLI 传入并贯通外部受控选择器**；P2 须最小接线并保证每层的 canonical `source_snapshot_id/input_hash/result_hash` 都包含本层上游与选价身份。`result_contract.py:18,62-69` 的 result_hash 排除 `run_id/created_at/artifact_manifest`，但包含业务/情景内容；不能凭 run ID 区分候选，不能只改侧车 hash。最终根重新生成独立候选并重跑全链，与所记录 `scenario_hash`、3C/3D/3E 哈希及残差对账。中间缓存如果要跨相同候选复用，必须以完整身份精确键控并重验；不同 p 不能复用受影响结果。

私有目录：`<授权workspace>/break-even/<selector_hash>/<scenario_hash>/`，实际目录构建必须先校验所有路径组件，使用本仓库安全 `local_target`/工作区路径限制，原目录只读；按唯一候选身份独占创建 `derived-export.json`、派生 D3 bundle、新 3C bundle、候选 3D/3E 证据，**绝不覆盖**。全局预算须含 D2 `maximum_iterations` 次完整评估（端点、分段界、最后根重验均计数）、D3 `BundleBudget` 输入/输出/磁盘/内存/墙钟限制；每次完整重扫 8760/35040 行，时间和空间成本至少与读取/复制原完整 bundle 相当，不能承诺常数开销。失败只清理本次拥有的未发布临时目录，不删除原 bundle 或其他运行结果；成功保留经批准的最小完整性证据和哈希，其他私有中间件按明确保留/安全删除政策处理（此政策尚需批准）；预算超限显式阻断，不偷省略 D3 消费。

## 6. 求根方法的**可证明条件**（P2 不得把设计当实现）

- `CERTIFIED_MONOTONE_RECALCULATION`：需要从实际 `Tariffs` 取价、交付量和 `financial_ledger` 的所有涉价转换构造**整个闭区间**上的有来源的单调性证书（含常量、平坦段及税/应收/亏损结转分界）；有限采样表现单调不构成证明。若严格单调并且两端异号或端点为零，可有界二分；须用**独立的货币残差容差**验根、用价格宽度验区间、保证域内全根。若只证明非严格单调且存在零平台，根可能为区间，现结果投影不能枚举，BLOCKED_METHOD_REVIEW 待表示协议批准。未证明单调时，不退化为猜测性搜索。
- `PIECEWISE_AFFINE_ALL_ROOTS`：仅在证明每个定价/税/VAT、税损使用、应收回收比例、债务约束、合同折扣和收益归属分支在有界价格区间上的**全部切换价格**均已枚举时成立；按证明区间重算两端/分界，验证斜率与联动结构，求该段线性 NPV 根，再在原完整链重算核残差，并审查零斜率/全段零、重合端点与根集合完整性。税费、亏损结转、应收可能引入新的 kink；不能只凭两个预设样本断言分段完备。任何未知外部价格规则、非仿射分支、预算超限、证明不足都阻断，不会选“有利根”。
- `break_even.price_tolerance` 单位元/kWh，只限制根隔离宽度；NPV 残差是元，必须按同一口径 `precision.abs_tolerance/rel_tolerance` 对明确目标规模作**经审批的独立货币误差界**，不把价格容差直接当货币容差，也不以任意“近零”推断零平台。`break_even.maximum_iterations` 是包括端点与重验的全链调用上限；每次失败应有清晰计数、状态和证据。零交付/不可达价格项、边界/负价、无根、多根及函数评价失败必须分开处理。

## 7. 旧插值的安全切换方案及必要代码范围（仅 P2 提案）

对比：(i) 只在 `phase3e.py` 正式路径阻断旧公式：**当前已成立**，但直接 `financial_metrics.evaluate("F-BREAK-EVEN-PRICE", samples)` 仍能报 `CALCULATED`；(ii) 给旧函数标非正式用途而不限制公开 `evaluate`：仍会误导；(iii) 公开公式执行器增加“全链证据必须经过验证”的能力守卫：能在批准 P2 时 fail-closed，同时保留纯样本函数为**内部非正式诊断**，旧直接单测需要明确分离/迁移，不能篡改其历史预期；(iv) 完成新的全链求解后用经验证的结果取代正式公式入口：是最终目标，必须维持旧字段绑定解释/结果状态契约。**推荐 P2 同时做 (iii)+(iv)**：未取得可核验的 3C→3D→3E 候选证明时，公开 `evaluate(F-BREAK-EVEN-PRICE)` 禁止 `CALCULATED`，而不是让 caller 传任意 `evidence_ok:true` 自证；保持旧样本插值函数仅作非正式内部分析直到审计旧消费者。若既有对外调用契约不允许这一步且必须保留旧 `CALCULATED`，冲突立即上报，不暗改冻结公式或删除旧功能。

拟修改（**当前均未修改**）：`calculation/break_even_execution.py`（新增严格控制解析/派生/求根）、`calculation/financial_metrics.py`（阻断公开样本伪通过及纯数学边界）、`calculation/phase3e.py`（基于已验证完整候选结果接入而非硬编码旧样本）、`calculation/input_contract.py`（将执行控制身份纳入 canonical scenario/snapshot，必要时最小扩展）、`calculation/revenue.py` 和 `calculation/financial_ledger.py`（仅接线合法情景身份；**不改既有收益税务算法**）、`cli.py`（新增独立命令或显式选价参数）、内部候选派生适配器（定位 `intake.py`/`models.py`/`timeseries_bundle.py` 的既有接口，若必须改 D3 协议则停审）、`calculation/result_contract.py`（优先不改 Schema；如现有结果不能表达批准的身份/连续根，则先审批）。不碰 03/05 原始目录与 D2、D3 Schema；先完成适配器可行性审查，未授权则 P2 不启动。

CLI 最小建议新增**独立子命令** `break-even`，而不是改变既有 `phase3e` 命令的默认为完整求根：保留 `--input --methods --settlement --output` 原行为；新命令显式 `--control <版本化受控JSON> --input <原Phase2 export> --methods <D2> --generation <3B目录> --generation-hash <已固定hash> --bundle <完整原D3目录> --budget <既有BundleBudget JSON> --output <全新私有目录>`，及现金流证据路径仅在**批准具体承载契约后**增设；路径由现有 Workspace 校验，stderr 仅错误码不泄露原价/私有路径。API/CLI 必须读取同一控制对象及相同原始身份，输出 canonical result hash 一致。

## 8. P2 专项测试与独立参考验收矩阵（**计划，P1 不新建/执行测试**）

每个测试先有经 `validate_export` 校验的**独立且明确 `SYNTHETIC`** 的合法小输入、已批准 D2、可读完整 D3（若该类别必需）、有效 3B 结果及**明确来源的全部目标现金流事件**；数值 expected 用手算/独立 Decimal 参考，不由生产 `revenue/financial_ledger` 反向生成。以下细化前置条件 P 和断言 A，P2 对受影响新源码运行关联回归、完整光伏/旧产品回归，并保存候选前后源码 SHA、JUnit 与全部 ID。

| 测项 | 前置条件（除上述共同条件外） | 预期断言 |
|---|---|---|
| 唯一 row_id，错/缺/重复行 | 原 `tariff.periods` 三行、受控唯一行；分别替换为不存在/重复 ID | 仅目标行变；后三项拒绝 `TARGET_NOT_UNIQUE`/失配，不回退索引 |
| 字段/项目/方法不匹配 | 项目 ID 改变；地面 MARKET_SERIES 却选 table.sale_price；PPA_DISCOUNT 却选 ppa_price | 均拒绝，未生效列不求根；不跨项目重用 |
| PPA 互斥、负价及经济基准 | 有效 PPA_FIXED 的源价；冲突固定价+折扣；有证据签约负价；错误 currency/tax_basis | 第一项通过定位；冲突和经济口径拒绝；只有被授权负价落域才进入 3C |
| 3B/3C/3D 连锁和主体分流 | 独立小型发电+负荷+表价；自用 `OWNER_AVOIDED_COST` vs `PPA_DISCOUNT` | 3B 哈希与物理资源恒定；仅对应行自用/售电收益变，合同 PPA 经旧折扣传导；自用避免支出不进入收款 |
| 税费、应收与现金支付 | 明示税率、纳税余额、收款比例，选择价跨税基/税损分界 | 按独立账簿参考逐年校核所得税/VAT/亏损结转、应收、现金税、实际收款；无默认零 |
| NPV 与不污染 | 不同 p、逆序评价、重复同 p，具备完备终期现金 | 3D/3E 源与结果哈希随 p 改；重算 NPV 匹配独立数值；原输入/3B/D3 hash 不变；相同 p 结果 hash 一致 |
| 手算线性 + 分段税务参考 | 人工规定小规模已完整链事实；独立推导真根与税务切换价 | 根、隔离区间、独立货币残差吻合；跨切换点仍全根，不能用插值冒充税务 |
| 搜索域/零根/多根/边界/负根 | 有合法域和独立参考的单/多/无根及允许负价 | 所有实际根重跑全链；全集证明；既有 `UNDEFINED` reason 与详情符合冻结语义；连续根显式阻断 |
| 预算及未证明全根 | 超 `maximum_iterations`、D3 字节/行/时间上限或单调证明缺失 | 真实调用计数不越界，`unexhausted`/相应阻断保留；不因局部根返回唯一值 |
| 缺终期现金/缺原 D3 | 案例原缺项、仅有 manifest | `BLOCKED_MISSING_INPUT`/缺源错误，**不生产数值价格、不补 0、不合成 8760 行** |
| 结果契约与 CLI | API/CLI 使用同一原数据、选择器与 D2；候选目录新建，JSON 顺序扰动 | `validate_result` 成功，公式/方法/源/上游/情景/残差证据齐，canonical result hash 与侧车一致，错误入参不生成貌似合法数值 |
| 旧样本路径 | 只给原 `_break_even` 的两组价格—现金流样本而无链路身份 | 可保留内部诊断值，但正式 `F-BREAK-EVEN-PRICE` 的 `CALCULATED` 必须被拒绝；旧历史结果保持不改 |

**独立数值参考办法**：小型线性情景先由已声明能源量与可追溯固定支出/收款逐项手算 `CF(p)`、`NPV(p)`、根；分段情景手算各税基/亏损结转触发区间及现金税、实收时间序列，独立算折现后 NPV 和全部根。任何税或收费无法形成合法测试输入/可独立核对时不构造伪 expected，以 `BLOCKED` 报审。P2 关联回归范围 3A 方法/结果、3B 发电身份、3C 消纳收入、3D 账簿、3E 21 公式和 API/CLI；最终候选完整 `python -m pytest tests/solar-pv -q` 与 `python -m pytest tests --ignore=tests/solar-pv -q`，这只是**经单独 P2 批准后的计划**。

## 9. 明确审批清单 / P2 停止界

**已批准且 P1 未改变：**原 89 式/469 输入/281 绑定，E05 词素勘误，D2 方法与 `break_even.*` 控制，D3 有界私有 bundle 协议，两种现有类别的 3B/3C/3D 已验证函数，统一结果 Schema 的现有状态/哈希规则。**尚需用户逐项批准：**(1) 方案 A 的独立版本化执行控制及 source/schema/hash 的具体形状；(2) 表价/自用/PPA/单行市场价的允许对象范围与真实价格变更授权（若不允许市场单行选价须从候选枚举移除）；(3) 派生 Phase 2 export/全量 D3 重封包是否允许作为仅供求根的情景事实及原原子来源保留规则；(4) 完整项目或权益终期/股东实际现金事实的现有契约接入方式，**不授权自动补值**；(5) 集合输出的 `value`/`details.roots` 语义、现 `CNY` 硬编码与 Catalog 电价集合单位的差异以及连续根区间表示，若要改结果 Schema 另案批准；(6) 单调/分段仿射**具体完整性证书**与货币 NPV 残差界；(7) 未发布中间候选目录保留/清理策略、执行预算及新 CLI 入口。批准方案 A **不等于**批准修改 D2 Schema、D3 协议、账簿算法、测试断言或封存案例。

**P2 精确边界（须再次明确执行授权）：**先验证派生导出 + D3 重封包 + 3B 复用的真实接口可行性；再实现严格 selector/身份；再接线每候选 3C→3D→同口径 3E NPV；最后在有已批准完整性证明的方法下求全根、复算核残差与哈希，执行上述独立测试/回归/留证。任何一步需要改原冻结字段、D2/D3 Schema、正式财务公式、结果语义或现金事件口径，立即停止受影响部分并申请审批。当前 Phase 3E **PARTIAL/BLOCKED**，不进入 3F/P2/发布。
