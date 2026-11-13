# V2-EXC-005 — CH08 R2完整原始草稿与原子发布

状态：本地实现候选，待离线回归及独立技术门禁；未经批准不上传。所属版本仍为SOLAR-PV-AI-REPORT-ENGINE-2.0.0；不是Phase E或新业务合同。

## 必要性

上轮两案各144条claims，其中claim数组占原始响应约三分之二；地面原始输出缺最外层闭合。正文中的注册技术ID仍被原裸数门禁拒绝，且独立存在事实血缘、支持状态与风险断言失败。仅补括号或放宽Schema不能解决这些问题。

## 最小差异

- 保留chapter-result/2.0、冻结report-spec及所有原严格validator，不改变金融计算、事实、原始source状态、R13入口、显示或Word版式。
- `host_session prepare-r2`在新request中增加`host_delivery=host-draft-publication/2.0-r2`与`writing_guidance`，共同参与request_hash。旧`prepare`及旧请求继续原合同，不被自动升级。Skill wrapper只透传参数，无依赖安装或源码注入。
- 原始模型输出保存为`<request-id>-draft.json`，仍是原四键envelope，完整内容必须由当前宿主产生。模型不可写发布标记或最终result。
- `publish`在既有host-operation内核锁内重验授权、canonical/模型/来源/upstream及request，再检查原字节和规范化输出预算、完整JSON、envelope与原validate_chapter。没有任何自动claim/fact/source填充或语义修复。
- 发布意图绑定request_hash、raw_draft_sha256、response_hash；复用Workspace已有原子独占写入发布response及publication回执。只改变JSON序列化格式，所有字符串、claims、槽和元数据原样保留。回执包含output_hash、计算五身份、evidence_hash、model_id与每段UTF-8原文SHA。此回执不是模型调用认证；call/session仍由原host-provenance独立记录并通过host-intent约束。
- 核心chapter_writer.accept/resume也检查R2完成回执，不能从另一CLI或装配入口绕开。没有完整合格response不得写result/装配。旧请求没有此新增要求。
- 通用章节CLI检测到host-authorization.json即拒绝prepare/accept/resume（HOST_NATIVE_ENTRY_REQUIRED），避免同一原生run绕开provenance、授权与内核锁链。原生host_session入口继续执行完整检查；普通非原生legacy run不受该入口限制。Python内部函数不是不可信调用者的权限边界，不声称可阻止任意脚本或OS用户修改文件。
- R2核心prepare/accept/resume与publish拒绝已取消run；仅checkpoint内部只读inspection可重验已接受结果，不允许该模式装配Word。原始字节预算读取前后检查，发布序列化预算计入末尾换行。
- `INCOMPLETE_OUTPUT`及普通契约失败保留draft并写失败码，已预留attempt不能修补再用。新生成必须新请求且仍受max_attempts_per_chapter/max_requests限制。未完成marker不会成为accepted结果。
- 发布过程中进程崩溃保留intent，允许同一原draft/response身份重试publish，只补回执，不追加模型调用或预算。任何冲突拒绝覆盖；重复publish仅读回验证。checkpoint区分INCOMPLETE_OUTPUT、OUTPUT_PUBLICATION_INTERRUPTED、OUTPUT_PUBLISHED_NOT_ACCEPTED；已接受仍沿用原恢复/来源校验。cancel继续只保证本地禁止后续操作，不认证远程取消。

## 本轮不做

不先引入六节分片、不改Schema、不增加模型重试预算；先使用紧凑完整六节指引。claims许可池不是配额；每个claim覆盖全部所指段落槽及真实来源，ASSUMED不得SUPPORTED。技术ID留元数据/已有合法term槽，不新增正文ID正则豁免。未来真实宿主仍失败时停在该失败证据，不暗中分片或续写。

不认为文件API是OS沙箱；保留现有Windows路径竞态局限。无受信安装引擎时只允许人工宿主写作观察，publish/accept/resume/Word仍阻断。本地开发解释器验证不代表Skill/Connector可安装或共享解释器。

## 验证及责任

专项文件`tests/solar-pv/test_ai_host_output_r2.py`及后续有界宿主回归验证少量claims、数字/ID、血缘/来源/状态、风险、半写、身份、预算、no-clobber、哈希变更与恢复。协议fixture必须标NOT AI；没有风险声明的错误自然语言仍可能通过结构检查，因此semantic_gate始终NOT_VERIFIED、专业复审不可免除。真实命令、JUnit、超时、后续审阅与最终源码身份由`workbuddy-host/protocol-r2-change-log.md`及其指向的runtime回执记录；本说明不预判测试PASS。

冻结版本及原财务/PDF/平台阻断不变，Phase D为USER_REVIEW_REQUIRED。新版Skill候选须先给用户精确SHA，取得新的明确授权后才可客户端导入/替换和双案新会话试验。
