# WorkBuddy 可上传发布清单

> 本清单只记录仓库内候选 ZIP 的本地存在性、归档完整性和 SHA-256。`CAN_ENTER_PLATFORM_TRIAL` 不等于已安装、已调用、已审核或已正式发布；本轮没有自动上传、提交审核或发布。

## 全部产品

| 产品名称 | 产品类型 | 版本 | ZIP 绝对路径 | SHA-256 | 发布状态 | 阻断原因 |
| --- | --- | --- | --- | --- | --- | --- |
| Document Assistant | Skill | 1.0.0 | F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-document-assistant-1.0.0-candidate.zip | 12544dbd203c3bed5cf6f0094ffc752b17d3fcc852377a6ff09113cb31b5c5b3 | SECURITY_BLOCKED; release_gate=BLOCKED | license file is absent; no license claim is verified |
| Document CLI Connector | Connector | 1.2.0 | F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-document-cli-1.2.0-connector-candidate.zip | be64b3b619382cbc74686fef6bd64a402f15f380487bde61e41620df66feb0e7 | SECURITY_BLOCKED; release_gate=BLOCKED | license file is absent; no license claim is verified |
| Software Consultant | Expert | 1.0.0 | F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-software-consultant-1.0.0-expert-candidate.zip | 577f3089d2f4707178f44ba1e5c395a99853bb9558f3e8c0e752a0e6ba2e30de | SUBMITTED_REVIEW; release_gate=BLOCKED | submission is recorded, but platform approval is not verified |
| 招标文件分析助手 | Skill | 0.1.0 | F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-tender-analyzer-0.1.0-skill-candidate.zip | 2e68809033301c97b02ec7c7fd59f7b477fcd2f1f86d515d69b5fc7b20146bc7 | SECURITY_BLOCKED; release_gate=BLOCKED | license file is absent; no license claim is verified |
| 应收账款逾期分析 | Skill | 0.1.1 | F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-receivable-analyzer-0.1.1-skill-candidate.zip | 1fc44aa4f7d8790ab6b3856977d04abd8906f72fb25587c108fb94f60cd7792e | SECURITY_BLOCKED; release_gate=BLOCKED | local files declare no independently verified license/dependency approval |
| 软件需求变更影响分析 | Skill | 0.1.0 | MISSING | UNKNOWN | MISSING; release_gate=BLOCKED | candidate ZIP is not present |
| 库存呆滞分析 | Skill | 0.1.1 | F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-inventory-analyzer-0.1.1-skill-candidate.zip | 1cdd808458ae57780e9b8cad77e26eb784683e3e6772efce1a0980d34ecbe686 | SECURITY_BLOCKED; release_gate=BLOCKED | local files declare no independently verified license/dependency approval |
| 垂直行业研究报告 | Skill | 0.1.0 | MISSING | UNKNOWN | MISSING; release_gate=BLOCKED | candidate ZIP is not present |
| 采购价格分析 | Skill | 0.1.1 | F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-purchase-analyzer-0.1.1-skill-candidate.zip | 673f076b51d760c3eaf8d6ad9c30e254846c60a4a23705d297635023e88814e5 | SECURITY_BLOCKED; release_gate=BLOCKED | local files declare no independently verified license/dependency approval |
| 销售数据分析 | Skill | 0.1.1 | F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-sales-analyzer-0.1.1-skill-candidate.zip | 52c7ee38efe9d46a87ebd89d3f9fd13060d16bebd1ca6e6c480d53ebe883c40d | SECURITY_BLOCKED; release_gate=BLOCKED | declarations require manual license and dependency verification |

## 分类说明

- `CAN_ENTER_PLATFORM_TRIAL`：本地候选存在、ZIP 完整性和登记哈希通过，且源码校验通过；平台安装、调用、审核仍未知。
- `DECLARED_OR_UNKNOWN`：源码声明了运行时或依赖，是否由 WorkBuddy 提供尚未验证。
- `SECURITY_BLOCKED`：归档、源码安全、路径、许可证或其他本地安全门禁未通过。
- `SUBMITTED_REVIEW`：仅保留提交证据，不升级为平台批准。
- `OFFICIALLY_PUBLISHED`：只有直接平台发布证据才可使用；当前仓库没有该证据。
- `MISSING`：候选 ZIP 尚未生成，不能视为可上传。

## 四个独立财务 Skill

### 应收账款逾期分析（`wangbin-receivable-analyzer`）

- 版本：`0.1.1`
- ZIP：`F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-receivable-analyzer-0.1.1-skill-candidate.zip`
- 文件存在：`True`；大小：`7691` bytes
- SHA-256：`1fc44aa4f7d8790ab6b3856977d04abd8906f72fb25587c108fb94f60cd7792e`（登记值匹配：`PASS`）
- ZIP 完整性：`PASS`
- 当前发布门禁：`BLOCKED`；上传状态：`SECURITY_BLOCKED`
- 许可证状态：`REQUIRES_MANUAL_REVIEW`；许可证说明：local files declare no independently verified license/dependency approval
- 额外安装依赖：`NONE_DECLARED`；平台运行时：`UNKNOWN`；平台验证：`False`
- 是否可单独上传运行：`不可宣称独立运行`（local files declare no independently verified license/dependency approval）
- ZIP 内部文件：
  - `wangbin-receivable-analyzer/LICENSE`
  - `wangbin-receivable-analyzer/SKILL.md`
  - `wangbin-receivable-analyzer/examples/fictional-receivables.csv`
  - `wangbin-receivable-analyzer/examples/fictional-receivables.expected.json`
  - `wangbin-receivable-analyzer/manifest.json`
  - `wangbin-receivable-analyzer/scripts/analyze_receivables.py`

### 库存呆滞分析（`wangbin-inventory-analyzer`）

- 版本：`0.1.1`
- ZIP：`F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-inventory-analyzer-0.1.1-skill-candidate.zip`
- 文件存在：`True`；大小：`12748` bytes
- SHA-256：`1cdd808458ae57780e9b8cad77e26eb784683e3e6772efce1a0980d34ecbe686`（登记值匹配：`PASS`）
- ZIP 完整性：`PASS`
- 当前发布门禁：`BLOCKED`；上传状态：`SECURITY_BLOCKED`
- 许可证状态：`REQUIRES_MANUAL_REVIEW`；许可证说明：local files declare no independently verified license/dependency approval
- 额外安装依赖：`NONE_DECLARED`；平台运行时：`UNKNOWN`；平台验证：`False`
- 是否可单独上传运行：`不可宣称独立运行`（local files declare no independently verified license/dependency approval）
- ZIP 内部文件：
  - `wangbin-inventory-analyzer/LICENSE`
  - `wangbin-inventory-analyzer/SKILL.md`
  - `wangbin-inventory-analyzer/examples/fictional-balances.csv`
  - `wangbin-inventory-analyzer/examples/fictional-inventory.expected.json`
  - `wangbin-inventory-analyzer/examples/fictional-issues.csv`
  - `wangbin-inventory-analyzer/examples/fictional-master.csv`
  - `wangbin-inventory-analyzer/examples/fictional-receipts.csv`
  - `wangbin-inventory-analyzer/manifest.json`
  - `wangbin-inventory-analyzer/scripts/analyze_inventory.py`

### 采购价格分析（`wangbin-purchase-analyzer`）

- 版本：`0.1.1`
- ZIP：`F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-purchase-analyzer-0.1.1-skill-candidate.zip`
- 文件存在：`True`；大小：`11734` bytes
- SHA-256：`673f076b51d760c3eaf8d6ad9c30e254846c60a4a23705d297635023e88814e5`（登记值匹配：`PASS`）
- ZIP 完整性：`PASS`
- 当前发布门禁：`BLOCKED`；上传状态：`SECURITY_BLOCKED`
- 许可证状态：`REQUIRES_MANUAL_REVIEW`；许可证说明：local files declare no independently verified license/dependency approval
- 额外安装依赖：`NONE_DECLARED`；平台运行时：`UNKNOWN`；平台验证：`False`
- 是否可单独上传运行：`不可宣称独立运行`（local files declare no independently verified license/dependency approval）
- ZIP 内部文件：
  - `wangbin-purchase-analyzer/LICENSE`
  - `wangbin-purchase-analyzer/SKILL.md`
  - `wangbin-purchase-analyzer/examples/fictional-purchases.csv`
  - `wangbin-purchase-analyzer/examples/fictional-purchases.expected.json`
  - `wangbin-purchase-analyzer/manifest.json`
  - `wangbin-purchase-analyzer/scripts/analyze_purchase.py`

### 销售数据分析（`wangbin-sales-analyzer`）

- 版本：`0.1.1`
- ZIP：`F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-sales-analyzer-0.1.1-skill-candidate.zip`
- 文件存在：`True`；大小：`10109` bytes
- SHA-256：`52c7ee38efe9d46a87ebd89d3f9fd13060d16bebd1ca6e6c480d53ebe883c40d`（登记值匹配：`PASS`）
- ZIP 完整性：`PASS`
- 当前发布门禁：`BLOCKED`；上传状态：`SECURITY_BLOCKED`
- 许可证状态：`REQUIRES_MANUAL_REVIEW`；许可证说明：declarations require manual license and dependency verification
- 额外安装依赖：`NONE_DECLARED`；平台运行时：`UNKNOWN`；平台验证：`False`
- 是否可单独上传运行：`不可宣称独立运行`（declarations require manual license and dependency verification）
- ZIP 内部文件：
  - `wangbin-sales-analyzer/LICENSE`
  - `wangbin-sales-analyzer/SKILL.md`
  - `wangbin-sales-analyzer/examples/fictional-sales.csv`
  - `wangbin-sales-analyzer/examples/fictional-sales.expected.json`
  - `wangbin-sales-analyzer/manifest.json`
  - `wangbin-sales-analyzer/scripts/analyze_sales.py`

## 本轮许可证审查

- 所有权证据：四个产品的源码提交和 manifest 作者字段指向 `wangbin` 或 `Wangbin Research`；这支持仓库内原创性判断，但不等同于本人对外授权意图的法律确认。
- 第三方代码与依赖：四个 Skill ZIP 内脚本只导入 Python 标准库，未发现第三方源码、付费 API 或独立运行依赖声明；WorkBuddy 是否提供 Python 运行时仍为 `UNKNOWN`。
- 许可证：四个 0.1.1 候选均包含独立 MIT LICENSE，版权主体候选为 `wangbin`；授权意图和权利归属仍需本人确认，因此许可证门禁为 `REQUIRES_MANUAL_REVIEW`，不能标记为已授权发布。
- 内容与数据：示例 CSV/JSON 均为 fictional 示例；本轮审查未发现客户、企业或个人敏感数据，也未发现需要保留的第三方版权声明。

## 证据边界

- 本清单不把本地 pytest、ZIP 校验或公开文档当作 WorkBuddy 平台安装、真实对话、审核通过或正式发布证据。
- 生产数据、安装量、调用量、审核结果和成本没有证据时保持 `UNKNOWN`；未自动上传或提交审核。
