# Q06 FIX-6 · 统一事实判定需求冻结（增量；非 QA PASS）

`product_id=wangbin-tender-analyzer`；`task_id=q06-fix6-evidence-first/A`；工作树 `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；分支 `skill/tender-response-check`；写前 HEAD/远端均 `4fe1e9cd4bc88fc608c6af19e3b788fc4f42fed5`、状态干净；生产源码 Git blob `468a06be4f50cf45d21940daa3a05c8052d9747c`（`packages/skills/wangbin-tender-analyzer/scripts/check_response.py`）；写前查无 `fix6-*` 重名文件。冻结的是新增判据，不覆盖 `requirements.md`、`input-output-contract.md`、`acceptance-cases.md` 和 `fix5-*`，也不更改独立 QA 原始 expected。

## 用户、问题、产品差异

用户为提交投标响应前核对招标要求、回应与已交证明文件的投标团队。既有单文件招标解析只抽要求，既有 Q06 多文件核查能生成五表及 Markdown；FIX-5 的 0.2.10 虽在原 53+13+16 案均过，却在新 12 案中仅 7 过。独立业务价值是**按义务对象、时间和多条回应综合作证**，并独立判明**确实已提供的文件**与**正文是否支持**；不是改提示词、改名或加行业关键词。不能把出现相近词、首条肯定或附件名当满足事实。

证据：`qa-fix5-0210-independent-report.md` SHA-256 `e7f8bb2e09bc2cba9a8f7fbdab6ad01c1e75babbd416ea97a8d84fffd698dd75`；`qa-fix5-0210-fresh-predeclared.json` `b9bfcc519934afd18ad65ae48c98c476ab3cea8ea8fe78fba8cfb69ecb78bca2`；`qa-fix5-0210-independent-results.json` `a7886ea08aba45199332a8477f24ed9f5bc518af6db48de138d1fa4a56e90656`；`qa-fix5-0210-independent.py` `0a9c6989fd29e34e8b4aa64281141bc694c343d652b9c8ef8518a03b5fc47bdc`。0.2.10 精确 ZIP SHA-256 `d11c09bff946ad128ee802d2c49d4e349af9c5393c48de7938ea69ffb53ca0e7`；当前源码文件 SHA-256 `710c3659953469b736ee04e14943419a15fa70de9e8ea53c27abaa2f702df1d8`。完整原件、输出哈希和逐案四维见 `fix6-acceptance-cases.md`。原 QA 结论 `LOCAL_QA_FAIL`，CLI exit 0 不构成业务 PASS。

## MVP 可测规则

| ID | 冻结判据 | 来源/差异 |
|---|---|---|
| F6-01 | 每条招标义务建独立对象、动作、条件、时态及 `文件:行`；以明确编号及对象语境绑定**所有相关回应**，编号不相同但明确同对象的第二条不得丢弃；编号相同但指向其他对象的句子不得借用；多对象不互借肯否、证据。无法唯一归属则候选待确认并保留行号，不猜归属。 | F04 `response.md:1,2`、F05 两义务；原 F5-01 仅单条挑选。 |
| F6-02 | 在已绑定同对象同当前时点事实集上判别：只有明确当前可用→有限文本已覆盖；明确当前不能运行/不可用且无同时间正证→可能不充分+确定缺口；明确“是否可用尚无核实结论”→待确认+原因；仅未来计划/条件不能覆盖当前义务，若同时明确当前不可用按确定不足；当前肯否两句并存→冲突待确认并同时引用两侧，输入行顺序/编号交换不得影响判断。未知不等于零、否定或肯定。 | F01/F02/F04/F05；与 H06、Z04、F03 等正反基线并存。 |
| F6-03 | 功能义务的“已覆盖”必须有已绑定的同对象、同时态、明确肯定证据；**禁止最终 token 交集兜底**，不能用相近词/候选名回升 `UNKNOWN`、当前否定、未来或冲突；不得为免误报把所有肯定降为待确认。 | `check_response.py:303–319` 的 `covered()` 后备分支；F01/F02/F05。 |
| F6-04 | 文件存在与正文证明力分开：显式提交可读文件即“已提供（可读文本）”；同文件明确“证照正文未附，当前仅有封面页”等词序变体→“不支持（文本层面）”、条件可能不充分、确定需补正文且引用否定行。仅标题无明示缺正文、部分摘要/证明力不明→待确认；有对应义务的明确正文正证→有限文本支持；同一文件正反正文并存→两行待确认。没给文件→仅已提供范围的未提供/未核验，绝不推断现实企业资质。 | F08、F07/F09/F10/F11/F06/F12；`material_assessment()` `:439–450,:484–492`。 |
| F6-05 | 结果保持四维、五表和 MD 同一义务及行源一致，概览逐维计数来自矩阵；确定缺口不得进入“已覆盖”，未知/冲突不得进入确定需补或已覆盖；附件行同步提供与支持状态。 | 原 QA 五表/MD；F01/F02/F04/F05/F08。 |

保留既有非功能合同：只处理用户授权显式给出的本地材料，不自动扫描/上传；安全路径、普通文件、UTF-8、大小上限、拒绝覆盖、公式注入防护、限长脱敏、无私有绝对路径、旧错误码均不弱化。旧 `analyze_tender.py --input` 单文件 JSON 快照、准备模式、补遗与版本、原 53+13+16+12 **94 项旧输入及 expected** 均为不可变回归门槛；错误五例加正控另计，不以旧组全绿抵消新失败。

不做：不改 Q01–Q05、光伏、主仓工作区、历史产品、许可证或原 QA 证据；不写业务源码、不提交、不 push、不 merge/rebase/强推、不上传或发布；不认证证照真伪、法律效力或中标，不以缺失数据作零。开发者动代码前须由授权角色仅限这三份合同路径单独 commit；QA 独立先冻结机制变体 expected/输入 SHA，再由开发修复并从精确 ZIP 独立验收。普通 push 仅由有权限角色/经理核验提交后在授权阶段进行，失败有限次重试并 `git ls-remote --heads origin skill/tender-response-check` 核对远端 SHA，禁止强推。合同冻结不是新版 QA PASS；宿主、平台、许可、人工相似性、发布均 `NOT_TESTED`。
