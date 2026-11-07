# AUDIT-R1 Q01 D | 0.1.5 开发者预 QA 本地候选

- product_id: `wangbin-import-precheck`; task_id: `t_56363e73`; workspace: `F:/ideaWorkSpace/wangbin-workbuddy-import-precheck`; branch: `skill/import-precheck`.
- 基线 HEAD `799424250c4749155b47d4ba286dae9261cd8119`；先将分析师三份独立冻结合同提交 `d673f83b566a8a642e929b954714e8c893d5de9c`，源码/测试/有限工厂选版提交 `33394a26f56ede58d76eb36ecced1009bc047958`。包来源按该提交的四个载荷文件读取；登记/证据提交另记于任务交接，不影响包字节。
- 旧 0.1.4 ZIP：`dist/wangbin-import-precheck-0.1.4-skill-candidate.zip` SHA-256 `536763a9c5d64d5b5b53364f5e6e7be93c13457351624b544a0b722b07955d3c`，本轮前后未变；旧版反例详见 `audit-r1-014-baseline.md`，历史 QA 不删不改。
- 新 0.1.5 ZIP：`dist/wangbin-import-precheck-0.1.5-skill-candidate.zip` SHA-256 `f8b4188f6b4fe11a5074a3e6ffc60016f3a1322938b7f28953c1a0a62b6f47ed`；同名 sidecar `.sha256`、工厂外部清单 `.manifest.json`（**工厂归档清单，不是 WorkBuddy 官方 manifest**）均在 dist。catalog 追加版本，`active_version` 留 0.1.4，未激活 0.1.5；无内置 manifest.json。
- ZIP 成员 SHA-256：`README.md` `2e2ec38a3ff73d2715fc88417b6704773ea23e4f1394a6ac9b9c9b9a3ea4ee10`；`SKILL.md` `9d178e7a867d324f36c1a367b888c71e1c6e11c4b7b28deeef0be2a3d2610032`；`references/rules.md` `e32f10a5377a4cef7d8f5db4ac1f0e2f73023e486d8b73d5e69887b8f4ab9142`；`scripts/precheck.py` `48192aedb769d4e41633621209eed56506ab7cb0b1f51c32ba6310f5c380e49f`。

|缺陷|基线与根因|本轮改动与开发者实测|独立 QA|
|---|---|---|---|
|F01|0.1.4 的候选按原表列加 row_id/source_line；映射未接导出|实际业务表按确认目标列序、文本 00123 保留、源额外列剔除；真实 CLI mapped C1/Q0；模板换序和长编码另由 L2 测试|NOT_TESTED|
|F02|旧版先查原值，只在转后补查唯一键；upper 修复仍被旧错误阻断|转换先于全套最终规则，变化表含原/最终值及字段规则状态；真实 CLI strip C0/Q1、lower C0/Q1 两问题、upper C1/Q0、upper collision C0/Q2、长度边界 C0/Q1。原唯一键重复仍保留。|NOT_TESTED|
|F03|缺参考虽标 PARTIAL，旧 split 只看 findings 仍导出 C1|缺/歧义引用按行记 PENDING，既违规又缺证据同时标记，不认作违规参考值；真实 CLI 缺参考 PARTIAL C0/Q1；L2 混合/歧义/补表/全量副本覆盖|NOT_TESTED|
|F04|旧 README 0.1.2 vs ZIP/SKILL 0.1.4|README/SKILL/包名/catalog candidate/工厂清单同步 0.1.5；旧包保留|NOT_TESTED|

## 实际命令与结果

- `uv run --no-project --with 'openpyxl>=3.1,<4' --with pytest --with pyyaml python -m pytest tests/test_import_precheck.py tests/test_import_precheck_audit_r1.py tests/test_product_factory.py -q` → exit 0，**53 passed, 2 skipped**（两项 Windows 符号链接能力不可用；不算 Windows 实测 PASS）。初次开发过程中的 8 个旧测试断言因旧目标列布局不再适用失败，已改为目标列的独立预期；工厂整套首次旧目录数断言与未激活夹具失败后修正，再运行结果如上。`python -m tooling.products test --id wangbin-import-precheck` → exit 0，20 passed（它只跑已注册旧测试路径；AUDIT-R1 新测试另单独执行）。
- `python -m tooling.products register-version --id wangbin-import-precheck --version 0.1.5 --no-activate` → exit 0，active 0.1.4；`python -m tooling.products validate --id wangbin-import-precheck --version 0.1.5` → PASS/exit 0；`package ... --version 0.1.5` → PASS/exit 0；`verify ... --version 0.1.5` → PASS/exit 0；`python -m zipfile -t dist/wangbin-import-precheck-0.1.5-skill-candidate.zip` → `Done testing`/exit 0。工厂针对非 active 候选的显式 `--version` 为本轮受限增量，默认 active 行为不变。
- `uv run --no-project --with 'openpyxl>=3.1,<4' python docs/products/wangbin-import-precheck/audit-r1-015-selftest.py` → exit 0：从最终 ZIP 干净解压在独立 scratch，用真实 CSV 调正式脚本，7 案全部子进程 exit 0、五表重开/业务行数/源 SHA 核验通过；命令、cwd、输入 SHA、输出路径、状态与逐案结果在 `audit-r1-015-selftest-results.json`。L2 测 CSV/XLSX，L3 开发自测这 7 案只用 CSV；独立 QA 须另测 XLSX、模板和更多变体。
- `uv run --no-project --with 'openpyxl>=3.1,<4' python -c "import importlib.metadata as m; ..."` 实测发行元数据：openpyxl 3.1.5 `License=MIT`，et_xmlfile 2.0.0 `License=MIT`。声明的版本区间和隔离安装步骤见包内 README/SKILL；未验证目标 WorkBuddy 安装和许可全文/发行权。

## 边界

产品原件只读，本轮测试合成文件在隔离 scratch；Git 仅本地提交、未 push。L4 真实宿主自然语言三轮：NOT_TESTED（交独立 QA）；L5 WorkBuddy 实际安装/运行：NOT_TESTED；平台上传/审核/发布：NOT_EXECUTED；许可证与权利、有效平台协议：NOT_VERIFIED/BLOCKED。0.1.5 仅为 **pre-QA 本地候选**，不能以开发自测代替独立复验。硬隔离/渲染/极端资源和符号链接 Windows 实测尚未证明。
