# 验收用例（mvp-1）

适用 `requirements.md` / `input-output-contract.md`。以下内容都是**虚构 CSV**，保存为 UTF-8；示例所示每行以换行符结束。所有成功用例在全新空输出目录运行，核查固定五文件、同一表头、升序和 `summary.json`。失败用例核查非零退出、stderr JSON 码/side/row、无本次成功输出文件。此文件定义预期，**不是测试已执行证明**。

## A01 四类各一（R02–R07）

`left.csv`：
```csv
id,amount
A,1.00
B,2.00
D,4.00
```
`right.csv`：
```csv
id,amount
A,1
C,3.00
D,4.01
```
四文件逐行预期（文件第一行均为 `id,left_amount,right_amount,left_row,right_row`）：

| 文件 | 数据行 |
|---|---|
| matched.csv | `A,1.00,1.00,2,2` |
| left_missing.csv | `C,,3.00,,3` |
| right_missing.csv | `B,2.00,,3,` |
| amount_mismatch.csv | `D,4.00,4.01,4,4` |

`summary.json` 与合同示例精确等价（键顺序与空格不限定）。断言四类并集 `A,B,C,D` 且无 id 重复出现。

## A02 精度与零非缺失（R04–R06）

左：`id,amount\nX,0\nY,-1.2\n`；右：`id,amount\nX,0.00\nY,-1.20\n`。预期 `matched.csv` 两行 `X,0.00,0.00,2,2`、`Y,-1.20,-1.20,3,3`；其余三文件仅表头，summary 为 `matched=2,left_missing=0,right_missing=0,amount_mismatch=0,distinct_ids=2`。

## A03 两表只有表头（R02、R07）

左右各 `id,amount\n`；四 CSV 仅表头，summary 五个计数全为 0 且 `status=ok`。

## A04–A12 无效输入矩阵（R01–R05、R08）

除所示变体外左右均用 `id,amount\nA,1.00\n`，输出目录全新；row 按**逻辑记录序号**：

| 用例 | 变体 | 预期 code / side / row |
|---|---|---|
| A04 | 左 `id,amount\nA,1\nA,2\n` | `DUPLICATE_ID / left / 3` |
| A05 | 右 `id,amount\n,2\n` 或 `id,amount\n   ,2\n` | `EMPTY_ID / right / 2` |
| A06 | 左 `id,amount\nA,\n`、`id,amount\nA, \n` | `INVALID_AMOUNT / left / 2`（不能作 0） |
| A07 | 右 `id,amount\nA,1.234\n` 或 `id,amount\nA,NaN\n` | `INVALID_AMOUNT / right / 2`（不取整） |
| A08 | 左表头为 `id,value\n` 或 `id,amount,extra\n` | `SCHEMA_ERROR / left / 1` |
| A09 | 右 `id,amount\nA,1,extra\n` | `CSV_FORMAT_ERROR / right / 2` |
| A10 | 左为无效 UTF-8 字节 `ff`；或未闭合引号 `id,amount\n"A,1\n` | `CSV_FORMAT_ERROR / left / null`（无法定位时） |
| A11 | 两输入指向同一文件；另次使用不存在的右路径 | `INPUT_PATH_ERROR / null / null`；`INPUT_PATH_ERROR / right / null` |
| A12 | 左 `id,amount\n=1,2\n`；另次在新目录已有 `matched.csv` | `INVALID_ID / left / 2`；`OUTPUT_ERROR / null / null`（既有文件保持原样） |

另验 R03：左 `A` 与 ` A ` 是不同 id；右仅 `A`，左文件 `id,amount\nA,1\n A ,1\n`、右 `id,amount\nA,1\n` 时 `matched` 为 `A`，`right_missing` 为 ` A `，计数 1、0、1、0、distinct_ids=2，不得自动 trim。另验 R08：左侧有 A04 错、右侧有 A07 错时优先报告左 A04；输入全部合法但目录不可写时为 `OUTPUT_ERROR`，没有部分结果。

## QA 核查清单

- 所有成功样例核验五文件名称/列顺序、JSON 解析后字段类型、四类互斥与数量守恒、两侧来源行号。
- 所有错误样例核验非零、side/row、无新目标文件；错误输入绝不回退为金额 0 或模型猜测。
- 本 T01 仅冻结文档；实际命令运行、代码版本及运行输出由下游实现/QA 报告记录，当前状态 `NOT_TESTED`。
