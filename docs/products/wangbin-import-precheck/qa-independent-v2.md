# Q01 独立 QA（T03，首轮）— FAIL / BLOCKED

- 产品 `wangbin-import-precheck`，分支 `skill/import-precheck`，工作区 `F:/ideaWorkSpace/wangbin-workbuddy-import-precheck`；冻结合同 `87d4be0df3ff400a8b175d3a33a3b01d8990600b`，被测源码及开发测试 `ee612333183507e4298da4a0003d3fdc85261a2b`。独立预期取权威 V2 §09–14、§32 和冻结 `acceptance-cases.md`，未从被测结果抄预期。仅本报告待单独提交，业务源码、ZIP、开发测试均未编辑。
- 候选 `dist/wangbin-import-precheck-0.1.2-skill-candidate.zip`，实算 SHA-256 `01f919ab6d4dd89ef0c6e934b0a95569b1ec59d7a28b892a283453de5bdde7e3`；ZipFile.testzip()=None；独立解压后实跑的脚本为 `wangbin-import-precheck/scripts/precheck.py`。成员/原始字节数：`README.md` 1400，`SKILL.md` 5054，`references/rules.md` 1862，`scripts/precheck.py` 24157（均位于 `wangbin-import-precheck/`）。侧车/工厂 verify 与实算哈希一致；不等于平台安装/审核。
- 独立测试脚本和完整 JSON 实际回执留在 QA profile scratch：`C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa_import_precheck_v2.py`、`qa_import_security.py`、`qa-import-v2/results.json`、`qa-import-v2/security-results.json`；输入/结果/解压产物同 `qa-import-v2/`。不读取开发者 demo。实际用 `uv run --no-project --with 'openpyxl>=3.1,<4' python <上述 QA 脚本>`；第一轮 QA 主脚本进程退出 1（断言 A12 差异失败，真实 shell `QA_EXIT=1`），安全补测退出 0 (`SECURITY_EXIT=0`，该退出码只代表探针完成，不是业务通过)。QA harness 修正了自己最初错误的候选列索引和全空行样例后重新运行，保留最终实测回执；未修改产品预期。

## 用例实测（来自独立解压程序，实际进程退出码）

|合同|实际及判定|
|---|---|
|IMP-01、03、04、06、07 / A01 CSV+XLSX|两次 exit 0，PARTIAL；分别是输入4、发现4、受影响3、重复组1；行2/3各重复、行3地区 R99、行5名称缺失；行4编号 `123` 与 `00123` 不合并；前导零文本留存、源 SHA 前后相同；变更表只有表头。`PARTIAL` 因 region required 未明示，正确保留未检查项。|
|IMP-02 / A02、A03|exit 0 PARTIAL：无模板为有限模式，目标规则未检查；两列争用目标时未静默选择，列待确认。|
|IMP-01 / A04|exit 2 REJECTED，原因 `SHEET_SELECTION_REQUIRED: 客户, 客户备份`，未静默选第一表；**状态不合冻结 NEEDS_INPUT/PARTIAL，见 D3**。|
|IMP-05 / A05、A06|缺参考表 exit 0 PARTIAL，发现3，不把 R99 认作无效；参考 R01 重复 exit 0 PARTIAL，发现5含 `REFERENCE_AMBIGUITY`，不随机采用，但**其发现定位为原客户文件，未给参考文件/工作表坐标，见 D4**。|
|IMP-03 / A07、A08|`0`、空和 `NULL` 三行（含非空定位 id 列）exit 0，只有空一项必填；日期歧义 exit 0 PARTIAL，格式未检查。XLSX 数值 0 专门例 NOT_TESTED。|
|IMP-06 / A09|exit 0，数值长编号得 TEXT_ENCODING_RISK/ PRECISION_RISK；数值 123 显示 00000 未被伪造为文本 00123。|
|IMP-04 / A10|两行组合键缺 country，exit 0 PARTIAL，分别必填两项、重复组0。|
|IMP-08 / A11|exit 0 PARTIAL；五表报告可用，另开候选/隔离两表；候选仅原行4的 `123`，隔离行2/3/5：`00123`、`00123`、`00007`；row_id 并集为4且无交集，原件未改。未授权 `--split` exit 2 REJECTED。|
|IMP-09 / A12|旧快照 R01/R02 发现4，新快照加入 R99 后 exit 0、发现3，旧文件仍在；**新回执/五表并未报告解决的旧发现、新旧差异或旧 run 关联，见 D1**。|
|安全 / A13|带 `=1+1`、`+SUM(1,2)`、`-1+2`、`@SUM(1,2)` 字面值 CSV 输入经 `--split` exit 0，报告和候选 XLSX 重开均无公式单元格。CSV 格式导出 NOT_TESTED（当前仅写 XLSX，不能据此证明 CSV 导出安全）。带 Excel 真公式输入 exit 2 REJECTED。|
|IMP-09 / A14|同源同规则再跑 exit 0；业务问题的行/类别及计数与 A01 一致，不覆盖旧报表。|
|格式/异常|坏 XLSX exit 2 REJECTED；无授权分流 exit 2；缺 `--header` 有效行 exit 2；符号链接测试因 Windows WinError 1314 无法创建，NOT_TESTED；20 MiB/5万行边界、大压缩炸弹、宏/外链、真正路径穿越与输出目录逃逸 NOT_TESTED。输入中的公式阻断实测；旧能力专项回归 exit 0：15 passed。|

五表分别为 `检查概览/字段映射/问题明细/变更记录/未检查项`，openpyxl 实际打开并回读行数据、冻结窗格/筛选配置；报告文件及候选均存在。结构 PASS；人工 Excel 视觉渲染 NOT_TESTED。`python -m tooling.products validate --id wangbin-import-precheck` exit 0、`verify --id ...` exit 0；`uv run --no-project --with 'openpyxl>=3.1,<4' --with pytest --with pyyaml python -m pytest -q --tb=short --basetemp C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/import-precheck-regression tests/test_import_precheck.py` exit 0，15 passed。这些自测/工厂校验不覆盖下列独立失败。

## 必须复修的缺陷（均可直接使用上述 QA scratch 真实输入复现）

**D1 高：IMP-09/A12 补参考表后不展示跨 run 差异。** 执行 `precheck.py --input <qa-import-v2/customers.csv> --output-dir <qa-import-v2/A01-CSV> --rules <qa-import-v2/core.json> --reference <qa-import-v2/regions.csv>`，再以新输出目录 `A12-new-reference`、参考 `regions-plus.csv` 重跑。预期旧行3 R99 发现保留在旧 run，新 run 报告/回执明确标记解决该发现并列出旧新依据，重复与缺名持续。实际两次分别4/3发现，旧文件仍在，但新报告/回执无 diff/run 对应及解决项；不能只靠人工比较两份另起名的文件达到“展示差异”。

**D2 严重：授权转换之后不重检唯一性，合格候选变成重复编码。** 见 `qa-import-v2/transform-unique.csv` 两行编码 ` A ` 与 `A`、`transform-rule.json` 要求 `code` 文本必填唯一。执行 `precheck.py --input <transform-unique.csv> --output-dir <security-output> --rules <transform-rule.json> --split --transforms '{"code":"strip"}' --authorization 'User explicitly authorizes trim and passing-subset split'`。预期转换后两行 `A` 构成重复、不得双双宣称合格候选（应重算且隔离/明确阻断）。实际 exit 0、发现0、候选两行均为 `A`、隔离0行；主报告写无阻断2。这违反 IMP-03/04/07/08，禁止放行候选。

**D3 中：多工作表未选被当作 REJECTED。** `--input qa-import-v2/multi.xlsx --rules core.json --reference regions.csv --output-dir <空目录>`；预期 NEEDS_INPUT 或 PARTIAL，明确选择哪张表；实际 exit 2 `{"status":"REJECTED","reason":"SHEET_SELECTION_REQUIRED: 客户, 客户备份"}`，把可补输入误报为不安全拒绝。修正状态但不得默认首表。

**D4 中：参考重复键的报告来源误指客户数据。** `--input customers.csv --rules core.json --reference duplicate-ref.csv --output-dir <空目录>`；预期 `REFERENCE_AMBIGUITY` 明示参考表文件 `duplicate-ref.csv` 和原始行2、3，才能回查冲突；实际该问题 `file=customers.csv, sheet='', line=''`，文字仅有 `duplicate reference key at lines 2,3`，源错指且未附参考文件，违反来源可核实要求。参考键不随机选这一点确实通过。

## 不把静态检查冒充实测

六条中英推荐提问按权威 V2 §14.9 与 `SKILL.md` examples_zh/en 字面逐条比对一致，**静态文案 PASS**；普通用户自然语言→自主规则提取、三条提问真实模型响应、连续多轮补文件/改规则/追问、WorkBuddy 真实安装运行、平台评测及审核均 **NOT_TESTED**，不能用 CLI JSON 试验冒充模型实测。规则 JSON 是测试内部夹具，不能证明用户不用手填 JSON 的入口已完成。ZIP 未包含 openpyxl/et_xmlfile wheels；WorkBuddy 环境依赖未知。候选没有独立明确产品许可证/权利证据，第三方依赖许可/作者声明需单独核验；**商业发布 BLOCKED**。不 push、不上传或登录平台。待经理建立独立开发修复卡（首次 QA 返工，最多两轮），修复后由 wb-quality 从新源码和新候选独立复验；本卡不以 review 取代失败。
