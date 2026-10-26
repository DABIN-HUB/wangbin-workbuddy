# wangbin WorkBuddy 工程

这是 `wangbin` 的 WorkBuddy 资产工程，当前 Phase 1 交付首个产品：**wangbin AI 万能文档助手**。

## 目录

- `services/document-engine/`：独立、可本地运行的文档解析和表格处理引擎。
- `packages/skills/`：WorkBuddy Skill 候选包。
- `packages/experts/`：WorkBuddy Expert 模板。
- `packages/connectors/`：WorkBuddy MCP/CLI Connector 模板。
- `tooling/`：统一校验、测试、打包和发布检查 CLI。
- `tests/`：真实文档夹具和自动化验收代码。
- `docs/`：平台规范、架构、安全、开发、发布和路线图。
- `reports/`：脱敏的验证证据。
- `dist/`：发布候选 ZIP 和哈希。

## 环境

工程工具包推荐 Python 3.12（根 `pyproject.toml` 仍为 1.0.0、最低 3.11）；**实际对外候选**是 `services/document-engine/pyproject.toml` 的独立 `wangbin-document-cli==1.2.0`，要求 Python 3.12 到 3.14，不能把工程工具包版本当作发布候选版本。本工程使用 `uv` 创建隔离环境：

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt
```

Linux/macOS 将解释器路径替换为 `.venv/bin/python`。

## 统一命令

从项目根目录运行：

```bash
python -m tooling validate
python -m tooling test
python -m tooling package
python -m tooling release-check
```

所有命令都会将报告写入 `reports/`；候选包写入 `dist/`。命令不会提交 Git、上传 WorkBuddy 或修改原始输入文档。

## 本地能力边界

本地引擎真实读取 PDF、DOCX、XLSX、PPTX、HTML、TXT 和 Markdown，并支持批处理、Excel 去重与安全导出。摘要功能只生成可供后续模型使用的结构化原文输入，不在本地伪造模型结论。

本地通过不等于 WorkBuddy 平台兼容。平台账号认证、ZIP 根层级试传、Skill 运行时、平台安装和实际对话调用在无授权环境下保持 `BLOCKED` 或 `NOT_TESTED`，详见 `docs/workbuddy-platform-spec.md` 和最终验收报告。

## Phase 2 本地 CLI 候选（1.1.0）

Phase 1 的 Skill ZIP 只含适配脚本，不包含引擎，不能直接交给普通用户作为可运行成品。Phase 2 从 `services/document-engine/` 构建真正含引擎与 CLI 的 Python wheel，并生成独立 Skill/CLI Connector 双候选包。Windows Python 3.12 干净 venv 已实际安装 wheel、下载依赖并验证七类文件；不依赖 `WANGBIN_ENGINE_SRC`。

```bash
uv build --wheel services/document-engine --out-dir dist
python -m tooling.phase2_packager
python -m tooling.phase2_acceptance --clean-env <独立安装的 scratch venv> --missing-env <仅安装 wheel 的 scratch venv> --scratch <Hermes scratch 目录>
```

注意：`wangbin-document-cli==1.1.0` 尚未发布至 WorkBuddy 用户可访问的可信 Python 包索引，WorkBuddy 真实安装/调用仍是 `BLOCKED`，**不得直接宣称新 ZIP 可安装使用**。操作与手工验收见 `docs/phase2-runtime-install.md`、`docs/phase2-platform-acceptance.md` 和 `reports/phase2-acceptance.md`。上述 Phase 1 `python -m tooling package` 命令只生成旧的 1.0.0 包；不能代替 Phase 2 的打包器。

## Phase 3 候选（1.2.0）

Phase 3 将解析执行放入可终止的独立子进程：父进程执行真实 wall-clock 超时和子进程清理，Linux 子进程额外设置 CPU/虚拟内存限制；Windows 已验证超时终止，但 Windows CPU/内存 Job Object 限制尚未实现，安全门禁保持 `BLOCKED`。Git 收尾候选新增文件私有快照和再次校验、跨 CLI 进程的两槽容量锁、Excel 流式读写及行/单元格/输出字节限额、目标文件原子无覆盖发布；这些是局部限制，不是解析沙箱或 Excel CPU/内存硬限，详见 `reports/git-review.md`。

Phase 3 生成 `1.2.0` wheel、Skill ZIP 和 CLI Connector ZIP，保留 Phase 2 的 1.1.0 产物及报告。Connector 安装命令固定版本、非交互且只接受二进制 wheel，但 `wangbin-document-cli==1.2.0` 尚未发布到可信索引；因此 `DISTRIBUTION_SOURCE_PASS`、`WORKBUDDY_INSTALL_PASS`、`WORKBUDDY_E2E_PASS` 和 `PUBLISH_READY` 仍不得标记 PASS。Windows 3.12 和 Linux Docker 已实际验证；macOS 仅准备 CI 工作流，状态为 `NOT_TESTED`。详见 `reports/phase3-final-summary.md`、`reports/phase3-distribution-analysis.md` 和 `reports/phase3-workbuddy-acceptance.md`。

从首次提交中的**源码**重建当前候选（不依赖已忽略的 `dist/` 或历史 1.1.0 包）：

```bash
uv build --wheel services/document-engine --out-dir dist --python <Python-3.12> -q
<Python-3.12> -m tooling.phase3_packager
cd dist && sha256sum -c wangbin_document_cli-1.2.0-py3-none-any.whl.sha256 wangbin-document-assistant-1.2.0-skill-candidate.zip.sha256 wangbin-document-cli-1.2.0-connector-candidate.zip.sha256
```

`phase3_packager` 在干净源码树无旧包时照常构建并将 `phase2_artifacts_available=false` 记录在清单；若本地保有旧包，则三个历史 SHA-256 必须全部匹配，不能覆盖或混用。`dist/`、`.venv/` 均被忽略；新候选的实际哈希和提交清单见 `reports/git-review.md`、`reports/git-commit-plan.md`。
