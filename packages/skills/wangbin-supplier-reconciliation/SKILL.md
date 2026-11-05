---
name: wangbin-supplier-reconciliation
display_name: 供应商双边对账
display_name_en: Supplier Reconciliation
description: 对授权的供应商与内部 CSV/XLSX 明细进行离线确定性逐行核对。
description_zh: 以明确业务键和 Decimal 金额核对双侧来源，输出六类状态与证据。
description_en: Offline deterministic two-sided reconciliation with traceable evidence.
version: 0.1.0
author: wangbin
license_type: PROPRIETARY
license_status: REQUIRES_MANUAL_REVIEW
allowed-tools: Read, Bash
---

# 供应商双边对账

仅在已授权的本地 Python 3.10+ 环境运行；依赖 `openpyxl`（缺失即失败）。WorkBuddy 安装、执行权限和审核尚未验证，不可将本地运行当作平台验收。输入须由用户明确选择，禁止联网、模糊匹配、推断币种、换汇及自动付款。

在仓库根目录运行：

```bash
python packages/skills/wangbin-supplier-reconciliation/scripts/reconcile.py --config packages/skills/wangbin-supplier-reconciliation/examples/fictional-config.json
```

示例配置中的相对路径相对执行时工作目录解析；真实数据请新建配置，显式指定 `supplier_input.path`、`internal_input.path`、XLSX `sheet`、`output_dir`，CSV 可声明 `encoding`（utf-8、utf-16 或 gb18030）。输出固定为指定目录中的 `reconciliation.json`、`reconciliation.xlsx`、`reconciliation.md`；失败退出 2 且 JSON 含错误码，不得当成功汇总。支持配置 `field_mapping`、`key_fields`、`amount_tolerance`、`amount_scale`、`allow_negative_amount` 和仅能降低的 `limits`。详细规则见仓库根目录 `requirements.md`、`input-output-contract.md`；虚构演示见 `examples/fictional-config.json`。

运行前确认文件权属和目录权限；不要把输出写入输入目录的同名文件；结果含业务标识和金额，请在受控目录保管。默认最大单文件 10 MiB、100000 数据行、200 列；无平台授权、许可证及数据保护审核时不得发布。仅本地逻辑验证，不保证 NTFS 强隔离。
