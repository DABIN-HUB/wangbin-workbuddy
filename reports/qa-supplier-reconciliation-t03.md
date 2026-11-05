# 独立 QA 报告：wangbin-supplier-reconciliation

- product_id: `wangbin-supplier-reconciliation`
- task_id: `t_37f7d307`
- QA 身份：wb-quality；独立于 T02 开发结论执行
- workspace: `F:/ideaWorkSpace/wangbin-workbuddy-supplier-reconciliation`
- branch: `skill/supplier-reconciliation`
- base_commit（T02 交接）：`da8520f2a16a02f2fac6006717252d870fdef39b`
- 被验收 result_commit：`3b1f3224d8d206097d83b6d3119fb00cea0e05c4`
- QA 结果：**LOCAL_QA_PASS**
- 平台/发布结果：**NOT_TESTED / BLOCKED**（无 WorkBuddy 平台安装、调用、审核或发布回执；许可证仍 `PROPRIETARY` + `REQUIRES_MANUAL_REVIEW`）

## 证据与真实命令

所有命令在上述 workspace 真实执行；独立探针未修改业务源码。

| 覆盖范围 | 命令/退出码 | 证据 |
|---|---|---|
| T02 专项回归 A01–A18（25 passed） | `python -m pytest -q tests/test_supplier_reconciliation.py` / **0** | 终端输出：`25 passed, 1 skipped`；唯一跳过是 Windows 无符号链接权限，非业务计算 |
| 产品工厂 test | `python -m tooling.products test --id wangbin-supplier-reconciliation` / **0** | 工厂 JSON `status=PASS` |
| 产品工厂 validate（含 secret scan） | `python -m tooling.products validate --id wangbin-supplier-reconciliation` / **0** | 工厂 JSON `status=PASS`, `findings=[]` |
| 独立 17-case 探针 | `python C:/Users/wangbin/.../cache/scratch/qa_probe.py` / **0** | `qa_probe.stdout`；完整逐例 JSON `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa_supplier_reconciliation/results.json` |
| 输出 XLSX 无公式 | `python C:/Users/wangbin/.../cache/scratch/check_xlsx.py` / **0** | 输出：`sheets=['Results','Summary','Errors']`, `formula_cells=[]` |
| 真实样例 CLI | `python packages/skills/.../reconcile.py --config packages/skills/.../examples/fictional-config.json` / **2** | 输出 `OUTPUT_EXISTS`；这是既有输出保护，不覆盖既有文件。首次样例成功由 T02 交接，当前目录已有输出 |
| Git 状态/提交核对 | `git status --short --branch && git rev-parse HEAD` / **0** | HEAD=`3b1f3224d8d206097d83b6d3119fb00cea0e05c4`；仅未跟踪 `supplier-reconciliation-out/`（T02 样例输出），QA 未修改源码 |

独立探针脚本与结果仅位于 profile scratch，不作为产品源码交付；其输入均为虚构数据。

## 独立真实业务覆盖

| 场景 | 输入/复现 | 实际结果 | 判定/证据 |
|---|---|---|---|
| 相等/Decimal 边界 | supplier `100.00`，internal `100.01`，默认 tolerance `0.01` | `rc=0`, `MATCHED`, difference `-0.01`, absolute `0.01` | PASS；`results.json` case `core`；证明 Decimal 方向和边界包含关系 |
| 金额差异 | 专项 A02：`100.00` vs `100.02` | `AMOUNT_DIFFERENCE`, `-0.02`, `0.02` | PASS；pytest A02 |
| 两侧单边/缺失不等于零 | 不同 document key | `ONLY_SUPPLIER`/`ONLY_INTERNAL`；缺侧对象 `null`，difference `null`，没有金额 0 | PASS；独立 cases `single`, `missing_not_zero` |
| 供应商重复 | 同完整 key 两行 `10.00`,`20.00`，内部一行 | 一个 `AMBIGUOUS`，sources 保留 3 行，不择首行 | PASS；独立 case `duplicate` |
| 内部/双侧重复 | 专项 A04 及 A17 | `AMBIGUOUS`，候选来源保留 | PASS；pytest |
| 空编号/非法金额/币种 | 空 key、`abc`,`1.234`,`NaN`、`人民币` | `INVALID`，错误码 `INVALID_KEY`/`INVALID_AMOUNT`/`INVALID_CURRENCY`；不作为金额匹配 | PASS；pytest A05/A06/A15 |
| 零/负金额 | 两侧 `0.00`、`-1.00` | 两条 `MATCHED`，精确 `0.00` 差额 | PASS；独立 case `zero_negative` |
| 前导零、大小写、NFC | `001` vs `1`；`abc` vs `ABC`；组合 NFC | 前两者不匹配，NFC 等价可匹配 | PASS；pytest A13 |
| 重复列/别名歧义 | `amount,amount`；“金额”和“含税金额” | `DUPLICATE_HEADER`/`FIELD_MAPPING_AMBIGUOUS`，非零且无成功结果 | PASS；pytest A07（独立源码复核 mapping_for 也确认拒绝） |
| CSV/XLSX、多工作表未指定 | UTF-8/UTF-16/GB18030 及 XLSX 显式 sheet/未指定/不存在 | 正确编码可运行；错误声明 `ENCODING_INVALID`；XLSX 未指定 `SHEET_SELECTION_REQUIRED`，不存在 `SHEET_NOT_FOUND` | PASS；pytest A08–A10，独立 case `xlsx_no_sheet` rc=2 |
| 公式单元格/Excel 注入 | XLSX amount `=1+1`；CSV key `=1+1`/`+cmd`；CSV amount formula | `FORMULA_CELL` 行级 INVALID；不执行公式；输出 Results/Summary/Errors 无公式单元格 | PASS；独立 `xlsx_formula`/`injection`/`formula_amount_csv`；`check_xlsx.py` |
| 大小/行数/列数 | 配置限制及专项边界 | `INPUT_TOO_LARGE`、`ROW_LIMIT_EXCEEDED`、`COLUMN_LIMIT_EXCEEDED`，rc=2，无成功 XLSX | PASS；pytest A12，独立 `rowlimit`/`columnlimit` |
| 混合互斥分类/汇总 | A17 同时构造六类状态 | 六状态互斥覆盖；`total_result_rows == len(results)`；Results/Summary/Errors 三表 | PASS；pytest A17 |
| 源行追溯/哈希/可复现 | 独立结果检查 source file/sheet/row；A16 两次运行 | 1 起始数据行号、CSV sheet null、输入 SHA-256；结果 ID 稳定且不含绝对路径 | PASS；pytest A01/A16；独立 JSON |
| 输入不覆盖/可复现 | 同输出目录第二次执行 | rc=2 `OUTPUT_EXISTS`，不覆盖；独立 case `output_overwrite` | PASS |
| 安全/联网/宏 | 输出 security 字段与工厂 validate | `network=false`, `formulas_executed=false`, `macros_executed=false`；validate 无 finding | PASS（本地边界）；平台沙箱 NOT_TESTED |

## 结果与残余风险

1. 本轮没有发现需阻断的业务缺陷；没有调用 `kanban_block`，因为独立真实用例均符合冻结合同。
2. symlink 运行时专项仍因 Windows 创建符号链接权限跳过（`NOT_TESTED`，不是 PASS）；实现代码的拒绝分支在静态复核和已有测试中覆盖，但 NTFS 权限隔离未宣称。
3. `manifest.json` 当前 `license_status=REQUIRES_MANUAL_REVIEW`，未发现本产品独立 LICENSE 文件；许可证授权、平台 ZIP 解析/安装/运行/审核/发布均未获真实平台证据，必须由后续门禁保持 BLOCKED/NOT_TESTED。
4. GitHub 远程 HEAD 与 push 仍是 T02 报告的网络阻断状态；本 QA 未 push、merge、rebase、force push 或部署。
5. WorkBuddy 平台能力不由本地 pytest、factory validate 或 ZIP 文件存在性推断。

## 结构化交付字段

- product_id: `wangbin-supplier-reconciliation`
- task_id: `t_37f7d307`
- workspace: `F:/ideaWorkSpace/wangbin-workbuddy-supplier-reconciliation`
- branch: `skill/supplier-reconciliation`
- base_commit: `da8520f2a16a02f2fac6006717252d870fdef39b`
- result_commit: `3b1f3224d8d206097d83b6d3119fb00cea0e05c4`
- changed_files: `reports/qa-supplier-reconciliation-t03.md`（仅本 QA 报告；业务源码未修改）
- artifacts: `reports/qa-supplier-reconciliation-t03.md`, `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa_supplier_reconciliation/results.json`
- verification_commands: 见上表
- verification_results: `LOCAL_QA_PASS`; 25 passed/1 skipped；独立 17 cases rc=0；致命错误 cases rc=2 且错误码正确；XLSX formula_cells=[]
- blocked_reason: `LICENSE/platform/remote-state NOT_TESTED or BLOCKED; not a local QA failure`
- residual_risks: symlink permission NOT_TESTED；PROPRIETARY license manual review；WorkBuddy platform parse/install/runtime/review/publish NOT_TESTED；remote HEAD/push network blocked
