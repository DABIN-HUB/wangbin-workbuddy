# 双侧 CSV 核对输入输出合同（mvp-1）

对应 `requirements.md` 的 R01–R08。`left_missing` = 左侧没有、右侧有；`right_missing` = 右侧没有、左侧有，不能按报告阅读方向倒置。

## 输入与校验

| 规则 | 明确约束 | 失败码 |
|---|---|---|
| R01 路径 | 两个显式指定的、互不相同的现存普通 `.csv` 文件；输出为显式指定的目录，与输入文件不得相同；不得默认扫描目录或读取未授权文件 | `INPUT_PATH_ERROR`、`OUTPUT_ERROR` |
| R02 编码/CSV | UTF-8（允许文件开头 UTF-8 BOM），标准逗号 CSV，双引号可转义；严格解析，包括非法引号/编码时报错；首条记录必须是恰好 `id,amount`，大小写敏感、不可重复、不可有额外列；每条数据记录恰好两列 | `CSV_FORMAT_ERROR`、`SCHEMA_ERROR` |
| R03 id | 非空、非纯空白，保留原文，不 trim、不大小写折叠；在各自文件中完全相同的字符串只准出现一次（包括第一个有效 id 的重复）。`A` 与 ` A ` 是不同 id，空白包围非空 id 合法 | `EMPTY_ID`、`DUPLICATE_ID` |
| R04 amount | 必填、不可空/纯空白；十进制字符串正则 `-?(0|[1-9][0-9]*)(\.[0-9]{1,2})?`，只允许整数/1～2 位小数，非科学计数法、非逗号千分位、无 `+`、无空格；允许负数与零；精确 Decimal 转换且不得用二进制浮点 | `INVALID_AMOUNT` |
| R05 比较精度 | 同 id 以 Decimal 精确比较，`1`、`1.0`、`1.00` 等值；输出金额定为两位小数（`1.00`）；不四舍五入超精度值，超精度即 R04 错误 | `INVALID_AMOUNT` |

CSV 文件中的第一行是物理第 1 行表头；报错 `row` 使用 CSV 逻辑记录序号，从 1 开始（多行引号记录仍占一个序号）。仅有表头的文件合法，空字节文件/缺表头报 `SCHEMA_ERROR`。重复 id 报第二次出现记录的行号。标识符和金额不得由模型生成或猜测。为避免 CSV 公式注入，输出 `id` 仅用 CSV 引号无法安全消除电子表格执行风险：对以 `=,+,-,@` 或控制字符开头的 id 拒绝并报 `INVALID_ID`；此约束同时用于输入校验（金额的负号不受此限制）。

## 分类规则 R06

两侧分别建以原样 id 为键的唯一记录集；取并集，每个 id 恰生成一条明细：

| 条件 | 分类 | 可用金额 |
|---|---|---|
| 左右均存在且 Decimal 相同 | `matched` | 两者均有 |
| 仅右侧存在 | `left_missing` | 仅右侧有；左侧为空 |
| 仅左侧存在 | `right_missing` | 仅左侧有；右侧为空 |
| 左右均存在且 Decimal 不同 | `amount_mismatch` | 两者均有 |

CSV 空格子表示该侧**不存在**，不是 0；存在且金额为 0 时输出 `0.00`。不输出未经验证的差额或合计金额。

## 成功输出 R07

指定输出目录下固定五个文件：`matched.csv`、`left_missing.csv`、`right_missing.csv`、`amount_mismatch.csv`、`summary.json`。四份 CSV UTF-8、逗号分隔、CRLF/LF 任一稳定一致，表头固定为 `id,left_amount,right_amount,left_row,right_row`；仅缺失侧的 amount 和 row 留空，存在侧 row 为输入逻辑记录序号。所有文件按原样 id 的 Unicode 码点升序排列（空分类也保留表头）。JSON UTF-8，固定键：

```json
{"status":"ok","matched":1,"left_missing":1,"right_missing":1,"amount_mismatch":1,"distinct_ids":4}
```

数量为非负整数；四类数量之和必须等于 `distinct_ids`，也等于两个输入 id 集合并集大小。输出目录不存在时允许新建；已有输出目录只允许不存在目标五文件，若目标已存在报 `OUTPUT_ERROR`，不得覆盖。可用安全临时文件原子提交完整的五文件；发生失败时清理本次临时文件，任何失败不得留下本次部分生成的五个目标文件。

## 失败输出 R08

校验顺序为 R01 路径 → 左文件 R02–R04 全量 → 右文件 R02–R04 全量 → 输出目标可写性/冲突 → 比较与写出。失败返回非零退出码（建议 2），stderr 可解析单行 JSON：`{"status":"error","code":"EMPTY_ID","side":"left","row":3,"message":"..."}`；无法定位的 `row` 使用 JSON `null`，无侧别时 `side` 为 `null`。错误码限上表及 `INVALID_ID`、`INTERNAL_ERROR`；`message` 只描述原因，不泄露文件内容。失败不得打印成功汇总；`INTERNAL_ERROR` 不吞掉原始失败导致误报成功。输入缺数据与非法数据始终失败，不能用零替代。
