# 六阶段 Kanban 模板
所有卡：board=wb-skill-factory，tenant/product_id=产品 ID，workspace=产品 worktree 的绝对路径，`idempotency_key=产品ID:阶段`，max_runtime=30m（复杂阶段需人工调整），max_retries=1，local-only；每卡写明验收条件，下一阶段依赖上一阶段。
每个产品必须另有一个 `wb-manager` T05 收尾根卡（幂等键 `产品ID:T05`），并把所有必要的开发、QA、修复、复验、打包和推送卡直接或间接依赖到该收尾卡；收尾卡只能核对真实物证、保存报告和汇报，不实现业务代码。
创建后不得依赖用户再次提醒：Ready 由 Gateway Dispatcher 自动领取，Todo 在父任务 Done 后自动晋级，Blocked 通过 `auto_subscribe_on_create`/`notify_in_gateway` 发送 terminal-event；经理收到事件后必须读取卡片、核验失败证据，按 `产品ID:fix:轮次` 幂等创建独立修复卡，并在最多两轮后保持 BLOCKED。
- T00 wb-developer：检查 ID/路径/分支/登记与基线，安全创建独立 worktree，报告可写性与原始状态。
- T01 wb-analyst：交付 requirements.md、input-output-contract.md、acceptance-cases.md，冻结 MVP；依赖 T00。
- T02 wb-developer：实现业务代码、SKILL.md、示例及专项测试，真实运行并本地 commit；必要检查通过后允许自动 push 到该产品远程分支；依赖 T01。
- Skill 用户可见文案在 T01 冻结：`display_name` / `display_name_en` 与 `description_zh` / `description_en` 均为非空的中英文名称和说明；兼容字段 `description` 与 `description_zh` 一致。说明以用户目标、可执行动作、可观察结果表述，只陈述已实现且可追溯的能力，不将模型猜测、法律/财务结论或平台安装、运行、审核、发布写成既成事实。
- T02 Skill frontmatter 的 `examples_zh` / `examples_en` 各须恰好 3 条不同的自然语言用户提问；每条含明确输入或目标。长度约定中文 8–120 字符、英文 12–180 字符；NFC、首尾去空白、连续空白折叠、casefold、末尾中英文标点归一后不得重复（包括同一 Skill 的跨语言数组）。不允许占位符、脚本命令、内部路径/字段/错误码或无证据的保证性承诺；PDF / Excel / CSV 等用户输入格式名称可以使用。语义上换词凑数和具体能力的证明须人工审阅，不得仅以静态扫描 PASS 代替。
- T02 的 SKILL.md 正文依次包含且仅以二级标题标出 `## Preparation / 准备`、`## Usage / 使用`、`## Processing / 处理`、`## Outputs / 输出`、`## Limits / 限制`；每段须有非占位说明，分别交代前置输入/依赖、用户使用方式、处理与缺失值、输出形态及不支持范围/人工核对/平台边界。本地验证不等于 WorkBuddy 平台验证。现有历史 Skill 正文标题/示例不作本次批量迁移；**新候选**严格验收，历史资产若缺新门禁只标 NOT_TESTED 或需迁移，不能记作用户文案 PASS。
- Skill 用户文案门禁为 `USER_EXAMPLES_PASS` 与 `USER_DESCRIPTION_PASS`，仅在对应检查真实运行且所有子项通过时记 `PASS`；任一结构、类型、数量、空项、规范化重复、术语/命令或确定的越界声明命中记 `FAIL`，未运行或无法静态证明的语义/能力对应检查记 `NOT_TESTED` 并人工复核。报告须含失败路径、字段、示例索引、规则 ID 与证据命令；YAML 安全解析失败不得吞为 PASS。Expert 的 `.codebuddy-plugin/plugin.json` `quickPrompts` 是另一种专家快捷入口，仍由 Expert 独立规则检查双语对象恰好 3 个及其首条与 `defaultInitPrompt` 一致，不套用 Skill examples 数组规则。
- T03 wb-quality：独立业务准确性、边界、安全和许可核查；依赖 T02，失败走 qa-rework.md。
- T03 独立执行 Skill 文案/示例正反用例、产品级 validate 与必要的本地专项测试；复查脚本/正文支持每项用户可见能力。T04 在打包前检查上述两门禁及人工语义复核证据；任一 FAIL 或 NOT_TESTED 时不能宣称该项已通过，也不能以一般结构 validate PASS、Expert quickPrompts PASS 或本地 ZIP PASS 冒充。平台三门禁仍须真实平台回执方可 PASS。
- T04 wb-quality：现有工厂的实际 ZIP 构建、SHA-256、版本、成员、回归和发布限制；必要验收证据提交后允许自动 push 到该产品远程分支；依赖 T03。
- T05 wb-manager：对照真实任务记录、提交哈希、包、测试和平台未测项完成交付；依赖 T04。
不能靠群聊或普通 CLI 输出代替 Worker 的 kanban_complete/kanban_block。经理需在工作前确认模型与 Dispatcher 可用，并在收尾卡保存最终报告路径、看板状态和通知送达状态。
每次新模板变更必须先用隔离的虚构任务验证：依赖晋级、Ready 领取、Blocked 事件、经理唤醒、独立修复/QA 续跑和 T05 收尾；任一步无真实事件、run 或评论证据均标记 NOT_VERIFIED。
