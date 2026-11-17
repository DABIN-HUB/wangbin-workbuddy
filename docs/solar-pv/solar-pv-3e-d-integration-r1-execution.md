# SOLAR-PV-3E-D-INTEGRATION-R1 执行回执（合成验证，非产品发布）

> 本报告只记录本轮亲自执行/独立 QA 可读回的事实。新项目产物与旧 R2 身份不同；`PARTIAL` 的 3G 运行状态不是项目/专业/发布通过。下列非正式输出、日志及恢复输入存于 Hermes scratch 和仓库忽略目录，均不属于正式四件套。主仓库未跟踪 `uv.lock`、历史 R2/R4/R8–R13 与旧 dist 均不允许因本报告而被覆盖或推送。本轮未授权推送、替换安装、打包发布或 Phase E/F/G。

## 1. Git、范围和执行目录

- 候选：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-bundle-push.NQ8BomSU`（独立 clone、`main`，非主目录 `F:/ideaWorkSpace/wangbin-workbuddy`）；本轮开始 HEAD `bd534f99f4bf6db6b2b31621fb801f6c274441d2`，其父 `00a73b0ddaff493890b7162f99624c0e51347623`，再前 `1ffef162f0464f4971b1cda506a9093afb9b6d33`，更前 `a4455560ed04c2ca463889580c928a384b08d424`。`git worktree list --porcelain` 在独立 clone 只列本目录，不能据此否认另一个独立目录。
- 本轮本地、未推送：`63ddb5c5f4451d8779fbe221e919e4a5a83a064b`（`dated_cash_events.py` 精度与负例），`7fe9c0e7a7ab245ef8d620046e89907027125da0`（`source_xlsx.py` F04 来源映射与回归）。审阅包及本报告的最终提交 SHA 见忽略目录 `.runtime/solar-pv/SOLAR-PV-3E-D-INTEGRATION-R1/final-state.json`（提交后生成）；不能在自身 Git 提交中预写自身 SHA。
- `git fetch origin main && git ls-remote origin refs/heads/main`：最初只读核对远端为 `1ffef162f0464f4971b1cda506a9093afb9b6d33`；报告收尾再以 `git ls-remote` 读回同一远端 SHA。候选 HEAD 快进祖先关系检查退出 0。未调用 `push`/merge/rebase。先前主工作区 `git status --porcelain=v1` 为 `?? uv.lock`，主 HEAD 为 `1ffef162…`；其文件未被修改。最终状态及差异应以本轮收尾回执为准。
- 显式改动范围仅日期事件对账、F04 来源列及其用户明确要求的回归用例、审阅包和本报告；提交前后须检查 `git diff --cached --check`、非目标文件与 `git status --porcelain=v1`。本轮所有运行日志均保留首次失败和复测回执，不用第二次绿灯覆盖第一次红灯。

## 2. Phase 3E：生产全链、日期来源、指标

- 恢复历史**合成**案例的原始输入：`reports/solar-pv/phase7l-r2-full-cases/{industrial_rooftop,utility_scale_ground}/archived-d3-and-intervals.zip`，使用外部 `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-3e-d-r1-tools/restore_r2_input.py` 核对归档哈希、ZIP CRC 与 `expanded-file-manifest.json` 每个成员，输出分别到 `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-3e-d-r1-roof-20261117/`、`solar-3e-d-r1-ground-20261117/` 新目录。没有写回原始归档或 R2 原件。仅属 `SYNTHETIC_TEST_ONLY`。
- 生产入口真实调用 `wangbin_solar_pv.calculation.project_runner.run_project`（`PYTHONPATH=services/solar-pv-engine/src`），从各自隔离目录读取 `input.json`、`methods.json`、`budget.json`、`bundle/`、`terminal.json`、`terminal.txt`、`trading-fee-payment.json`；以 `BundleBudget` / `Workspace` / `Catalog` 调用。屋顶日志 `roof-python-r2.log`/`roof-python-r2.exit`：退出 0，`3B→3C→3D→3E` 均不是 reuse，耗时 529.0774322 秒；地面 `ground-python.log`/`.exit`：退出 0，四阶段均不是 reuse，耗时 656.4734576 秒。输出 `r1-roof-python/`、`r1-ground-python/`；两案 3D `financial-ledger.periods`、`annual` 均为 26 项（CONSTRUCTION + OPERATING_YEAR_1…25）。两案当前整体验收状态均 `PARTIAL`；日期 NPV 的实际 metric status 为 `BLOCKED_MISSING_INPUT`，reason 为 `BLOCKED_MISSING_DATED_CASH_EVENTS`，并非计算伪造。
- 普通项目 CLI 按实际 `python services/solar-pv-engine/solar_pv.py --help` 和 `... project --help` 参数调用，仍使用各自同一完整输入，`--workspace <各隔离目录> project --input input.json --methods methods.json --budget budget.json --bundle bundle --terminal-source terminal.json --terminal-document terminal.txt --trading-fee-payment-source trading-fee-payment.json --output r1-{roof,ground}-cli`。屋顶 `roof-cli.log`/`.exit` 退出 0，返回 `PARTIAL`、耗时 673.8321704 秒，canonical/result hash `ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f`；地面 `ground-cli.log`/`.exit` 退出 0、返回 `PARTIAL`、耗时 754.4675201 秒，canonical/result hash `69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138`。每案 CLI 与自己 Python 入口的结果哈希及四项项目指标一致；run ID 各不相同，不能混用两个运行的四件套。

| 本轮新合成生产运行 | Python `run_project` canonical.json 字节 SHA-256 / receipt.json SHA-256 | CLI canonical.json 字节 SHA-256 / receipt.json SHA-256 | 结果/input/source snapshot identity |
| --- | --- | --- | --- |
| 屋顶 | `8b1d650fc8be19d38ca7f1395c66ea657be5c2006086b500cae4e48f81c30a0e` / `ff14cc88b363131e15dcc9fc3c29467d50e23113f2e7a4aa8e84afb687ea8a26` | `b1a9f5b9b4872b38033c28b99c67653ed3e379380b646ee24ce17f4583cccb84` / `30e2c143acf3738dc9d3073a3500d1e70deff78fa0e9a8551a198f121a94838d` | `ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f` / `830e9f5edcc3b1aff1fe1cb758dbb99d19b78cecffc7a9c66fcd3f5278d17d73` / `27e8f594654940fb0eca40d750269b9daf2929bc7604f1dc8148a1d78a1a81f4` |
| 地面 | `eef87ad326354ca26bc0492eb3cd980d25b181b05038fb58295b7becbadaa47b` / `da7f82e8faa8cd71b503f0d1289dcc5541bf8a89dbd1b336179b77465b58a3a4` | `d5d00be0afc6ceccd7219f69075b38e757c066fb088d533564dc13e9008186bc` / `d005f37b29cc1374699b88f4b678f7e918abdb2972ccb8ede915c7e7e1e8ee19` | `69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138` / `7a0deebd88d70c110635f168ef5bd0a29f822a9b756f347ce1acc94e40a89933` / `4599a07c52537bcb07cef04a7bce028faaa5587df479e9c856b616713dd10a53` |

两案 `model_version=solar-pv-engine/0.3.0`；四个不同的 `run_id` 分别为屋顶 Python `7df9ba84-ac49-43f5-80bd-64f77cae0cdb`、屋顶 CLI `50511574-6f25-4b59-83c8-463a45cfd68d`、地面 Python `a84eff9d-b80b-49ff-bf6c-ec6235782e8e`、地面 CLI `09537915-70d2-49fb-9b9f-b81424aba726`。每次运行五项身份必须从**其自身** canonical 和 receipt 读取，绝不可仅因相同结果 hash 而拼接产物。

`validate_result(loads(canonical.json), Catalog())` 四份均返回有效；屋顶 `project_npv=670443.03157723156426540087957481923290686629`、`project_irr=0.2287232636150403342067960466010845266282558`、静态回收 `4.1755595560815796734933088477107346480077497`、动态 `5.2151811065288815123262051766206951282745555`；地面依次为 `260918.67724391645319481452274338300911840777`、`0.1115648000478395129864139789788168855011463`、`7.0263615715380309203472300904555703454009574`、`11.339888182363122260120288064168382581043518`。以上是合成输入上的项目口径，不是日期来源或真实工程结论。
- 新日期参数前置校验：屋顶 `--dated-event-carrier dated-invalid-r1.json` 而不带 CSV，`roof-dated-pair.log`/`.exit` 显示退出 2、`DATED_CASH_SOURCE_PAIR_REQUIRED`。屋顶真实生产 CLI 再同时传 `--generation r1-roof-python/3b --generation-hash d5747fc5215f2f2daaed0a9f23f84f9675c033f9b78d677ee3b80394191ff217 --dated-event-carrier dated-invalid-r1.json --dated-source-csv dated-invalid-r1.csv --output r1-roof-dated-invalid`，仍通过 3C/3D 后到达日期合同校验；`roof-dated-invalid.log`/`.exit` 显示退出 2、`DATED_CASH_SOURCE_SCHEMA`，证明带双参数的来源进入生产读取并被拒绝。两个文件都是本轮明确标记合成的无效反例，**不是日期来源正例**。
- 日期正例 `tests/solar-pv/test_phase3e_dated_cash_events.py::test_independent_synthetic_table_recalculates_dated_npv_without_annual_substitution` 是**三期独立合成 CSV**的来源字节/SHA/时间差与独立 Decimal 数值检验，且 `_record_sourced_dated_npv` 后 sealed 结果能被 `validate_result` 读取；不是 25 年生产入口的真实日期来源正例。两案旧 R2 的 25 年日期事件独立原始资料未提供；禁止从已算年度现金流复制/猜测年末日期，故两个 25 年“带日期来源的正例”与日期 CLI 正例仍 `BLOCKED_SOURCE_REQUIRED`。不能因普通项目路径算出年度 NPV/IRR 就称日期合同 25 年通过。
- 修复前 `precision-red.log`：新增大数正负抵消后遗留 `0.01` 未对账的回归，退出 1、`DID NOT RAISE ContractError`。修复在 `dated_cash_events.py` 逐期保留各事件金额，于局部 80+最大事件位数精度内合计，错误 `DATED_CASH_LEDGER_RECONCILIATION` 正确阻断；`precision-green.xml`：37 tests、0 failures、0 errors、0 skipped（`test_phase3e_dated_cash_events.py`、`test_phase3e_sourced_irr_controls.py`、`test_phase3e_irr_roots.py`、`test_phase3e_financial_metrics.py`，开发方组合定向，不等于全库）。独立 QA 的 32 项日期/IRR 及 1 项 F04 专项复测另列。独立 QA 的行为探针观察到非法金额、缺折现率、旧版本被拒，但不是分别命名的 pytest 回归用例；**专项用例覆盖缺口未关闭**。
- 指标区分：`project_npv`、项目 IRR、静态/动态回收是年度项目现金流口径；`dated_npv` 依赖独立日期现金及折现率，不能用年度期限代替；有多根时保留全根及搜索区间，不挑有利根。项目回报/经营现金/会计利润/股东现金/瞬时覆盖不可互换；未绑定的终期现金、费用支付、回收继续 `BLOCKED`。

## 3. Phase D：冻结身份、非正式渲染、F04、40 项用户审阅

| 合成案例（旧 R2） | `input_hash` | `result_hash` | 保留状态 |
| --- | --- | --- | --- |
| 工商业屋顶 | `656f694764e2afc1437cb6db603ecc23a9072fa5bea28495c9b036d540624556` | `398474aff972dee9f0a34bf85380a348bb27f8d4b102d7337ca0478ae0d34fe4` | 历史 canonical，不混入新日期来源 |
| 集中式地面 | `41ffe63a77738f275dc6fefa3ad9bed6f6ce953098924eb2d27d84d3e1e025d3` | `cd4fca1268dea37283a65680512774053d8e3008cd268375e7dd9f7e9abb2b46` | 同上 |

- 只读 `tests/fixtures/solar-pv/phase7l-r2-delivery/{industrial_rooftop,utility_scale_ground}/`，核对 manifest 五项身份与 canonical、F01/F03/F04 原始字节 SHA；独立从旧 F03「财务指标」的原始值/显示值与旧 F01 正文比较 `project_npv`、`project_irr`、`static_payback`、`dynamic_payback`，双案 16/16，脚本 `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-3e-d-r1-tools/verify_old_16.py`，正回执 `.runtime/solar-pv/SOLAR-PV-3E-D-INTEGRATION-R1/old-16-verification-r2.log`。保留首次该脚本按错误文本精度失败的 `old-16-verification.log`，只调整了**仓库外探针**显示精度，未调整 canonical/原件。
- 从受保护的 F01 **副本**在各自新目录通过 WPS KWPS COM 导出非正式 PDF，不改受保护 F02：屋顶 PDF SHA-256 `4846671169c9bff36cecc0f6d682d5c27df43e83637f86a6db18933066fce446`；地面 `fcdadcde36bb475af6d2884bf5c5c423afd1d8f065cea96a19b931b49c179296`。各 50 页；独立 QA 程序化检查未发现空文字页、U+FFFD 或基础文字 span 越界，抽查四项完整公式文本可搜索。**未做页面目视抽样**；全部公式语义/复制搜索、可编辑 OMML、逐页目视、TOC 页号和表格**尚未判 PASS**。旧六份局部 PDF 的替代字符历史缺陷仍保留，非正式新 PDF 不能替代正式 F02。渲染回执 `.runtime/solar-pv/SOLAR-PV-3E-D-INTEGRATION-R1/pdf-{industrial_rooftop,utility_scale_ground}/nonformal-render-receipt.json`；旧 F02 `BLOCKED`。
- `source_xlsx.py` 增加活动原子来源的原件/URL、定位/期间/发布日期/检索时间、地区与更新、原始单位、经济口径、公式 ID/版本、上游实例、转换规则、敏感级和缺失原因投影，保留原值、来源身份、审批状态。不补零、不升级来源审批。双案新 F04 草稿位于 `.runtime/solar-pv/SOLAR-PV-3E-D-INTEGRATION-R1/f04-final-{industrial_rooftop,utility_scale_ground}/r1-source-projection.xlsx`；屋顶 SHA `f3f1367c80bc0532176b31de0aaca7fcfb8bf513fd4636dbb9a7fb2064bba090`，622 活动记录；地面 SHA `eeee9cfe9de5d84eccd5d4b1d0c114a817e8001eac7293c4b18cfffa5bef141f`，576 活动记录；各值/来源对照 `missing=0,value_mismatch=0,provenance_mismatch=0`，回执 `f04-final-both.log`。两案都仍 `DRAFT_PARTIAL`，原始资料/审批/专业签审未替用户补齐；静态工作簿亦不等同表格软件重算。
- `docs/solar-pv/phase-d-ch08-ch10-ch16-user-review-pack-r1.md` 有两案各 CH08/10/16 共 40 条旧/新全文对照、节级引用来源和待办。它是 `HERMES_ASSISTED_UNVERIFIED` 的审阅组织材料，不是假装 WorkBuddy 宿主生成的本轮正文；40/40 `user_review=PENDING`、40/40 专业签审 `BLOCKED`。独立 QA 对最初文件 SHA `86b30dc1e316b6d29b8a4e538048f5392a779b83db98795a8681de086c552ed8` 发现 76 个数字字面量截断/漏列问题、涉及 28 条；经理只改清单未改正文，修订后文件 SHA-256 `15445afb4911ab658ef74ad97297e922f249469090d4179f5d0dc4e94803c10d`。针对这一新 SHA 的**另一次独立只读复核** `python3 -B -c '…'` 退出 0：40/40 清单与候选正文 token 完全对应，数字出现 129 次、去重清单项 119 个，缺失/误列各 0；千分位 79、百分比 16、零值 6、负值 3 项均在核对范围；可在 Hermes 委派回执 `deleg_52800d6a` 中追溯。此复核不替代逐数原始来源证明、用户接受或专业签审。任何接受/退回/资料补充均须用户逐项决定；完整四件套身份与正式 F02/人工审阅门禁保持未完成。

## 4. Windows Skill / Connector 集成分级

- 先查运行进程和真实安装路径，不以 `WorkBuddy.exe` 不在 PATH 推断客户端缺失。候选 `packages/skills/wangbin-solar-pv-prestudy`、`packages/connectors/wangbin-solar-pv-cli` 在源码仓库；已见运行中客户端，但已安装 Skill 的精确版本与源码候选绑定/Connector 实际托管 Python、wheel/依赖闭包未经本轮真实宿主回执核证。隔离目录中的 `python`/`PYTHONPATH` 项目运行只能证明本地 Python CLI，**不是**客户端 Skill→Connector 路由。本轮未在隔离 clone 生成/修改 dist 候选，也未以主工作区旧候选代替本轮安装证明。
- 未获安装、替换、上传新包授权；没有新一轮能独立核实的 WorkBuddy `prepare→真实宿主模型正文→accept→resume` / 产物回传原始调用回执。本轮没有伪造 `host_call_id`、预填正文或协议重放。宿主实测为 `NOT_TESTED / REQUIRES_INSTALLED_CANDIDATE_AND_AUTHORIZATION`，并非“客户端不存在”。
- `git check-ignore -v` 在主工作区确认两条历史候选路径均被 `dist/` 规则忽略；只读检查发现主工作区及隔离 clone 对应 `packages/{skills/wangbin-solar-pv-prestudy,connectors/wangbin-solar-pv-cli}/dist/` 目录当前均不存在。本轮未删除、创建或验证任何候选 ZIP，`DIST_LOCAL_VALID=BLOCKED / CANDIDATE_NOT_FOUND`；不能用历史文档中的候选名推断本机包仍有效或已安装。

## 5. 独立 QA、卫生及保留的失败

| 项 | 原始回执/命令 | 结果及限定 |
| --- | --- | --- |
| 日期精度首次反例 | `precision-red.log`，单用例 | 退出 1、1 failed；已由 `63ddb5c5` 修复，保留红灯 |
| 首次屋顶生产命令环境 | `roof-python.log`、`roof-python.exit` | 退出 1，shell 仅设 `W=...` 未 export，Python `KeyError: 'W'`；补 `export W=...` 后 `roof-python-r2` 退出 0；环境错误不是财务计算失败 |
| 日期+IRR+财务组合 | `precision-green.xml`，`pytest` 四文件 | 退出 0，37/37、failed=0、skipped=0；开发方组合，**非独立 QA** |
| F04 定向 | `f04-final-r2.*` 和 `f04-final-both.log` | 退出 0，记录计数；曾有第一次读取校验失败，保留早期日志，不抹除 |
| 旧双案 16 数字 | `old-16-verification-r2.log` | 退出 0，16/16；只读旧文件，不代表正式 PDF |
| 真实生产双案 | `roof-python-r2.exit`、`ground-python.exit` | 均退出 0，25 年生产链回读，项目最终状态 PARTIAL |
| 普通项目 CLI | `roof-cli.exit`、`ground-cli.exit` | 双案均退出 0、状态 PARTIAL；日期两源无效合同 CLI 退出 2、`DATED_CASH_SOURCE_SCHEMA`（预期负例） |
| 独立 QA 日期/IRR 专项 | `.../solar-3e-d-r1-independent-qa1-20261117/date.exit`=`0`，`date.xml` SHA-256 `2d8529a804cbd6400ca1a2b0f30db304f8c658daf4840553528416abe183d60c`；`python -m pytest -q -p no:cacheprovider --basetemp=<QA>/date-basetemp --junitxml=<QA>/date.xml tests/solar-pv/test_phase3e_dated_cash_events.py tests/solar-pv/test_phase3e_sourced_irr_controls.py tests/solar-pv/test_phase3e_irr_roots.py` | XML 自报与逐例计数一致：32 tests、0 failures、0 errors、0 skipped；对应候选代码 HEAD `7fe9c0e7…`，不代表 Phase 3B–3E 全套通过 |
| 独立 QA F04 专项 | `.../solar-3e-d-r1-independent-qa1-20261117/xlsx.exit`=`0`，`xlsx.xml` SHA-256 `b01f7d3839679a03b258318320ca41111376fdf051877eb6c4f0b9fe55219c27` | XML 自报与逐例计数一致：1 test、0 failures、0 errors、0 skipped；仅 F04 专项 |
| 独立 QA 扩展回归 | `.../solar-3e-d-r1-independent-qa1-20261117/regression.log`、`fast.log` | 独立 QA 报告两轮运行分别约 285/140 秒、监督限时退出 124；本目录无相应 `.exit` 和最终 JUnit XML，日志只有进度，逐例数**未知**；状态 `TIMEOUT / INCOMPLETE / NOT_PASSED`，不得据进度推算 PASS |
| 独立 QA Phase D 原审阅包 | `.../solar-3e-d-r1-independent-qa2-20261117/audit-result.json` SHA-256 `62d09e189d6cdaafae3db425961639b4f0f205ab8ac38eb5c0dae1df5d35e516` | 原 SHA 文件 40 行审阅状态吻合、双案历史身份及 16 项显示对照；发现数字清单 76 个问题。随后清单修订的自检（40/40 匹配）与独立 QA 原结果分开，后者**不覆盖**新文件 |
| 独立 QA Phase D 修订清单 | 委派 `deleg_52800d6a`，当前文件 SHA-256 `15445afb4911ab658ef74ad97297e922f249469090d4179f5d0dc4e94803c10d`；`python3 -B -c '…'`、`sha256sum` 均退出 0 | 独立逐节对照 40/40；119 个唯一清单 token 无缺漏/误列；40 `PENDING` / 40 `BLOCKED`，非专业签收 |

**文件保护与写入边界：** 只允许新目录恢复输入及仓库忽略的 `.runtime/solar-pv/SOLAR-PV-3E-D-INTEGRATION-R1/` 新候选；修订审阅包后重新执行 `python tooling/solar_pv_workspace_hygiene.py --check` 退出 0（识别 1296 个已跟踪文件、两份待提交文档；检查本身不判历史日志可删除）。最后阶段还须检查主工作区 `?? uv.lock`、隔离仓库工作树、旧 dist/historical 文件哈希与最终提交。无授权不执行任何 `--clean`。历史产品数据未经用户审定、正文未经 40 项人工签审、PDF 未签证、WorkBuddy 宿主不可验证，整体不能 PASS。

## 6. 门禁与下一轮解除条件

| 门禁 | 状态 | 原因 / 所需行动 |
| --- | --- | --- |
| 3B→3C→3D→3E 双案无日期来源的合成生产入口 | `PARTIAL` | 真执行；缺日期原始资料与正式审批，不能视为真实工程 |
| 两案普通 CLI | `PASS_SCOPE_LIMITED` | 双案合成生产 CLI 真实退出 0 且四个项目指标/结果 hash 与各自 Python 入口相符；整体仍 PARTIAL，不抬真实工程门禁 |
| 独立 QA 定向测试与扩展回归 | `PARTIAL / INCOMPLETE` | 精确 JUnit 32+1 项专项通过；两次扩展回归 124 超时且无终结 XML，不能计全套通过 |
| 双案 25 年独立日期来源正例、CLI 正例 | `BLOCKED_SOURCE_REQUIRED` | 分别提供原始事件字节、时间、合同、来源快照与财务账簿逐期一致的独立来源；不得由年末现金流反推 |
| 缺源及恶意输入 | `PARTIAL` | 前置双参数缺失及双参数无效合同均被 CLI 真实拒绝；非法金额、日期折现率缺失、旧合同版本缺分别命名的 pytest 回归用例，探针拒绝不等于回归覆盖 |
| R2 五项身份及 16 个数字 | `PASS_SCOPE_LIMITED` | 旧合成冻结文件只读核对，不代表新日期计算 |
| 非正式 PDF 字符/数字基础探针 | `PARTIAL` | 两案 WPS 原件副本；全页目视、公式语义/复制搜索、专业签审未完成，旧 F02 仍 `BLOCKED` |
| F04 源映射投影 | `PARTIAL` | 自动追溯修复，真实资料/来源审批/税费及正式 F04 门禁未齐 |
| CH08/10/16 共 40 项 | `USER_REVIEW_REQUIRED` | 审阅包准备；须用户逐条接受/退回/要求资料，不能自动签审 |
| WorkBuddy Skill / Connector / 宿主全链 | `NOT_TESTED` | 核实安装资产版本/环境，获得新增安装/模型调用授权及真实宿主回执后重试 |
| 本机 Skill / Connector `dist` 候选有效性 | `BLOCKED / CANDIDATE_NOT_FOUND` | 主工作区与隔离 clone 指定候选 `dist` 目录均缺；Git 忽略规则存在但无 ZIP 可读回。不得覆盖或伪称旧包有效 |
| Phase E/F/G、正式四件套、发布 | `BLOCKED_NOT_AUTHORIZED` | 当前轮未授权，不能通过合成测试推断发布 |

**明确请求（按优先级）：** P0 为双案独立日期现金事件原始 CSV/JSON、独立日计数/折现率/根域、上游账簿与来源审批，以及 40 条用户审阅；P0 为正式 PDF 所需字体/可编辑公式复制搜索及逐页专业/视觉签审；P1 为 WorkBuddy 精确安装/运行环境与允许的真实宿主模型闭环授权。各阻断都需保持原合同，不应由 Hermes 补造数据或冒名替用户决定。新提交的普通 push 必须另获本轮明确授权；将来获授权后先再 `git ls-remote origin refs/heads/main`、验证快进及保护规则，方可从**本隔离目录**执行 `git push origin main`，绝不自动推送。
