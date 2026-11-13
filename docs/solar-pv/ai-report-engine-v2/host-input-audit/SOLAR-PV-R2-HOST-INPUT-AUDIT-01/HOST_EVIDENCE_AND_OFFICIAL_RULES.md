# 主机事件、官方规则与未发送询证

任务：SOLAR-PV-R2-HOST-INPUT-AUDIT-01。仅只读审计；不是新的宿主试验。

## 1. 证据等级与本轮新增现场观察

### A. manager 本轮直接工具操作后转交 developer（不是用户转述或 provider log）

manager 在已有屋顶 R2 任务中观察 `WorkBuddyAI.exe`，PID `219384`、window `16267348`，UI 显示 `5.5.2`。未提交输入、未创建新模型任务。

- 帮助菜单实际存在“诊断工具”“打开日志目录”。诊断工具显示网络/代理/hosts 服务检测及“开始检测”；未执行检测、未打开日志目录。
- 设置→安全中心→审计中心→查看全部实际可访问。界面有全部类型/结果/时间筛选，显示 86 条；可见首条时间 `2026/11/13 09:47:48`，不能把它当作本次 R2 运行日志。
- 界面有“导出日志”“清空”，均未点击。没有导出全量无关记录，没有清除日志。
- 审计中心官方搜索框精确查 `r2-client-552-20261113-132354` 为零条；扩大为 `r2-client-552` 仍零条。只操作审计搜索框，未向模型发送内容。
- 没有改变安全、防护、内置 Python 或其他开关。审计入口附近的“内置 Python 启用”控件不证明 Skill Bash 实际解释器、安装包或 Connector 环境。

结论：**5.5.2 本机存在安全/审计 UI，已不再 UNKNOWN；该 UI 是否覆盖 provider 敏感返回仍 UNKNOWN。** 零搜索结果仅说明这两项查询在当前可见列表无匹配，不证明后台没有事件。没有可确认本次事件的独立日志；`PARTIAL_TRACE`、后台原因 `UNKNOWN` 保留。原始交互事件属于 manager 现场会话，developer 不冒充亲自操作或 provider 原始记录。manager 未给出逐点击绝对时间，不能补造。

截图原件位于 `C:/Users/wangbin/AppData/Local/hermes/cache/images/`，三个选定原件在ignored runtime私下保留且不变；manager-ui-index.json保存准确原路径/字节/SHA。归档仅用新的最小裁剪衍生，全量UI树/原截图/无关审计记录不入包；最终ZIP实际身份见RUN/final-delivery.json，developer裁剪不冒称独立QA隐私验收。

### B. 历史本机原始材料（已读真实文件并重新核验）

真源目录：`.runtime/solar-pv/r2-client-552-20261113-132354/`。

- `RESULT.md`、`client-identity.json`、`gates.json`；review ZIP 载荷与本地材料逐字节相同。
- 屋顶 `workspaces/industrial_rooftop/host-prompt.txt` 与 `host-response-ui-copy.txt` 完整读取。回复中“继续对话”文字属于原样保存的宿主文本，不证明有人追加提示；旧 RESULT 明确只提交一次。
- `ui-trace/roof-03-read-end-context-compression.json` 的可见辅助树包含“正在压缩上下文”。`roof-04-host-stopped.json` 记录停止回复及 13:44；两者均标 `VISIBLE_UI_ACCESSIBILITY_ONLY_PARTIAL_TRACE`，不是全量传输记录。
- 旧 RESULT/截图记录总时长 `7m32s`。时长与压缩 UI 是现场可见记录；本轮未重新发起观察任务。
- 两案 run 内都没有 `CH08-1-draft.json`；不执行 Schema/strict 产品校验、不增加章节通过数。

### C. 宿主自述，不能升级为后台事实

`host-response-ui-copy.txt` 第 24–25 行称：读过 1–11000 行，11001–11500 行返回 `SENSITIVE_CONTENT_UNAVAILABLE`，后两段空返回；压缩后具体事实槽、来源映射、公式表格与 Schema 已不在当前上下文。

这只能归为 **HOST_REPORTED**。未取得对应 Read 原始 payload 或 provider 诊断码；不能认定具体安全规则、某个词触发、hash 被误判密钥、普通 token 超限或改模型即能恢复。磁盘完整文件、界面“已读取”、模型回显 hash，都不能证明生成时完整持有上下文。

## 2. 官方资料边界

五个指定入口已由现有Python3.14.9标准库urllib.request实际GET并落盘完整HTML，不执行网页脚本；每入口20秒timeout、五路并行，HTTP均200/exit0。查询日2026-11-13、时区UTC+08:00，逐URL真实起止/正文SHA/支持范围在RUN/official/sources.json和support-index.json；命令解释器、脚本SHA、URL集inputhash、实际exit/stdout/stderr在fetch-command.json。必要摘取是标行号的独立衍生，完整原文保留本地，不能拿文本SHA当HTML原SHA。

| 入口 | 当前文档真实支持与版本界限 | 完整HTML SHA-256 / 实际查询起止（UTC+08） |
|---|---|---|
| `https://open.workbuddy.cn/docs/skill` | references作为上下文、scripts经Bash调用（text77–89行）；不证明本次Skill Bash解释器/依赖或持续持有 | `6ac24dbdbe0d7f8bf907e30b9c71909c0f87499561ee87de011a0a818041c68c`；15:32:22.878442—15:32:23.228737 |
| `https://open.workbuddy.cn/en/docs/connector` | CLI runtime中Python最低版本标注v5.0.0，托管Python/venv/pip隔离（text569、578–592）；不证明普通Skill Bash共用解释器。勿把stdio MCP的Node-only字段当Python证据 | `c251ffbcd0ecb0d15490bc8bbae0bf076d1e66fec5cfca9976868615c0d724eb`；15:32:22.879704—15:32:23.397156 |
| `https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes` | 安全中心、运行时、审计拦截/放行及导出/清空（text225–229、245–246）；本机5.5.2 UI另有manager实证，provider本次覆盖/原因UNKNOWN | `0135246b8198a468572a192ff2db9572d32fc0473f302b2269c92a3d0583f51d`；15:32:22.880666—15:32:23.334382 |
| `https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Model` | 当前经济模式/上下文压缩选项（text137–140）不倒推历史5.5.2/Hy4实际设置或容量；未改设置 | `21385d3152774fe22083bdd492ecfe02cedc63aca063135cd974565647129240`；15:32:22.881584—15:32:23.289769 |
| `https://www.workbuddy.cn/docs/cli/tools-reference` | CodeBuddy CLI Read单行2000字符、默认20000 token及PARTIAL说明（text543–554）仅旁证；不能套为WorkBuddy AI5.5.2实测阈值，不据此重投 | `24d582058bd879a3885b4bf2af9a2d58a5046930f350bdc30003bb0971ec36e7`；15:32:22.882393—15:32:23.428782 |

未公开的工具返回字节上限、token、截断标志、安全错误精确定义及恢复机制均 UNKNOWN。当前官网说明不能自动推出 5.5.2 的 provider 实现。现场审计 UI 可见也不证明它收录所有工具返回。

实际渠道：analyst/manager前期标准库GET、manager公开搜索降级索引及本阶段重新落盘的标准库GET。manager已说明web_extract在当前backend为search-only而失败；公开索引覆盖Skill/Connector/security/Model，CLI索引空但实际GET200，不能将搜索0当文档不存在。五个原文hash与manager早期GET转交值一致，但本阶段原文来自上述新GET，不冒充早期响应体。不声称成功web_extract/web.run或伪造引用句柄；analyst live log是长消息截断预览，不补造其完整历史hash/内存程序。

三个必要截图已在RUN/share-preparation/cropped-ui/另存新身份；cropped-ui-index.json记录原SHA、新SHA、半开坐标、源图尺寸和像素精确对应。审计存在只保留标题区，两项零搜索仅保留panel，排除左账号/任务侧栏、背景正文和无关记录。原图/全量capture/AX树不入包。此为developer整改，不是quality重新验收。

## 3. 未发送的官方询证稿

**状态：DRAFT_NOT_SENT。没有联系支持、发送资料或执行模型提示。**

建议由用户另行批准后询问：

1. WorkBuddy AI `5.5.2`、可见模型 `Hy4` 的 Read 返回限制、截断标识、上下文压缩后工具内容保留机制是什么？请给版本化官方说明，而非客户端外观推断。
2. `SENSITIVE_CONTENT_UNAVAILABLE. The Tool or MCP result could not be safely inspected, so its content was withheld from the model.` 属于哪层公开错误类别？是否存在不包含项目正文的事件 ID、原因分类及本次事件专用诊断导出？
3. 安全中心审计列表覆盖文件防护、模型/provider 返回、工具返回中的哪些类别？用 run 目录名搜索不到，是否需要官方支持的本次事件时间/会话标识过滤？不得请求扫描私有数据库。
4. 本版本是否有受支持、透明且不绕过防护的完整整章输入通道？需什么能力证据才能保证文件所有字段和完整 Schema 在生成时可用？
5. 普通 Skill Bash 与 Connector Python runtime 的解释器选择、环境隔离、依赖安装和版本读回分别如何证明？内置 Python 开关的确切语义是什么？

6. 当前Model文档压缩选项最早适用哪些客户端版本？如何仅由已有无正文事件标识确认历史5.5.2设置，而不读取models.json/私有会话库或重发受阻内容？

最小拟发送范围（仍未发送）：版本/可见模型名、事件时间范围、脱敏错误原句、文件字节/行数与 hashes、无正文的 run 标识、必要裁剪截图。**不发送** canonical、全部请求内容、合同、来源附件、Token/Cookie、models.json、私有会话库、全量审计日志或账号侧栏。若需要正文/更广日志，必须另行取得用户范围批准。

## 4. 结论约束

独立QA原文总裁定PARTIAL，见QA_INDEX.md与RUN/independent-qa/QUALITY_REPORT.verbatim.md，仅覆盖原作者快照。`closure()`仅部分引用一致性helper，UNKNOWN metric/claim、duplicate source和同源跨节事实不能由它独立识别，VALID不等于完整授权PASS。当前双案权限来自独立QA另查；decoder另以可信原请求完整树精确比较拒绝重seal篡改。本轮仅补文档/机器回执与共享隐私，审计脚本/实验不改；developer落实不冒称quality复验文档或ZIP。

缩小输入不等于解除安全返回。不得把离线视图重新投递为试探，不改名/换工具/编码/移位内容绕过防护。只有官方支持路径和单独的新请求/候选/会话授权闭合后，才讨论一次新的 CH08 试验；此轮不执行。
