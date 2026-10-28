# Phase 0 — 本地仓库基线与只读复用审计

> 父任务最终收口：Phase 0审计完成，`PASS_WITH_RECORDED_LIMITATIONS`；独立发行环境真实回归145通过、0失败、5项Windows符号链接跳过，288个保护文件复算无变化。最终命令、首轮144通过/1失败/5跳过及未关闭安全/平台风险见 `../../reports/solar-pv/phase0-acceptance.md` 和 `phase0-protection-verification.json`。下面“待父任务整合”属于子审计采样时的历史状态，不覆盖此收口结论；光伏引擎/四文件仍未实现。

## 0. 结论与证据等级

- 审计日期：2026-10-28（UTC+08:00）；文件哈希采集时间见 `00-protected-artifacts.json.captured_at`。
- 工作树：`F:/ideaWorkSpace/wangbin-workbuddy`；分支 `main`；HEAD `c9b73291200e904a875ec2e2642f7492bd311036`。
- **本地只读审计已形成三份新文档；不代表完整 Phase 0 总门禁通过。** 本子任务不运行测试、不打包、不改旧文件、不提交，不执行 pull/reset/checkout/push/上传/部署。完整测试证据、当期官方文档快照及整合后的保护哈希由父代理收口。
- 可复用的是现有产品台账、按产品隔离的 CLI/候选打包机制、严格校验器、有限附件读取与证据表达模式；**没有据此发现已实现光伏资源/工程/项目财务计算、18章报告生成、PDF 渲染或四文件一致性引擎**。
- `services/document-engine/` 是附件文本提取和 XLSX 检查/去重服务，**不是光伏报告生成器、财务引擎或 OS 安全沙箱**。`tooling/financial_xlsx.py` 只把一个明确选择的 XLSX 工作表转成 CSV，不计算 NPV/IRR/LCOE，也不输出财务模型工作簿。
- 下面的“已有测试”均指已阅读测试源码/历史报告，不能解释成本子代理执行通过。源码审查发现均是静态证据；没有执行利用验证，也不声称完成渗透测试。

## 1. 仓库与远端关系

| 检查 | 真实结果 | 边界 |
|---|---|---|
| 首条 `git status --short` | 无输出，审计开始时干净 | 只证明采样时刻；最终工作区由父代理再读 |
| `git branch --show-current` | `main` | 未切换分支 |
| `git rev-parse HEAD` | `c9b73291200e904a875ec2e2642f7492bd311036` | 本地真实读回 |
| `git log -1` | `c9b7329 fix: align financial skill calculations and claims` | 未作提交 |
| 父代理 `git ls-remote main` | `5407d86b990633753ae577a9e799640da93f4c54` | 父代理共享实测；本子代理未重复联网 |
| `git merge-base --is-ancestor 5407d86... HEAD` | 退出码 0 | 本地对象确认远端采样 SHA 是祖先 |
| `git rev-list --count 5407d86b990633753ae577a9e799640da93f4c54..HEAD` | `1` | 本地领先一个提交，不能说与远端完全一致 |
| `git diff --stat 5407d86..HEAD` | 28 files changed, 525 insertions(+), 179 deletions(-) | 涉及四财务产品、测试、catalog 与报告；不可 pull/reset 抹去 |
| 仓库/父目录及仓库内部 `AGENTS.md` | 本轮路径检查未发现 | 不推断用户家目录其他配置 |

本轮新文件仅为 `docs/solar-pv/00-repo-audit.md`、`00-reuse-matrix.md`、`00-protected-artifacts.json`。父代理其他并行文档不在本子任务写权限内。

## 2. 源码审阅范围与入口证据

全部行号锚定上述 HEAD 的真实文件；详细函数级复用/禁止复用表见 `00-reuse-matrix.md`。

| 实际阅读文件 | 关键定义/行为 | 结论 |
|---|---|---|
| `tooling/product_factory.py:89,93,171,189` | catalog 读取、校验、查找、按类型初始化；检查名称/源码目录/候选冲突 | 延续现有工厂，不另建注册数据库；初始化不等于成品 |
| `tooling/product_factory.py:268,296,340` | 成员白名单、产品校验、登记测试路径的 pytest 子进程 | 可复用产品隔离；`test` 会真实执行测试，本轮未调用 |
| `tooling/product_factory.py:367,397,463` | 追加版本、内存快照确定性 ZIP、源码/归档/manifest/hash 复核 | 不覆盖旧版本/旧候选；历史包不能拿新源码复验 |
| `tooling/product_factory.py:494,519,552,603` | 版本指标、组合报告、许可/依赖独立门禁、release-check | UNKNOWN 不转 0；本地通过不升级平台门禁；release-check 会跑测试 |
| `tooling/product_factory.py:643,729,773` | 归档目录/hash 盘点，组合清单，写 `reports/workbuddy-upload-list.md` | `upload-list` 不上传，但**会写旧报告**，本轮禁止执行 |
| `tooling/products.py:12` | 产品级 CLI；`main` 分派 validate/test/package/verify/register-version/record 等 | 优先保留现有入口；不要把命令都当只读 |
| `products/catalog.json:2`、`products/metrics.json:3` | 真实产品/历史版本与经营指标 | 保留原始状态和缺数；本轮只读与哈希 |
| `tooling/validators/project_validator.py:34,60,88,144` | Skill/Expert/Connector 基础结构检查与全项目扫描 | 通用 Expert 检查比产品严格校验弱，不能替代后者 |
| `tooling/expert_rules.py:16` | prompt-only Expert 的资产、身份、双语字段、头像、外部依赖限制 | 保留旧规则；不是平台全部可选能力的规范全集 |
| `tooling/generators.py:10` | Skill 目录与元数据骨架 | 只复用结构，不把默认“处理文档”文案当光伏能力 |
| `packages/skills/wangbin-tender-analyzer/scripts/analyze_tender.py:65,200,374,399` | 限长脱敏引文/文本行号、保守提取、1 MiB UTF-8 TXT/MD CLI | 借鉴证据与缺失状态；不复制招标资格/评分业务 |
| `packages/skills/wangbin-tender-analyzer/SKILL.md:22,26,41,50,64`、`templates/tender-checklist.md:3` | 输入/平台/页码/脱敏边界 | 文案与脚本保持一致；脱敏摘录不是原件证明 |
| `packages/experts/wangbin-software-consultant/agents/wangbin-software-consultant.md:14,18,32,42,46` | 当前会话状态、每轮至多三问、预算口径、仅 Markdown 交付及隐私 | 只借鉴分阶段交互与假设/待确认表达；不能移植成本规则 |
| `packages/experts/wangbin-software-consultant/README.md:3,15,17,29`、`LICENSE:1` | 无外部依赖的 prompt-only 候选；独立 MIT 范围；测试不入包 | 严格保护；不改成光伏专家、不改许可 |
| `packages/experts/wangbin-expert-template/agents/wangbin-document-expert.md:11` | 模板本身有 `skills` 预加载列表 | 与 prompt-only strict validator 不同；模板不等于已发布成品 |
| `services/document-engine/src/wangbin_document_engine/` 下全部 Python 源码 | engine/security/process_runner/resource_slots/adapter/models/errors/metadata/spreadsheets/serialization/API | 已逐一阅读生产源码；不审 build/lib 或 pycache 作为源码 |
| `services/document-engine/src/wangbin_document_cli/main.py:19,41,62`、service `pyproject.toml:6` | 发行元数据健康检查、CLI parse/batch/deduplicate 与独立 1.2.0 发行契约 | 仅源码可 import 不足以通过 CLI doctor/status |
| `tooling/financial_xlsx.py:36,58,67,85,116,185` | 宏/公式拒绝、全工作簿扫描、明确 sheet、CSV 发布和脱敏错误 | 仅安全读取思路可有条件复用；非投资测算/报告输出 |
| `tooling/cli.py:31`、`tooling/release_check.py:21`、`tooling/packager.py:22`、`tooling/phase5_expert_packager.py:34` | 旧 CLI 固定产物/报告路径，旧 Expert 打包器可直接覆盖同名 ZIP | 保留兼容但严禁在本次只读审计里运行 |
| `tooling/validators/zip_validator.py:20`、`tooling/similarity.py:26,84,123` | 旧 ZIP 检查与内部 AST/输入输出相似度 | ZIP 路径判断有静态缺陷；相似度不是平台合规阈值 |

财务四产品的业务分析脚本本轮只做文件保护与 AST 位置盘点，不作为光伏计算复用候选；已阅读其四套专项测试和独立许可，不声称完成这些业务代码的新一轮数值审计。其他旧 docs/reports 通过保护哈希保全；下节列出的文档已阅读全文，其余不伪称逐份语义审查。

## 3. 测试与文档证据：历史、当前、未执行分开

### 3.1 实际阅读的测试

| 文件 | 定义行号与覆盖范围 | 对光伏的作用/缺口 |
|---|---|---|
| `tests/test_product_factory.py:38,107,124,134,176,242,253,265,279,292,312` | 登记、碰撞、确定性、篡改、隐私文件、未知指标、门禁、版本、路径、非有限值 | 复用隔离 tmp_path 模式；236 行测试把产品总数硬编码为 10，未来增量注册必须有意识调整预期，不是本轮改动 |
| `tests/test_tender_analyzer.py:30,76,104,121,141,203,230,248,271` | 确定性样例、缺数、错误隐私、限长脱敏、日期冲突、逐项证据 | 可借鉴真实脚本/expected 断言；不证明工程计算正确 |
| `tests/test_financial_xlsx.py:32,59,73,91,109,127,139,164` | 真实 XLSX 保序保重、公式/宏/容器拒绝、空输入/路径/CLI 隐私 | 不覆盖报告工作簿生成、公式重算缓存或 PDF |
| `tests/test_document_engine_real_formats.py:25,31,36,44,52` | 七种真实夹具的文本标记、Markdown 标题、空/损坏、中文文件名 | 是提取测试，不是布局/页码保真或报告渲染 |
| `tests/test_batch_processing.py:10,18` | 单文件失败不拖垮批次、数量限制 | 不证明跨任务 OS 隔离 |
| `tests/test_security.py:10,18,25,32` | 路径越界、字节/ZIP 限制、symlink | Windows symlink 能力可能跳过；不是恶意解析器沙箱测试 |
| `tests/test_spreadsheets.py:12,20,34,41` | 检查/去重后可重开、注入前缀文本化、输出隔离 | 不是光伏测算工作簿或全功能财务 Excel |
| `tests/test_phase3_security_limits.py:23,34,48,55,65,71,82,101` | 快照清理、两槽、行/格/字节、无覆盖发布、超时直接子进程回收 | 不覆盖全部后代进程、OS 低权限和加载/保存硬限额 |
| `tests/test_tooling.py:15,20,27` | 真实结构和旧 CLI、临时 ZIP | CLI validate 会改 `reports/validate.*`；父代理回归需保护/恢复历史报告 |
| `tests/test_receivable_analyzer.py:26,50,61,79,97,114,121` | 币种/精度、客户聚合优先级、坏行、样例和物理行号 | 业务边界不可移植为光伏现金流 |
| `tests/test_inventory_analyzer.py:76,107,117,134,158,174,187,204,217,228,236` | 缺失/已知零/无库存/不完整期间区别及输入安全 | 可借鉴状态建模，不复用周转/库存决策 |
| `tests/test_purchase_analyzer.py:49,90,103,118,135,151,169,178,197,208` | 同供应商变化与跨供应商价差、可比税/币种/规格、坏输入 | 不将采购旧价当光伏现价 |
| `tests/test_sales_analyzer.py:52,94,115,127,143,157,171,186,193` | 可比期间、缺数、公式、CLI、市场文案能力一致性 | 不将销售收入模型当光伏分时售电/PPA 模型 |
| `packages/experts/wangbin-software-consultant/tests/test_expert_candidate.py:19,31,42,53,66` | strict 元数据、旧 ZIP、固定报价算术、静态 scenarios 字段 | scenarios 完整不等于真实模型/WorkBuddy 对话通过；根 pytest `testpaths=["tests"]` 不默认收集包内 Expert 测试 |
| `tests/conftest.py:10`、`tests/generate_fixtures.py:17,40` | 缺 sample.pdf 时生成夹具；PDF/DOCX/XLSX/PPTX 虚构输入生成 | 测试收集/运行也可能写夹具；生成测试 PDF 不等于生产报告 PDF 渲染器 |

### 3.2 已阅读的历史文档/报告与矛盾处理

- `README.md:19,39,61,63`：工具包 1.0.0 与独立 CLI 1.2.0 分开；旧命令写报告/dist；资源限额不是沙箱；历史平台/分发仍阻断。
- `docs/product-factory.md:24,41,45,47,49`：版本不可覆盖、招标文本边界、平台与本地分离、upload-list 写报告、相似度只供人工审阅。
- `docs/architecture.md:23,32,36`、`docs/security-guide.md:5,14,22,29`：仅旧架构/安全意图，不覆盖后续威胁模型，也不是本轮当前官方确认。
- `docs/workbuddy-platform-spec.md:3,27,88,96`：2026-10-26 历史研究记录；其中 Agent `skills` 已被记为可选，但 prompt-only validator 有意收窄。不能用旧文档宣称当前官方禁止组合能力。
- `reports/phase4-threat-model.md:7-16`：Windows 硬限额、Excel 主进程、后代回收、目录竞态、同用户权限、解析库漏洞、并发与隐私均保留风险；明确 `SECURITY_PASS=BLOCKED`。
- `reports/phase6-platform-acceptance.md:103-131`、`reports/phase7-release-check.md:113-152`、`reports/phase8-platform-name-fix.md:119-170`：同一 Expert 1.0.0 的历史报告曾记录不同 ZIP 哈希；**按现存文件重新实测的 `577f3089…` 为本轮保护基线**，旧报告保留，不涂改历史，也不伪造旧哈希对应文件仍存在。Phase 8 记录的名称超长反馈仅代表历史错误，不代表修正后已平台安装/审核。
- `reports/financial-skills-phase9-release-candidate.md:18-25`：历史记录全仓库 `109 passed, 5 skipped`、四产品专项和归档本地 PASS；许可/平台仍阻断。它不等于本轮 HEAD 的当前回归。
- `reports/workbuddy-proprietary-license-review.md:3,25-35,41-49`：四经营 Skill 私有声明和账号生效协议未核验；不得用根 MIT 元数据重新授权它们。

### 3.3 当前测试与官方信息（父代理通报，待最终整合）

本子代理**没有执行任何测试、产品 CLI、打包或 release-check**。父代理在 2026-10-28 通报：首轮回归 `144 passed, 1 failed, 5 skipped`，失败源于缺少 `wangbin-document-cli` 发行元数据；随后在 scratch venv 安装既有归档 wheel + requirements，复跑退出码 0。**最终通过/跳过计数与完整命令日志尚待父代理整合，不用历史 109 或首轮 144 冒充最终数。**

根因在当前源码可见：`services/document-engine/src/wangbin_document_cli/main.py:16-34` 使用 `importlib.metadata.version` 检查发行包和固定依赖版本；仅把引擎源码加入 PYTHONPATH 不建立发行元数据。该说明不等于本子代理重复验证父代理结果。

父代理 2026-10-28 官方直连通报：当前 Expert 页面 plugin.json 可选 `skills` 技能路径；Agent frontmatter 可选 `skills` 预加载列表；“内置 MCP 与连接器依赖”章包含 `dependencies.mcpServers` / `dependencies.connectors` 或根 `.mcp.json`。这与仓库**专用于 prompt-only** 的 `tooling/expert_rules.py:61-62` 收窄策略有差异，不是“官方不支持”。本轮不改旧规则；Phase 7 应新增隔离的校验/产品 profile（此处不是修改 Hermes 运行配置），再做真实平台安装/调用验证。普通 Skill 的依赖自动安装仍未确认。正式引用、页面快照、获取时间与最终官方能力风险报告由父代理补齐；本子代理不假装已自行联网复核，也不宣称可选字段已证明端到端调用链可用。

## 4. 既有产品、模板、许可与指标保护

机器清单 `00-protected-artifacts.json` 保存 **288 个既有文件**的路径、大小与 SHA-256；其中既有 `packages/` 发布/模板文件 66 个，`dist/` 全部文件 72 个。同时保全 Git 跟踪的旧源码、测试、文档和报告。分组可重叠，分组数量不能直接相加为总数。缓存、venv、build/egg-info 和用户运行输出不作为候选发布资产；没有读取凭据文件内容。清单不包含自身或本轮新文档，避免自引用哈希。

模板实际目录：`packages/experts/wangbin-expert-template`、`packages/connectors/wangbin-cli-connector-template`、`packages/connectors/wangbin-mcp-connector-template`。保留模板所有已有文件的逐文件哈希，不把模板初始化为可发布业务产品。

许可审查边界：

1. `packages/experts/wangbin-software-consultant/LICENSE` 与 `services/document-engine/LICENSE` 各自是 MIT 文本；Expert README 限定随包资产范围。
2. 四经营分析 Skill 的独立 LICENSE 是保留版权声明，非 MIT；catalog 各自 `license_policy.type=PROPRIETARY`、`platform_agreement=NOT_VERIFIED`。不替换、不撤销、不从目录内其他 MIT 声明推断它们可开源。
3. 根 `pyproject.toml:12` 的 MIT 是工程元数据，不自动覆盖所有独立产品；根目录本轮未发现独立 `LICENSE` 文件。招标 Skill 的现有文件/ZIP 中没有独立 LICENSE，不能据此补写授权或声称许可门禁 PASS。
4. `products/metrics.json:8,10,12,13` 仍保存四财务产品 0.1.2 的未知指标，catalog 已选 0.1.3；这表示 active 版指标没有对应观测数据，不是 0，更不是可移用旧版数据。`portfolio_report:524` 按当前版本匹配，缺项保持 UNKNOWN。

关键保护哈希（完整逐文件清单以 JSON 为准）：

| 文件 | 本轮 SHA-256 |
|---|---|
| `products/catalog.json` | `78222e31dfa1a3742132474b2cf3014a5a0cf43ddbe74cd48ba28bde8fd5b60e` |
| `products/metrics.json` | `60e46f57cecba114e3793b4097315e3e00b18fa74507a70b540303afea514a67` |
| `tooling/product_factory.py` | `3f5f70810accad6d573c079cda3fd409789e5c3e08cf1e02072b082c78055828` |
| `tooling/products.py` | `e6ae9670d8323a129cdf8cafa83f2853b3973bcb3932dc3d13772b17d0cecdd6` |
| `tooling/expert_rules.py` | `b7d77207c3845ffcb976d15af98242e29db8e1fb6ff4561487957143a6b259d5` |
| `tooling/financial_xlsx.py` | `19837d4de29c0dd21ac8c4f28ec30285302ce21946aa9b2cf6fbfdb5b87ff252` |
| `services/document-engine/LICENSE` | `506377ce49d410995b6e7d11b9cd5fd6ea5d3b560a193f779b32e337367937a6` |
| `packages/experts/wangbin-software-consultant/LICENSE` | `506377ce49d410995b6e7d11b9cd5fd6ea5d3b560a193f779b32e337367937a6` |
| `packages/skills/wangbin-receivable-analyzer/LICENSE` | `47d51945aa6bd882aff7f2631ea4a8776b3eae2e60f05e232e4266aef29df93e` |
| `packages/skills/wangbin-inventory-analyzer/LICENSE` | `47d51945aa6bd882aff7f2631ea4a8776b3eae2e60f05e232e4266aef29df93e` |
| `packages/skills/wangbin-purchase-analyzer/LICENSE` | `47d51945aa6bd882aff7f2631ea4a8776b3eae2e60f05e232e4266aef29df93e` |
| `packages/skills/wangbin-sales-analyzer/LICENSE` | `47d51945aa6bd882aff7f2631ea4a8776b3eae2e60f05e232e4266aef29df93e` |

## 5. 全部历史 dist ZIP/wheel 与 catalog 候选盘点

本次直接枚举磁盘 `dist/`，未依赖 git ls-files（dist 被忽略），共 **25 个归档：23 ZIP + 2 wheel**，配套已有 sidecar 25 个均与本轮实测 SHA-256 一致。清单只读中央目录和原始文件哈希；**没有重新打包、解包执行或运行 CRC/测试**，所以不把成员目录可读等价为归档全内容/运行完整性 PASS。

catalog 有 10 产品、22 版本记录：18 条登记哈希与现存文件一致；4 条 UNKNOWN 包含文档 Skill/Connector 两个已有候选的登记 SHA 未填及两个 BACKLOG 产品未知候选。没有发现已登记 SHA 与实物不一致。JSON 同时列出每条历史版本/候选，不只列 active。以下为 active 概览：

| 产品 ID | 类型 | active 版 | 台账产品/审核状态 | 候选存在/登记哈希比对 |
|---|---|---|---|---|
| `wangbin-document-assistant` | Skill | 1.0.0 | DEVELOPING / NOT_TESTED | 存在；UNKNOWN |
| `wangbin-document-cli` | Connector | 1.2.0 | DEVELOPING / BLOCKED | 存在；UNKNOWN |
| `wangbin-software-consultant` | Expert | 1.0.0 | SUBMITTED / USER_REPORTED_SUBMITTED | 存在；PASS |
| `wangbin-tender-analyzer` | Skill | 0.1.0 | DEVELOPING / NOT_TESTED | 存在；PASS |
| `wangbin-receivable-analyzer` | Skill | 0.1.3 | TESTED / NOT_TESTED | 存在；PASS |
| `wangbin-requirement-impact` | Skill | 0.1.0 | BACKLOG / NOT_TESTED | MISSING / UNKNOWN |
| `wangbin-inventory-analyzer` | Skill | 0.1.3 | TESTED / NOT_TESTED | 存在；PASS |
| `wangbin-industry-research` | Skill | 0.1.0 | BACKLOG / NOT_TESTED | MISSING / UNKNOWN |
| `wangbin-purchase-analyzer` | Skill | 0.1.3 | TESTED / NOT_TESTED | 存在；PASS |
| `wangbin-sales-analyzer` | Skill | 0.1.3 | TESTED / NOT_TESTED | 存在；PASS |

`wangbin-document-assistant-cli` 目录是文档 CLI 工作流说明来源，未被单独登记为新产品；不得只看目录数量就宣称产品数量。`wangbin-requirement-impact` 和 `wangbin-industry-research` 的源目录实测不存在，只是 BACKLOG。

以下全部路径相对 `F:/ideaWorkSpace/wangbin-workbuddy`；JSON 的 `archives[].absolute_path` 提供完整 Windows 绝对路径。**全部为既有受保护产物，历史版本不是新的上传推荐。**

| 归档 | 字节 | 实测 SHA-256 | 台账归属 |
|---|---:|---|---|
| `dist/wangbin-document-assistant-1.0.0-candidate.zip` | 5877 | `12544dbd203c3bed5cf6f0094ffc752b17d3fcc852377a6ff09113cb31b5c5b3` | 已登记 |
| `dist/wangbin-document-assistant-1.1.0-skill-candidate.zip` | 2946 | `c96a8644047146c595a2267769aadf8b7e6d6532615be4343d34014efb33678c` | 未登记历史产物 |
| `dist/wangbin-document-assistant-1.2.0-skill-candidate.zip` | 3332 | `38133ee51a91db38091032c60ecb4b84db9e3c63e9953307575b13b7a649de2f` | 未登记历史产物 |
| `dist/wangbin-document-cli-1.1.0-connector-candidate.zip` | 4451 | `e04486c39f804307b98d33eabe5a477c6336910708c260ead8703b7fee305fbf` | 未登记历史产物 |
| `dist/wangbin-document-cli-1.2.0-connector-candidate.zip` | 4864 | `be64b3b619382cbc74686fef6bd64a402f15f380487bde61e41620df66feb0e7` | 已登记 |
| `dist/wangbin-inventory-analyzer-0.1.0-skill-candidate.zip` | 11877 | `b2b7d51998243d819d11237aa2652c486640133bda66a3e75fd6736691b09fdf` | 已登记 |
| `dist/wangbin-inventory-analyzer-0.1.1-skill-candidate.zip` | 12748 | `1cdd808458ae57780e9b8cad77e26eb784683e3e6772efce1a0980d34ecbe686` | 已登记 |
| `dist/wangbin-inventory-analyzer-0.1.2-skill-candidate.zip` | 12535 | `f2e720d7c544bb4a4d24aa4f01c21a58826965a67f3195c5e8d9020caaeee62c` | 已登记 |
| `dist/wangbin-inventory-analyzer-0.1.3-skill-candidate.zip` | 13281 | `b99e839de10e7bd8533b2387a99b38c48cdf9360f14919608b35ae8694be17a0` | 已登记 |
| `dist/wangbin-purchase-analyzer-0.1.0-skill-candidate.zip` | 10865 | `00aaac8d7104151c1ea06e4f709234b94145ea4fca4972d3b866540814453571` | 已登记 |
| `dist/wangbin-purchase-analyzer-0.1.1-skill-candidate.zip` | 11734 | `673f076b51d760c3eaf8d6ad9c30e254846c60a4a23705d297635023e88814e5` | 已登记 |
| `dist/wangbin-purchase-analyzer-0.1.2-skill-candidate.zip` | 11517 | `1e0de940a4198a3ea92d86b7fd0a84b999620247e43e74dd76315b4e75621dd4` | 已登记 |
| `dist/wangbin-purchase-analyzer-0.1.3-skill-candidate.zip` | 12071 | `37376d189e9b97847e2a6d9943c171ef1c05f225d93234680c54853e641630ec` | 已登记 |
| `dist/wangbin-receivable-analyzer-0.1.0-skill-candidate.zip` | 6812 | `229b302ae5109639e3379be61cd259549197f9b22e90a8ffbcf43539dfec1929` | 已登记 |
| `dist/wangbin-receivable-analyzer-0.1.1-skill-candidate.zip` | 7691 | `1fc44aa4f7d8790ab6b3856977d04abd8906f72fb25587c108fb94f60cd7792e` | 已登记 |
| `dist/wangbin-receivable-analyzer-0.1.2-skill-candidate.zip` | 7470 | `3165ecc4d2ce435ac3ed263dc52d4585a89ac46c5b66324b995878d5a26e897f` | 已登记 |
| `dist/wangbin-receivable-analyzer-0.1.3-skill-candidate.zip` | 7777 | `d4177a8e5657061fd3630780cee88b07e3524c144e0c3bec8be0dfde2278e171` | 已登记 |
| `dist/wangbin-sales-analyzer-0.1.0-skill-candidate.zip` | 9250 | `571664ec2652a917ac1ea06a3b59b97e271d725f03843529228935b910cf62ab` | 已登记 |
| `dist/wangbin-sales-analyzer-0.1.1-skill-candidate.zip` | 10109 | `52c7ee38efe9d46a87ebd89d3f9fd13060d16bebd1ca6e6c480d53ebe883c40d` | 已登记 |
| `dist/wangbin-sales-analyzer-0.1.2-skill-candidate.zip` | 9889 | `34378ecb2159f8562f71b5c89074e449556c72f74f814e5fc37291f3107f1425` | 已登记 |
| `dist/wangbin-sales-analyzer-0.1.3-skill-candidate.zip` | 10033 | `60b3d66cb0a5f88d5499f1ab875cd579de951633e691f18f94b58bdd74af2d3d` | 已登记 |
| `dist/wangbin-software-consultant-1.0.0-expert-candidate.zip` | 13567 | `577f3089d2f4707178f44ba1e5c395a99853bb9558f3e8c0e752a0e6ba2e30de` | 已登记 |
| `dist/wangbin-tender-analyzer-0.1.0-skill-candidate.zip` | 12580 | `2e68809033301c97b02ec7c7fd59f7b477fcd2f1f86d515d69b5fc7b20146bc7` | 已登记 |
| `dist/wangbin_document_cli-1.1.0-py3-none-any.whl` | 15287 | `51071474a8668d5c4ba153896a5cde4d4233881f6042d7b16f305259fda702f9` | 未登记历史产物 |
| `dist/wangbin_document_cli-1.2.0-py3-none-any.whl` | 20970 | `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa` | 未登记历史产物 |

五个未登记历史归档是文档 Skill 1.1.0/1.2.0、文档 Connector 1.1.0、CLI wheel 1.1.0/1.2.0。不能因为未在 catalog 中就删除；也不在本轮擅自注册、修改旧候选路径或补写台账 SHA。

## 6. 安全边界与阻断清单

| ID | 静态证据/风险 | 本轮处理与后续门禁 |
|---|---|---|
| P0-S01 | `process_runner.py:38-53` Windows 直接返回，没有 CPU/内存 Job Object；69-108 只回收直接 multiprocessing 子进程 | 不宣称 OS 沙箱/进程树硬隔离；公开任意不可信附件解析保持 BLOCKED |
| P0-S02 | `engine.py:39-40` 注入 adapter 路由在主进程；`spreadsheets.py:31,77,130,193` XLSX 加载/保存/重开在主进程，165 起只在迭代检查 deadline | 不把 timeout 参数解释为覆盖所有阶段的硬中断；需要隔离、资源额度和实际压力验证 |
| P0-S03 | `security.py:43-102,111-126` 路径/链接/快照有限防护；同用户解析进程仍继承 OS 权限 | TOCTOU/祖先目录竞态不是已证明闭环；独占受控目录不等于沙箱 |
| P0-S04 | `financial_xlsx.py:131,134,140,151` 宏检查/inspect/扫描/输出分多次 source 快照；67-93 扫描没有自己调用 `_bounded_rows`，且 140/151 路由没有 hold_resource_slot | 不能直接面向恶意商业附件复用；先在新适配层统一受限快照和资源策略，再补专测；本轮不改旧源 |
| P0-S05 | `load_workbook(...keep_links=False)` 丢弃链接并非显式拒绝所有外链；泛用 SecurityPolicy 未逐项拒宏；`financial_xlsx` 才有额外宏拒绝 | 新光伏资料接入需要宏、外链、公式、ZIP bomb 的独立强门禁；不偷换“不执行”为“拒绝所有” |
| P0-S06 | `serialization.py:9-11,31,37,41-43` 可原样写 JSON/Markdown，单文件 Markdown 可含全文；CLI `main.py:98` 输出完整解析结果 | 禁止把结果默认写公共日志/报告；需分离授权用户输出与审计摘录、保留期/清理/附件 ID |
| P0-S07 | `tooling/validators/zip_validator.py:27` 使用 `"../" in name.split("/")`，而 `../x` 拆分元素为 `..` 和 `x`，不能正确识别该穿越段；没有展开预算 | 静态缺陷，未执行攻击测试；禁止拿它作为新光伏归档/用户附件安全边界，未来单独修复与恶意用例门禁 |
| P0-S08 | `product_factory.py:40-55` 检查 symlink，没有 engine `_has_link_component` 的 junction 特判；文件打包白名单不是 OS 权限隔离 | 不把工厂 `_safe_relative` 宣称 Windows 任意联接安全；新 profile 需单独验证 Windows 路径变体 |
| P0-S09 | `product_factory.py:603-635` 将平台安装/对话/发布独立阻断；旧 `release_check.py:42,46` 却用文档存在/本地校验与测试来标规范或安全 PASS | 光伏不能沿用旧 aggregate 的过度门禁含义；将文档/数值/来源/运行时/安装调用/审核分别判断 |
| P0-S10 | `product_factory.py:268-293` 现有白名单未含 DOCX/PDF/XLSX；新报告四件不是现有 Skill 静态成员合同 | 产物输出与发布包职责分离；不在本轮扩大老产品打包面，也不在包中放客户商业附件 |
| P0-S11 | `product_factory.py:431-459` 拒覆盖不同内容、单文件原子替换，但三归档文件与 catalog 不是跨文件事务 | 不宣称断电/并发下四文件全有或全无；光伏四件套需要 canonical JSON、hash 一致性与事务发布新设计 |
| P0-S12 | strict Expert 第61行拒外部 skills/dependencies，与父代理当前官方可选能力存在策略差异 | **不是官方禁止组合能力**；不削弱旧 validator；Phase 7 新增隔离 profile 与平台实机验证；普通 Skill 依赖托管仍 UNKNOWN |
| P0-S13 | 引文只提供文本行号；提取器未提供可靠 PDF 页码/表格坐标或 OCR | 不能编造页码、将扫描件未识别当无要求；来源位置必须注明能力限制和待核实 |
| P0-S14 | 独立产品授权不同；外部气象/政策/工程报告尚未取得数据许可/实际站址证据 | 未核实来源 LICENSE=REQUIRES_REVIEW；不抓取商业资料、不上传客户商业附件、不默认远端模型获授权 |

## 7. 光伏新增缺口与下一阶段依赖

1. 不另建产品工厂、数据库或微服务；优先新增 `services/solar-pv-engine`、独立 Skill/Expert 目录、`tests/solar-pv` 和脱敏报告目录，是否建立目录由后续授权决定。本轮不生成代码骨架。
2. 新增 canonical calculation JSON、输入 Schema/单位/证据链、成熟度 L1/L2/L3 与缺数/冲突/假设状态；报告与计算不可互相反推迎合目标 IRR。
3. 新增屋顶与地面两个隔离 P0 模型，分别验证容量、资源/月度发电/逐年衰减、负荷同期匹配或全额售电、CAPEX/OPEX、税折旧、债务、项目/股东现金流及 IRR/NPV/LCOE/DSCR；旧应收/库存/采购/销售规则不适用。
4. 新增18章/附录、公式逐符号解释和双语词表、两 XLSX 与 DOCX/PDF 真实渲染。依赖存在不代表 PDF 转换器可用；不能用测试夹具生成函数伪装生产四件套。
5. P1 农光/渔光/光储与 P2 公共/户用/车棚BIPV/荒漠矿区保持独立分类/NOT_IMPLEMENTED，不借 P0 名称替换宣称覆盖。
6. 以父代理完整需求冻结、可执行验收矩阵、官方研究与本轮最终回归为 Phase 1/2 前置；数值、数据真实性、文档完整性、环境、WorkBuddy 调用、平台审核六门禁分别落证。

## 8. 本子任务验收状态

| 门禁 | 状态 | 证据/剩余事项 |
|---|---|---|
| REPO_IDENTITY_READ | PASS（本地采样） | main/HEAD/初始干净；相对父代理远端采样领先1提交 |
| SOURCE_REUSE_AUDIT | 完成只读审计文档 | 定义行号、实际功能、禁止边界见本文件与矩阵；不等于安全认证 |
| PROTECTED_BASELINE_CAPTURE | PASS（采集） | 288 文件、25归档、22 catalog 版本记录及 sidecars；JSON 真实 SHA-256 |
| POST_INTEGRATION_HASH_VERIFY | PENDING_PARENT_INTEGRATION | 父代理最后复算保护哈希；不得仅据写入成功宣称全仓库未变 |
| CURRENT_REGRESSION | PENDING_PARENT_INTEGRATION | 父代理隔离环境复跑 exit0，最终计数/命令/日志待整合；子代理未跑 |
| CURRENT_OFFICIAL_PLATFORM_EVIDENCE | PENDING_PARENT_INTEGRATION | 已接收父代理 Expert 可选能力通报；正式来源/快照由父代理整合 |
| SOLAR_PV_COMPUTATION_AND_FOUR_FILES | NOT_IMPLEMENTED | 本轮不生成 DOCX/PDF/XLSX，不把 Markdown 当四件套 |
| WORKBUDDY_INSTALL_RUNTIME_REVIEW | NOT_TESTED / BLOCKED | 没有上传/安装/真实调用/审核/发布动作 |
| LOCAL_COMMIT | NOT_RUN_BY_SUBAGENT | 本任务明确不 commit；最终 HEAD/提交权限由父代理完整任务收口 |
