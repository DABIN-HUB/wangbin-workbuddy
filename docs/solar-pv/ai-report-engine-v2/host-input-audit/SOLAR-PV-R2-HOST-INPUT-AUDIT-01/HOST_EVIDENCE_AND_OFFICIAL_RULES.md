# 主机事件、官方规则与未发送询证

任务：SOLAR-PV-R2-HOST-INPUT-AUDIT-01。仅只读审计；不是新的宿主试验。

## 1. 证据等级与本轮新增现场观察

### A. manager 直接只读现场（本轮用户转交；不是 provider log）

manager 在已有屋顶 R2 任务中观察 `WorkBuddyAI.exe`，PID `219384`、window `16267348`，UI 显示 `5.5.2`。未提交输入、未创建新模型任务。

- 帮助菜单实际存在“诊断工具”“打开日志目录”。诊断工具显示网络/代理/hosts 服务检测及“开始检测”；未执行检测、未打开日志目录。
- 设置→安全中心→审计中心→查看全部实际可访问。界面有全部类型/结果/时间筛选，显示 86 条；可见首条时间 `2026/11/13 09:47:48`，不能把它当作本次 R2 运行日志。
- 界面有“导出日志”“清空”，均未点击。没有导出全量无关记录，没有清除日志。
- 审计中心官方搜索框精确查 `r2-client-552-20261113-132354` 为零条；扩大为 `r2-client-552` 仍零条。只操作审计搜索框，未向模型发送内容。
- 没有改变安全、防护、内置 Python 或其他开关。审计入口附近的“内置 Python 启用”控件不证明 Skill Bash 实际解释器、安装包或 Connector 环境。

结论：**5.5.2 本机存在安全/审计 UI，已不再 UNKNOWN；该 UI 是否覆盖 provider 敏感返回仍 UNKNOWN。** 零搜索结果仅说明这两项查询在当前可见列表无匹配，不证明后台没有事件。没有可确认本次事件的独立日志；`PARTIAL_TRACE`、后台原因 `UNKNOWN` 保留。原始交互事件属于 manager 现场会话，developer 不冒充亲自操作或 provider 原始记录。manager 未给出逐点击绝对时间，不能补造。

截图原件位于 `C:/Users/wangbin/AppData/Local/hermes/cache/images/`；本轮 runtime 的 `manager-ui-index.json` 仅保存准确路径、字节与 SHA。最终归档前仅挑必要且隐私复核通过的图片，不能把全量 UI 树或无关审计记录入包。此阶段没有最终审计 ZIP。

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

官方文档本轮 manager/analyst 的可溯源摘录、查询时间及适用范围仍为 `PENDING_MANAGER_EVIDENCE`。以下只是用户指定待核对入口，不把补充背景中的转述当成本轮官方新证据：

| 入口 | 需要确认 | 当前审计状态 |
|---|---|---|
| `https://open.workbuddy.cn/docs/skill` | Skill references/scripts/Bash、依赖与受信执行边界 | PENDING_MANAGER_EVIDENCE |
| `https://open.workbuddy.cn/en/docs/connector` | 托管 Python、隔离安装、适用版本、与 Skill Bash 关系 | PENDING_MANAGER_EVIDENCE |
| `https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes` | 安全/审计能力及导出范围 | 本机存在 UI 已证实；provider 事件覆盖 UNKNOWN；官网版本支持待补 |
| `https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Model` | 当前模型上下文/压缩说明及 5.5.2 适用性 | PENDING_MANAGER_EVIDENCE；Hy4 tokenizer/capacity UNKNOWN |
| `https://www.workbuddy.cn/docs/cli/tools-reference` | CodeBuddy CLI Read 限制 | 仅旁证；不得套用为 WorkBuddy AI 5.5.2 实测 |

未公开的工具返回字节上限、token、截断标志、安全错误精确定义及恢复机制均 UNKNOWN。当前官网说明不能自动推出 5.5.2 的 provider 实现。现场审计 UI 可见也不证明它收录所有工具返回。

## 3. 未发送的官方询证稿

**状态：DRAFT_NOT_SENT。没有联系支持、发送资料或执行模型提示。**

建议由用户另行批准后询问：

1. WorkBuddy AI `5.5.2`、可见模型 `Hy4` 的 Read 返回限制、截断标识、上下文压缩后工具内容保留机制是什么？请给版本化官方说明，而非客户端外观推断。
2. `SENSITIVE_CONTENT_UNAVAILABLE. The Tool or MCP result could not be safely inspected, so its content was withheld from the model.` 属于哪层公开错误类别？是否存在不包含项目正文的事件 ID、原因分类及本次事件专用诊断导出？
3. 安全中心审计列表覆盖文件防护、模型/provider 返回、工具返回中的哪些类别？用 run 目录名搜索不到，是否需要官方支持的本次事件时间/会话标识过滤？不得请求扫描私有数据库。
4. 本版本是否有受支持、透明且不绕过防护的完整整章输入通道？需什么能力证据才能保证文件所有字段和完整 Schema 在生成时可用？
5. 普通 Skill Bash 与 Connector Python runtime 的解释器选择、环境隔离、依赖安装和版本读回分别如何证明？内置 Python 开关的确切语义是什么？

最小拟发送范围（仍未发送）：版本/可见模型名、事件时间范围、脱敏错误原句、文件字节/行数与 hashes、无正文的 run 标识、必要裁剪截图。**不发送** canonical、全部请求内容、合同、来源附件、Token/Cookie、models.json、私有会话库、全量审计日志或账号侧栏。若需要正文/更广日志，必须另行取得用户范围批准。

## 4. 结论约束

缩小输入不等于解除安全返回。不得把离线视图重新投递为试探，不改名/换工具/编码/移位内容绕过防护。只有官方支持路径和单独的新请求/候选/会话授权闭合后，才讨论一次新的 CH08 试验；此轮不执行。
