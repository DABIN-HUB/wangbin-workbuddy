# Phase 3E-P2-3B-R1-2/R1-3 实施与验收

## 结论与边界

在**独立、明确标记为 SYNTHETIC** 的一期运营年场景中，已从实际 Phase 2 → D3 → 3B → 3C → 3D 计算结果接入经项目、日期和资产核对的 `NO_DISPOSITION` 来源，执行冻结 `F-PROJECT-CASH-FLOW`、`F-PROJECT-PRETAX-CASH-FLOW`、`F-NPV`；三组电价 0.4／0.6／0.8 元/kWh 的结果与独立 Decimal 参考一致。正式 3E 结果仍为 `PARTIAL`、`real_project=NOT_VERIFIED`，不代表真实项目收益或整份 Phase 3E 全部通过。已记录的营运资金和应收收款不再加回；来源未能证明交易级排重的 `EVENTS` **一律拒绝进入项目 NPV**。未实施盈亏平衡电价根搜索、P2-4、P2-5、Phase 3F、推送、部署或发布。

起始分支 `main`，HEAD `2c304d9c564f0542e21f05fee84117a80148797e`；六份用户既有差异未改。冻结的 469 输入字段、89 公式、281 绑定语义、D2/D3、结果 Schema、3B/3C/3D 数值算法、既有 IRR 及两份封存案例均未更改。唯一 R1-1 代码兼容改动：`terminal_disposition.py` 的 `phase2_source_snapshot_id` 在保留裸 SHA-256 的同时接受真实 Phase 2 导出的 `sources-<SHA-256>`；其他 R1-1 Schema 和经济含义未重写，R1-1 原有 15 用例在本轮 smoke 中通过。

## 二十项审查结论

| # | 问题 | 真实结论及证据 |
|---|---|---|
| 1 | R1-1 保持不变？ | **不是完全逐字不变**；仅作上述真实快照 ID 格式兼容，未修改旧来源经济字段或两个封存案。 |
| 2 | 当前候选 3D 真绑定？ | **是，仅对满足门禁的 SYNTHETIC 场景。** `terminal_binding.py:70-126` 验证 Phase 2、D2、完整 D3、3B/3C/3D 正式哈希，复用 `_check_settlement()`、`_check_financial()` 并用批准的 3D 生产者重新计算账簿；`phase3e.py:261-274` 又要求从原始 export/D3 仅派生选定电价。 |
| 3 | 错误来源能冒充 3C/3D？ | **不能通过当前门禁。** 逐字段篡改并重封来源仍被拒；重封 3D 的错误上游也被拒。11 项身份变异及旧候选绑定负例见 `binding.xml`、`npv.xml`。 |
| 4 | 资产来自真实账簿？ | 3D `financial-ledger.depreciation.records` 与已验证 Phase 2 的 `capex.items`、`assets.depreciation`、`assets.replacements` 和 3D `capex.ids/replacement_links` 对账后形成覆盖集合，而非仅采用来源自报清单。 |
| 5 | 资产与事件覆盖完整？ | **已验证的无处置场景：是。** 唯一资产 `SYNTHETIC-asset` 完整覆盖；来源字节还须明确 `project_id` 与 `terminal_date`。**有处置交易：未证明，仍阻断**；没有把缺交易证据当作零事件。 |
| 6 | 哪些事件证实无重复？ | 无新增处置收款、直接成本及新增处置税；财务年度记录的应收终期结清已含在收款中，末年营运资金 `200` 元已含在 3D。未对任何有处置交易作未重复入账的肯定断言。 |
| 7 | 具体账簿来源？ | `financial-ledger.capex.ids/replacement_links`、`depreciation.records`、`annual[*].revenue_cash_receipts/receivables_terminal_collection/working_capital_increase/working_capital_release/cash_tax_total_project/income_tax_cash_paid_project/other_cash_taxes_project/tax_cash_bridge_project/vat_output/vat_input_eligible`；以及 `NO_DISPOSITION` 原始字节 SHA-256 和受控绑定。 |
| 8 | 税费重叠？ | 无处置场景的新增所得税、其他税和 VAT 向量均为零；`T_P` 只取当前候选的 3D 项目已付现金税一次。税前向量只加回项目所得税，不加回 VAT 或其他税。事件模式无交易级证据，不计算其增量税。 |
| 9 | 价格变化重算税？ | **是。** 0.4／0.6／0.8 的实际 3D 重新运行，项目所得税运营年分别 `0.000`、`2182.5000`、`4372.5000` 元；VAT 分别 `3888.15044247787610619469027`、`5903.72566371681415929203540`、`7919.30088495575221238938053` 元。未复用旧电价税额。 |
| 10 | 金额及日期？ | 来源声明与来源字节均明确 `terminal_date=2025-12-31`；评价日 `2024-12-31`，投运日 `2025-01-01`，D2 为运营年、年末现金流；建设期与 `OPERATING_YEAR_1` 各一项。`EVENTS` 的任意实际付款日期没有获准折算为年末流。 |
| 11 | 唯一口径？ | 此 SYNTHETIC 案例已取得有来源、授权且标 `ASSUMED` 的项目税后名义 CNY 年末折现率 `0.1`，执行控制选择项目税后；没有把 `both`、项目/股东或实际/名义混为同一口径。 |
| 12–14 | 三个冻结公式运行？ | **都实际运行**：`phase3e.py:316-338` 调用现有 `_record()` → `financial_metrics.evaluate()`，分别以 `F-PROJECT-CASH-FLOW`、`F-PROJECT-PRETAX-CASH-FLOW`、`F-NPV` 产生封存指标；回读 `validate_result()`、结果哈希与 sidecar。旧缺数路径维持阻断。 |
| 15 | 独立 Decimal 参考？ | 独立测试按 3D 批准税算法使用 28 位 Decimal，以 80 位 Decimal 手算 3E 年末流和折现。三组参考 NPV（元）分别为 `146523.49959774738535800482702727272727272727272727272727272727272727272727272727`、`154652.52212389380530973451327272727272727272727272727272727272727272727272727273`、`162774.72646822204344328238133636363636363636363636363636363636363636363636`；本轮再次独立计算的差异均为 `0E-74`。 |
| 16 | 三候选数值与哈希？ | 见下表及机器证据。**同一轮**原始来源哈希相同，Phase 2/D3、3C/3D、候选绑定、3E 结果分别不同，3B 一致；0.6 候选在同一来源与上游结果下做 JSON 往返重算，完整 `result_hash` 相同。两次独立测试轮次的输入来源时间戳、run ID 和消费数据哈希不同，不能把跨轮次结果哈希不同误报为同一输入不稳定。 |
| 17 | 两份封存项目？ | 屋顶与地面原案例仍为 SYNTHETIC；`cashflow_tax_basis=both` 未核实唯一口径、项目折现率 `UNVERIFIED`、缺当前候选终期声明；地面还缺所有权来源。其原 3D 已含营运资金回收 `50000`／`120000` 元，均不得再加回。两案输入／方法／结果文件 SHA-256 与此前审计逐一一致；未生成它们的项目 NPV。 |
| 18 | 本轮回归？ | 本轮 `binding.xml` **16 passed**；`npv.xml` **3 passed**；`solar.xml` **4171 passed、7 skipped**；`legacy.xml` **109 passed、5 skipped**。四次实际退出码均为 0；跳过均为 Windows 符号链接权限不足。TMPDIR 与 pytest `--basetemp` 分离，JUnit、完整测试 ID、跳过原因分别保存在同目录 XML、`all-test-ids.txt` 与 `evidence.json`。 |
| 19 | 分阶段本地提交？ | R1-2A `1ace1fb76ce9f72c92865393bb3955ec2b93cd92`；R1-2B `822676d1f92323b23d9448686737dfaf5458526c`；R1-3A `227a6883043b15d557de57fbf56f50fc844f1067`；R1-3A 的同源重算哈希稳定性修复 `102cf3cd66ac13c399548308462f43516ce92fab`。本报告所属 R1-3B 提交不能在自身内容中预写自己的 SHA；提交后终端及最终交付单独回读。 |
| 20 | 剩余问题？ | 有处置交易仍缺交易级 3D 入账身份、收付/成本/VAT/所得税/其他税排重与当前候选税基适用性证明；不为其生成 NPV。股东实际收付、动态现金覆盖、DATED-NPV、IRR 等非本次已接线指标未升级，原结果仍 `PARTIAL`。没有将 `NOT_IMPLEMENTED` 的项目收益接线误称为现金流缺失。 |

### 单一来源轮次的项目数值

| 电价 元/kWh | 首年开票 元 | 建设期现金流 元 | 运营年项目税后现金流 元 | 运营年项目税前现金流 元 | 项目 NPV 元 |
|---:|---:|---:|---:|---:|---:|
| 0.4 | 35040 | -1330 | 162638.84955752212389380530973 | 162638.84955752212389380530973 | 146523.49959774738535800482702727272727272727272727272727272727272727272727272727 |
| 0.6 | 52560 | -1330 | 171580.77433628318584070796460 | 173763.27433628318584070796460 | 154652.52212389380530973451327272727272727272727272727272727272727272727272727273 |
| 0.8 | 70080 | -1330 | 180515.19911504424778761061947 | 184887.69911504424778761061947 | 162774.72646822204344328238133636363636363636363636363636363636363636363636 |

两期向量均为 `[CONSTRUCTION, OPERATING_YEAR_1]`。实际收款是开票额的 `0.75`，不将开票误记为实收；已在账簿的 `200` 元营运资金释放只体现在项目现金流的工作资本净变动，不进入终期新增资产现金。任何 `EVENTS` 声明在交易级排重证明不足时由 `TERMINAL_TRANSACTION_LEDGER_PROOF_MISSING` 拒绝，故上表只适用于经过来源和资产全覆盖证明的无处置 SYNTHETIC 场景。对事件专项清单中尚无可合法计算的处置税、付款日及重复交易正例，不宣称已数值验收。

## 证据与保护

- 机器证据：`reports/solar-pv/phase3e-p2-3b-r1-2-3-evidence.json`。原始 JUnit：同目录 `binding.xml`、`npv.xml`、`solar.xml`、`legacy.xml`；完整 `classname::testname`：`all-test-ids.txt`。JUnit 四份 SHA-256 分别为 `d486baa757b0d5793b8f6ad9fe24fe90eeb464a7f6d72841691e7a0113c49d80`、`7efda816883a18f41732ff720e050fd394d8a0f6e8ddbfa24b685bd5ee20b3e4`、`24be2e5fe48136af70ae39b7a5f3fe759dfd2bd444e68f6e89b2902633e03ab3`、`f40cc65091d888fc8bc49788fab6439b1b6a4a4d6d0bcf38c74be266d2101aa2`。
- 保护基线 `phase3c-startup-state.json` 的 288 项核对为 **286 匹配、2 项既有差异**（`reports/validate.json`、`reports/validate.md`）、**0 缺失**；六份用户原有差异文件始末 SHA-256 在机器证据中分别记录，不暂存或修改。
- 本报告记录的是本轮真正跑出的退出码/JUnit，而不是以历史 4137／109 成绩代替本轮。结果样本的正式哈希不是源文件 SHA-256；未在任何报告保存凭据。没有执行自动推送、部署、发布或扩大 Phase 3E 阶段。
