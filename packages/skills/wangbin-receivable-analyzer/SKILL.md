---
name: wangbin-receivable-analyzer
display_name: wangbin 应收逾期分析
display_name_en: wangbin Receivables Analyzer
description: 本地分析授权的应收账款 CSV，分币种核算逾期与账龄并提示异常。
description_zh: 仅处理用户明确选择的 UTF-8 CSV 应收明细，按基准日及币种输出金额、账龄、客户排序和核查清单。
description_en: Analyze authorized local CSV receivables with Decimal totals, aging and anomalies per currency.
examples_zh:
- 按明确基准日核对本地应收账款明细中的逾期发票
examples_en:
- Analyze the explicitly selected local receivables CSV at a given as-of date
version: 0.1.1
author: wangbin
license_candidate: MIT
license_status: REQUIRES_MANUAL_REVIEW
allowed-tools: Read, Bash
---

# wangbin 应收逾期分析

本 Skill 的 Python 脚本只在已授权的本地执行环境中处理明确提供的 UTF-8 CSV。WorkBuddy 普通 Skill 是否能提供 Python、文件路径或执行权限尚未验证：脚本在仓库中运行不等于平台安装或调用成功。

## 输入

固定表头 `invoice_id,customer_id,due_date,open_balance,currency`（其他列忽略），每行一张未结发票。`due_date` 严格按 `YYYY-MM-DD`，`open_balance` 为非负、不超过两位小数的未结余额，`currency` 为三位大写 ISO 风格代码。基准日 `--as-of YYYY-MM-DD` 必须由用户明确指定，使用日历日比较，**不自动使用当前日期，也不隐式转换时区**。一个文件最多 1 MiB，只接受非符号链接的普通 `.csv` 文件；不读取目录，不支持 XLSX、PDF、DOCX 或扫描件。输入未经业务授权检查，须先由用户确认来源。

```bash
python packages/skills/wangbin-receivable-analyzer/scripts/analyze_receivables.py --input "<已授权的 UTF-8 CSV 文件>" --as-of 2026-10-27
```

这是仓库 checkout 的本地命令，不保证上传 ZIP 后仍存在相同路径或 Python。若本地 Excel 文件需要转换，先使用仓库经过安全审查的离线工具；不要假设普通 Skill 自动提供 openpyxl 或 Excel 读写权限。

## 计算和输出

- 对每种币种独立计算 `totals.open`（有效行未结总额）和 `totals.overdue`（到期日严格早于基准日、余额大于零），绝不跨币种相加或换汇；金额用 `Decimal` 保留两位。
- `aging` 以逾期日历天数分 `1-30`、`31-60`、`61-90`、`91+`，到期当日不逾期。每桶的金额及发票数只来自有效且逾期的行。
- `customers` 按同币种逾期余额降序、客户 ID 稳定排序；超 90 天为高优先级核查，其余为中优先级，均是**人工核对建议**，不是自动催收、信用判断或法律建议。
- 重复 `invoice_id` 只保留首个出现的记录；缺字段、无效日期、非法币种、负数/非有限/超过两位小数的余额及公式样式内容均从统计排除，`issues` 仅列文本行号和固定错误码，不回显原行或本机路径。没有任何有效数据时返回非零码而非伪造零额结论。
- 计算输出仅写标准输出，不主动上传或记录原始明细日志；**输出仍含客户 ID 和聚合金额**，必须由获授权人员妥善保管。生成的 CSV 不执行公式、宏或任何输入代码。

## 验证和边界

虚构样例在 `@examples/fictional-receivables.csv`；执行相同命令并对照 `@examples/fictional-receivables.expected.json`。真实发票完整性、付款抵扣、争议款、客户身份及币种清算不由该 CSV 自动证明。平台安装、真实调用、审核与公开发布保持 `NOT_TESTED` / `BLOCKED`；本地校验、测试和打包不能替代 WorkBuddy 平台验收。
