# CH08 WorkBuddy原生宿主协议R2本地整改记录

状态：**LOCAL_PROTOCOL_CANDIDATE / PARTIAL / MODEL_INTEGRATION_BLOCKED**。版本仍为SOLAR-PV-AI-REPORT-ENGINE-2.0.0；Phase D为USER_REVIEW_REQUIRED，不进入E/F/G。本轮未运行新的WorkBuddy会话、未上传/覆盖Skill、未安装依赖、未创建Expert、未push或发布。

## 结论先行

**本轮没有取得两案由WorkBuddy新生成且通过原严格契约的CH08。** 上轮观察到真实新内容，但屋顶仍因裸技术ID、claim段落血缘及风险声明失败；地面还存在不完整envelope与SUPPORTED/ASSUMED冲突。R2当前只完成本地协议候选、定向测试和同模型隔离补充审阅，不能将协议fixture的通过、Word存在或文字指引变更替代宿主生成证据。

正式wb-quality不可调用的状态保持`INDEPENDENT_QA_NOT_EXECUTED`；两次隔离代理均明确`SUPPLEMENTAL_SAME_MODEL_REVIEW`，不充当独立QA或专业签审。用户新批准之前不得开始R2客户端试验。

## 身份、冻结及原件

- 原基线：`9faf44b86f4bb99a8a1021e1b35c70a4a49571e9`；R2-0诊断/计划提交：`c4eda89e8a44d4a8b84b1003403ad6a62d65e566`。后续阶段及最终HEAD由下述`final-state.json`读回记录，本文件不自引用自己的提交SHA。
- 本轮目录：`.runtime/solar-pv/ai-v2-host-protocol-r2-20261113-101239/`（下称RUN）。全部详细回执、错误原件和临时协议案例在此；不改旧运行。
- 原99成员审阅ZIP SHA：`09b81e392bb07da74f4c83191925c33f7a5d78d1ab41f3e7604f19f5e05f6aaf`。98项载荷的成员集合、逐项哈希及CRC已核验。
- 原失败map：`diagnosis/original-failure-map.json`，SHA `938973ae3970d60183157cd170f48fd6144fabae9178d2f000022935fc3f5747`。脚本及负向复现不补括号、不执行accept、不生成新专业正文。
- 最新真实spec-check：`receipts/r22-spec-final.*`，退出0，规格SHA `59e379906f6b83d91a76179f14fdc00e5c0dc9346ef5d272bbcf04da90df7532`；18章100小节、13附录26小节、469字段、89公式、281映射、189术语不变。
- 上轮364文件保护清单：361项原字节不变；3项为本轮明确授权的`reporting/__main__.py`、`chapter_writer.py`、`host_session.py`源码修改，不能写成“364全部不变”。详见`r2-protection-comparison.json`。未改canonical、金融计算、冻结定义、旧R13输出或历史宿主响应。

## 原始失败精确分类

| 项目 | 屋顶 | 地面 |
|---|---:|---:|
| 原claims | 144 | 144 |
| 原正文段落 | 30 | 24 |
| 数字命中字段/token | 26 | 14 |
| 段落绑定违规独立claims | 85 | 99 |
| claim–paragraph违规发生数 | 91 | 106 |
| SUPPORTED与ASSUMED冲突claims | 0 | 42 |
| 已声明fact的source遗漏claims | 0 | 0 |
| 额外SEMANTIC_RISK_BLOCKED claims | 4 | 3 |

数字命中在这两个样本中均为章节、表格或方法状态标识；不等于允许这些ID裸放正文。91/106不是独立claim数，历史148条观察不能机械相加。预算cost不能作PAID_FEE，假设零不能作已计算ZERO_VALUE。源遗漏为零也不能抵消fact_refs没有覆盖其所指段落的问题。逐字段原文、分类和诊断限制见`root-cause-and-compatibility.md`及完整map。

## 最小变更

1. 保留chapter-result/2.0及全部原数值/claims/source/semantic_risk校验，未引入六节分片器。新prepare-r2增加参与request_hash的交付协议与紧凑写作规则；旧prepare兼容。
2. 指引明确许可ID池不是24条配额；仅生成真实必要claims并覆盖所有所指段落事实及来源；ASSUMED不得SUPPORTED；正文内部ID改为自然读者语言/合法槽，而非扩大数字白名单。
3. 新`reporting/host_output.py`只读本请求的模型原始draft，验证完整envelope、预算、身份和原章节契约后原子独占发布response/完成回执。固定raw draft SHA、output摘要、计算五身份、evidence_hash及每段原文SHA；不写专业正文、不补造claim、不修旧JSON。
4. 半写输出为INCOMPLETE_OUTPUT并保留原件、关闭尝试；新生成只能占用剩余预算的新request。发布进程崩溃只允许同一原字节恢复，不能改稿。实际os._exit进程中断和Windows内核锁释放有专项覆盖。
5. 初次回归发现core取消旁路（两案失败原件保留），已加R2 prepare/accept/resume/publish取消检查；checkpoint仅以内部只读inspection重验旧结果，不能借此装配。
6. 隔离补充审阅发现SQR-P1-01：通用章节CLI可跳过native provenance写result。采用最小入口隔离，遇host-authorization.json即拒绝prepare/accept/resume为HOST_NATIVE_ENTRY_REQUIRED；真正legacy run保留。双案实际子进程负向测试和代理探针验证。该边界不是任意Python代码或OS用户的沙箱。
7. raw字节预算读取前后重验；发布序列化预算包含实际末尾换行。完整技术差异在`V2-EXC-005-host-output-publication.md`，未静默修改冻结规格。

## 真实测试及失败账本

所有命令使用显式开发解释器/开发源码；**不是已安装WorkBuddy运行时**。每次执行保留argv、超时上限、退出码、stdout/stderr与JUnit（若完整生成）。`run_bounded.py`为可恢复命令工具，拒绝覆盖旧回执，并绑定执行前后源文件SHA。未运行全仓数千项或600秒终期链。

| 最新相关专项回执（RUN/receipts） | 结果 | 范围 |
|---|---|---|
| r22-unit-final | 96通过 | 两案紧凑claims、ID/数字、血缘/状态/风险、半写、身份、预算、原子发布、恢复 |
| r22-session-roof / ground | 各9通过 | R2核心取消四入口、缺marker、预算、真实进程退出恢复、native协议链 |
| r22-native-final-roof / ground | 各1通过，替代上行对应正向用例 | 最终新增CLI入口guard后两案prepare-r2→publish→accept→局部Word→cancel/checkpoint；含3个真实通用CLI子进程拒绝 |
| r22-display-lock-configured | 37通过 | 既有wrapper/内核锁、数字显示、选定OMML及章节位置 |
| r22-original-negative | 42通过，29未选 | 原来源授权、裸数、注入/外链、非法引用、缺表、UNKNOWN≠0、canonical篡改 |
| r22-legacy-roof / ground | 各3通过，其他未选 | 旧prepare/幂等接受、来源恢复不能改标、过期/取消 |
| r22-word-roof / ground | 各3通过，另一项目未选 | 旧固定报告样式/表格与读者预览保护；不宣称PDF视觉通过 |

以上按实际JUnit用例ID去重为**205项通过、零失败/错误/跳过**，不是把多轮重复执行累加，也不是全模块或全仓通过。最终来源匹配及提交后再验证记录在`verification-summary.json`、`final-state.json`；不同源码版本的旧结果不替代最终对应路径验证。

必须同时保留的非通过记录：

- `r20-host-baseline`：180秒TIMEOUT，无完整JUnit，不推定通过数。
- `r21-core-gates`：8通过、2失败，后续修复取消guard并复测；不是未披露的全绿基线。
- `r22-display-lock-compat`：34通过、3失败，原因REPORT_OMML_CONVERTER_UNAVAILABLE。定位已存在Pandoc后显式传路径复跑37通过；没有安装或删除公式。
- `r22-original-core`：150秒TIMEOUT，未生成完整JUnit；随后按实际收集的71项选择相关42项有界负向验证，剩余29项未计通过。原模块整体仍未完成，不以42项替代其结果。
- 代理初次复现初始化错误、第二次60秒超时、第三次聚焦成功均在qa中保留；后续探针未覆盖正向运行，不从静态审查推导测试PASS。
- pytest产生既有anyio/pytest弃用警告；未加依赖、未改相关配置。

## 技术复核与候选

`qa/SUPPLEMENTAL_SAME_MODEL_REVIEW.md`保留原P1，`qa-followup/SUPPLEMENTAL_FOLLOWUP_REVIEW.md`记录最小修复负向实测通过：一个60秒上限命令实际约4.81秒退出0，三CLI动作均2/HOST_NATIVE_ENTRY_REQUIRED；旧qa 65文件逐路径哈希不变。母任务另读回5个受审源码哈希与当前文件一致。正式INDEPENDENT_QA仍NOT_EXECUTED；语义始终NOT_VERIFIED，专业签审未完成。

唯一新Skill候选：

`dist/wangbin-solar-pv-prestudy-0.1.3-host-protocol-r2-20261113-101239.zip`

SHA-256：`7054c670e66ad3caeab73a1ad8e9b35fd3c85f340b345aa9976e501b3250bbc9`

21成员，214276字节；原有产品validator/secret扫描通过，LICENSE、manifest、CRC、精确成员集合和当前源码逐项字节读回通过；旁有`.zip.sha256`及`.zip.manifest.json`。独名创建，不覆盖旧候选、不修改catalog。**仅本地包完整性合格且REVIEW_REQUIRED，不代表独立QA、可安装或获准上传。** ZIP不含引擎，不能让旧已装引擎凭空获得prepare-r2/publish；内部wheel可信分发、Pillow依赖、Skill与Connector同解释器依旧未闭合。现有离线安装失败保留，不用开发PYTHONPATH冒充安装成功。

## 分项门禁（仅本轮R2）

| 门禁 | 状态 |
|---|---|
| WORKBUDDY_SKILL_IMPORTED | NOT_EXECUTED，等待新候选授权；旧候选导入属历史证据 |
| WORKBUDDY_MODEL_NEW_CONTENT_OBSERVED | NOT_EXECUTED；上轮观察不可继承为R2成功 |
| CH08_ROOF_CONTRACT_ACCEPTED | BLOCKED：无R2真实宿主输出；上轮仍失败 |
| CH08_GROUND_CONTRACT_ACCEPTED | BLOCKED：无R2真实宿主输出；上轮仍失败 |
| WORKBUDDY_HOST_TOOL_EXECUTED | NOT_EXECUTED |
| LOCAL_CH08_ACCEPT_RESUME_DOCX | 开发源码+NOT AI协议样本通过；真实宿主内容/安装链BLOCKED |
| CONNECTOR_DEPENDENCY_DISTRIBUTION | BLOCKED |
| WORKBUDDY_HOST_E2E_VERIFIED | BLOCKED |
| SERVER_MODEL_ATTESTATION | NOT_VERIFIED |
| INDEPENDENT_QA | INDEPENDENT_QA_NOT_EXECUTED |
| PROFESSIONAL_REVIEW | NOT_EXECUTED / REQUIRED |
| PHASE_D_CONTENT_REVIEW | USER_REVIEW_REQUIRED |

终期现金、有效多候选排名、基准独立交易费支付、会计/经营/股东方法、PDF公式复制检索、正式四文件与发布继续独立阻断。

## 恢复、卫生与下一停止点

最终交付索引为RUN下`final-state.json`、`verification-summary.json`、`source-diff.patch`及Git增量bundle；审阅ZIP和MANIFEST逐项核验另在`archive-readback.json`。增量bundle需要原基线9faf44b，**不是独立全仓备份**。受保护大包及旧运行以路径/大小/SHA索引保留，审阅包不等于安装包或云备份。

本轮无已证实废弃的历史资产删除：净删除0文件、释放0字节。旧已安装候选、正式旧Skill/Connector及历史失败证据继续保留；测试输出放已忽略RUN，作为此次真实验收/失败及恢复材料保留。卫生工具--check为只读且不能把历史日志标记自动解释为可删除；未执行全仓清理。dist和runtime均忽略，不提交ZIP/JUnit/原始大JSON；只提交明确生产、测试和必要文档。最终文件数/字节、Git状态、dist和保护验证以final-state读回为准。

后续须解决正式独立QA与可信隔离安装条件，并由用户对上述精确候选明确批准新的客户端试验；若提示覆盖同ID，仍须暂停确认。新会话只能读本次新request及授权事实，不能读旧authored/draft/Word。双案严格接受前不得解锁其他章节或Phase E。当前停止于本地候选审阅，不再用改写旧正文追求PASS。
