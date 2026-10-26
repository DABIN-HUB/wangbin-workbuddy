# Phase 2 验收报告（本地候选，未平台发布）

- 版本：1.1.0；路线：Python CLI Connector + 配套 Skill；独立 Skill 不含引擎。
- 干净环境真实用例：PASS 28 / FAIL 0 / SKIP 1；Windows 3.12 本地 wheel + 从 PyPI 下载依赖。
- Python CLI 入口、`doctor`/`status`、七种格式解析、批处理、Excel 去重 XLSX/CSV 重读、路径与损坏文件失败、Windows junction 均在隔离 venv 实际执行；符号链接创建权限不足，保持 SKIP。
- 原 Phase 1 ZIP 校验：原始 SHA-256 保持不变

## 门禁

| 门禁 | 状态 |
|---|---|
| `DOCUMENT_ENGINE_PASS` | **PASS** |
| `CLEAN_INSTALL_PASS` | **PASS** |
| `CLI_RUNTIME_PASS` | **PASS** |
| `SKILL_INTEGRATION_PASS` | **BLOCKED** |
| `SECURITY_PASS` | **BLOCKED** |
| `PACKAGE_VALIDATION_PASS` | **PASS** |
| `WORKBUDDY_INSTALL_PASS` | **BLOCKED** |
| `WORKBUDDY_E2E_PASS` | **BLOCKED** |
| `PUBLISH_READY` | **BLOCKED** |

门禁计数：PASS 4 / FAIL 0 / BLOCKED 5 / NOT_TESTED 0。

## 关键阻断

- 候选 `init` 命令使用固定版本的包索引安装，但 2026-10-26 查询公开 PyPI 为 HTTP 404；没有授权发布 wheel，不能将 Connector ZIP 称为普通 WorkBuddy 用户可运行产品。
- 尚未登录 WorkBuddy、未验证 ZIP 根解析/托管 Python、未安装、未通过对话执行文档任务或接受平台审核。个人主体认证仍需用户本人进行。
- 本地 `SKILL.md`/CLI 命令静态匹配和干净 CLI 实测均成功，但平台 Skill→CLI 调用未执行，`SKILL_INTEGRATION_PASS` 仍为 BLOCKED。
- 安全检查覆盖路径、容器、大小和 junction；符号链接直接试验 SKIP，解析器缺乏硬隔离超时与资源限额，不把局部验证外推成完整安全 PASS。
- macOS/Linux 实机：NOT_TESTED；依赖许可证逐项法律审查：BLOCKED；通用转换 T15：SKIP。

## 证据与人工步骤

- 干净环境逐命令、退出码、结果哈希：`reports/phase2-clean-install.json`、`.md`。
- 构建物及哈希：`dist/wangbin-document-cli-1.1.0-candidate-manifest.json`、两个 ZIP 与 wheel 各自的 `.sha256`。
- 实际依赖：`reports/phase2-windows-py312-resolved.txt`、`reports/phase2-dependencies.json`，另见 `docs/third-party-notices.md`。
- 详细安装/卸载：`docs/phase2-runtime-install.md`；人工平台试传/安装/对话验收：`docs/phase2-platform-acceptance.md`。
- 本轮未运行 git commit、push、reset 或切换分支，也未自动上传/正式发布。
