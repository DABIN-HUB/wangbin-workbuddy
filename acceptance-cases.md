# 供应商对账 MVP 验收用例

- **product_id**: `wangbin-supplier-reconciliation`
- **task_id**: `t_9d7ec034`
- **来源/约定**: 用户冻结目标与任务验收条件、T00 `t_d1a01c5a` 交接；输入输出详见同目录 `requirements.md` 与 `input-output-contract.md`。
- **执行前置**: 每例使用临时普通文件和显式输出目录；不得联网。除特别说明，金额阈值为 `0.01`、键为 `reconciliation_id,document_id,line_id,item_code,currency`，行号从表头后第一行计 2。

## 验收矩阵

| ID | 场景与输入 | 预期结果（必须逐项断言） |
|---|---|---|
| A01 | 两侧 CSV，各一行：键 B1/D1/1/M1/CNY，金额均 `100.00`，UTF-8 | 退出 0；恰有一条 `MATCHED`，`difference="0.00"`；双方来源行正确；JSON/XLSX/MD 均生成且 schema/product/task 正确。 |
| A02 | 同键两侧金额 `100.00` 与 `100.02` | 恰有一条 `AMOUNT_DIFFERENCE`；差额为 `-0.02`（supplier - internal，按实际侧值断言）、绝对差额 `0.02`；不生成 MATCHED。 |
| A03 | 仅供应商有有效键 S1；仅内部有有效键 I1 | 分别为 `ONLY_SUPPLIER`、`ONLY_INTERNAL`；缺侧金额为 `null` 而不是 0；来源行可回溯。 |
| A04 | 一侧同一完整键两行金额 10、20，另一侧一行 | 仅该键一个 `AMBIGUOUS`；候选来源行包含重复侧两行和另一侧行；不得首条优先、不得 AMOUNT_DIFFERENCE。 |
| A05 | 行缺 `currency` 表头或请求映射找不到 `amount` | 表头缺失为致命 `REQUIRED_FIELD_MISSING`、非零、无成功汇总；若仅一行缺值则该行 `INVALID`/`INVALID_CURRENCY` 或 `REQUIRED_FIELD_MISSING`，不进入匹配。 |
| A06 | amount=`abc`、`1.234`、`NaN`、`=SUM(A1:A2)`；currency=`人民币`；空键字段 | 各行均为 `INVALID`，错误码稳定（`INVALID_AMOUNT`/`FORMULA_CELL`/`INVALID_CURRENCY`/`INVALID_KEY`）；没有把无效金额当零。 |
| A07 | 同一文件重复表头 `amount,amount`，或别名同时有“金额”和“含税金额”且未显式映射 | 非零 `DUPLICATE_HEADER`/`FIELD_MAPPING_AMBIGUOUS`；不猜测列、不覆盖、不生成成功结果。 |
| A08 | XLSX 含 `对账明细`、`汇总` 两工作表，请求明确选择 `对账明细` | 只读取指定表，来源 sheet 精确为 `对账明细`；`汇总` 中同键内容不得进入结果。 |
| A09 | XLSX 多工作表但未传 sheet；传不存在的 sheet 名 | 前者 `SHEET_SELECTION_REQUIRED`，后者 `SHEET_NOT_FOUND`；均非零，不自动选第一张/最像的一张。 |
| A10 | CSV 分别为 UTF-8 BOM、显式 UTF-16、显式 GB18030；再以错误编码声明读取 | 正确声明的文件可解析且结果稳定；错误声明返回 `ENCODING_INVALID`，禁止替换乱码后继续。 |
| A11 | 输出/输入字段含 `=1+1`、`+cmd`、`@user`；XLSX 输入含公式单元格或宏启用扩展名 | 不执行公式/宏；行标 `FORMULA_CELL` 或安全拒绝；输出 XLSX 对危险前缀使用安全文本（不新增可执行公式）；`.xlsm` 为 `UNSUPPORTED_FORMAT`。 |
| A12 | 文件超过 10 MiB；CSV 数据行超过 100,000；列超过 200 | 分别为 `INPUT_TOO_LARGE`、`ROW_LIMIT_EXCEEDED`、`COLUMN_LIMIT_EXCEEDED`；非零；不部分输出成功汇总。 |
| A13 | 同键值含前导零 `001` 与 `1`，大小写 `abc` 与 `ABC`，Unicode NFC 等价文本 | 前导零/大小写不同不匹配；NFC 与去首尾空白后的等价键可匹配；原始来源行仍正确。 |
| A14 | 两侧金额 `-1.00`、`0.00`、不同币种 USD/CNY；自定义键不含 currency | Decimal 精确比较；不跨币种换算/相加；币种不一致不输出 MATCHED，按合同分类为 `AMBIGUOUS`/无效错误并可追溯；缺金额不补零。 |
| A15 | 同一键一侧有一个无效行，另一侧有有效行；另有完全无效文件 | 无效行单列 `INVALID` 并带行号/错误码，不伪装 `ONLY_*`；完全无效文件返回非零或仅错误对象，绝不生成全零成功报告。 |
| A16 | 运行两次，输入字节和配置完全相同；改变文件绝对路径但文件名和内容相同 | JSON 结果、`result_id`、排序、摘要一致（除运行时间若实现记录，时间不得参与 ID）；输出不泄漏绝对路径。 |
| A17 | 正常结果含 6 类状态后检查三种文件 | JSON 为机器合同；XLSX 有 Results/Summary/Errors 三表且无公式；MD 有规则、阈值、状态摘要、来源位置、限制；金额为 Decimal 字符串，null 不是 0。 |
| A18 | 请求路径为目录、符号链接、未知扩展名、损坏 XLSX、密码保护 XLSX | 分别返回 `INPUT_NOT_REGULAR_FILE`/安全拒绝、`UNSUPPORTED_FORMAT`、`XLSX_PARSE_ERROR` 或等价稳定错误；不读取目录/跟随链接，不上传。 |

## 六类结果覆盖断言

- `MATCHED`: A01。
- `AMOUNT_DIFFERENCE`: A02。
- `ONLY_SUPPLIER`、`ONLY_INTERNAL`: A03。
- `AMBIGUOUS`: A04、A14。
- `INVALID`: A05、A06、A10、A11、A15、A18。

## 验收执行与证据

开发者必须为每例保存脱敏 fixture、调用参数、退出码、三种输出存在性和关键字段断言；错误例还必须断言“不生成误导性成功汇总”。来源证据至少包含 `file_name`、`sheet`、`row_number`、规范字段映射和输入 SHA-256。不得以模型解释、猜测的币种/键/金额或本地通过替代 WorkBuddy 平台安装、调用、审核、发布证据；平台相关项保持 `NOT_TESTED`/`BLOCKED`，除非另有真实回执。