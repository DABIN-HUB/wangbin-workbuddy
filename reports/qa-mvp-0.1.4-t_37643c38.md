# 0.1.4 固定候选独立 QA / T03

- product_id: `wangbin-purchase-threeway-match`; task_id: `t_37643c38`; session_id: `local-6eb0e12a5c76f934a7ee7028c8b833d61c042c567d3d469bfe9b54d94be2a1d7`。直接 wb-quality Profile，不是开发者/Kanban Worker；未操作看板。
- workspace: `F:/ideaWorkSpace/wangbin-workbuddy-purchase-threeway-match`; branch: `skill/purchase-threeway-match`; base_commit: `48aef036fc226816a6c8818b099de48ca0963c99`; result_commit: 以本报告提交后的 `git rev-parse HEAD` 为准（commit 无法自含自身 SHA）。changed_files: **仅本报告**。artifacts: 本报告及独立 scratch `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa014-t37643c38-independent-r5/evidence.json`（含全部输入/输出 SHA、命令、stdout/stderr、行结果）；探针 `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa014_t37643c38_probe.py`。
- 结论：**0.1.4 固定 ZIP 已执行的本地业务 QA PASS；许可、相似性人工审查与 WorkBuddy 平台及发布 BLOCKED。** 绝不等同平台安装/对话/审核通过。`reports/qa-mvp-0.1.3-t_37643c38.md` 后段历史 A07 FAIL 保留，不覆盖旧版结论。冻结 `requirements.md`、`input-output-contract.md`、`acceptance-cases.md` 的 A01–A19 已重读；`reports/t03-a07-dev-checkpoint-t_e353c71a.md` 和 `reports/t03-0.1.4-candidate-t_e353c71a.md` 仅为线索，以下独立实测不借用开发 PASS。
- 预检 `git rev-parse HEAD`、`git branch --show-current`、`git diff --quiet`、`git diff --cached --quiet`：HEAD/branch 与指定值一致、tracked/index 均干净；六项已有未跟踪文件保持。`git worktree list --porcelain` 只在当前 worktree 登记该产品分支；禁止目录只读取 worktree 登记，未读取业务内容。`ps -ef | grep ...` 返回含 `Binary file (standard input) matches`，**不能据此证明进程无并发写者**；仅确认无同产品第二 worktree，仍保留并发不可证明风险。未 package、未修改 ZIP/源码/测试/历史报告/许可证，未 push。

## verification_commands / verification_results

所有命令在本 worktree 运行；shell 包裹 `printf` 的 exit=0 不替代各子命令退出码。Python `.venv/Scripts/python.exe` 3.11.15。

| 命令 | 实际子命令 exit | 观测 |
|---|---:|---|
| `sha256sum dist/wangbin-purchase-threeway-match-0.1.4-skill-candidate.zip dist/wangbin-purchase-threeway-match-0.1.4-skill-candidate.zip.sha256 dist/wangbin-purchase-threeway-match-0.1.4-skill-candidate.zip.manifest.json products/catalog.json` | 0 | 四个字节 SHA 见下节。 |
| `.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa014_t37643c38_probe.py` 首轮 | 1 | QA 探针误把 catalog `archive_evidence` 当 `.manifest.json`；尚未执行 CLI，非业务缺陷。 |
| 同探针第二轮 | 1 | QA 探针误算 payload snapshot（工厂输入是 `{"members": members}`），非包缺陷。 |
| 同探针第三轮 | 1 | QA 探针把 Excel 公式防护的 `'-2` 当作 JSON `-2` 错误；此前业务断言均通过，非包缺陷。 |
| 同探针第四轮 | 1 | QA 探针错误在预期拒绝 exit2 时返回 None；非产品缺陷。 |
| 同探针第五轮，全新 `...independent-r5` | **0** | `INTEGRITY_AND_ISOLATED_CASES_PASS`，19 次包内 CLI：14 次成功 + 5 次预期 exit2；每次命令/输入/输出 hash 见 evidence.json。先前失败 scratch 原样保留，不覆盖证据。 |
| `uv run --no-sync --offline --with pytest python -m pytest tests/test_purchase_threeway_acceptance.py tests/test_purchase_threeway_match.py -q --basetemp=C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa014-pytest --tb=short` | **0** | 44 passed, 1 skipped (Windows symlink privilege unavailable), 37.02s。**这是源码入口测试，不是包内测试。** |
| `.venv/Scripts/python.exe -m tooling.products validate --id wangbin-purchase-threeway-match` | **0** | PASS、findings=[]。 |
| `uv run --no-sync --offline --with pytest python -m tooling.products test --id wangbin-purchase-threeway-match` | **0** | PASS、内部 returncode=0、9 passed in 0.92s。 |
| `.venv/Scripts/python.exe -m tooling.products verify --id wangbin-purchase-threeway-match` | **0** | PASS，候选 SHA 与本报告相同。 |
| `uv run --no-sync --offline --with pytest python -m tooling.products release-check --id wangbin-purchase-threeway-match` | **1** | `BLOCKED`：本地候选/测试/归档 PASS；许可证缺失 BLOCKED；相似性 REVIEW_REQUIRED；platform_install/dialogue/review NOT_TESTED，publication BLOCKED。绝不改写为 PASS。 |

## 固定包实测完整性

`dist/wangbin-purchase-threeway-match-0.1.4-skill-candidate.zip` SHA-256=`a8fda7da724c4f64b4d83b8175dace0204dd3eb41d10087cfeb91dfd9ad242b7`；sidecar 文件 SHA=`c8b56dfa5d41d86e7670daed0cb7f40bb43257c31e14530b093d4bbcefda58a5`，文本为该 ZIP SHA + 双空格 + basename + LF；archive manifest 文件 SHA=`7eb5bce116f3b1c3f82c5e7da2d7b656be3d40d3d1a75e1d920e1b04747f1db2`；catalog SHA=`4a551afa96a85142f2be03c043fffa5d2e0e0ce9de66c8288c75b62bd69002a3`。Catalog active_version=0.1.4 且保留 0.1.0–0.1.3 条目；0.1.4 candidate/archive_evidence 指向同一 ZIP，SHA 相同。归档 manifest id/version/status/platform=`wangbin-purchase-threeway-match`/`0.1.4`/PASS/BLOCKED；成员快照规范 JSON SHA=`83fb2fb1060e8b8912f256b35fdf7c82fb9eaeee515404805560fbedb48fb73f`。ZipFile.testzip() 为 None；七成员路径无重复、无越界/符号链接，均与 manifest 声明大小及 hash 和对应工作区源文件字节相同；全新 scratch 解压后逐成员 hash 相同：

| 成员（前缀 `wangbin-purchase-threeway-match/`） | 字节 | SHA-256 |
|---|---:|---|
| `SKILL.md` | 3508 | `1e56f9331539c8f16a48045980ea53668371e0385d5fc931e864b2b84fbba111` |
| `examples/data/invoices.csv` | 211 | `c72c3dddc1897e24dabc2f12a77ca61b97eeec157dc047a0f0305b6550fa6c83` |
| `examples/data/po.csv` | 122 | `a40216b264646addad211e126747f25c300fe8c731e562205a3f969a3df2fd52` |
| `examples/data/receipts.csv` | 138 | `4076e7b505806d15441adc5bbbe023cb174b5f66601ef5e32ddff8582a48e67c` |
| `examples/manifest.json` | 465 | `418fceb5437b850326b6ea1935d40fdc873c01a9ec1bb465c19e33590426c630` |
| `manifest.json` | 179 | `8bcfe198f74993c6fe9f99db6d64191a71b78376fa41219e4d563dbf7363105b` |
| `scripts/threeway_match.py` | 23997 | `1080b6cceef262291023b0b3daddee23caed91c6c6671e68373e8e3bb8251eb3` |

## 独立包内入口

统一命令为 `.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa014-t37643c38-independent-r5/unpacked/wangbin-purchase-threeway-match/scripts/threeway_match.py --manifest <case>/manifest.json --output <case>/output`，cwd 是隔离 scratch case；完整逐条命令和三 CSV/XLSX 输入 SHA（before=after）、manifest SHA、三输出 SHA 在 `evidence.json`。所有成功场景均独立重读 summary.json、report.md 和 XLSX；七表顺序严格为 Match Summary / Line Results / Exceptions / Unmatched Receipts / Unmatched Invoices / Source Trace / Run Manifest；JSON 每个行字段与 Excel 对齐（负数 Excel 的安全前缀 `'` 单独识别），异常行数/状态/引用和 Markdown 相符；Run Manifest 0.1.4、输入文件哈希正确；每源行保留文件名/物理行号/64 位哈希。包内示例用解压后的 examples/manifest.json 和三个 CSV，exit0，1 key/1 matched/0 exception；示例原文件前后 SHA 相同。

| 新隔离输入（默认同键 P1/1/SKU，PO qty10 × USD5.00=50.00，receipt10 EA，invoice10 × USD5.00=50.00） | 包内 CLI exit 与观测 |
|---|---|
| A07 PO amount 空 | 0；expected_amount 50.00，DERIVED，MATCHED。 |
| A07 PO qty 空、PO amount 空，receipt/invoice 同键 qty10 | 0；key 保留，1 PO key、0 matched、2 exceptions=MISSING_REQUIRED_FIELD+NOT_COMPARABLE；expected_amount/source NOT_AVAILABLE，received/invoiced=10、两 unmatched 表为空、PO:2 和 receipt/invoice:2 来源齐全；无伪孤儿。 |
| A07 PO price 空、PO amount 空，receipt/invoice 同键 qty10 | 0；同样 1/0/2，expected_amount/source NOT_AVAILABLE，缺价保留追溯、receipt/invoice 非孤儿；两分支修复了旧版实际 FAIL。 |
| A12 PO USD 5×10=50，invoice CNY 70×10=700，receipt 无 currency | 0；1/0/2，仅 CURRENCY_MISMATCH/NOT_COMPARABLE；原币 CNY700.00 分桶，跨币 invoiced_amount/weighted price/amount_variance NOT_AVAILABLE，绝无伪 PRICE_MISMATCH；报告含 USD/CNY/700.00。 |
| A12 混币 USD5×5=25.00、CNY70×5 声称351.00，receipt11 | 0；1/0/4：QTY_OVER/CURRENCY_MISMATCH/NOT_COMPARABLE/AMOUNT_MISMATCH；USD25.00/CNY351.00 分桶，receipt variance=1；内部发票算术错误不冒充跨币价差，跨币金额/加权价 NOT_AVAILABLE。 |
| A12 单张 CNY70×10 声称701.00 | 0；CURRENCY_MISMATCH/NOT_COMPARABLE/AMOUNT_MISMATCH，跨币 amount_variance NOT_AVAILABLE。 |
| 完全未收货（receipt CSV 仅表头） | 0；0 matched、NOT_COMPARABLE，received_quantity NOT_AVAILABLE，不虚构 0。 |
| 部分收货 qty8 | 0；QTY_UNDER，非 MATCHED。 |
| 分批收货4+6、拆票3+7 | 0；累计收到/开票均10，MATCHED、0 exception，trace 五物理行；本次均在各自单 CSV 多行，跨文件拆分另由源码 pytest A03 覆盖。 |
| 部分开票 qty7/35.00 | 0；QTY_UNDER+AMOUNT_MISMATCH，invoice_variance=-3。 |
| 超量开票 qty11/55.00 | 0；QTY_OVER+AMOUNT_MISMATCH，invoice_variance=1。 |
| 三份具名 XLSX sheet=po/receipt/invoice，另有 ignored sheet | 0；MATCHED，三种 source_sheet 正确。 |
| CSV item_code `=CMD` | 0；MATCHED；Excel Source Trace 文本 `'=CMD`，不作为公式。 |
| batch max_batch_bytes=100 降限 | **2**，LIMIT_EXCEEDED，无 output；**不等于默认真实 200MiB 边界**。 |
| `../outside.csv`、`C:/outside.csv`、`bad.txt` 分别作为 PO path；以及 output=input_root | 四次各 **2**，INVALID_INPUT，无新 output，原输入未覆盖。 |

## A01–A19 冻结矩阵（输入、结果、证据来源严格区分）

“源码 pytest”表示本次实跑 `tests/test_purchase_threeway_acceptance.py`（其 `SCRIPT` 指向工作区源码），不是 ZIP 包内执行；具体测试名见该文件行号。包内证据为上述 r5/evidence.json 的 case 名。基准为 PO10/USD5/50、receipt10、invoice10/USD5/50，未列字段沿用基准。

| ID | 输入 → 结果 | 本次证据 / 状态 |
|---|---|---|
| A01 | 三 CSV 基准 → MATCHED、七表、0 差额 | 包内 `packaged-example`（包内示例数据）、源码 pytest `test_a01_csv_matched_seven_sheets_and_evidence`；PASS |
| A02 | 三 XLSX 具名 sheet 与 ignored sheet → MATCHED、来源 sheet 保留 | 包内 `xlsx-three-inputs` + 源码 pytest `test_a02_named_xlsx_sheets`；PASS |
| A03 | receipt4+6、invoice3+7 → 累计10/10、MATCHED | 包内 `split-receipt-invoice`（同文件多行）；跨文件源码 pytest `test_a03_split_receipts_and_invoices`；PASS |
| A04 | receipt8 → QTY_UNDER、非 MATCHED | 包内 `partial-receipt` + 源码 pytest `test_a04_under_receipt`；PASS |
| A05 | invoice 5.01/50.10，单价和金额容差0.01 → 仅 AMOUNT_MISMATCH、金额差0.10 | 源码 pytest `test_a05_inclusive_price_exclusive_amount`；PASS（未另做包内） |
| A06 | receipt8、invoice5.02/50.20，容差0.01 → QTY_UNDER/PRICE_MISMATCH/AMOUNT_MISMATCH | 源码 pytest `test_a06_quantity_price_amount_multi_exception`；PASS（未另做包内） |
| A07 | PO amount空 → DERIVED=50.00；PO qty空/price空与同键 receipt/invoice → key/source 保留、NOT_COMPARABLE、expected_amount NOT_AVAILABLE、非孤儿 | 包内 `a07-derived`/`a07-missing-ordered_quantity`/`a07-missing-po_unit_price` + 源码 pytest `test_a07_*`；PASS |
| A08 | 两 PO 同键 → DUPLICATE_PO_KEY，trace4，不算 matched | 源码 pytest `test_a08_duplicate_po_key`；PASS（未另做包内） |
| A09 | receipt item_code 空 → MISSING_REQUIRED_FIELD、unmatched 一行，非 AMBIGUOUS_KEY | 源码 pytest `test_a09_missing_receipt_key`；PASS（未另做包内） |
| A10 | invoice document+line 重复 → 两物理行保留、DUPLICATE_SOURCE_ROW 两来源 | 源码 pytest `test_a10_duplicate_invoice_document_line`；PASS（未另做包内） |
| A11 | invoice item_code 空 → MISSING_REQUIRED_FIELD、unmatched 一行、双语 cannot match | 源码 pytest `test_a11_missing_invoice_key`；PASS（未另做包内） |
| A12 | USD5×10=50 vs CNY70×10=700；混币+超收+单票内部金额异常 | 包内 `a12-cross`/`a12-mixed-over`/`a12-single-self` + 源码 pytest `test_a12_*`；PASS |
| A13 | receipt11、invoice11×6=66 → QTY_OVER 与 PRICE_MISMATCH 同行并分列例外 | 源码 pytest `test_a13_multi_exception_separate_rows`；PASS（未另做包内） |
| A14 | 无 PO、OTHER 收货+发票 → 两种孤儿，各 unmatched 一行 | 源码 pytest `test_a14_orphans`；PASS（未另做包内） |
| A15 | 相同有效数据两次运行 → JSON/status、汇总/trace 一致 | 源码 pytest `test_a15_deterministic_repeat`；PASS（未对包内重复运行） |
| A16 | traversal、绝对路径、扩展名、output=input → INVALID_INPUT exit2 且无新输出；symlink 权限不可用 | 包内 `path-*` 四组 + 源码 pytest `test_a16_reject_paths`；已运行子项 PASS，**symlink SKIP** |
| A17 | 降限100 bytes → LIMIT_EXCEEDED；真实 50MiB+1 单文件、51 个文件在源码 pytest → LIMIT_EXCEEDED | 包内 `limit-lowered` + 源码 pytest `test_a17_real_default_file_limit_and_file_count`；已运行子项 PASS，**真实默认总批量 200MiB NOT_TESTED** |
| A18 | CSV `=CMD` 安全文本化；XLSX 公式/ignored sheet公式、伪 macro/外链/外部关系 → INVALID_INPUT | 包内 `a18-csv-formula` + 源码 pytest `test_a18_reject_active_xlsx_with_traceable_error`；已运行子项 PASS，**真实 Office 宏执行/远程网络监听 NOT_TESTED** |
| A19 | invoice qty 空/abc、uom BOX → MISSING_REQUIRED_FIELD/INVALID_INPUT/UOM_MISMATCH，非 MATCHED | 源码 pytest `test_a19_missing_malformed_uom`；PASS（未另做包内） |

blocked_reason: release-check exit1、未具备本产品 LICENSE/可核实授权及依赖许可审核、相似性人工审查未完成，WorkBuddy 解析/安装/对话/审核/发布无证据。residual_risks / 每个未测：Windows symlink 权限子项 SKIP；默认真实总量 200MiB 边界 NOT_TESTED（降限模拟不能代替）；真实 Office 宏执行及远程网络访问监听 NOT_TESTED；其它 OS NOT_TESTED；不同订单日期/时序的专项 NOT_TESTED；许可证权利/依赖/平台条款 NOT_VERIFIED；WorkBuddy ZIP 平台解析、安装、对话、审核、上传/发布全部 NOT_TESTED/BLOCKED；进程层并发无强隔离证明。旧 0.1.0–0.1.3 候选与 QA FAIL 保持原状。只有本地已测范围 PASS，无发布许可。
