# T04 本地候选打包验收 — wangbin-supplier-reconciliation

- product_id: `wangbin-supplier-reconciliation`; task_id: `t_ab0f5217`; 身份：独立质量验收 `wb-quality`
- workspace: `F:/ideaWorkSpace/wangbin-workbuddy-supplier-reconciliation`（由 `git worktree list --porcelain` 确认）；branch: `skill/supplier-reconciliation`
- base_commit（T03 交接）: `3b1f3224d8d206097d83b6d3119fb00cea0e05c4`; result_commit: 见最终 handoff（若远端网络仍阻断，不代表已 push）。
- 结论：**LOCAL_CANDIDATE_PASS；PUBLISH_READY=BLOCKED**。T03 独立 QA 已通过本地业务验收；此处重新执行本地回归与工厂命令，不推断 WorkBuddy 平台能力。

## 命令和真实结果

所有下列命令在上述 workspace 执行。退出码以实际 CLI 为准；`release-check` 的整体进程退出码为 **1**，不是通过。

| 命令 | 退出码 | 实际内容/判定 |
|---|---:|---|
| `python -m tooling.products --help`、`python -m tooling.products package --help`、`verify --help`、`release-check --help` | 各 0 | 真实参数表含 `--id`；检查 `tooling/products.py` 确认 `package_product`/`verify_package`/`release_check` 的调用、失败返回码与工厂路径。 |
| `python -m tooling.products validate --id wangbin-supplier-reconciliation` | 0 | JSON `status=PASS`, `findings=[]`；本地源结构/secret scan，不是平台安全认证。 |
| `python -m tooling.products test --id wangbin-supplier-reconciliation` | 0 | JSON `status=PASS`, `returncode=0`; `25 passed, 1 skipped`，跳过为 Windows symlink creation requires privileges。 |
| `python -m pytest -q tests/test_supplier_reconciliation.py` | 0 | `25 passed, 1 skipped in 2.57s`；symlink 场景 NOT_TESTED，不以其他测试代替。 |
| `python -m tooling.products package --id wangbin-supplier-reconciliation` | 0 | JSON `status=PASS`, `version=0.1.0`, `source=packages/skills/wangbin-supplier-reconciliation`，6 个成员，`platform=BLOCKED`；产出受控 dist 下 ZIP、sidecar、manifest。工厂先比较已有工件再写，不覆盖不同内容历史包；运行前 dist 目录不存在。 |
| `python -m tooling.products verify --id wangbin-supplier-reconciliation` | 0 | JSON `status=PASS`, `sha256=232be0d241179f18e2190b5622e7482d8522ac55e09ee18fb877c95d69e35412`，按源文件与归档/manifest/sidecar 核验。 |
| `sha256sum dist/wangbin-supplier-reconciliation-0.1.0-skill-candidate.zip` | 0 | 独立输出同上 64 位 digest；sidecar/manifest/catalog 与现场值相同。 |
| `python -m zipfile -t dist/wangbin-supplier-reconciliation-0.1.0-skill-candidate.zip` 与 `python -m zipfile -l ...` | 各 0 | `Done testing`；列示 6 个成员，固定时间戳 1980-01-01。 |
| `python C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/verify_supplier_candidate_t04.py` | 0 | 独立 `ZipFile.testzip()`、来源逐字节/成员哈希和长度、无重名/越界、内外 manifest 0.1.0、catalog/sidecar、XLSX 可重开且无公式、JSON 汇总断言全部 PASS。 |
| `python -m tooling.products release-check --id wangbin-supplier-reconciliation` | **1** | JSON `status=BLOCKED`, `local_candidate=PASS`, validation/tests/archive PASS；`license_and_dependencies={type:UNKNOWN,status:BLOCKED,reason:"license file is absent; no license claim is verified"}`；similarity `REVIEW_REQUIRED`（10 pairs）；`LICENSE_PASS=BLOCKED`, `PACKAGE_VALIDATION_PASS=PASS`, `LOCAL_TEST_PASS=PASS`, `WORKBUDDY_ZIP_PARSE_PASS=NOT_TESTED`, `WORKBUDDY_RUNTIME_PASS=NOT_TESTED`, `WORKBUDDY_REVIEW_PASS=NOT_TESTED`, `PUBLISH_READY=BLOCKED`。 |
| `git ls-remote --heads origin` | **128** | `Failed to connect to github.com port 443 ... Could not connect to server`；远程目标 HEAD 未可靠查得，不执行 push。先前精确 refs 查询曾返回空/0，不视为远程一致的证据。 |

## 实物、业务输出、门禁

- ZIP: `dist/wangbin-supplier-reconciliation-0.1.0-skill-candidate.zip`；sidecar `.zip.sha256`；manifest `.zip.manifest.json`；SHA-256: `232be0d241179f18e2190b5622e7482d8522ac55e09ee18fb877c95d69e35412`。
- 成员（均以 `wangbin-supplier-reconciliation/` 为根；逐一与源文件字节相同）：`SKILL.md`、`examples/fictional-config.json`、`examples/fictional-internal.csv`、`examples/fictional-supplier.csv`、`manifest.json`、`scripts/reconcile.py`。不含 `LICENSE`；catalog 仅本产品 `candidate/archive_evidence/sha256` 被工厂更新，其他版本不动。dist 被 Git ignore，候选仅留本地。
- 现有虚构样例产物 `supplier-reconciliation-out/reconciliation.json`, `.xlsx`, `.md` 已独立重开：总行数 **4**；`MATCHED=1`, `AMOUNT_DIFFERENCE=1`, `ONLY_SUPPLIER=1`, `ONLY_INTERNAL=1`, `AMBIGUOUS=0`, `INVALID=0`；币种 CNY 计数与状态一致，错误 0；差额 `20.00 - 21.00 = -1.00`；单边缺失为 null，非零；XLSX 表 `Results/Summary/Errors`、无公式单元格。样例来自 T02 保留的已有输出，不伪称本次 CLI 新生成。
- 安全：本地 validate 无 finding；虚构样例 JSON 报告 `network=false`, `formulas_executed=false`, `macros_executed=false`；平台权限/沙箱 NOT_TESTED。
- 授权：manifest 声明 `PROPRIETARY` / `REQUIRES_MANUAL_REVIEW`；工厂许可门禁 `type=UNKNOWN`, `BLOCKED`（未有产品 LICENSE 和许可授权证据），绝非 LICENSE_PASS。
- 平台 ZIP 解析、安装、运行、对话、审核、发布均 **NOT_TESTED/BLOCKED**，没有上传、提交审核、部署或发布回执。内部相似度检查 10 pairs 均证据不足/需人工审阅，不能等同独立性认证。

## 结构化交接

- product_id: `wangbin-supplier-reconciliation`; task_id: `t_ab0f5217`; workspace: `F:/ideaWorkSpace/wangbin-workbuddy-supplier-reconciliation`; branch: `skill/supplier-reconciliation`。
- base_commit: `3b1f3224d8d206097d83b6d3119fb00cea0e05c4`；result_commit: 见最终交接；changed_files: `products/catalog.json`（工厂更新本产品候选字段）、`reports/qa-supplier-reconciliation-t03.md`（T03 已有独立证据）、`reports/package-supplier-reconciliation-t04.md`（本报告）。
- artifacts: 上述 ZIP、`.sha256`、`.manifest.json`、本报告和已有样例 3 文件；verification_commands/verification_results: 见表。
- blocked_reason: `LICENSE 缺产品独立许可证与权利证据；WorkBuddy 平台解析/安装/运行/审核未测试；内部独立性 REVIEW_REQUIRED；远程 HEAD 无法可靠核对（GitHub 443），因此 GIT_PUSH_PASS NOT_TESTED/BLOCKED。`
- residual_risks: symlink 权限未测；License 与平台协议未决；WorkBuddy 平台链路未测；内源相似度需人工判断；远程 push 不可确认。仅本地候选通过，不得转述为可发布。
