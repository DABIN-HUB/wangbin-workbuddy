---
name: wangbin-contract-return-check
display_name: 合同回传变更检查
display_name_en: Returned Contract Change Check
description: 比较发出稿与回传稿，定位条款变化，整理付款、交付和验收等商务确认事项。
description_zh: 比较发出稿与回传稿，定位条款变化，整理付款、交付和验收等商务确认事项。
description_en: Compare an original contract with a returned draft, trace clause changes, and identify commercial points requiring confirmation.
user_facing_standard: v1
examples_zh:
  - 第一份是我们发出的合同，第二份是对方回传稿，帮我检查付款、交付和验收条件改了哪些地方。
  - 只看会影响交易条件的变化，编号调整和普通文字润色简单说明即可。
  - 根据已经确认的差异，帮我写一段发给对方的确认文字，语气客气，但不要替我接受修改。
examples_en:
  - The first file is our original contract and the second is the returned draft. Check changes to payment, delivery, and acceptance terms.
  - Focus on commercial changes and briefly summarize numbering adjustments and wording edits.
  - Draft a polite clarification message based on the verified differences without accepting the changes on my behalf.
version: 0.1.4
author: wangbin
---
# 合同回传变更检查 / Returned Contract Change Check

## Preparation / 准备

仅处理用户授权的两份独立 DOCX：`original` 为发出稿，`returned` 为回传稿。若用户未明确两个角色、上下文与参数冲突，先追问并停止；不要从文件名、上传顺序或时间戳猜测。不同文件即便字节相同仍合法。跨轮筛选/草稿仅复用用户明确的同一对源文件、角色、哈希和已核实变化；无该上下文则重新询问，换文件须重新运行。不可将自然语言声明与显式参数冲突当作同意。中英文问法遵守同一限制。

## Usage / 使用

依赖 Python 3.11+、`python-docx>=1.2,<2`、`openpyxl>=3.1,<4`、`defusedxml>=0.7,<1`，须在运行环境显式安装/确认；WorkBuddy 平台依赖和附件参数映射尚未验证。用户提供已授权输出目录 `output_dir`；建议由宿主另行明确其独立于 `output_dir` 的共同 `authorized_root`，以 `--authorized-root "<明确授权共同根>"` 限定三条路径（未传根时仅依赖调用方明确授予三个原始路径，不能把 `output_dir` 当成其链接目标的授权证明）。目录可新建，逐层检查原路径的链接、Windows junction / 重解析点并在创建后复验，发现跳转拒绝 `ERROR: UNSAFE_PATH`；真实 symlink 权限不足环境仍须标未测。执行：

```bash
python scripts/compare_contracts.py --authorized-root "<另行明确授权的共同根>" --original "<用户明确发出稿.docx>" --returned "<用户明确回传稿.docx>" --output-dir "<用户授权输出目录>" --focus-topics 付款 交付 --draft-message --contract-name "合同"
```

`focus_topics` 省略即全量，限付款/金额/交付/验收/服务范围/期限/其他；`draft_message` 默认 false。通过 JSON 状态、源 SHA-256 与实际 XLSX/DOCX 路径回复用户，不以范文代替本地执行。返回码 2 为 `NEEDS_INPUT` 或 `ERROR`；不得声称已比较。无网络发送或源文件写入。

## Processing / 处理

正文和普通表格均带可复核位置；变化类型 `ADD/DELETE/MODIFY/MOVE/NUMBER` 与商务主题分开。仅唯一的双方业务动作及相容正文、双方有明确不同条号且剥号后非空正文完全相同、表格唯一业务键等确定证据生成差异 ID；纯编号变化的 NUMBER 保留双方完整原文、位置和明确编号差值，不另报 MODIFY。正文同条号、同槽位、前后锚点或余一对均不能单独证明相同义务；未证实候选保留双方原文和位置并标 `PARTIAL`，不计入草稿/确定变化。重复对应及不支持载体标 `PARTIAL` 和待确认，不将其写作零变化。未解决修订暂停，要求接受修订后的副本。此对齐是保守启发式，不是语义证明；跨语种或彻底改写需人工核对。

## Outputs / 输出

实际输出是四表 XLSX 与可编辑 DOCX，记录源角色、SHA-256、定位和原文；主题筛选仅改变显示，不改变全量变化计数。无网络发送或源文件写入。

## Limits / 限制

不支持图片 OCR、文本框/嵌套表格比较。超出输入上限/损坏报错。草稿不自动发出、不替用户接受或断言法律效力、损失、对方动机。人工核验关键差异及覆盖范围后再沟通。脚本只供本地候选，模型/平台/许可均 NOT_TESTED。
