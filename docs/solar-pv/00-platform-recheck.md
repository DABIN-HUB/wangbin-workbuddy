# Phase0 WorkBuddy官方能力重新核实

核实时间2026-10-28（中国标准时间），以官方公开文档及实际HTML正文读取为证；不是账号权限或平台安装证据。旧 `docs/workbuddy-platform-spec.md` 不改写，其历史结论不能替代本次核实。

本轮 `web_extract` 因检索后端不支持提取而失败；采用urllib HTTPS直连（四页均HTTP200），剔除script/style/nav后读取正文，原始HTML仅留scratch，不将官网全文复制入商用包。访问记录和响应SHA-256见 `00-official-access.json`。以下只作有限摘要。

| source_id | 来源 | 本次正文确认 | 仓库差异/运行时门禁 |
|---|---|---|---|
| WB-SKILL | 官方Skill | SKILL.md及references/scripts/templates；AI通过Bash执行scripts | 未确认普通Skill自动安装Python/文档渲染依赖；不能把Connector runtime借给普通Skill；附件/文件导出路径待实机 |
| WB-EXPERT | 官方Expert | plugin.json可选skills目录；Agent frontmatter可选skills预加载；工具系统分配；文档包含MCP/既有Connector依赖声明 | `tooling/expert_rules.py:61`刻意禁止skills、dependencies及自行tools，属现有prompt-only产品规则，不是“官方不支持”。不改旧规则；Phase7才设计新的隔离集成profile+回归+真机 |
| WB-CONNECTOR | 官方Connector | CLI+Skill有cli.json/runtime，Python自5.0.0支持；至少macOS/Linux，建议Windows；MCP/CLI为不同接入路线 | 先比较后选，不把两条运行时混装；非交互安装与依赖/分发/转换器/字体/路径需实测。公开规则不等新包可获取、已连接或能导出四文件 |
| WB-COVENANT | 开发者公约 | 功能/运行条件/依赖/数据用途如实披露，第三方权利和用户授权需合法依据 | 原始客户资料无授权不外传；公开访问不等转售权；本地包完整不等正式审核或发布 |

## 集成选择的冻结决策

优先本地确定性引擎。可运行Skill和能力有限的引导Expert可以分离交付；不能宣传Expert已自动调用计算。官方可选skills及依赖提供未来集成研究依据，但需验证技能目录/预加载、依赖解析、工具权限、运行时、安装及真实文件路径等完整链路。既有Expert中文名≤15字规则继续保留；拟用中文名须按Phase7当期平台再验。

普通Skill路径、CLI Connector托管Python路径、MCP+Skill路径分别列出本地/账号/依赖/隐私/文件回传证据，不默认新增公网服务。MCP是否可选Python不能从CLI runtime条款外推。没有可验证的私有安装入口时保持BLOCKED，不走正式审核作测试。本轮未登录、上传、安装、召唤、提交审核、定价、发布或部署。

## 来源

- WB-SKILL：https://open.workbuddy.cn/docs/skill
- WB-EXPERT：https://open.workbuddy.cn/docs/expert
- WB-CONNECTOR：https://open.workbuddy.cn/docs/connector
- WB-COVENANT：https://open.workbuddy.cn/docs/developer-agreement

全部能力结论仅为文档层确认；安装调用NOT_TESTED，平台审核NOT_TESTED，发布BLOCKED。源站页面无公开版本号时记录访问日及内容hash，不杜撰版本。
