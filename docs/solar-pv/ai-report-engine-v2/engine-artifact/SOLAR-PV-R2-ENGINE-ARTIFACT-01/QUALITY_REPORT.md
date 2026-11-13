# SOLAR-PV-R2-ENGINE-ARTIFACT-01 — 独立 QUALITY_REPORT

## 1. 独立裁定与范围

**THIS_TASK_INDEPENDENT_QA = PASS_LOCAL_ARTIFACT_STATIC_QA_WITH_LIMITATIONS。**

本结论来自独立 quality 读取最终真实代码、Git blobs、实际 wheel、原始依赖 METADATA 和冻结 payload 后运行的只读静态审计，不是开发者 verdict 的复制。包内批准 R2 核心、正式规格、声明 package-data、成员与 RECORD 完整性通过；尚未完成依赖受信分发闭包，不是普通隔离安装、Skill 运行、WorkBuddy 宿主、专业语义或发布验收。没有执行产品命令、pytest、财务或 Office/PDF 生成，没有安装、下载、重建 wheel、模型调用或 Git 写入。

| 对象 | 独立结论 |
|---|---|
| 源码与批准候选绑定 | PASS_LOCAL_APPROVED_SOURCE；不等于公众来源/所有权证明 |
| 本地唯一构建 | WHEEL_BUILT_LOCAL；真实 backend/原回执身份通过，quality 未重建 |
| wheel 成员/CRC/SHA/RECORD | PASS_INTEGRITY_AND_EXACT_MEMBERSHIP |
| 内容范围 | PASS_SCOPED_R2_MODULES_SPECS_DECLARED_DATA；不是全功能自包含运行包 |
| 静态入口 | AST_STATIC_TARGET_RESOLVED_NOT_EXECUTED |
| 12 目标 observed METADATA 图 | PASS_OBSERVED_METADATA_CONSISTENCY_NOT_A_LOCK |
| 依赖受信分发、binary wheel 与许可闭包 | BLOCKED_DEPENDENCY_DISTRIBUTION_NOT_CLOSED |
| 387 成员固定审阅 payload | PASS_EXACT_FROZEN_ALLOWLIST_WITH_DISCLOSED_LINEAGE_LIMITATIONS；只限第 6 节身份 |
| 普通隔离安装/installed import/help/业务运行 | NOT_TESTED |
| Skill Bash/Connector 同解释器与运行 | NOT_TESTED；未来 readiness 另有已知阻断 |
| WorkBuddy host E2E/真实模型新 CH08 | BLOCKED；没有新 draft |
| 专业语义/正式四文件/发布 | NOT_TESTED / BLOCKED；不升级历史门禁 |

不存在本轮确认、需要擅改批准核心源码的新增实质缺陷。第 7 节的发布阻断、可选默认资源缺口和证据重放限制必须保留，不能将本表压缩为无条件 PASS。

## 2. 被审身份与最终代码审查

- 审阅 HEAD：`27aa7d37d2eae1b4e82198ce5898bc8e4f58f494`，分支 `main`，实际 status/index 干净。
- 批准源基线：`94ce5f04b72937a205c194d55005bddd4ce6bd90`。
- 相对基线唯一生产改动为 `services/solar-pv-engine/pyproject.toml` 分发版本 `0.3.1` → `0.3.2`；其余变更仅本任务交付文档。独立保存完整最终 diff 于 `independent-qa/reviewed-final-candidate.diff`，未打印 Git 个人邮箱。
- 129 件源 snapshot 与当前工作树、`RUN/build-source` 原字节逐项相同；129 件源对应基线及最终 HEAD 的真实 Git blobs，只有批准版本差异。Git checkout 的 CRLF/LF 比较仅用于 Git 解释，source → wheel 始终比较原字节。
- snapshot 集合 SHA-256：`d4662f988413fcfecb7024db3c418887c680239ca51aa2b887f47930d0eb743c`。
- 八核心全 hash 集合：`3b41751eb36a632e38c0aab123e25eb66a271e84d2de1ee42d0b06a5f92993c4`。与 `approved-core-before.json`、旧 RESULT/PROTOCOL、旧 R1/R2 独立 QA 身份绑定不变，不把历史 136 用例当作本轮新执行。

实际阅读 `host_input_view.py`、`chapter_writer.py`、`host_session.py`、`host_output.py` 等真实生产路径及相关 Catalog/registry/wrapper：新模式仍经授权、原 request/canonical/spec/model/重建 pack 的可信链；首次派生前 `_request_base`，后续公共 `_request` 和 publish/verify 入口校验共享 view/manifest，缓存上游不会绕开公共校验。源码内容与批准版本逐字节绑定；这不是重新执行生命周期或穷举并发/崩溃的证明。引擎冻结标识 `SOLAR-PV-AI-REPORT-ENGINE-2.0.0` 未变。

## 3. 唯一 wheel 的逐件独立核验

候选：`RUN/candidate-wheels/wangbin_solar_pv_input-0.3.2-py3-none-any.whl`。

- 实际 **557392 B**，SHA-256 **`cd7be44ca5350da87c4760898ddeb46b8a73646d8f2f8de6be61e48cca9f7808`**。同目录只有这一候选 wheel，ASCII/LF sidecar 原字节一致。
- **122** 个唯一、安全成员；无大小写别名、绝对/穿越路径、反斜杠/盘符路径、目录/链接/特殊类型或加密项。逐成员实际读取、size、CRC32、SHA-256 和 ZIP 完整 CRC 均核对；不只相信外部 manifest。
- RECORD 恰好 **122** 唯一行，成员集合完全相等；**121** 非自身项逐项核对 URL-safe、无 padding SHA-256 与十进制 size；RECORD 自身 hash/size 均为空。
- 从真实 pyproject 的包发现与 package-data 模式独立计算期望集合，再与 ZIP 集合核对；**117** 件 authored 映射 = **97** Python 模块 + **20** 声明 data。全部 source → snapshot → wheel 原字节一致，97 模块全部 AST parse。
- 四个 R2 关键模块 `host_input_view/chapter_writer/host_session/host_output` 均存在且为批准原字节；两件正式 `reporting/specs` 全在包中。正式 report-spec 归一化 LF SHA 仍为 `59e379906f6b83d91a76179f14fdc00e5c0dc9346ef5d272bbcf04da90df7532`。
- **5** 个 `.dist-info` 是 backend 生成，不能冒称源码原件：METADATA、WHEEL、entry_points.txt、top_level.txt、RECORD。METADATA 与本次 sourcecopy 生成的 PKG-INFO 同字节；entry_points/top_level 与生成源同字节。Name/Version、Requires-Python、8 项 Requires-Dist 与 pyproject 的语义精确相等。
- WHEEL `py3-none-any` / purelib、console script `wangbin_solar_pv.cli:main`、package `__main__`、reporting `__main__`、host_session `main` 静态对象可达。没有 import、`--help` 或安装验证；从源码能解析对象不代表实际依赖存在。

构建原证：现成 Hermes Python **3.14.9** 与 setuptools **84.1.0** 直接 `setuptools.build_meta`，不是裸 global python/pip。实际 backend 文件 hash、生成元数据、命令输入 SHA、stdout/stderr SHA、exit0、显式离线环境与嵌入原 receipt 均独立核对。真实 build receipt 11.623812300153077s，backend 内部 1.9162649996578693s；quality 不再构建。环境与 Python audit hook 是合作式离线防护，不是 OS 沙箱；只构建一次，不能声称 reproducible build。

## 4. 包内必要资源的独立判定

**本轮 R2 核心/正式规格/声明数据完整，不应升级为“全部运行功能自包含”。** 这不是看到作者披露缺项就忽略问题：

1. 11 件 tracked synthetic/editorial fixture JSON 确实在 129 源 snapshot 中、但不在声明 package-data 或 wheel 中。`report_narrative.load_editorial_fixture` 默认定位包内 `fixtures/solar_pv_editorial`，该默认演示资源路径静态上不完整。因此可选默认演示加载存在真实包内容限制；不能声称全部 demo/legacy API 可用。它们不是 R2 正式宿主输入，亦未作为真实 canonical/模型结果补齐。当前范围不授权打包或业务行为修复。
2. Catalog 从包内 `baseline-lock.json` 读取 **12** 件冻结外置基线，并按既有 `--baseline-dir` 合同加载；wheel 未携带这些原件。quality 逐项核对仓库真实基线、锁定 LF 内容 SHA，以及现有 Skill wrapper 所带 12 件副本的归一化内容。wrapper 明确传 baseline-dir，不能据此说 standalone wheel 无外部资源即可运行。
3. 若验收口径是“批准 R2 模块和正式 specs/声明 data 构件”，本轮通过；若口径是“所有功能、默认演示和冻结基线全部包内自包含”，本轮**不满足**。两种标准不可混写。未运行产品，故不宣称穷举所有动态资源组合。

## 5. 实际 METADATA 依赖、平台与来源

独立从真实原 METADATA 重新解析 Name/Version/Requires-Python/Requires-Dist、extras 和 markers，再计算固定点可达集、全部 active/inactive 边、选定 observed 版本约束；不是重复 analyst 的 counts/verdict。

- 目标为 Windows AMD64、Linux x86_64、macOS x86_64、macOS arm64，各 Python 3.12/3.13/3.14，共 **12** 矩阵；每个 **44** 个可达 observed METADATA 节点，extras/marker 与图一致，当前选定集合无版本/Requires-Python 冲突。
- 原图 source candidate 缺独立 wheel 的 43 项包括尚未构建的 solar；绑定实际新 wheel 后，每个目标仍缺 **42** 个第三方独立 wheel。保留 analyst 原图 SHA，不把安装目录/cache 的 METADATA 或 WHEEL 文件当作可安装 wheel。
- `markitdown[docx,pdf,pptx,xlsx]==0.1.9` extras 实际展开；其 core → magika，magika 的 Python 分支要求 onnxruntime，xlsx → pandas，pdf → pdfminer/pdfplumber/Pillow/pypdfium2 等均纳入，不只列直接 8 项。
- 实际 pdfplumber METADATA 要求 `pdfminer.six==20260107`、`Pillow>=12.2.0`；与 solar 的 `Pillow>=10,<13` 共同约束，不能只看 solar 的较宽范围。
- 实际 local pandas **3.1.1** 的 direct tzdata 仅 win32/emscripten；但实读 local python-dateutil **4.0.0** 的 Requires-Dist 为无条件 tzdata。因此 Linux/macOS 仍经 markitdown[xlsx] → pandas → python-dateutil → tzdata。这里仅陈述所绑定的 local observed METADATA，不假设等于上游常规记忆。
- 对 **18** 个非纯通用的 installed/cache 分发，另读真实 WHEEL 文件确认 tags。Pillow 观察值是 **cp311-cp311-win_amd64**，不兼容任一 CPython 3.12/3.13/3.14 目标，尤其不能当作各 OS 可用 wheel。ABI3 不能一概按 cp311 拒绝；不同 OS/architecture、Python ABI 和 macOS deployment/manylinux policy 必须分别证明。补充 tag 表是保守静态诊断，不是发布 resolver 或完整目标 tag 锁。
- 新/原/派生 metadata 索引共 **50** 条逐项核对 original SHA/bytes → 明确 email 替换 → shared SHA/bytes；**43** 条带 email 脱敏。原/派生 Name/Version/Requires-Python/Requires-Dist/extras 语义未变，没有伪造依赖边。派生 hash 不充当原件 hash，也未输出邮箱值。
- 真实 build backend 的静态 Requires-Dist/Requires-Python 同样读回；未请求动态 build requirements，不以 backend 的测试/文档 extras 冒充本次必要安装依赖。现成 setuptools 自带 bdist_wheel，独立 wheel 分发缺失没有阻止已发生的本地构建。

独立读回 4 份历史 wheel：只有一份旧 solar0.3.1，实际缺 host_input_view/host_output；两份 document1.2.0 同名不同 SHA，其中历史 candidate 缺 LICENSE 成员，不能覆盖/改名/互换旧件。现有本地 hash、sidecar、manifest 不证明公众不可变分发、授权来源或完整许可证清单。新 wheel 本身也不关闭这些信任问题。

官方页面证据核对的是 analyst 保留的脱敏正文及其 SHA。原始 HTTP body 只有 receipt 中的 digest/长度，不是当前保留正文的原字节；本轮没有重新联网，不对原 HTTP body 做独立重放证明。当前官方文档的声明也不是 WorkBuddy 5.5.2 实际部署、OS 沙箱、业务超时/清理、发布者权限或 Skill Bash 解释器的实测证据。

## 6. 冻结 payload、隐私与原证

本次允许清单只绑定 `RUN/review-payload` 当前固定树，不绑定未来改文档后的另一 payload：

- **387** 文件，实际合计 **9226577 B**。
- `RUN/payload-index.json` SHA-256：**`846187c624ce4907a81b6e6772e46d95e2694341937e0dd0178d9f3e30d3903d`**。
- tree SHA-256：**`4a853ddbed248b8218a874cc51e00083f70529548ab773d2a2e5cd752f7455e6`**；算法为按路径排序，对 `UTF8(path) + NUL + ASCII(member_sha256) + LF` 拼接后 SHA-256。不是 Git tree 对象。

逐项验证实际集合、唯一安全路径/类型、size/hash、源映射、email 原/派生转换与 earlier report 精确保留身份。排除 wheel 二次嵌入、venv/cache/buildtree、完整测试目录、保护的 canonical/request 原文、秘密/私有会话；既有 synthetic fixtures 仅作为 source 审阅副本，不是新增测试或真实资料。唯一 wheel 外置，payload 不是 Skill 安装包。

- 对 payload 使用仓库既有 secret scanner 原字节代码，没有扩充全局 SAFE_VALUES。唯一 finding 精确落在绑定 SHA 的 pdfplumber METADATA 公共用法示例；独立核对 password-protected PDF 的 `e.g.` 上下文和 matched-value hash，判为该精确文件内公开示例，不是实际凭据。未输出 matched value。除此之外扫描无未解释 finding；email regex 无剩余匹配。这不等于任意形式秘密的数学完备性证明。
- build receipt 在原文件中**没有字面 `202****1021` 掩码**，其 recorder 解释器路径实际存在；payload 的对应原件/源映射同样没有该字面掩码。工具展示层出现的星号不能据此判为文件被静默隐私改写。原/派生身份依实际 bytes，而非渲染文本。
- **29** 份既有命令 receipt 及完整 stdout/stderr 的 exact SHA/bytes 独立读回；其中 **6** 份失败原证保留。所有已变化的失败命令脚本均找到匹配原 input SHA 的旧副本且已入 payload，不覆盖失败 raw，也不将独立审计失败改写为成功。
- 另发现 **5 条成功命令输入引用**（4 个不同历史输入）无法在所审任务原证/payload 找到其 recorded SHA 的原版：analyst dependency_audit.py、metadata-catalog.json（两份 receipt 引用）、ANALYST_REPORT.md，以及旧 developer-candidate-freeze.json。当前文件不同不意味着原执行虚构；但不能声称这些历史成功命令具有完整原输入重放链。当前 graph/50 metadata/最终 source/wheel 均已由 quality 独立重算，不依赖重放那些旧脚本。详见 QEA-04。

因此本次 payload **字节/允许清单/已知隐私扫描通过，带明确历史 lineage 限制**；其原 PENDING 字段是冻结历史状态，quality 不追改。未封 ZIP、未自引用、未改 payload。后续只允许对这棵精确树做确定性 manifest/QA 身份记录及逐件读回；如正式 RESULT/VALIDATION/NEXT_GATE/QUALITY_REPORT 追加后产生新集合或实质正文变化，必须新 index/新 tree 并进行限定独立复核，不能沿用本次确认自动批准。

## 7. Findings、严重性与真实整改需求

| ID | 严重性/范围 | 独立 finding 与下一步 |
|---|---|---|
| QEA-01 | HIGH / 安装发布阻断，既有未闭合 | 12 目标各缺 42 第三方独立 wheel，来源/完整许可/不可变受信渠道未闭合。未来另批取得精确目标 wheel+SHA+约束及许可来源；当前保持 BLOCKED，不下载、不假造 lock。 |
| QEA-02 | MEDIUM / 未来运行阻断，非本轮新增 | 包内 connector_runtime readiness 与三 OS Connector init 仍钉 solar0.3.1，Skill 说明仍旧。0.3.2 分发 metadata 不会自动 LOCAL_READY。未来另批最小版本元数据对齐，随后证明受信隔离安装及 Skill 同解释器；本轮不可偷改运行合同。`__version__=0.3.0` 是 input_module_version，不据此判断 wheel 分发身份错误。 |
| QEA-03 | MEDIUM / 非自包含及可选演示资源限制 | 12 基线需显式外置；11 tracked fixture 被排除且 optional 默认加载路径缺资源。本轮 R2 核心/specs/声明 data 通过，但 full-runtime/default-demo 完整性不可 PASS。未来若需该承诺，另批明确演示 API 是否支持及资源分发合同，不以 mock 或真实宿主输入替代。 |
| QEA-04 | MEDIUM / 历史证据可重放性；不阻断当前独立字节审计 | 5 条成功 receipt 输入引用缺 exact 原版；另原 HTTP body 只有 digest，不能从保留脱敏正文重建。不得声称完整历史重放/原 raw 全保留。若原版确实仍存在，可另存原件+派生索引；否则只能明确 NOT_REPLAYABLE，禁止合成原输入。当前固定 payload 审阅允许清单可接受，但新的正式收口材料必须披露此限制。 |

这些 finding 未触发批准核心修改。QEA-01/QEA-02 是未来安装/发布 stop gate，QEA-03 是内容承诺边界，QEA-04 是复现性边界；均不能用本轮静态 PASS 关闭。

## 8. 独立命令、失败保留、保护与预算

所有独立 OS 审计命令经 `RUN/record_command.py --role quality`，独名 label、绝对现成解释器、`-I -B`、input SHA、stdout/stderr、开始结束/exit/耗时落原证。未注入 PYTHONPATH，未安装包装成 installed PASS。

| label | timeout 上限 | 实际 elapsed s | 结果 |
|---|---:|---:|---|
| independent-artifact-audit-r1 |100|12.481718000024557|exit1；source/provenance/protection/dependency 通过；独立审计脚本误写 codec `utf8-sig`，另初版按更严格规则拒绝缺 exact 旧成功输入；非产品执行失败。原脚本及 raw 不改。|
| independent-wheel-payload-r2 |60|11.488323300145566|exit0；新独名脚本改合法 `utf-8-sig`，完整 wheel/payload 检查，保留旧成功输入差异并交独立 finding 裁定，未隐藏或删除差异。|
| independent-resource-lineage-supplement |90|1.7069613998755813|exit0；实际 WHEEL tags、12 外置基线/Skill副本、4 历史 wheel、build元数据、所有失败输入留存及历史门禁核对。|

最终只读封口命令与 confirmation/provenance 的实际身份见 `RUN/commands/quality-independent-final-readback.json`、`independent-qa/provenance.json`，后者不预填当前命令未来 elapsed。累计精确时间以全部 quality receipt 求和，包含失败；本角色预算 200s、任务总预算 900s，每命令 <=120s。表中耗时是实测执行时间，不以会话墙钟代替。

保护实读：**1929** 项中 **1928** 原字节不变，唯一变化为批准 pyproject 版本；installed **22**（21 payload+1 metadata）SHA 不变；历史 **2638** 仅 size/mtime_ns 不变，明确**没有做历史全内容 hash**。无生产/测试/fixture/版本/docs/Git/安装写入，无删除/净回收。只新增 `RUN/independent-qa` 审计脚本/原证/本报告与授权的 `RUN/payload-quality-confirmation.json`，command recorder 按合同追加 role-quality 原 receipt。正式 QA 文档由唯一 writer 原字节复制，quality 不写正式 DOC。

## 9. 继承门禁（原值精确保留）

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

旧 R1 PARTIAL、旧 R2 PASS_LOCAL_QA_NOT_AI_NOT_HOST_E2E 与旧 timeout 不追溯改判。本轮新 gate 名为 THIS_TASK_INDEPENDENT_QA，不能覆盖上述历史 gate。终期现金合法重绑定、SCENARIO_COMPARISON BLOCKED/ranking 空、独立交易费实付、专业签审、同 canonical 五身份正式四文件及 STATIC_SNAPSHOT 披露等原未决不关闭；Phase D 范围不扩展，无 CH10/16 或 Phase E/F/G 解锁。

## 独立原证索引

以本任务 RUN 为根：

- `independent-qa/source-readback.json`：129 源映射、八核心、最终 diff 身份。
- `independent-qa/wheel-members-independent.json`：122 成员 CRC/SHA/RECORD、117 source 映射、实际 metadata、入口、11 excluded 源文件。
- `independent-qa/dependency-recomputation.json`：50 原/派生 metadata、12 矩阵全部重算边及缺项。
- `independent-qa/payload-members-independent.json`：387 逐件身份、29 命令流、精确 secret 例外、历史 input 差异。
- `independent-qa/audit-result.json`：首轮失败原裁定；`audit-result-r2.json`：完成技术检查的限定结果，不覆盖首轮。
- `independent-qa/supplement-readback.json`：18 实际非通用 WHEEL tag 记录、12 baseline、4 历史 wheel、5 历史成功 input 缺口、官方正文及 inherited gates。
- `independent-qa/provenance.json` / `RUN/payload-quality-confirmation.json`：封口读回、report/证据 hash、精确候选身份和允许清单边界；不自引用。
