# Q06 FIX-5 / 0.2.10 独立 ZIP 一次验收：LOCAL_QA_FAIL

- product_id `wangbin-tender-analyzer`；task_id `t_2951015b`；workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch `skill/tender-response-check`；base/source commit `a215165a8b7cbd80e9d568b4ed61fed4e8c16ca2`；QA 变体先行冻结 commit `fdcaef372e103efc96677b583d9d3f7b11bc4270`。只运行一次 `python docs/products/wangbin-tender-analyzer/qa-fix5-0210-independent.py`；脚本 exit 0 **不等于业务 PASS**。
- 精确被测 ZIP `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check/dist/wangbin-tender-analyzer-0.2.10-skill-candidate.zip`，SHA-256 `d11c09bff946ad128ee802d2c49d4e349af9c5393c48de7938ea69ffb53ca0e7`。sidecar、manifest `id/version/sha256`、目录版本及 SKILL.md frontmatter 一致；11 个唯一安全成员顺序与 manifest 一致，逐个 SHA-256/size/源树字节一致，ZipFile.testzip() 无坏成员；CLI 仅用新建 `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_fix5_independent_0210_once/extract/wangbin-tender-analyzer/scripts/check_response.py`，每次调用移除 `PYTHONPATH`。原 0.2.7/0.2.8/0.2.9 SHA 分别为 `12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09` / `8eddf4883c35da2eb645ef97acaf1b6f8d77e8384b01e4256382d26b1ea282be` / `d5ed3fd8e06c92046dee6ce6db01a53120be65883d3e6e807b8e3f408fde83ce`，未改。旧独立 JSON/脚本 SHA 分别 `0e99b0fb53d47e80eeb4d4efd8a1d0356ba25ddaefed6e25ba93759bee94421d` / `0a06bdbb1d76ae1276222c5b72f2fe73adaa770f8c151709cf55dfc271078503`；旧 82 案 expected/input_sha 经本次读回逐项相同。

## 分组结果及判据

| 组 | 实际通过/总数 | 失败 |
|---|---:|---|
| 原冻结 53（原输入字节来自证据 ZIP） | 53/53 | 0 |
| FIX-3 原独立 Z01–Z13 | 13/13 | 0 |
| FIX-4 原独立 H01–H16 | 16/16 | 0；旧 H06/H10/H12 均关闭 |
| 本次预提交独立 F01–F12 | **7/12** | **5：F01/F02/F04/F05/F08** |
| 错误输入及正控 | 6/6 | 0；错误 5 项 exit 2、正控 exit 0 |
| 旧 analyze_tender.py JSON 快照 | 1/1 | 0 |

原 53+13+16 与新增每案实际生成五表（核查概览/要求响应矩阵/附件核对/补遗与版本/待确认事项）及 Markdown；脚本逐维对四状态、行数、概览计数守恒、附件绑定、来源和缺口/MD 分区、公式单元格，另检查跨对象响应行、证据行与旧 V09 补遗。每案 input SHA/expected/actual/stdout/stderr/exit、实际五表所有行、MD 全文、cwd/argv 与 XLSX+MD 路径及 SHA 见 `qa-fix5-0210-independent-results.json`；`qa-fix5-0210-fresh-predeclared.json` 保存 CLI 前生成的新输入 SHA/期望。只读 `python docs/products/wangbin-tender-analyzer/qa-fix5-0210-audit-evidence.py` 复核旧82预期与输入、94案所有输入及产物哈希并输出重点案。**上述结构守恒不抵消下述业务错误。**

## 已关闭旧三缺陷（原案实物重验）

- H06，回应 `自动备份的实际投用情况目前无法确认`：实际 `已定位/待确认/不适用/不适用`，待确认表与 MD 人工确认有 `tender.txt:1`、`response.md:1`，MD 已覆盖为空；非确定未部署。
- H10：真实可读 `营业执照.txt:2` 明言只有标题、没有证照正文或登记内容；实际 `已定位/可能不充分/已提供（可读文本）/不支持（文本层面）`，矩阵和附件行保留反证位置、确定缺口；MD 确定需补/未覆盖，不推断现实企业未持照。
- H12：真实可读 `营业执照.txt:1` 明言不完整、缺少正文、仅有封面；同上四维/缺口/MD，未把已提供降为未提供。

## 五项新阻断：原输入 → 预期 → 实际（均 CLI exit 0）

共同功能招标 `tender.txt:1` 为 `1. 必须支持自动备份。`（除 F05 的第二义务外），每案另有真实 `response.md`；四维按响应存在/条件覆盖/附件实际提供/内容支持；原输入/输出哈希逐项见 JSON，输入及真实失败五表 XLSX/MD 在 `qa-fix5-0210-failures/<ID>/`。用 `qa-fix5-0210-independent.py` 的 `--tender/--mode check/--response/--output-dir/--project` 及适用时的 `--evidence-file` 可从原材料复现；不要重跑此已限一次的 QA 卡。

| ID | 原始响应/证据关键行 | 预期四维 | 实际四维；额外错误 |
|---|---|---|---|
| F01-unknown-operability | `response.md:1` 自动备份当前是否可正常使用，尚无核实结论。 | 已定位/待确认/不适用/不适用 | 已定位/**已覆盖**/不适用/不适用；待确认表空、MD 错列已覆盖 |
| F02-current-no-service | `response.md:1` 自动备份现阶段不能实际运行，计划后续启用。 | 已定位/可能不充分/不适用/不适用 | 已定位/**已覆盖**/不适用/不适用；确定缺口空，MD 已覆盖 |
| F04-same-object-conflict | `response.md:1` 自动备份当前已经正常使用；`:2` 自动备份当前不能实际运行。 | 已定位/待确认/不适用/不适用；两行同对象冲突应保留 | 已定位/**已覆盖**/不适用/不适用；虽位置同时列两行，摘录与 MD 只呈现肯定句，待确认表空 |
| F05-two-object-separation | `tender.txt:1` 自动备份、`:2` 离线查询；`response.md:1` 备份当前已正常使用、`:2` 离线查询当前不能实际运行。 | 行1 已定位/已覆盖/不适用/不适用；行2 已定位/**可能不充分**/不适用/不适用 | 行1 正确；行2 **已覆盖**且无缺口，MD 将两个对象均列已覆盖；两行响应位置正确但负现况误判 |
| F08-explicit-no-body | 招标提供营业执照；回应见附件；实物 `营业执照.txt:1` 营业执照材料封面、`:2` 证照正文未附，当前仅有封面页。 | 已定位/可能不充分/已提供（可读文本）/不支持（文本层面）；确切证据行 2、需补正文 | 已定位/**待确认**/已提供（可读文本）/**待确认**；虽然证据位置含行2，缺口空，附件行待确认，MD 误列人工确认不列确定需补 |

独立正控 F03 当前可用、F10 有同对象正文均通过；F07 只有标题但无明示缺正文仍待确认，F09 部分摘要证明力不明仍待确认，F11 同文件正反冲突待确认，F06 无文件仍未提供，F12 乙类正证不得借给甲类；不能以“全待确认”伪过。这五项证明 FIX-5 对同义未知、现况否定和明确无正文仍不稳健，尤其 F04 顺序选取肯定句导致虚假覆盖。没有据此断言法律效力或真实企业资质。

**门禁结论：LOCAL_QA_FAIL。** 新 FAIL 实物完整保留，原 0.2.9 FAIL 证据、冻结预期未改；不得复制 `qa-passed`、不得启动 FIX-6/第二轮 QA、不得建议经理更新六产品合格候选清单。本轮未 push、未上传/试传、未提审或发布；WorkBuddy 平台运行及审核、许可证及分发权利、人工相似性、物理 symlink 均 `NOT_TESTED`/`NOT_VERIFIED`。跨文件同一材料正反归属未覆盖为充分法律证明，保留残余风险。