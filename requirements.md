# 供应商对账核对 MVP 需求

- **product_id**: `wangbin-supplier-reconciliation`
- **task_id**: `t_9d7ec034`
- **状态**: 0.1.0 历史需求基线；以 0.1.1 校准条款为当前默认合同。
- **来源/约定**: 用户冻结目标与本任务验收条件；T00 `t_d1a01c5a` 交接（worktree、基线及工厂边界）；现有产品文档仅用于差异分析。T00 未报告安全冲突，因此不绕过任何依赖。
- **产品根目录**: `F:/ideaWorkSpace/wangbin-workbuddy-supplier-reconciliation`
- **基线 commit**: `da8520f2a16a02f2fac6006717252d870fdef39b`

## 0.1.1 最小输入及规则

默认 basic 两侧仅需 `document_no,amount`；旧 `document_id` 为字段及映射别名。单供应商以 NFC/去首尾空白后的 `document_no` 唯一核对；同侧重复进入 `AMBIGUOUS`，不得择一。检测到不同 `supplier_id` 或显式 `matching_mode: "supplier"` 时启用 `[supplier_id,document_no]`，缺失 ID 的有效行进入 `AMBIGUOUS`/`SUPPLIER_ID_REQUIRED`、Excel Manual Review。若多供应商数据完全不提供 ID，程序无法可靠推断，调用方必须显式选择 supplier 模式；缺 ID 不猜测供应商。高级复合键仅通过 `matching_mode: "advanced"` 搭配 `key_fields` 或单独显式 `key_fields` 启用；两侧必须存在所选列。

默认 `amount_tolerance="0"`，以 Decimal 完全相等；20.00 对 20.01 为 `AMOUNT_DIFFERENCE`。非零容差仅显式传入且写入 `run.amount_tolerance`。不按零填空、不做模糊匹配。Excel 固定六表 `Summary`、`Matched`、`Amount Differences`、`Supplier Only`、`Internal Only`、`Manual Review`；后者同时承载 `AMBIGUOUS` 和带错误码/来源的 `INVALID`，Summary 的分类计数与结果行相同。Python 3.10+，需安装 openpyxl；在独立解压目录进入 Skill 根目录运行 `python scripts/reconcile.py --config examples/minimal-config.json`，相对路径相对运行目录；WorkBuddy 环境尚未验证。
- **来源/约定**: 用户冻结目标与本任务验收条件；T00 `t_d1a01c5a` 交接（worktree、基线及工厂边界）；现有产品文档仅用于差异分析。T00 未报告安全冲突，因此不绕过任何依赖。
- **产品根目录**: `F:/ideaWorkSpace/wangbin-workbuddy-supplier-reconciliation`
- **基线 commit**: `da8520f2a16a02f2fac6006717252d870fdef39b`

## 1. 用户与问题

面向采购、财务对账人员：将供应商对账单与内部采购/收货/应付明细按确定性业务键逐行核对，明确金额相等、金额不同、单侧存在、键不唯一和输入无效，保留可回看的来源文件、工作表与行号。MVP 只做可复现的规则核对，不作付款、税务、汇率、舞弊或信用判断。

## 2. MVP 范围

1. 输入一份供应商侧文件和一份内部侧文件，格式为 `.csv` 或 `.xlsx`；文件必须是用户明确选择的本地普通文件。
2. CSV 使用明确编码（默认 UTF-8/UTF-8 BOM；可选 UTF-16、GB18030 必须由调用参数显式指定）；XLSX 必须由用户显式选择工作表，绝不自动猜测工作表。
3. 通过固定字段别名映射读取业务字段；别名命中多个规范字段、规范字段映射多个源列或两列同名均报歧义，不静默覆盖。
4. 必填字段：`reconciliation_id`、`document_id`、`line_id`、`item_code`、`amount`、`currency`。推荐但非必填的展示字段：`supplier_id`、`document_date`、`quantity`、`unit`、`description`。
5. 默认确定性键：`reconciliation_id + document_id + line_id + item_code + currency`；调用方可显式指定一组键，但必须在两侧都存在且顺序固定，不能使用金额或行号作为键。
6. 金额使用十进制定点 `Decimal` 解析和比较；不得先转二进制浮点。默认金额精度为小数点后两位，金额差阈值由调用方显式指定（默认 `0.01`，不可为负）；不做币种换算，币种必须逐值相同。
7. 输出 JSON、XLSX、Markdown 三种结果；所有结果行带两侧来源文件名、工作表（CSV 为 `null`）和 1 起始数据行号。
8. 单次运行不联网、不执行单元格公式、宏、外部链接或输入中的脚本，不向日志写入原始整行内容；输出只写到用户指定目录。

## 3. 六类结果（互斥、可测试）

按输入顺序和稳定键排序确定输出顺序；每个确定性键最多一个结果。

| status | 定义 | 金额字段要求 |
|---|---|---|
| `MATCHED` | 两侧各恰有一条有效记录，键完全相等，币种相同且 `abs(supplier_amount - internal_amount) <= tolerance` | 输出两侧金额、差额 |
| `AMOUNT_DIFFERENCE` | 两侧各恰有一条有效记录，键完全相等、币种相同，但差额大于阈值 | 输出两侧金额、带符号差额、绝对差额 |
| `ONLY_SUPPLIER` | 仅供应商侧有一条有效记录，内部侧无该键 | 不把内部缺失金额写成 0 或空的数值结论 |
| `ONLY_INTERNAL` | 仅内部侧有一条有效记录，供应商侧无该键 | 不把供应商缺失金额写成 0 或空的数值结论 |
| `AMBIGUOUS` | 任一侧同一键出现两条或以上可解析记录，或字段映射/键定义导致无法唯一确定匹配 | 保留候选行引用；不得任选首行 |
| `INVALID` | 行缺必填字段、金额/币种/键格式非法、编码或文件结构无法解析，或金额精度超过约定 | 不进入金额汇总和匹配；记录稳定错误码与来源位置 |

重复键属于 `AMBIGUOUS`（不作首条优先）；格式、编码、结构和字段问题属于输入错误状态，若可定位到行则该行输出 `INVALID`。文件无法读取或缺工作表时运行失败并输出错误对象，不伪造六类结果。

## 4. 规则与不可推断项

- 空白字符串、`null`、`NA` 等缺失值不是零；缺失金额永不按零参与比较。
- 键字段按 Unicode NFC、去除首尾空白后比较；不大小写折叠，不去除内部字符，不猜测前导零。规范化前后原值均仅在受控输出中保留必要证据。
- `currency` 必须是三位 ASCII 大写 ISO 4217 风格代码；本 MVP 不验证该代码是否正在流通、不换汇、不跨币种合计。
- 金额只接受普通十进制数字（可有前导 `+/-`、千分位约定须由配置显式开启）；科学计数法、货币符号、公式文本和无穷/NaN 为 `INVALID`。负数是否业务允许由配置决定，默认允许并原样比较。
- XLSX 公式单元格读取缓存值仍不得作为已核实事实：实现必须默认拒绝公式单元格为 `INVALID`（或在结果中明确 `FORMULA_CELL`），不得执行公式；CSV 中以 `=`, `+`, `-`, `@` 开头的疑似公式字段按安全规则转义/拒绝，不能当作可执行表达式。
- 汇总只按币种分别统计六类计数和有效金额；两侧缺失金额不补零。任何模型/LLM 推断的供应商、键、币种、金额均不得进入结果。
- 来源追溯使用文件安全名称、显式工作表名、数据行号、规范字段到源列映射和输入文件 SHA-256；不记录绝对路径和原始整行。

## 5. 限制与安全边界

- 默认单文件最大 10 MiB、单工作表/CSV 最大 100,000 个数据行、最大列数 200；超限为 `INPUT_TOO_LARGE`，不部分运行。
- 仅接受 regular file，不跟随符号链接；拒绝目录、宏启用 XLSM、密码保护或损坏 XLSX、未知扩展名和超出编码声明的文件。
- 不上传、联网、执行宏/公式/外部链接，不修改输入；输出目录需由调用者指定且不得覆盖输入文件。输出文件名固定且安全净化，防止路径穿越。
- 本 MVP 不包含自动付款、发票入账、汇率转换、税额重算、OCR/PDF、模糊实体匹配、跨期归并、人工审批、平台安装/发布验证。

## 6. 与现有产品的独立价值

- **采购价格分析**（`packages/skills/wangbin-purchase-analyzer/SKILL.md`）只处理 UTF-8 CSV，按物料/规格/单位/供应商/币种/税务处理做价格趋势和供应商报价比较；它不做供应商文件与内部文件的逐键双侧存在性、重复键和金额对账，也不支持 XLSX/显式工作表。本产品的核心输出是双侧证据和差异状态，不是价格异常候选。
- **应收账款逾期分析**（`packages/skills/wangbin-receivable-analyzer/SKILL.md`）按基准日和币种计算未结/逾期账龄及客户级核查排序；它只有单侧应收 CSV，不比较供应商侧与内部侧，也不产生上述六类对账状态。本产品不推断逾期、回款优先级或客户信用。
- 因此本产品的独立业务价值是“同一确定性键的双来源完整性与金额一致性审计”，不是更换行业关键词或提示词。

## 7. 完成定义

后续实现必须能依据 `input-output-contract.md` 生成三种输出，并使 `acceptance-cases.md` 的每个用例达到预期状态、错误码、计数、来源行和安全行为；实现不得擅自增加模糊匹配、自动汇率或缺失值填零。