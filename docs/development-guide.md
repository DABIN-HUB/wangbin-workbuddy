# 开发指南

## 安装

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt
.venv/Scripts/python.exe tests/generate_fixtures.py
```

Linux/macOS：将 `.venv/Scripts/python.exe` 替换为 `.venv/bin/python`。

## 常用命令

```bash
.venv/Scripts/python.exe -m tooling validate
.venv/Scripts/python.exe -m tooling test
.venv/Scripts/python.exe -m tooling package
.venv/Scripts/python.exe -m tooling release-check
```

命令从项目根目录执行，也可以传入 `--root` 指定项目根。`validate`、`test` 和 `release-check` 将证据写入 `reports/`，`package` 将候选 ZIP 写入 `dist/`。

## 引擎调用

```python
from pathlib import Path
from wangbin_document_engine import DocumentEngine, SpreadsheetService

root = Path("tests/fixtures")
result = DocumentEngine().parse_file(root / "sample.pdf", root)
batch = DocumentEngine().parse_many([root / "sample.pdf", root / "sample.docx"], root)
export = SpreadsheetService().deduplicate(root / "sample.xlsx", root, Path("output"))
```

结果对象包含稳定状态、文本、元数据、章节、质量提示、错误码和耗时。失败结果不泄漏底层路径和异常堆栈。

## 依赖边界

- 生产解析：MarkItDown 0.1.9 及其 PDF/DOCX/XLSX/PPTX extras。
- 表格导出：openpyxl 3.1.5。
- Skill frontmatter 校验：PyYAML 6.0.3。
- 本地测试夹具：python-docx、python-pptx；测试运行器：pytest。
- 不依赖在线模型、不发送文档到外部 API、不执行宏或脚本。

## 变更要求

新增格式必须同时增加：引擎映射、真实夹具、质量限制、测试 ID、Skill 任务协议、许可证说明和发布包白名单。禁止仅改文件扩展名实现“转换”。
