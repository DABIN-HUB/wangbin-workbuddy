# Phase 4 — WorkBuddy 人工私有验收逐页手册（尚未执行）

**停止条件优先**：目前无本人授权的开发者登录态、已确认的私有草稿入口、公开可安装的 wheel，也没有安全门禁通过；**不要立即上传**。只有本人先决定关闭/承担安全风险、明确同意仅在平台真实非公开的授权测试环境使用无敏样例、提供可信安装来源并确认隐私政策后，才可继续下述私有验收。若页面只有“提交正式审核/公开发布”，在该页停止，不点提交；不要上传正式资产、设置收费或提交密码/验证码/Token。页面按钮名称以登录后实际界面为准；不存在的入口记录 `UNKNOWN` 而不是猜测。

### 页面 1：本人登录/权限核验（仅本人操作）

1. 打开 `https://open.workbuddy.cn/`，本人自行登录；按 [入驻指南](https://open.workbuddy.cn/docs/onboarding) 检查账号、个人/组织主体、CLI Connector 发布权、Skill 草稿权限和私有名单/测试账号，**不把身份材料贴到聊天**。
2. 记录客户端版本、系统版本、开发者主体类别（不记证件号码）和可用的入口名称；截取已脱敏的权限说明。若尚无主体权限或私有测试入口，记 `BLOCKED` 并停止。
3. 确认开发者公约要求功能说明、依赖、权限、数据用途、测试方式与提交版本一致；灰度/授权测试与“公开审核提交”不同（[公约](https://open.workbuddy.cn/docs/developer-agreement)）。

### 页面 2：先确认安装来源，再准备两个 ZIP（不得先上传）

1. 当前 1.2.0 `cli.json` 请求 PyPI 包名，但公开接口 404；因此本阶段**不能跳到页面 3**。由本人在另一获授权阶段选择合法公开无认证来源，核对 wheel URL/哈希、依赖、许可、目标客户端能访问，且安全问题已妥善处理。切忌把 `file:///F:/...` 或私有令牌 URL 写入公开 `init`。
2. 执行位置为仓库的 `dist/` 目录，人工核对 `sha256sum -c` 三个 1.2.0 sidecar；历史本地哈希见 `phase4-distribution.md`。重新构建后必须重新算，不要使用历史旧 wheel。检查 Connector ZIP 内 `connector-meta.json`、`cli.json`、`icon.svg`、`skills/.../SKILL.md`；Skill ZIP 内 `SKILL.md` 与其引用。当前 ZIP 根目录有外层目录，是否接受留待私有解析。
3. **安装顺序**：若存在私有试传，先安装/连接 Connector ZIP `wangbin-document-cli-1.2.0-connector-candidate.zip`（内嵌 Skill）；只有确需验证独立安装路径且平台确认同名 Skill 不冲突时，才另外导入 `wangbin-document-assistant-1.2.0-skill-candidate.zip`。不要单独安装老版 1.0.0 脚本 Skill 并冒充 1.2.0 能力。

### 页面 3：私有资产草稿/解析（有明确非公开入口才进入）

1. 在实际开发者后台找到**草稿、私有预览或仅测试账号可见的试传入口**；确认不会触发公开审核，再导入 Connector ZIP，记录资产 ID、版本、`minWorkbuddyVersion=5.0.0`、包内 Skill 文件树与解析结果；如 ZIP 外层目录不接受，停下记录错误，不直接提交公开审核。
2. 仅在已确认私有导入与目标客户端权限后，在测试客户端找到“专家·技能·连接器”相关连接器入口，选择该 Connector 并点界面实际的“安装/连接”；观察 `init`、托管 Python 3.12 的实际位置（只记录脱敏路径）、5 分钟内是否完成、是否访问正确可信源、依赖解析和失败提示。WorkBuddy 并未承诺业务命令的硬限或安装在本机；观察后再记录。
3. CLI 诊断：在平台允许的非交互命令环境中执行或从平台调度 `wangbin-document-cli version`、`doctor`、`status`（Windows 为 `.exe`），留退出码与 `version=1.2.0`、`dependencies=ready`、`LOCAL_READY`；`pip check` 在同一托管 Python 中执行。无外部账号，**不要伪造 OAuth/Token**。如果平台不提供直接命令面板，记录 UI 限制，改以真实 Skill 调用日志取证，不绕权限。看到 `LOCAL_READY` 仅证明包依赖健康，不证明安全隔离。

### 页面 4：聊天/文件输入（只用无敏授权样例）

1. 在有权访问的私有对话里确认 Connector 内嵌 Skill 已启用、Bash 调用需要的授权已实际获准；若平台支持独立 Skill 市场安装，按 [Skill 页面](https://open.workbuddy.cn/docs/skill) 左侧“专家·技能·连接器”→“技能”→卡片右上角“+”安装**1.2.0 版本且已私有解析成功的** Skill，再检查是否出现同名冲突。页面里无私有资产可安装则记录 `BLOCKED`。
2. 本地准备一个**本人创建且无个人信息**、可文本提取的 PDF，以及一个包含表头和两条相同数据、一条不同数据的 XLSX。先记录源文件 SHA-256 和期望行数；不要上传生产文档、真实凭据或客户资料。文件只授权到专用只读输入目录，输出到不同的专用目录；验证它们在 CLI 实际运行位置可见，别预设 UI 上传自动得到本地路径。
3. PDF 测试：显式选择该 PDF 后输入“帮我提取这个 PDF 的全部文本，并标记质量限制，不要把原文提取冒充 AI 摘要。”观察是否由真实 Skill 触发 `status`→`parse --input <实际授权路径> --input-root <授权目录> --output-root <独立目录>`；记录脱敏命令、退出码、JSON `status/source_name/text/quality_notes`、实际消息。若空文本、扫描件或失败，报告原错误而非补写结果。再要求模型总结已提取文本，单独保存真实模型调用/原文事实与推断；无模型调用就不能叫 AI 摘要。
4. Excel 测试：仅在**安全与平台许可均允许的非公开环境**显式选择该 XLSX，输入“把这份 Excel 按整行去重并导出新的 XLSX，不覆盖源文件。”观察真实 `deduplicate --format xlsx` 的输入/输出授权路径、JSON `output_path/rows_read/rows_written/duplicates_removed`、退出码；对照源哈希不变、新 XLSX 重新打开且内容正确。若 WorkBuddy 未给可下载附件或导出路径仅在隐藏的 CLI 宿主，判端到端**失败**，不能把 JSON 路径当可下载交付。

### 页面 5：失败、清理、卸载及记录

1. 用无敏且明确授权的损坏 PDF、错误扩展名、越界路径和不可写输出目录触发失败，查对话错误、CLI JSON `error.code` 与退出码；使用平台合法的日志/调试入口查看脱敏信息，不绕过系统权限，也不要把原始私密文本写入公开日志。观察超时及直接子进程；后代与硬资源风险仍需独立验证。
2. 在消息附件/下载处**实际点击下载**新 XLSX，核对扩展名、打开结果、文件哈希与源文件不覆盖；如果只看到 `output_path`、无下载按钮，记 `WORKBUDDY_E2E_PASS=FAIL/BLOCKED` 并停下，不假造交付。
3. 查看客户端卸载/断开 Connector 和 Skill 的实际入口；记录命令仍可调用否、平台是否保留托管 Python/pip 缓存/输出（文档未承诺清理）；人工清理**本人专用无敏测试目录**，不删除用户源文件。若平台需要公开提交审核才可完成以上任一步骤，停在该步骤。

**脱敏取证模板**：步骤号｜实际页面标题/客户端版本｜私有资产 ID（非凭据）｜OS/Python｜命令与退出码｜解析后的 JSON 状态/错误码｜模型调用是否真实发生｜PDF 原文段落对应关系｜源/输出哈希｜可下载附件实证｜结论 PASS/FAIL/BLOCKED/NOT_TESTED。所有账号、密码、Token、密钥、连接字符串以 `[REDACTED]` 代替。没有这些真实记录时 `WORKBUDDY_INSTALL_PASS` 和 `WORKBUDDY_E2E_PASS` 保持 `BLOCKED`。