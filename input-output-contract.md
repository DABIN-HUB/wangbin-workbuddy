# 供应商对账输入/输出合同

- **product_id**: `wangbin-supplier-reconciliation`
- **task_id**: `t_9d7ec034`
- **来源/约定**: 用户冻结 MVP、T00 `t_d1a01c5a` 交接；与 `requirements.md` 同版本冻结。

## 0.1.1 默认接口覆盖条款（下文示例为 0.1.0 历史高级配置）

默认配置只要求双方 `path` 和显式 `output_dir`，CSV 文件仅需 `document_no,amount` 两列表头；XLSX 同样两列但输入须提供精确 `sheet`。`document_id` 是 `document_no` 兼容别名（表头/field_mapping/key_fields）。无 `key_fields` 时 `matching_mode=basic`，键 `document_no`；显式 `matching_mode=supplier` 或检测到不同供应商编码时键 `[supplier_id,document_no]`，缺失供应商 ID 的有效行 `AMBIGUOUS`，`error_codes=["SUPPLIER_ID_REQUIRED"]`。多供应商且全部 ID 缺失无法自动发现，需显式 supplier 模式。`key_fields` 自动启用 advanced（也可显式 `matching_mode=advanced`），金额不可入键，所选列两侧表头均必需。默认容差 `"0"`，显式非零才生效；`run` 增加 `matching_mode`、`supplier_id_required` 并记录实际 `key_fields`/`amount_tolerance`。

XLSX 固定顺序为 `Summary`、`Matched`、`Amount Differences`、`Supplier Only`、`Internal Only`、`Manual Review`；Summary 每行 `currency,status,count`；其余五表共用 `status,result_id,key,supplier_amount,internal_amount,difference,absolute_difference,supplier_source,internal_source,sources,error_codes`。`AMBIGUOUS` 和 `INVALID` 一并进入 Manual Review，明细的 `status` 明确区分；空类别仍有表头。JSON 的 `summary.by_status` 是六种状态计数，总数等于五张明细表数据行之和，`summary.by_currency` 中缺币种标记 `UNSPECIFIED`，不做换汇或金额归并。行级错误仍保留在 `errors` 和 Manual Review；不再输出单独 Errors 工作表。
- **根目录**: `F:/ideaWorkSpace/wangbin-workbuddy-supplier-reconciliation`

## 1. 调用请求

实现应提供等价于以下字段的本地调用接口（CLI/函数名可不同，但语义不可不同）：

```json
{
  "supplier_input": {"path": "supplier.xlsx", "format": "xlsx", "sheet": "对账明细", "encoding": null},
  "internal_input": {"path": "internal.csv", "format": "csv", "sheet": null, "encoding": "utf-8"},
  "field_mapping": {
    "reconciliation_id": "对账批次",
    "document_id": "单据号",
    "line_id": "行号",
    "item_code": "物料编码",
    "amount": "含税金额",
    "currency": "币种"
  },
  "key_fields": ["reconciliation_id", "document_id", "line_id", "item_code", "currency"],
  "amount_tolerance": "0.01",
  "amount_scale": 2,
  "allow_negative_amount": true,
  "limits": {"max_file_bytes": 10485760, "max_data_rows": 100000, "max_columns": 200},
  "output_dir": "./out"
}
```

`field_mapping` 可使用规范字段别名表（中英文别名由实现固定登记并可审计），但显式映射优先。若未提供 XLSX `sheet`，即使只有一个工作表也返回 `SHEET_SELECTION_REQUIRED`；若名称不存在返回 `SHEET_NOT_FOUND`。CSV 的 `sheet` 必须为 `null`。

## 2. 输入文件和列合同

### 2.1 文件级

- `path` 必须是用户明确选择的 regular file，扩展名仅 `.csv`/`.xlsx`；禁止目录、符号链接、宏启用 `.xlsm`、密码保护和损坏文件。
- CSV 编码必须显式声明或是可无歧义识别的 UTF-8/UTF-8 BOM；声明与实际不符返回 `ENCODING_INVALID`，禁止静默替换字符。CSV 必须有一行表头，逗号分隔、双引号遵循 RFC 4180；坏引号/坏行返回 `CSV_PARSE_ERROR`。
- XLSX 读取不执行公式、宏、外链；工作表名必须精确匹配调用值。合并单元格造成必填列为空按行错误，不向下填充猜测。
- 第一行是表头，数据行号从 2 开始；空白尾行不计入数据行。原始位置结构：`{file_name, sheet, row_number}`。

### 2.2 规范字段

| 字段 | 类型/约束 | 必填 | 默认别名示例 |
|---|---|---:|---|
| `reconciliation_id` | 非空字符串，键规范化后仍非空 | 是 | 对账批次、批次号、reconciliation_id |
| `document_id` | 非空字符串 | 是 | 单据号、发票号、订单号、document_id |
| `line_id` | 非空字符串；按文本比较，`001` 不等于 `1` | 是 | 行号、明细行号、line_id |
| `item_code` | 非空字符串 | 是 | 物料编码、商品编码、item_code |
| `amount` | 十进制字符串，最多 2 位小数；输出为字符串 | 是 | 金额、含税金额、总额、amount |
| `currency` | 三位 ASCII 大写代码 | 是 | 币种、货币、currency |
| `supplier_id` | 字符串 | 否 | 供应商、供应商编码 |
| `document_date` | `YYYY-MM-DD` | 否 | 单据日期、日期 |
| `quantity` | Decimal，非必填展示 | 否 | 数量、quantity |
| `unit` | 字符串 | 否 | 单位、unit |
| `description` | 字符串 | 否 | 描述、备注 |

一个源列不能映射为多个规范字段；同一规范字段不能由多个源列自动合并。无命中必填字段返回 `REQUIRED_FIELD_MISSING`；别名冲突、重复表头或显式映射不存在返回 `FIELD_MAPPING_AMBIGUOUS`。

## 3. 规范化、键和分类算法

1. 对每侧逐行做字段存在性、编码、格式、金额和安全检查；失败行生成 `INVALID`，不进入键索引。
2. 规范化键字段：Unicode NFC、去首尾空白；保留大小写和内部字符。按 `key_fields` 连接时使用长度前缀/结构化数组，避免分隔符碰撞。
3. 对每侧有效行按键建立列表。列表长度大于 1 的键生成一个 `AMBIGUOUS` 结果，带两侧全部候选来源行；不得任选首个。
4. 两侧均唯一时：两侧都有则比较币种（币种在默认键中已包含，若自定义键不含币种仍要求相同，否则 `AMBIGUOUS`/`INVALID` 需按错误策略明确，不得换汇）；差额 `supplier_amount - internal_amount` 为 Decimal。绝对差额不超过阈值为 `MATCHED`，否则 `AMOUNT_DIFFERENCE`。
5. 仅一侧唯一有效记录分别为 `ONLY_SUPPLIER` 或 `ONLY_INTERNAL`。另一侧缺失字段/无效行不应伪装成单侧缺失；该键同时保留相应 `INVALID` 行结果/错误引用。
6. `INVALID` 行结果的 `result_id` 由输入侧、规范化文件 SHA-256、工作表、行号、错误码稳定生成；唯一键结果的 `result_id` 由状态和结构化键稳定生成。

## 4. JSON 输出合同

文件名：`reconciliation.json`，UTF-8，稳定键序和数组排序；金额均为十进制字符串，缺失值为 JSON `null`，绝不用 `0` 表示缺失。

```json
{
  "schema_version": "1.0",
  "product_id": "wangbin-supplier-reconciliation",
  "task_id": "t_9d7ec034",
  "run": {
    "key_fields": ["reconciliation_id", "document_id", "line_id", "item_code", "currency"],
    "amount_tolerance": "0.01",
    "inputs": [{"side":"supplier","file_name":"supplier.xlsx","sheet":"对账明细","sha256":"..."}]
  },
  "summary": {"total_result_rows": 0, "by_status": {}, "by_currency": {}},
  "results": [
    {
      "result_id": "...",
      "status": "MATCHED",
      "key": {"reconciliation_id":"B1","document_id":"D1","line_id":"1","item_code":"M1","currency":"CNY"},
      "supplier": {"amount":"100.00","source":{"file_name":"supplier.xlsx","sheet":"对账明细","row_number":2}},
      "internal": {"amount":"100.00","source":{"file_name":"internal.csv","sheet":null,"row_number":2}},
      "difference":"0.00",
      "error_codes": []
    }
  ],
  "errors": [],
  "security": {"network":false,"formulas_executed":false,"macros_executed":false}
}
```

错误对象至少含 `code`、`message`（不含原始敏感值）、`side`、`source`（若可定位）、`fatal`。致命错误（文件不可读、工作表未选、缺必填表头、超限）可以没有 `results`，但必须有 JSON 错误且非零退出。

## 5. XLSX 与 Markdown 输出

- `reconciliation.xlsx`：工作表 `Results`（六类状态、规范键、两侧金额、差额、两侧来源文件/工作表/行号、错误码）；`Summary`（按状态和币种计数/金额）；`Errors`（错误码、侧别、来源位置、不可执行的消息）。所有单元格写入文本或数值时防止公式注入：以 `= + - @` 开头的外部值加单引号并标记 `SAFE_TEXT`；不写入公式；不含宏。
- `reconciliation.md`：包含运行元数据、输入文件名/工作表/hash、规则与阈值、按状态统计、逐结果表、错误与限制说明。Markdown 只展示必要标识和截断后的安全文本，不展示绝对路径、秘密或原始整行。

## 6. 错误码和退出语义

`INPUT_NOT_FOUND`、`INPUT_NOT_REGULAR_FILE`、`INPUT_TOO_LARGE`、`ROW_LIMIT_EXCEEDED`、`COLUMN_LIMIT_EXCEEDED`、`ENCODING_INVALID`、`CSV_PARSE_ERROR`、`XLSX_PARSE_ERROR`、`SHEET_SELECTION_REQUIRED`、`SHEET_NOT_FOUND`、`REQUIRED_FIELD_MISSING`、`FIELD_MAPPING_AMBIGUOUS`、`DUPLICATE_HEADER`、`INVALID_AMOUNT`、`INVALID_CURRENCY`、`INVALID_KEY`、`FORMULA_CELL`、`UNSUPPORTED_FORMAT`。可定位行错误进入 `INVALID`；文件级致命错误退出非零且不生成看似成功的汇总。