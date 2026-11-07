# wangbin-tender-analyzer · 独立验收案例（冻结预期）

来源：Q01 T00 附件19 §19.7–19.9；BID-01–08 和 `input-output-contract.md`。本页是**开发前冻结的预期**，非已经运行的测试结果。测试输入均为虚构 UTF-8 文本；以 1 起始行号标位，断言 XLSX 五表重开、MD 关联一致；测试可由独立 QA 实现，不修改预期迁就实现。新版 CLI 具体参数由开发者在 SKILL 写明，QA 使用真实命令与退出码记录，不得宣称未执行的结果。

## 公共断言

每个正常案例验证 XLSX 文件名、五表顺序 `核查概览/要求响应矩阵/附件核对/补遗与版本/待确认事项`，以及 `-提交前核对清单.md`；核查概览每维计数由矩阵重算，MD 的每条缺口与待确认均有 requirement_id 和真实 basename:行（清单用表名/CSV 行）位置。四维状态独立，不得把未知当 0 或通过。准备模式须醒目注明“响应未核查”。输出文本真实来源、限长脱敏，不得把材料文本“声称具备”写成资质真实性。对照差异均用 requirement_id + 原始编号 + 来源行 + 补遗关系定位，不能凭常识生成证据。

| 案例 | 虚构输入（每引号为对应文件的单行；未列的可选输入不存在） | 独立验收预期 / 规则 |
|---|---|---|
| BID-CORE-19.7 | tender.txt L1 `1. 必须提供指定资质证明 qualification.txt。`；response.txt L1 `1. 我方具备该资质。`；attachments.csv L1 `附件名称`, L2 `qualification.txt`；**没有**实际 qualification.txt。 | 精确编号找到响应且位置 `response.txt:1`；附件目录在 `attachments.csv:2`，但**实际未提供/仅目录登记**、内容 `未核验`、证据完整性不能通过；条件覆盖不能因“具备”而代替“提供证明”。明确建议补材料并核内容，不写“必然废标”。BID-01–04/06/08。 |
| BID-A02 | tender.txt L1 `2. 须说明运维响应时间。`；response.txt L1 `1. 我方具备资质。` | 要求 2 保留 `tender.txt:1`，响应 `未找到（限已提供响应）`、条件不能标覆盖；缺口指向要求 2，不把别的章节相似词作为回应。BID-02/06。 |
| BID-A03 | tender.txt L1 `3. 技术方案必须同时说明备份周期和恢复时间。`；response.txt L1 `3. 每日备份。` | 存在 `已定位`，条件 `可能不充分`，明确指出“恢复时间”未有响应依据；不能自动将四维都标通过。BID-02/03。 |
| BID-A04 | tender.txt L1 `4. 提供有效期覆盖2027年的资质证明。`；response.txt L1 `4. 资质有效期覆盖2027年，见 certificate.txt。`；certificate.txt L1 `本证明有效期至2026年12月31日。` | 实际附件 `已提供（可读文本）`，内容 `不支持（文本层面）`，列出 response:1 与 certificate:1 对照；不代替机构核验或伪造2027年证书。BID-03/04。 |
| BID-A05 | tender.txt L1 `5. 交付期为30日。`；amendment.txt L1 `正式补遗第1号：原第5条交付期30日替换为45日。`；response.txt L1 `5. 交付期30日。` | 旧要求仍可追溯但按有依据的替换边不再适用；新要求 45 日有效，响应沿用旧 30 日触发版本冲突，补遗表含双方行与关系原句。BID-05/06。 |
| BID-A06 | tender.txt L1 `6. 提供纸质两份。`；amendment-a.txt L1 `正式补遗A：原第6条改为纸质一份。`；amendment-b.txt L1 `正式补遗B：原第6条改为纸质三份。`；response.txt L1 `6. 提供纸质一份。` | 两补遗针对同一旧条款相互冲突且无确定相互优先依据：同时列两边及来源，`待确认`，不能按文件名/上传顺序选 B 或把 A 自动标为最终覆盖。BID-05。 |
| BID-A07 | tender.txt L1 `7. 系统须支持离线查询。`；response.txt L1 `7a. 系统支持离线查询。` | 可列候选关联，写出两端原文行及“编号变更、文本对应”依据；不得将无依据的编号变化当精确编号命中；需要时人工确认。BID-02。 |
| BID-A08 | tender.txt L1 `8. 提供同城双活灾备方案。`；response.txt L1 `8. 我方提供异地冷备方案。`, L2 `9. 我方提供同城双活机房简介。` | 8 的响应不能因 L2 相似章节出现“双活”而断言全覆盖；保留 8 条不满足/待确认条件与 L2 候选来源，不移花接木。BID-02/03。 |
| BID-A09 | tender.txt L1 `9. 必须附报价函。`；无 response.txt | 自动准备模式；输出要求与准备报价函清单，所有响应核查状态 `未核查`，不得把“无响应输入”算成“已检查未回应”；若用户**明确要求核查模式**则 `MISSING_RESPONSE` 非零。BID-01/06。 |
| BID-A10 | tender.txt 合法；response.txt 用非 UTF-8 字节或用户指定 `response.pdf`；另一个样本 attachments.xlsx 损坏 | 非 UTF-8→`INVALID_UTF8`，PDF→`INPUT_TYPE_UNSUPPORTED`，坏清单→`CATALOG_READ_FAILED`；非零且无完整两文件，不泄漏路径或正文；若经用户选择局部处理，输出必须标受影响要求与未核验范围。旧入口错误码/exit 2 单独回归。 |
| BID-A11 | 基于 CORE，第一次只有目录；第二次显式传实际 qualification.txt L1 `仅说明拟申请资质，尚未取得。`；有另一条独立要求 2 | 只有要求 1 的附件存在状态和聚合随输入改变；内容不能提升支持，旧“仅目录”缺口变成“材料内容不支持”；要求 2 内容/状态稳定。BID-03/07。 |
| BID-A12 | 现有 `tests/test_tender_analyzer.py`、原 `fictional-tender.expected.json`、原 `--input` 样例不改 | 运行原测试及旧 CLI：JSON stdout、资格/评分/技术/日期、同名日期冲突、待核实、120 字符内脱敏行证据、basename、隐私范围、未知实际得分 null、symlink/编码/超大拒绝；不能以新版成功替代旧回归。 |
| BID-A13 | 样本含一条已定位、一条未找到、一条只有目录、一个冲突补遗 | 四维统计与矩阵逐行一致；MD 已覆盖/未覆盖/待确认范围引用对应 ID、文件行及真实状态；清单不存在时不报“附件缺失已证实”。BID-06/08。 |
| BID-A14 | tender.txt L1 `10. 须附有效资质与近三年案例，投标截止日期另行通知。`；response.txt L1 `10. 我方正在准备材料。` | 输出不得添加证书号码、资质、业绩项目、合同/实际日期，也不得推断中标率、法定后果；日期未知并待核实。BID-01/08。 |

## 附加逆例（规则覆盖完整性）

- BID-01 重号：tender.txt L1 `1. 须提交A证明。`、L2 `第二章 1. 须提交B证明。` 与 amendment.txt L1 `1. 请说明C材料。`；不同 requirement_id、三条来源均保留，不覆盖/合并。
- BID-03 不需附件：纯叙述型要求已回应时，附件与内容维度仅能为 `不适用` 且有理由；缺目录不能被统计为无附件。
- BID-05 无依据关系：amendment.txt L1 `最终版：请提交三份。` 无正式替换出处/指定关系，只列待确认；文本中“最终版”不产生替换边。
- 安全与可追溯：同名附件清单两行、清单中的 `=HYPERLINK(...)`、重复输入 basename、输出名含 `../`、已存在输出、文件 symlink、加密 XLSX 必须拒绝或记录冲突/待确认；XLSX 表格单元格必须是安全纯文本，不执行公式/外链。单据文字不作为指令执行。

## 开发/QA 应运行并保存的命令与退出码（本轮仅冻结，**NOT_TESTED**）

从独立工作树根目录：

```text
python -m pytest -q tests/test_tender_analyzer.py
python packages/skills/wangbin-tender-analyzer/scripts/analyze_tender.py --input packages/skills/wangbin-tender-analyzer/examples/fictional-tender.txt
python -m tooling.products validate --id wangbin-tender-analyzer
python -m tooling.products similarity-check --id wangbin-tender-analyzer
```

开发者应另列出真实新版 CLI 运行命令，分别执行准备/核查/错误用例，重开 XLSX 检查五表、核对 MD 与矩阵；记录每条命令实际 exit code、stdout/stderr 摘要和输出文件 hash（不得伪造）。预期旧测试/旧样例/合法新输入 exit 0；错误新入口非零且无成功产物；`validate` 只能说明结构；`similarity-check` 即使 exit 0 也不能替代人工差异审查或许可证权利核查。历史预检 `similarity-check` 曾 exit 1/REVIEW_REQUIRED；本次没有重跑。发布、平台调用、用户许可、模型自然语言对话/双语六问、人工相似性复核全部 `NOT_TESTED`，须由后续授权角色独立验收。

## AUDIT-R1 BID-F01–F05：新增独立实文件矩阵（新版 NOT_TESTED）

所有下列用例**先由本表确定预期**，不从 actual/当前源码生成；各自建独立临时目录，真实 UTF-8 `tender.txt`、`response.md`，若写出则是对应文件的完整 L1 一行；`attachments.csv` 若列出则 L1 `附件名称,关联要求编号`，L2 为所写行；`.xlsx` 目录变体用表 `Sheet1` 的同两列/同 L1–L2；证据文件 `evidence.txt`/`certificate.txt` 为真实文件且**显式作为 evidence_files 参数提交**，并不凭目录名打开。每个正常用例从**新版最终 ZIP 干净解压**调用包内正式核查脚本，清理工作树 PYTHONPATH，参数由最终 SKILL/CLI 实际定义，输出至该例专用空目录；重新打开 `{项目名称}-投标响应检查.xlsx` 五表与 `{项目名称}-提交前核对清单.md`，按 requirement_id 逐格核对四维、行证据、冲突、确定缺口/人工确认及概览计数。没有目录/材料即不传这些参数；无附件义务时两材料维度应有理由地 `不适用`。所有正反结果仅为**文本层面**，不认证证照真伪。下表“旧实际”只据 `qa-audit-r1-old-023.md` 的**对应** L3 案例；未跑的变体标 NOT_TESTED，不混入历史已复现数。有效期比较对能确认的截止端可先下不满足结论，但正向证明覆盖**必须**起止和对象证据完整。

| ID / 缺陷 | 实际输入文件（各 L1，未注明即无可选输入） | 独立 expected（各维顺序：响应 / 条件 / 附件 / 内容；以及缺口/定位） | 旧 0.2.3 对应证据 / 新候选 |
|---|---|---|---|
| R01 F01 过期 | tender `1. 甲类资质须有效覆盖2028-01-01至2028-12-31，附甲类证明 certificate.txt。`；response `1. 甲类有效期覆盖该期，见certificate.txt。`；CSV L2 `certificate.txt,1`；certificate.txt `甲类证明：2027-01-01生效，有效截止2027-12-31。` | `已定位 / 可能不充分 / 已提供（可读文本） / 不支持（文本层面）`；明确截止早于目标止日，证据 certificate.txt:1，缺口及 MD 确定需补不能空。 | `date_expired_2028` L3 FAIL（旧内容待确认、无缺口）；新 NOT_TESTED |
| R02 F01 起点不足 | 同 R01，certificate.txt 改 `甲类证明：2028-01-02生效，有效截止2029-12-31。` | 条件不能覆盖整个要求区间，附件已提供、内容不支持；指出生效比起日迟一天，而不能只查截止日。 | NOT_TESTED / NOT_TESTED |
| R03 F01 正向签发/边界 | tender `1. 甲类资质须覆盖2027-01-01至2027-12-31，附certificate.txt。`；response `1. 甲类资质覆盖期间，见certificate.txt。`；CSV L2 `certificate.txt,1`；certificate.txt `甲类证明签发于2026-04-03，2027-01-01生效，2027-12-31失效。` | `已定位 / 已覆盖（文本层面） / 已提供（可读文本） / 支持（文本层面）`（内容与声明对应，双端同日闭区间）；签发2026不是冲突；状态限日期和文本承诺。 | `date_signed_valid` 另有跨期正例 L3 FAIL；本边界 NOT_TESTED / NOT_TESTED |
| R04 F01 单签发 | 同 R03 的要求/回应/目录，certificate.txt `甲类证明签发于2026-04-03。` | `已定位 / 待确认 / 已提供（可读文本） / 待确认`；注明缺有效起止/期限，不能说过期或覆盖；MD 人工确认而非已覆盖/确定过期。 | `date_issue_only` L3 FAIL（误判不支持）；新 NOT_TESTED |
| R05 F01 多证书 | 同 R01，certificate.txt L1 `乙类证明有效期2026-01-01至2035-12-31。` L2 `甲类证明有效期2027-01-01至2027-12-31。`；目录仍指文件 | 甲类截止不足→`不支持（文本层面）`、甲类证据 certificate.txt:2；乙类证据不能填甲类缺口，即使文本顺序交换结论不变。 | `date_two_certs` L3 FAIL（旧无解释）；新 NOT_TESTED |
| R06 F01 年份平移 | 将 R01 所有明确 2028→2033、2027→2032，保持对象/文件/相对区间不变 | 四维及缺口分类与 R01 相同，实际日期与来源变为 2033/2032，不出现固定 2027/2026 文案。 | `date_shift_2032` 不同年组 L3 FAIL；本变体 NOT_TESTED / NOT_TESTED |
| R07 F01 目标歧义 | tender `1. 甲类资质须覆盖2028年，附certificate.txt。`；response `1. 甲类证明见附件。`；CSV L2 `certificate.txt,1`；certificate.txt `甲类证明签发于2027-02-02；有效期另行确定。` | 已定位、附件已提供；条件和内容待确认（要求“覆盖某年”的起止含义未明确且材料缺有效期），提示确认范围与有效期，不猜日期。 | NOT_TESTED / NOT_TESTED |
| R08 F02 否定 | tender `1. 必须支持自动备份。`；response `1. 我方不支持自动备份。` | `已定位 / 可能不充分 / 不适用 / 不适用`；明确冲突 response.md:1，缺口非空，MD 不在已覆盖范围。 | `response_negated` L3 FAIL；新 NOT_TESTED |
| R09 F02 肯定 | 同 R08，response `1. 我方支持自动备份。` | `已定位 / 已覆盖（文本层面） / 不适用 / 不适用`，不得全待确认；MD 已覆盖该文本义务，不凭本例推出实际系统功能。 | `response_positive` L3 PASS（文本维度）；新 NOT_TESTED |
| R10 F02 双否定 | tender `1. 不使用外部云存储。`；response `1. 本方案不使用外部云存储。` | 与 R09 同四维，对象及否定作用域相同，不当作矛盾。 | `response_double_negative` L3 PASS；新 NOT_TESTED |
| R11 F02 附条件/未实现 | 同 R08，response `1. 若另行购买模块，我方才支持自动备份。`；再独立变体 `1. 我方拟于交付后支持自动备份，当前尚未实现。` | 均已定位，但无条件“必须支持”不能标已覆盖；前者条件限制保留并列缺口，后者当前尚未实现记冲突；附件两维不适用，MD 不误列已覆盖。 | `response_conditional` L3 FAIL（仅前者类似）；新 NOT_TESTED |
| R12 F02 否定隔离 | tender L1 `1. 必须支持备份。` L2 `2. 必须支持离线查询。`；response L1 `1. 我方不支持备份。` L2 `2. 我方支持离线查询。` | 两行 ID 独立：1 已定位/可能不充分且冲突；2 已定位/已覆盖；否定不能跨行，也不能把 2 的肯定抵消 1 的缺口。 | NOT_TESTED / NOT_TESTED |
| R13 F03 无文件名 | tender `1. 必须提供营业执照。`；response `1. 我方提供营业执照。` | `已定位 / 可能不充分 / 未提供（限已提供材料） / 未核验`；材料义务从 tender.txt:1 提取，附件核对有缺口，不适用禁止，未提供只限本次材料。 | `license_missing` L3 FAIL（旧两维不适用）；新 NOT_TESTED |
| R14 F03 仅目录 | 同 R13；CSV L2 `营业执照.txt,1`，无真实文本；另以同列 XLSX Sheet1 第2行分别重跑 | `已定位 / 可能不充分 / 仅目录登记 / 未核验`；目录来源 CSV:2 或 Sheet1:2 不是实际证据；两格式业务结论等价。 | `license_catalog_csv/xlsx` L3 PASS（仅目录维度）；新 NOT_TESTED |
| R15 F03 真材料但反证 | 同 R14，加显式实际 `营业执照.txt` L1 `本件是目录占位；营业执照正在申请，尚未取得。` | `已定位 / 可能不充分 / 已提供（可读文本） / 不支持（文本层面）`；正文反证行准确、不能因文件存在升格支持；只说本次文本不支持，不推断企业真实状况。 | `license_actual` 是不同的正例 L3 有限 PASS；本反例 NOT_TESTED / NOT_TESTED |
| R16 F03 真材料正例/重名 | 同 R14，实际 `营业执照.txt` L1 `营业执照文本：统一社会信用代码为虚构示例编号。`；另独立变体把 CSV L2 和 L3 重复 `营业执照.txt,1` | 单目录项+实际正文→附件已提供、内容只在“提供了营业执照文本”这一**有限声明**上可支持，不能认证真实有效；重复目录须保留待确认并列来源，不能任选一条自动支持。 | `license_actual` 有限文本关联 PASS；`license_duplicate` 待确认 PASS；新 NOT_TESTED |
| R17 F04 空条件 | tender `1. 须提供certificate.txt资质证明。`；response `1. 证书见certificate.txt。`；CSV L2 `certificate.txt,1`；实际 certificate.txt L1 `certificate.txt：仅为目录占位，不含证书。` | `已定位 / 可能不充分 / 已提供（可读文本） / 不支持（文本层面）`；材料仅文件名+明确否认，不得 `all([])` 支持；冲突/缺口写入矩阵、附件核对、MD。 | `filename_empty_conditions` L3 FAIL（已复现目录锚定 all([])）；新 NOT_TESTED |
| R18 F04 无目录变体 | 同 R17，不传目录，仍显式提交实际 certificate.txt | 若能凭明确指定和内容唯一关联：已提供且内容不支持；若关联不唯一：附件/内容待确认并保留候选，但**绝不支持**；记录所用关联依据。 | `filename_only` 旧未完整复现 all([])，本变体 NOT_TESTED / NOT_TESTED |
| R19 F03/F04 跨要求错配及增量 | tender L1 `1. 必须提供甲类资质证明。` L2 `2. 必须提供乙类资质证明。`；response L1 `1. 甲类证明已提交。` L2 `2. 乙类证明已提交。`；首轮仅目录 CSV `甲类.txt,1`、`乙类.txt,2`；次轮显式提供甲类.txt L1 `甲类证明文本：甲类有效。` | 首轮两条仅目录/未核验；次轮甲类可读且**仅对甲类文本声明**能支持，乙类仍仅目录/未核验，2 的 requirement_id/状态不变；不得拿甲类证乙类。 | NOT_TESTED / NOT_TESTED |
| R20 F05 旧接口/快照 | 从新 ZIP 解压的 `scripts/analyze_tender.py --input examples/fictional-tender.txt`；并运行已有 `tests/test_tender_analyzer.py` | 旧 JSON stdout/exit0/既有语义与**原包已冻结** `examples/fictional-tender.expected.json` 对照；旧非法输入错误码/exit2 保留。新样例 actual 不可重写历史 expected；SKILL 不再指示由 actual 更新 expected，解压路径可执行。 | `legacy_json` 与包内原快照旧 L3 PASS；SKILL:99 L1 FAIL；新 NOT_TESTED |

**每例共同交叉断言**：`要求响应矩阵` 的四维/缺口/来源为基准，`附件核对` 逐证据不将目录当实物，`核查概览` 各维每个状态数由矩阵重新计，`待确认事项` 只列未决且指 ID/来源，`补遗与版本` 无补遗时明确无提供；MD 分类/四维/位置与矩阵一致，R01/R08/R17/R15 不得进已覆盖且其缺口不能空，R03/R09/R10 不得用 blanket pending 躲避。附加回归原 BID-CORE/A02–A14（尤其正式补遗冲突/准备模式/错误输入/安全）不得消失；明确新入口缺响应 `MISSING_RESPONSE`、错误编码 `INVALID_UTF8`、损坏目录 `CATALOG_READ_FAILED` 非零且不得留两份成功文件。R06 将对象名/行顺序再变换一次，QA 在开发后另选未写进生产代码的年份、文件名及等义改写，记录实际 fixture 哈希、调用数组、exit、输出哈希和逐格差异，**不能凭这里固定值硬编码**。

**层级与放行界线**：旧 0.2.3 精确 ZIP SHA `5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce` 的旧 QA L3 机械重开通过但业务已阻断；旧 0.1.0 ZIP 物理原件 `NOT_VERIFIED`。本增量只有规格/独立预期，未执行新版 L1/L2/L3/L4/L5：均 `NOT_TESTED`。新 L3 需最终 ZIP、脱离源码树的实际文件、正式入口、XLSX/MD 回读；L4 需真实宿主模型拿原始资料用三类自然多轮问法执行，不是复制模板或预写 JSON；L5 需 WorkBuddy 实际安装和使用，未经权限不得声称。`validate`/ZIP结构、静态检查不能替代业务 L3；证照真实性、许可和人工相似性门禁分别未验，不可据本合同宣称发布。历史两轮 QA 原始 PASS/FAIL 不删除、不占用新阶段的最多两轮 QA 退回额度；新阶段首次集中修复后才开始计退回。
