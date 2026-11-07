# Q06 FIX-4 独立 ZIP 验收：FAIL（53/53 + FIX-3 13/13 + 新变体 13/16）

- product_id `wangbin-tender-analyzer`；task_id `t_c1690b2a`；workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch `skill/tender-response-check`；tested source commit `14504f390c09731841f9e8439d36b5efa1025a19`，base commit `a279517598a36765441fe98e596e3554e4e5d764`。唯一一次实际业务验收命令 `python docs/products/wangbin-tender-analyzer/qa-fix4-029-independent.py`：脚本 exit 0，业务 **FAIL**，不可写 LOCAL_QA_PASS。业务来源为新 ZIP 干净解压在 wb-quality profile scratch，去掉 `PYTHONPATH`；并非开发树执行或开发者 PRE-QA。
- 受测精确 ZIP `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check/dist/wangbin-tender-analyzer-0.2.9-skill-candidate.zip` SHA-256 `d5ed3fd8e06c92046dee6ce6db01a53120be65883d3e6e807b8e3f408fde83ce`。0.2.8 历史 SHA `8eddf4883c35da2eb645ef97acaf1b6f8d77e8384b01e4256382d26b1ea282be` 未变；0.2.7 SHA `12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09` 未变。冻结53输入的 0.2.7 原证据 ZIP SHA `a791979b9e6d83b36b8e533cde7f65ab1ac3267ced9a909512827413dbc3c986`。11成员 ZIP CRC/testzip、唯一路径安全、manifest 长度和逐成员 SHA、源码同路径字节、sidecar、frontmatter 0.2.9、catalog 版本均通过；仅说明包完整，**不说明业务通过**。
- 原53逐字节冻结输入/原预期 53/53 PASS，FIX-3 原13项原输入/原预期 13/13 PASS，Z04 由已覆盖变待确认、Z10 由已覆盖/支持变待确认/待确认；新增独立16案仅 13/16 PASS，H06、H10、H12 FAIL。错误探针 6/6（五项错误 exit2 + 正控 exit0）；旧 `analyze_tender.py` 单文件 JSON 与旧 ZIP 快照一致；正式补遗 V09 在原53中通过。每案真正 CLI exit、cwd/argv、stdout/stderr、四维预期/实际、五工作表全部行、MD 全文、源/输出绝对路径及 SHA 见 `qa-fix4-029-independent-results.json`；可重复运行输入与预期见 `qa-fix4-029-independent.py`，三个失败的输入及真实 XLSX/MD 固化在 `qa-fix4-029-failures/`。五表顺序、矩阵行数、状态分类计数守恒、来源/响应位置、附件绑定、缺口/MD 分段、无公式注入由脚本逐案核查；业务 FAIL 不能由这些结构检查或 CLI exit0 抵消。

## 三个阻断案例：可复现输入、预期、实际

共同招标/回应除 H06 外：`tender.txt` 为 `1. 必须提供营业执照。`，`response.md` 为 `1. 营业执照见附件。`，以材料 `营业执照.txt` 为 `--evidence-file`。执行命令在原始 JSON `argv`，即解压版 `scripts/check_response.py --tender <case>/tender.txt --mode check --response <case>/response.md --output-dir <case>/out --project 虚构核验<id> [--evidence-file <case>/营业执照.txt]`；三个案例均 **CLI exit 0**、生成真实 XLSX+MD。四维按响应存在/条件覆盖/附件实际提供/内容支持排列。

| ID | 有差异的原始输入 | 预期四维 | 实际四维 | 额外错误 |
|---|---|---|---|---|
| H06-unknown-synonym | 招标 `1. 必须支持自动备份。`；回应 `1. 自动备份的实际投用情况目前无法确认。` | 已定位 / 待确认 / 不适用 / 不适用 | 已定位 / **已覆盖（文本层面）** / 不适用 / 不适用 | 缺口空，待确认表空，MD 把未知投用列为已覆盖 |
| H10-license-title-only | 材料两行：`营业执照`；`本文件仅有标题，没有证照正文或登记内容。` | 已定位 / 可能不充分 / 已提供（可读文本） / 不支持（文本层面） | 已定位 / **待确认** / 已提供（可读文本） / **待确认** | 明确“没有正文”未进确定缺口；待确认表误替代负证 |
| H12-license-insufficient | 材料：`营业执照材料不完整，缺少正文，仅有封面。` | 已定位 / 可能不充分 / 已提供（可读文本） / 不支持（文本层面） | 已定位 / **待确认** / 已提供（可读文本） / **待确认** | 明确“缺少正文”未进确定缺口 |

三个案例的要求来源均为 `tender.txt:1`、响应位置 `response.md:1`；H10 实际证据位置 `营业执照.txt:1；营业执照.txt:2`，H12 `营业执照.txt:1`。附件核对表绑定实际材料且错误标 `待确认`，而非材料丢失。根因定位：功能状态歧义同义句“实际投用情况目前无法确认”未被未知状态分支覆盖，回应被正向覆盖；材料正文“没有证照正文”“缺少正文”未被确定缺失/负证分支覆盖，而降为不确定。已提供可读文本不等于文本支持，历史 Z04/Z10 固定字面修复不足以涵盖同义与缺失正文。上述为文本层判定缺陷，不推断真实营业执照法律效力。

- 三案源输入、预期、实际、CLI 返回码、输出绝对路径/哈希由原始 JSON 自证；QA 失败输出文件均在 `docs/products/wangbin-tender-analyzer/qa-fix4-029-failures/<id>/` 单独留存，历史 FIX-3 证据及 0.2.7/0.2.8 候选均未修改。
- 停止；不另开 FIX-5 或第二次 QA，不复制 qa-passed，不 push、不上传 WorkBuddy、不提审/发布。平台宿主运行/审核 NOT_TESTED；许可证/分发权利 NOT_VERIFIED；物理 symlink NOT_TESTED。向经理交付 **LOCAL_QA_FAIL** 与真实证据，由经理终验。
