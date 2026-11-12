# WorkBuddy 原生宿主长任务：最终门禁结论

**判定：LOCAL_CANDIDATE_VERIFIED / REAL_HOST_BLOCKED。不能宣称普通用户安装专家后已经可以无旧稿生成新项目专业章节。**

本轮完成H0/H1审计和裁定、H2最小本地候选、H3离线双案阻断验证以及H4证据整理。H3真实宿主试点未执行，正式wb-quality QA未执行；整体业务目标未达到，不将这些阶段标成全部PASS。Phase D保持USER_REVIEW_REQUIRED，不进入Phase E。

## 核心回答

- 官方资料支持Skill脚本与宿主工具编排这一候选方向；这不是本产品安装、召唤或实际运行已验证。H0官方正文、访问时间及哈希在h0/official-sources.json；兼容性矩阵与决策文档保留H0/H1审计时点，H2变化见architecture-diff.md。
- 新代码不调用额外Python LLM API。预期作者是实际WorkBuddy宿主会话；**本轮没有执行该模型步骤**。Hermes只开发协议与指引，没有预写这两份CH08专业正文。
- 同一CH08冻结任务对两份不同的原合成canonical均实际prepare成功并停在AWAITING_AUTHORIZED_HOST；checkpoint重验成功，无结果resume实际exit 2。没有response/result/新Word，不交付冒充的双案新AI样稿。
- 本机客户端安装不等于光伏Expert/Skill/Connector已安装授权。当前没有光伏专属Expert包的真实召唤证据；Skill是否继承Connector托管解释器仍未知。
- 两个固定内部包公开PyPI获取失败，未提供受信私有源。本地候选wheel构建成功并验证CRC/RECORD；新隔离环境离线安装实际因Pillow缓存缺失失败。随后真实Skill包装器返回INSTALLED_ENGINE_UNAVAILABLE_OR_INVALID_RESPONSE。安装和分发未闭合。

## 分项门禁

| 门禁 | 本轮判定 | 证据/限制 |
|---|---|---|
| WORKBUDDY_PLATFORM_DOCS_COMPATIBILITY | DOCUMENTED_SUPPORTED / 部分UNKNOWN | 原生方向有文档依据；无凭据生命周期、Skill解释器衔接仍需平台实测 |
| EXPERT_PACKAGE_CONTRACT | BLOCKED / NOT_RUN | 未新增光伏Expert候选，原prompt-only规则不变；专属召唤体验未验收 |
| CONNECTOR_DEPENDENCY_DISTRIBUTION | BLOCKED | 公共精确版本404；本地构建不等于可获取；离线依赖解析失败 |
| LOCAL_HOST_FILE_PROTOCOL | PASS（限定本地Windows专项） | 最终258项专项去重通过，含58宿主会话、9锁/包装器、71原协议、18依赖、102规格 |
| HOST_MODEL_NEW_CONTENT_TWO_SAMPLE | BLOCKED | 双案仅新request，无宿主response，不存在可评新正文 |
| WORKBUDDY_HOST_TOOL_E2E | MODEL_INTEGRATION_BLOCKED | 未安装候选、未验证真实Read/Write/Bash、未运行模型 |
| SEMANTIC_HIGH_RISK / mechanical | PASS（已声明风险的限定测试） | 结构化残值→实绩回款反例阻断；其它预测/实绩和指标边界负测通过 |
| SEMANTIC_HIGH_RISK / professional | PROFESSIONAL_REVIEW_REQUIRED | risk_assertions可选，不能覆盖未声明的自然语言误述；semantic_gate仍NOT_VERIFIED |
| INDEPENDENT_TECHNICAL_REVIEW | COMPLETE，修复由主执行者复验 | 独立只读子代理发现三项问题；原报告保留，未冒充wb-quality |
| WB_QUALITY / PROFESSIONAL_APPROVAL | INDEPENDENT_QA_NOT_RUN / BLOCKED | 没有正式wb-quality运行回执，没有独立工程/财务签审 |
| PHASE_D_CONTENT_REVIEW | USER_REVIEW_REQUIRED | 不自行放行 |
| PHASE_C_FINANCIAL / SCENARIO_COMPARISON | BLOCKED（原状态保留） | 终期现金、有效多候选排名及未裁定方法未改 |
| PDF_FORMULA_COPY_SEARCH / FORMAL_FOUR_FILE_DELIVERY | BLOCKED | 无新正式四文件或PDF公式验收 |
| FULL_REPOSITORY_REGRESSION | NOT_RUN；发布门禁仍BLOCKED | 本轮仅专项，不运行4609项或终期长重放 |
| PLATFORM_RELEASE | BLOCKED / NOT_RUN | 无push、安装商店资产、上传、审核、发布或付费服务 |

## 四项能力必须分开

1. 正文数值槽及协议装配：本地协议专项通过，内容属于明确的NOT-AI测试fixture。
2. 一次性AI样稿质量：本轮没有新增专业样稿；历史Hermes样稿继续待用户/专业审核。
3. 运行时自主生成：没有真实宿主新内容证明，BLOCKED。
4. 正式WorkBuddy宿主集成：MODEL_INTEGRATION_BLOCKED。

不能由第1项推导后面任何一项通过。

## 双案与恢复证据

`runtime-e2e-evidence/two-project-blocked.json`记录两案五身份、原canonical字节SHA、新request摘要、相同研究规格摘要和实际命令回执。完整本地输入和新request在runtime-e2e-evidence/local-protocol；没有读取authored、历史Word或旧draft作为这些请求输入。该记录证明本地输入范围，不是假定的WorkBuddy读取审计。

原canonical SHA：
- industrial_rooftop：b763dec6bd6d37cea78525c777ccfd8a4133a7a18b6c646385f329019671dca3
- utility_scale_ground：c83ae242bc864a6566c83a1b6b3851d33587ca4b9b2d3d51447315ebac73080b

冻结Registry SHA保持59e379906f6b83d91a76179f14fdc00e5c0dc9346ef5d272bbcf04da90df7532。两案CH08任务摘要一致，证据摘要不同，未篡改canonical。

已验证：本地有限请求/尝试、字节预算、接受期限、来源与身份变化拒绝、幂等接受、结果及来源发布中断恢复、本地取消。四类锁由真实子进程持有后硬超时终止，再获取成功；保留活跃锁互斥及未知legacy锁阻断。相对workspace在改变cwd前固定。以上不是WorkBuddy重启恢复实测。

未暴露或未验证：远程模型执行超时、token/积分/费用、宿主上下文上限、跨宿主会话恢复、OS强隔离、Linux/macOS运行。完整请求超限即阻断，不自动删事实或切片凑合。取消不声明终止远端模型。

## 失败与范围限制

初次测试解释器缺pytest；三个180秒组合运行超时；构建解释器无pip；新的隔离venv离线安装失败。均保留原始失败回执。测试随后按完整选定文件拆分，最终258项无failure/error/skipped；没有把超时或deselected累计成PASS。anyio插件的弃用警告保留，不改测试断言或依赖来消音。

两个候选wheel为本地未发布构件，版本仍沿用原固定版本，须以本轮字节SHA区分，不能认为与任何现存同版本分发物等价。Windows实测不能推出Linux/macOS通过。旧dist两个候选原样保留并验证，属于历史候选，**不是包含H2改动的新安装包**。

## 仓库卫生与恢复包

- 未净删除任何已跟踪历史资产；原canonical、冻结规格、公式/Word生产者及旧dist保护检查通过。
- 清理仅限本轮创建的构建副本和失败的隔离venv：卫生工具实际删除293文件、5,215,122字节（含95字节清理标记）；292个原生成文件为5,215,027字节。未清理历史运行/旧工作树/其他产品。
- 最终Git文件数、blob与工作树字节数、源码摘要、最终HEAD及干净状态在final-state.json，避免文档自引用未来提交SHA。
- 恢复包包含本轮文档、精确增量源码、候选wheel、JUnit/命令回执、双案canonical/request、原始技术审查和Git增量bundle。bundle前置基线为d6b4043e19d391ce6055747ef058e46af1ffd3c0，不是整个仓库备份；大型历史资产仍外置保护，位置和SHA另列。
- 恢复包不得直接当WorkBuddy安装/上传ZIP。使用说明见包内README.md。

## 最小下一步批准

无需重新规划2.0。继续真实验证只缺以下具体前提：

1. 权利人提供两个内部wheel的合法受信分发来源，或批准使用本轮精确SHA的离线候选，并补齐声明的依赖包；先完成独立安装与依赖核验。不要提供密钥到聊天中。
2. 指定并明确授权一个WorkBuddy私有测试入口及候选安装动作（本轮禁止平台上传/安装，未擅自执行）；确认光伏专家入口或批准其薄角色包装、模型处理合成资料权限及实际Read/Write/Bash工具。
3. 在该入口仅执行两案CH08：现场新研究→Write→accept/resume→真实可见日志→独立内容复审。成功前CH10/CH16继续锁定，Phase D用户审核前不进入Phase E。
