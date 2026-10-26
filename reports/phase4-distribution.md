# Phase 4 — wheel 分发实况与回滚

核对日期 2026-10-26；只读探测 `https://pypi.org/pypi/wangbin-document-cli/json` 和 `/1.2.0/json` 均 HTTP 404；`https://api.github.com/repos/DABIN-HUB/wangbin-workbuddy/releases` HTTP 200、JSON 空数组 `[]`。这些只证明**探测时这两个具体位置没有可用 1.2.0 资产**；404 不证明包名归属或今后可注册，空 Release 列表不排除别的私有存储。没有代用户公开上传。WorkBuddy 文档的 `cli.json` 安装实例与 Python 托管位置见 [Connector 规范](https://open.workbuddy.cn/docs/connector)。

| 方式 | 本地 wheel 安装 | 本轮公开地址下载 | WorkBuddy 安装器接受/目标客户端网络 | 普通用户无额外配置 |
|---|---|---|---|---|
| PyPI 固定包名版本 `wangbin-document-cli==1.2.0` | **PASS（仅本地 wheel）**；历史 Windows/Linux 新环境实际安装与 `pip check` 见 `reports/git-review.md`。 | **BLOCKED**，两个 PyPI JSON 接口 404。 | **UNKNOWN**，官方示例支持 pip 包名安装，不代表本包实际可装。 | **BLOCKED**。 |
| GitHub Release | 同一 wheel 的本地能力不等于 URL 能下载。 | **BLOCKED**，仓库 Releases API 空数组，未创建资产。 | **UNKNOWN**，访问域名/HTTPS asset/重定向与依赖索引需目标客户端实测。 | **BLOCKED**。 |
| 受信任 HTTPS wheel | 本地可安装。 | **BLOCKED**，没有已验证的公开、不可变、无需认证的 URL。 | **UNKNOWN**；不能将 `file:///F:/...` 用作正式地址或把私有签名/需要认证的链接写进公开 `cli.json`。 | **BLOCKED**。 |
| 官方其他方式 | Connector 包提交审核是资产元数据流程，不是平台承诺代为托管 Python wheel。 | **UNKNOWN**。 | **UNKNOWN**，需平台授权核实私有包源/允许域名/依赖服务策略。 | **UNKNOWN/BLOCKED**，未完成实际安装。 |

**版本锁定**：当前 `cli.json` 的 `init` 固定 `wangbin-document-cli==1.2.0`、`--no-input --only-binary=:all:`，管理 Python 3.12、最低客户端 5.0.0；产品 wheel 声明 `>=3.12,<3.15`、直接依赖 `markitdown[pdf,docx,xlsx,pptx]==0.1.9` 与 `openpyxl==3.1.5`。直接依赖固定不意味着所有传递依赖固定或 supply chain 可重现；平台 pip 是否无交互、来源是否允许须验。

**哈希与依赖核验**：本地 `sha256sum -c` 在正确 `dist/` 目录对三个 1.2.0 sidecar 全部返回 `OK`（本阶段只读复核），值如下。sidecar 不会被当前 `pip install <包名>` 自动强制校验；公开发布后必须下载真实 wheel 核对实际哈希与版本，并在目标运行时执行 `python -m pip check`、`wangbin-document-cli version/doctor/status`，核对 `pip` 解析的索引、所有传递依赖及许可/NOTICE。若源重建导致字节变化，以新 SHA-256 和新受审清单为准；不能假定相同版本自动相同哈希。

| 本地历史候选（非公开资产） | SHA-256 |
|---|---|
| `wangbin_document_cli-1.2.0-py3-none-any.whl` | `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa` |
| `wangbin-document-assistant-1.2.0-skill-candidate.zip` | `38133ee51a91db38091032c60ecb4b84db9e3c63e9953307575b13b7a649de2f` |
| `wangbin-document-cli-1.2.0-connector-candidate.zip` | `be64b3b619382cbc74686fef6bd64a402f15f380487bde61e41620df66feb0e7` |

**选择与回滚**：长期首选有本人控制包名的 PyPI 固定版本，但**当前不授权发布**。得到真实分发许可后，先复核安全、第三方许可、macOS 和受保护的私有平台入口，才由本人选择发布并重做公开来源+平台安装验收。不要覆盖已分发 wheel/ZIP 或重用 1.2.0 同名版本发布不同字节；问题版本应停止新用户连接/宣传、告知现有用户风险，在平台提供的正规禁用/下架途径操作，并将 Connector 指向**已实际验收过的**旧兼容版本（如有）或发审核过的新版本；不能假设 1.1.0 可安全回滚或当前平台支持一键回滚。保留候选哈希、不可变记录及历史 Phase 2 证据。若没有已验可用的回退版本，状态保持停用而非假恢复。

四层门禁分别为 `LOCAL_WHEEL_INSTALL=PASS (历史双平台)`、`PUBLIC_DOWNLOAD=BLOCKED`、`WORKBUDDY_SOURCE_ACCEPTED=UNKNOWN`、`ZERO_EXTRA_CONFIGURATION=BLOCKED`；`DISTRIBUTION_SOURCE_PASS=BLOCKED`。