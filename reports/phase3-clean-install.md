# Phase 3 Windows 干净安装与运行验收

> 以下原始记录保留为历史证据；Git 安全收尾重建的最新 wheel 的 Windows 3.12 安装、复跑与源代码回归见本文末尾“Git 收尾候选追加验证”。旧 wheel SHA-256 已失效。

环境：Windows 10 / CPython 3.12.0；最终候选独立虚拟环境 `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wangbin-phase3-audit-clean`。安装来源是**本地** `dist/wangbin_document_cli-1.2.0-py3-none-any.whl`，不是公开包索引，也不是 WorkBuddy 托管环境。安装时不依赖 `PYTHONPATH`、`WANGBIN_ENGINE_SRC` 或全局用户站点；普通生产命令不联网。

## 执行命令与结果

```text
uv venv --python 3.12 --seed <隔离目录>
<隔离目录>/Scripts/python.exe -m pip install --no-input --disable-pip-version-check --only-binary=:all: --no-cache-dir dist/wangbin_document_cli-1.2.0-py3-none-any.whl
<隔离目录>/Scripts/python.exe -m pip check
PYTHONNOUSERSITE=1 WANGBIN_ENGINE_SRC= PYTHONPATH= <隔离目录>/Scripts/wangbin-document-cli.exe version
PYTHONNOUSERSITE=1 WANGBIN_ENGINE_SRC= PYTHONPATH= <隔离目录>/Scripts/wangbin-document-cli.exe doctor
PYTHONNOUSERSITE=1 WANGBIN_ENGINE_SRC= PYTHONPATH= <隔离目录>/Scripts/wangbin-document-cli.exe status
<隔离目录>/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3-windows-acceptance.py
```

安装退出码 0；从在线索引实际下载 MarkItDown 及传递依赖，`pip check` 返回 `No broken requirements found.`。`version` 报 `1.2.0`，`doctor` 报 Python `3.12.0`、`dependencies=ready`、`issues=[]`，`status` 为 `LOCAL_READY`，均退出码 0。Windows 验收脚本最终退出码 0：真实 PDF/DOCX/XLSX/PPTX/HTML/TXT/Markdown 全部返回 `success`、真实文本非空；中文、空格和方括号 `[x]` 路径返回 `success`；XLSX 去重输出重新打开为 3 行（含表头）；越界路径返回 `PATH_OUTSIDE_ROOT` 且退出码 1。Windows 当前无建立 symlink 的权限，该单项 `NOT_TESTED`，**不能**因 Linux 拒绝而替代其 Windows 结果。

另外，`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3-timeout-probe.py` 以 `timeout_seconds=0.05` 运行真实 PDF，返回 `PARSER_TIMEOUT` 且命令退出码 0（探针断言通过）。Windows CPU、内存、并发进程聚合隔离未证明。详细清理与限制见 `phase3-security.md`。

最终候选 IPC 安全修改后重新构建并在全新隔离环境安装，版本/doctor/status、七格式与路径、超时/无孤儿进程、公式/异常清理均重新执行，退出码 0。日志：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3-windows-audit-final.log`；安装命令记录在本次会话终端结果。此处的日志为本机短期 scratch，不是可复现的远端公开安装凭据。

结论：**本地隔离 wheel 安装和 Windows 格式路径运行通过**；尚未证明 Connector `init` 在 WorkBuddy 全新客户端能下载安装。`CLEAN_INSTALL_PASS=PASS` 仅限本地 wheel 干净安装；不可由此推导 `DISTRIBUTION_SOURCE_PASS` 或 `WORKBUDDY_INSTALL_PASS`。

## Git 收尾候选追加验证（不改写以上历史测试）

新 wheel SHA-256 `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa`。Windows 10 / CPython 3.12.0：在 scratch 独立 venv 安装依赖后，对**当前** wheel 执行 `python -m pip install --force-reinstall --no-deps dist/wangbin_document_cli-1.2.0-py3-none-any.whl`、`python -m pip check`（`No broken requirements found.`）；同一已安装 wheel 的 `version=1.2.0`、`doctor=ready`、`status=LOCAL_READY` 通过。`phase3-windows-acceptance.py` 实际七格式、复杂路径、去重重新打开、越界共 10 项通过，symlink 创建权限不足仍为 `NOT_TESTED`，运行脚本退出 0。候选源码执行 `.venv/Scripts/python.exe -m pytest -q`：`31 passed, 1 skipped`，包含八个新增的容量、快照、Excel 限制/清理、目标文件防覆盖和超时回归；退出 0。首次使用未更新的流式 XLSX 输出时，旧验收对 `max_row==3` 的断言失败；补上维度声明并增加回归后重建本 wheel 再验收通过。最新验收日志：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wb-phase3-windows-release.json`；用户系统 Python 未用于 CLI 命令。工作进程并不是安全沙箱，Windows 无 CPU/内存硬限制。
