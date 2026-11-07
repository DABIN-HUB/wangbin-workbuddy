---
name: wangbin-tender-analyzer
display_name: wangbin 招标分析助手
display_name_en: wangbin Tender Analyzer
description: 对照已授权招标文本、正式补遗和响应稿，检查漏答、附件证据及版本冲突；保留单文件分析。
description_zh: 对照招标要求、正式补遗和响应材料，检查漏答、附件证据与版本冲突。
description_en: Check bid responses against tender requirements and formal amendments, identifying omissions, missing evidence, and version conflicts.
examples_zh:
  - "这是招标文本和拟提交的响应稿，帮我检查漏答、缺证明材料和前后不一致的地方。"
  - "对照正式补遗重新核查标书，指出哪些响应还沿用了旧要求。"
  - "根据附件清单检查提交材料，只有名字但没有实际证据的项目单独列出来。"
examples_en:
  - "Check this tender and draft response for omissions, missing evidence, and inconsistencies."
  - "Recheck the response against the formal amendments and identify sections that still use superseded requirements."
  - "Check the submission against the attachment list and separate listed filenames from evidence that is actually available."
version: 0.2.13
author: wangbin
allowed-tools: Read, Bash
---
# wangbin 招标分析助手

## 0.2.13 自然对话与本地执行合同

本候选只按已绑定的同一功能对象聚合当前肯否、未知和未来事实；第二条明确同对象回应即使改编号也进入判定，其他对象同号不得借用。未知/仅计划不当成当前覆盖，明确当前不能运行不被词语交集回升；当前肯否冲突须引用双方并待确认。实际材料已提供与正文支持分开；同文件明示缺正文是该文件文本不足，正反证并存待确认，引用两侧各自限长脱敏正文摘录与真实文件行号供回原件审计，不推断企业现实资质。仅 PRE-QA 本地候选，未获独立业务 QA 验收。

用户用自然语言请求核查时，先确认招标 TXT/MD、响应稿 TXT/MD、是否准备模式、正式补遗、附件目录 CSV/XLSX、实际可读文本材料、项目名与输出目录；不要凭用户对话猜本机路径、读取目录或未经授权上传。仅当输入文件已由用户明确选择且确认授权，并且本地 Python + `openpyxl` 可用，才将路径逐一映射到以下真实 CLI。只说“核查”而缺响应时请求提供响应，不假装漏答；只有招标文本时可进入准备模式，并标“响应未核查”。附件目录只代表登记，实际材料必须以 `--evidence-file` 显式给出。请用户确认真实资格/保证金/版本关系及原件，不能声称已认证或已提交。自然语言路由及 WorkBuddy 宿主 Python/cwd/权限**未在平台实测**。

从仓库根目录调用（不是固定的 WorkBuddy 路径）：

```bash
python packages/skills/wangbin-tender-analyzer/scripts/check_response.py --tender "<已选择招标.txt>" --response "<已选择响应.md>" --mode check --amendment "<正式补遗.txt>" --attachment-catalog "<附件清单.csv或.xlsx>" --evidence-file "<实际材料.txt>" --project "<安全单段项目名>" --output-dir "<已存在的授权输出目录>"
```

运行前安装 Python 3.11+ 与 `openpyxl>=3.1,<4`（例如 `python -m pip install 'openpyxl>=3.1,<4'`，仅在经用户允许的本地环境）；若未安装先告知依赖缺失而非假定 WorkBuddy 提供。期限对照须区分证书签发日、生效日和有效截止日，只有同对象且双端来源明确才可证明整段覆盖；明确截止端不足或生效日晚于要求起日可据实列缺口，年份和对象不硬编码。肯否、双否定、无法支持、仅有设计文档/功能未上线和“购买后才支持”等前提按相同义务及当前功能状态比较；同一功能是否已上线尚待核实则标待确认，不可升格为当前支持，明确否定不降为未知。提交营业执照等无具体文件名的义务仍核查附件，目录不是文件，文件不等于内容支持；无目录但已明确提供与要求同名的可读材料时仍核验正文，不将实际材料误称缺失，亦不凭文件名宣称内容支持；明确提交的示例占位文件不构成材料文本支持，登记信息且正式证照资格尚待核实也不得判支持；无目录时按材料对象和文件正文双重关联，仅乙类文本不能冒充甲类材料；若目标或材料无法唯一对应则记录待确认而不伪造通过或冲突。四维状态分别说明依据；MD 已覆盖项不得包含确定缺口。仅输出文本层面结论，不认证证件真实性。

`--tender` 必需；省略 `--response` 为准备模式，`--mode check` 明确核查而缺响应报 `MISSING_RESPONSE`；`--mode prepare` 不接受响应稿；`--amendment` 与 `--evidence-file` 可重复且不扫描目录；清单可选。`--output-dir` 必需且目录须事先存在；`--project` 可省略并标“未提供项目名称”，拒绝越界/覆盖既有产物。只读 UTF-8 `.txt/.md`（每份≤1 MiB），仅目录支持 `.csv/.xlsx`；运行环境需 Python 3 与 `openpyxl`，不在 WorkBuddy 平台假定可用。解压 ZIP 时可将上述脚本路径换成 `<解压目录>/wangbin-tender-analyzer/scripts/check_response.py`，旧 `analyze_tender.py --input` 仍输出原 JSON。

成功时输出五表 `{项目}-投标响应检查.xlsx`（核查概览、要求响应矩阵、附件核对、补遗与版本、待确认事项）及 `{项目}-提交前核对清单.md`。编号精确匹配仍需确认上下文；语义候选不自动确认为回应，强制条件逐项对照文本，材料存在/目录登记/内容支持为不同状态。招标要求证明材料且唯一编号响应明确引用文件名、正文语境相关时可关联显式提交的材料；重复清单名称、跨要求编号冲突和响应候选歧义标待确认，不据任意同名文件认证。正式替代仅在补遗原句同时指明旧条款和改为/替换/撤销时生效；冲突补遗并列待确认，非正式说明不更新优先级。错误 `ERROR <CODE> role=<角色>` 返回 exit 2，不回显文件私有绝对路径或原文。脱敏不完备；只核提供范围，不证明证书/签署/保证金真实性，不推定中标率、法律后果、投标截止时间或 PDF/DOCX 解析。具体业务限制与案例见仓库 `docs/products/wangbin-tender-analyzer/`；ZIP 内请依据本段限制解释。

以下六句推荐语是静态引导文本，不是已完成模型对话的证据：

- 这是招标文本和拟提交的响应稿，帮我检查漏答、缺证明材料和前后不一致的地方。
- 对照正式补遗重新核查标书，指出哪些响应还沿用了旧要求。
- 根据附件清单检查提交材料，只有名字但没有实际证据的项目单独列出来。
- Check this tender and draft response for omissions, missing evidence, and inconsistencies.
- Recheck the response against the formal amendments and identify sections that still use superseded requirements.
- Check the submission against the attachment list and separate listed filenames from evidence that is actually available.

## 旧版单文件分析（兼容）

本 Skill 的旧单文件入口仍可运行。脚本只在本地进程中分析一个已由用户选择的 UTF-8 `.txt` 或 `.md` 文件；它不会验证用户是否拥有该文件的处理权限，不执行 PDF/OCR/宏/脚本，也不上传远程服务。结果只用于辅助核对，不替代采购文件原件、法律意见、人工评审或 WorkBuddy 平台审核。

## 输入和安全边界

- 输入必须是单个文件，扩展名为 `.txt` 或 `.md`（大小写不敏感）、regular file、非 symlink，且不超过 1 MiB。目录、symlink、其他类型、超大文件和非 UTF-8 输入以稳定错误码拒绝。
- 只处理用户明确选择并授权的文件；脚本**不验证授权**，因此结果不会声称“已授权输入”。不要扫描目录、读取无关文件或上传远程服务。
- 输入只读。脚本不故意把全文写入日志或缓存；输出只通过标准输出返回分析结果。不要把含有报价、联系人、证件、账号或其他敏感信息的文件交给未经授权的远程服务。
- `source_name` 仅输出文件 basename，不输出输入路径。证据中的 `line` 是 1 起始的文本行号，不是页码、坐标或模型推断。

## 在仓库 checkout 中运行

下面的命令是**仓库本地示例**，假设当前目录是仓库根目录、仓库文件存在且该本地环境有可用 Python：

```bash
python packages/skills/wangbin-tender-analyzer/scripts/analyze_tender.py --input "<仓库 checkout 中的已授权 .txt 或 .md 文件>"
```

Windows 路径使用双引号。命令只接受一个显式 `--input` 文件，不接受目录扫描。读取失败或输入不合规返回非零退出码和稳定错误码（例如 `INPUT_SYMLINK`、`INPUT_NOT_REGULAR`、`INPUT_TYPE_UNSUPPORTED`、`INPUT_TOO_LARGE`、`INVALID_UTF8`），不输出原文。

这条仓库路径和命令**不代表 ZIP 安装后仍存在**，也不代表 WorkBuddy 平台运行时的当前工作目录或 Python 可用性。平台安装和平台调用在本 MVP 范围内均为 **BLOCKED/NOT_TESTED**；本地脚本成功不能描述为已安装、可调用、已审核、已发布或真实投标成功。

## 输出字段

- `eligibility`：逐条资格/资质条款；`scoring`：逐条评分条款、可识别的满分和待核实得分；`technical`：逐条技术要求。`criterion`、`requirement`、风险描述等用户文本字段也经过上下文脱敏。
- `dates`：投标文件递交/投标截止、开标、报名、采购文件获取、答疑/澄清、投标保证金和合同签订等日期。日期变体会归一到相应名称；同一名称的重复值保留为多条，不覆盖。
- `checklist`：逐条绑定资格、评分、技术和日期证据，并额外检查保证金/押金、表单/函件、附件/证明材料、提交方式/份数/递交和签字/盖章/授权签署。文本中未发现的类别仍保留 `待核实` 项且 `evidence: null`。
- `risks`：歧义、缺失重要日期和重复/冲突日期。日期冲突风险的 `evidence` 是包含全部相关日期摘录的数组。
- `limitations`：扫描件、复杂版式、表格和附件的已知限制；不能据此生成页码、坐标、法律结论或实际投标得分。
- `evidence`：去重后的证据索引。每条包含 `source_name`、1 起始的 `line`、不超过 120 字符的 `quote` 和固定标签 `label: "redacted excerpt"`。摘录可能截断并会脱敏，**不是输入字节逐字证明**；回看原文件核对。
- 如需人工汇总与复核，可使用 `@templates/tender-checklist.md`；表内摘录仍须对照原始采购文件。
- `privacy`：明确 `execution_scope: "local_script_only"`、`authorization_verified: false`、`remote_upload: false`，并标出 `platform_installation`/`platform_call` 为 `BLOCKED/NOT_TESTED`。脚本不把本地执行结果升级为平台事实。
- 结论状态使用 `待核实` 表示文本不足以确认投标人是否满足、实际得分或条款含义。脚本从不生成 PASS、实际投标得分、法律结论、虚构页码或平台行为。

## 分析步骤

1. 在仓库 checkout 的本地环境中确认文件是用户明确选择的 `.txt`/`.md`、非 symlink、regular file、UTF-8 且不超过 1 MiB；完成后才执行脚本。
2. 运行命令并保留 JSON；检查每项 `evidence.line` 可回到该文本行。不要把 `quote` 当作逐字原文：它是限长、已脱敏的上下文摘录。
3. 对 `待核实`、缺失日期、重复/冲突日期、歧义条款、扫描/复杂版式/表格/附件限制回看原始采购文件，由用户或合规人员确认。
4. 把结果作为辅助响应清单；不要把本地运行成功描述为 WorkBuddy 平台安装、调用、审核、发布或真实投标成功。

## 已知限制与隐私边界

扫描 PDF 若没有可靠 OCR 文本、复杂版式的页眉页脚/坐标关系、表格或跨页附件可能在抽取中丢失；相关内容必须标记并人工回看。文本缺失、冲突或“另行通知/以采购人通知为准”等表述不会被猜测为确定值。引文只保留短摘录并对常见联系人、电话、邮箱、证件、账号和凭证值做上下文脱敏，但脱敏不是完整的隐私检测；执行前仍应最小化敏感输入并确认权限。

## 验证

可使用公开虚构样例验证实际命令和确定性 JSON。该命令仅证明仓库 checkout 中的本地脚本和样例可运行：

```bash
python packages/skills/wangbin-tender-analyzer/scripts/analyze_tender.py --input packages/skills/wangbin-tender-analyzer/examples/fictional-tender.txt
```

将标准输出解析成 JSON 并与仓库中原始 `examples/fictional-tender.expected.json` 做**只读对照**；预期快照由独立冻结需求和已审查历史版本提供，禁止用当次 actual 重写 expected、禁止为了通过而改写历史预期。若不一致，保留差异和来源，交由独立审查；仅经另行审批和独立证据才可更新快照。样例不代表真实采购条件、得分、权限、平台安装/调用或合规意见。
