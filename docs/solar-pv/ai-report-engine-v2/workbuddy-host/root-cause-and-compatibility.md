# R2-0 原始失败诊断（开发源码只读）

## 结论

两份原始宿主响应均不能被原严格契约接受。本次没有新模型调用、accept/resume、JSON修补、生产/测试修改、依赖安装或UI操作；不是正式 wb-quality，也不是独立专业签审。

**重要计数纠正：91 / 106 是 claim–paragraph 违规发生数，不是独立违规 claim 数；独立 claim 数分别为 85 / 99。** 地面历史148条观察是106条段落发生记录与42条支持状态记录的集合，不能当作148条独立claim，也不能与本次结果机械相加。

| 原始观察 | 屋顶 | 地面 |
| --- | ---: | ---: |
| request 字节 | 341233 | 342119 |
| response 字节 | 113537 | 109527 |
| 小节 / 段落 / claims | 6 / 30 / 144 | 6 / 24 / 144 |
| 自然语言字段检查数 | 369 | 342 |
| 数字命中字段 / token发生数 | 26 / 26 | 14 / 14 |
| 不同命中token | 8 | 5 |
| 段落绑定违规独立claims | 85 | 99 |
| 段落绑定违规发生数 | 91 | 106 |
| 涉及的不同段落 | 17 | 16 |
| SUPPORTED状态冲突claims | 0 | 42 |
| 已声明fact对应source遗漏claims | 0 | 0 |
| 缺失段落fact的来源不在claim.source_refs发生数 | 0 | 0 |
| 额外风险断言阻断claims | 4 | 3 |

## 数字不是业务数值，但仍被当前正文规则拒绝

屋顶26次命中：正式章/节ID 9次、正式表格ID 11次、`PHASE1_METHOD_REVIEW_REQUIRED` 6次。地面14次：正式章ID 6次、表格ID 8次。本样本这些命中中没有裸指标值、百分比、年份、金额或未核实技术版本号；中文数词不属于 `isdigit()` 覆盖，仍需语义审核。

`original-failure-map.json` 的 `cases.*.numeric_hits` 逐项保留JSON Pointer、准确token、字段内偏移、上下文片段及分类。分类使用已登记规格章/节、该请求表格/公式和公式状态的精确集合，不将宽泛正则匹配当作授权。**正式注册不等于允许写入正文**：当前 `check_text` 只剔除合法fact/term槽后，任何 `isdigit()` 字符仍阻断。

## JSON闭合与写入

- 屋顶完整JSON合法，内部output Schema通过，严格chapter验证首先返回 `CHAPTER_UNBOUND_NUMBER`。
- 地面原始JSON返回 `INVALID_JSON`。解码器在字符84189、UTF-8字节109527（EOF），第299行第1列报告缺分隔符；字符串感知的括号栈确认只余偏移0的最外层 `{` 未闭合。
- 地面既有output在字符区间 `[154, 84188)`、字节区间 `[154, 109526)` 已完整闭合，之后只有换行。仅对该原始区间执行 `raw_decode` 作诊断，**未生成补括号后的响应**。其Schema通过，严格chapter验证仍首先返回 `CHAPTER_UNBOUND_NUMBER`。
- 宿主Write内部是否原子，不能从最终字节认证。当前手动宿主协议要求直接Write最终response，未展示经过验证的暂存/完成发布流程；地面不完整最终文件证实“文件存在”不足以作完成标记。
- 引擎自身 `Workspace._write` 有临时文件、fsync、原子独占发布机制，不能把它当作宿主Write已使用的实现。`serialization.loads` 会拒绝坏JSON；本次没有执行accept来证明运行时链。
- 人工停止不是远程timeout认证；不能凭这些单次样本推断模型固有上下文/输出上限。

## Claim与来源根因

每条claim按其原始 `paragraph_indexes` 求所指段落全部 `[[fact:...]]` 集合，逐段减去该claim的 `fact_refs`，同时计算所有缺失事实的 `source_ids` 与claim来源缺口。明细完整记录于 `cases.*.claims`。

主因是claim多按单项事实写作，却绑定了包含多事实槽的整段。两案每节均用满24条claims，但Schema只规定1至24上限，scope中的24个ID是许可池，不是必须全部使用。来源缺口检查为零不能抵消fact缺口：本样本大量事实共享同一个synthetic来源，因此来源集合覆盖仍可能与事实集合覆盖失败并存。

地面42条 `SUPPORTED` 含 `ASSUMED`，违反仅允许 `CALCULATED/VERIFIED` 的既有basis规则；不能通过更改事实状态通过。

## 独立P0：额外SEMANTIC_RISK_BLOCKED

逐claim调用现有 `validate_risk_assertions`，不修改任何输入：

- 屋顶：`CH08.02-C17`、`CH08.03-C13`、`CH08.04-C12`、`CH08.05-C07`。
- 地面：`CH08.02-C10`、`CH08.03-C08`、`CH08.03-C09`。
- 除地面 `CH08.03-C08` 外，上述均是 `ZERO_VALUE/FORECAST` 引用 `ASSUMED`，不满足风险校验的已计算事实要求，即使值确为零、正文说“假设零”也不改变规则。
- 地面 `CH08.03-C08` 声明 `PAID_FEE/FORECAST`，却引用 `ASSUMED` 的更换预算cost，不是 `pilot:cash.*.transaction_cost_cash_paid` 已计算付款台账；其正文明确否认已付款，结构化风险声明与叙述不一致。

逐项路径、原声明、事实状态/值/来源与原文已写入 `risk_assertion_errors`。这些是额外机械门禁失败，不自动等于所有对应中文专业判断错误；不得删除应声明风险、改状态或加免责声明来绕过。自由文本是否还有“残值当现金”“模拟当实测”等问题仍须独立专业复审。

## 精确字节组成与启发式重复

主分区使用原始UTF-8跨度，互不重叠、总和精确等于原文件字节；不重新序列化估算。

| 原始字节分区 | 屋顶 | 地面 |
| --- | ---: | ---: |
| 六个claims数组value（含括号/原格式） | 75422（66.429446%） | 72669（66.348024%） |
| 非claim自然语言字符串token（含引号/转义） | 28083（24.734668%） | 17744（16.200572%） |
| 其它元数据、键、标点与空白 | 10032（8.835886%） | 19114（17.451405%） |
| 合计 | 113537 | 109527 |

“免责声明”不是结构化类型，因此仅报告**明确启发式**：检查全部自然语言字段，按句号/分号/问叹号/换行切片、strip，匹配脚本列出的限制/假设关键词正则；完全相同句块至少出现两次才归为重复，不做语义同义归并。

- 屋顶：14组、40次；全部重复发生解码UTF-8字节2198，超出首次部分1316；全部自然语言解码字节60700，对应3.621087% / 2.168040%。
- 地面：4组、12次；全部重复发生解码UTF-8字节627，超出首次部分414；全部自然语言解码字节44264，对应1.416501% / 0.935297%。

这些比例仅是上述启发式相对于解码自然语言的比例，**不是原始响应中免责声明的精确占比**，且与claims/body分区交叠，不可相加。逐组原文和发生位置保存在JSON。

## 有界建议（未实施）

1. 优先将正文编号/状态码换成自然读者语言，保留受控元数据；不放宽全局数字保护。
2. 新生成按实际段落覆盖写必要claims及真实来源，明确24是上限；不自动发明专业判断。
3. 明确SUPPORTED、ASSUMED和结构化风险声明的证据要求；保留全部原有风险负向规则。
4. 新run引入半成品与最终文件区分，完整解析和独占原子发布后才允许接受。先缩减无必要重复；若仍超长，再单独设计有界分节与同请求绑定汇总。
5. 不修改旧响应、不延长旧请求、不把只读开发校验冒充Skill安装或真实客户端E2E。

## 复现与范围证明

- HEAD：`9faf44b86f4bb99a8a1021e1b35c70a4a49571e9`；分支main。
- 引擎已提交目录Git tree：`198d2d70543194406ef09ab038651aba63c31c8f`。
- 实际读取源码清单SHA-256：`6a4f6ebb305ad79733c3f353bc212788afc2bdda543c760d81e9ccc47700ba63`，逐文件哈希和入口行号见JSON `source_index`。
- ZIP重新核验99成员、98载荷Manifest大小/SHA、CRC均通过；前后SHA仍为 `09b81e392bb07da74f4c83191925c33f7a5d78d1ab41f3e7604f19f5e05f6aaf`，未执行ZIP内代码。
- 实际运行 `verify_diagnosis.py`：更新本任务自生成诊断map退出0、重新计算全量对比 `--verify` 退出0、`--negative` 退出2。确切argv、stdout/stderr、耗时及文件SHA见 `execution-receipt.json`。
- 开发解释器通过明确的两个源码路径调用现有validator，关闭pyc写入；不证明普通用户已安装依赖、不证明WorkBuddy使用同解释器。

独立只读重算命令（不会改写map）：

```bash
"C:/Users/wangbin/AppData/Local/hermes/installs/dff2a7c1aa1d2670/environments/3d191065334546e08496a64b86fa12ed/venv/Scripts/python.exe" -B "F:/ideaWorkSpace/wangbin-workbuddy/.runtime/solar-pv/ai-v2-host-protocol-r2-20261113-101239/diagnosis/diagnose_original.py" --verify
```

负向复现将同一命令最后参数改为 `--negative`，预期实际返回2。0仅表示诊断完成，不是章节通过。默认生成模式独占新建map；`--refresh-own-diagnosis`只用于更新本目录同scope、同ZIP身份的自生成map，不接受任意目标路径。
