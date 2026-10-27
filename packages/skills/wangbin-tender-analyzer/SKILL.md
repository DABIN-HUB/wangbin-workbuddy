---
name: wangbin-tender-analyzer
display_name: wangbin 招标分析助手
display_name_en: wangbin Tender Analyzer
description: 本地分析单个 TXT/MD 招标文本，输出带脱敏摘录证据的待核实清单。
description_zh: 仅在本地分析单个 UTF-8 TXT/MD 文本，提取资格、评分、技术、日期和响应清单，并绑定限长脱敏摘录。
description_en: Analyze one local UTF-8 TXT/MD tender file with bounded redacted excerpts and pending verification items.
examples_zh:
  - "在仓库本地分析这份已获授权的招标 TXT，列出资格和关键日期"
  - "从仓库本地 Markdown 招标文本提取技术要求和评分条款"
  - "检查本地招标文本中缺失、冲突或有歧义的响应项"
examples_en:
  - "Locally analyze one authorized tender TXT in the repository checkout"
  - "Extract technical requirements and scoring clauses from a local Markdown tender"
  - "Flag missing, conflicting, or ambiguous response items in local tender text"
version: 0.1.0
author: wangbin
allowed-tools: Read, Bash
---
# wangbin 招标分析助手

本 Skill 是可运行的、文本优先的招标分析 MVP。脚本只在本地进程中分析一个已由用户选择的 UTF-8 `.txt` 或 `.md` 文件；它不会验证用户是否拥有该文件的处理权限，不执行 PDF/OCR/宏/脚本，也不上传远程服务。结果只用于辅助核对，不替代采购文件原件、法律意见、人工评审或 WorkBuddy 平台审核。

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

将标准输出与 `examples/fictional-tender.expected.json` 比较；预期 JSON 必须由上述命令的实际输出更新，不得手写虚构结果。样例不代表真实采购条件、得分、权限、平台安装/调用或合规意见。
