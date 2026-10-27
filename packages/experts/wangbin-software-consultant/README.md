# 软件需求与报价专家 · 1.0.0

独立 WorkBuddy Expert 候选；无需 Python、MCP、CLI、Docker、数据库或外部 API。仅通过 WorkBuddy 模型对话处理用户提供的文字。不同于仓库中的文档助手，不解析 PDF/Word/Excel，也不生成 Word/PDF 下载文件。平台解析/召唤/模型表现尚未经真实 WorkBuddy 验证。

## 用户能得到什么

- 用最多三项优先问题逐轮澄清目标、角色、人数、流程、接口、迁移、部署、预算与周期；即使用户暂不回答，也先提供有用的初稿。
- 输出已确认需求、假设和待确认事项；将功能拆到输入/处理/输出/异常、优先级、依赖、验收标准。
- 结合规模比较单体与复杂系统架构，工业协议先确认现场设备能力和网络/许可边界。
- 针对 MVP、标准、完整定制分别给出按前端/后端/数据库/接口/测试/部署/沟通拆分的人天区间、缓冲与可审计的单价假设；第三方/维护单列，信息不足不伪造市场价。
- 按需在对话里输出需求说明书、模块清单、技术方案、阶段计划、工作量评估、预算参考、确认清单的 Markdown 文本；不是已生成可下载附件。

## 平台结构与授权边界

本 Expert 目录中的发布资产按目录内 `LICENSE` 采用 MIT 授权；该授权仅覆盖本候选包内的 Expert 资产，不扩展或重新声明仓库其他目录、历史文档引擎或任何未随包分发的专有代码。`plugin.json` 的 `license=MIT` 与该范围一致；正式发布前仍应由权利人确认授权范围。

`plugin.json` 的 `expertType=agent`、`agentName`、`agents` 相互对应；`displayName`/`profession` 双语；`defaultInitPrompt` 与第一条 `quickPrompts` 两种语言完全一致；分类 `12-IndustryConsultant`。Agent Markdown 带有名称、描述、双语显示名/职业的 frontmatter，不声明 `skills`、`dependencies`、`tools` 或外部运行时。图形头像为原创 512×512 PNG，与旧文档专家不是同一图形。目录根层级为 `wangbin-software-consultant/{.codebuddy-plugin,agents,avatars,README.md,LICENSE}`；官方专家示例采用这一结构，**是否在目标账号私有上传界面接受 ZIP 尚未实测**。[1]

公开入驻说明存在个人主体认证，但没有保证本账号已获得此 Expert 的提交权限；须本人登录核实。[3]

官方“收入变现”说明个人用户须另填结算信息、审核并微信签约后才能发布付费技能/专家，目前只支持一次性买断或按月订阅；内测期暂不支持已发布免费资产转付费。**本候选未设置价格，不执行收费入驻，也不得假设以后可一键转付费。**[4]

个人主体服务类目文档列“办公”“企业管理”等业务，但不能直接推断该 Expert 的选类和资质已审核通过。[5]

开发者公约要求真实能力、描述与运行条件一致，不得重复铺量/虚假宣传；如以后设为付费，必须事先说明收费范围、计费、必要额外费用，当前包不配置价格或付款链接。合作只在被问到人工实施或咨询结束且用户需要时，简短说明平台允许的渠道；不诱导站外支付、强索联系方式、植入广告或伪造案例。[2]

## 研发与验收

包内有四项运行资产和一份授权声明：`.codebuddy-plugin/plugin.json`、`agents/wangbin-software-consultant.md`、`avatars/expert.png`、`README.md`、`LICENSE`。独立质量场景与结构测试保存在 `tests/`（不打入 ZIP）；`tooling/phase5_expert_packager.py` 只读取本专家路径，并在 `dist/` 生成独立候选和侧车哈希。全局 `dist/` 仍忽略，Phase 1～4 历史文件不被更新。测试分静态结构/算术基线、模拟模型对话及真实 WorkBuddy 对话：后者必须在授权的私有环境人工执行，否则保持 BLOCKED。详见 `reports/phase5-software-consultant.md`。

## 使用边界

所有报价为用户输入或明确标注的演示假设，不是经市场验证的价格、正式合同、利润保证或固定工期；实际开发还需现场访谈、技术评审、接口授权和书面确认。用户无需留手机号/微信即可使用。只提交为分析必要的脱敏文字；不主动访问用户其他文件、系统或第三方服务。

## Sources

[1] https://open.workbuddy.cn/docs/expert
[2] https://open.workbuddy.cn/docs/developer-agreement
[3] https://open.workbuddy.cn/docs/onboarding
[4] https://open.workbuddy.cn/docs/monetization
[5] https://open.workbuddy.cn/docs/service-categories-individual
