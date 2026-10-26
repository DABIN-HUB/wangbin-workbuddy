# Phase 3 分发方案分析（候选 1.2.0）

核对日期：2026-10-26（中国标准时间）  
项目：`wangbin AI 万能文档助手`  
当前仓库远端：`https://github.com/DABIN-HUB/wangbin-workbuddy.git`  
状态：**未发布、未上传、未注册包名**。

## 官方安装约束

根据最新读取的官方 Connector 页面：

- CLI Connector 必须提供 `connector-meta.json`、`cli.json`、`icon.svg`；`skills/{skill-name}/SKILL.md` 强烈推荐。
- `runtime.type=python` 时，WorkBuddy 自 5.0.0 起准备托管 Python，并把 pip 与缓存隔离在 WorkBuddy 管理目录；官方建议使用 `python -m pip install <package>`，不能使用 `pip install --user`，也不能依赖用户系统 Python。
- `init.{darwin,linux,win32}` 是必填的平台安装命令；`versionCheck` 是可选字段，当前不猜测其未核实格式。
- 官方文字说明 CLI 应有明确 `auth`、`status`、`unAuth`，但字段表将 `auth` 标为按需，将 `unAuth` 和认证状态 `status` 标为“有认证时必填”。本产品没有远程账号，因此不在 Connector 配置中伪造 OAuth、Token 或登录态；本地 CLI 仍保留只读诊断语义。
- 官方未承诺普通 Skill 自动托管 Python 依赖，因此普通 Skill 仍不能作为引擎交付载体。

来源：

- https://open.workbuddy.cn/docs/connector
- https://open.workbuddy.cn/docs/skill
- https://open.workbuddy.cn/docs/developer-agreement

## 方案比较

| 方案 | `cli.json` 兼容性 | 依赖获取 | 稳定性/版本 | SHA-256 | 风险与维护 | 结论 |
|---|---|---|---|---|---|---|
| A. 正式 PyPI | 与官方 `python -m pip install <package>` 建议最一致；当前命令已固定版本、非交互、仅二进制 | wheel 从 PyPI，MarkItDown 及传递依赖从可信索引 | 包名版本、元数据和 PyPI 文件哈希成熟；更新需发新版本 | PyPI 元数据有文件哈希；本地仍保留 `.sha256` | 公开发布不可撤销；必须先确认包名所有权、许可证和依赖再分发义务 | **长期推荐** |
| B. GitHub Release wheel | pip 支持 HTTPS wheel URL，但 `init` 要写入精确公开 URL；未核实 WorkBuddy 网络策略前不能宣称 | 自有 wheel 从 GitHub，依赖仍需索引可达 | Release asset 可固定 tag/文件名；GitHub 限流、域名访问和仓库权限是额外变量 | 可附 `.sha256`，但普通 pip 命令不会自动校验 sidecar | 维护 release asset；删除/重传会影响可复现性；需公开仓库 | 可作人工候选发布方案，不是当前已验证来源 |
| C. 可信 HTTPS 文件地址 | pip 支持直接 HTTPS wheel URL；固定 URL 可写入 `init`，但需实际网络验证 | 自有 wheel 从文件地址，依赖仍需索引 | 需自建不可变对象存储/版本目录；缓存和 CDN 行为需维护 | sidecar 可供人工校验；不能仅靠 sidecar 让 pip 自动校验 | URL 劫持、误覆盖、证书/CDN、长期可用性和访问控制 | 不优于 A，除非已有可信不可变存储 |
| D. 私有/其他索引 | 可配 pip index，但 WorkBuddy 的私有认证、证书和环境变量行为未被官方确认 | 依赖可统一托管 | 版本管理可控 | 可启用 hash lock，但安装配置复杂 | 账号、凭证、网络白名单和平台托管环境风险最高 | 当前禁止写入公开 Connector |

## 推荐与当前决策

**推荐长期方案：A，正式 PyPI 包。** 原因是 Connector 官方直接示例是 `python -m pip install <package>`，WorkBuddy 已声明会托管 Python 和隔离 pip；PyPI 能同时提供版本索引、元数据和依赖解析，避免把私有认证写入 Connector。Phase 3 只准备发布工作流，不执行注册、上传或发布。

当前 `cli.json` 已改为非交互安装：

```text
python -m pip install --no-input --disable-pip-version-check --only-binary=:all: wangbin-document-cli==1.2.0
```

这条命令只有在 `wangbin-document-cli==1.2.0` 被用户本人发布到 WorkBuddy 可访问的可信索引后才可用。实际请求 `https://pypi.org/pypi/wangbin-document-cli/1.2.0/json` 与包级 `/json` 均返回 HTTP 404；404 不证明此包名未来可注册或归本项目所有。因此不能把 `DISTRIBUTION_SOURCE_PASS` 或 `WORKBUDDY_INSTALL_PASS` 标为 PASS，也不能上传 Connector 作为可用产品。Windows/Linux 干净安装里依赖是从 PyPI 下载的，但正式客户端网络和 5 分钟 `init` 时限尚无平台证据。

### 元数据和许可预检（非法律许可结论）

wheel `pyproject.toml` 声明 `requires-python >=3.12,<3.15`（与 Connector 托管 Python 3.12 对齐；避免在未复核 junction API 的 3.11 上误装）、MIT、直接依赖 `markitdown[pdf,docx,xlsx,pptx]==0.1.9` 与 `openpyxl==3.1.5`；`python -m pip check` 在 Windows 3.12 和 Linux 3.12 均通过。Windows 安装环境中 `importlib.metadata` 的初步信息：MarkItDown=MIT、openpyxl=MIT、pypdfium2=`BSD-3-Clause, Apache-2.0, dependency licenses`、pandas=BSD-3-Clause、onnxruntime=MIT、magika=Apache-2.0、lxml=BSD-3-Clause、mammoth=BSD-2-Clause、python-pptx=MIT、cryptography=`Apache-2.0 OR BSD-3-Clause`、Pillow=MIT-CMU；pdfplumber 顶层 License 字段为空。已有 Phase 1 的 `reports/licenses.md` 只覆盖少数依赖；`certifi`（MPL-2.0）、`numpy` 复合许可及 PDFium 等均需具体核对。**必须逐项检查正式 wheel/sdist 的许可证全文、NOTICE、捆绑二进制许可与再分发义务**，这份字段盘点不是发布许可。

## 人工发布前检查清单（不由本轮自动执行）

1. 用户本人确认 PyPI 包名所有权或选择组织拥有的包名。
2. 审阅 wheel 的 `METADATA`、`WHEEL`、LICENSE、依赖版本和第三方许可证/NOTICE。
3. 发布前先在干净环境从**本地最终 wheel**安装并执行 `pip check`、七格式 CLI 验收；从包名 `pip install ... wangbin-document-cli==1.2.0` 的真实来源验收应在发布后执行（见第 5 步），不可把 404 当成功。
4. 推荐使用准备好的 `.github/workflows/phase3-pypi-publish.yml`：本人先在 GitHub 配置 `pypi` Environment 审批/分支保护，并在 PyPI 为该仓库/该工作流/该环境配置 OIDC Trusted Publisher；本人审核最终构建源码与许可证后，在 `main` 上手动 `workflow_dispatch` 并键入精确确认字符串 `PUBLISH 1.2.0`，审批通过后才可能发布。发布前应将工作流引用的第三方 Actions 固定到审核过的 commit SHA。若不具备受保护环境，**不要执行工作流**；避免使用长期 PyPI token，也不在聊天中接收任何凭据。本轮没有触发工作流。
5. 发布后从**全新隔离环境**通过包名安装，记录实际下载 URL、版本、退出码、`pip check` 和 wheel SHA-256。
6. 仅在以上证据完成后重新构建/上传 Connector 候选并进行 WorkBuddy 私有测试；若平台只允许正式审核，停止等待本人决定。

GitHub Release 只作为备选：若用户明确选择 B，应先在本人仓库创建不可变 `v1.2.0` Release，上传 wheel 与 `.sha256`，再用 HTTPS asset URL 做 pip dry-run 和 WorkBuddy `init` 实测；本轮没有创建 Release 或上传文件。
