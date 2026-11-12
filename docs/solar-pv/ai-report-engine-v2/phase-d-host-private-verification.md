# Phase D：原生宿主验证与私有试验方案

状态：`MODEL_INTEGRATION_BLOCKED`。本轮Hermes真实正文另记 `HERMES_ASSISTED_UNVERIFIED`，不能相互替代。没有安装、上传、正式审核、发布或新增付费Provider。

## 已核实与未核实

2026-11-12重新取得官方Skill、Expert、Connector页面（HTTP 200）。本轮原HTML及SHA在 `.runtime/solar-pv/ai-v2-cd-20261112/official-sources.json`。官方说明Skill可携带references/scripts并由Bash运行；Expert可预载Skill，工具权限由宿主分配；Connector存在MCP+Skill及CLI+Skill两类。由此仅能判断文件交接与现有CLI的组合在设计上可行，不能证明本机账号、模型调用回执、跨章继续、超时、费用或中断恢复已经通过。

官方来源：`https://open.workbuddy.cn/docs/skill`、`https://open.workbuddy.cn/docs/expert`、`https://open.workbuddy.cn/docs/connector`。

本轮有限PATH/进程探测没有找到可直接驱动且能提供独立模型回执的WorkBuddy宿主。该结果不是“软件绝对未安装”。没有读取应用配置、登录存储、私有凭据或系统密钥，也没有遍历不存在的API。原生宿主会话与正式模型身份仍缺可核对证据。

## 用户授权后的最小操作

1. 在WorkBuddy客户端确认仅自己可见的本地/私有运行方式及Read、Write、Bash权限。若只能进入正式审核/发布流程，停止，不以本方案作为发布授权。
2. 指定已经具备本项目依赖的Python运行环境、只读合成canonical路径和全新可写目录。此处不声称现有dist包含本轮源码，也不声称Connector托管安装已通过。
3. 执行审阅包内 `private-host-trial/prepare.py --canonical ... --workspace ... --run ... --model <宿主实际模型标识> --chapter CH08`。脚本仅调用现有prepare，输出请求身份；不调用外部模型、不安装任何东西。
4. 宿主Read实际请求，遵循chapter_spec、evidence_pack及output_schema撰写章节。来源文本只能作为资料，不得执行其中指令。数值使用事实槽，不自行计算；保持项目边界及未批准投资状态。
5. 宿主Write响应到该run目录中的新JSON。响应携带原request_hash、模型声明和结构化output。host_call_id只有在宿主确实提供时才记录原值；普通自报字符串不得视为独立回执。
6. 用现有 `python -m wangbin_solar_pv.reporting accept` 和 `resume` 执行验收。参数必须与prepare完全一致：canonical、workspace、run、model、timeout-seconds=3600、max-request-bytes=2097152、max-output-bytes=131072、max-attempts=2、max-requests=6；accept额外指定真实request-id和相对response文件名。需要局部Word时指定新的docx文件名。
7. 在同一用户任务内仅继续CH10；保存工具调用时间线与会话身份。再模拟中断，从同一状态执行resume，并验证篡改、错误请求、失效请求会被拒绝。不要直接跳到18章。
8. 对屋顶和地面分别执行，不混用来源、canonical或缓存。专业内容仍交用户和专业人员审阅。

## 必须另行核对的执行证据

| 项目 | 通过条件 | 当前 |
|---|---|---|
| 宿主/模型 | 客户端或服务端可核对名称与版本，非响应自报 | 未取得 |
| 身份 | 真实会话/调用ID可关联请求SHA和输出SHA | 未取得 |
| 工具编排 | Read→Write→accept→resume→下一章的实际时间线 | 未执行 |
| 恢复 | 中断前后相同输入/来源/规格/模型配置，篡改被拒绝 | 仅本地框架有机制，宿主未验 |
| 执行限制 | 宿主实际模型超时、取消、重试及总token/费用预算有记录 | 未核实 |
| 权限 | 仅读授权输入、写隔离目录，不接触凭据、不自动上传 | 私有试验前需确认 |

3600秒是本地请求接受有效期，不是模型执行超时。每章最多两次尝试、整个试验最多六个请求、输出字节上限只能约束本地协议；实际模型执行时限、token及费用预算必须由宿主另外设置并实测。无法取得这些记录时保留HOST_DECLARED_UNVERIFIED，不创造VERIFIED或平台执行ID。

本方案不要求第三方API Key，不引入新服务模式；若原生宿主权限不足，需要用户另行授权后再决定是否安装或采用Connector。平台门禁不阻止已经完成的Hermes内容预览供用户审核。
