---
name: wangbin-supplier-reconciliation
display_name: 供应商对账差异定位
display_name_en: Supplier Reconciliation Difference Locator
description: 供应商对账差异定位，帮助采购、财务和对账人员核对供应商对账单与内部明细。
description_zh: 把供应商对账单与内部明细放在一起逐项核对，定位金额一致、金额差异、单侧记录、需人工核对或无效输入，并保留来源位置。
description_en: Compare supplier statements with internal details and locate traceable reconciliation differences.
version: 0.1.3
author: wangbin
license_type: PROPRIETARY
license_status: REQUIRES_MANUAL_REVIEW
allowed-tools: Read, Bash
---

# 供应商对账差异定位

供应商对账差异定位，帮助采购、财务和对账人员把供应商对账单与内部明细放在一起逐项核对，快速看清哪些记录金额一致、哪些金额存在差异、哪些只出现在一侧，以及哪些记录需要人工核对或无法作为有效输入处理。结果保留来源文件、工作表和行号，方便回看原始记录；它只提供可追溯的对账线索，不替你付款、换汇、判断舞弊或作信用结论。

## 怎么使用

### 1. 准备两份输入文件

选择一份供应商侧文件和一份内部侧文件。两份文件均支持 CSV 或 XLSX；文件应是用户明确授权的本地普通文件。使用 XLSX 时请明确选择工作表；CSV 不需要选择工作表。

### 2. 用自然语言开始

直接说明“请核对这两份文件”，并补充文件角色、工作表名称和字段对应关系即可，一般不需要先理解复杂 JSON 配置。需要特殊匹配方式或金额容差时再明确提出，不要让系统自行猜测。

### 3. 字段对应与检查内容

默认 basic 模式只需 `document_no` 和 `amount`（旧 `document_id` 是兼容别名）。字段名不同可通过 `field_mapping` 明确对应；两侧必须具备指定字段，缺失数据不会被补齐。系统检查记录能否唯一对应、金额是否一致、是否只有一侧存在，以及输入是否缺字段或格式不合法，并保留来源文件、工作表和行号。缺失数据不会当成零；不会猜测供应商、金额或币种。

六类结果：**金额一致**、**金额存在差异**、**仅供应商侧有记录**、**仅内部侧有记录**、**需要人工核对**（含键不唯一）和**输入无效**。异常和无法唯一确定的记录交由人工处理，不自动改账、付款、生成会计凭证或换算币种。

### 4. 查看六个输出工作表

Excel 固定包含以下六个工作表，名称和顺序不变：`Summary`（汇总）、`Matched`（金额一致）、`Amount Differences`（金额差异）、`Supplier Only`（仅供应商）、`Internal Only`（仅内部）和 `Manual Review`（需人工核对，含无法唯一确定及输入无效）。同时输出 `reconciliation.json`、`reconciliation.xlsx` 和 `reconciliation.md`；输入失败时退出码为 2，不伪造成功汇总。

## 能力边界与安全提示

不做付款、自动改账、会计凭证、换汇、税务重算、OCR/PDF、模糊匹配、自动审批或舞弊/信用结论；不联网、不执行宏或公式、不修改原始文件。异常需要人工处理，未获授权不得上传文件。输出含业务标识和金额，应存放在受控目录。默认限制为单文件 10 MiB、100000 数据行、200 列；仅本地逻辑验证，不保证 NTFS 强隔离。

## 技术执行（给开发或管理员）

仅在已授权的本地 Python 3.10+ 环境运行；依赖 `openpyxl`，缺失即失败。进入解压后的 Skill 根目录运行：

```bash
python scripts/reconcile.py --config examples/minimal-config.json
```

相对路径按运行时工作目录解析；真实数据请显式指定 `supplier_input.path`、`internal_input.path`、XLSX `sheet`、`output_dir`，CSV 可声明 `encoding`（utf-8、utf-16 或 gb18030）。支持 `field_mapping`、`key_fields`、`amount_tolerance`、`amount_scale`、`allow_negative_amount` 和仅能降低的 `limits`。详细规则见独立产品源仓库的 `requirements.md`、`input-output-contract.md`（不随 Skill ZIP 打包）。机器状态码为 `MATCHED`、`AMOUNT_DIFFERENCE`、`ONLY_SUPPLIER`、`ONLY_INTERNAL`、`AMBIGUOUS`、`INVALID`，输出结构保持现状。失败退出 2 并输出错误码/错误对象，不伪造成功汇总。WorkBuddy 安装、执行权限、平台运行时和审核目前未验证，必须标记 `NOT_TESTED`/`BLOCKED`，不能写成平台验收通过。许可证类型/审核状态、安全限制、输入只读和输出独立目录保持现状。
