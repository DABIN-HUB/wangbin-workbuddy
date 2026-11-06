# A12 开发检查点（直接 Profile，会话非 Kanban Worker）

- product_id: `wangbin-purchase-threeway-match`; task_id: `t_e353c71a`; workspace: `F:/ideaWorkSpace/wangbin-workbuddy-purchase-threeway-match`; branch: `skill/purchase-threeway-match`; original_base_commit: `2374cc753300e3d18d809723bd3314dbf4b805bd`; 本轮 base_commit: `111ba52f4597e319b629e707589e0e99da8a37fc`；result_commit: 见提交输出（不能在自身提交中预写自身哈希）。
- 前次 session_id: `local-6b6da1c6b51ecf29ad470073da839dce266933f7aff7e9f0b681aa9510ae4777`。新会话开始 git status 确认前次脚本、测试、报告已在 `111ba52` 提交，已无未提交 diff；worktree 列表显示本产品仅此分支工作树，进程检查未发现其他本产品写者。原有六项未跟踪（五份旧 QA 文件、uv.lock）不暂存。
- 原始开发边界参考 `reports/t03-fix3-direct-t_b8b08bb8.md`、`reports/t03-pkg-recovery-t_b9121c8a.md`；冻结合同、A01–A19 及独立 `reports/qa-isolated-0.1.2-t_a085c1f1.md` 均已阅读。使用 QA 原始 `.../wb-quality/cache/scratch/qa012-t_a085c1f1-r2/a12/manifest.json` 只读输入先复现：CLI exit 0，JSON 的 `AMOUNT_MISMATCH, CURRENCY_MISMATCH, NOT_COMPARABLE, PRICE_MISMATCH` 各 1，属 FAIL。
- 修复源码后对相同 QA 输入用源码 CLI、独立开发 scratch `a12-dev-after-original` 运行：exit 0，`summary.json` 为 `SUCCEEDED_WITH_EXCEPTIONS`、matched=0、exceptions=2，只有 `CURRENCY_MISMATCH` 与 `NOT_COMPARABLE`；`invoiced_amount`, `amount_variance`, `weighted_invoice_unit_price` 均 `NOT_AVAILABLE`，保留 PO `USD/50.00`、invoice `CNY/700.00`，数量两侧 10/差额 0。报告含双语币种不可比说明。开发输出不是独立 QA/新候选。
- 本轮只改源码及本产品专项测试：原币种分类金额及追溯行保留，混币不合计、不加权，不跨币种产生价格/金额差；数量独立检查，发票自身金额算术仍核验；额外限制配置不得提升默认限额，批次限额在读取前检查。**没有**变更 metadata、catalog、旧候选或发布 ZIP；没有 push。

## 开发侧 A01–A19 矩阵（当前证据，不是正式冻结结论）

最终命令：`uv run --no-sync --offline --with pytest python -m pytest tests/test_purchase_threeway_acceptance.py tests/test_purchase_threeway_match.py -q --basetemp=C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/a12-checkpoint-final2 --tb=short`，exit **0**，`42 passed, 1 skipped in 38.79s`。测试输入由 `tests/test_purchase_threeway_acceptance.py` 的 `po/receipt/invoice` CSV/XLSX fixture 生成，子进程调用真实 CLI，核 JSON、Excel、Markdown、输入哈希与追溯；所有新增用例均已在最终命令复跑。工厂 `uv run --no-sync --offline --with pytest python -m tooling.products test --id wangbin-purchase-threeway-match` exit 0、PASS、`9 passed in 1.17s`；同解释器 `python -m tooling.products validate --id wangbin-purchase-threeway-match` exit 0、PASS、findings=[]。均为本地测试，不等于独立 QA。

| Case | 实际输入；测试函数及关键断言 | 最终状态 |
|---|---|---|
| A01 | CSV 10/10/10、七表、追溯与零差额；`test_a01_csv_matched_seven_sheets_and_evidence` | PASS |
| A02 | 三份多工作表 XLSX 显式命名，matched=1、sheet 追溯；`test_a02_named_xlsx_sheets` | PASS |
| A03 | 两文件 4+6 收货、3+7 发票，五行 trace，matched=1；`test_a03_split_receipts_and_invoices` | PASS |
| A04 | 收货 8，QTY_UNDER；`test_a04_under_receipt` | PASS |
| A05 | 5.01/50.10，价格容差 0.01，金额差 0.10 报 AMOUNT_MISMATCH；`test_a05_inclusive_price_exclusive_amount` | PASS |
| A06 | 收货 8、发票 5.02/50.20，数量/价格/金额三异常；`test_a06_quantity_price_amount_multi_exception` | PASS |
| A07 | PO 金额空，DERIVED/50.00；`test_a07_derived_po_amount` | PASS |
| A08 | 重复 PO 键，DUPLICATE_PO_KEY，两物理行保留；`test_a08_duplicate_po_key` | PASS |
| A09 | 收货缺 item_code，MISSING_REQUIRED_FIELD、未匹配收货一行；`test_a09_missing_receipt_key` | PASS |
| A10 | 同一发票标识两行，重复码分别关联 :2/:3；`test_a10_duplicate_invoice_document_line` | PASS |
| A11 | 发票缺 item_code，未匹配一次、双语无法匹配；`test_a11_missing_invoice_key` | PASS |
| A12 | USD/CNY 原始 QA 同形输入、USD+CNY 混币超收及 CNY 发票自身 351≠5×70、空发票、BOX 单位、CNY 内部 701≠10×70、缺价排除；`test_a12_qa_original_currency_and_quantity`, `test_a12_mixed_currency_and_self_check_and_quantity`, `test_a12_absent_invoice_and_incompatible_uom_have_no_monetary_variance`, `test_a12_invoice_internal_arithmetic_only_on_complete_invoice_row`；跨币种/不同 UOM 无伪差，内部同单位同单价算术仍告警 | PASS（内部发票 qty 与单价同一发票行口径） |
| A13 | 超收 11、发票价 6，QTY_OVER+PRICE_MISMATCH 多异常行；`test_a13_multi_exception_separate_rows` | PASS |
| A14 | 孤立收货与发票各一，未匹配表/例外分别记录；`test_a14_orphans` | PASS |
| A15 | 相同 CSV 两次运行，JSON、行、来源追溯一致；`test_a15_deterministic_repeat` | PASS |
| A16 | 遍历、绝对路径、扩展名、输出根同输入根拒绝；`test_a16_reject_paths[../outside.csv,/outside.csv,bad.txt,same_root]` PASS；`test_a16_reject_paths[symlink]` SKIP（Windows symlink privilege unavailable） | SKIP（symlink 子项）；其他 PASS |
| A17 | `test_a17_file_limit` 配置降低为 1 byte，模拟门禁 PASS；`test_a17_real_default_file_limit_and_file_count` 真正 50 MiB+1 byte 和同 CSV 51 次文件引用均拒绝且未产生输出 PASS；真实 >200 MiB 聚合字节量 NOT_TESTED | PASS（文件与 50 files）；200 MiB NOT_TESTED |
| A18 | `test_a18_formula_text_injection` CSV `=CMD` 导出文本；`test_a18_reject_active_xlsx_with_traceable_error` 原 XLSX 修改为公式（含 ignored sheet）、加入宏条目、外链条目、外部关系，全部拒绝并给文件名/INVALID_INPUT、无输出；真实 Office 宏执行与远端访问监测 NOT_TESTED | PASS（静态拒绝）；运行时无执行/网络监听 NOT_TESTED |
| A19 | 空数量、坏小数、UOM BOX 不 MATCHED；`test_a19_missing_malformed_uom` 三参数 | PASS |

- changed_files: `packages/skills/wangbin-purchase-threeway-match/scripts/threeway_match.py`, `tests/test_purchase_threeway_acceptance.py`, 本报告。artifacts: 本报告、隔离 scratch 运行输出（非正式候选）。verification_commands/results: 见上述最终专项与工厂命令，均 exit 0；未修改元数据、原 0.1.2 ZIP/候选，不打 0.1.3、不 push。
- blocked_reason: 发布仍需独立 QA、许可证授权和平台实测；A16 symlink 子项 SKIP。residual_risks: A17 真实 200 MiB 聚合 NOT_TESTED；A18 静态构造的 XLSX 危险容器非真实 Office 样本，网络监测 NOT_TESTED；XLSX 其他容器边界、全合同强度及其他 OS NOT_TESTED。测试通过不代表 WorkBuddy 审核或付款批准。
