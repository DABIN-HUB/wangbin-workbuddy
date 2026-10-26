# Phase 5 本地候选验收 — Wangbin 企业软件需求分析与报价专家

日期：2026-10-26；项目 ID `wangbin-software-consultant`，独立版本 `1.0.0`。本产品是**仅依赖 WorkBuddy 模型对话的 Expert**，不调用旧文档助手的 Python、CLI、MCP、Docker、数据库或外部 API。包内无脚本与可执行依赖。只创建新产品目录、独立打包器、独立测试和本报告；Phase 1～4 文件及报告不改。没有 WorkBuddy 私有登录/上传、召唤专家或真实模型对话记录，也没有正式审核/收费设置。

## 1. 官方规范与准入

[专家规范](https://open.workbuddy.cn/docs/expert) 的示例根目录为 `my-expert/.codebuddy-plugin/plugin.json`、`agents/*.md`、`avatars/expert.png`、`README.md`；必填 `name/version/description/author/agents/expertType/agentName/displayName/profession/displayDescription/avatar/categoryId/defaultInitPrompt/plugin/tags/quickPrompts`，Agent Markdown 需 YAML frontmatter。[1] 当前 `agentName` 与 `agents` 文件名一致，`defaultInitPrompt` 两语言均与第一条 `quickPrompts` 完全相同；`tags` 和 `quickPrompts` 各三项，中文市场简介 49 字，分类 `12-IndustryConsultant`；原创头像 PNG 512×512、3786 字节，不复用旧文档专家头像。[1][2] **ZIP 层级只经与官方示例的静态对照及本地重开校验；目标平台实际解析未知。**

入驻指南有个人认证（当前要求中国大陆二代身份证），但页面未明确保证本账号可发布/试传此具体 Expert，私有入口待本人登录核实。[3]

官方收入变现页说明个人用户要填写结算相关资料，经过资料审核及微信签约后才有付费资产资格；当前仅支持一次性买断或按月订阅，且内测期**不支持已发布免费资产转付费**，本阶段不开户、不设置价格。[4]

个人主体服务类目列“办公”“企业管理”等服务，但具体 Expert 类目/资质能否匹配仍需平台实际确认，不能把类目文字当审核结果。[5]

开发者公约规定服务能力与展示一致，付费资产需事先明确收费范围、计费及必要额外费用；禁止伪造案例、强行引流、把同质产品换皮铺量。[2] 本专家与旧文档专家的实际区别是**需求拆解与定价参考**而非文档解析；未配置真实价格、支付或外部联系方式。

## 2. 专家能力、对话流与交付模板

Agent 正文 `packages/experts/wangbin-software-consultant/agents/wangbin-software-consultant.md` 是**全部运行规则**，不要求 WorkBuddy 加载 README 或本报告：

1. 识别 ERP/OA/CRM/MES/WMS/工业物联网/小程序/Web/SaaS/AI 等场景；从目标、流程、角色与规模、接口、工期、预算筛出最大成本驱动。每轮至多三个关联问题；用户只要报价/文档时先交可用初稿。
2. 维护四类对话状态：已确认、合理假设、待确认、变更记录；修改范围则抛弃被撤回前提再计算。
3. 输出需求说明书：`背景｜目标与可测指标｜用户与角色权限｜功能模块及业务流程｜数据对象｜非功能需求｜外部接口/迁移｜部署与运维｜关键风险｜验收｜待确认`，每一项标明证据级别。
4. 功能表模板：`版本｜模块｜输入→处理→输出/异常｜优先级｜复杂度及原因｜前置依赖｜可核验验收标准`；按实际业务拆，不给空泛模块名。方案比较先评估小型单体，必要时才讨论分布式；工业协议需设备端支持/版本/现场网络与许可确认。
5. 根据用户目标，直接在对话中生成 Markdown 需求说明、模块清单、技术实施方案、阶段计划、工作量表、报价参考、需求确认清单；不能把未写出的文档称作“已生成”，不宣称 Word/PDF 可下载。

## 3. 工作量与报价方法

对各版本的模块和共用工作包分别列前端、后端、数据库/迁移、第三方接口、测试、部署/文档、项目沟通及其他明确工作。记录每行低/高人天 `L_i/H_i`，`B_L=ΣL_i`、`B_H=ΣH_i`；风险缓冲单列 `r_L/r_H`，总人天 `E_L=B_L×(1+r_L)`、`E_H=B_H×(1+r_H)`。`1 人月=20 人天` 仅演示可调整换算。固定单价 `p` 时开发费 `[E_L×p,E_H×p]`；分角色单价则分角色计费再求和。一次性第三方 `T`、**未含入人天**的部署外费 `D`、周期性维护 `M` 分开；只有输入已知或明确写演示假设时才能报一次性总预算 `[C_L+T_L+D_L,C_H+T_H+D_H]`，未知第三方费不能按零处理。工期 = 受限并行能力+先后依赖/接口等待/验收等，不是简单的人天除以人数承诺。MVP、标准、完整定制基于实际模块取舍分别估，不靠固定比例放大。

**实际算术核对**：以 agent 文件中的**非市场行情示意** `B_L/B_H=30/45` 人天、缓冲 `10%/20%` 得 `33/54` 人天；演示单价 1000 元/人天，开发费 `33000/54000` 元；用户改为 1200 元/人天后应得到 `39600/64800` 元。第三方费未知时，输出“开发费区间 + 第三方待询价”，不能声称这是含所有费用的合同价。具体角色/模块拆分仍由用户输入决定，以上只校验公式一致性。

## 4. 场景集与本地结果（证据层级不可混用）

独立场景集 `packages/experts/wangbin-software-consultant/tests/scenarios.json` 含 **32 个**有真实提示语与期待行为的场景：S01 ERP、S02 OA、S03 小库存、S04 MES、S05 工业网关、S06 小程序、S07 官网、S08 AI Agent、S09 集成、S10 低预算、S11 不现实工期、S12 只要报价、S13 需求修改、S14 不懂技术、S15 大系统架构、S16 单体/微服务、S17 未知接口费、S18 精确工期、S19 高并发、S20 迁移、S21 二开、S22 工业协议、S23 范围冲突、S24 保证利润、S25 假案例、S26 非法数据、S27 拒留联系方式、S28 只要需求文档、S29 预算差距、S30 多轮方案、S31 单价复算、S32 并行与接口等待。

| 证据层 | 范围 | 当前结果 | 不能推出什么 |
|---|---|---|---|
| 静态结构/算术/场景数据 | 独立 `test_expert_candidate.py`、`phase5_expert_packager.py`，32 条场景仅校验目录结构、字段、示意计算和测试输入存在 | **36 passed**；本地包源/成员与 zip 完整性 PASS | 32 条场景中的模型回答**没有**因测试文件存在就通过。 |
| 非 WorkBuddy 模拟模型对话 | `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wb-phase5-simulation-a.md`（S02/S12/S31）、`...simulation-b.md`（S04/S22/S23）、`...simulation-c.md`（S25/S27/S28） | **9 个场景已完成站外离线模拟；不能替代平台测试**：S02、S04、S22、S23、S25、S27、S28、S31 合格；S12 有条件合格 | 这是依据 Agent 与场景文件生成并评审的实际中文回复，不是 WorkBuddy 特定模型、权限或系统提示词效果；其余 23 个场景未做站外模拟。 |
| WorkBuddy 真正私有上传/对话 | ZIP 解析、召唤专家、多轮方案、预算复算、交付 Markdown | **BLOCKED**：无本人授权会话和确认可用的私有测试入口 | 不得声称“已在 WorkBuddy 使用”“模型对话测试通过”。 |

本地命令实际执行：`.venv/Scripts/python.exe -m tooling.phase5_expert_packager` 输出 `status=PASS,status_scope=local_schema_and_archive_integrity_only`；README 官网付费规范补充后重新构建，最新复跑 `.venv/Scripts/python.exe -m pytest -q packages/experts/wangbin-software-consultant/tests/test_expert_candidate.py` 得 **36 passed in 0.19s**。现有 `validate_expert` 对新增目录返回 `expert.required_fields=PASS`、无 findings；图形头像与旧模板经像素比较不同。原有仓库全量测试未在本阶段执行，不能把新专家测试当作旧引擎回归。

### 4.1 站外模拟的实际结果与限制

以下结果只记录三个独立离线模拟文件中的实际用户可见回复及其评审，不把站外模型结果写成 WorkBuddy 验收：

| 场景 | 站外模拟结论 | 关键观察 |
|---|---|---|
| S02 模糊 OA | 合格 | 先给最小流程草案，再问 3 个高影响问题；示例范围、人数、接口和工期均未冒充已确认。 |
| S12 仅报价 | 有条件合格 | 给出可复核的演示人天、10%/20% 缓冲和单价算式，并明确不是市场行情/合同价；“完整定制”仍只是示例配置，不能覆盖未知企业范围。 |
| S31 需求变更复算 | 合格（条件复算） | 保留用户给定的 30/45 人天与 10%/20% 缓冲，将 1,000 元/人天改为 1,200 元/人天，复算为 39,600–64,800 元；未审计缺失的逐工作包明细。 |
| S04 MES、S22 工业协议、S23 范围冲突 | 各合格 | 每场均不超过 3 个问题；MES 逐项拆解模块和验收；四种协议均要求设备/版本/映射/网络/测试证据；MVP 与全国全量范围冲突被显式拆开。 |
| S25 假案例、S27 拒留联系方式、S28 只要需求文档 | 各合格 | 拒绝虚构客户案例；不索取电话/微信并交付可复制框架；仅交付需求说明书初稿，不附报价或销售引导。 |

S12 的数字是显式演示假设下的开发费，不是市场验证价格；S31 只能复核用户提供的基础合计，不能证明 30/45 人天本身合理。S27 和 S28 因缺少业务事实只能生成标注“待确认”的可用初稿。三个文件都明确写明：没有 WorkBuddy 宿主环境、真实多轮状态或专家执行日志，不能据此推断平台模型表现；其余 23 个场景仍为 `NOT_TESTED` 的站外模拟层。

## 5. 市场介绍与合规边界

名称：**Wangbin 企业软件需求分析与报价专家**。介绍（与 `plugin.json` 一致）：“通过对话澄清企业软件需求，拆解可验收功能、技术方案与人天工作量，以单价假设提供预算区间和风险提示。” 推荐语：`帮我梳理企业软件需求，并估算实施工作量与预算`。无需外部账号或环境安装；报价仅是经用户输入或示意假设的区间，非已验证市场行情/固定合同价；未知费用另询价。所有材料仅对话 Markdown，不能承诺文件下载。只在用户明确询问合作时提及平台允许的咨询渠道，不收集手机号/微信/密码；拒绝违法获取商业数据和伪造案例。[2]

## 6. 发布包、状态与本人后续步骤

本地候选 `dist/wangbin-software-consultant-1.0.0-expert-candidate.zip`；SHA-256 `4813386b13378be4f171fa433d23f9afc749c1323f60af36648f116dd0636deb`；对应 `.sha256` 和 `dist/wangbin-software-consultant-1.0.0-expert-manifest.json`。ZIP 仅四项，以 `wangbin-software-consultant/` 为唯一根。`dist/` 被忽略；**该 ZIP 不是 WorkBuddy 已安装/审核通过资产**。对 ZIP 再构建必须重新核对哈希并更新本报告，不能沿用本值。

| 门禁 | 本地/平台状态 | 范围 |
|---|---|---|
| EXPERT_SCHEMA_PASS | PASS | 官方字段、Agent frontmatter/路径/头像静态核验；平台 ZIP 解析未测。 |
| REQUIREMENT_ANALYSIS_PASS | BLOCKED | 已写对话协议与测试集；9 个场景有站外离线模拟，23 个场景未做站外模拟，实际 WorkBuddy 对话不可用。 |
| ESTIMATION_LOGIC_PASS | PASS | 静态公式 + 独立算术参考回归；不代表模型每次都算对。 |
| PRICING_LOGIC_PASS | PASS | 版本范围、未知费与复算规则及算术参考；不代表正式报价。 |
| SECURITY_PRIVACY_PASS | PASS | **静态资产及 9 个站外模拟**未发现脚本/密钥/外部依赖、强制推广、虚构案例或强索联系方式；真实 WorkBuddy 模型是否遵守待测。 |
| PACKAGE_VALIDATION_PASS | PASS | 本地 ZIP 四成员、来源字节及哈希校验。 |
| WORKBUDDY_INSTALL_PASS | BLOCKED | 无私有试传/平台解析/召唤证据。 |
| WORKBUDDY_DIALOGUE_PASS | BLOCKED | 无平台实际对话、多轮算价、文档交付证据。 |
| PUBLISH_READY | BLOCKED | 平台资格、付费权限、私有测试和真实对话仍待本人验证；未授权正式发布。 |

本阶段开始时 `main` 的 HEAD 为 `931c098`；工作区已有七份 **Phase 4 未跟踪报告**，保持原样。本轮独立专家源、场景/测试、打包器与本报告新增且未提交；`dist/` 候选因 `.gitignore` 忽略，不可只靠它复原产品。需要本人核验主体/权限与非公开测试入口，导入仅该专家 ZIP 并在私有对话逐条运行 32 个场景，特别核对算价/多轮变更/对外引流；若只能走公开提审，停止并请求另行授权。不得在聊天提供身份证、密码、Token；出现凭据只写 `[REDACTED]`。

## Sources

[1] https://open.workbuddy.cn/docs/expert
[2] https://open.workbuddy.cn/docs/developer-agreement
[3] https://open.workbuddy.cn/docs/onboarding
[4] https://open.workbuddy.cn/docs/monetization
[5] https://open.workbuddy.cn/docs/service-categories-individual
