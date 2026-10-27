# 四个经营分析 Skill 发布建议与最终验收

> 历史报告：本文记录 `0.1.2` 候选整改前状态，不代表 Phase 9 的当前候选结论。当前状态见 `reports/financial-skills-phase9-release-candidate.md` 和 `reports/workbuddy-upload-list.md`。

日期：2026-10-27
候选版本：四个均为 `0.1.2`。
审计基线：`b2dd61354665ec80e4afe8598eadc9ab755883e1`。

## 直接回答

**四个 Skill 具有足够初步独立价值，可保留为四个分别维护的候选产品；当前不适合直接分别提交 WorkBuddy 正式审核。**

理由：四者确实有不同的数据合同和核心算法，不属于仅改名或替换提示词的明显复制；但本轮发现库存、采购、销售和应收的能力边界/文案缺口，反同质化五项门禁仍需人工确认，许可证及平台运行门禁仍阻断。保留独立产品不是平台合规 PASS，也不等于允许试传。

不建议现在合并或删除任何现有 Skill。若后续产品负责人确认用户只需要一个入口，再另行编写合并方案；当前四类岗位输入和交付明显不同，合并会提高单资产输入复杂度。

## 功能与整改结论

| 产品 | 当前实际能力 | 主要问题 | 发布建议 |
|---|---|---|---|
| 应收 | 逾期、账龄、客户逾期排序可运行；输出客户级而非发票级 | 优先级仅 HIGH/MEDIUM；业务异常实际主要是输入质量；重复 ID 首行非法时会排除后续合法行 | 修正文案并补充边界后列入首批私有验证 |
| 库存 | 快照、收货/发料、价值、无移动、慢动/超储和余额候选 | 无发料时明细 `UNKNOWN` 却产生周转率 `0` 慢动候选；`reorder_point` 未使用；未输出最后出库日/呆滞天数 | **先修复再验证**，当前不推荐提交 |
| 采购 | 五项可比键价格变化、不可比组、金额集中度和趋势 | 最高/最低报价可来自同一供应商，不能直接称为供应商之间比价或节约机会 | 收窄文案或修复算法后再验证 |
| 销售 | 收入、自然月趋势、产品排名、客户贡献和集中度 | 客户/产品结构跨期异常未实现；`anomalies` 目前仅为大订单候选 | 可作为后续候选；不要宣传结构异常已实现 |

允许的整改方向：修正文案、补齐输入边界、修复明确计算矛盾、把未实现字段标为未实现；不允许通过无意义字段或提示词制造差异，不修改测试预期掩盖问题，不因降低代码比例而重写合理通用基础代码。

## 方案判断

选择“分别保留”而不是当前合并：

- 应收用户关心逾期和回款，库存用户关心库存状态和流转，采购用户关心可比报价，销售用户关心收入与客户/产品结构。
- 四个输入协议不能互换；八组交叉测试中正确领域 4 组成功、错误领域 4 组以缺字段非零拒绝。
- 合并会减少平台资产数量，但会增加用户选择和输入协议复杂度，且四套算法仍需独立维护。
- 独立发布的前提是每项资产单独说明触发、输入、交付、限制，并取得平台对四次资产的实际接受结果。

## 当前门禁

| 门禁 | 状态 | 证据/原因 |
|---|---|---|
| `ANTI_DUPLICATION_PASS` | `REVIEW_REQUIRED` | AST/字段/元数据审计初步不同；独立服务价值与图标需人工确认 |
| `FUNCTIONAL_DISTINCTNESS_PASS` | `REVIEW_REQUIRED` | 核心算法不同，但多个 requested ability 仅 PARTIAL/NOT_IMPLEMENTED |
| `INPUT_OUTPUT_DISTINCTNESS_PASS` | `REVIEW_REQUIRED` | 输入结构差异明确；输出通用字段及边界语义需人工审查 |
| `METADATA_DISTINCTNESS_PASS` | `REVIEW_REQUIRED` | 文案不同；完整市场展示、图标未验证 |
| `INDEPENDENT_VALUE_PASS` | `REVIEW_REQUIRED` | 尚无独立收费/维护/平台展示的真实证据 |
| `LICENSE_PASS` | `BLOCKED` | 私有版权协议和源码分发边界未获账号/平台确认 |
| `LOCAL_TEST_PASS` | `PASS` | 四组专项与全仓已有本地证据；非平台证据 |
| `PACKAGE_VALIDATION_PASS` | `PASS` | 四个 0.1.2 ZIP 完整性、成员和登记 SHA 已核验 |
| `WORKBUDDY_ZIP_PARSE_PASS` | `NOT_TESTED` | 未上传平台 |
| `WORKBUDDY_RUNTIME_PASS` | `NOT_TESTED` | 未取得 WorkBuddy Python/调用回执 |
| `WORKBUDDY_REVIEW_PASS` | `NOT_TESTED` | 无平台审核结果 |
| `PUBLISH_READY` | `BLOCKED` | 反同质化、许可证和平台门禁未闭合 |

## 试传和审核判断

| 操作 | 当前结论 |
|---|---|
| 人工平台试传 | **不允许**：许可证协议仍未确认，且四产品有待修正的能力/文案问题 |
| 非公开运行验证 | **未执行**；需先由账号所有者确认合法私有入口和候选版本 |
| 正式提交审核 | **不允许** |
| 公开上架 | **不允许** |

“可先试传产品”：当前没有一个获得本轮正式放行。完成本地修复后，建议先核验销售或应收的私有运行路径，再核验库存和采购；这只是排序建议，不是平台许可。

## 现有候选包

| 产品 | 版本 | ZIP 绝对路径 | SHA-256 | 当前试传 |
|---|---|---|---|---|
| 应收账款逾期分析 | 0.1.2 | `F:\\ideaWorkSpace\\wangbin-workbuddy\\dist\\wangbin-receivable-analyzer-0.1.2-skill-candidate.zip` | `3165ecc4d2ce435ac3ed263dc52d4585a89ac46c5b66324b995878d5a26e897f` | 不允许 |
| 库存呆滞分析 | 0.1.2 | `F:\\ideaWorkSpace\\wangbin-workbuddy\\dist\\wangbin-inventory-analyzer-0.1.2-skill-candidate.zip` | `f2e720d7c544bb4a4d24aa4f01c21a58826965a67f3195c5e8d9020caaeee62c` | 不允许 |
| 采购价格分析 | 0.1.2 | `F:\\ideaWorkSpace\\wangbin-workbuddy\\dist\\wangbin-purchase-analyzer-0.1.2-skill-candidate.zip` | `1e0de940a4198a3ea92d86b7fd0a84b999620247e43e74dd76315b4e75621dd4` | 不允许 |
| 销售数据分析 | 0.1.2 | `F:\\ideaWorkSpace\\wangbin-workbuddy\\dist\\wangbin-sales-analyzer-0.1.2-skill-candidate.zip` | `34378ecb2159f8562f71b5c89074e449556c72f74f814e5fc37291f3107f1425` | 不允许 |

这些 ZIP 是上一轮已真实构建的候选；本轮只修改工厂、台账和报告，没有修改包内源，因此没有伪造新哈希。若后续修复任一包内文件，必须升版本、重新构建并重新计算 SHA-256。

## 凭证与候选包复核

- `.venv/Scripts/python.exe -c "from pathlib import Path; from tooling.validators.secret_scanner import scan_for_secrets; ..."`：扫描结果 `0` 个疑似凭证；报告、`dist`、`.venv` 和 Git 元数据按扫描器规则排除，原始凭证值未写入报告。
- 四个 `0.1.2` 候选的实际字节数和 SHA-256 已重新读取，分别为 7470/12535/11517/9889 bytes 与表中哈希一致。由于本轮未修改包内源，不生成伪造的新 ZIP。

## 必须完成的下一步

1. 修复库存周转 UNKNOWN/0 逻辑并重新生成新版本候选；同步说明 `reorder_point` 是否实现。
2. 对采购价差明确“同供应商价格波动”与“跨供应商报价比较”，或在代码中要求不同供应商后升版。
3. 将销售客户/产品结构异常标为未实现，或另行设计经过验证的跨期算法；不要只改标题。
4. 决定应收是否需要逐发票状态和更细粒度优先级；未实现前保持 PARTIAL 文案。
5. 由账号所有者确认 WorkBuddy 有效协议、私有测试入口、ZIP 源码分发边界和审核流程；留存脱敏回执。
6. 私有平台路径真实执行 ZIP 解析、安装、调用和失败反馈后，才更新 `WORKBUDDY_*` 门禁。
