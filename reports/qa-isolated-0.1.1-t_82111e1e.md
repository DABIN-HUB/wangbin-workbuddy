# 独立 QA：0.1.1 固定候选（直接 Profile 会话）

- product_id: `wangbin-purchase-threeway-match`；task_id: `t_82111e1e`；version: `0.1.1`。
- 直接会话 ID: `local-8b74d8d7e31fbef633e2cd99544f90c03a6e0ecb83011bf7e62f14ccacbc676a`；不是 Kanban Worker/run，没有 Done 声明、后台任务、push 或发布。
- workspace: `F:/ideaWorkSpace/wangbin-workbuddy-purchase-threeway-match`；branch: `skill/purchase-threeway-match`；base_commit/result_commit（本轮未提交）: `587d3d5ec5f01cfeb68e30748a2e881c2afbe069`。先读取 `reports/qa-handoff-0.1.1-t_82111e1e.md`，后以 `git rev-parse HEAD` 实核同一提交。
- 固定候选: `F:/ideaWorkSpace/wangbin-workbuddy-purchase-threeway-match/dist/wangbin-purchase-threeway-match-0.1.1-skill-candidate.zip`；冻结 SHA-256: `664dcd9f3b30f6be4b40d21c6d14257085ef49dda2dbe049f3d01476a7b200c1`。
- 结论：**FAIL（A11 报告缺少冻结要求的“无法匹配 / cannot match”原因）；候选发布门禁 BLOCKED**。其余下列已执行项逐项如实列示，不将九个 pytest PASS 当成候选全部 PASS。

## 环境、命令和退出码

在上述 workspace，以已有 `.venv/Scripts/python.exe` 运行包内 `scripts/threeway_match.py`（Python 3.11.15、openpyxl 可用）。独立 QA 脚本仅写于 `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa011_probe.py`；隔离解压及实验输入/输出在同一 scratch 下 `qa011-isolated-8b74d8d7-c/`；没有以源码工作区入口替代包内入口。实验 manifest 的相对 `input_root` 均由包内 CLI 在另一 cwd 解析。

| 实际执行 | 退出码 | 实测结果 |
|---|---:|---|
| `git status --short && git branch --show-current && git rev-parse HEAD && git worktree list --porcelain && printf 'SESSION=%s\n' "$HERMES_SESSION_ID"` | 0 | 本产品分支与指定 HEAD；其他 worktree 仅由 git 登记识别，未读禁区业务内容。 |
| `.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa011_probe.py`（首轮） | 1 | QA 自身 openpyxl Workbook 非 context manager 用法错误，止于示例输出读取；**不算产品失败**。仅修复 scratch 探针。 |
| 同上（第二轮） | 1 | ZIP、示例、A05 成功；A11 冻结报告措辞断言真实失败，尚未执行 A12；只调整 scratch 探针，使已知缺陷被记录且继续后续用例，不修改断言期望。 |
| 同上（第三轮，完整链） | 1 | `ALL_PROBES_COMPLETED`；唯一记录失败为 A11 report 缺少必需 cannot-match reason；其余断言执行通过。以下所有示例/用例 CLI 退出码来自此轮真实 subprocess。 |
| `uv run --no-sync --offline --with pytest python -m pytest tests/test_purchase_threeway_match.py -q` | 0 | 独立运行 `9 passed in 0.89s`；现有测试未覆盖 A11 报告措辞，不以此覆盖失败。 |
| `sha256sum dist/wangbin-purchase-threeway-match-0.1.1-skill-candidate.zip dist/wangbin-purchase-threeway-match-0.1.0-skill-candidate.zip; git rev-parse HEAD; git status --short; printf 'SESSION=%s\n' "$HERMES_SESSION_ID"` | 0 | 0.1.1 SHA 与冻结值相同；旧 0.1.0 SHA `65c046f47c8d9e8d529d9afbd63c85f45e01797257ca7d82822c4d6836f96fff`；HEAD 不变。 |

### 包与历史输入

- ZIP `ZipFile.testzip() is None`；7 个唯一、安全的 `wangbin-purchase-threeway-match/` 前缀成员，成员集合、逐成员字节数和 SHA-256 对 `dist/*.zip.manifest.json` **全部一致**；`payload_snapshot_sha256` 对 manifest members 的规范 JSON 重新计算一致；解压后的 7 个文件再逐个读取核对 SHA 均一致。sidecar `.zip.sha256` 的 hash 与 ZIP 文件名精确匹配；catalog `products/catalog.json` 的 active_version=0.1.1、候选路径/hash 与 archive manifest 一致；包内 manifest id/version=指定值，`license_type=PROPRIETARY`、`license_status=REQUIRES_MANUAL_REVIEW`。
- 包内示例：入口 `.../qa011-isolated-8b74d8d7-c/unpacked/wangbin-purchase-threeway-match/scripts/threeway_match.py --manifest .../examples/manifest.json --output .../example-output`，退出 **0**；JSON `SUCCEEDED`、PO keys=1、matched=1、exceptions=0；重读 `report.md` 和 `threeway_match.xlsx`，工作表顺序严格为 `Match Summary`、`Line Results`、`Exceptions`、`Unmatched Receipts`、`Unmatched Invoices`、`Source Trace`、`Run Manifest`；对应数据行数 1/1/0/0/0/5/1；来源追溯是 `po.csv:2`、`receipts.csv:2,3`、`invoices.csv:2,3`，每行有文件名、物理行及行哈希。JSON/Markdown/Excel 计数一致。包内 `examples/data` 所有文件在运行前/后各按文件 SHA-256 快照比对，完全一致。
- 每项 A05/A11/A12 的 `historic-input` CSV 运行前/后按文件 SHA-256 快照完全一致；输出目录独立。额外以现有输入目录下的 `output` 作目标调用，包内 CLI 退出 **2**，stderr `{"run_status":"FAILED_INPUT","error_code":"INVALID_INPUT","message":"output root must be distinct"}`，输入哈希及文件集合不变。此安全验证只覆盖这里列出的路径/实例，不外推为所有输入边界已通过。

### 冻结规则独立复现

三用例均在 scratch 新建 manifest、CSV 和输出；使用固定键 `P1/1/SKU`，PO `10 × 5.00=50.00 USD EA`，收货 `10 EA`，完整输入均有文件名/行号。每次包内入口真实退出 **0**；每次重新读取三种输出、七表顺序，核对 JSON/Exceptions 行数、matched/Match Summary 行数、报告可读性；三表源行在 `Source Trace` 都是物理行 2。详情见 scratch 中每用例 `manifest.json`、`historic-input/*.csv`、`output/{summary.json,report.md,threeway_match.xlsx}`。

| 用例 | 输入差异 | 期望 / 实际 | 判定 |
|---|---|---|---|
| A05 | invoice qty 10，price 5.01，amount 50.10；price tolerance 0.01、amount tolerance 0.01 | 价格差恰为 0.01 不标 `PRICE_MISMATCH`；金额差 0.10 超容差。实际 `amount_variance=0.10`、`AMOUNT_MISMATCH`、matched=0、exceptions=1、结果状态 AMOUNT_MISMATCH。 | PASS |
| A11 | invoice `item_code` 空，invoice_number=INV1，line=1；不配置部分键搜索 | 实际仅一条 `Unmatched Invoices`：`MISSING_REQUIRED_FIELD`，`Source Trace invoice.csv:2` 对应相同 hash，Exceptions 有 `invoice.csv:2`，没有 `AMBIGUOUS_KEY`，matched=0；PO 因无可用发票另有 `NOT_COMPARABLE`，总 exceptions=2。**但是 report.md 没有“无法匹配”也没有“cannot match”。** | **FAIL（详下）** |
| A12 | invoice currency=CNY，PO=USD；receipt 无 currency 字段 | 实际 `CURRENCY_MISMATCH;NOT_COMPARABLE`、matched=0、exceptions=2；PO/发票货币留在来源输入，PO 汇总 USD，三源行追溯保留。未要求 receipt currency 或汇率配置。 | PASS（下列残余风险） |

### 阻断缺陷：A11 报告缺失必需原因

复现：在 `qa011-isolated-8b74d8d7-c/a11/historic-input/` 使用如上 PO、receipt、`invoice.csv:2`（`item_code` 为空），从新解压包入口运行：
`<项目 .venv/Scripts/python.exe> <scratch>/unpacked/wangbin-purchase-threeway-match/scripts/threeway_match.py --manifest <scratch>/a11/manifest.json --output <scratch>/a11/output`。
实际进程 exit **0**，JSON `SUCCEEDED_WITH_EXCEPTIONS`；unmatched invoice 和 trace 正确保留一次，Exceptions 有 `MISSING_REQUIRED_FIELD` + `NOT_COMPARABLE`；但重读 `<scratch>/a11/output/report.md`，不含 `无法匹配` 或 `cannot match`。预期按 `acceptance-cases.md:17`：明确报告原因 `无法匹配 / cannot match`，同时不推断候选。包内脚本的报告组装见 `packages/skills/wangbin-purchase-threeway-match/scripts/threeway_match.py:206-235`（此处用于定位，运行依据是已核哈希的包内脚本）。**需要产品经理转交开发修复，再由独立 QA 以新固定候选复验；本轮不改业务源码或测试预期。**

### 门禁与剩余风险

- `LOCAL_ARCHIVE_INTEGRITY=PASS`；`BUNDLED_EXAMPLE=PASS`；`A05=PASS`；`A11=FAIL`；`A12=PASS`；`HISTORICAL_INPUTS_TESTED=PASS`；`RELEASE_VERDICT=BLOCKED`（A11 产品缺陷及下面外部门禁）。
- A12 虽有 NOT_COMPARABLE，输出仍显示 `amount_variance=0.00`、`weighted_invoice_unit_price=5.00`，未做汇率换算；这些跨币种数值存在误读风险，需产品经理评估是否还应置为 `NOT_AVAILABLE`，本轮没有将未明确冻结的行为假称另一个通过/失败。
- ZIP 中没有 `LICENSE` 成员，只有 manifest 的 proprietary/manual-review 声明；授权、依赖权利、平台协议与许可证审核 `NOT_TESTED/BLOCKED`。WorkBuddy 实际安装/调用、平台审核/上传/上架和 Linux/macOS 运行均 `NOT_TESTED`。无发布或付款批准证明。
- 本轮只检查上述目标用例、包内示例与一个输出覆盖边界；A01–A19 全矩阵（除已明确列出的 A05/A11/A12）、其它安全边界及真实平台运行不能推断为 PASS。没有重建/更改 ZIP、sidecar、catalog、`uv.lock`、旧 QA 或生产代码。
- changed_files: `reports/qa-isolated-0.1.1-t_82111e1e.md`（仅新报告）；artifacts: 本报告和上文 scratch 隔离输出（scratch 会被清理）；blocked_reason: `A11 报告措辞冻结规则失败；许可证手动审核和 WorkBuddy 平台验证尚未进行`。
