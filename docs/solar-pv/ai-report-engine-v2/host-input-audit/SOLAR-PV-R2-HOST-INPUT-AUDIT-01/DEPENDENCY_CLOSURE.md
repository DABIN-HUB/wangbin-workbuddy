# 普通安装链与依赖闭包

状态：`AUDITED_NOT_INSTALLED`；本轮不安装、不升级、不构建 wheel，不使用开发 PYTHONPATH 冒充宿主。证据：runtime `wheel-inspection.json`、`interpreter-metadata.json`、`exact-original-verification.json` 及对应命令回执。

## 1. 实物而非版本字符串

| 实物 | 原字节 SHA-256 | 本轮实际静态结论 |
|---|---|---|
| `.runtime/solar-pv/ai-v2-host-20261112-144349/candidate-wheels/wangbin_solar_pv_input-0.3.1-py3-none-any.whl`（548537 B） | `9c0abf6597c6b444c646eaafc3a802fa2e78cddcfe720633c6b65b2463f8a64b` | CRC 通过；120 成员。含 host_session/chapter_writer/llm_provider，**无 host_output.py、host_session 无 prepare-r2 字面入口**；不能作 R2 分发物。没有执行其代码。 |
| `dist/wangbin_document_cli-1.2.0-py3-none-any.whl`（20970 B） | `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa` | CRC 通过，19 成员；METADATA 版本 1.2.0、Python >=3.12,<3.15。仅本地实物，不证明受信索引存在或平台安装。 |
| 上述 candidate-wheels 内同名 document 1.2.0（20077 B） | `8f2ef2ab31c0f058612884ddf36a797b2dded4fc8ffdd5781453901e98a86bbd` | CRC 通过，18 成员。与 dist 同版本**不是同字节实物**；不得混用其哈希或安装回执。 |
| `dist/wangbin_document_cli-1.1.0-py3-none-any.whl`（15287 B） | `51071474a8668d5c4ba153896a5cde4d4233881f6042d7b16f305259fda702f9` | 历史版本；不满足当前 document==1.2.0 约束。仅保护，不安装。 |
| R2 Skill ZIP | `7054c670e66ad3caeab73a1ad8e9b35fd3c85f340b345aa9976e501b3250bbc9` | 21 成员与安装目录精确相同，但**没有引擎 wheel**。Skill 导入 PASS 不推出 R2 引擎/依赖 PASS。 |

仓库 `services/solar-pv-engine/pyproject.toml` 仍名 `wangbin-solar-pv-input==0.3.1`，源码包含 R2，旧同版本 wheel 不包含。此次找到旧 wheel 原件并按 ZIP/METADATA/成员核验，比只复述交接版本名多一层实证。已查范围为仓库 dist、服务 dist 及 `.runtime/solar-pv` 的相关 wheel；**不宣称穷尽全磁盘或索引**。

## 2. 当前源码直接依赖（只读清单）

来自 `services/solar-pv-engine/pyproject.toml:5–20`：

- Python `>=3.12,<3.15`；构建系统 setuptools `>=68`（本轮不构建）。
- `jsonschema==4.26.0`
- `wangbin-document-cli==1.2.0`
- `openpyxl==3.1.5`
- `python-docx==1.2.0`
- `Pillow>=10,<13`
- `pdfminer.six==20260107`
- `defusedxml==0.7.1`
- Windows：`tzdata==2026.5`

Document 1.2.0 wheel METADATA 另外声明 `markitdown[docx,pdf,pptx,xlsx]==0.1.9` 与 `openpyxl==3.1.5`。Connector `cli.json` 也安装 markitdown extras；其命令未显式列 Pillow，但光伏 wheel 声明是传递依赖，不能因此认定会自动成功解析。完整传递 wheel 集、每项 SHA、来源/许可证、平台兼容与离线可得性**尚未闭合**。

## 3. R2 必要模块与入口

真实源码及静态符号清单在 `exact-original-verification.json#/source_symbols`：

- `wangbin_solar_pv.reporting.host_session`：`PROTOCOL_VERSION='native-host-session/2.0'`；`execute()`/`main()` 的 `prepare-r2/publish/accept/resume/checkpoint/cancel`。
- `chapter_writer.prepare(..., host_delivery=None)`、`_request`、`accept`、`resume`。
- `host_output.PROTOCOL='host-draft-publication/2.0-r2'`、`publish_response`、`verify_publication`、`publication_state`。
- `llm_provider.ModelConfig.to_dict()`、`evidence_pack_builder.build_pack()`、严格 `claim_validator.validate_chapter()`、`semantic_risks.validate_risk_assertions()`。
- `chapter_registry.Registry` 及包内 `reporting/specs/report-spec.json`、`spec-lock.json`；基线文档与 definition/catalog 依赖也不能只靠复制一个 host_output.py 补齐。
- Skill `scripts/run_ai_chapter.py:30` 使用当前 `sys.executable -I -m ...host_session`，清除 PYTHONPATH/PYTHONHOME，cwd 转到包内基线；没有被安装的正确引擎必须停止。
- 既有 console entry point 是 `wangbin-solar-pv-input = wangbin_solar_pv.cli:main`；R2 实际用 `-m ...reporting.host_session`，不能只验证旧 console 命令存在。
- `connector_runtime.main()` 当前 readiness 仅核版本、可 import host_session 及其协议字符串，**不逐项验证 host_output/prepare-r2/publish**。旧同版本源码可能满足部分 readiness 条件而不提供 R2；未来可信分发验收必须逐个验证必要入口，而非凭 LOCAL_READY 文本推断。

## 4. 三类解释器分开

| 环境 | 本轮无模型读取证据 | 判定 |
|---|---|---|
| 作者标准库解释器 | 每个录制器回执与最终 OFFLINE_VALIDATION 记录实际 executable/version | 仅证明本轮离线脚本运行；不是 Skill/Connector。 |
| 仓库 `.venv/Scripts/python.exe -I` | 实际 Python 3.12.0；metadata 找不到两个 wangbin 分发包。Pillow 13.0.0 与 `<13` 不符；tzdata 2026.6 与 ==2026.5 不符，其余被列直接库版本见原回执。没有 import 产品或尝试运行引擎。 | 不能宣称普通安装可用；更不能转移为本次宿主缺包结论。 |
| `services/solar-pv-engine/.venv/Scripts/python.exe -I` | 实际 Python 3.12.0；本轮所列产品与直接依赖 metadata 均未找到。 | 只是该开发环境，不是客户端解释器。 |
| WorkBuddy Skill Bash | 旧 R2 运行没有 Bash 调用；本轮不发环境检查提示。manager 所见“内置 Python”控件未操作。 | **UNKNOWN**。 |
| Connector 托管 Python | `cli.json` 声明 Python 3.12，init 固定依赖；没有此次真实 runtime executable、pip install、模块读回或平台调用。 | **UNKNOWN / UNVERIFIED_BLOCKED**。 |

没有读取 Token/Cookie/models.json、索引凭据、私有会话库或环境秘密；metadata 中仅记录 direct_url 是否存在，不读取其中路径或敏感内容。历史开发离线安装失败仍保留在旧记录，不用本轮只读 metadata 改写它。

官方规则已通过本轮实际GET核验：Skill references供上下文、scripts经Bash；Connector CLI runtime的Python最低标注v5.0.0并描述托管venv/pip隔离，但不能据此证明普通Skill Bash共用解释器或本机已安装。精确URL/时间/原文SHA与版本界限见HOST文档和RUN/official/support-index.json。本次独立QA总裁定PARTIAL，安装门禁不因此提升。

## 5. 后续可信安装的独立批准项（不执行）

1. 权利人提供唯一可追溯的 R2 wheel：新唯一版本/构建身份、原 SHA、源码提交、必要模块/入口/包数据及许可证。不能覆盖旧 0.3.1 实物来制造同名升级。
2. 明确可信公开/私有索引或离线轮包来源，并给全依赖包版本、SHA、许可和目标 Python/平台。当前 `distribution_status=REQUIRES_TRUSTED_INTERNAL_WHEEL_INDEX`，不能猜索引或使用开发者认证。
3. 用户独立批准安装环境、确切 wheel/依赖及风险；仅在授权隔离解释器安装。随后无模型读回 executable、metadata、模块与入口和文件 SHA，先证明这一个环境。
4. 另证 Skill Bash 真实调用该受信解释器；Connector 仍须独立安装/状态/生命周期验证，不能靠文档声称共享。
5. Skill 替换和一次新 CH08 试验分别另行授权；不把安装批准当作上传/发布、模型传输或下一阶段批准。

专业语义门禁保持预测/实绩、假设/已支持、账面残值/处置回款、项目/股东、应付/实付分别审阅。结构 PASS 永不升级为语义 PASS。
