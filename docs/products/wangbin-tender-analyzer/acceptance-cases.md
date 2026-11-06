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
