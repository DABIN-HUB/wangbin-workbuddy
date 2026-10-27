# WorkBuddy 产品工厂第二批财务 Skill 本地验收报告

日期：2026-10-27

## 范围与结论

本报告覆盖四个独立的 0.1.0 CSV 计算 Skill、可选的本地 XLSX→CSV 预处理工具，以及原有招标 Skill 发布阻断复核。所有结果均为本地仓库证据；没有把本地脚本、ZIP 校验或公开文档当作 WorkBuddy 平台安装、调用、审核或发布证据。

四个新 Skill 均完成真实业务计算、虚构 CSV、实际生成的 JSON 示例、专项测试和独立候选 ZIP。四个候选的本地完整性通过，但平台运行时、安装、对话调用和审核均未验证，因此发布门禁均为 `BLOCKED`。

## 产品结果

| 产品 | 本地专项测试 | ZIP SHA-256 | 本地验证 | 平台门禁 |
|---|---:|---|---|---|
| `wangbin-receivable-analyzer` | 6 passed | `229b302ae5109639e3379be61cd259549197f9b22e90a8ffbcf43539dfec1929` | PASS | BLOCKED |
| `wangbin-inventory-analyzer` | 7 passed, 1 skipped（Windows 无符号链接能力） | `b2b7d51998243d819d11237aa2652c486640133bda66a3e75fd6736691b09fdf` | PASS | BLOCKED |
| `wangbin-purchase-analyzer` | 9 passed | `00aaac8d7104151c1ea06e4f709234b94145ea4fca4972d3b866540814453571` | PASS | BLOCKED |
| `wangbin-sales-analyzer` | 8 passed | `571664ec2652a917ac1ea06a3b59b97e271d725f03843529228935b910cf62ab` | PASS | BLOCKED |

每个 ZIP 都用 `ZipFile.testzip()` 做了读回检查，成员未发现绝对路径或 `..` 路径段，实际 SHA-256 与上表一致。候选包均为独立目录、独立版本和独立工厂操作；没有合并四个 Skill。

### 实际计算边界

- 应收：显式 `--as-of`、未结余额、到期日、币种分组、1–30/31–60/61–90/91+ 账龄、客户逾期排序和可解释优先级；异常行拒绝且不回显原始敏感值。
- 库存：余额快照、收货、发料和可选主数据；库存价值按币种计算；周转率证据不足时返回 `UNKNOWN`；无移动、慢动、超储和余额不一致均为待复核候选。
- 采购：仅在物料、规格、单位、币种和税务处理完全一致时比较价格；不兼容组明确 `NOT_COMPARABLE`，不直接判定异常；提供报价价差、金额集中度和首尾等长半区间趋势。
- 销售：销售趋势、产品排名、客户贡献和集中度按币种计算；MoM/YoY 只有显式完整期间和 as-of 条件满足时才计算；无成本数据时利润、毛利率和盈利能力保持 `UNKNOWN`。
- 四个 Skill 均只承诺本地 UTF-8 CSV；不执行公式、宏或代码，不引入未经验证的付费 API，不声称平台自动提供 Python 或依赖安装。

## XLSX 本地预处理

新增 `tooling/financial_xlsx.py`，复用 document-engine 的 `SecurityPolicy`、输入快照、容器校验、输出路径和资源预算；仅作为仓库外发给普通 Skill 的**可选本地工具**，不放入四个 Skill ZIP，也不声称普通 WorkBuddy Skill 原生支持 XLSX。

专项结果：`tests/test_financial_xlsx.py` **8 passed**。已覆盖真实 XLSX 保序转换、重复行保留、公式拒绝、宏标记拒绝、容器大小限制、错误扩展名、空工作表、路径越界及 CLI 隐私输出。

## 招标 Skill 0.1.0

报告：`reports/tender-0.1.0-release-review.md`。

- 原候选 SHA-256 保持：`2e68809033301c97b02ec7c7fd59f7b477fcd2f1f86d515d69b5fc7b20146bc7`。
- ZIP 根目录、六个成员、`SKILL.md` 相对路径和本地完整性检查通过。
- ZIP 没有独立 `LICENSE`/`NOTICE`，仓库根也没有独立 LICENSE；分发权利和许可证覆盖范围需人工确认。
- 脚本仅使用 Python 标准库，普通 Skill Python 运行、工作目录、权限和依赖机制仍未知。
- 没有授权的 WorkBuddy 私有安装会话；未上传、未安装、未调用、未提交审核或发布。
- 不修改或覆盖原始 0.1.0；若权利人确认采用 MIT，仅补充发行文件时应另建新版本候选。

## 回归与工厂门禁

- 全仓库回归：**103 passed, 5 skipped**。跳过项均为当前 Windows 环境无法创建符号链接的能力测试，未伪称通过。
- `python -m tooling.products validate`：PASS。
- `python -m tooling.products portfolio`：成功；未取得的曝光、安装、使用、反馈、成本和商业潜力保持 `UNKNOWN`。
- 四个新产品的 `release-check` 均以退出码 1 结束，顶层状态为 `BLOCKED`；其中 `local_candidate` 为 `PASS`，`platform` 为 `BLOCKED`。没有把本地通过错误聚合成发布通过。
- 受保护软件顾问 Expert 候选 SHA-256 保持：`577f3089d2f4707178f44ba1e5c395a99853bb9558f3e8c0e752a0e6ba2e30de`。

## 本地提交

- `f1c588c4923fb2e6a0c218f345d11822ec2e8abb` — `feat: add receivables aging Skill`
- `bbb09219e9d884a13e80430f6fce299ba6474605` — `docs: audit tender Skill release blockers`
- `a1f24f14886c86e17b0c3532d4b54cebbb3c0d49` — `feat: add purchase price analyzer Skill`
- `292ff8ca2fd1edf40dc94819839d170c93ca9d93` — `feat: add inventory slow-moving analyzer Skill`
- `6e2887fb7740b7b43a3623cae4bbbef4e99f6334` — `feat: add sales revenue analyzer Skill`
- `fb627a1c39267142fa52e3c6b647aae76a127297` — `feat: add safe local XLSX to CSV preprocessor`

未执行 push、PR、Tag 修改、平台上传或正式审核提交。

## 尚需人工完成

1. 由权利人确认四个新 Skill 及招标 Skill 的独立分发许可证和样例数据授权范围。
2. 在有授权的 WorkBuddy 私有环境中，使用虚构样例验证 ZIP 解析、安装、脚本路径、Python 可用性、读文件权限和真实对话调用。
3. 若唯一可用入口会触发正式审核或公开发布，先取得单独授权；当前不执行。
4. 记录平台返回的候选版本、安装回执、调用结果和审核状态后，再更新 `review_status`；不得从本地 PASS 推断 `APPROVED` 或 `PUBLISHED`。

## 第三批建议

建议保持独立产品边界，按数据可得性和计算可审计性排序：

1. 供应商交付与采购履约分析：交期、到货完整率、退货和质量异常，复用采购 Skill 的可比维度与异常候选框架。
2. 现金流预测：仅在有完整账期、回款和付款计划时计算，缺失期间保持 `UNKNOWN`。
3. 费用预算偏差分析：按成本中心、期间、币种和预算版本比较，严格区分实际、预算与预测。

第三批仍应优先使用本地 CSV、`Decimal`、显式期间和可解释候选；不得在数据不足时推算利润、周转或商业成功率。
