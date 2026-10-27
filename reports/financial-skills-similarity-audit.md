# 四个经营分析 Skill 同质化代码与元数据审计

日期：2026-10-27
仓库基线：`b2dd61354665ec80e4afe8598eadc9ab755883e1`
范围：四个 `0.1.2` 财务 Skill，并将全部 10 个已登记产品纳入工厂扫描。

## 结论摘要

四个 Skill **不是仅通过改名、提示词或少量参数复制的空壳**。源码使用了不同输入模型、核心聚合键、业务公式和输出决策字段，具备初步独立服务价值：

- 应收：发票到期/逾期、账龄、客户逾期排序。
- 库存：快照、收货/发料、数量周转、无移动/慢动/超储/余额一致性候选。
- 采购：物料规格单位税务可比组、价格变化、不可比组和供应商金额集中度。
- 销售：收入、自然月趋势、产品排名、客户贡献和集中度。

但本地结构扫描**不能直接给出 WorkBuddy 合规 PASS**。官方规则的判据是独立服务价值和实际能力，而非代码百分比；本次扫描将四个反同质化门禁保持为 `REVIEW_REQUIRED`。同时存在需要修正或重新说明的产品问题：库存无发料时产生 `0` 周转慢动候选但明细状态为 `UNKNOWN`；采购报价价差未要求最高价与最低价来自不同供应商；销售尚未实现客户/产品跨期结构异常；应收优先级仍是粗粒度候选。

当前建议：**保留四个独立产品形态，不建议现在提交正式 WorkBuddy 审核**。先修正文案/边界和上述明确逻辑问题，再分别取得平台私有运行证据。

## 扫描方法与边界

新增 `tooling/similarity.py`，由 `python -m tooling.products similarity-check` 调用：

1. 扫描 `products/catalog.json` 的全部已登记产品，不只比较四个最近产品；本次全量为 10 个产品、45 个两两组合。
2. 读取每个源目录的 Python 脚本并解析 AST；记录函数节点序列、核心函数名、常量字段、输出字典键和源文件证据路径。
3. 比较精确函数 AST 摘要、节点序列辅助比例、输入字段交集、输出字段交集、展示元数据重复字段。
4. 输出四类配对状态 `DISTINCT`、`OVERLAP_REVIEW`、`LIKELY_DUPLICATE` 或 `INSUFFICIENT_EVIDENCE`，并将五个反同质化门禁和独立价值保持 `REVIEW_REQUIRED`。
5. 命令始终返回退出码 1；这是审查门，不是失败地声称重复，也不是通过地声称合规。

AST 节点比例只用于定位人工审查重点，**没有官方阈值，也没有被用于单一判定**。结构相似的 CSV 读取、Decimal 格式化、错误码和 JSON 输出属于合理基础复用；是否是同一服务仍须看业务算法、用户、输入、交付和必要性。

## 四个 Skill 的证据画像

| 产品 | 核心源码证据 | 输入模型 | 业务输出 | 当前独立性判断 |
|---|---|---|---|---|
| 应收 `wangbin-receivable-analyzer` | `packages/skills/wangbin-receivable-analyzer/scripts/analyze_receivables.py:81-160` | 单 CSV：`invoice_id, customer_id, due_date, open_balance, currency` | `totals`、`aging`、`customers`、`issues` | 有独立逾期/账龄价值；部分能力仍粗粒度 |
| 库存 `wangbin-inventory-analyzer` | `.../analyze_inventory.py:293-389` | balances、receipts、issues，master 可选 | `inventory`、`inventory_value`、无移动/慢动/超储/余额异常候选 | 有独立库存状态与流转价值；当前有周转证据矛盾 |
| 采购 `wangbin-purchase-analyzer` | `.../analyze_purchase.py:225-350` | 采购订单：物料、供应商、规格、单位、币种、税务处理 | 可比价格变化、价差、供应商集中度、趋势、不可比组 | 有独立采购可比分析；供应商价差语义需收窄 |
| 销售 `wangbin-sales-analyzer` | `.../analyze_sales.py:252-323` | 销售订单：客户、产品、日期、金额、币种 | 收入、月度趋势、产品排名、客户贡献/集中度、风险 | 有独立收入分析；客户/产品结构异常尚未实现 |

四个源 `SKILL.md`、`manifest.json`、LICENSE、示例和专项测试均已实际读取。许可证仍是 `PROPRIETARY` + `REQUIRES_MANUAL_REVIEW`，与同质化判断分开。

## 六组两两扫描结果

| 对比 | AST 节点序列辅助比例 | 共享输入字段 | 共享输出字段 | 内部标记 | 实际业务判断 |
|---|---:|---|---|---|---|
| 应收 vs 库存 | 0.0379 | `currency` | `limitations` | `DISTINCT` | 发票逾期与库存流转/状态不同，独立价值明确 |
| 应收 vs 采购 | 0.0598 | `currency` | `limitations` | `DISTINCT` | 应收账龄与采购可比价差不同 |
| 应收 vs 销售 | 0.0282 | `currency` | `limitations` | `DISTINCT` | 应收余额/到期日与销售订单收入不同 |
| 库存 vs 采购 | 0.2095 | `currency`、`quantity` | `anomaly_candidates`、`summary`、`invalid_rows` 等通用键 | `DISTINCT` | 都处理数量和金额，但库存按快照/移动平衡，采购按五项可比组；需人工确认边界 |
| 库存 vs 销售 | 0.0252 | `currency` | `summary`、`invalid_rows`、`limitations`、`privacy` | `DISTINCT` | 库存状态与销售收入/客户结构不同 |
| 采购 vs 销售 | 0.0359 | `currency`、`order_date`、`order_id` | 通用 `summary`、`invalid_rows`、`limitations`、`privacy` | `DISTINCT` | 都有趋势/集中度，但采购看供应商/可比价格，销售看客户/产品收入 |

以上标记是内部扫描状态，不是平台认证。全量扫描还将未实现或非脚本产品标为 `INSUFFICIENT_EVIDENCE`，避免只因缺少代码而误判为独立或重复。

## 需要人工复核的同质化风险

1. 四个 Skill 共用 UTF-8 CSV、Decimal、稳定 JSON、输入公式拒绝和本地执行说明；这是合理基础复用，不构成重复产品结论。
2. 四个 Skill 都有 `summary`、`invalid_rows`、`limitations`、`privacy` 等通用输出键；这些不能作为核心交付相同的证据。
3. 四个 Skill 的展示作者、专有许可、版本和本地脚本形态相近；品牌共用不等于业务服务相同，但四个产品的头像/图标本轮没有资产证据，不能判定 2.2.2 已满足。
4. 当前源代码扫描无法判断 WorkBuddy 对话触发、实际安装、平台交付和用户搜索展示；这些门禁保持 `NOT_TESTED`。

## 对照的官方规则

详见 `reports/workbuddy-anti-duplication-policy.md`。关键结论：官方开发者公约 §2.2.1 要求名称体现具体任务/服务对象/场景，禁止仅用编号、近义词或排列组合区分；§2.2.2 要求同一开发者不同资产的头像/图形可辨识地不同；§2.2.3 要求描述说明服务对象、核心能力、场景和交付，不能只替换关键词；§2.3.1–2.3.3 要求实际完成声明能力、说明触发/执行条件、发布前测试并如实反馈；§2.6.2 以功能、内容、交付结果是否相同或无实质差异及独立服务价值为核心，并明确共用品牌、模板、代码或接口不必然阻止分别提交；未公布代码相似度阈值。§2.7.1 要求第三方代码、数据、接口和开源许可具有合法依据。

## 当前状态

| 内部门禁 | 状态 | 依据 |
|---|---|---|
| `ANTI_DUPLICATION_PASS` | `REVIEW_REQUIRED` | 结构不同，但仍需人工确认独立服务价值及平台展示资料 |
| `FUNCTIONAL_DISTINCTNESS_PASS` | `REVIEW_REQUIRED` | 四者有核心差异，但库存、采购、销售存在明确能力/语义缺口 |
| `INPUT_OUTPUT_DISTINCTNESS_PASS` | `REVIEW_REQUIRED` | 输入模型差异明显，通用字段不能代替人工交付审查 |
| `METADATA_DISTINCTNESS_PASS` | `REVIEW_REQUIRED` | 名称和说明不同，但头像/完整市场资产未验证 |
| `INDEPENDENT_VALUE_PASS` | `REVIEW_REQUIRED` | 需要产品负责人确认分别收费/使用和维护必要性 |
| `LICENSE_PASS` | `BLOCKED` | 平台有效协议和私有分发边界未核实 |
| `LOCAL_TEST_PASS` | `PASS`（现有回归） | 仅是本地测试证据 |
| `WORKBUDDY_RUNTIME_PASS` | `NOT_TESTED` | 无平台运行证据 |
| `PUBLISH_READY` | `BLOCKED` | 前置门禁未满足 |
