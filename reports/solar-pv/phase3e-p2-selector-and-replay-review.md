# Phase 3E-P2：受控选价、合成候选重放及冻结现金来源核查

## 范围与裁决

**P2-1 / P2-2：限定范围内完成；项目级 Phase 3E：BLOCKED_MISSING_INPUT。** 本报告只认证版本化单原子选择、合法 Phase 2 / D3 合成候选以及保持 3B 不变的两次真实 Phase 3C 收益重算。不认证 Phase 3D/3E 候选现金流、NPV、正式 F-BREAK-EVEN-PRICE、全根证明或价格/货币残差；不进入 P2-3、3F/3G。本轮两组全量回归在所述最终代码候选上完成；机器证据为 `phase3e-p2-selector-and-replay-evidence.json`，逐项测试 ID 和原始 JUnit 位于 `phase3e-p2-evidence/`。

- P2-1 本地提交 `c53e235137e04f3762471184b744966a8f83c470`：独立 `solar-pv-break-even-execution/1.0.0` Schema，严格 `additionalProperties: false`；校验项目/类别/公式、单个 field_id/row_id/field_instance_id/原子哈希、原 Phase 2 输入与来源快照、D2 方法身份、原 D3 内容身份、经济基准和实际结算模式；市场价必须有完整可读 D3，负价须有原约束及适用规则。四种 P1 对象分别守卫，分时行不可合并为一个变量。专项先红后绿，最终 P2-1 JUnit：17 passed、0 failed/error/skipped。
- P2-2 本地提交 `a2cbd7aaf2090e6b2eba2358243f293f1d9d7455`：私有原子派生登记原来源候选和独立 `ASSUMPTION` 情景来源，重新从 `IntakeSession.export()` 生成并由 `validate_export()` 验证候选，保留未选中字段及行的原子字节语义；从原 D3 完整流式重封各数据集，验证逐数据集 hash/头来源与候选 bundle 的独立身份；两次调用现有 Phase 3C 并核真实非零结算影响。失败不返回候选结果，且仅按工作目录所有权、成员与非链接/非硬链接检查清理本次私有输出。3C 的逐时价格来源现在进入实际收益指标的 `source_ids`。候选重放专项经过先红、修复、再红、修复，最终 JUnit：7 passed、0 failed/error/skipped。
- 未修改 D2 Schema、D3 协议、469 字段、89 冻结公式、281 域绑定、3B 结果、两份封存项目、正式结果 Schema、IRR 或 Phase 3E 编排。`revenue.py` 只补齐已结算的逐行价格来源汇集，继续调用原有收入计算；没有第二套结算、税费或现金流引擎。

## 可复核的独立 SYNTHETIC 实跑（非项目正式结果）

合成项目 `SYNTHETIC-industrial_rooftop`；被选中 `tariff.periods.sale_price`，`row_id=flat`，`field_instance_id=price-flat-sale_price`。原子价从 0.4 到 0.6 元/kWh，仅此行的此原子变动；另行的未选中价格保留专项已单独验证，原来源记录与新的情景覆盖来源分别保留，候选价来源 `SYNTHETIC:p2-replay` 在收益指标 `source_ids` 中可读取。原输入/原 D3/3B 结果只读，原和派生 Phase 2 均经过既有验证，原和派生 D3 均经过既有全量读取校验。

| 身份或数值 | 实跑值 |
|---|---|
| 原 / 派生 Phase 2 input_hash | `772edb427abd5113c45c5002802a348f0565e874ae642f2df378af41a9843b8c` / `4f0dad3f176bce6ce915dfe4a404fefdb4cfff09dbe4c12c5b1c74c4c82b8caa` |
| 原 / 派生 D3 content_hash | `8eb27e8cfdd07ea9aab525cd343c921996537bf27ab2b7fc65c48738dcad37c5` / `6e0f8d6422f811277c96f3de322278afba111f1feae2eb9adc538282178c7cc7` |
| 原 / 派生资源 canonical_array_hash | `2f0034a9ec349672305315601d663cb4fcb759c827ddc1a9a6e1edc1cd25259e` / 同左 |
| 原 / 派生负荷 canonical_array_hash | `aed869034586dda82be55e903cd1883b292c83a863d1af71094176097d248d9d` / 同左 |
| 固定 Phase 3B result_hash | `f4506bc824da44f131512dd5c9a7ed908cfb8e3f371de860737950ff690fab98` |
| 原 / 派生 Phase 3C result_hash | `7825b76e4279722e9b16fb086164260ba358b81638339171b11c9218c8345598` / `f2ca0e86f3d75e82c05e94197545cd845804d01a7026d563a366547d8a5309f5` |
| 原 / 派生首年外售收入（CNY） | `35040.0` / `52560.0` |

独立 Decimal 参考：差额 `17520.0 = 87600 × (0.6 − 0.4)`，分别来自真实 3C 年度账簿；重复相同候选得到相同派生导出、D3 内容身份和 3C `result_hash`。3C 收据记录 8760 行发电和 8760 行负荷。另一个市场价 SYNTHETIC 专项将完整 8760 行 D3 单行派生后重新读取，确认仅目标行价格变、原块不被修改，验证所需预算与来源；**该市场专项不是市场价 Phase 3C 真跑数值证明**。PPA 固定价及屋顶可避免购电价由 P2-1 专项核选择适用性，但未在此表声称四类各自完成 3C 全链实跑。

失败路径专项包含非法来源、错误原始原子/项目/结算方法、重复行身份、缺失市场原始 D3、超出 D3 行预算、错误 3B 哈希、未来未参与结算价格行拒绝、失败后不发布有效候选及不删除原件。真实财务结果不得从上述合成收益差额推断。

## 两份封存案例的冻结财务来源（只读）

`docs/solar-pv/05-field-bindings.json` 的 `finance.cash_flow_basis` 映射 `project.cashflow_tax_basis` 与 `project.ownership_mode`，定义是“项目税前、项目税后、股东实际收付中的一个完整口径标签”，绑定状态本身为 `FROZEN_MAPPING_IMPLEMENTATION_NOT_STARTED`。03 原字段允许 `pre_tax/post_tax/both`，但没有把 `both` 自动化为唯一标签的规则。修复后封存的屋顶和地面 `input.json` 中，税口径均为 `both` / `SYNTHETIC-phase3d-repair` / `UNVERIFIED`；屋顶权属为 `owner_invested` / `SYNTHETIC-settlement` / `UNVERIFIED`，地面权属缺失。屋顶可在执行控制明确选择已有税前或税后候选时形成**条件性标签**，但两案都没有由此证明完整同口径的项目或股东实际现金流；地面连权属标签也欠缺。股东折现率不能用项目折现率代替，不能创设新口径枚举。新的执行控制 `basis` 仅限制选择，不能制造财务事实。

`finance.project_terminal_cash` 绑定 `assets.depreciation.residual_value`、`assets.replacements.salvage`、`finance.working_capital`，冻结定义是“期末处置净现金和未在 ΔW 中回收的残余资金，税务影响进 T”；映射不等于三个数直接相加。两案的折旧资产残值及更换资产残值均有 `SYNTHETIC-phase3d` / `UNVERIFIED` 来源，属于账面折旧/更换设备相关账面假设，**不是独立的终期现金到账**。3D 的 `_depreciation()` 记录被更换旧资产的账面处置与新资产残值，没有生成处置收款。两案营运资金各有同类 SYNTHETIC 来源：屋顶 50,000 元、地面 120,000 元；3D 末年账簿 `working_capital_release` 已分别入账 50,000 / 120,000 元，不能重复加为终期现金。未见独立可核的终期处置对象、净收款金额、收款日、税务现金影响和未回收资金对账，也无可直接复用的已验证完整终期处置现金事件承载。`phase3e.py:123-147,191-203` 仍将终期现金置空并使依赖公式阻断；不得补零或自动制造合同、股东收付与退出时间。

**P2-3 进入条件：**先在既有冻结边界内核对单一项目/权益及税前/税后口径、合法折现率、真实来源的终期净处置现金及日期、已入账营运资金/更换处置/税影响不重复、股东实际收付及日期，并对两案分别完成可核来源与全链调用；若冻结契约无此承载能力，提交最小差异另行审批。本轮不开展 3D→3E 候选重算、NPV、价格求根或价格残差验收；两封存案例维持 `BLOCKED_MISSING_INPUT`。

## 回归、保护与交付门禁

- 本轮光伏全量回归 `python -m pytest tests/solar-pv -q`（附加隔离临时目录与 JUnit）：退出码 **0**，JUnit `solar-final.xml` 显示 **4127 passed、6 skipped、0 failed/error**，合计 4133 测试 ID。P2-1 专项 `p2-1-selector.xml`：**17 passed**；P2-2 专项 `p2-2-replay.xml`：**7 passed**。专项已包含于全量集合，不相加为额外测试数。
- 旧产品回归 `python -m pytest tests --ignore=tests/solar-pv -q`（附加隔离临时目录与 JUnit）：最终 `legacy-final.xml` 退出码 **0**，**109 passed、5 skipped、0 failed/error**，合计 114 测试 ID。此前两次让 `TMPDIR` 与 pytest `--basetemp` 同路径的整组运行各为退出码 **1**、**108 passed / 1 failed / 5 skipped**，均是未修改的文档 CLI 跨进程容量锁用例 `tests/test_phase3_security_limits.py::test_capacity_is_enforced_across_cli_processes`；其失败 JUnit 分别保留为 `legacy-initial-failed.xml`、`legacy-repeat-failed.xml`。相同源码下将两目录分离后定点两项通过、整组通过，故仅把分离目录的整组运行作为本轮旧产品绿门禁，不抹去失败历史或修改无关模块。
- 六份用户既有差异文件开始、阶段提交前、最终 SHA-256 一致，未修改、未暂存、未清理；288 项历史基线最终为 **286 匹配、2 项既有差异**（`reports/validate.json` / `reports/validate.md`）、**0 缺失**。哈希列于机器证据。此处的 286 匹配不是声称另外两份等于旧基线。
- 机器证据保存四组最终 JUnit 和两次未通过 JUnit 的 SHA-256、退出码、计数、完整测试 ID/跳过 ID/失败 ID、只读候选身份及金额、财务阻断和用户保护哈希。没有 push、部署、发布或进入 Phase 3F/3G。
