# SOLAR-PV-R2-ENGINE-ARTIFACT-01 — 本地构建阶段计划

## 已确认输入与冻结边界

唯一 developer 负责生产版本与正式文档；analyst/quality 只写独立 runtime 证据。已全文读取根规则、用户附件、旧 RESULT/PROTOCOL/DELIVERY、R1/R2 QA 原文、40/41、EXC004/005 及批准核心八文件。开工实读 main / `94ce5f04b72937a205c194d55005bddd4ce6bd90`，tracked/staged/status 空；八文件原字节重算集合 `3b41751eb36a632e38c0aab123e25eb66a271e84d2de1ee42d0b06a5f92993c4`。前轮最终归档身份由 RUN/previous-final-archive-identity.json 原值保存。

RUN = `.runtime/solar-pv/SOLAR-PV-R2-ENGINE-ARTIFACT-01`。现有 manager 版本发现实际 exit0：75 受控记录、4 独立 wheel、58 ZIP 中央目录，无 0.3.2 冲突，仅 `LOCAL_RECORDS_NOT_OCCUPIED`，不证明公共名称/版本所有权。发现可信冲突即停止，不另选号。

## 步骤及允许差异

1. 已完成只读解释器/backend 发现，原回执 `commands/developer-discovery.*`。`python` 实际解析到现有 Hermes venv Python 3.14.9，setuptools 84.1.0、packaging 26.3；无独立 wheel/build 包。Hermes `python3`、仓库两个 venv 与全局 Python 3.12 缺 backend，不能只据 `python3` 判定所有工具缺失。
2. 仅将 `services/solar-pv-engine/pyproject.toml` 分发版本 0.3.1 改为 0.3.2。保留依赖、Requires-Python 和所有 package-data 配置。`__init__.__version__=0.3.0` 被 intake 导出为 input_module_version，非分发版本真源；不为美观修改此既有输出合同。旧 egg-info 是历史输入，不复制、不修改。
3. 新建 RUN/build-source，只复制 pyproject 与受 Git 控制的引擎 src 原文件，排除环境/build/dist/egg-info/cache。每件保存原 SHA、size、Git blob 身份；不执行历史脚本。现有 setuptools.build_meta 直接 build_wheel，不运行 pip/uv、build isolation 或安装。输出独立 RUN/candidate-wheels，不覆盖任何旧 wheel/dist。
4. 显式离线环境：PIP_NO_INDEX=1、PIP_CONFIG_FILE=nul、PIP_NO_BUILD_ISOLATION=1、PIP_DISABLE_PIP_VERSION_CHECK=1、UV_OFFLINE=1、PYTHONDONTWRITEBYTECODE=1、PYTHONNOUSERSITE=1；SOURCE_DATE_EPOCH 使用实际基线 committer timestamp 1794564157。backend 进程 audit hook 拒绝 socket 连接、外部子进程及 setuptools 依赖获取；不宣称 OS 沙箱。3.14.9 位于目标 >=3.12,<3.15，但纯 wheel 构建仍不是任何目标 OS/runtime 安装证据。
5. 逐成员唯一/安全路径/size/CRC/SHA/RECORD hash 与 size、集合及 RECORD 自空规则；全 src 模块与正式 specs、声明 data 原字节映射；缺失或额外 data 显式分类，不能将未声明 demo fixture 当已包含。验证 METADATA Name/Version/Requires-Python/Requires-Dist 与 source、entry_points 对齐，入口用 AST 定位，不安装、不注入 PYTHONPATH。
6. 保存 BUILD_PROVENANCE.json、WHEEL_CONTENT_MANIFEST.json、VALIDATION.md、RESULT.md 与完整 runtime developer-report；冻结全部源码与 core/wheel 身份。独立 QA、依赖闭包仍 PENDING，不代写 QUALITY_REPORT，不封最终 review ZIP。
7. 执行现成只读卫生和 secret scan，重核保护范围与版本 allowlist。精确 staging、diff/check/cachedcheck 后本地非发布提交；读回 HEAD/status/ignore。无 push/sync/reset。

## 预算与停止门

所有实际验证用 RUN/record_command.py，role=developer、独名、每批 <=120s；本阶段累计 <=260s（实际 discovery 1.86333499988541s 已计）。构建上限90s，静态审计60s，保护/卫生/提交分别有界；不以用满为目标。工具/版本/data 失败只阻断对应 gate，保留原 stdout/stderr。没有新测试代码、Mock、fixture、pytest、财务/Office/宿主动作。

冻结报告版本 `SOLAR-PV-AI-REPORT-ENGINE-2.0.0` 与事实/计算/公式/运行协议不变。继承 R2 Skill 导入 PASS；屋顶 BLOCKED_NO_DRAFT，地面 NOT_TESTED_BLOCKED_BY_STOP_GATE；两案 Schema/strict NOT_TESTED_NO_DRAFT。安装 NOT_TESTED、宿主 E2E BLOCKED、专业 NOT_TESTED、Phase D USER_REVIEW_REQUIRED，全部 C/D/财务/PDF/正式四文件/发布门禁不关闭。

## analyst完成后的writer续阶段

原构建步骤/原freeze保持历史身份；source/wheel不重建。新增final-wheel-binding将实际METADATA对齐analyst原12×44观察图，只在独立overlay把43 pending/missing减去新root得到42缺第三方wheel；原graph不追改，来源/许可闭包仍BLOCKED。整合依赖、Python/runtime、Connector/Skill边界与NEXT_GATE正式材料，保留QUALITY_REPORT供独立QA。随后精确提交九件当前docs（八正式加PLAN）及唯一pyproject版本差异，冻结review-payload+逐成员index、必要METADATA原证/明确脱敏件与全部截至冻结的command originals；candidatewheel单独外置。此时不封最终reviewZIP、不调用新宿主、不扩生产范围。

## 独立 QA 后正式收口（当前续写授权）

THIS_TASK_INDEPENDENT_QA = PASS_LOCAL_ARTIFACT_STATIC_QA_WITH_LIMITATIONS；首次quality已独立完成，报告原字节复制，原阶段PENDING仅属历史。QEA-01 HIGH依赖受信分发/binary/完整许可/公共来源BLOCKED、QEA-02 MEDIUM旧0.3.1 readiness、QEA-03 MEDIUM外置12基线/缺11可选默认fixture、QEA-04 MEDIUM历史成功输入/HTTP原body NOT_REPLAYABLE均未闭合。QEA-04是5条成功receipt引用4个不同输入缺recordedSHA精确原版；原HTTP只有digest/长度，脱敏正文不是原body。所有失败receipt及变化失败脚本匹配原版保留，不补造原输入或旧HTTP，不宣称完整历史重放。

本续写仅DOC文档、本地docs commit及忽略RUN新审阅材料/封包脚本；核心八/129snapshot/版本/wheel/Connector/Skill/测试/旧保护原件不改。实际执行新增累计<=100s，每命令<=120s，经record_command roledeveloper新label保留原证，失败计入。复核diff仅DOC、source/wheel/保护与卫生/secret/citation，精确暂存提交后外置final-docs-state。九正式要求+PLAN齐全；原387件payload/index/首次确认不动，新finalpayload以prefix保留旧树，完整新index冻结后不再改。新文档和封包脚本必须限定独立复审；不沿用首次确认、不代签独立PASS、不封最终ZIP、不安装/运行产品/模型/Office/pytest，不推进后续门禁。
