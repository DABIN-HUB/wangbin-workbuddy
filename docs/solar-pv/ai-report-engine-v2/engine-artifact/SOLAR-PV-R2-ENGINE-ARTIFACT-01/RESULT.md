# SOLAR-PV-R2-ENGINE-ARTIFACT-01 — 本地构件与独立静态 QA 结果

**THIS_TASK_INDEPENDENT_QA = PASS_LOCAL_ARTIFACT_STATIC_QA_WITH_LIMITATIONS；WHEEL_BUILT_LOCAL，尚非依赖闭包、受信安装或发布通过。** 独立结论仅绑定原候选及原 387 件冻结树；本次正式文档和新 final payload 须另作限定独立复审，不能自动沿用原确认。唯一候选：

- `.runtime/solar-pv/SOLAR-PV-R2-ENGINE-ARTIFACT-01/candidate-wheels/wangbin_solar_pv_input-0.3.2-py3-none-any.whl`
- 557392 bytes；SHA-256 `cd7be44ca5350da87c4760898ddeb46b8a73646d8f2f8de6be61e48cca9f7808`；同目录 ASCII/LF `.sha256`。
- 来源 HEAD `94ce5f04b72937a205c194d55005bddd4ce6bd90`、main；批准核心八文件原 SHA 集合 `3b41751eb36a632e38c0aab123e25eb66a271e84d2de1ee42d0b06a5f92993c4` 未变。
- 唯一生产差异为 solar-pv-engine/pyproject.toml 分发版本0.3.1→0.3.2；冻结 `SOLAR-PV-AI-REPORT-ENGINE-2.0.0`、依赖、事实/计算/公式/运行协议无变更。

## 直接证据与判定

| gate | 构建阶段状态 |
|---|---|
| TRUSTED_WHEEL_SOURCE | PASS_LOCAL_APPROVED_RAW_SOURCE；实际129源文件对应批准 Git blobs；不是公众分发所有权证明 |
| VERSION_RESERVATION | LOCAL_RECORDS_NOT_OCCUPIED；75受控记录、4历史独立wheel、58ZIP中央目录；未联网/不证明所有机器或公众记录无冲突 |
| WHEEL_BUILD | WHEEL_BUILT_LOCAL；现有Python3.14.9 + setuptools84.1.0 直接backend，离线、独立source快照、真实exit0 |
| WHEEL_INTEGRITY | PASS；122安全唯一成员、CRC/SHA/完整RECORD集合与自空规则 |
| WHEEL_CONTENT | PASS_DECLARED_PACKAGE_SCOPE_WITH_EXPLICIT_RUNTIME_LIMITATIONS；117原字节映射=97模块+20声明data，正式specs两件完整 |
| ENTRY_REACHABILITY | AST_STATIC_TARGET_RESOLVED_NOT_EXECUTED；不是import、help、安装或业务运行 |
| DEPENDENCY_CLOSURE | BLOCKED_DEPENDENCY_DISTRIBUTION_NOT_CLOSED；analyst原12×44图不改，新wheel独立绑定43→42第三方缺wheel；observed metadata consistent不等于lock/closure |
| THIS_TASK_INDEPENDENT_QA | PASS_LOCAL_ARTIFACT_STATIC_QA_WITH_LIMITATIONS；独立 quality 原报告原字节复制，限定原候选/387 件树；新 final payload 待另行独立确认 |
| ISOLATED_INSTALLATION | NOT_TESTED（本轮禁止） |
| WORKBUDDY_SKILL_RUNTIME | NOT_TESTED |
| WORKBUDDY_HOST_E2E | BLOCKED |
| PROFESSIONAL_SEMANTIC_REVIEW | NOT_TESTED |
| RELEASE_READY | BLOCKED |

命令回执、失败原证及历史成功输入重放限制见 VALIDATION.md；完整映射见 WHEEL_CONTENT_MANIFEST.json；构建来源与原始时间见 BUILD_PROVENANCE.json，不追改已发生的命令。独立 QUALITY_REPORT.md 为 20247 B，SHA-256 `7c1f7b4727b9740dc27a6e5be291ec106d0b3b8a3f7806a4d0165a90b4bf2d32`；原 provenance SHA `8afdf3e3d0155561e32f5400ac45996357f777eb6d49bb180beaf57916c841b3`，原 payload confirmation SHA `df87db15c1cda56123a5e6c0154e96a946525ae8ec7c51e7efa456d4158d6bbb`。其审阅 HEAD 为 `27aa7d37d2eae1b4e82198ce5898bc8e4f58f494`，不是本次未来文档提交。独立重新计算 source/wheel、50 metadata、12×44 图及原 payload 身份有效；不等于完整历史原输入重放。

## 不扩大本轮成功范围

- wheel不含12件外置冻结基线；Catalog原合同要求显式baseline-dir，已有Skill wrapper单独提供。11件既有tracked synthetic/editorial fixture源文件未声明package-data、未入wheel；可选演示加载默认目录仍不完整，不把它们冒充R2宿主输入或全功能PASS。逐件分类/大小/SHA均在manifest。
- legacy `__version__=0.3.0` 是input_module_version；引擎内connector_runtime readiness仍钉0.3.1，Connector init与Skill说明同样旧钉。为保留本阶段运行合同未改这些文件。未来0.3.2安装也不能自动READY；后续另批最小metadata对齐、分发及实际部署验证。
- 历史solar0.3.1轮子缺新host_input_view/host_output；document1.2.0有两份不同hash。版本号并非批准源码一致性证明；所有旧wheel/dist原字节保留，没有覆盖、替换或改名冒充。
- 构建只实际做一次，SOURCE_DATE_EPOCH不等于reproducibility；现有3.14.9位于声明范围也不证明各OS或3.12托管环境。未安装wheel、不注入PYTHONPATH、不声称installedimportPASS。
- 首轮静态工具因错误codec名称exit1，修正后新独名批次exit0；原receipt/stdout/stderr及匹配原input SHA脚本完整保留。初版manifest将11演示数据误标UNTRACKED，实际ls-files封口修正为TRACKED；源码/wheel不变，不覆盖原命令事实。

保护实读：1929项中1928不变，1项批准版本变更；installed22全部SHA不变，R8–R13metadata2638不变（非全内容hash）。无删除，净删除0文件/0B/释放0B。本次只提交 DOC 文档；九项正式交付文件及 PLAN 共十文件齐全。最终实际 HEAD/clean/index、计数与已完成命令计时外置 `RUN/final-docs-state.json`，不自引用未来 commit。原 `review-payload` 387 件/9226577 B、原 index 与首次 confirmation 均不改；新 `final-review-payload` 以 frozen-candidate/ 前缀原字节保留原树，根 RESULT 为当前入口，外置 `final-payload-index.json` 冻结新集合。唯一 wheel 继续外置；源码审阅包不是 Skill 安装包、不是完整仓库备份，不含 Git bundle/私人 Git 配置。待新独立确认及 manager 最后保护复核前不封 ZIP；详见 NEXT_GATE。

## 独立 findings — 原级、均未闭合

| ID | 严重性 | 当前限制 |
|---|---|---|
| QEA-01 | HIGH | 依赖受信分发/binary/完整许可/公共不可变来源仍 BLOCKED；12 目标矩阵每格缺 42 第三方独立 wheel，observed 图不是 lock。 |
| QEA-02 | MEDIUM | readiness 与 Connector 仍钉旧 0.3.1；0.3.2 分发元数据不能自动 LOCAL_READY，未改 Connector/Skill。 |
| QEA-03 | MEDIUM | 12 外置冻结基线与 11 缺失可选默认演示 fixture；R2 核心/specs/声明 data 通过不代表全功能自包含。 |
| QEA-04 | MEDIUM | 5 条历史成功 receipt 输入引用涉及 4 个不同输入，缺 recorded SHA 精确原版：analyst dependency_audit.py、metadata-catalog.json（两次引用）、ANALYST_REPORT.md、旧 developer-candidate-freeze.json。原 HTTP body 仅存 digest/长度，保留脱敏正文不是原 body。上述链为 NOT_REPLAYABLE，不得声称完整历史重放或所有 raw 全保留，不补造丢失输入或重建旧 HTTP。所有失败 receipt 及已变化失败脚本的匹配原版保留；本项不是失败原证缺失。 |

## 历史门禁逐值保留

```text
WORKBUDDY_552_CLIENT_VERIFIED = PASS
WORKBUDDY_R2_SKILL_IMPORTED = PASS
WORKBUDDY_R2_HOST_NEW_ROOF_CH08 = BLOCKED_NO_DRAFT
WORKBUDDY_R2_HOST_NEW_GROUND_CH08 = NOT_TESTED_BLOCKED_BY_STOP_GATE
ROOF_JSON_SCHEMA_VALID = NOT_TESTED_NO_DRAFT
GROUND_JSON_SCHEMA_VALID = NOT_TESTED_NO_DRAFT
ROOF_STRICT_CHAPTER_VALID = NOT_TESTED_NO_DRAFT
GROUND_STRICT_CHAPTER_VALID = NOT_TESTED_NO_DRAFT
INSTALLED_R2_ENGINE_AND_DEPENDENCIES = UNVERIFIED_BLOCKED
WORKBUDDY_R2_PUBLISH_ACCEPT_RESUME_DOCX = BLOCKED_NOT_EXECUTED
WORKBUDDY_R2_HOST_E2E = BLOCKED
R2_REAL_MODEL_CONTENT_ACCEPTANCE = BLOCKED_NOT_PASS
INDEPENDENT_QA = PARTIAL_PREVIOUS_EXECUTED_UNCHANGED
PROFESSIONAL_SEMANTIC_REVIEW = NOT_TESTED
PHASE_D_CONTENT_REVIEW = USER_REVIEW_REQUIRED
TRUSTED_ENGINE_INSTALL = BLOCKED_UNVERIFIED
WORKBUDDY_INSTALLED_HOST_E2E = BLOCKED
THIS_AUDIT_INDEPENDENT_QA = PARTIAL
```

旧R1 PARTIAL/R2限定本地源码QA原结论不覆写。候选终期现金合法重绑定、SCENARIO_COMPARISON BLOCKED/ranking空、独立交易费实付缺口、会计盈利/经营现金/股东回收裁定、PDF公式复制检索/真实资料/专业签审、同canonical五身份正式四文件、STATIC_SNAPSHOT披露、全仓回归/Expert/发布均不关闭，不移AFTER_V2。Phase D仍双案CH05/08/10/14/15/16/17/18；无CH10/16解锁或Phase E/F/G推进。没有客户端新任务、模型、下载/安装/环境改动、Connector/Skill变更或替换、push/sync/reset/发布。
