# WorkBuddy 增量产品工厂设计

## 边界与基线

在现有 `tooling/`、`packages/`、`services/` 上增量建设，无数据库或服务端。保留现有四个统一命令的参数和语义；旧文档助手、CLI Connector、Expert 源码及其发布候选不进入本次修改清单。软件顾问 ZIP 的基线 SHA-256 为 `577f3089d2f4707178f44ba1e5c395a99853bb9558f3e8c0e752a0e6ba2e30de`。用户报告该 Expert 已提交审核，仅记录 `USER_REPORTED_SUBMITTED` 证据；没有平台回执不能断言 APPROVED、安装或调用通过。

## 现状与复用

已有统一 CLI 和生成器 (`tooling/cli.py`, `tooling/generators.py`)、三类基本结构校验 (`tooling/validators/project_validator.py`)、凭证扫描、ZIP 校验及哈希 (`tooling/validators/`)、确定性 Expert/Phase 3 打包模式 (`tooling/phase5_expert_packager.py`, `tooling/phase3_packager.py`)。现有通用 Expert 校验比 phase5 宽松，严格规则必须单独抽出并由旧 packager 保持原接口。文档引擎支持多种文本文件和受限解析，但没有可信页码、坐标或完整安全沙箱；不能推定 WorkBuddy 普通 Skill 自动安装 Python 依赖。

## 数据模型

`products/catalog.json` 包含 schema_version 及 products；每项包括唯一 kebab-case ID、名称、Skill/Expert/Connector 类型、目标用户、场景、开发/维护信息、状态、审核状态、版本记录。状态限 BACKLOG、DEVELOPING、TESTED、SUBMITTED、APPROVED、REJECTED、PUBLISHED、PAUSED；审核字段允许 USER_REPORTED_SUBMITTED、UNKNOWN、NOT_AVAILABLE、BLOCKED、NOT_TESTED 等带证据状态，不自动提升产品状态。版本包含源目录、版本号、候选路径及 SHA-256（未知写 UNKNOWN）、日期（未知写 UNKNOWN）。审计时间、证据来源与范围必须明确，不能把本地 PASS 当平台 PASS。

`products/metrics.json` 按产品 ID + 版本登记平台曝光、安装、使用、反馈、审核结果、开发及维护成本；未取得数据统一使用 UNKNOWN 或 NOT_AVAILABLE，不以零替代。产品组合报告对可计算的真实数据展示比较，对证据不足的成本、成功率、商业潜力给出 UNKNOWN 和数据缺口，不作成功预测。

## 命令与文件边界

新增 `python -m tooling.products {list,init,validate,test,package,verify,record,portfolio,release-check}`；全部接收 `--root`，产品级命令接收 `--id`；输出范围限指定产品。init 从已有 Skill 生成器和 Expert/Connector 模板复制，明确 Connector 的 CLI/MCP 模式；建立目录前核对注册 ID、现有包元数据名称、目录与发布路径，拒绝冲突和已有目录，失败不覆盖。模板占位不作为已可发布产品。test 仅运行该产品关联的既有自动化检查/样例验收，不能推断平台测试；生产路径不依赖其他产品包。package 采用白名单和稳定 ZIP 元数据，排除 symlink/缓存/私有文件，重新读取逐字节校验并生成 manifest 与 sidecar；输出 `dist/{id}-{version}-{type}-candidate.zip`，已存在非同一字节的目标禁止覆写。verify 校验成员、sidecar 和源内容；release-check 汇集元数据、内容、凭证、许可证、ZIP 与证据门禁，保持平台 BLOCKED/NOT_TESTED。

严格 Expert 校验单独成为可复用 profile：必需字段及双语对象、中文描述 40–50 字、中文展示名不超过 15 字、三个双语 tags/quickPrompts、首个 quick prompt 一致、Agent identity/frontmatter 对齐、PNG 512×512 不超过 500 KB、无未声明外部 runtime/tool/skill 依赖、无 symlink。既有软件顾问固定 ID、版本、类目、路径继续作为旧 packager 的额外约束；新 Expert 可明确选择可审查配置，不沿用宽松通用校验作为发布门禁。

## 招标 Skill MVP

`packages/skills/wangbin-tender-analyzer/` 包含 WorkBuddy frontmatter、隐私/能力边界、文本优先分析入口、输出模板和可公开的虚构示例及预期输出。对用户明确授权的 TXT/Markdown 或当前引擎能可靠抽取文本的文件，逐条识别资格、评分、技术要求、日期及响应项；每条结论绑定原文短引文与可证明的文本行位置。对复杂版式、扫描件、表格丢失、冲突/缺失条款显示待核实。不得生成未经证明的页码、法律结论、实际投标得分或平台行为。分析代码只处理已抽取文字；解析失败或运行时缺失应明确失败，不能猜测。

## 验收和人工门禁

分别验证旧四个命令、已有 Expert 严格规则、旧 ZIP 哈希、产品级初始化/校验/测试/打包/校验哈希、重复构建、名称路径冲突、UNKNOWN 汇总、招标示例输入与输出、发布报告。仅本地验证通过方可标 LOCAL_CANDIDATE；WorkBuddy 上传解析、安装、真实对话、账号权限、审核结论及公开发布仍需人工或授权平台证据，不会以本地测试代替。只提交显式审查过的文件；不 push、不建 PR、不改 tag。
