# 架构说明

## 组件

```text
WorkBuddy Skill 候选
  └─ scripts/run_document_engine.py
       └─ wangbin_document_engine
            ├─ SecurityPolicy
            ├─ MarkItDownAdapter
            ├─ DocumentEngine
            └─ SpreadsheetService

本地工程 CLI
  ├─ validate  -> 结构、字段、资源、凭证
  ├─ test      -> pytest 真实文件处理
  ├─ package   -> Skill 白名单 ZIP
  └─ release-check -> 汇总门禁和候选包
```

## 处理流程

1. 由用户选择文件，并提供允许的输入根目录。
2. `SecurityPolicy` 解析路径、拒绝符号链接/越界路径、检查扩展名与文件签名、检查 Office ZIP 条目和展开大小。
3. `MarkItDownAdapter` 以 `enable_plugins=False` 调用 MarkItDown 0.1.9。
4. `DocumentEngine` 生成结构化结果；单文件失败不抛出到批次外层。
5. `SpreadsheetService` 使用 openpyxl 读取 XLSX，不执行公式，输出新文件并重新打开验证。
6. Skill 适配器输出 JSON，平台没有文档引擎时返回 `ENGINE_RUNTIME_MISSING`，不伪造成功。

## 为什么暂不使用 Docling

MarkItDown 0.1.9 在真实测试中覆盖 PDF、DOCX、XLSX、PPTX、HTML、TXT 和 Markdown，满足 Phase 1 的读取目标。Docling 会显著增加运行时依赖和资源开销，当前没有已验证的能力缺口，因此暂不加入；扫描件 OCR、复杂版式保真和高级表格重建列入后续评估。

## 平台适配结论

WorkBuddy Skill 文档确认脚本可由 Bash 调用，但没有在 Skill 页面承诺 Python 依赖托管；Connector 文档明确 Python runtime 自 5.0.0 可声明。因此本地引擎与 Skill 内容可以先验收，平台稳定运行需要后续将引擎包装为官方 CLI Connector 或使用平台内置能力，并在有账号的真实环境中验证。
