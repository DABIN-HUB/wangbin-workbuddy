# 依赖闭包 — final wheel 绑定后的正式候选

**DEPENDENCY_CLOSURE = BLOCKED_DEPENDENCY_DISTRIBUTION_NOT_CLOSED。**

Observed metadata consistent != dependency lock/closure。以下为真实本地 METADATA 的有界观察图，不是公开源真实性证明、解析器生成的发布锁或已安装环境。

## 最终 wheel 与原 analyst 图

唯一 0.3.2 wheel 的实际 METADATA Name/Version、Requires-Python、8项 Requires-Dist（包含规范化名称、范围、extras、marker）与 pyproject 和 analyst 捕获边界逐项语义相等。`RUN/final-wheel-binding.json` 独立绑定 SHA `3c49370cf360cc131a2b11300a0f0b19d7ea1595b33b5d43d264f8ee6c044199`；wheel 身份见 RESULT/BUILD_PROVENANCE。

`RUN/analyst/dependency-closure.json` 保持原字节，不追改：原图43项 pending/missing 包含未交付的新 solar。绑定后仅去掉这个根节点的 pending：每矩阵剩42个第三方节点缺独立 wheel，2个项目节点存在本地构件字节（新solar与document），但不等于两项可信公众分发已闭合。历史solar0.3.1不能满足0.3.2。

| Target | Observed nodes | Active edges | Missing metadata | Constraint/Python conflicts | Analyst原pending/missing | Final缺第三方wheel |
|---|---:|---:|---:|---:|---:|---:|
| Windows-AMD64-CPython3.12 | 44 | 65 | 0 | 0 / 0 | 43 | 42 |
| Windows-AMD64-CPython3.13 | 44 | 64 | 0 | 0 / 0 | 43 | 42 |
| Windows-AMD64-CPython3.14 | 44 | 64 | 0 | 0 / 0 | 43 | 42 |
| Linux-x86_64-CPython3.12 | 44 | 63 | 0 | 0 / 0 | 43 | 42 |
| Linux-x86_64-CPython3.13 | 44 | 62 | 0 | 0 / 0 | 43 | 42 |
| Linux-x86_64-CPython3.14 | 44 | 62 | 0 | 0 / 0 | 43 | 42 |
| macOS-x86_64-CPython3.12 | 44 | 63 | 0 | 0 / 0 | 43 | 42 |
| macOS-x86_64-CPython3.13 | 44 | 62 | 0 | 0 / 0 | 43 | 42 |
| macOS-x86_64-CPython3.14 | 44 | 62 | 0 | 0 / 0 | 43 | 42 |
| macOS-arm64-CPython3.12 | 44 | 63 | 0 | 0 / 0 | 43 | 42 |
| macOS-arm64-CPython3.13 | 44 | 62 | 0 | 0 / 0 | 43 | 42 |
| macOS-arm64-CPython3.14 | 44 | 62 | 0 | 0 / 0 | 43 | 42 |

## 原始观察版本表（不是锁）

以下表格继承 analyst 观察选择；solar 行的 pending 是**原图时点**。最终root构件已由上一节独立绑定，不能将本节历史 MISSING 当作当前构建失败。

| Project | Observed version | Requires-Python | Evidence | Wheel bytes |
|---|---|---|---|---|
| attrs | 26.1.0 | >=3.9 | installed_metadata | MISSING in audited repository wheel inventory |
| beautifulsoup4 | 4.15.0 | >=3.7.0 | installed_metadata | MISSING in audited repository wheel inventory |
| certifi | 2026.10.23 | >=3.7 | installed_metadata | MISSING in audited repository wheel inventory |
| cffi | 2.1.1 | >=3.10 | installed_metadata | MISSING in audited repository wheel inventory |
| charset-normalizer | 3.5.2 | >=3.7 | installed_metadata | MISSING in audited repository wheel inventory |
| click | 8.5.1 | >=3.10 | installed_metadata | MISSING in audited repository wheel inventory |
| cobble | 0.1.4 | >=3.5 | installed_metadata | MISSING in audited repository wheel inventory |
| cryptography | 50.0.2 | >=3.9, !=3.9.0, !=3.9.1 | installed_metadata | MISSING in audited repository wheel inventory |
| defusedxml | 0.7.1 | >=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.* | installed_metadata | MISSING in audited repository wheel inventory |
| et-xmlfile | 2.0.0 | >=3.8 | installed_metadata | MISSING in audited repository wheel inventory |
| flatbuffers | 25.12.19 | unspecified | installed_metadata | MISSING in audited repository wheel inventory |
| idna | 3.20 | >=3.9 | installed_metadata | MISSING in audited repository wheel inventory |
| jsonschema | 4.26.0 | >=3.10 | installed_metadata | MISSING in audited repository wheel inventory |
| jsonschema-specifications | 2025.9.1 | >=3.9 | installed_metadata | MISSING in audited repository wheel inventory |
| lxml | 6.1.3 | >=3.8 | installed_metadata | MISSING in audited repository wheel inventory |
| magika | 1.0.3 | >=3.8 | installed_metadata | MISSING in audited repository wheel inventory |
| mammoth | 1.13.0 | >=3.7 | installed_metadata | MISSING in audited repository wheel inventory |
| markdownify | 1.2.3 | unspecified | installed_metadata | MISSING in audited repository wheel inventory |
| markitdown | 0.1.9 | <3.15,>=3.10 | installed_metadata | MISSING in audited repository wheel inventory |
| numpy | 2.5.4 | >=3.12 | installed_metadata | MISSING in audited repository wheel inventory |
| onnxruntime | 1.31.1 | >=3.11 | installed_metadata | MISSING in audited repository wheel inventory |
| openpyxl | 3.1.5 | >=3.8 | installed_metadata | MISSING in audited repository wheel inventory |
| packaging | 26.3 | >=3.9 | installed_metadata | MISSING in audited repository wheel inventory |
| pandas | 3.1.1 | >=3.11 | installed_metadata | MISSING in audited repository wheel inventory |
| pdfminer-six | 20260107 | >=3.10 | installed_metadata | MISSING in audited repository wheel inventory |
| pdfplumber | 0.11.10 | >=3.8 | installed_metadata | MISSING in audited repository wheel inventory |
| pillow | 12.3.0 | >=3.10 | unpacked_uv_cache | MISSING in audited repository wheel inventory |
| protobuf | 7.36.2 | >=3.10 | installed_metadata | MISSING in audited repository wheel inventory |
| pycparser | 3.12 | >=3.11 | installed_metadata | MISSING in audited repository wheel inventory |
| pypdfium2 | 5.15.1 | >= 3.6 | installed_metadata | MISSING in audited repository wheel inventory |
| python-dateutil | 4.0.0 | >=3.11 | installed_metadata | MISSING in audited repository wheel inventory |
| python-docx | 1.2.0 | >=3.9 | installed_metadata | MISSING in audited repository wheel inventory |
| python-pptx | 1.0.2 | >=3.8 | installed_metadata | MISSING in audited repository wheel inventory |
| referencing | 0.37.0 | >=3.10 | installed_metadata | MISSING in audited repository wheel inventory |
| requests | 2.34.2 | >=3.10 | installed_metadata | MISSING in audited repository wheel inventory |
| rpds-py | 2026.9.1 | >=3.11 | installed_metadata | MISSING in audited repository wheel inventory |
| six | 1.17.0 | >=2.7, !=3.0.*, !=3.1.*, !=3.2.* | installed_metadata | MISSING in audited repository wheel inventory |
| soupsieve | 4.0.1 | >=3.11.5 | installed_metadata | MISSING in audited repository wheel inventory |
| typing-extensions | 4.16.0 | >=3.9 | installed_metadata | MISSING in audited repository wheel inventory |
| tzdata | 2026.5 | >=2 | unpacked_uv_cache | MISSING in audited repository wheel inventory |
| urllib3 | 2.8.0 | >=3.10 | installed_metadata | MISSING in audited repository wheel inventory |
| wangbin-document-cli | 1.2.0 | <3.15,>=3.12 | wheel | present; public source UNKNOWN |
| wangbin-solar-pv-input | 0.3.2 | >=3.12,<3.15 | source_project_candidate_wheel_metadata_pending | MISSING in audited repository wheel inventory |
| xlsxwriter | 3.3.1 | >=3.8 | installed_metadata | MISSING in audited repository wheel inventory |


## 依赖链、来源和许可边界

- 直接边界：jsonschema==4.26.0；wangbin-document-cli==1.2.0；openpyxl==3.1.5；python-docx==1.2.0；Pillow>=10,<13；pdfminer.six==20260107；defusedxml==0.7.1；tzdata==2026.5 仅 solar direct win32 marker。
- document真实METADATA激活 `markitdown[docx,pdf,pptx,xlsx]==0.1.9`，再激活 lxml/mammoth、pdfminer-six/pdfplumber、python-pptx、openpyxl/pandas，及 magika→onnxruntime base链。未请求all/Azure/audio/YouTube保持inactive；完整active/inactive边及extras上下文见原JSON，不凭记忆补依赖。
- Linux/macOS仍有实际观察链 markitdown[xlsx]→pandas3.1.1→python-dateutil4.0.0→tzdata。pandas自己的direct tzdata是win32/emscripten；不将solar direct marker误当完整传递条件，也不把这些本地版本认作所有上游发布的普遍事实。
- 42项第三方独立wheel不在本次有界本地分发库存中；installed METADATA、解包uvcache、WHEEL tag诊断不能替代wheel字节、来源和不可变分发渠道。未知发布源、版本全集、依赖组合/ABI和再分发许可仍阻断；本轮禁止下载补齐。
- document1.2.0两份同名轮子SHA分别 `8f2ef2ab31c0f058612884ddf36a797b2dded4fc8ffdd5781453901e98a86bbd`（历史candidate）和 `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa`（dist）。前者无LICENSE成员，后者LICENSE原字节匹配当前document源码通知 `506377ce49d410995b6e7d11b9cd5fd6ea5d3b560a193f779b32e337367937a6`。两者13/13模块匹配不说明整个wheel等同；所有历史document METADATA描述与当前README不同。当前LICENSE只读核验，不修改document/旧wheel、不据元数据MIT认定完整第三方许可。
- solar build requires setuptools>=68 / setuptools.build_meta；document另声明wheel。当前build实际使用现有setuptools84.1.0，详见BUILD_PROVENANCE；构建依赖与runtime图分开。独立wheel/build分发未安装不妨碍本次已有setuptools内置bdist_wheel真实执行，但不关闭未来离线backend分发。

## 完整证据与隐私

RUN为 `.runtime/solar-pv/SOLAR-PV-R2-ENGINE-ARTIFACT-01`。analyst原件 `ANALYST_REPORT.md`、`dependency-closure.json`、`DEPENDENCY_CLOSURE.md`、`metadata-catalog.json`、`inventory-provenance-summary.json`、`connector-skill-runtime-boundary.json`、`build-dependencies-metadata.json` 均以精确SHA保留在review-payload，不修改原图；额外原证包括wheel-inventory/document-readme-license-provenance/official-doc-fetch/citation与现成tool probes。

writer从选中44节点原source、build元数据及历史/新wheel提取50条最小必要元数据证据，逐件核对原SHA和依赖头。`RUN/dependency-metadata-index.json` / `RUN/dependency-metadata/` 保存7条原字节和43条EMAIL_REDACTED派生件：派生件与原件双SHA/size、来源、redaction数分别记录，不把脱敏文本称为原始METADATA；带email的原件只读留原source，不共享或更改。未复制虚拟环境、整个cache、客户文件、canonical、请求原件或测试全文。

声明兼容性见 PYTHON_RUNTIME_COMPATIBILITY，实际Skill/Connector边界见 CONNECTOR_SKILL_RUNTIME_BOUNDARY；安装/Skill runtime均NOT_TESTED，host E2E BLOCKED，许可和发布BLOCKED。独立QA仍PENDING。
