# Phase 3E-P2-3B — 项目现金流来源与完整 NPV 接线审计

## 结论与执行边界

**本轮结论：`FULL_PROJECT_NPV_REPLAY_BLOCKED`（仅为审计判断，不是生产状态枚举）。** 两个封存 SYNTHETIC 项目的 `finance.cash_flow_basis` 未唯一且经来源验证地闭合，`finance.project_terminal_cash` 也没有合法的终期处置净现金来源。缺少后者所需的已批准现金事件承载契约，按本轮停止条件，**没有实施 Phase 3E 项目现金流、没有计算项目 NPV、没有生成独立 Decimal 完整项目 NPV 参考值，也没有开发盈亏平衡电价求根**。现有数学 `F-NPV` 执行器的可调用性、已通过的 P2-3A 真实 3C→3D 账簿链，均不构成完整项目财务来源链验收。冻结公式 `F-PROJECT-CASH-FLOW` 明确要求期末处置净现金及未通过营运资金变化回收的残余资金，缺值不能当零（`docs/solar-pv/05-formula-registry.md:2159-2205`）；`F-NPV` 要求唯一口径、对应现金流与匹配折现率（同文件 `:2571-2607`）。

本次仅核验冻结契约、受控来源与只读封存 JSON，并生成本报告和机器证据；只读调用现有 `result_hash()` / `validate_result()` 回读两份既有 3D 结果，均报告 canonical hash 匹配、`CALCULATED_SYNTHETIC`，并未执行 3E。**没有改 469 字段、89 公式、281 绑定、D2/D3、正式结果 Schema、3B/3C/3D 数值算法、任何生产代码或测试代码**。起始分支 `main`、HEAD `c257725e38dcb6681b884b441aaf6becfdfabd04`。既有六份用户差异文件未被操作。参照前轮 P2-3A 与 R1 报告（`reports/solar-pv/phase3e-p2-3a-financial-replay-review.md:48-54`；`phase3e-p2-3a-strict-temp-regression-review.md:26-54`），不把历史测试结果冒充本轮执行。

## A．`finance.cash_flow_basis`：字段、来源、实际控制

- 冻结映射只列 `project.cashflow_tax_basis` 与 `project.ownership_mode`，`producer_formula_ids=[]` 且 `contract_status=FROZEN_MAPPING_IMPLEMENTATION_NOT_STARTED`；映射存在不等于自动生成唯一选择（`docs/solar-pv/05-field-bindings.json:2347-2377`）。原字段税口径允许 `pre_tax`、`post_tax`、`both`；`both` 仅允许两候选，不是唯一评价口径（`03-input-fields.json:972-982`）。所有原字段必须保留其来源信封，经 `input_contract.validate_export()` 重新校验输入及来源快照完整性（`services/solar-pv-engine/src/wangbin_solar_pv/calculation/input_contract.py:31-77`）。
- 独立价格执行控制已有 `basis=项目税前/项目税后`，生产 `_cash_basis` 将其分别映射到项目税口径，校验原字段、所有权记录以及 `both` 的兼容性；它**不能选择股东实际收付**，不能给项目/股东建立折现率，也不能使两个封存案自动有唯一 NPV 评价口径。地面封存案没有 `project.ownership_mode` 记录，无法通过该控制的来源检查（`calculation/break_even_execution.py:64-73,108-141`，上述生产路径前缀同前）。
- 封存屋顶与地面输入均声明 `project.cashflow_tax_basis=both`、`status=UNVERIFIED`；屋顶 `project.ownership_mode=owner_invested` 也是 `UNVERIFIED`，地面缺该记录。两案各有数值 `0.08` 的项目与股东折现率，**四个原字段来源状态均为 `UNVERIFIED` / `USER_PROVIDED`**，数值相同不是同口径许可；方法配置中没有折现率选择项。`finance.project_discount_rate` 必须与项目税口径、名义/实际和时点相容，`finance.equity_discount_rate` 只用于股东流，不能互相替代（`docs/solar-pv/03-input-fields.json:1202-1271`）。封存来源是 SYNTHETIC，不能冒充真实项目核验。
- **无新 Schema 的条件路径仅限项目口径**：若另一项目在现有冻结字段中提供已核验的明确 `pre_tax` 或 `post_tax`，或经来源约束的既有执行控制在 `both` 下显式选定项目税前/税后，并且匹配的项目折现率、真实年度现金流均来源完整，才可能对该指定执行形成唯一口径；须逐项核对原始来源状态、方法、现金流、税基、名义/实际与评价日期，不按收益或 NPV 优劣择口径。股东实际收付还缺独立真实出资/分配/退出收款及匹配股东率，不能用项目控制或项目流代替。**两封存案不满足这些条件。**

## B．`finance.project_terminal_cash`：余额不等于处置现金

- 冻结绑定列 `assets.depreciation.residual_value`、`assets.replacements.salvage`、`finance.working_capital`，但其状态同样是 `FROZEN_MAPPING_IMPLEMENTATION_NOT_STARTED`，无已实现的合法现金生产者（`docs/solar-pv/05-field-bindings.json:2938-2960`）。折旧残值是账面折旧输入；更新事件的 salvage 与运营期旧设备有关，现有 3D 折旧处理不产出完整期末资产净收款；期初营运资金占用更不是新的期末处置收入（`services/solar-pv-engine/src/wangbin_solar_pv/calculation/financial_ledger.py:128-157,214,228-250`）。即使账面残值为零，也不能推出实际终期处置净收款为零。
- 两封存 3D 账簿均含建设期和 25 个运营年度。`OPERATING_YEAR_25` 中屋顶 `working_capital_release=50000`、地面 `=120000` 元，均已在原账簿回收，禁止再加进终期 `S_P,y`。`cash.terminal_collection_fraction` 只结清既有应收并进入 `revenue_cash_receipts`，不是资产出售新收款（`financial_ledger.py:240-250`）。账簿有项目与权益分别计算的所得税和现金税，却**没有**经过来源证明的期末处置交易金额/收款日期、处置成本与对应项目税费现金影响；不能把账面价值、运营期替换折旧或已收应收借作该事实（`financial_ledger.py:228-250`）。
- Phase 2 输入要求原字段来源与重导出身份一致（`input_contract.py:31-77`）；D2 `parameters` 禁止未注册键（`method_config.py:139-167`），D3 是资源/负荷/市场电价序列而非资产处置现金事件。结果 `evidence` 是输出，不是可用作未经校验新输入的绕行接口。现有 3E 明确设置 `finance.project_terminal_cash=None`，`F-PROJECT-CASH-FLOW` 为 `BLOCKED_MISSING_INPUT`，依赖的 `F-NPV` 为 `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW`；返回整体 `PARTIAL` 而非伪项目 NPV（`calculation/phase3e.py:118-149,205-212`）。本文未对封存 3D JSON 运行或篡改 3E 计算；这里是生产路径与既有状态的静态核验。

### 唯一建议的最小承载（**待审批，不实施**）

批准一个**独立、严格版本化、仅限项目期末处置的来源证据承载**，而不是任意年度现金流注入、银行/资金系统或新原始字段。每个事件必须绑定已验证的项目身份、相应 Phase 2／D2／D3／3B／3C／3D 内容身份与资产/残余资金标识；携带来源类型与来源定位、状态/复核人、币种、项目（而非股东）经济边界、明确的收款金额与实际/预测性质、收款日期、处置直接付现成本及其日期、相关项目所得税/其他税/VAT 付现或完整可复核的适用税务事实和日期。对于**经过证明没有处置净收款**的项目，也须有显式、有来源的零事件/无处置声明与税务边界，不能系统默认零；同时须定义终期财务期的归属与评价日期。

读取时校验可追溯来源和状态、金额/单位/时点、源项目与原/候选重算身份一致性；以资产/交易/收款唯一标识对照现有 3D 的替换回收、应收终期收款及 `working_capital_release`，明确只把**未入账的项目期末净处置现金**放进 `S_P,y`，合法相关税费进同一项目的 `T_P,y`，而不篡改现存 3D 年度账簿或把税费再扣一次。股东处置/分配/退出是另一个未获批准且缺实际收付来源的边界，绝不由项目出售自动推断；项目流不包含债务本金、利息、提款或股东事件。

该方案须由用户单独批准新承载的输入来源、与既有 Phase 2/D2/D3/正式结果身份的结合方式、来源审查及税务桥后方可实施。**拟议影响**：不改变 469 原字段、89 公式、281 绑定业务语义、D2 Schema、D3 协议、正式结果 Schema；增加单独版本化受限来源信封及其验证/内容哈希、封存 3D→3E 的新增只读接线和既有结果快照/输入身份关联，并明确税务处理不改 3D 已验收数值算法。如果现行结果身份无法真实承载这份来源，须进一步审批接口兼容性，不得自行重写哈希或伪装旧身份。最小待批代码范围：受限信封解析/验证与排重；Phase 3E 的项目现金流组装及项目现金税桥；只复用已存在 `financial_metrics.evaluate()` 的 `F-PROJECT-CASH-FLOW`、`F-PROJECT-PRETAX-CASH-FLOW`、`F-NPV`；对接现有 `validate_result()` 与只新增输出目录。**本轮没有实施上述任何一项。**

## C／D／E．执行与门禁（逐项回答）

| 问题 | 本轮真实结果 |
| --- | --- |
| 1 现金流基准闭合？ | **否**。`both` 和未验证折现率无法给封存两案唯一、可核验地选项目税前/税后或股东实际流；只有上述条件性项目路径无需扩原字段。 |
| 2 终期现金闭合？ | **否**。实际期末处置净收款、日期及税费缺来源和现成已批准承载。 |
| 3 使用冻结来源/已批准接口？ | **只作只读校验**；复用既有字段、控制和 3D 账簿作审计；没有以输出容器或方法配置虚构新输入。 |
| 4 需要新增业务契约？ | **是**，若要完整闭合终期事实，须先审批上文最小受限承载；未擅自新增。 |
| 5 真正执行 3E 项目现金流？ | **否**；现有生产流程明确将其阻断。 |
| 6 真正计算 NPV？ | **否**；不能发布完整项目 NPV 或价格残差。 |
| 7 独立 Decimal 参考？ | **无完整项目 NPV 参考数值**；前轮仅验证 3C→3D 账簿及数学内核，不能反推伪完整 NPV。 |
| 8 缺事实/最小承载？ | 已核验选择及同口径折现率、真实期末资产处置净现金/日期/税费/排重；受限版本化处置证据方案如上。 |
| 9 重计或混口径？ | **本轮未发生**；已识别并拒绝折旧残值变现、重复加回营运资金、应收再次入账、项目率代股东率等风险。 |
| 10 封存两案状态？ | 原 3D 均为 `CALCULATED_SYNTHETIC`；项目级 3E 仍 `PARTIAL`、相关指标 `BLOCKED_MISSING_INPUT`/上游阻断；**没有改动封存项目，也未升级其门禁**。 |
| 11 完整回归？ | **本轮未运行，不得称本轮 PASS**：没有生产代码改动，且停止条件禁止继续受影响开发。历史 R1 专项 17 passed/1 skipped、光伏 4137 passed/7 skipped、旧产品 109 passed/5 skipped，均为前轮不同目录真实运行且退出 0；符号链接权限项仍 skipped。 |
| 12 本地提交 SHA？ | 本报告与 JSON 仅在核验后作**单个本地文档提交**；由于同一提交不能自引用 SHA，实际值在提交后终端回读及最终交付说明，不在已提交文件内预写。 |
| 13 Phase 3E 当前真实门禁？ | **`PARTIAL/BLOCKED_MISSING_INPUT`；`FULL_PROJECT_NPV_REPLAY_BLOCKED` 是本报告的阻断标签，不是正式状态枚举。** 等待用户审批上述最小契约，并提供具有来源、同口径率与终期事实的独立数据后再决定实施范围。 |

## 保护与可复查性

机器证据 `phase3e-p2-3b-cashflow-source-evidence.json` 记录原始冻结文件哈希、两封存输入/方法/结果文件 SHA-256 及结果自身的 canonical `result_hash`（两者不可混同）、六个差异文件始末 SHA、288 基线的差异、代码路径和本轮测试执行状态。起始对 288 项实际核对为 **286 匹配、2 个预存差异（`reports/validate.json`、`reports/validate.md`）、0 缺失**。报告完成后再次复核全部保护文件、工作区、提交文件集合与基线；旧红色 JUnit 和两封存案例保持原样。不 push、部署或发布；不进入 Phase 3F/Phase 4。