# 第三方依赖与许可证声明

## 直接依赖

| 包 | 版本 | 用途 | 许可证/来源 |
|---|---:|---|---|
| MarkItDown | 0.1.9 | 七类文档内容提取 | MIT；来源：https://github.com/microsoft/markitdown；仓库 LICENSE 已在 2026-10-26 读取 |
| openpyxl | 3.1.5 | XLSX 检查和安全导出 | MIT；https://openpyxl.readthedocs.io |
| PyYAML | 6.0.3 | Skill frontmatter 校验 | MIT；https://pyyaml.org/ |
| pytest | 8.4.2 | 用户明确要求的本地自动化测试 | MIT；https://pytest.org/ |
| python-docx | 1.2.0 | 真实 DOCX 测试夹具 | MIT；https://github.com/python-openxml/python-docx |
| python-pptx | 1.0.2 | 真实 PPTX 测试夹具及 MarkItDown 依赖 | MIT；https://python-pptx.readthedocs.io/ |

## MarkItDown 依赖说明

MarkItDown 的 PDF/DOCX/XLSX/PPTX extras 解析到 `pdfminer-six`、`pdfplumber`、`pypdfium2`、`mammoth`、`openpyxl`、`python-pptx` 等依赖；MarkItDown 0.1.9 的实际环境安装还包含 `magika`/`onnxruntime` 等传递依赖。完整版本清单见 `reports/pip-freeze.txt`，应在每次更新后重新生成并复核许可证。

## 合规边界

- 许可证信息来自安装包元数据、上游项目文档或 LICENSE 文件；元数据为空时不把空值猜成许可证。
- 发布候选包不包含 Python 依赖本体；平台侧运行时托管或安装方式仍需要单独审核。
- `OPEN_SOURCE_LICENSE_PASS` 只有在实际依赖清单与上游许可证逐项复核后才能通过；本地候选报告会保守记录状态。
- 本文件不授予任何第三方品牌、数据、模型或接口的额外使用权。

## Phase 2 独立 CLI wheel（2026-10-26）

本地隔离 Windows Python 3.12 安装共解析出 38 个安装包（其中含 pip 和本项目），每项元数据声明的许可证/分类见 `reports/phase2-dependencies.json`；实际固定解析版本见 `reports/phase2-windows-py312-resolved.txt`。CLI wheel 内只装本项目的引擎/CLI 源码和项目 LICENSE，**不把上述第三方 wheel 塞入 WorkBuddy Connector ZIP**。安装时由用户许可的 Python 索引下载依赖。

除直接依赖的 MIT 外，实际依赖中还出现 `certifi` 的 MPL-2.0、`cryptography` 的 Apache-2.0/BSD-3-Clause 双许可、`numpy` 的复合许可证、`pypdfium2` 的 PDFium/依赖许可及其他 BSD、Apache、PSF/PSFL 条款。元数据有声明不等于法律合规审查完成；**正式对外分发前仍须逐项读取对应 wheel 的 LICENSE/NOTICE 及传递依赖再分发义务**，尤其是 PDFium、NumPy 多重条款。此项保持 `BLOCKED`，不能仅用 Phase 1 的 `OPEN_SOURCE_LICENSE_PASS` 代替 Phase 2 发布法律审查。
