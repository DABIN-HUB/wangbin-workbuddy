# Phase 3 Linux Docker 运行验收

> 以下旧记录保留历史原貌；最新 Git 收尾候选的实测追加于本文末，不能以原 wheel 结果替代新 wheel 验收。

环境：Docker `python:3.12-slim`（容器内 `Python 3.12.15`），宿主 Windows 10；项目以只读卷挂载到 `/workspace`。此为**真实 Linux 用户态/依赖 wheel 安装和 CLI 执行**，不等同 macOS 或 WorkBuddy 平台执行。

## 1 GiB 失败与修正

第一次 1.2.0 全量链在默认 `RLIMIT_AS=1 GiB` 时退出码 1；最小化 PDF 探针提高至 2 GiB 和 4 GiB 后各退出码 0。基于这个观察，候选默认改为 `2 GiB`，重新构建并重新安装 1.2.0 wheel。不能把调大限制等同于完整恶意输入安全保证；详情见 `phase3-security.md`。

## 最终实际命令

```text
docker run --rm --pull=missing -v F:/ideaWorkSpace/wangbin-workbuddy:/workspace:ro -v C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3-linux-acceptance.py:/probe/acceptance.py:ro -w /workspace python:3.12-slim bash -lc '
  set -e
  python --version
  python -m pip install -q --no-input --disable-pip-version-check --only-binary=:all: dist/wangbin_document_cli-1.2.0-py3-none-any.whl
  python -m pip check
  cd /probe
  PYTHONPATH= WANGBIN_ENGINE_SRC= PYTHONNOUSERSITE=1 python acceptance.py
'
```

IPC 安全复核前同一候选版本的 Linux 链已运行 `version`、`doctor`、`status`、PDF/DOCX 解析、XLSX 去重与重新打开，退出码 0；该记录属于旧 wheel，不替代新 wheel 验收。最终安全修正后重新构建并重新从 wheel 安装、`pip check` 与下列全部 16 项执行，退出码 0；日志：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wangbin-phase3-linux/audit-final-complete.log`。

## 结果

最终全格式验收输出 `status=PASS`、容器退出码 0、`pip check=No broken requirements found.`，共 **16 项断言**：

- 最终 wheel 的 `version=1.2.0`、`doctor` (`runtime=3.12.15`, `dependencies=ready`)、`status=LOCAL_READY`，均返回退出码 0。
- 七种真实文件的 `parse`（PDF、DOCX、XLSX、PPTX、HTML、TXT、Markdown）返回 `success`/退出码 0，提取文本非空。
- Excel 去重 `success`/退出码 0、输出重新打开为 3 行（含表头）。
- 受损 PDF 返回 `CORRUPT_DOCUMENT`/退出码 1；越界路径 `PATH_OUTSIDE_ROOT`/退出码 1；真实 symlink `SYMLINK_INPUT`/退出码 1。
- 构造的高压缩比 Office ZIP 返回 `ZIP_COMPRESSION_RATIO`/退出码 1；`timeout_seconds=0.05` 的真实 PDF 在独立解析进程中返回 `PARSER_TIMEOUT`，并在调用返回后检查活动子进程集合与调用前一致。

容器退出后 `--rm` 删除自身；本轮没有常驻 Linux 服务。故 `LINUX_RUNTIME_PASS=PASS`（仅对此候选、以上运行项）；POSIX CPU/内存极端输入、进程树清理与并发总量安全仍 `BLOCKED`。macOS 尚未执行；已提供 `.github/workflows/phase3-cross-platform.yml` 供后续在真实 macOS runner 运行，不能标记 `MACOS_RUNTIME_PASS=PASS`。

## Git 收尾候选追加验证（不改写旧记录）

最新 wheel SHA-256 `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa`。宿主 Windows 10，Docker `python:3.12-slim` / Linux Python 3.12.15：只读挂载项目，执行 `python -m pip install --only-binary=:all: dist/wangbin_document_cli-1.2.0-py3-none-any.whl pytest==8.4.2 python-docx==1.2.0 PyYAML==6.0.3`，`python -m pip check` 为 `No broken requirements found.`；随后从**安装的 wheel**、清空 `PYTHONPATH` 运行 `phase3-linux-acceptance.py`，16 项全部通过、退出码 0；最新结果 `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wb-phase3-linux-release.json`。源码完整回归早先因少装 PyYAML 在收集时失败，再因只读挂载的 `test_tooling` 需写 `reports/validate.json` 而有 30 项通过、1 项失败；两次失败均没有删除或改写测试。最终候选在容器内将源码复制到可写的 `/tmp/phase3-source`，安装相同依赖、`pip check` 后执行 `python -m pytest -q -p no:cacheprovider`，真实结果 **32 passed**、退出码 0；复制与写入只在 `--rm` 临时容器内，宿主历史报告未被测试覆盖。这里的流式 Excel 仅协作式检查行/单元格/字节/迭代时间，未对 `load_workbook`/写出提供 OS 级硬限制；不代表安全门禁通过。
