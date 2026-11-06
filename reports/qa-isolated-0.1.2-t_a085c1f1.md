# 0.1.2 固定 ZIP 独立 QA（直接 Profile 会话）

- product_id: `wangbin-purchase-threeway-match`; task_id: `t_a085c1f1`; version: `0.1.2`。
- session_id: `local-3daf783e97ded3ab90df1a06bb0c20340e9d3283cc6a18a1c303702089ce491a`；直接 Profile 会话，不是 Kanban Worker/run，不声称卡片 Done。
- workspace: `F:/ideaWorkSpace/wangbin-workbuddy-purchase-threeway-match`; branch: `skill/purchase-threeway-match`; base_commit: `b578ad229d5c901df0c588d225d57d0353912f6b`；result_commit: 报告提交后另以 `git rev-parse HEAD` 记录在会话交接中（自身不能预载其哈希）。
- 候选: `dist/wangbin-purchase-threeway-match-0.1.2-skill-candidate.zip`；独立实算 SHA-256 `aec7d2821c01ff092a6dce03ea94f2cf80c5c521d32e53fa6af76cc5a3b165e5`，与冻结值一致。
- **独立结论：FAIL；候选 QA / 发布门禁 BLOCKED。** A11 修复真实通过；但 A12 异币种仍直接做单价与金额差比较并产生无意义的差异码及数值。工厂/既有 pytest PASS 不能覆盖这个缺陷。请项目经理转开发按币种不可比规则修复、产生新固定候选，再由独立 QA 复验；本报告不更改产品文件、测试或旧证据。

## 实际执行、退出码

环境：项目现有 `.venv/Scripts/python.exe` = Python 3.11.15；`openpyxl` 可以实际读取所有输出；工作目录为上述产品 worktree。仅在 `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/` 创建 `qa012_t_a085c1f1.py` 独立探针及隔离解压、实验输入/输出；最终完整运行目录 `qa012-t_a085c1f1-r2/`。CLI 一律调用**解压后** `unpacked/wangbin-purchase-threeway-match/scripts/threeway_match.py`，不是工作区脚本；示例从另一个 cwd 执行。

| 命令（均在上述 workspace；探针所调 CLI 见下一节） | exit | 独立实测 |
|---|---:|---|
| `git status --short; git branch --show-current; git rev-parse HEAD; git worktree list --porcelain; printf 'session=%s\n' "$HERMES_SESSION_ID"` | 0 | 指定分支与 b578ad...；禁区仅由 worktree 注册识别，未读取其业务文件；原有六项未跟踪文件保持不动。 |
| `sha256sum dist/wangbin-purchase-threeway-match-0.1.2-skill-candidate.zip` | 0 | `aec7d2821c01ff092a6dce03ea94f2cf80c5c521d32e53fa6af76cc5a3b165e5`。 |
| `.venv/Scripts/python.exe -m tooling.products validate --id wangbin-purchase-threeway-match` | 0 | JSON status=PASS, findings=[]。 |
| `.venv/Scripts/python.exe -m tooling.products test --id wangbin-purchase-threeway-match` | **1** | JSON status=FAIL, returncode=1，环境缺 `pytest` (`No module named pytest`)；**依赖缺失不算通过，也不算产品断言失败**。 |
| `uv run --no-sync --offline --with pytest python -m tooling.products test --id wangbin-purchase-threeway-match` | 0 | 不改 `uv.lock` 的离线替代环境：工厂 status=PASS、内部 returncode=0、`9 passed in 0.84s`。 |
| `.venv/Scripts/python.exe -m tooling.products verify --id wangbin-purchase-threeway-match` | 0 | status=PASS，报告 ZIP SHA 与独立实算一致；这是本地验证，不是 WorkBuddy 平台验证。 |
| `.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa012_t_a085c1f1.py`（首轮） | 1 | 探针自身将空 Excel cell 当字符串 `.split`，止于 A05 0.10 后，A12 未执行；只修复 scratch 探针并使用新的隔离目录，未把此轮算产品失败。 |
| 同上（第二轮，完整链） | **1** | `ALL_PROBES_COMPLETED`；所有 ZIP/示例/A11/A05/七表/输入哈希断言通过，唯一产品断言 `A12 no raw cross-currency amount/price comparison` FAIL。包内各 CLI 实际 exit 0，不能将 exit 0 偷换为 A12 验收通过。 |
| `sha256sum dist/wangbin-purchase-threeway-match-0.1.2-skill-candidate.zip dist/wangbin-purchase-threeway-match-0.1.2-skill-candidate.zip.sha256 dist/wangbin-purchase-threeway-match-0.1.2-skill-candidate.zip.manifest.json products/catalog.json; git rev-parse HEAD; git branch --show-current; printf 'SESSION=%s\n' "$HERMES_SESSION_ID"; git status --short` | 0 | 四个独立文件哈希、HEAD、会话和未跟踪文件复核，见下。 |

## ZIP / 工厂证据

- `ZipFile.testzip() is None`；严格七个互异、安全且都位于 `wangbin-purchase-threeway-match/` 下的成员：`SKILL.md`、`examples/data/{invoices,po,receipts}.csv`、`examples/manifest.json`、`manifest.json`、`scripts/threeway_match.py`。逐成员原始字节大小和 SHA-256 对 archive manifest 七项完全相符，隔离解压后逐成员 SHA 仍相符；没有新增隐藏/越界成员。规范 JSON `{"members": members}` 的重新散列得到 `payload_snapshot_sha256=9641dac67caf28618f20e90e397fc63d9706621ea8e36896d76f7afb85e84a0b`。
- `.zip.sha256` 的完整内容为 `aec7d2821c01ff092a6dce03ea94f2cf80c5c521d32e53fa6af76cc5a3b165e5  wangbin-purchase-threeway-match-0.1.2-skill-candidate.zip` 加 LF；sidecar 文件 SHA=`05f6f8e4a8058270c22a3791f48b4e01b3bb5c03e18453a2443862ee00bf6739`；archive manifest 文件 SHA=`382a066670d5a785da12f0f7d8123a7c9b20163f08479871477b6b55ed0fa93c`；catalog 文件 SHA=`4f843af9bd1fbb8ec525228a0003954be3180eb64ab6bda4f30e9337a67c3021`。Catalog 该产品 active_version 0.1.2，其 candidate/archive_evidence/hash 与 ZIP 一致。
- 包内 manifest id/version 对齐，`license_type=PROPRIETARY`、`license_status=REQUIRES_MANUAL_REVIEW`；无独立 LICENSE 成员。授权、依赖权利及平台协议不能由 ZIP 完整性替代，人工许可证门禁未通过（NOT_TESTED/BLOCKED）。

## 隔离 CLI、三种输出重读

实际调用模板：`.venv/Scripts/python.exe <scratch>/qa012-t_a085c1f1-r2/unpacked/wangbin-purchase-threeway-match/scripts/threeway_match.py --manifest <scratch>/qa012-t_a085c1f1-r2/<case>/manifest.json --output <scratch>/qa012-t_a085c1f1-r2/<case>/output`。示例输入改为包内 `examples/manifest.json`、`examples/data`，输出为 `<scratch>/qa012-t_a085c1f1-r2/example-output`；六次 CLI（示例、A11、A05 三种配置、A12）均 exit **0**，stderr 空。每次重读 `summary.json`、`report.md` 和 `threeway_match.xlsx`，严格按 `Match Summary`、`Line Results`、`Exceptions`、`Unmatched Receipts`、`Unmatched Invoices`、`Source Trace`、`Run Manifest` 七表顺序，并校验 JSON/Markdown/Excel 状态、汇总/明细、例外数与各来源文件/物理行/64 位行哈希、Run Manifest 版本 0.1.2 和输入文件哈希。六次运行前后各输入文件集合及 SHA-256 都不变（Run Manifest 的记录也等于运行前哈希）。

| 情景及输入（每组新建 `historic-input`，键 P1/1/SKU；PO `10 × 5.00=50.00 USD EA`、收货 10 EA；物理行 2） | JSON / 表格实测 | QA |
|---|---|---|
| 包内示例，5 来源行（po:2, receipts:2,3, invoices:2,3） | `SUCCEEDED`、po_keys=1、matched=1、exceptions=0；七表数据行依序 1/1/0/0/0/5/1。 | PASS |
| A11：invoice `item_code` 为空，INV1/1、qty 10、5.00 USD、50.00；无部分键搜索 | `SUCCEEDED_WITH_EXCEPTIONS`、1/0/2，异常 `MISSING_REQUIRED_FIELD` 和 `NOT_COMPARABLE` 各一，未有 `AMBIGUOUS_KEY`；`Unmatched Invoices` 仅一条 invoices.csv:2，`Source Trace` invoice 仅一条且 hash 与 unmatched 相同；invoice 未并入汇总。report.md 实有 `无法匹配 / cannot match`、`invoices.csv:2`、`item_code`、`no candidate inferred`，PO 结果 `NOT_COMPARABLE`。七表 1/1/2/0/1/3/1。 | **PASS（0.1.1 缺陷已修复）** |
| A05 amount tolerance=0.01、unit price tolerance=0.01；invoice qty 10、单价 5.01、金额 50.10 USD | `amount_variance=0.10`，`AMOUNT_MISMATCH` 一项，价格等于容差不报 `PRICE_MISMATCH`，matched=0，exceptions=1，结果状态 `AMOUNT_MISMATCH`；七表 1/1/1/0/0/3/1。 | PASS |
| A05 amount tolerance=0.10、unit price tolerance=0.01；同一输入 | 差额 `0.10` 位于包含边界：`MATCHED`、matched=1、exceptions=0；七表 1/1/0/0/0/3/1。 | PASS |
| A05 不写 config（默认零容差）；同一输入 | `PRICE_MISMATCH;AMOUNT_MISMATCH`、`amount_variance=0.10`、matched=0、exceptions=2；七表 1/1/2/0/0/3/1。 | PASS |
| A12：PO USD `5.00/50.00`，invoice CNY `70.00/700.00`，无汇率配置；receipt 无 currency 列 | `SUCCEEDED_WITH_EXCEPTIONS`、matched=0、exceptions=4；有 `CURRENCY_MISMATCH;NOT_COMPARABLE`，PO currency=USD、三源行仍在 trace；**另外错误地给出** `PRICE_MISMATCH;AMOUNT_MISMATCH`、`weighted_invoice_unit_price=70.00`、`amount_variance=650.00`，把 CNY 700.00 减 USD 50.00。七表 1/1/4/0/0/3/1。 | **FAIL（跨币种直接比较，见缺陷）** |

输入 SHA 运行前后相同（按 po/receipts/invoices）：A11 `d0eaf634fb1763a87ee5f5ec2e292316e64878f0b967ea5496d5c22fbb1e4e56` / `2e9e352746b2aa048e1a949e637772503492adf7aad47864734c254c9f01846b` / `dd053204b36d43083dc40ee5f87f74c80d7e5ccff06b4b4de40a76e2f02bc12b`；A05 三组前后均为上述 po/receipts 哈希及 invoices=`6bddeebcaa623a4d832ab4f611581d3a506785c88f9ed10345716a3b8422f98d`；A12 前后为上述 po/receipts 哈希及 invoices=`4b9e1a670ddd4770a3c17ed2f27ee7b8821aa299d811746875838daf9598bec7`；包内示例三个 CSV 的前后哈希分别为 invoices=`c72c3dddc1897e24dabc2f12a77ca61b97eeec157dc047a0f0305b6550fa6c83`、po=`a40216b264646addad211e126747f25c300fe8c731e562205a3f969a3df2fd52`、receipts=`4076e7b505806d15441adc5bbbe023cb174b5f66601ef5e32ddff8582a48e67c`。

## 阻断缺陷：A12 混合币种被直接比较

复现目录：`<scratch>/qa012-t_a085c1f1-r2/a12/`；使用上面模板运行其 `manifest.json`，查看 `output/summary.json`、`output/report.md`、`output/threeway_match.xlsx` 的 `Match Summary`、`Exceptions`、`Source Trace`。输入 po.csv:2 为 P1/1/SKU, qty=10, USD, unit=5.00, amount=50.00；receipts.csv:2 qty=10 EA 且**无 currency 字段**；invoices.csv:2 qty=10, CNY, unit=70.00, amount=700.00。预期：仅按 PO/Invoice 币种判断异币种，不强制 receipt 币种；`CURRENCY_MISMATCH` 和 `NOT_COMPARABLE`；无汇率不得将不同计价货币的单价/金额直接相减形成 `PRICE_MISMATCH` 或 `AMOUNT_MISMATCH`，跨币种差值不得被当成有意义的可比金额，源币种/来源行保留。实际：进程 exit 0、summary `SUCCEEDED_WITH_EXCEPTIONS`、4 例外；前两码正确，但另两码错误；Excel 显示 `amount_variance=650.00`、`weighted_invoice_unit_price=70.00` 且 currency 一列仅 USD，report.md 对这两码也列出引用 `po.csv:2`，容易被误读成同币种金额差。包内入口同哈希源码相应逻辑见 `packages/skills/wangbin-purchase-threeway-match/scripts/threeway_match.py:172-185`：检测币种后仍继续做直接价格/金额比较。冻结 A12 要求不猜汇率、NOT_COMPARABLE；本轮额外按明确的“跨币种不直接比较金额”门禁断言，**不把包含正确币种标志等同完整通过**。风险不是“仅显示可能误导”：还实际生成了无意义的异常码。请产品经理转开发修复并冻结新候选后独立复验；本会话不修改业务代码/断言。

## 门禁、范围、交付

- `LOCAL_ZIP_INTEGRITY=PASS`；`FACTORY_VALIDATE=PASS`；`FACTORY_TEST_INITIAL=FAIL_DEPENDENCY`、`FACTORY_TEST_OFFLINE_RETRY=PASS`；`FACTORY_VERIFY=PASS`；`BUNDLED_EXAMPLE=PASS`；`A05=PASS`；`A11=PASS`；`A12=FAIL`；`RELEASE_VERDICT=BLOCKED`。
- 许可证人工审查、第三方权利与平台协议 `NOT_TESTED/BLOCKED`；WorkBuddy 平台安装/调用/审核、上传/上架/发布、其它 OS 运行 `NOT_TESTED`。此处仅验证指定场景，A01–A19 其余独立完整矩阵及其它输入安全边界 `NOT_TESTED`；本地测试和工厂 PASS 都不代表平台批准。
- changed_files: `reports/qa-isolated-0.1.2-t_a085c1f1.md`（仅新增自己的报告）；artifacts: 本报告、上述 scratch 探针/临时隔离输出（scratch 非持久交付）；blocked_reason: `A12 无汇率跨币种直接做单价/金额比较产生伪差异；许可证手动审核和 WorkBuddy 实测仍未完成`。没有重建/改写 ZIP、sidecar、catalog、旧报告、uv.lock、业务代码或测试；没有 push、merge、平台操作或 Kanban 生命周期操作。
