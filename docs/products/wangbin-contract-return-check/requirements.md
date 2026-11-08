# 合同回传变更检查 / Returned Contract Change Check — 冻结 MVP 需求安全副本

product_id: `wangbin-contract-return-check`；版本 0.1.3。该副本由冻结业务规则重写，移除历史机器路径与旧 QA 资料引用；不授予输入合同公开权。开发自测、独立 QA、WorkBuddy 和平台评测分别判定，旧版本执行结果不继承。

## 产品身份与用户价值

中文简介：比较发出稿与回传稿，定位条款变化，整理付款、交付和验收等商务确认事项。
English description: Compare an original contract with a returned draft, trace clause changes, and identify commercial points requiring confirmation.
用户仅为持有两份获授权 DOCX 的采购、销售和合同运营人员。双版本方向、结构定位、五类差异和商务人工确认及四表 XLSX/可编辑 DOCX 是本产品边界；不是法律意见，也不代表与其他平台产品的全量相似性审查。

## 冻结规则

- 输入必须由用户明确指认发出稿 `original` 和回传稿 `returned`，两个不同文件均为可读 `.docx`；相同内容的独立文件允许。上下文角色冲突/未指定须 `NEEDS_INPUT: ROLE_AMBIGUOUS`，不能依据文件名、时间或上传次序猜测方向。`focus_topics`、`draft_message`、合同名和 `output_dir` 可选；跨轮追问只能复用已确认角色、文件哈希和已核实 change_id，换文件需重新比较。
- CON-01：保留正文段落与普通表格可见文本的逐字原文和位置；否定/义务词、金额、日期、天数、百分比、条件不能被规范化吞掉；缺失数值不补零。
- CON-02：已确定同文本跨位置仅一条 `MOVE`，不同时产生该单元 `ADD/DELETE/MODIFY`。CON-03：纯条号变化仅 `NUMBER`；编号与内容都变化时分别记一次编号和一次内容，不重复计同一商务事实。
- CON-04：表格依据唯一业务标识配对；重复标题/同名行/多种合理对应不得武断匹配。CON-06：歧义写入待确认，已确定部分仍输出且标 `PARTIAL`，不把歧义当零变化。
- CON-05：`ADD | DELETE | MODIFY | MOVE | NUMBER` 与付款、金额、交付、验收、服务范围、期限、其他主题分别存储；30→60 天可说延长 30 天，金额 100000→100000 不报金额变更；无证据不得断言资金损失、法律效力或对方动机。
- CON-07：主题筛选仅改变显示，必须列明筛选和未显示范围，全量与筛后计数分开。CON-08：仅在已确定双侧证据下生成礼貌问题和可选草稿；候选不得作确定变化，不自动发送或替用户接受。
- CON-F01：同条号、邻接、同槽位、首尾锚点或“只剩一对”均非同一商务义务的充分依据。确定对应需双方逐字原文、位置、唯一且相容的动作/对象或业务键，且排除竞争候选，并附对齐依据；否则在待确认表及说明保留双方候选原文和位置，`PARTIAL`，候选不计入确定差异/草稿。30→60/60→30、纯移动、仅编号等明确情形不能一律降为待确认。独立单边新增/删除须有单边证据。
- CON-F02：明确授权的原始输入/输出路径不是对重解析目标的授权。打开前检查路径自身及其全部现存父组件的 symlink、Windows junction/重解析点；本版遇任一跳转 `ERROR: UNSAFE_PATH`，不打开目标/写目标；检查后确认普通文件、不同身份及受控根，新建输出目录后复核，无法防止竞态时失败关闭。普通无链接授权路径必须可用。输入源不得写入，前后 SHA-256 一致。
- Word 未解决修订须 `NEEDS_INPUT: REVISION_STATE` 并要求提供明确接受修订后的副本；文本框/图片/扫描与复杂嵌套等未支持载体按可定位位置及影响标 `PARTIAL`，不声称“整份无变化”。损坏、不可读、恶意 OOXML、超限、输出失败各报明确 `ERROR`，不生成空白成功报告。单份建议上限 10 MiB、2000 单元、100000 字符。
- 实际生成的四张 XLSX 工作表及可编辑 DOCX 必须包含方向、来源 SHA、定位、原文、确认问题及覆盖边界；详见 `input-output-contract.md`。验收逐例预期在 `acceptance-cases.md`。输出中任意来自合同的 `= + - @` 开头字符串须作为文字，不执行公式。

## 推荐自然问法（双语）

1. 第一份是我们发出的合同，第二份是对方回传稿，帮我检查付款、交付和验收条件改了哪些地方。
2. 只看会影响交易条件的变化，编号调整和普通文字润色简单说明即可。
3. 根据已经确认的差异，帮我写一段发给对方的确认文字，语气客气，但不要替我接受修改。

1. The first file is our original contract and the second is the returned draft. Check changes to payment, delivery, and acceptance terms.
2. Focus on commercial changes and briefly summarize numbering adjustments and wording edits.
3. Draft a polite clarification message based on the verified differences without accepting the changes on my behalf.

不做 OCR、复杂嵌套解析、自动接受修订、自动发送、法律结论或云端上传。自然语言参数映射/真实 WorkBuddy 安装、评测官方模板与许可仍 `NOT_TESTED`；本地 CLI 不能冒充宿主对话。安全副本仅保留冻结预期，新生成虚构用例需重新执行，不继承旧统计。
