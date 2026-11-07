# Q06 FIX-3 0.2.8 ZIP 独立验收：FAIL（原53/53；新变体11/13）

- `product_id=wangbin-tender-analyzer`；`task_id=t_03cbcafd`；workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch `skill/tender-response-check`；QA 基线 commit `99d8ce34072fe3751be30f62c526cf0a7ddbfa70`。本结论独立于开发自测，**不放行业务**：两项新增独立歧义反例误升已覆盖/支持。**STOP；NO FIX-4；NO PUSH。**
- 新包 `dist/wangbin-tender-analyzer-0.2.8-skill-candidate.zip` SHA-256 `8eddf4883c35da2eb645ef97acaf1b6f8d77e8384b01e4256382d26b1ea282be`，旧包 0.2.7 SHA-256 `12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09` 不变；原输入证据 ZIP SHA-256 `a791979b9e6d83b36b8e533cde7f65ab1ac3267ced9a909512827413dbc3c986`。包内 11 文件，全成员对 manifest SHA/长度、源码同路径字节相等，CRC/testzip、相对路径、无重复/敏感路径、sidecar、SKILL frontmatter 0.2.8、catalog 0.2.8 已核；仅本地完整性。
- 独立脚本 `python docs/products/wangbin-tender-analyzer/qa-fix3-028-independent.py`（无 `PYTHONPATH`，从 0.2.8 ZIP 干净解压，原 53 原始输入逐字节取原冻结证据 ZIP、原 JSON expected 不变）；首次 QA 探针自身将 JSON 四维列表误当多行、并将响应位置误查来源（无业务失败定论），更正探针后在全新 profile scratch `q06_fix3_independent_028_r2` 重跑，并以最终脚本在全新 `q06_fix3_independent_028_r3` 再复核同结论。首次探针发现独立歧义反例并在重跑前将 Z10 输入明确为“是否构成正式执照尚待核实”；历史原预期、ZIP、业务代码均未改。记录当前逐案原始实际结果及命令、cwd、退出码、stdout/stderr、输入输出 SHA 于 `qa-fix3-028-independent-results.json`。
- 原 53：**53/53** 原四维与五表行数/概览逐状态计数、MD 已覆盖/缺口、部分附件关联、无公式、真实 XLSX/MD 通过；六项旧失败 Q02/Q03/Q05/Q06/Q07/Q10 均在原件上关闭。新变体：**11/13**，Z04/Z10 两项 FAIL（精确见下）。旧 JSON CLI 与旧 ZIP 内 expected 结构快照相同；prepare、check、正式补遗（原 V09）均实际执行；错误输入 5 项预期 exit 2 / 稳定错误码 / 无伪输出，正控 exit 0 / 两文件。
- **门禁：本地 L3 QA FAIL**。宿主自然语言多轮与 WorkBuddy 安装/平台审核 NOT_TESTED；许可证/分发权利 NOT_VERIFIED/BLOCKED；Windows 物理 symlink NOT_TESTED；企业现实资质真实性和政府核发 NOT_TESTED。0.2.8 不应作为已验收候选发布/上传。

## 六旧失败的前后对比（四维顺序：响应/条件/附件/内容）

| 案例 | 原 0.2.7 四维 | 本次 0.2.8 四维 | 结果 |
|---|---|---|---|
| Q02-not-available-yet | [['已定位', '已覆盖（文本层面）', '不适用', '不适用']] | [['已定位', '可能不充分', '不适用', '不适用']] | PASS |
| Q03-proposed-future | [['已定位', '已覆盖（文本层面）', '不适用', '不适用']] | [['已定位', '可能不充分', '不适用', '不适用']] | PASS |
| Q05-no-cross-subject | [['已定位', '已覆盖（文本层面）', '不适用', '不适用'], ['已定位', '已覆盖（文本层面）', '不适用', '不适用']] | [['已定位', '可能不充分', '不适用', '不适用'], ['已定位', '已覆盖（文本层面）', '不适用', '不适用']] | PASS |
| Q06-evidence-not-issued | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] | PASS |
| Q07-evidence-empty-wrapper | [['已定位', '待确认', '已提供（可读文本）', '待确认']] | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] | PASS |
| Q10-cross-object-negative | [['已定位', '可能不充分', '未提供（限已提供材料）', '未核验'], ['已定位', '待确认', '已提供（可读文本）', '待确认']] | [['已定位', '可能不充分', '未提供（限已提供材料）', '未核验'], ['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] | PASS |

## 新增失败：精确复现

两项均为 CLI exit 0 且生成五表，不能以退出码当业务 PASS；目标不要求认证现实证件真伪，只要求不要把明确“不知道”变成确定已满足。

### Z04-unknown-status

- 招标 `tender.txt`: 1. 必须支持自动备份。；回应 `response.md`: 1. 自动备份功能是否已经上线尚待核实。
- 预期（四维）：`['已定位', '待确认', '不适用', '不适用']`；实际：`['已定位', '已覆盖（文本层面）', '不适用', '不适用']`；实测差异：`['1:1:1 条件覆盖状态: expected 待确认, actual 已覆盖（文本层面）']`。
- `缺口`：``；`来源`：`tender.txt:1`；`响应位置`：`response.md:1`；`证据位置`：``。
- 原输入 SHA-256：`{'response.md': '1b68b425af862e3fd2c7dfa85f4807d8994da2369b9e178bd39b77acdbd09ef5', 'tender.txt': 'cbf4dd72c1e1f9f768a4e4c5d56ad909491a2e6ab2a1cf0975be27dedaa7f9ea'}`；输出 SHA-256：`{'虚构核验Z04-unknown-status-投标响应检查.xlsx': 'd5bc5cca3cb7d279eb762dcae4f6decdf57cea67035eac8bbcd12027af56e644', '虚构核验Z04-unknown-status-提交前核对清单.md': '32387097b2ddbc1d7a4ca63da009845d3c62dfb667d788514c328c7fa279df28'}`。
- 执行 `C:\Users\wangbin\AppData\Local\hermes\installs\dff2a7c1aa1d2670\environments\3d191065334546e08496a64b86fa12ed\venv\Scripts\python.exe C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\extract\wangbin-tender-analyzer\scripts\check_response.py --tender C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\cases\Z04-unknown-status\tender.txt --mode check --response C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\cases\Z04-unknown-status\response.md --output-dir C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\cases\Z04-unknown-status\out --project 虚构核验Z04-unknown-status`；cwd `C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\cases\Z04-unknown-status`；exit `0`；stdout `CREATED 虚构核验Z04-unknown-status-投标响应检查.xlsx 虚构核验Z04-unknown-status-提交前核对清单.md<br>`；stderr ``。
- 待确认表：``；附件核对表：``；MD 已覆盖分段：`<br>- 1:1:1 (原编号 1；tender.txt:1；响应 response.md:1)：已定位。四维：已定位 / 已覆盖（文本层面） / 不适用 / 不适用。<br><br>`。
- 修复预期仅为下次经理决策参考，本卡不启动返工：未知是否上线不能推出已上线；仅登记信息且“是否构成正式营业执照尚待核实”不应推出材料支持或条件已覆盖。

### Z10-license-uncertain

- 招标 `tender.txt`: 1. 必须提供营业执照。；回应 `response.md`: 1. 营业执照见附件。
- 实际材料 `营业执照.txt`: 本件仅为登记信息，是否构成正式营业执照尚待核实。
- 预期（四维）：`['已定位', '待确认', '已提供（可读文本）', '待确认']`；实际：`['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']`；实测差异：`['1:1:1 条件覆盖状态: expected 待确认, actual 已覆盖（文本层面）', '1:1:1 内容支持状态: expected 待确认, actual 支持（文本层面）']`。
- `缺口`：``；`来源`：`tender.txt:1`；`响应位置`：`response.md:1`；`证据位置`：`营业执照.txt:1`。
- 原输入 SHA-256：`{'response.md': '3e46c6db2bb24a72db41847c5f5087d56d8be975e9a8e2727e4a1ae6eeeed898', 'tender.txt': 'e15882d7f3447a02d456f4f078005fc5a4146b83cfbbdba4ca9077455bb1a00f', '营业执照.txt': 'fa951d262d31cef67a34817b29a2d2c4c3b92c9cc876acdc07af6cba4d1ce9a6'}`；输出 SHA-256：`{'虚构核验Z10-license-uncertain-投标响应检查.xlsx': '6985ba919a4303653ef5bfe0493785f1ff0ea639979ff805aa7bef231403ac32', '虚构核验Z10-license-uncertain-提交前核对清单.md': '7a1e7ab43efe21a099a17536d7ede98dc8852506842b42c16d933b60b22135cf'}`。
- 执行 `C:\Users\wangbin\AppData\Local\hermes\installs\dff2a7c1aa1d2670\environments\3d191065334546e08496a64b86fa12ed\venv\Scripts\python.exe C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\extract\wangbin-tender-analyzer\scripts\check_response.py --tender C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\cases\Z10-license-uncertain\tender.txt --mode check --response C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\cases\Z10-license-uncertain\response.md --output-dir C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\cases\Z10-license-uncertain\out --project 虚构核验Z10-license-uncertain --evidence-file C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\cases\Z10-license-uncertain\营业执照.txt`；cwd `C:\Users\wangbin\AppData\Local\hermes\profiles\wb-quality\cache\scratch\q06_fix3_independent_028_r3\cases\Z10-license-uncertain`；exit `0`；stdout `CREATED 虚构核验Z10-license-uncertain-投标响应检查.xlsx 虚构核验Z10-license-uncertain-提交前核对清单.md<br>`；stderr ``。
- 待确认表：``；附件核对表：`[['1:1:1', None, None, '营业执照.txt', '已提供（可读文本）', '支持（文本层面）', '营业执照.txt:1', '文本支持不认证真伪']]`；MD 已覆盖分段：`<br>- 1:1:1 (原编号 1；tender.txt:1；响应 response.md:1；材料 营业执照.txt:1)：已定位。四维：已定位 / 已覆盖（文本层面） / 已提供（可读文本） / 支持（文本层面）。<br><br>`。
- 修复预期仅为下次经理决策参考，本卡不启动返工：未知是否上线不能推出已上线；仅登记信息且“是否构成正式营业执照尚待核实”不应推出材料支持或条件已覆盖。

## 全案摘要（详见可执行脚本与原始 JSON）

| ID | 类型 | 比对结果 | 四维实际 |
|---|---|---|---|
| R01-expiry | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| R02-start | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| R03-edge-positive | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| R04-issued-only | frozen53 | PASS | [['已定位', '待确认', '已提供（可读文本）', '待确认']] |
| R05-two-certificates | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| R06-shift | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| R07-ambiguous-year | frozen53 | PASS | [['已定位', '待确认', '已提供（可读文本）', '待确认']] |
| R08-no-backup | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| R09-yes-backup | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| R10-neg-neg | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| R11-conditional | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| R11-not-implemented | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| R12-scope | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用'], ['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| R13-license-missing | frozen53 | PASS | [['已定位', '可能不充分', '未提供（限已提供材料）', '未核验']] |
| R14-catalog-csv | frozen53 | PASS | [['已定位', '可能不充分', '仅目录登记', '未核验']] |
| R14-catalog-xlsx | frozen53 | PASS | [['已定位', '可能不充分', '仅目录登记', '未核验']] |
| R15-license-negative | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| R16-license-positive | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| R16-duplicate | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '待确认', '待确认']] |
| R17-empty-conditions | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| R18-no-catalog | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| R19-before | frozen53 | PASS | [['已定位', '可能不充分', '仅目录登记', '未核验'], ['已定位', '可能不充分', '仅目录登记', '未核验']] |
| R19-after | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）'], ['已定位', '可能不充分', '仅目录登记', '未核验']] |
| V01-shift-object | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| V02-shift-boundary | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| V03-cross-negation | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| V04-rephrase-no | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| V05-rephrase-promise | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| V06-irrelevant | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| V07-irrelevant-evidence | frozen53 | PASS | [['已定位', '待确认', '已提供（可读文本）', '待确认']] |
| V08-prepare | frozen53 | PASS | [['未核查', '未核查', '不适用', '不适用']] |
| V09-amendment | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用'], ['候选待确认', '可能不充分', '不适用', '不适用']] |
| N01-rephrase-incapable | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| N02-rephrase-limited | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| N03-rephrase-positive | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| N04-rephrase-scope | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用'], ['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| N05-no-catalog-negative | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| N06-no-catalog-positive | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| N07-no-file-control | frozen53 | PASS | [['已定位', '可能不充分', '未提供（限已提供材料）', '未核验']] |
| N08-cross-object | frozen53 | PASS | [['已定位', '可能不充分', '未提供（限已提供材料）', '未核验'], ['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| N09-date-shift-positive | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| Q01-unable-present | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| Q02-not-available-yet | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| Q03-proposed-future | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| Q04-positive-operational | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| Q05-no-cross-subject | frozen53 | PASS | [['已定位', '可能不充分', '不适用', '不适用'], ['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| Q06-evidence-not-issued | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| Q07-evidence-empty-wrapper | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| Q08-evidence-genuine-text | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| Q09-cross-object | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）'], ['已定位', '可能不充分', '未提供（限已提供材料）', '未核验']] |
| Q10-cross-object-negative | frozen53 | PASS | [['已定位', '可能不充分', '未提供（限已提供材料）', '未核验'], ['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| Q11-date-shift | frozen53 | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| Q12-date-boundary | frozen53 | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| Z01-current-unavailable | independent_variant | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| Z02-future-instead | independent_variant | PASS | [['已定位', '可能不充分', '不适用', '不适用']] |
| Z03-positive-installed | independent_variant | PASS | [['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| Z04-unknown-status | independent_variant | FAIL: ['1:1:1 条件覆盖状态: expected 待确认, actual 已覆盖（文本层面）'] | [['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| Z05-two-functions | independent_variant | PASS | [['已定位', '可能不充分', '不适用', '不适用'], ['已定位', '已覆盖（文本层面）', '不适用', '不适用']] |
| Z06-two-functions-invert | independent_variant | PASS | [['已定位', '已覆盖（文本层面）', '不适用', '不适用'], ['已定位', '可能不充分', '不适用', '不适用']] |
| Z07-license-not-issued | independent_variant | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| Z08-license-wrapper | independent_variant | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| Z09-license-positive | independent_variant | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| Z10-license-uncertain | independent_variant | FAIL: ['1:1:1 条件覆盖状态: expected 待确认, actual 已覆盖（文本层面）', '1:1:1 内容支持状态: expected 待确认, actual 支持（文本层面）'] | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| Z11-two-materials | independent_variant | PASS | [['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）'], ['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']] |
| Z12-two-materials-reversed | independent_variant | PASS | [['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）'], ['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |
| Z13-other-material-no-proof | independent_variant | PASS | [['已定位', '可能不充分', '未提供（限已提供材料）', '未核验'], ['已定位', '已覆盖（文本层面）', '已提供（可读文本）', '支持（文本层面）']] |

## 实物与限制

- `qa-fix3-028-independent.py` 为从 ZIP 重放的可执行证据；`qa-fix3-028-independent-results.json` 为逐行四维、gap/provenance、完整五表行、MD 全文、所有输入输出 SHA 与错误探针原始返回。
- `qa-fix3-028-examples/` 是原 CLI 实际生成的两个案例（一个原失败已闭合，一个新增歧义失败）的 XLSX+MD。输入留在 profile-owned scratch，逐字节 hash 见 JSON；报告含复现输入原文。
- 原 0.2.7 QA 47/53 FAIL 的历史结果不改写；本次失败数是 **新增独立变体 2/13**，不是原 53 回归失败。确认矩阵不等于平台运行与许可证授权。
