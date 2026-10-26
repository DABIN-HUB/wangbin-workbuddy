---
name: wangbin-document-cli-guide
display_name: wangbin 文档 CLI 使用说明
display_name_en: wangbin Document CLI Guide
description: Explain how an AI should call the document CLI and report errors.
description_zh: 指导 AI 调用文档 CLI 并如实报告错误。
description_en: Explain how an AI should call the document CLI and report errors.
version: 1.0.0
author: wangbin
---
# CLI 使用说明

模板中的 CLI 必须以 JSON 返回业务结果，明确记录认证前提、参数类型、超时和错误码。不得在命令参数、日志或 Skill 中写入真实凭证。
