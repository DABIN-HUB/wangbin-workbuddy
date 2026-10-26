# Phase 3 WorkBuddy 私有验收操作手册与结果

**当前结果：`WORKBUDDY_INSTALL_PASS=BLOCKED`，`WORKBUDDY_E2E_PASS=BLOCKED`。** 没有本人授权的开发者登录态、确认可用的草稿/私有测试入口或公开可安装的 1.2.0 包；本轮没有登录、上传 ZIP、执行平台对话、正式提交审核或设置收费。此文是人工验收顺序，不是伪造的平台运行记录。

官方参考：

- https://open.workbuddy.cn/docs/onboarding （本人入驻、主体/账号信息）
- https://open.workbuddy.cn/docs/connector （CLI Connector 规范、托管 Python、安装与状态）
- https://open.workbuddy.cn/docs/skill （Skill 资源规范）
- https://open.workbuddy.cn/docs/developer-agreement （授权/发布边界）

## 必须先由本人完成

1. 在浏览器访问 https://open.workbuddy.cn/ ，本人登录并按 `docs/onboarding` 核实开发者主体、账号类型、创建和**草稿/私有测试**权限。不要向聊天提供密码、验证码、Token、身份证或私有索引凭证。
2. 本人确定包分发（推荐 PyPI，见 `phase3-distribution-analysis.md`）。在许可证与安全阻断项被本人接受/关闭后，本人自行发布 1.2.0 wheel。验证 `wangbin-document-cli==1.2.0` 从目标 WorkBuddy 客户端网络、托管 Python 环境可独立安装及依赖可达；记录版本/下载 URL/SHA-256/退出码（遮蔽凭据）。**没完成不得把当前 Connector ZIP 当作已可安装产品上传。**
3. 以 `sha256sum -c` 或平台等效校验命令对 `dist/*.sha256` 中的 1.2.0 三个候选校验；确认包里只有 `connector-meta.json`、`cli.json`、`icon.svg`、`skills/...` 等允许内容，不含用户文档、测试数据和私钥。当前候选 ZIP 有一层 `wangbin-document-cli/` 或 `wangbin-document-assistant/` 根目录，实际平台是否接受**仍须平台私有解析来确认**。

## 私有试传（仅在确实存在不公开入口时）

| 步骤 | 本人操作 | 必须保留的脱敏证据 | 未通过时 |
|---|---|---|---|
| P01 | 在开发者后台的草稿/私有预览入口导入 `dist/wangbin-document-assistant-1.2.0-skill-candidate.zip` | 页面、资源树、Skill 版本及 ZIP 根目录解析结果 | 若只有“提交公开审核”，立即停止，不提交 |
| P02 | 同一私有入口导入 `dist/wangbin-document-cli-1.2.0-connector-candidate.zip` | `connector-meta.json`/`cli.json`/自带 Skill 的解析回执与平台识别的 `minWorkbuddyVersion` | 若要求未知认证字段，不伪造 OAuth；保存脱敏报错待官方确认 |
| P03 | 在 WorkBuddy >=5.0.0 测试客户端安装/连接 Connector | 托管 Python 版本、是否独立于系统 Python、`init` 安装命令/退出码、`pip check` 与 `status=LOCAL_READY` | 如果不能从索引安装依赖则 `WORKBUDDY_INSTALL_PASS=FAIL`，不继续对话 |
| P04 | 启用 Connector 自带 Skill；独立 Skill 仅在必要且不冲突时启用 | Skill 实际触发名、CLI 实际可执行路径、Bash 权限提示 | 记录双份 Skill 的冲突，不删用户数据 |
| P05 场景 A | 在授权的测试文件夹给一个 PDF，说“帮我提取这个 PDF 的全部文本。” | 命令退出码、JSON `status`/`source_name`/质量提示，以及对话里真实展示的提取文本（只用无敏示例） | 空提取不能称完整文本；保存错误码 |
| P06 场景 B | 给一个有重复记录的 XLSX，说“帮我把 Excel 里面的重复记录删除，然后生成新的 Excel。” | 源/产物 SHA-256、`rows_read`/`rows_written`/`duplicates_removed`、客户端确实返回可下载的新 XLSX 且重新打开 | 文件未交付或被覆盖视为失败 |
| P07 场景 C | 授权多文件，说“帮我分析这些文件，并分别生成内容摘要。” | 原文解析 JSON + 明确的 WorkBuddy 模型实际调用记录 + 每份摘要与原文引用的区别 | 未发生模型调用只能报“原文提取”，不能声称 AI 摘要 |
| P08 | 损坏文件、中文/空格路径、越界路径、无输出权限和异常后恢复 | CLI JSON 错误码、退出码、脱敏运行日志与无多余输出/孤儿进程观察 | 输入失败不应伪装成功 |
| P09 | 检查更新/卸载提示、不触碰用户源文档或输出、缓存中不残留敏感信息 | 平台和本地检查记录 | 不自动卸载或删用户文件 |

平台仍须确认：私有试传实际入口、上传权限、ZIP 根层级、`init` 网络/权限/工作目录、无远程账号时的 `status` 联通判据、Skill 附带 CLI 的运行授权及输出附件交付。没有真实平台执行证据前，`SKILL_INTEGRATION_PASS`、`WORKBUDDY_E2E_PASS` 保持 BLOCKED。

取证模板（本人在本地安全保存，不把凭据或原始私密文档贴入聊天）：WorkBuddy 桌面版本；OS/Python 版本；开发者后台私有资产 ID；步骤号；命令/退出码；脱敏日志位置；实际 JSON 状态/错误码；生成文件 SHA-256；操作者确认。遇见密钥、Token、账号密码或连接字符串，一律用 `[REDACTED]`。
