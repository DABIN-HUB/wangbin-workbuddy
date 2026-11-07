# Q06 FIX-5 · 需求及判定冻结（开发前）

`product_id=wangbin-tender-analyzer`；分析卡 `t_fdae5931`；依赖开发卡 `t_f523f963`；唯一工作树 `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`，分支 `skill/tender-response-check`，分析时 HEAD `a0a8b4712e8e8d1b98453d405bfe7ed4920aa567`；0.2.9 业务开发提交 `14504f390c09731841f9e8439d36b5efa1025a19`。此页补强原 `requirements.md` BID-01–08 / BID-F02–F04、`input-output-contract.md` 四维和 AUDIT-R1 节、`acceptance-cases.md` 及 `acceptance-fix3-six-failures.md`；原合同不改写。用户仍是投标团队提交前复核人员，业务价值是将逐要求回应的**当前事实状态**和实际材料**存在/正文证明力**分别归属到有源位置的义务，避免把“提及”当“满足”。不是改名、补关键词或推断真实证照效力。

## 证据冻结与差异

原独立 QA `qa-fix4-029-independent-report.md`（SHA-256 `1c5dfb76297b5515c62c8a745cf7adbad014606e701e4d177ba8f1045c13742b`）、原脚本 `qa-fix4-029-independent.py`（`0a06bdbb1d76ae1276222c5b72f2fe73adaa770f8c151709cf55dfc271078503`）、原 JSON `qa-fix4-029-independent-results.json`（`0e99b0fb53d47e80eeb4d4efd8a1d0356ba25ddaefed6e25ba93759bee94421d`）共同冻结原 53/53、FIX-3 13/13、FIX-4 13/16；82 案原 `cases[].input_sha/expected/actual/issues` 均保持原字节、不删不改。0.2.9 ZIP `dist/wangbin-tender-analyzer-0.2.9-skill-candidate.zip` SHA-256 `d5ed3fd8e06c92046dee6ce6db01a53120be65883d3e6e807b8e3f408fde83ce`，其 `scripts/check_response.py` 与本树 `packages/skills/wangbin-tender-analyzer/scripts/check_response.py` 实测 SHA-256 `479284e406316ff9c407cbbe6739b0e1c82af973338a8548457cc1887e850df0`，不是以 0.2.7 源码猜测新行为。原 53 输入基准 `qa-audit-r1-new-027-fixtures-outputs.zip` SHA-256 `a791979b9e6d83b36b8e533cde7f65ab1ac3267ced9a909512827413dbc3c986`；FIX-3/4 原输入哈希由原 QA JSON 各案和原独立脚本先行预期冻结。H06/H10/H12 均 CLI exit 0、XLSX/MD 生成，却业务 FAIL；具体逐案证据见 `fix5-acceptance-cases.md`。0.2.10 ZIP/sidecar/manifest 分别开工检查为 FREE，开发须再核对，不能覆写旧包。

## MVP 机制规则（必须连同正反/歧义对照测试）

| 键 | 可核查判据 | 原合同追溯 |
|---|---|---|
| F5-01 义务和回应绑定 | 先取招标义务对象/条件/时点及 `tender.txt:行`，再以编号+语境绑定响应 `response.md:行`。多义务、多候选或代词不明保留候选，绝不跨行借肯定、否定或材料；同一要求冲突保留双向来源。 | BID-01–03、BID-F02、FIX-3 Q05/Q10 |
| F5-02 当前事实 | 对同一对象分别规范化 `CONFIRMED_AVAILABLE`（当前明确可用）、`CONFIRMED_UNAVAILABLE`（当前明确不可用/未启用）、`CONDITIONAL_OR_FUTURE`（仅将来/有前提）、`UNKNOWN`（是否投用无法确认）、`CONFLICT`（同对象同一时点正反并存）；记录来源、否定作用域、时态。未知不等于不可用，也不等于可用；未知只能待确认，不能由词交集/“实际”/“投用”回升覆盖；明确否定在无相反证据时是不充分的确定缺口；无条件明确肯定不得一律降未知。若明确将来且明确当前不足，保留两个事实，当前不满足；仅有条件而无当前状态不得推定当前不可用或可用，列条件及待确认/有依据的不足。 | BID-F02、BID-03/06、FIX-3 Q02/Q03、FIX-4 Z01–Z06/H01–H08 |
| F5-03 材料分层 | 独立记录“用户实际显式提交可读文件”与“正文是否支持对应义务”。文件不存在→限定给定范围的未提供/未核验；仅目录→仅目录登记/未核验；可读仅标题或封面且**明确**无正文/登记内容→已提供/不支持，条件可能不充分且确定文本缺口；部分正文但无法核实证明力→已提供/待确认，原因与行位置；匹配对象的明确正文正证→可作有限文本支持；明确申请/未颁发/不是证明→不支持。标题单词、文件名、同主题词与空条件不得自动支持。明确缺正文只表示**此文件**不能证明，绝不宣告企业未持证。 | BID-03/04、BID-F03/F04、FIX-3 Q06/Q07、FIX-4 Z07–Z13/H09–H16 |
| F5-04 冲突/呈现 | 同对象同时间或同文件正反证冲突时保留各原句位置、待确认冲突，不凭首条或单一负词/正词决定；不同对象不能互借。确定缺口必须同时进入矩阵/附件核对（适用时）/概览/MD 确定需补和未覆盖；真正未知只在待确认事项及 MD 人工确认，不混称确定缺失；四维分别计数守恒。 | BID-06/07、input-output-contract.md 输出/状态、acceptance-cases.md 公共断言 |

不做：修改原 53+13+16 输入或 expected、修改业务源码、旧入口或任何旧 QA 证据；本分析不运行新版/发布/上传/推送/安装，不保证法律效力、执照真实、投标结果、平台运行。开发在动代码前由授权者单独限范围提交这三份 `fix5-*` 合同；新实现与一次独立 QA 各由依赖角色履行。本阶段新版业务 PASS、工厂 validate/test/package/verify、宿主/许可/人工差异/平台门禁均 `NOT_TESTED`；既有 0.2.9 QA 仍为 FAIL。
