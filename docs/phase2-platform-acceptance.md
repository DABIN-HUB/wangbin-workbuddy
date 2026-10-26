# WorkBuddy 真机验收用例与人工操作（Phase 2）

本文件是**操作指南，不是已执行结果**。当前所有平台安装、聊天执行与审核均 `NOT_TESTED/BLOCKED`；不在聊天发送密码或 Token，不自动提交审核。完整候选包路径与 hash 见 `dist/wangbin-document-cli-1.1.0-candidate-manifest.json`。

## 前置门禁

1. 在开发者本人浏览器打开 https://open.workbuddy.cn/ ，自行登录/入驻；按 https://open.workbuddy.cn/docs/onboarding 完成个人或企业主体认证。由本人确认是否拥有创建/上传连接器、Skill 的权限。不要交付身份证、验证码或账户凭据给代理。
2. 在**任何上传之前**，由本人将经过许可证与安全审核的 `wangbin-document-cli==1.1.0` wheel 发布至目标 WorkBuddy 所能访问的可信 Python 包索引，并在该客户端网络/托管 Python 环境实际验证 `python -m pip install --only-binary=:all: wangbin-document-cli==1.1.0`；保留包名所有权、下载 URL/版本哈希、安装退出码、`pip check` 证据。如果不做此步，**停止上传**，因为现在公开 PyPI 路径不存在。
3. 核对 WorkBuddy 桌面版本至少 5.0.0。`cli.json` 声明 Python 3.12；如果 WorkBuddy 不提供该版本，停止并记录实际错误，不自动回退到系统 Python。
4. 检查候选包 SHA-256 与 manifest 一致，仅把候选中的官方资源上传，不把本地用户文件、wheel、开发报告或密钥塞进 Connector ZIP。

## 平台顺序与证据（人工）

| 顺序 | 人工动作 | PASS 判据 | 失败时记录 |
|---|---|---|---|
| P01 | 在 https://open.workbuddy.cn/ 的登录态开发者入口选择创建 Skill，参考 https://open.workbuddy.cn/docs/skill 上传 `dist/wangbin-document-assistant-1.1.0-skill-candidate.zip` 的**私有测试候选**。仅确认解析，勿正式提审。 | 解析显示 Skill 名称、版本和资源，确认 ZIP 根层级。 | 脱敏错误、上传页面和产品 ID；根层级未明时不得猜填字段。 |
| P02 | 参考 https://open.workbuddy.cn/docs/connector 的 CLI 方案，在有权限的开发者入口以私有/测试方式导入 `dist/wangbin-document-cli-1.1.0-connector-candidate.zip`。 | 能识别 `connector-meta.json`、`cli.json`、`icon.svg`，Skill 被读取；没有未知必填字段。 | 脱敏平台解析消息。若必须提交审核才能导入，**停止该动作并请本人决定**。 |
| P03 | 在经授权的 WorkBuddy 客户端测试安装 Connector（至少 5.0.0）；检查它执行由平台托管的 Python `init`。 | `init` 真正从可信索引安装同一 1.1.0 wheel 及依赖，不从用户系统 Python 取包；`status` 返回 `LOCAL_READY`。 | 安装命令退出码、脱敏日志、Python 版本；绝不记录索引凭据。 |
| P04 | 连接/启用 Connector 并检查其自带 Skill；若 Skill 未自动加载，再人工启用 P01 的独立 Skill。 | 只加载所需 Skill，不出现重复冲突；确认 Bash 命令 `wangbin-document-cli` 或 Windows `.exe` 可调用。 | 安装/加载错误、技能是否重复。 |
| P05 | 在对话选择一份授权的真实 PDF、DOCX、XLSX、PPTX、HTML、TXT、Markdown，逐种下达“读取并整理”请求。 | 七类均有真实文本、质量提示；未上传到未经授权服务；产物和来源对应。 | 每格式失败码、脱敏结果摘要，不截图用户全文。 |
| P06 | 选择多份文件（含一个损坏文件）下达批处理请求。 | 返回 `partial_failure`，成功文件结果保留，损坏文件原因明确。 | 批次状态/逐项数量。 |
| P07 | 对授权 XLSX 去重并导出到独立目录。 | 新 XLSX/CSV 可真实重新打开，删除重复行数量准确，源文件 hash 不变。 | 输入/输出文件 hash、计数和脱敏文件名。 |
| P08 | 用含中文/空格的路径、越界路径、大文件和缺依赖情形验证失败处理。 | 引号和编码正确；越界、超限、安全拒绝有稳定码；依赖缺失不被误报处理成功。 | 退出码、错误码、进程时间、输出是否写入。 |
| P09 | 确认断网时已安装的处理命令仅本地工作；检查用户文件权限和报错脱敏。 | 无解析时下载或未授权外传。 | 脱敏网络/进程观察证据。 |

P01/P02 是否可在无正式提审情况下私有试传并非公开文档确认；若入口不允许私有测试，**不要提交审核**，保持对应项 BLOCKED。所有对话测试必须由有权使用该 WorkBuddy 账号的人完成，平台结果另存到 `reports/`，不得回写或改称本地结果为平台证据。

## 状态边界

- 本地轮：Windows 隔离安装与 CLI 实测支撑 `CLEAN_INSTALL_PASS` 和 `CLI_RUNTIME_PASS` 为 PASS，Skill 命令与元信息仅静态校验；没有 WorkBuddy 中真实 Skill→CLI 调用证据，`SKILL_INTEGRATION_PASS` 保持 BLOCKED。
- 平台轮：只有上述 P01–P09 真的取得记录后，才更新 `WORKBUDDY_INSTALL_PASS`、`WORKBUDDY_E2E_PASS`；审核/上架仍由平台决定。
- macOS/Linux 与 WorkBuddy 真实托管 Python 尚未执行；跨 OS 和 Python 包公开可达性不能从 Windows wheel 成功推断。
