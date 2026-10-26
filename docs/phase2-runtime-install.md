# Phase 2 安装、升级与卸载（候选 1.1.0）

## 当前交付状态

1. `dist/wangbin_document_cli-1.1.0-py3-none-any.whl`：本地构建的纯 Python 引擎 + CLI wheel；含项目 MIT LICENSE，不包含 MarkItDown 或其依赖源码。
2. `dist/wangbin-document-cli-1.1.0-connector-candidate.zip`：WorkBuddy CLI Connector 元数据、Python runtime 声明与配套 Skill。
3. `dist/wangbin-document-assistant-1.1.0-skill-candidate.zip`：只包含 CLI 使用说明；**单独安装无法处理文档**。Connector 内已嵌相同 Skill，原则上先尝试只安装 Connector，避免重复加载同名 Skill；是否仍需单独 Skill 需平台实测。
4. `dist/wangbin-document-cli-1.1.0-candidate-manifest.json`：文件大小、逐成员和三个构建产物的 SHA-256；两个 ZIP 和 wheel 均附有 `.sha256` 校验文件。

上述均是本地候选。`cli.json` 的 `init` 使用官方建议的 `python -m pip install --only-binary=:all: wangbin-document-cli==1.1.0`，且 WorkBuddy 托管 `runtime.type=python`, version=3.12，最低客户端为 5.0.0。2026-10-26 查询 https://pypi.org/pypi/wangbin-document-cli/json 返回 HTTP 404；本轮没有授权将 wheel 上传到公开或私有索引。因此 **WorkBuddy 新用户目前不能依赖该 init 命令安装，WORKBUDDY_INSTALL_PASS 与 PUBLISH_READY 均为 BLOCKED**。不应直接把 ZIP 上传为可用产品。公开发布 wheel 前须经用户审阅、核对名称所有权和第三方依赖许可；发布/索引凭据不可粘贴到聊天。

## Windows 本地干净安装（已执行）

在**独立 scratch** 新建 Python 3.12 venv（不是本仓库 `.venv`），执行：

```text
uv venv --python 3.12 --seed C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wangbin-phase2-clean
C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wangbin-phase2-clean/Scripts/python.exe -m pip install --no-input --only-binary=:all: --no-cache-dir F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin_document_cli-1.1.0-py3-none-any.whl
C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wangbin-phase2-clean/Scripts/python.exe -m pip check
C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wangbin-phase2-clean/Scripts/wangbin-document-cli.exe version
C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wangbin-phase2-clean/Scripts/wangbin-document-cli.exe doctor
C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wangbin-phase2-clean/Scripts/wangbin-document-cli.exe status
```

安装需要访问 PyPI 或已批准的包索引来下载固定直接依赖 MarkItDown 0.1.9、openpyxl 3.1.5 和其传递依赖；实际 Windows 解析版本见 `reports/phase2-windows-py312-resolved.txt`。运行 `parse`、`batch`、`deduplicate`、`status` 时**不安装任何包**。传递依赖在此版本中不是跨平台 hash lock；变更索引或平台后需重新审查。`--only-binary=:all:` 阻止源发行包执行本地构建脚本，但仍须信任所用索引及第三方 wheel。

## 本地调用

所有路径必须显式指向用户授权文件；输入根目录是该文件所在目录，输出目录位于输入目录以外；命令参数需逐个传入，含空格/中文的路径须引用。示例：

```text
wangbin-document-cli.exe parse --input "C:\\authorized files\\中文 文件.pdf" --input-root "C:\\authorized files" --output-root "C:\\results"
wangbin-document-cli.exe batch --files "C:\\authorized files\\one.pdf" "C:\\authorized files\\two.docx" --input-root "C:\\authorized files" --output-root "C:\\results"
wangbin-document-cli.exe deduplicate --input "C:\\authorized files\\table.xlsx" --input-root "C:\\authorized files" --output-root "C:\\results" --format xlsx
```

macOS/Linux 的入口是 `wangbin-document-cli`，Python venv 的脚本目录为 `bin/`；两平台尚未实机验证，不能报告 PASS。持续集成建议建立隔离 macOS/Linux Python 3.12 job：安装同一 wheel，从独立工作目录调用七种真实文档并复验输出和错误码，记录 OS/架构、版本和 SHA-256，部署前再于 WorkBuddy 客户端实际安装。

## 无外部账号和 WorkBuddy 认证边界

本 CLI 不读取远程账号或 Token。官方 https://open.workbuddy.cn/docs/connector 将 `auth` 设为按需，`unAuth` 仅在有认证时必填。因此此候选 `cli.json` **只声明 init、status 和 statusMatch**；不会伪造授权 URL 或持久化虚假登录态。CLI 本身提供 `auth`（报告无需远程账号）与 `logout`（不会删除文件），供诊断和人工使用；`status` 无业务状态写入，成功输出 `LOCAL_READY`。如果平台强制要求认证配置或无法将安装完成的本地工具判定为已连接，平台门禁保持 BLOCKED，需取得 WorkBuddy 真实错误再修订协议。

## 升级/回滚/卸载

- 构建者：修改生产代码后增加 wheel 和双包版本，重新完成干净安装、ZIP 校验、哈希和许可证复核；旧 Phase 1 证据/ZIP 保留，不覆盖。
- 最终用户若从**可信索引**安装：使用受 WorkBuddy 管理的 Python 环境安装经审核的新固定版本；Connector 更新需重新提交平台审核，勿假设已有连接自动切换版本。
- 本地卸载仅作用于当前 venv：`python -m pip uninstall wangbin-document-cli`；不会删除用户输入、输出或 WorkBuddy 配置。完整清理用户文件须由本人另行决定。
- 回滚仅在旧 wheel/依赖仍可获取且平台允许对应版本时由用户选择旧固定版本重新安装；不要对当前工程执行 git reset 或强制覆盖。

## 官方依据

- https://open.workbuddy.cn/docs/skill ：Skill 结构与 Bash 调用；未规定通用 Skill 的 Python 依赖托管和精确 ZIP 外层解析。
- https://open.workbuddy.cn/docs/connector ：CLI + Skill 结构、托管 Python runtime、init/status/auth 表、平台认证超时、跨 OS 要求及 Connector 提交审核。
- https://open.workbuddy.cn/docs/developer-agreement ：第三方依赖、数据、权限、真实能力与审核约束。
