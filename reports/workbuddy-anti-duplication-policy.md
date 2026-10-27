# WorkBuddy 反同质化规则与本地门禁

日期：2026-10-27
来源均为官方公开页面；本报告不代表当前开发者账号的审核结果。

## 官方来源

- [WorkBuddy 开放平台开发者公约（试行）](https://open.workbuddy.cn/docs/developer-agreement)，页面版本 1.0，2026-10-22。
- [WorkBuddy 技能规范](https://open.workbuddy.cn/docs/skill)。

## 逐条核验

| 条款 | 官方短引 | 对本项目的适用结论 | 状态 |
|---|---|---|---|
| §2.2.1 名称与定位 | “名称应体现具体任务、服务对象或适用场景”；“不得仅以编号、近义词或排列组合区分不同团队” | 四个名称分别指向应收逾期、库存呆滞、采购价格、销售收入；名称不同不是充分证据，仍需与实际能力一致 | `CONFIRMED` |
| §2.2.2 头像与图标 | “同一开发者的不同资产均不得重复使用相同图形”；“主体图形、构图等应具有可辨识的差异” | 本轮没有四个头像/图标资产，不能判定满足；共用品牌元素不等于可以完全复用图形 | `CONFIRMED / NOT_TESTED` |
| §2.2.3 描述与简介 | “说明服务对象、核心能力、适用场景及主要交付结果”；“不得仅替换名称、行业关键词或少量文字复用同一描述与简介” | 四份 SKILL.md 有不同输入、算法和输出说明，但库存/采购/销售仍有文案超出实际实现的问题，需先修订 | `CONFIRMED / REVIEW_REQUIRED` |
| §2.3.1 实际能力 | “能在声明条件下完成所描述的核心任务”；“优先打磨少量精品，并在具备独立服务价值和维护能力后持续新增” | 本地脚本分别完成不同核心任务，但局部能力为 PARTIAL/NOT_IMPLEMENTED；平台实际运行未验证 | `CONFIRMED / REVIEW_REQUIRED` |
| §2.3.2 使用条件 | “发布技能时，说明触发场景和执行内容” | 四份文档说明 CSV 字段、日期和运行方式；平台是否提供 Python、路径和权限仍未知，不能写成已验证 | `CONFIRMED / REVIEW_REQUIRED` |
| §2.3.3 运行与更新 | “发布资产前应测试核心流程”；“任务执行失败或部分完成时应向用户如实反馈” | 专项测试和交叉测试支持本地证据；必须保留失败/UNKNOWN，不得用本地测试代替平台调用 | `CONFIRMED` |
| §2.6.2 重复铺量与资源占用 | “功能、内容及交付结果相同或无实质差异”；仅改价格/收费方式或资产类型“不构成实质差异”；“共用品牌、模板、代码或接口，不影响其分别提交有独立服务价值的资产” | 核心判定是独立服务价值，不是名称或 AST 百分比。四个输入和算法不同，初步支持分别保留；仍需人工确认产品必要性、市场展示和真实交付 | `CONFIRMED / REVIEW_REQUIRED` |
| §2.7.1 合法使用与侵权 | 第三方品牌、肖像、内容、代码、模型、数据、接口须有合法依据并遵守开源许可证；“公开可访问不等于允许复制、转售或再分发” | 共享代码/数据/图标及专有许可证仍需分别审查；`PROPRIETARY` 和本地扫描不等于平台许可 | `CONFIRMED / BLOCKED` |

官方页面没有公开 Python AST 相似度、代码重合率或“相似度通过百分比”阈值。仓库的 AST 结果只能辅助定位人工审查对象，不得转写为官方认证。

《技能》页面的“技能基础结构”和“Frontmatter 字段”将 `SKILL.md`、YAML frontmatter、Markdown 正文，以及 name/display_name/display_name_en/description/description_zh/description_en/version/author 列为基础字段；`allowed-tools`、`examples_zh`、`examples_en`为非必填。四个 SKILL.md 均有这些主要字段。字段存在不等于内容已获平台审核，尤其是触发词、作者主体和实际能力描述仍需人工确认。

## 本地反同质化门禁设计

`tooling/similarity.py` 与 `tooling/products.py` 的 `similarity-check`：

- 默认扫描全部 10 个已登记产品，避免只比较四个财务 Skill；可传 `--id` 做单产品与所有注册产品的比较。
- 记录 AST 函数结构、精确函数摘要、输入字段、输出键、描述/场景/目标用户重复字段和源代码证据。
- 返回四类内部配对状态：`DISTINCT`、`OVERLAP_REVIEW`、`LIKELY_DUPLICATE`、`INSUFFICIENT_EVIDENCE`；另返回五个反同质化门禁状态。
- 总体状态固定为 `REVIEW_REQUIRED`，命令退出码为 1；不是平台认证，也不是单一分数判定。
- `release-check` 暴露五个新增门禁：`ANTI_DUPLICATION_PASS`、`FUNCTIONAL_DISTINCTNESS_PASS`、`INPUT_OUTPUT_DISTINCTNESS_PASS`、`METADATA_DISTINCTNESS_PASS`、`INDEPENDENT_VALUE_PASS`；未完成人工审查时均保持 `REVIEW_REQUIRED`。

## 当前四产品门禁

| 门禁 | 状态 | 说明 |
|---|---|---|
| `ANTI_DUPLICATION_PASS` | `REVIEW_REQUIRED` | 结构不同但需人工确认资产必要性和展示资料 |
| `FUNCTIONAL_DISTINCTNESS_PASS` | `REVIEW_REQUIRED` | 核心领域不同，库存/采购/销售有明确语义缺口 |
| `INPUT_OUTPUT_DISTINCTNESS_PASS` | `REVIEW_REQUIRED` | 输入协议明显不同；输出通用键不构成核心同质 |
| `METADATA_DISTINCTNESS_PASS` | `REVIEW_REQUIRED` | 文案有差异，四个图标/市场资料未完整核验 |
| `INDEPENDENT_VALUE_PASS` | `REVIEW_REQUIRED` | 需要产品负责人确认独立收费、维护和搜索价值 |
| `LICENSE_PASS` | `BLOCKED` | 私有版权与平台有效分发协议仍未核实 |
| `LOCAL_TEST_PASS` | `PASS` | 本地专项/全仓证据，不是平台证据 |
| `WORKBUDDY_RUNTIME_PASS` | `NOT_TESTED` | 没有平台安装和 Python 运行回执 |
| `PUBLISH_READY` | `BLOCKED` | 不允许由内部审计工具升级 |
