# Phase 4 — WorkBuddy 平台能力证据（非平台实测）

核对日期：2026-10-26。证据范围：当日重新获取的 WorkBuddy 官方公开页面正文，以及当前仓库配置；没有开发者登录态、私有试传页面截图或 WorkBuddy 执行日志。`UNKNOWN` 表示文档没有对**本产品所需的具体行为**给出足够明确的承诺，不能反推支持或不支持。平台文档描述与客户端实测严格分开。

## 官方逐项核对

| 项目 | 公开文档能确认什么 | 当前产品/缺口 | 结论 |
|---|---|---|---|
| CLI 运行位置 | Connector 文档称 WorkBuddy 安装、调度 CLI，并准备托管 Python、管理安装目录；**未明确写明所有 CLI 业务命令一定运行在用户本机、文件可见范围或由哪个进程身份执行**。 | `cli.json` 为 Python 3.12 与各 OS 的 `init`；本地 CLI 运行不证明 WorkBuddy 运行位置。 | **UNKNOWN**：目标客户端实际主机/沙箱位置需私有实测。 |
| 本机与云端 | 文档将 MCP 远程服务与本地 stdio、用户本机 Token 存储区分开；对 CLI 业务命令的云端代理、模型可见的文档文本和网络传输边界没有完整保证。 | 原始文件本地解析的宣传、返回 JSON 进入聊天模型是不同的数据流；不能宣传端到端“所有内容不上传”。 | **UNKNOWN**：CLI/模型/附件路径需实际观察。 |
| Python 运行时 | Connector `cli.json` 的 `runtime.type: python` 从 WorkBuddy 5.0.0 起支持；文档称准备托管 Python 并激活管理的虚拟环境，pip 与缓存位于管理目录，用户不必预装 Python。 | 当前 `minWorkbuddyVersion=5.0.0`，`runtime.version=3.12`；目标客户端是否实际安装成功待测。 | **文档支持**运行时管理；**实际兼容 UNKNOWN**。 |
| 操作系统权限 | 文档要求 CLI 跨 macOS/Linux、建议 Windows；没有给出受限账号、文件系统授权、工作目录、可访问用户文件或网络权限的完整保证。 | CLI 与用户权限等同还是更小无法由 venv 推出。 | **UNKNOWN**。 |
| 安全隔离 | 文档只称 Python venv、pip 目录/缓存与系统环境隔离。 | venv 不是 CPU/内存/系统调用/文件权限沙箱，当前普通解析子进程也不是。 | **OS 安全沙箱 UNKNOWN**；不可把“隔离安装”写为沙箱。 |
| CPU/内存限制 | 官方 Connector 页没有声明 CLI 业务命令的强制 CPU、内存、进程数配额。 | Windows 无 Job Object 限额，Excel 主进程仍无硬限。 | **UNKNOWN**。 |
| 超时/终止 | 文档列出 `init` 5 分钟、`auth` 10 秒、`status` 10 秒、`unAuth` 30 秒及认证轮询 5 分钟；这些是安装/认证命令的规则，不是 `parse`/`deduplicate` 的业务命令限制，也不保证杀进程树。 | 本产品 `parse` 父进程内部有壁钟超时；Excel 迭代限时是协作检查。 | **安装/认证有文档值**；业务命令超时与后代清理 **UNKNOWN**。 |
| Skill 与 Connector | Connector 包允许 `skills/{name}/SKILL.md`，CLI 缺工具协议所以强烈推荐 Skill；文档称包内多个 Skill 会加载。独立 Skill 在技能市场可单独安装并在对话中调用。 | Connector ZIP 内嵌 CLI Skill，另有独立 Skill ZIP；内嵌说明要求先安装 Connector，但**不存在文档证据表明独立 Skill 自动安装 CLI**，双份同名 Skill 是否冲突未测。 | **包内结构有文档支持**；实际触发/顺序/权限 **UNKNOWN**。 |
| 用户安装/卸载 | 技能市场：左侧“专家·技能·连接器”→“技能”，卡片右上角“+”安装；Connector 文档描述用户“连接”触发 `init`→`status`→按需 `auth`。未给出本产品 CLI wheel 的目标客户端获取与卸载/缓存删除的完整流程。 | `status=LOCAL_READY` 是本地依赖诊断，不是账号登录；没有真实平台安装/卸载记录。 | **技能安装、连接流程文档支持**；Connector UI 细节/卸载效果 **UNKNOWN**。 |
| 个人开发者发布 CLI | 入驻指南明确有个人认证，一个账号最多一个个人主体，当前仅支持大陆二代身份证；Connector 页要求提交目录给团队审核通过后进入市场。没有逐条承诺**个人主体有 CLI Connector 公开上架权**。 | 个人认证≠该类资产发布许可；不得代替本人认证。 | **个人主体可申请认证**；CLI 类目发布权限 **UNKNOWN**。 |
| 私有测试 | 公约允许如实披露的灰度发布、授权测试；但公开页面未给出个人账号可操作的 Connector/Skill ZIP 私有上传入口、名单、权限及预览生命周期。 | 未持授权会话，也没确认草稿/私有测试入口。 | **UNKNOWN**；若只有公开审核提交，停止。 |

依据：[Connector](https://open.workbuddy.cn/docs/connector)（CLI + Skill、运行时管理、认证时限、包结构与提交前检查）；[Skill](https://open.workbuddy.cn/docs/skill)（市场安装与 SKILL.md）；[入驻指南](https://open.workbuddy.cn/docs/onboarding)（个人认证）；[开发者公约](https://open.workbuddy.cn/docs/developer-agreement)（2.1.2、2.1.4 的审核/授权测试）；[专家](https://open.workbuddy.cn/docs/expert)（专家依赖声明仅作另一产品形态参考）。以上链接是文档证据，不是平台功能实测证据。

## 本项目静态链路与不成立的推论

`packages/connectors/wangbin-document-cli/connector-meta.json` 为 `type=cli`、版本 1.2.0、最低客户端 5.0.0；`cli.json` 以 `python -m pip install ... wangbin-document-cli==1.2.0` 安装，并通过 `statusMatch=^LOCAL_READY$` 判断依赖就绪；Connector 自带 `packages/skills/wangbin-document-assistant-cli/SKILL.md` 指导 Bash 执行 `status/parse/batch/deduplicate`。独立 Skill `packages/skills/wangbin-document-assistant/SKILL.md` 属于较早的 1.0.0 脚本方案，**不能将它与 1.2.0 运行能力混为同一实际安装链**。模型摘要必须有真实模型调用，CLI 只产出提取数据。

尚需在真实 WorkBuddy 中核实：私有 ZIP 解析根层级；CLI 实际执行位置/身份、Python 路径/版本、进程树和资源配额；Bash 授权；双 Skill 命名与触发；文件/文本传输与附件；卸载后虚拟环境/缓存处理。验收顺序见 `phase4-manual-acceptance.md`。