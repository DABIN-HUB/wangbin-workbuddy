# A12 开发检查点（直接 Profile，会话非 Kanban Worker）

- product_id: `wangbin-purchase-threeway-match`; task_id: `t_e353c71a`; workspace: `F:/ideaWorkSpace/wangbin-workbuddy-purchase-threeway-match`; branch: `skill/purchase-threeway-match`; base_commit: `2374cc753300e3d18d809723bd3314dbf4b805bd`；result_commit: 见直接会话终端交接（提交本文件时不能预写自身哈希）。
- session_id: `local-6b6da1c6b51ecf29ad470073da839dce266933f7aff7e9f0b681aa9510ae4777`。worktree 列表显示本产品仅此独占分支工作树；未发现其他本产品写入进程。原有六项未跟踪（五份旧 QA 文件、uv.lock）均未暂存。
- 原始开发边界参考 `reports/t03-fix3-direct-t_b8b08bb8.md`、`reports/t03-pkg-recovery-t_b9121c8a.md`；冻结合同、A01–A19 及独立 `reports/qa-isolated-0.1.2-t_a085c1f1.md` 均已阅读。使用 QA 原始 `.../wb-quality/cache/scratch/qa012-t_a085c1f1-r2/a12/manifest.json` 只读输入先复现：CLI exit 0，JSON 的 `AMOUNT_MISMATCH, CURRENCY_MISMATCH, NOT_COMPARABLE, PRICE_MISMATCH` 各 1，属 FAIL。
- 修复源码后对相同 QA 输入用源码 CLI、独立开发 scratch `a12-dev-after-original` 运行：exit 0，`summary.json` 为 `SUCCEEDED_WITH_EXCEPTIONS`、matched=0、exceptions=2，只有 `CURRENCY_MISMATCH` 与 `NOT_COMPARABLE`；`invoiced_amount`, `amount_variance`, `weighted_invoice_unit_price` 均 `NOT_AVAILABLE`，保留 PO `USD/50.00`、invoice `CNY/700.00`，数量两侧 10/差额 0。报告含双语币种不可比说明。开发输出不是独立 QA/新候选。
- 本轮只改源码及本产品专项测试：原币种分类金额及追溯行保留，混币不合计、不加权，不跨币种产生价格/金额差；数量独立检查，发票自身金额算术仍核验；额外限制配置不得提升默认限额，批次限额在读取前检查。**没有**变更 metadata、catalog、旧候选或发布 ZIP；没有 push。

## 开发侧 A01–A19 矩阵（当前证据，不是正式冻结结论）

命令：`uv run --no-sync --offline --with pytest python -m pytest tests/test_purchase_threeway_match.py tests/test_purchase_threeway_acceptance.py -q --tb=short --basetemp=C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/a12-matrix-r2`，exit **1**，实际 `1 failed, 33 passed, 1 skipped in 22.58s`。测试输入由 `tests/test_purchase_threeway_acceptance.py` 的 `po/receipt/invoice` CSV/XLSX fixture 生成，子进程调用真实 CLI，各成功运行重新读 JSON、七表 Excel 与 Markdown，核输入哈希、行追溯和 Run Manifest；测试基目录为上述隔离 scratch。前一轮同脚本 `-q` exit 1、`25 failed,10 passed`，原因主要为测试对 Excel 空格值的错误归一化，已修正，未改动冻结断言。矩阵记录为该次运行观察；后续限额前置检查增量尚未重跑，不能据此称所有测试 PASS。

| Case | 输入/实测关键输出 | 本轮状态 |
|---|---|---|
| A01 | CSV 10/10/10、七表、追溯，断言把数值零字符串 `0` 错定为 `0.00` | FAIL（测试断言已修正但未重跑） |
| A02 | 三份多工作表 XLSX 显式命名，matched=1、sheet 追溯 | PASS |
| A03 | 两文件 4+6 收货、3+7 发票，五行 trace，matched=1 | PASS |
| A04 | 收货 8，QTY_UNDER | PASS |
| A05 | 5.01/50.10，价格容差 0.01，金额差 0.10 报 AMOUNT_MISMATCH | PASS |
| A06 | 收货 8、发票 5.02/50.20，数量/价格/金额三异常 | PASS |
| A07 | PO 金额空，DERIVED/50.00 | PASS |
| A08 | 重复 PO 键，DUPLICATE_PO_KEY，两物理行保留 | PASS |
| A09 | 收货缺 item_code，MISSING_REQUIRED_FIELD、未匹配收货一行 | PASS |
| A10 | 同一发票标识两行，重复码分别关联 :2/:3 | PASS |
| A11 | 发票缺 item_code，未匹配一次、双语无法匹配 | PASS |
| A12 | USD/CNY QA 同形 fixture，无伪差；混合 USD/CNY+数量超收+发票自身金额错误亦核验 | PASS（且 QA 原始输入源码 CLI exit 0，细节见上） |
| A13 | 超收、发票错价，QTY_OVER+PRICE_MISMATCH 多异常行 | PASS |
| A14 | 孤立收货与发票各一，未匹配表/例外分别记录 | PASS |
| A15 | 相同 CSV 两次运行，JSON、行、来源追溯一致 | PASS |
| A16 | 遍历、绝对路径、扩展名、输出根同输入根均拒绝；Windows 缺创建 symlink 权限 | PARTIAL（4 PASS，symlink SKIPPED） |
| A17 | 通过降低单文件限额到 1 byte 测 LIMIT_EXCEEDED | PARTIAL（默认 50 MiB+1、批次 200 MiB/50 files 尚 NOT_TESTED） |
| A18 | CSV 类似公式前缀文本化并检查 Excel 非公式 | PARTIAL（XLSX 内嵌公式/宏/外链 NOT_TESTED） |
| A19 | 空数量、坏小数、UOM BOX 不 MATCHED | PASS |

- changed_files: `packages/skills/wangbin-purchase-threeway-match/scripts/threeway_match.py`, `tests/test_purchase_threeway_acceptance.py`, 本报告。artifacts: 本报告及开发 scratch 运行输出（非正式候选）。verification_commands/results: QA 源码复现与修复后 CLI 均 exit 0、其结果见上；专项 pytest 第二轮 exit 1；`git diff --check` 在限额修补前 exit 0；限额修补后完整复测 NOT_TESTED。
- blocked_reason: 矩阵未全 PASS（A01 修复后待跑、A16 symlink 权限、A17 默认边界、A18 XLSX 危险容器均需进一步真实核验）。residual_risks: XLSX 容器安全/输出失败状态/未实施的完整合同边界、独立 QA、许可证人工审核与平台实测均未通过。不得建议冻结 0.1.3。保留旧 ZIP、QA 记录、原未跟踪文件；不声明 Kanban Done。
