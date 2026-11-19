# SOLAR-PV-R5-DEBT-F1-RUNTIME｜限定执行回执（非发布）

> 范围仅为本仓库光伏预可研；基线 `main / f707147537fd00bd535d68c4f0b89eec26e261d6`，父提交 `57715cdbc5cb85e936df46a264906c7558ce83c0`。本报告提交后的完整 HEAD、Git 读回和最后独立 QA 结论以忽略目录 `.runtime/solar-pv/R5-debt-f1-runtime/final-state.json` 为准；报告不能预先嵌入自身提交 SHA。此处的候选不代表 WorkBuddy 已安装或产品获准发布。

## 1. 债务证据与方法边界

- `_debt()` 原实现即使显式计划或期初余额存在，仍可能因 `finance.debt_ratio=0` 返回 `has_debt=False` 和期初零。现在非空计划、非零期初本金或期初应付利息是债务证据；`NO_DEBT_DECLARED` 与证据冲突报 `DEBT_BASIS_EVIDENCE_CONFLICT`。零比例但无证据且未明确 `NO_DEBT_DECLARED` 报 `DEBT_BASIS_NO_DEBT_REQUIRED`；只有明确无债且无证据才返回无债。不凭比例值将债务抹零。
- 期初本金在既有偿还算法未定义如何纳入 bullet、等额本金、annuity 和剩余期限前报 `DEBT_OPENING_PRINCIPAL_REPAYMENT_UNSPECIFIED`，**未补偿还公式**。已有显式债务计划仅在其余方法与输入齐备时计算；缺资料保持阻断。输入层不再以 `ZERO_DEBT_WITH_SCHEDULE` 在方法绑定前拒绝整个零比例计划；敏感性 `LOAN_INTEREST` 及 IN-C06 条件义务均按显式计划/余额判断，不把 `ASSUMED` 来源升级成已核实事实。
- `finance.debt_ratio` 缺失、UNKNOWN、CONFLICT、非有限或非精确数值在直接敏感性校验中仍报 `BLOCKED_MISSING_INPUT`；公开 `prepare_scenario` 对畸形输入会更早返回既有的 `INPUT_VALIDATION_FAILED`，不是该直接校验的错误码。明确无债时 DSCR 原有 `NOT_APPLICABLE/NO_DEBT` 与有债但零偿债额 `UNDEFINED/ZERO_DEBT_SERVICE` 不合并；CFADS 仍独立阻断。未更改冻结公式、真实工程日期模型或 R3 现金流。

## 2. F1 负例与实测回执

- 终端来源字节与 `source_content_sha256`、carrier hash 同步重封；未声明资产的原文断言 `TERMINAL_ZERO_DECLARATION_UNSUPPORTED`；有自洽声明、但资产不在账簿范围的原文断言 `TERMINAL_ASSET_SCOPE_MISMATCH`。原案/候选交易费来源分别绑定；保持来源缺失与重算 fail-closed。最初目标负例因来源字节错误曾失败，旧 XML/日志原样保留，新回执不能覆盖它。
- JUnit `<testcase>` 实际计数（全部保存在忽略的 `.runtime/solar-pv/R5-debt-f1-runtime/`，非正式 L3）：

| 专项 XML | 通过 | FAIL / ERROR / SKIP | XML SHA-256 | 最后源码关系 |
|---|---:|---|---|---|
| `financial-ledger-remediation.xml` | 18 | 0 / 0 / 0 | `a4b1aefb73039b4547928ae76fcef5461d9722471cdf92181acd5b4088a607f0` | 最终 IN-C06 的 `conditions.py` 修改前；账簿/验证相关源码未再变 |
| `terminal-binding-final-rerun.xml` | 18 | 0 / 0 / 0 | `c60940ad1ab112dd05bdfa0f721c60f599d59d74ad5f1e6106d70fcced408533` | 最终 IN-C06 修改前；终端/账簿相关源码未再变 |
| `phase3f-scenario-runner-final.xml` | 12 | 0 / 0 / 0 | `a5bf71a767599387c2e64ddc25bdaf970e02ad4c4c7026ed38326af8def1ba2d` | 最终 IN-C06 修改前；敏感性源码未再变 |
| `conditions-final.xml` | 18 | 0 / 0 / 0 | `d6bd8da30c98304b00e0ca017191264394223fd381e1b469f9f47ec2102b3dca` | 最终 ASSUMED IN-C06 修复后实测 |

过去 F1 两项定向修复回执 `R4-F1-remediation-final-01/result.xml` SHA-256 `a0d07062a7b1398298c1a9792e52fd5851bda15220d0f930e5c97393c9b6c347`，属于先前源码，不与本轮重复累加。第三方插件的 `PytestRemovedIn10Warning` 另记，不计失败；首次超时的 F1 进程无完整 XML，不计 PASS。

最后独立只读 QA（`deleg_98f62f67`）针对 ASSUMED IN-C06 修复后的源码给出 `CONDITIONAL_PASS / 无本地代码缺陷`：独立核对上述四份原始 XML、债务判据、F1 来源字节与终端范围拒绝、当时的 0.3.2 wheel/RECORD/98 个 Python payload，以及受保护 `uv.lock`；该 QA **没有亲自重跑测试**。暂存时发现两个 Python 文件的工作树是 CRLF、Git 索引归一为 LF；仅做行尾字节归一（语义与已测代码不变），重建最终 wheel 并再次核对全部 Python payload、RECORD、manifest/sidecar、五个修改的生产文件 Git 索引字节。原独立 QA 的旧 wheel 哈希不再是最终包的证明；最终包采用下列新哈希。条件仍指完整回归、宿主安装、平台执行与发布未验证，不能称独立 QA 为产品验收通过。

## 3. 收集、去重与尚未执行

- 当前 `tests/solar-pv` collect 退出 0，共 **5083 唯一 nodeid**；`solar-collect-final.txt` SHA-256 `70ec13a3a92c2e19af327a7efeeaa0485f0be8fc2f5f97af7c1826af5698c344`。对 R4 的 5071，新增 13、拆去原 F1 混合负例 1；不能沿用旧 5071 或称全部验证。
- R2 原件保持 `829 = 820 PASS / 4 FAIL / 4 ERROR / 1 SKIPPED`；R4 历史限定选定 `843 = 842 PASS / 1 SKIPPED`（含后续 F1 两节点替换回执）。其中原混合 F1 节点已拆分，历史限定集合与当前集合交集为 842；历史结果不升级为 R5 最终 HEAD 回归。
- 本轮四份 XML 按 nodeid 去重，**66 PASS / 0 FAIL / 0 ERROR / 0 SKIPPED；其余 5017 当前节点为 NOT_TESTED（最终 IN-C06 编辑前的 48 项回执也不能充当整套最终 HEAD L3 证书）**。66 项中 28 与 R4 限定集合重叠，38 为该集合外实际执行。逐 ID 当前状态、历史指针、回执路径/哈希在 `r5-current-coverage.json`，该文件自身 SHA-256 `5a964f69c43a0d743f9bbde01eb16187807419f0ad0534e8af25d09126da1bcd`。R4 旧的 Windows symlink 跳过仍未在有权限的环境补测；完整 collect-l2/l3-solar/l3-workbuddy 三门禁**未运行**，`REGRESSION_TESTS=PARTIAL`。

## 4. 0.3.2 本地候选，不等于宿主

- 引擎分发、Skill engine/dependencies、Connector 三平台 init 与 `connector_runtime ready` 严格要求 `wangbin-solar-pv-input==0.3.2`。`__version__` / `input_module_version` 的 `0.3.0` 是**输入/模型契约身份**，未借分发升级改写旧输入哈希。
- 从 `services/solar-pv-engine` 包根以现有 `setuptools.build_meta.build_wheel` 重建唯一 R5 wheel，未联网安装新依赖。最终 wheel：`.runtime/solar-pv/R5-debt-f1-runtime/candidate-wheels/wangbin_solar_pv_input-0.3.2-py3-none-any.whl`，SHA-256 `8614cf0f159f862d356d09ab1eb7c1b6733dc8ec76b4a4fe945f76fe784c3097`，564828 字节；123 成员/RECORD 行，所有 RECORD 哈希与 98 个打包 Python 源码字节均已本地比对，且五个修改的生产文件与暂存 Git blob 逐字节相同。身份清单 `candidate-wheel-manifest.json` 和同目录 `.whl.sha256` 保留在忽略运行区。
- Skill/Connector 当前仓库源码重新打包至被忽略的 `dist/`，不覆盖既有 0.1.3/0.1.2 历史候选：`wangbin-solar-pv-prestudy-0.1.3-r5-0.3.2-skill-candidate.zip` SHA-256 `e2c207185049880c08bdeb92dc71a2727e167433f55cc0c552ec20715f28c283`；`wangbin-solar-pv-cli-0.1.2-r5-0.3.2-connector-candidate.zip` SHA-256 `d02a3bf2c7a410b3067b6dbbaf71fcc91fea23121ebcaec59d5bea9544a0f34d`。两者均核对 ZIP CRC、全部成员源码字节、manifest、sidecar；只是**本地包完整性**，不是上传或宿主安装。旧候选身份不被替换；`dist/` 与 `.runtime/` 已验证被 Git 忽略。
- 依赖下载/隔离安装、宿主解释器真实 import、Skill/Connector 安装启用、`LOCAL_READY`、WorkBuddy CH08 及文件回传均 **NOT_VERIFIED / 未授权执行**。需先选定目标客户端、解释器和实际 wheelhouse，裁定两份不同 `wangbin-document-cli==1.2.0` wheel 的身份，再由所有者逐项授权需要的安装/附件/模型及预算；不能拿开发机 PYTHONPATH、ZIP CRC 或静态 ready 文本冒充宿主成功。

## 5. 外部阻断与保护

- 两案 25 年日期现金事件仍缺可独立事先冻结并满足逐期对账的原始金额/日期/日计数来源：`BLOCKED_SOURCE_REQUIRED`；不得由现有 3D/3E 年度现金流反推来源。真实工程资料仍缺；保持 `SYNTHETIC` 限定。
- 屋顶/地面 CH08 均无新宿主模型调用/输出、`host_call_id` 或 prepare-r2→publish→accept→resume 回执；不能解锁 CH10/CH16。须先取得两份 canonical 的真实同运行五身份、来源许可及明确模型预算/附件授权；不伪造宿主请求或历史文稿。
- F04 仍 `DRAFT_PARTIAL`、正式 F02 公式复制/搜索及全页视觉仍 BLOCKED、40 项用户审阅 `PENDING`；专业签审、完整根集合、正式四件套和发布均未完成。不推进 Phase E/F/G，不修改报价专家、`uv.lock`、原始 R2/R3 证据或冻结财务公式。
- 本轮无已审定可净删的跟踪历史文件：净删除 0 文件/0 字节；保留原件。`uv.lock` 为唯一受保护未跟踪文件，不暂存、不修改；生成的 XML、矩阵和 wheel 留在忽略目录。`TRACKED_ARTIFACT_CLEANUP=PASS(0)`，`UNTRACKED_HYGIENE=PASS(受保护保留)`，`DIST_LOCAL_VALID=本地完整性 PASS / 宿主 BLOCKED`，`PLATFORM_RUN=NOT_TESTED`，`RELEASE_READY=BLOCKED`。最终仓库卫生、QA 和 Git 证据以 `final-state.json` 读回为准。
