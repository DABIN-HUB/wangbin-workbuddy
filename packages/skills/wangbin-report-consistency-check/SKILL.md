---
name: wangbin-report-consistency-check
display_name: 经营报告数字一致性检查
display_name_en: Business Report Number Consistency Check
description: 对照 Excel 来源核查 Word 报告中的数字、单位与指标口径，输出可定位的差异清单。
description_zh: 对照 Excel 来源核查 Word 报告中的数字、单位与指标口径，输出可定位的差异清单。
description_en: Check figures in Word reports against Excel sources, accounting for units and metric definitions, with traceable differences and limitations.
version: 0.1.4
author: wangbin
examples_zh:
  - 这是月度经营报告和原始 Excel，帮我核对收入、成本和完成率，口径不同的先说明。
  - 检查报告里元和万元的换算，以及合计、占比有没有写错。
  - 我修改了原始数据，请重新检查报告，并说明相比上次新增或已经解决的问题。
examples_en:
  - Check revenue, cost, and completion rates in this monthly report against the source Excel file, identifying definition differences first.
  - Check currency-unit conversions, totals, and ratios in the report.
  - I have updated the source data. Recheck the report and explain which issues are new, resolved, or still pending.
---
# 经营报告数字一致性检查 / Business Report Number Consistency Check

在明确用户授权的本地 `input-root` 下接收 `source-xlsx`、`report-docx`（必填）；`context` JSON 和 `prior-run` JSON 可选，输出目录 `output-dir` 必填且为独立已存在授权目录。安装 Python 3.11+、openpyxl>=3.1、python-docx>=1.1。仅本地脚本验证；WorkBuddy 平台安装、模型自然语言调用、许可证和发布均 NOT_TESTED。

```bash
python scripts/check_report.py --input-root "<已授权输入目录>" --source-xlsx "<完整源xlsx路径>" --report-docx "<完整报告docx路径>" --output-dir "<独立输出目录>" [--context "<输入目录下JSON>"] [--prior-run "<上次JSON快照>"]
```

JSON 配置示例在 `templates/context.example.json`。仅在上下文不明确时向用户询问**具体**映射（sheet!cell）、主体、期间、实际/预算、币种/税、单位、计算和舍入；其他可核对项继续运行。`mappings` 可按指标名或 `段落1:收入` 提供；已确认的非预置指标（如净利润）也可核对，未确认派生公式不猜。`rules` 为确认过的白名单结构操作，不解释任意公式。`rounding` 必须明确 mode=ROUND_HALF_UP 与 places；`exact=true` 才声明非零原始差额为 MISMATCH。报告值－来源值为差额方向。公式缓存未经核实不作为已验证数值，Word 永不编辑。

对完成率变化，直接格格式 `0%` 下的 .10/.12 或普通格式且表头明确 `(%)` 下的 10/12 分别表示 10%/12%；输出 +2 个百分点与相对 +20%。缺单位的 .10 不猜作 10%；上期 0 时只算百分点，不能算相对增幅。公式格保留公式/缓存/位置并标未验证，不用缓存认定 MATCH。普通 Word 表格支持“指标｜数值”及“指标｜本月｜累计”的逐格对应；空值待确认，0 是数值。不同主体、期间、币种、税和实际/预算不可随意混合。

用户问询时先说明正文/普通表格范围与页眉、图片、图表、嵌入对象等未覆盖；运行 CLI 并回看五表：核查概览、指标对应、差异明细、待确认口径、未覆盖项；解释差异方向、来源文件哈希、位置、待确认问题与输出路径。用户重传来源时传上次 snapshot JSON，且输出到**新的独立目录**；输出变化类别但须核对报告版本，不能将失踪候选说成问题解决。平台实际多轮对话未测，不假装已调用。拒绝缺失、越界、伪装、恶意 OOXML 和不可信运算。单文件最大12MiB、展开最大480MiB、每表最多40000格、报告最多3000块、规则最多100格；超限 RESOURCE_LIMIT。仅输入原文件只读，输出不覆盖；不处理图像 OCR、复杂嵌入或整簿财务审计，人工复核未知定义与版权/许可。
