---
name: wangbin-document-assistant
display_name: wangbin AI 万能文档助手
display_name_en: wangbin AI Document Assistant
description: 当用户要读取、整理 PDF/Word/Excel/PPT/HTML/TXT/Markdown 或 Excel 去重时，使用已安装的本地 wangbin CLI。
description_zh: 本地读取七类办公文档，批处理并安全导出 Excel/CSV。
description_en: Process office documents locally, in batches, and safely export spreadsheets.
version: 1.2.0
author: wangbin
allowed-tools: Bash
examples_zh:
  - "帮我整理这个 PDF 的内容"
  - "把这个 Excel 去重，并导出新文件"
examples_en:
  - "Organize this PDF"
  - "Deduplicate this Excel file and export a new file"
---
# wangbin AI 万能文档助手（本地 CLI）

使用前仅处理用户明确选择/授权的本地文件；不要搜索无关目录。须先安装并连接 `wangbin-document-cli` 连接器；独立安装本 Skill 不会自动安装 Python 或解析器。仅通过 Bash 调用已安装的 CLI，绝不在执行文档时联网安装依赖。若 CLI 缺失或 `status` 不是 `LOCAL_READY`，停止处理并提示用户先在 WorkBuddy 安装/连接 CLI Connector。

## 执行

为所有文件传入**单独引用的路径参数**；绝不拼接用户文件名到未加引号的命令中。令 `<输入根目录>` 为已授权文件的所在目录，`<独立输出目录>` 必须与输入目录分开；Excel 输出不覆盖源文件。Unix 命令为 `wangbin-document-cli`，Windows WorkBuddy CLI 环境中的可执行文件为 `wangbin-document-cli.exe`；不要写死 Python 或虚拟环境的绝对路径。

```bash
wangbin-document-cli status
wangbin-document-cli parse --input "<用户授权文件>" --input-root "<输入根目录>" --output-root "<独立输出目录>"
wangbin-document-cli batch --files "<文件一>" "<文件二>" --input-root "<输入根目录>" --output-root "<独立输出目录>"
wangbin-document-cli deduplicate --input "<用户授权的.xlsx>" --input-root "<输入根目录>" --output-root "<独立输出目录>" --format xlsx
```

Windows 应使用同名 `.exe` 命令和双引号包裹中文/空格路径；不要把未验证的占位符作为真实路径执行。命令输出为 JSON（`status` 只输出 `LOCAL_READY`）；读取其中的 status/error.code，不能仅凭进程启动判定成功。`partial_failure` 应逐项报告；`failed` 应向用户说明错误码；`success_with_warning` 必须保留质量提示。基于提取文本生成的摘要需将原文事实与推断区分；扫描 PDF、复杂布局和高级表格无法保证提取。

## 用户请求映射

- “帮我提取这个 PDF 的全部文本”：先执行 `status`，再对用户明确授权的 PDF 执行 `parse`；返回真实提取文本、质量提示和 `source_name`，不把解析结果称为模型摘要。
- “帮我把 Excel 里面的重复记录删除，然后生成新的 Excel”：执行 `deduplicate --format xlsx`，返回 `output_path`、`rows_read`、`rows_written` 和 `duplicates_removed`；确认源文件未被覆盖，并把生成文件作为新结果交付。
- “帮我分析这些文件，并分别生成内容摘要”：先对每个授权文件执行 `batch` 或逐个 `parse`，再把返回的原文和元数据交给 WorkBuddy 模型生成摘要；明确分开“CLI 原文提取”“原文事实”“模型推断”，没有模型调用时不得声称已生成 AI 摘要。

不把用户文档提交给未经授权的远程服务，不执行嵌入脚本/宏/公式，不改动原文件。若平台尚未实际安装并验收此连接器，不宣称在 WorkBuddy 中运行成功。任务约束参见 @references/runtime.md。
