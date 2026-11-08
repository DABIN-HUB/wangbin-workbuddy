# 全仓库产品开发任务与 QA 交接模板

> 适用于新建和既有 Expert、Skill、Connector、服务、工具及其 QA 工作；这是开发任务入口，不是用户运行时指令。权威规则只在根目录 `agent.md`，本文件不复制完整规则。

## 开始前（analyst / developer / quality / manager 均执行）

1. 在本次任务的实际工作树完整读取仓库根目录 `AGENTS.md`，由其定位并完整读取根目录 `agent.md`；再读取该产品的冻结合同、更严格本地规则与上一阶段真实门禁。找不到文件时停止 Git 写入和破坏性清理，报告阻断。
2. 记录产品 ID、任务范围、输入、受保护原件、预期输出、分支、HEAD、`git status --short --untracked-files=all`、验收命令及所有已有改动的归属。不得跨产品清理或覆盖其他 Agent 工作树。
3. 子任务/看板卡必须显式传递上述仓库路径、读取顺序、冻结合同和本模板，不把根目录 `AGENTS.md` 的存在误当作子目录工作树或 Bot 运行时已自动注入规则。

## 执行和交接

- **wb-analyst**：确认需求、批准的功能边界、冻结合同、真实输入与缺口；列出可验证门禁，不宣称独立 QA。
- **wb-developer**：按合同最小实现；运行受影响的合法测试与构建；生成当前有效交付物；核对输出身份与来源。测试 FAIL、超时、未执行须原样登记。
- **wb-quality**：独立读回测试退出码、受保护输入/Fixture、结果身份与哈希；检查临时文件清理、有效 dist 的 ZIP/manifest/LICENSE/SHA-256 和 Git 忽略、已跟踪废弃产物的普通删除记录、无无用 `??` 文件、许可证与平台门禁。仅以实际读回结果给 PASS；未装平台不写平台 PASS。
- **wb-manager**：核对独立 QA、分支与提交；已完成的可验证阶段显式暂存授权文件、检查 `git diff --cached --name-status` / `git diff --cached --check` 后本地 commit，读回 HEAD、暂存区、`git status --short --untracked-files=all`、`git diff --check`。不能因自动化任务已派发就视为完成。

## 最终 QA 必填证据

| 门禁 | 具体证据 |
| --- | --- |
| 产品合同/仓库入口 | `AGENTS.md` → `agent.md` → 产品冻结合同实际读取范围及冲突处理 |
| 测试与构建 | 命令、实际退出码、通过/失败/跳过/超时数量、环境和源码快照 |
| 文件卫生 | 本轮已跟踪无用文件净删除及 `git rm` 提交；未跟踪文件分类和清理；受保护输入未误删 |
| dist 候选 | 现行 ZIP、manifest、LICENSE、SHA-256 读回与 `git check-ignore -v`；不强制添加 dist 到 Git |
| 本地提交 | 仅显式暂存、提交 SHA、最终 HEAD、暂存区和 `git status --short --untracked-files=all` 原始结果 |
| 平台/发布 | 无真实安装与运行则 NOT_TESTED/BLOCKED；许可/人工签审各自独立，不自动升级 |

**边界**：不得自动 push、merge、上传 WorkBuddy、安装、审核、发布或启动未经批准的新阶段。无变更不制造空提交；失败阶段若需保留工作只能标为非发布 WIP。

## Hermes Dots 四 Bot 接入边界

本模板可由仓库内任务生成器与人工/看板任务描述引用；根目录 `AGENTS.md` 不会在任意子目录或仓库外 Bot 配置中自动继承。将上述“开始前”步骤分别注入 `wb-analyst`、`wb-developer`、`wb-quality`、`wb-manager` 的真实 Bot 开发者指令或看板任务模板，并在各 Bot 的独立工作树验证读入；需先定位实际 profile/提示词配置与运行入口。仓库文件接入本身不证明四 Bot 的外部配置已修改或运行强制生效。

当前本机四份角色提示位于 `C:/Users/wangbin/AppData/Local/hermes/profiles/{wb-analyst,wb-developer,wb-quality,wb-manager}/SOUL.md`，已分别增补本模板入口、根目录文件读取顺序和禁止自动 push 约束。它们不属于仓库 Git 提交；已有 Bot 会话是否重新加载、实际看板任务是否读入正确版本仍需独立运行时观察，不因文件修改而标 PASS。
