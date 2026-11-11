# AI Report Engine 2.0：Phase A/B阶段交付

日期：2026-11-11。范围：同一独立会话、隔离工作树内的需求冻结和基础框架；未进入C—G，未替换旧报告入口，未删除任何固定正文。

## 1. 本次结论

**Phase A规格冻结完成；Phase B本地章节协议与Word装配可运行，但真实模型集成仍阻断。** 本次不是完整AI报告产品验收。不存在可供用户审核的真实AI试点正文，协议测试样本不能顶替Phase D。

| 状态 | 当前结论 |
|---|---|
| REQUIREMENTS_FROZEN | 已完成结构与覆盖验证；专业提示词效果仍需真实试点 |
| ARCHITECTURE_READY | A/B设计、协议、Schema与阶段计划已落盘；宿主adapter条件明确 |
| FRAMEWORK_IMPLEMENTED | **PARTIAL**：本地最小链路通过；遵照正式任务，不因Mock/协议fixture就宣称完整AI框架完成 |
| LLM_INTEGRATION_VERIFIED | **MODEL_INTEGRATION_BLOCKED** |
| PILOT_CONTENT_REVIEWED | NOT_STARTED，须真实双类型试点及用户确认 |
| ALL_CHAPTERS_GENERATED | NOT_STARTED |
| FACT_VALIDATION_PASSED | 未通过整报告门禁；局部仅STRUCTURE_AND_REFERENCES_VALID |
| FOUR_FILES_GENERATED | NOT_STARTED（2.0） |
| FULL_DELIVERY_VERIFIED | NOT_PASSED |
| PLATFORM_RELEASE_READY | BLOCKED |

## 2. 交付索引

路径相对隔离工作树 `F:/ideaWorkSpace/wangbin-workbuddy-ai-report-engine-v2`。

- 冻结需求：`docs/solar-pv/40-ai-report-engine-2.0-requirements-frozen.md`。
- 18章总提示词、100小节任务、13附录/26节及字段/指标/公式/表格映射：`services/solar-pv-engine/src/wangbin_solar_pv/reporting/specs/report-spec.json`。
- 126条正文/附录验收矩阵：`docs/solar-pv/ai-report-engine-v2/acceptance-matrix.json`。
- 冻结hash：同目录 `freeze-manifest.json`；包内 `reporting/specs/spec-lock.json`。
- R13调用链、固定正文识别、模块复用/重构判断：`baseline-audit.md`。
- 架构和A—G计划：`docs/solar-pv/41-ai-report-engine-2.0-architecture-plan.md`。
- 必要例外：`V2-EXC-001-host-model-exchange.md`，不改Phase A冻结文本。
- 源码：`services/solar-pv-engine/src/wangbin_solar_pv/reporting/`下10个Python模块。
- 专项测试：`tests/solar-pv/test_ai_report_spec.py`与`test_ai_report_engine.py`。测试编写/运行来自本任务第十一节明确授权。
- 原始执行回执、JUnit、局部Word、wheel核验：`.runtime/solar-pv/ai-report-engine-v2/`，忽略且不作为平台包。

规格SHA-256（UTF-8/LF）：`885b92420ee3bbfd9b6ce473ed764584a224d9c246e0d294be638a549fd85f91`。

保护计数：18章/100小节、13附录/26小节、469字段、89公式、281映射、189术语。字段/公式/映射继续通过原Catalog定义锁验证，不改变原计算hash。

## 3. 实际运行与测试

全部pytest运行有180秒进程上限；每次写独立JUnit和exit receipt，不运行全仓。

| 回执前缀 | 选择 | 结果 |
|---|---|---|
| phase-a-final | test_ai_report_spec.py | 102 passed，0失败/错误/跳过，exit 0 |
| phase-b-close-roof | test_ai_report_engine.py -k 'industrial_rooftop or host_integration' | 36 passed，exit 0 |
| phase-b-close-ground | test_ai_report_engine.py -k utility_scale_ground | 35 passed，exit 0 |
| phase-b-finance-regression | test_phase3e_financial_metrics.py + 原数值单位显示测试 | 18 passed，exit 0 |
| phase-b-legacy-export | 原完整Word样式/章节/公式三项 × 双类型 | 6 passed，exit 0 |

最终分组选择共197项通过，0失败/错误/跳过；两种类型的分组互补，未将deselected当作执行通过。最终命令/退出码/JUnit位置在 `close-verification-summary.json`；`verified-runs-summary.json`是此前195项快照。收口前补入“不得省略冻结必需表格”负例，两种类型完整复跑。全部新模块测试及这些旧入口专项通过不等于全仓通过。

历史执行不抹除：`phase-b-first`合并运行180秒超时，exit 124，无最终JUnit，最终计数未知；`phase-b-isolate`遇首错退出，26项中25通过/1失败，exit 1。错误是负例把没有缺证的首节当成必须报缺证的章节，改为选择证据包实际有缺证的小节，未放宽生产校验。其后按类型完整运行通过。

Wheel首次 `python -m pip wheel`因当前Python没有pip退出1；没有混用另一Python的pip或安装依赖。改为现有uv、显式同一解释器、`--offline --no-build-isolation --no-python-downloads`实际构建成功。wheel包含10个模块与2个规格JSON，规格锁重新校验通过。其版本沿用既有包0.3.1，报告研发规格是2.0；此wheel仅核验包数据收录，不是新发布候选。

## 4. 最小端到端实物

`cli-protocol-check/commands.json`保留实际公开CLI：status（exit 3）、spec-check/schema及两案prepare→accept→resume（exit 0）。明确使用 `model_id=protocol-fixture-only`、`host_call_id=PROTOCOL_FIXTURE_NOT_LLM`，正文也是协议检验说明，不是AI专业样本。

每案第八章局部DOCX均读回：动态字段位置在章标题之后、首小节之前；6个二级小节、4张受控表、12个可编辑OMML；无残留fact占位符；原canonical哈希未变。原件和回执位于：

- `cli-protocol-check/industrial_rooftop/protocol-fixture-not-AI.docx`
- `cli-protocol-check/utility_scale_ground/protocol-fixture-not-AI.docx`
- `cli-protocol-check/receipt.json`

屋顶DOCX SHA-256：`0db407930b816f7dc615f6c80e02e75579c6a2c467b33aebbfd190bdb127d38f`。

地面DOCX SHA-256：`6c0d5e64370287428e577eb42e92ae0e8d17b125899e7ff4e5f5b310ec1b82f1`。

Word装配使用独立安装Pandoc 3.13和原公式转换器；未安装新依赖。未启动WPS/Word刷新或PDF导出，未作页面视觉验收。既有公式来源冲突及PDF数学文字层缺陷依然未闭合。

最后源码再次resume并验证上述相同DOCX hash，记录在`final-source-artifact-revalidation.json`。该次首次探测误用execute_code内核的基础Python，因缺docx退出1；改用实际pytest回执中的同一venv解释器后两案退出0，没有安装依赖。

## 5. 操作入口与恢复

在隔离工作树根目录，Windows Git Bash源码环境：`PYTHONPATH='services/solar-pv-engine/src;services/document-engine/src'`。执行 `python -m wangbin_solar_pv.reporting --help`查看完整参数。

- `spec-check`核验规格；`schema`输出证据包和章节结果JSON Schema；`plan`输出依赖顺序，摘要最后。
- `status`没有授权宿主adapter时返回阻断及exit 3，绝不假成功。
- `prepare --canonical <明确授权的canonical.json> --workspace <已存在的输出根> --run <新运行名> --chapter CH08 --model <实际模型ID> --authorized-source <允许发送的来源ID>`生成请求。多来源重复提供授权参数；不提供则无事实值，非自动全量授权。
- 宿主须读取request约束，实际调用后写响应JSON：`request_hash/model_id/host_call_id/output`。不能把本轮fixture当作宿主实现。
- `accept`提供相同canonical/workspace/run/model和预算参数，以及`--request-id CH08-1 --response <run内响应文件.json>`；可加`--docx <新文件.docx>`。公式引用需要现有Pandoc路径通过`WANGBIN_SOLAR_PV_PANDOC`传入。
- `resume`使用同一绑定重验已接受结果；修改模型配置、输入、来源、规格或正文均不复用旧成功缓存。失败尝试不会改写为成功，需在剩余预算内重新prepare；超出预算明确停止。

文档提供的是当前实际CLI，不承诺自动provider。输出目录授权只是本地边界而非OS沙箱；远程token/费用、工具权限及真正调用超时仍由将来授权宿主执行并出具回执。

## 6. 未闭合事项及下一门禁

1. **真实模型路径**：无已验证宿主调用。需要用户确认/提供正式可用的WorkBuddy宿主编排或授权provider适配条件；不得读取其他会话凭据。改变平台方案若属B类须审批。
2. **嵌套来源与时序专用适配**：B只提供安全标量与有限计算序列；未绑定数据明确适配缺口，不推断用户没有提供资料。图表引用暂空，须在后续实现受控图数据绑定。
3. **上游结论与全报告语义**：当前request列出未供给上游，不能把它视作已研究完成。C/D前应实现已验证上游结论注入；E实现完整跨章一致性。引用合法不证明因果或审批结论成立，专业审核不能省略。
4. **Phase C**：会计利润、经营现金、项目静动态回本、股东现金事件仍须分离；未增加新指标或情景算法。
5. **Phase D**：至少双类型重点章真实模型内容、R13对照与用户内容确认；未经确认不进入E。
6. **原R13门禁**：PDF公式复制/搜索、数学语义裁定、真实工程资料、许可证及平台安装/发布独立保持未通过。

## 7. Git、资产与卫生

原工作区main保持 `ecaac498e3d14dbae4874e7fa46e63d74c5da2df`，只读核验status为空。重构只在 `refactor/solar-pv-ai-report-engine-v2`。

Phase A独立commit：`2723d7a04b8f43a3b3aeac78e5b5ded21c2103a1`。本文件随Phase B本地源码提交；确切B SHA及最终status另存运行目录 `final-state.json`并在最终回复给出，避免文档自引用提交hash。

- 旧计算、report/ground-report、Skill/Connector、R8—R13历史文件无修改/删除。
- `pyproject.toml`只新增reporting规格JSON打包声明，没有依赖/版本变更。
- 已跟踪历史资产净删除0、释放0；保留原有效dist两包，ZIP、manifest逐成员hash及sidecar均已核验，仍被忽略。它们不是2.0发布包。
- 本轮wheel的104份重复build文件逐字节匹配源码后，移动到独立有界目录、写专属marker，经卫生工具check/clean实际删除；含marker共105文件、2,187,852字节。最后源码在隔离临时副本重新构建wheel并逐模块与源码比对；其副本/构建元数据清理233文件、4,438,918字节，旧wheel清理2文件、515,724字节。三份独立回执合计340文件、7,142,494字节，位于`.runtime/solar-pv/hygiene-receipts/`。只删除本轮确认可再生的临时材料，不清理旧证据。当前wheel在`wheel-final/`，验证回执`wheel-final-verification.json`。
- 原始执行日志、失败回执和当前协议DOCX保留在忽略运行目录供复核，不提交大型生成物。
- 不push、merge、rebase、reset、发布或部署。独立专业QA及用户试点审核未完成。
