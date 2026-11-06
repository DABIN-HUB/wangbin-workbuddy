# 0.1.3 固定候选独立 QA / T03

- product_id: `wangbin-purchase-threeway-match`; task_id: `t_37643c38`（复用卡号；本次是直接 wb-quality Profile 会话，非 Kanban Worker，没有操作卡片生命周期）。
- workspace: `F:/ideaWorkSpace/wangbin-workbuddy-purchase-threeway-match`; branch: `skill/purchase-threeway-match`; base_commit = result_commit = `b2e9c8030fe4ef323bf7637d50075cef795c7a1e`（报告未提交）。changed_files: 仅新增 `reports/qa-mvp-0.1.3-t_37643c38.md`；原有六个未跟踪项保持原状。
- **结论：0.1.3 固定 ZIP 的本地完整性和本次独立核心业务复验 PASS；发布/平台门禁 BLOCKED。** 0.1.2 的 `reports/qa-isolated-0.1.2-t_a085c1f1.md` 是历史 FAIL，不修改、不将其改判为 PASS；本次新版本单独验收。冻结的 `requirements.md`、`input-output-contract.md`、`acceptance-cases.md` 与上述历史 QA、`reports/t03-a12-dev-checkpoint-t_e353c71a.md`、`reports/t03-0.1.3-candidate-t_e353c71a.md` 均已读取；开发记录仅作线索，下面结果来自独立重跑。
- 独占核验：`git worktree list --porcelain` 仅见本产品当前 worktree 绑定该产品分支；另一个 `wangbin-workbuddy-dev` 仅看 Git worktree 登记，**未读取其业务文件**。`git status --short` 无已跟踪产品文件 diff；`ps -ef` 按 threeway_match/tooling.products/pytest/purchase013 检索未见其他产品写进程（自身 Hermes 命令包含关键词，不算并发写者）。这只是可观察时点检查，不是 OS 隔离保证。

## verification_commands / verification_results（产品根目录，退出码逐项记录）

| 命令 | exit | 实测重要结果 |
|---|---:|---|
| `git status --short --branch && git rev-parse HEAD && git worktree list --porcelain && git log -1 --format='%H %s'` | 0 | 分支 `skill/purchase-threeway-match`，HEAD `b2e9c8030fe4ef323bf7637d50075cef795c7a1e`；六项既有未跟踪项。 |
| `ps -ef ...; git status --porcelain=v1; git diff -- packages/skills/wangbin-purchase-threeway-match products/catalog.json tests/test_purchase_threeway_acceptance.py tests/test_purchase_threeway_match.py; .venv/Scripts/python.exe --version; uv --version` | 0 | 产品 diff 空；Python `3.11.15`、uv `0.12.9`；未见并发产品写进程。 |
| `uv run --no-sync --offline --with pytest python -m pytest tests/test_purchase_threeway_acceptance.py tests/test_purchase_threeway_match.py -q --basetemp=C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/purchase013-qa-pytest --tb=short` | 0 | **42 passed, 1 skipped in 32.77s**；SKIP 为 Windows symlink privilege unavailable。项目根执行；离线 overlay，不同步 `uv.lock`。这些测试调用源码脚本，不能代替包内入口实测。 |
| `.venv/Scripts/python.exe -m tooling.products validate --id wangbin-purchase-threeway-match` | 0 | `PASS`, `findings=[]`。 |
| `uv run --no-sync --offline --with pytest python -m tooling.products test --id wangbin-purchase-threeway-match` | 0 | `PASS`, returncode 0，`9 passed in 0.88s`。 |
| `.venv/Scripts/python.exe -m tooling.products verify --id wangbin-purchase-threeway-match` | 0 | `PASS`，登记 ZIP SHA `e2c3b6cf0fa0d506a91a9ec6096514af0808c2ee4434044cb5bdba92e5ddde90`。 |
| `uv run --no-sync --offline --with pytest python -m tooling.products release-check --id wangbin-purchase-threeway-match` | **1** | `BLOCKED`；其中 local_candidate/local_tests/archive PASS，license_and_dependencies BLOCKED（无 LICENSE）、similarity_audit REVIEW_REQUIRED；platform_install/dialogue/review NOT_TESTED、publication BLOCKED。外层 for 循环最终 shell exit 0，逐命令标记 `FACTORY_release-check_EXIT=1`，不能混淆。 |
| `.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa013_probe_t37643c38.py` 首轮 | **1** | QA scratch 探针自身错误使用紧凑 JSON 散列重算工厂快照，止于归档快照断言；非候选缺陷。核对工厂 `_dump` 的 `ensure_ascii=False, indent=2, sort_keys=True` + LF 后只修改 scratch 探针，新隔离目录重跑。 |
| 同一探针，第二轮 | **0** | `INTEGRITY_AND_ISOLATED_CASES_PASS`；7 成员字节哈希/大小及归档快照、sidecar、catalog、隔离解压、四次包内 CLI/三种输出独立断言均通过。运行目录 `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa013-t37643c38-isolated-r2/`；探针为同级 `qa013_probe_t37643c38.py`。 |
| `sha256sum dist/wangbin-purchase-threeway-match-0.1.3-skill-candidate.zip; git rev-parse HEAD; git status --short` | 0 | ZIP 指定 SHA 一致，HEAD 未变；原有未跟踪项保持（报告新增后另行复核）。 |

## 独立 ZIP/许可证核对

对 `dist/wangbin-purchase-threeway-match-0.1.3-skill-candidate.zip` 实算 SHA-256=`e2c3b6cf0fa0d506a91a9ec6096514af0808c2ee4434044cb5bdba92e5ddde90`；sidecar 文件字节 SHA=`474c12841a8d0f17f2af62808fc4ce160d4ddc1485aa68bd888d23f8445e74e2`，内容严格是 ZIP SHA + 双空格 + basename + LF；archive manifest 文件 SHA=`8688d9b8165b5727d9ea4afeaf0ad6c752b5335ea813f0b04a061f4c2815b1bc`；catalog SHA=`5089c09e65bb45ddc959ee6378d14db48183a0eae4233b4e07c02070312fbc1c`。Catalog 本产品 active_version 0.1.3、新条目 candidate/archive_evidence/sha256 对齐，归档 manifest id/version/status=PASS/platform=BLOCKED 对齐。`ZipFile.testzip() is None`，7 个路径互异且位于产品目录，未见越界/符号链接成员；工厂 JSON 规范编码的 members 快照 SHA=`5a6f0df313487f59fa5fd9fb7dca189ec81296b3b926bf2e565ef07a5d4a40d9` 与 manifest 一致。每个成员先比较归档声明，再比较工作区相应源文件原始字节、隔离解压后的字节：

| 成员（均以 `wangbin-purchase-threeway-match/` 为前缀） | bytes | 独立 SHA-256 |
|---|---:|---|
| `SKILL.md` | 3508 | `d2e2b5d7122075ed3cde8a892c50045a5679cef7bd92f68304f4bfe72dbcbfa1` |
| `examples/data/invoices.csv` | 211 | `c72c3dddc1897e24dabc2f12a77ca61b97eeec157dc047a0f0305b6550fa6c83` |
| `examples/data/po.csv` | 122 | `a40216b264646addad211e126747f25c300fe8c731e562205a3f969a3df2fd52` |
| `examples/data/receipts.csv` | 138 | `4076e7b505806d15441adc5bbbe023cb174b5f66601ef5e32ddff8582a48e67c` |
| `examples/manifest.json` | 465 | `418fceb5437b850326b6ea1935d40fdc873c01a9ec1bb465c19e33590426c630` |
| `manifest.json` | 179 | `7c62cb86b0fcd87613810320325c1103df62fdd0d9d2aa248fcfa10d1bcd07c1` |
| `scripts/threeway_match.py` | 23212 | `fd1a681eb8ace9d0190284aceb6a873b39268a507302113d357824778c25334f` |

包内 manifest 声称 `PROPRIETARY`、`REQUIRES_MANUAL_REVIEW`；ZIP 无独立 LICENSE 文件。许可证权利/依赖/平台协议未由 QA 证实，**不能用 ZIP 完整性或元数据声明代替许可审核**。

## 隔离包内真实入口与财务断言

所有独立 CLI 均由 `.venv/Scripts/python.exe <scratch>/qa013-t37643c38-isolated-r2/unpacked/wangbin-purchase-threeway-match/scripts/threeway_match.py --manifest <case>/manifest.json --output <case>-output` 调用，工作 cwd 为独立 scratch；四次各 exit 0、stderr 空。包内示例直接使用解压 `examples/manifest.json`/包内 3 CSV。其他三组各自独立 `historic-input/{po,receipts,invoices}.csv`，manifest 相对指向历史输入，输出为新建隔离目录；前后输入 SHA 集合完全相同，Excel Run Manifest 的实际 SHA 与前值一致。CSV 的 receipt 表只有 `po_number,po_line_id,item_code,receipt_number,receipt_line_id,received_quantity,uom`，**没有 currency**。每组重读 `summary.json`、`report.md`、`threeway_match.xlsx`；七表严格顺序为 Match Summary、Line Results、Exceptions、Unmatched Receipts、Unmatched Invoices、Source Trace、Run Manifest；JSON 与 Excel 每行状态/数量/币种/币种分桶/金额/差额/例外一致，Excel Exceptions 实际行数等于 JSON 计数；Markdown 状态、引用及币种解释逐一核验。Run Manifest version=0.1.3，Source Trace 行数与输入行数相符且物理行号、来源文件、64 位行哈希俱全。

| 场景及真实输入（共同 PO P1/1/SKU qty10 × USD5.00、PO amount USD50.00, UOM EA） | 实际 JSON/Excel/Markdown | QA |
|---|---|---|
| 包内样例：包内 PO/receipt/invoice CSV，共 5 行来源 | `SUCCEEDED`；po_keys=1/matched=1/exceptions=0；Match Summary MATCHED，received=10/invoiced=10，amount=50.00，variance=0.00，weighted=5.00；trace=5，报告状态 SUCCEEDED | PASS |
| A12：receipt R1 qty10 EA 无 currency；invoice I1 qty10 × CNY70.00，原币金额 CNY700.00（各输入物理行2） | `SUCCEEDED_WITH_EXCEPTIONS`、1/0/2；例外**仅** CURRENCY_MISMATCH、NOT_COMPARABLE，Excel 汇总 PO USD、invoice CNY，`invoice_amounts_by_currency={"CNY":"700.00"}`；`invoiced_amount/amount_variance/weighted_invoice_unit_price` 全为 NOT_AVAILABLE，绝无伪 PRICE_MISMATCH/AMOUNT_MISMATCH。Source Trace invoice:2 原 `currency=CNY, invoice_amount=700.00`、receipt:2 无 currency；报告含 USD/CNY/700.00 和“币种不可比”。 | PASS（历史 0.1.2 的跨币种伪差缺陷在此候选未复现） |
| 混币+数量超收+发票自身错误：receipt qty11；invoice I1 USD qty5 ×5.00=25.00，I2 CNY qty5 ×70.00 声称 351.00（应为350.00） | `SUCCEEDED_WITH_EXCEPTIONS`、1/0/4；QTY_OVER、CURRENCY_MISMATCH、NOT_COMPARABLE、AMOUNT_MISMATCH 各1；receipt_variance=1、invoiced_qty=10。USD 25.00/CNY 351.00 分桶和 invoice:2/:3 来源保留；合计金额/加权价/跨币金额差均 NOT_AVAILABLE，**无 PRICE_MISMATCH**。AMOUNT_MISMATCH 是 CNY 发票内部 `351≠5×70`，不是 CNY-USD 差。 | PASS |
| 单一 CNY 发票内部错误：receipt10、invoice qty10 × CNY70.00 申报 CNY701.00 | 异常仅 CURRENCY_MISMATCH、NOT_COMPARABLE、AMOUNT_MISMATCH；跨币 `amount_variance=NOT_AVAILABLE`，无 PRICE_MISMATCH；原币 CNY701.00 保留。 | PASS |

## A01–A19 独立实测矩阵

下列 A01–A19 由上述离线专项 pytest 在本会话产品根**实际运行**；除 A12/样例额外使用上面隔离包内 CLI 外，矩阵其余行执行的是源码 CLI 的 `tests/test_purchase_threeway_acceptance.py`（`run()` 生成 CSV/XLSX、调用子进程、重读三种输出/来源哈希），并不冒称每个情景都对 ZIP 单独运行。共享基准 PO qty10/USD5.00/50.00，receipt qty10 EA，invoice qty10/USD5.00/50.00；每行所列差异覆盖默认值。`tests/test_purchase_threeway_match.py` 随同运行，合计 42 passed/1 skipped。

| ID | 本轮真实输入和关键观测 | 状态 |
|---|---|---|
| A01 | 基准三 CSV；MATCHED，三数量一致，差额零；七表、trace=3、JSON/Excel/Markdown | PASS |
| A02 | PO/receipt/invoice 各 XLSX，显式 sheet=`po/receipt/invoice`，另有 ignored sheet；MATCHED，三个 sheet 名留痕 | PASS |
| A03 | 两 receipt CSV qty 4+6、两 invoice CSV qty 3+7，trace=5，累计 received/invoiced=10、MATCHED | PASS |
| A04 | receipt qty8，QTY_UNDER，非 MATCHED | PASS |
| A05 | invoice price5.01/amount50.10；价、金额容差均 0.01；仅 AMOUNT_MISMATCH，差额0.10 | PASS |
| A06 | receipt qty8、invoice price5.02/amount50.20、价/金额容差0.01；QTY_UNDER + PRICE_MISMATCH + AMOUNT_MISMATCH、金额差0.20 | PASS |
| A07 | PO amount 空；expected_amount=50.00 且 `expected_amount_source=DERIVED`；缺 qty/price 的另一分支未独立直接构造 | PASS（派生分支）；另一分支 NOT_TESTED |
| A08 | 两个 PO 同一完整键；DUPLICATE_PO_KEY，trace 留两行、matched=0 | PASS |
| A09 | receipt item_code 空；MISSING_REQUIRED_FIELD=1、无 AMBIGUOUS_KEY、unmatched receipt=1/trace=3 | PASS |
| A10 | 两个相同 invoice doc/line；invoiced_qty=20，DUPLICATE_SOURCE_ROW 在 Exceptions 有 invoice0.csv:2/:3 | PASS |
| A11 | invoice item_code 空；MISSING_REQUIRED_FIELD=1、无 AMBIGUOUS_KEY、unmatched invoice=1、报告有双语 cannot match | PASS |
| A12 | USD PO、无币种 receipt、CNY invoice 10×70/700；并独立对包内 ZIP 运行，详见上表；混币分桶及数量异常/同币内算术另测 | PASS |
| A13 | receipt qty11、invoice qty11 ×6/66；QTY_OVER 与 PRICE_MISMATCH 同行，Exceptions 单独列出 | PASS |
| A14 | 无 PO 行，OTHER 键 receipt 与 invoice 各一；ORPHAN_RECEIPT/ORPHAN_INVOICE，各 unmatched 表一行 | PASS |
| A15 | 相同基准输入两次运行，不同输出目录；JSON、Match Summary/Source Trace 相同，输入 hashes 记录 | PASS |
| A16 | `../outside.csv`、`/outside.csv`、`bad.txt`、输出路径=input 根均 exit2/INVALID_INPUT、无新输出；symlink 创建被 Windows 权限拒绝 | PASS（四子项）；**SKIP symlink 子项** |
| A17 | 限额 1byte 模拟拒绝；**实际**生成 50MiB+1 byte 单文件，exit2 LIMIT_EXCEEDED、错误含 52428801；同一路径引用 51 次报 50 files；真实总字节超过 200MiB 未测 | PASS（单文件/数量）；**NOT_TESTED 真实聚合 200MiB** |
| A18 | CSV item_code=`=CMD` Excel 导出 `'=` 文本；XLSX 公式/ignored sheet 公式、伪 macro、外链、external relationship 拒绝 exit2 INVALID_INPUT，报文件名且无输出；真实 Office 宏执行及远程网络监听未测 | PASS（静态构造与转义）；运行时 NOT_TESTED |
| A19 | invoice qty空、qty=`abc`、uom=`BOX` 分别 MISSING_REQUIRED_FIELD/INVALID_INPUT/UOM_MISMATCH，均非 MATCHED、空值不变零 | PASS |

额外范围标注（此处是首次会话的原始结论；本报告末尾有同一 ZIP 的独立增量复验）：完全未收货（receipt 列表为空）和不同订单分批履约的时序/日期专项当时 **NOT_TESTED**；部分收货 qty8 为 A04 PASS；4+6 分批收货与 3+7 拆票为 A03 PASS；重复键/源行为 A08/A10 PASS；CSV、显式 XLSX 为 A01/A02 PASS；路径、公式等安全为 A16/A18 的上述有限范围。历史输入不覆盖：隔离 CLI 四次输入运行前后 SHA 相同，输出位于不同新目录；pytest fixture 自有临时目录（不是对历史用户文件的写入测试）。没有检查其它 OS、真实 Office 样本宏/远端访问，均 NOT_TESTED。真正 200MiB 聚合边界需逐个有效文件都安全解析；在本有界会话避免制造多份接近 50MiB 的巨型有效 CSV 并一次性读入造成不受控内存峰值，明确 NOT_TESTED，绝不把 1byte 降限模拟当真边界。

blocked_reason: `release-check` exit1；无 LICENSE/授权核验，差异性需人工审查，WorkBuddy ZIP 解析、安装、对话、平台审核、上传、上架和发布全部 NOT_TESTED/BLOCKED。residual_risks: A16 symlink SKIP；A17 真实 batch 200MiB 未验；A07 缺 qty/price 的另一分支未直测；A18 真实宏/网络行为未测；其它 OS、完整端到端商用授权未测。仅证明本地候选在已执行情景下行为符合断言，不能称平台或发布 PASS。artifacts: 本报告；独立探针及隔离输入/输出保存在上述 wb-quality scratch（非永久交付）。没有更改业务代码、测试、ZIP、sidecar、catalog、已有许可证或历史报告；没有 commit/push、merge/rebase、部署、上传或发布；未操作 Kanban。

## 同一固定 ZIP 的覆盖缺口独立增量复验（新直接 Profile 会话）

**增量最终判定：整体 QA FAIL / 阻断候选验收。** 上述首次会话 PASS 仅为其已测范围的历史结果，不擦除；此次新增 A07 缺 PO qty/price 两分支的合同缺陷，不因其他分支 PASS 或 CLI exit0 改判。请项目经理安排开发修复并提供新版本/新候选供独立复验；原 0.1.3 ZIP 不改、不发布。无 Kanban 生命周期操作。

环境及边界：当前分支 `skill/purchase-threeway-match`、复验前 HEAD `b2e9c8030fe4ef323bf7637d50075cef795c7a1e`；`git worktree list --porcelain` 仅登记本产品独立分支，无该产品第二工作树；未读取 `wangbin-workbuddy-dev` 业务内容。`ps -ef | grep ...` 的输出为 `Binary file (standard input) matches`，**不能据此证明无并发**；通过单独工作树、未见其它产品工作树、无产品跟踪文件 diff 限定只读候选复验，并保留进程并发不可证风险。`sha256sum dist/wangbin-purchase-threeway-match-0.1.3-skill-candidate.zip` exit0，仍为 `e2c3b6cf0fa0d506a91a9ec6096514af0808c2ee4434044cb5bdba92e5ddde90`；新隔离 scratch `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa013-gap-t37643c38-independent-b/` 独立解压该 ZIP，`ZipFile.testzip() is None`、成员均位于产品目录，无越界。所运行脚本即新解压成员 `scripts/threeway_match.py`（不是源码直接调用）。仅在 wb-quality scratch 生成探针、输入和输出，无改候选/manifest/catalog/业务/测试。

复现及记录方式：探针 `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa013_gap_probe_t37643c38.py`；在产品根运行 `.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa013_gap_probe_t37643c38.py` exit **0**（探针完成记录，不表示所有业务断言通过），输出 `FAILED_CASES ['po-qty-missing', 'po-price-missing']`。各组包内 CLI 命令形式为 `.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa013-gap-t37643c38-independent-b/unpacked/wangbin-purchase-threeway-match/scripts/threeway_match.py --manifest C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa013-gap-t37643c38-independent-b/<case>/manifest.json --output C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa013-gap-t37643c38-independent-b/<case>/output`。manifest 固定 `input_root: input`、三文件 `po.csv/receipts.csv/invoices.csv`，除最后一组外 config={}；所有输入键 `(P1,1,SKU)`、币种 USD/UOM EA，正常 PO qty10/price5.00/amount50.00，正常 receipt R1 qty10，正常 invoice I1 qty10/price5.00/amount50.00；每组单独输入目录。机器可读逐次命令、原始输入、进程 stdout/stderr、三类输出、逐文件前后 SHA、断言及判定：`C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa013-gap-t37643c38-independent-b/evidence.json`。每组输入 SHA 前后完全一致；Excel 七表顺序、Run Manifest 输入 SHA/状态、Source Trace 全部实际行的文件/物理行号/64位哈希、JSON 与 Excel 异常数、Markdown 状态/例外引用均已核验。Excel 中负数字符串前缀 `'` 是防公式注入的安全转义（如 JSON `-3`、Excel `'-3`），不是数量错误；首次探针误判部分开票以及预设错误触发文件名的低阈值批量场景只发生在未作为正式结论的旧 scratch `...independent-a/`，已在**全新** `...independent-b/` 复跑纠正，旧证据未覆盖。

| 独立案例（CSV 均有表头，数据物理行2） | 包内 CLI exit；JSON/Excel/Markdown 实测 | QA |
|---|---|---|
| `no-receipt`：PO qty10 ×5.00/50.00、**receipt 仅表头零行**、invoice qty10 ×5.00/50.00 | exit0；`po_keys=1, matched=0, exceptions=1`，行状态和唯一例外 `NOT_COMPARABLE`；received_quantity/receipt_variance=`NOT_AVAILABLE`，而非 0 或 `MATCHED`；invoice qty10/variance0；Excel Match Summary/Exceptions 相同，Source Trace PO:2+invoice:2 共2行；Markdown `NOT_COMPARABLE at po.csv:2`。没有虚构 `QTY_UNDER`，无实际收货数量时按不可比判定。 | **PASSED**（首次 NOT_TESTED 已补） |
| `po-qty-missing`：PO `ordered_quantity=''`, `po_unit_price=5.00`, `po_amount=''`；receipt/invoice 均 qty10/50.00 | exit0，`SUCCEEDED_WITH_EXCEPTIONS` 但 `po_keys=0, matched=0, line_results=[]`；Excel Match Summary/Line Results 均零行，Exceptions 为 `MISSING_REQUIRED_FIELD po.csv:2` + `ORPHAN_RECEIPT receipts.csv:2` + `ORPHAN_INVOICE invoices.csv:2`；Source Trace 三行，PO:2 `_reason=MISSING_REQUIRED_FIELD` 且原始 qty 为空；Markdown 只有这三个异常，无 `NOT_COMPARABLE`；**没有任何 expected_amount 行可供审计**，也没有将空值写成0的证据。 | **FAILED**：A07/IO-07 要求缺 qty 时 `NOT_COMPARABLE` 且显示缺失操作数；不能以丢弃 PO 结果行、伪造两个孤儿的方式代替完整键的可追溯 PO 对比。 |
| `po-price-missing`：PO `ordered_quantity=10`, `po_unit_price=''`, `po_amount=''`；receipt/invoice 同上 | exit0，和缺 qty 分支同样 `po_keys=0, matched=0, line_results=[]`；Excel 空汇总/行级结果，三个异常与三条 Source Trace 均存在，PO:2 `_reason=MISSING_REQUIRED_FIELD` 且原始 price 为空；Markdown 无 `NOT_COMPARABLE`，expected_amount 未出现（未见虚构数值，但也没有必需的不可比行）。 | **FAILED**：同一缺操作数路径，遗漏 A07 明确的 `NOT_COMPARABLE`/逐键结果及不可派生 expected_amount 语义。 |
| `invoice-partial`：PO/receipt qty10，invoice qty7 ×5.00/35.00 | exit0；`po_keys=1, matched=0`；JSON/Excel 行 `invoiced_quantity=7`, `invoice_variance=-3`（Excel 安全文本为 `'-3`）, `QTY_UNDER;AMOUNT_MISMATCH`，amount_variance=-15.00；Exceptions 两行，Markdown 两异常含 `po.csv:2`；Trace 三行。 | **PASSED** |
| `invoice-over`：PO/receipt qty10，invoice qty11 ×5.00/55.00 | exit0；`po_keys=1, matched=0`；JSON/Excel `invoiced_quantity=11`, `invoice_variance=1`, `QTY_OVER;AMOUNT_MISMATCH`，amount_variance=5.00；Markdown 两异常、Trace 三行。 | **PASSED** |
| `batch-lowered-cap`：三份正常 CSV 单文件各 117/106/164 bytes；`config.limits.max_batch_bytes=165` bytes（单文件皆合规，PO+receipt 已超总量） | exit **2**；stderr JSON `FAILED_LIMIT/LIMIT_EXCEEDED`，明确 `receipts.csv: batch exceeds 50 files or 165 bytes`；未生成 Excel/JSON/Markdown 输出目录，不冒充成功，输入前后 SHA 相同。 | **PASSED，仅降低后的 165-byte 聚合配置**；默认真实 200MiB 批量边界依旧 **NOT_TESTED**。 |

输入 SHA-256（每行的 before=after；列依次 `po.csv`, `receipts.csv`, `invoices.csv`）：

| case | PO | receipt | invoice |
|---|---|---|---|
| no-receipt | `d0eaf634fb1763a87ee5f5ec2e292316e64878f0b967ea5496d5c22fbb1e4e56` | `1a8704488d8039851621c9ed2691d8d438dc7de3b2aa8b5c56c7834ff4ab58cd` | `eca9276849f3471fb4fecad98ba514568df4fa267811161d2d6f6080b01bcd21` |
| po-qty-missing | `4c6edf4cba3d67152a2d0dbf1c7eba7a94a87f5aefef11122ff277264bf24e79` | `74448bdc4db066d38e09b8e327907dbd840ebe4c73d7c257d9054ba5061f2dba` | `eca9276849f3471fb4fecad98ba514568df4fa267811161d2d6f6080b01bcd21` |
| po-price-missing | `4cda31df31ec992eb3d0cc3381c058b315ae0c21cdc0fad0636a6c07cd305e29` | `74448bdc4db066d38e09b8e327907dbd840ebe4c73d7c257d9054ba5061f2dba` | `eca9276849f3471fb4fecad98ba514568df4fa267811161d2d6f6080b01bcd21` |
| invoice-partial | `d0eaf634fb1763a87ee5f5ec2e292316e64878f0b967ea5496d5c22fbb1e4e56` | `74448bdc4db066d38e09b8e327907dbd840ebe4c73d7c257d9054ba5061f2dba` | `6798ecce67eb8e58c816bcf33939e57761f1d501dd4f7ae4d329642ce3eaaca2` |
| invoice-over | `d0eaf634fb1763a87ee5f5ec2e292316e64878f0b967ea5496d5c22fbb1e4e56` | `74448bdc4db066d38e09b8e327907dbd840ebe4c73d7c257d9054ba5061f2dba` | `e841785eae8a3c635393710356061dc8498a518fa9c81f5f56a64eda8bd79cd5` |
| batch-lowered-cap | `d0eaf634fb1763a87ee5f5ec2e292316e64878f0b967ea5496d5c22fbb1e4e56` | `74448bdc4db066d38e09b8e327907dbd840ebe4c73d7c257d9054ba5061f2dba` | `eca9276849f3471fb4fecad98ba514568df4fa267811161d2d6f6080b01bcd21` |

定位线索（非修改授权）：源码 `packages/skills/wangbin-purchase-threeway-match/scripts/threeway_match.py:145-159` 将缺 PO qty/price 行放入 invalid 而不放 pos；`:167-179` 把同键 receipt/invoice 当作 orphan；`:194,208-222` 的不可比/expected_amount 计算因此根本不会执行。冻结 `acceptance-cases.md:13` 指定 A07 缺 qty/price 应 NOT_COMPARABLE；`requirements.md:45-60`、`input-output-contract.md:70-77,103-115` 要求缺数不归零、不可比且留痕。风险/剩余 NOT_TESTED：原 A16 symlink SKIP、A17 默认真实 200MiB 聚合边界、A18 真实 Office 宏/外链网络行为、不同订单时序/日期、其他 OS、商用授权及 WorkBuddy 平台安装/对话/审核/发布。`release-check` 原 exit1/许可 BLOCKED 不因增量改变。artifacts: 本报告及上述新 scratch 探针/完整 `evidence.json`/独立输入输出。此段不是对首次会话的隐性改判；增量发现使**本候选整体 QA FAIL**。不 push、不操作看板。
