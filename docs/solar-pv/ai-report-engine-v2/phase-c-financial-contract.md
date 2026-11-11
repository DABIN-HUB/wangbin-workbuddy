# Phase C 财务评价与候选证据契约

状态：**PARTIAL，非完整 Phase C 验收，不是投资批准**。版本仍为 SOLAR-PV-AI-REPORT-ENGINE-2.0.0；未修改冻结公式、会计方法或旧计算生产者。

## 已实现的独立评价

入口为 `reporting.financial_evaluation.evaluate_financial`，以及 `python -m wangbin_solar_pv.reporting evaluate --canonical <canonical.json>`。输入重新通过原 ReportModel 验证；输出绑定原五项身份、期间、币种、折现率、原指标状态/原因/公式/来源和评价 hash。此入口是本地审阅，不是向模型传输数据的授权。

| 评价 | 本轮两案实际状态 | 边界 |
| --- | --- | --- |
| 会计盈利年度 | NOT_CALCULABLE | 缺独立会计净利润生产者和确认口径；应税所得、税务折旧与销售额不替代净利润 |
| 经营现金流转正 | NOT_CALCULABLE | 年度为正与累计转正分别留槽；现有项目现金流不是独立经营现金流；屋顶节费不冒充现金销售回款 |
| 静态投资回收 | CALCULATED | 原项目现金流与累计生产者，保留建设期、税费、更换等边界 |
| 动态投资回收 | CALCULATED | 原项目折现率及折现累计现金流，不生成精确日历回本日期 |
| 项目投资回报 | CALCULATED | 原项目 NPV/IRR，保留完整根集详情，不择优取根，不混入股东回报 |
| 股东资金回收 | NOT_CALCULABLE | 独立股东出资/分配/退出及回收生产者未闭合，原股东指标状态同时保留 |

输出另列“首次项目净现金为正期间”，明确它既不是会计盈利年度，也不是经营现金转正或累计回本。没有投资目标不判达标；具备单一认证 IRR 根、同口径目标或投资起点回收目标时仅输出模型假设下的条件比较。未匹配的时间起点、预算与专业准入继续待核。所有状态均不等于真实工程/投资可行。

会计、经营和股东缺口属于当前生产者/口径能力未闭合，不应统一归咎于用户未给资料。若要定义新的会计方法或现金分类边界，应先取得专业裁定；本轮没有以报告层自行求和填补。

## 已执行候选的验证与比较

入口为 `reporting.scenario_comparison.compare_scenarios`，以及 `compare --canonical <canonical.json> --scenario-bundle <scenario-evidence.json>`。bundle 只保存在本地；章节请求只携带获授权的受控事实和表格。

bundle 包含原 Phase 2 export、methods 和最多八个已执行条目；每条包括 control、原始 prepared_export、3D/3E results 和真实 runner receipt。验证内容：

- 原基准 Phase 2 输入/来源身份；合法控制、可变变量及方法约束。
- 原 prepared_export 通过原输入校验，与重新 prepare 的经济值、来源、单位、许可语义一致。
- prepare 会重新生成候选 ID 和 last_updated；二者不用于跨次语义比较，但**封存核验始终使用实际执行时保存的原 prepared_export 哈希**，不以重新生成的身份覆盖真实回执。
- 使用原 `seal_scenario_run` 验证各阶段身份与回执；拒绝重复运行/结果、错误项目和类型、篡改回执。
- 比较同币种、价格/税后口径、日期、期限、折现率、现金流时点及容量边界；完整指标和唯一认证 IRR 根不足时不排名。
- 至少两个同口径有效候选才提供条件性税后 NPV 顺序；不声明全局最优，不证明工程约束、风险或资金条件已满足。
- 初始项目净现金与初始 CAPEX/资金需求区分。未形成独立资金需求结果时，表格不凭空填数。
- CH06.04/.05、CH17.01/.02 的数值由程序绑定到候选结果身份；CH17.01 过滤非单因素候选。CH17.03 仍使用冻结的 break-even/hurdle 原指标表，不用情景点冒充阈值求解。
- 未授权候选不进入事实/表格。缓存绑定 bundle hash，变动使 accept/resume 拒绝。

## 两案实际运行及未闭合项

本轮复用已有屋顶和地面合成示例，分别真实执行一个显式 SYNTHETIC/ASSUMED 运维费用压力候选（原维护费乘以 1.05），不是市场报价或真实客户数据。每案均保留基准和候选两行、独立运行身份与 3D/3E 回执。

两案候选的原引擎项目现金流均返回 `BLOCKED_MISSING_INPUT`，详细缺口是 `finance.project_terminal_cash` 与 `transaction_cost_cash_paid`；NPV、IRR、静态/动态回收随后为 `BLOCKED_UPSTREAM_PROJECT_CASH_FLOW`。这是当前通用 scenario_runner 路径没有接续同身份终期/交易费现金来源的集成缺口；不能推断用户没有原始资料，也不能移用基准已绑定的结果或补零。

因此本轮实际比较状态是 **NO_VALID_MULTI_CANDIDATE_COMPARISON**，ranking 为空。不能声称已完成收益优化，更不能用“已有两行”冒充两个可比的有效方案。终期及交易费用来源的候选重绑定、正向多候选排名验收、容量/负荷/布局等优化路径尚未闭合。

当前阶段交付的是可运行的评价/校验适配及真实缺口证据，**不是用户全部 Phase C 目标已经实现**。

## 实际验证与失败记录

证据根：`.runtime/solar-pv/ai-v2-bcd-20261111/`。

- `phase-c-executed-v2/<类型>/`：control、prepared-export、实际 scenario 3D/3E、sealed receipt、完整本地 bundle、comparison、evaluation-final。
- `protocol-verified/`：CH17 prepare/accept/resume 和 NOT-AI 协议 DOCX；它不是 Phase D 样本，也不证明模型调用。
- `negative-cache/`：专门隔离的篡改负例，未破坏有效运行证据。
- `negative-evidence-receipt.json`：无授权不泄漏数值、伪造回执拒绝。
- `cli-evaluate-*`、`cli-compare-*`：公开 CLI 的真实退出码和输出。
- 财务评价新增专项 13 项通过；原财务 kernel 专项 17 项通过。完整分组见 final-verification-summary.json，不能与历史重跑重复累加。

保留的失败：首次候选比较使用重新 prepare 的新身份导致封存不匹配，改为保留并验证原 prepared_export；首次协议检查发现有效候选已登记但未消费来源不能列入白名单，补全已验证候选的已知来源集合；一次检查误把 CH17.03 当比较表，按冻结契约纠正检查而不改规格；无授权多行重复缺口触发 uniqueItems，改为按实际结果身份区分缺口。原失败 log/exit 回执均保留，不覆盖成 PASS。

## 恢复与后续门禁

先运行 spec-check，使用存量 canonical 与 bundle 重跑 evaluate/compare；不要覆盖原目录或重算原项目来掩盖状态。旧 generation run 没有 scenario_bundle_hash 时会被新校验拒绝，应创建新 run，不手工修改缓存。

在专业口径和候选现金来源闭合、正向可比结果获得后，再补相关验证。真实宿主未独立核验，Phase D 仍 NOT_EXECUTED；独立专业 QA、完整四文件、PDF 及平台发布均未通过。本轮不进入 E/F/G。其他扩展仅进入 AFTER_V2，不启动 2.1。
