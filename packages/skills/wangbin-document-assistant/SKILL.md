---
name: wangbin-document-assistant
display_name: wangbin AI 万能文档助手
display_name_en: wangbin AI Document Assistant
description: 读取、整理和导出办公文档，支持 PDF、Word、Excel、PPT、HTML、TXT 和 Markdown；遇到不支持或失败的内容如实说明。
description_zh: 面向普通办公人员和中小企业，读取、整理和导出常见办公文档。
description_en: Reads, organizes, and exports common office documents for everyday work.
examples_zh:
  - "帮我整理这个 PDF 的内容"
  - "把这个 Excel 去重，并导出新文件"
  - "提取这份 Word 的关键事项"
  - "将这些文档分别生成摘要"
  - "提取 PDF 里面的表格"
  - "把这几份材料整理成一份报告"
examples_en:
  - "Organize the contents of this PDF"
  - "Deduplicate this Excel file and export a new file"
  - "Extract the key action items from this Word document"
  - "Create separate summaries for these documents"
  - "Extract tables from this PDF"
  - "Organize these materials into one report"
version: 1.0.0
author: wangbin
allowed-tools: Read, Bash, Write
---
# wangbin AI 万能文档助手

当用户要求读取、整理、摘要输入文件、去重表格或导出新文件时，按下面流程执行。

## 执行前提

- 只处理用户明确选择或授权的文件，不扫描用户无关目录。
- 输入文件只读；所有结果写入独立输出目录，不覆盖原文件。
- 本地运行脚本需要可用的 `wangbin` 文档引擎环境；若运行时不可用，应明确提示“当前 WorkBuddy 运行环境未提供文档引擎”，不得声称已处理成功。
- 文档可能包含敏感信息。默认不向未授权外部服务发送文件。

## 任务路由

1. 单个文件读取：调用 `parse`，返回格式、基本元信息、提取文本、标题/章节、质量提示和失败信息。
2. 多文件批处理：调用 `batch`，逐个返回状态；单个文件失败时继续处理其余文件，并汇总 `success`、`failed` 和 `partial_failure`。
3. Excel 去重和导出：调用 `deduplicate`，先确认输入文件和输出格式；输出新文件，报告去重数量和重开验证结果。
4. 整理或摘要：先读取真实文本，再基于原文生成结构化输入。把原文事实、用户要求和模型推断分开标注；原文没有的信息不得补写成事实。
5. 文件转换：只在引擎明确支持且输出文件已重新读取验证时报告成功；不能只修改扩展名。

## 推荐调用

```bash
python scripts/run_document_engine.py parse --input "<用户授权文件>" --input-root "<输入根目录>" --output-root "<独立输出目录>"
python scripts/run_document_engine.py batch --input-root "<输入根目录>" --files "a.pdf" "b.docx" --output-root "<独立输出目录>"
python scripts/run_document_engine.py deduplicate --input "<xlsx 文件>" --input-root "<输入根目录>" --output-root "<独立输出目录>" --format xlsx
```

脚本优先输出 JSON；出现错误时使用稳定错误码，不输出完整凭证或无关本地路径。

## 输出格式

- 首先给出任务状态：`success`、`success_with_warning`、`partial_failure` 或 `failed`。
- 单文件输出：文件格式、大小、标题/章节、提取文本、质量提示、错误码和耗时。
- 批处理输出：每个文件的状态和错误，再给出总数。
- Excel 导出输出：新文件路径、读取行数、写入行数、去重数量；明确说明源文件未被覆盖。
- 摘要类输出使用“原文事实”“待办事项”“风险提示”“模型推断（如有）”分栏。

## 不支持和失败处理

扫描 PDF、需要复杂视觉还原的布局、受密码保护或损坏的文件可能无法可靠提取。遇到空文本、版式丢失、错误扩展名、超大文件、路径越界或运行时缺失时，报告具体限制和下一步建议，不伪造结果。

更多任务协议见 `@references/task-protocol.md`，隐私约束见 `@references/privacy.md`。
