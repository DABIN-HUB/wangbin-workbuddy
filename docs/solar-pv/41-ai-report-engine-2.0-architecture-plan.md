# AI Report Engine 2.0 架构与执行计划

> 在同一会话使用 executing-plans 逐项执行，不启动其他会话并行修改。用户已指定完整设计方向并授权A/B，D保留独立用户审核门禁。

**Goal:** 建立可运行、证据约束、可恢复的逐章研究基础框架，不迁移旧正文。

**Architecture:** 既有Catalog/ReportModel验证canonical；注册表加载冻结规格；证据包只给授权事实；宿主模型通过文件协议接收章节任务并返回结构化结果；程序验证后组装局部Word。正式四文件依然走旧入口，Phase F才接入新正文。

**Tech Stack:** Python现有标准库、jsonschema、python-docx；复用本包Catalog、serialization、Workspace、report_word_styles/report_numbering/report_export工具，不新增依赖。

**Spec:** `40-ai-report-engine-2.0-requirements-frozen.md` 与已锁定 `reporting/specs/report-spec.json`。

## 1. 方案取舍与模块

不采用整本一次调用（上下文与失败范围过大），不采用100次机械独立调用（依赖和风格割裂）；采用按章任务、局部上下文、结构化验证和有界交接。不新增并行计算器、不重写PDF、不接未经授权的厂商账号。

| 新模块 | 入口及职责 | 复用 |
|---|---|---|
| chapter_registry | `Registry()`；校验包内规格SHA和稳定ID；`chapter(id)` | Catalog/CHAPTERS/APPENDICES |
| evidence_pack_builder | `build_pack(model, registry, chapter_id, allowed_source_ids)` | 原子来源读取、canonical值及状态；绝不调用build_claim正文 |
| report_planner | `plan(registry)`返回依赖顺序与阶段限制 | 冻结依赖图 |
| chapter_result_schema | `result_schema()`返回严格JSON Schema | jsonschema；限制长度、数组、未知键 |
| claim_validator | `validate_chapter(output, pack, chapter)`与`render_text` | 原数字显示；槽引用必须属于本节 |
| llm_provider | `ModelConfig`、`integration_status()` | 无默认网络、无Stub；宿主文件交接 |
| chapter_writer | `prepare`、`accept`、`resume` | Workspace独占写入；请求、尝试和验证回执 |
| report_assembler | `assemble_chapter`生成局部待审Word | 现有样式/标题书签/表格/OMML |
| __main__ | spec-check / plan / prepare / accept / status CLI | 不修改report/ground-report |

盈利与optimization不建空类，Phase C真实实现后才加入口。全报告consistency在Phase E完成；B提供身份、section范围和依赖输出绑定，不把局部验证冒充全报告语义通过。

## 2. 证据和章节协议

证据包键：`schema_version/identity/report_spec_version/prompt_version/spec_hash/chapter_id/pv_type/maturity/sections/facts/formulas/tables/figures/constraints/evidence_hash`。每节包含允许的fact/metric/formula/table/source/claim引用、缺失事项和不适用说明。事实键由程序生成：指标为`metric:<id>`，原子输入为`input:<instance>`；包含label/value/unit/status/period/boundary/source_ids。数字及数组元素由程序展开而非模型算数。仅从显式来源白名单中选择；缺授权的值不发送。原件路径不作为文件读取指令。

模型输出Schema含全部冻结字段及fact_refs/source_refs。正文中的数值只能用 `[[fact:<fact_id>]]`，例如事实ID为`metric:dc_capacity`时占位串是 `[[fact:metric:dc_capacity]]`。裸阿拉伯数字拒绝；所有正文字段（包括引言、决策影响、缺证、总结）都检查，不只检查paragraphs。技术名含数字也应引用对应输入或改用中文技术名称；中文数词/否定关系/因果解释另需语义审阅。表/图由程序按受控定义创建，模型不能自行提交表格数据。无正式图数据则figure_refs为空。

事实校验通过的内容状态为 `STRUCTURE_AND_REFERENCES_VALID`，专业状态仍 `PENDING_REVIEW`。只允许局部待审文档，不允许标记最终 `FACT_VALIDATION_PASSED`。不能用“未发现”代替全语义证明。

## 3. 模型编排、预算、恢复

使用真实可执行的prepare/accept协议，不声称已有自动provider。prepare绑定用户显式model_id、思考等级、超时、最大请求/结果字节、每章尝试和总任务预算；生成有限有效期的请求。宿主执行端须承担模型调用超时、凭据和成本计量；没有宿主不能把配置值冒充已限制远程调用。engine不主动联网，因此没有无限网络重试。

accept验证当前canonical重新建包、规格hash、配置hash、请求hash、章节、输入/来源/结果身份、请求有效期、响应model_id和调用ID；对失败保存稳定错误码且不能覆盖成功结果。每次尝试独立文件；达到上限停止。请求/输出hash分别记录，model调用ID仅属宿主声明，在没有独立平台回执时 `LLM_INTEGRATION_VERIFIED`仍未通过。

恢复复核请求和已存output，再次校验数值及引用；不能只信validation_status。输入/规格/模型参数/授权选择不同不恢复。缺失上游时prepare在请求中明确列明，禁止伪造上游已完成；B局部研究可进入待审，不允许摘要或综合结论绕过依赖称完成。

输出使用授权Workspace，拒绝越界、符号链接/重解析点及已存在目标。诊断仅稳定错误码，不将模型原始错误或凭据写日志。当前本地授权工作区不宣称OS沙箱；恶意用户修改本地文件与模型幻觉是不同威胁。

## 4. Word复用和Phase C—G边界

B局部Word使用原Word配置、章节编号书签和表工具；每章标题→动态引言→稳定小节→分析→受控表/公式→发现与决策含义。公式使用原转换器的89式注册映射，缺pandoc则阻断公式装配，不输出图片或伪公式。局部文档非完整四文件，不重设计封面；完整封面/目录/附录接入留F。

C从canonical真实生产者组织六类盈利口径，审查scenario_runner未闭合的终期分支；不支持候选只保留待分析方向。D双类型重点章节真实调用及R13对比，交付用户审核；未确认停止。E按依赖生成全量，F完整四件同源和格式，G证明旧正文无引用后清理。每阶段有自己的本地commit及未关闭门禁。

## 5. 执行清单与验收

- [x] Phase A独立commit，规格全部合法引用与覆盖102测试通过。
- [x] 新增registry、evidence、planner：加载hash拒漂移；两个现有PARTIAL canonical均可建包；外型/未知来源/源冲突不得成为有效事实。嵌套来源typed adapter保留明确未闭合状态。
- [x] 新增严格Schema与validator：正常、缺失、错ID、错节、裸数字、XML/注入意图、未授权来源等负例；程序不能宣称自然语言安全完整。
- [x] 新增宿主交接及CLI：无adapter状态明确阻断；prepare独占目录，accept过期/错run/错模型/预算拒绝；resume拒绝旧证据与篡改输出。宿主自动调用和真实模型验证未完成。
- [x] 新增局部Word：双类型公开CLI真实装配协议fixture，读回标题引言位置、六小节、四表及十二个OMML；不作AI内容/PDF/视觉PASS。
- [x] 显式运行 `test_ai_report_spec.py`、`test_ai_report_engine.py`；第一次合并运行180秒TIMEOUT，随后按规格/类型拆分，全部选择均完成，保留原失败与超时。另运行原财务/数值/完整Word样式和公式专项，不运行全仓。命令及JUnit见交付回执。
- [x] 审diff、敏感信息、旧资产和dist，包数据收录检查均已执行；本地提交及SHA/status的最终读回单独保存在运行目录`final-state.json`，不以本项勾选替代Git回执。

新规格test_id是逐项验收标识；参数化规格测试只覆盖定义，后续正文实质审核须逐个更新独立运行回执，不原地涂改冻结规格状态。若真实模型接入阻断，本轮交付必须同时给出阻断与框架本地执行结果，不以测试fixture冒充AI样本。

实现后的可恢复说明、CLI参数与阶段状态见 `ai-report-engine-v2/phase-ab-delivery.md`；A类补充见 `ai-report-engine-v2/V2-EXC-001-host-model-exchange.md`。本计划的执行勾选不替代 `FRAMEWORK_IMPLEMENTED` / `LLM_INTEGRATION_VERIFIED` / 用户试点质量门禁。
