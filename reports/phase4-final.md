# Phase 4 最终结论 — 真实发布可行性与安全边界

2026-10-26；仓库 `F:/ideaWorkSpace/wangbin-workbuddy`。本阶段只读检查官方文档、源码/历史验收、公开分发接口及本地三件候选哈希，新增七份分析/人工手册；**未改生产代码、CLI、Skill、Connector、版本和既有测试；未重新构建任何产物**。未提交 Git、上传 WorkBuddy、部署服务、公开发布 PyPI/Release、做收费设置或触发公开审核。Phase 2/3 报告原样保留，Phase 3 原有成功/跳过项不被改写为新验收。

## 六项决策

1. **推荐架构**：现有 1.2.0 的 A（普通本地解析子进程）只保留受控研发用途；公开不可信文件处理的目标推荐 **B：低权限 OS 级本地隔离**，覆盖解析与 Excel 主进程、CPU/内存、进程树、可访问目录和网络；前提是 WorkBuddy 实际允许并通过 Windows/Linux/macOS 验证。若不允许再另行评估 C 远程 MCP/容器服务及隐私/持续成本，不在本轮部署。详见 `phase4-runtime-decision.md`。
2. **安全是否阻断**：是，`SECURITY_PASS=BLOCKED`。Windows 缺硬资源限额、XLSX `load_workbook`/保存仍在主进程、后代回收、敌对目录 TOCTOU、同用户文件权限、解析库漏洞和跨用户并发未闭环；venv 非安全沙箱，JSON IPC 仅关闭 pickle 通路。详见 `phase4-threat-model.md`。
3. **最小可发布集合**：当前 1.2.0 文件解析/去重 CLI **不存在已被验证安全且可公开分发的子集**；本轮未在代码中禁用格式，故不声称“仅 TXT/Markdown 已可发布”。现有独立 Skill 1.0.0 和专家模板仍含解析脚本/文档处理承诺，也不能直接冒充纯提示词产品。唯一可先评估的更简单首品是**另行获授权、无解析器/脚本/CLI 依赖、只处理用户粘贴文字的纯 Skill 或专家**，仍需真实私有平台验收和内容审核；不属于本轮已交付可上架资产。见 `phase4-mvp-scope.md`。
4. **真实安装尚缺**：PyPI 包级及 1.2.0 版本接口 HTTP 404，仓库 GitHub Releases API 空数组；无可信公开 wheel URL、无 WorkBuddy 允许来源/普通用户自动安装证据。官方文档说明托管 Python/venv 及 CLI 配置，并**没有**为当前产品证明业务命令位置、权限和安全隔离。macOS 未实测，WorkBuddy 私有上传、Skill→CLI、模型摘要、XLSX 实际下载均无记录。详见 `phase4-platform-capabilities.md` 与 `phase4-distribution.md`。
5. **本人需执行**：决定是否暂停此 CLI 公开方案并选 B/另行许可的 C 或纯文字首品；在自行管理的账号内确认个人认证/CLI 发布资格及**真实非公开草稿入口**；审阅安全设计、许可/NOTICE、目标平台隐私边界和 macOS 真机结果；在另行明确授权后由本人建立可信不可变 wheel 分发并验证下载哈希/依赖；仅在真正私有测试环境、无敏样本、符合前述安全前提时按 `phase4-manual-acceptance.md` 逐页验证。若只能公开提审，**到此停止该步骤**。勿在聊天提供账号凭据。
6. **是否有更简单的先行产品**：有**潜在**方向——纯文字事实/待办整理 Skill/专家，无文件解析、无外部账号、无 CLI 安装；但当前仓库没有合规的现成包，须单独制作和审查，不能宣布已可上架、已发生模型摘要或已完成平台验收。

## 门禁（限定证据范围）

| 门禁 | 结论 | 依据/边界 |
|---|---|---|
| LOCAL_WHEEL_INSTALL | PASS（沿用 Phase 3 实测） | Windows 3.12/Linux 3.12.15 本地 wheel 与依赖；并非平台安装。 |
| SOURCE_REBUILD_PASS | PASS（沿用 Phase 3） | Phase 3 无 dist 源码重建；Phase 4 未重新构建。 |
| PACKAGE_VALIDATION_PASS | PASS（仅包结构和本地哈希） | Phase 4 再次在 `dist/` 核对三个 sidecar `OK`；不代表平台 ZIP 解析。 |
| WINDOWS_RUNTIME_PASS | PASS（Phase 3 功能范围） | 31 passed/1 skipped，symlink 权限测试未实测。 |
| LINUX_RUNTIME_PASS | PASS（Phase 3 功能范围） | 32 passed，16 项 wheel 验收；不替代 macOS。 |
| MACOS_RUNTIME_PASS | NOT_TESTED | 无真机/CI 实际运行记录。 |
| SECURITY_PASS | BLOCKED | 存在上述公开不可信输入发布阻断。 |
| DISTRIBUTION_SOURCE_PASS | BLOCKED | 没有 1.2.0 公开可信 wheel；不将本地文件路径当正式来源。 |
| CONNECTOR_SKILL_E2E | BLOCKED | 只有包结构和静态链路；平台真实触发未验。 |
| WORKBUDDY_INSTALL_PASS | BLOCKED | 未获非公开授权入口，未真实安装。 |
| WORKBUDDY_E2E_PASS | BLOCKED | 无实际平台 PDF、XLSX、模型与下载验收。 |
| PUBLISH_READY | BLOCKED | 安全、分发、macOS 与平台端到端均缺。 |

**当前唯一三件 1.2.0 本地候选 SHA-256**（未重建，Phase 4 `sha256sum -c` 再次 OK）：wheel `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa`；Skill ZIP `38133ee51a91db38091032c60ecb4b84db9e3c63e9953307575b13b7a649de2f`；Connector ZIP `be64b3b619382cbc74686fef6bd64a402f15f380487bde61e41620df66feb0e7`。若任一重新构建，必须重算并更新清单，不得引用此表作为新产物。

文档依据：[Connector](https://open.workbuddy.cn/docs/connector)、[Skill](https://open.workbuddy.cn/docs/skill)、[入驻](https://open.workbuddy.cn/docs/onboarding)、[公约](https://open.workbuddy.cn/docs/developer-agreement)、[专家](https://open.workbuddy.cn/docs/expert)。公开页面说明≠账号权限/实际执行证据；详细判断见本阶段其他六份报告。报告到此停止，保持全部未实测/阻断状态。