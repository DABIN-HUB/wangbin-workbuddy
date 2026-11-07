# AUDIT-R1 Q06 · 0.2.7 最终独立 ZIP L3 复验：FAIL 47/53

product_id `wangbin-tender-analyzer` · task_id `t_b7703b65` · workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check` · branch `skill/tender-response-check` · base_commit `f246cd88522fbb9a0ec7c5c2514409eaa648cf51`。本轮返工 2/2 已用尽；历史 0.2.5 29/32 FAIL 与 0.2.6 36/41 FAIL 保持不变。

## 锁定候选与范围

- 本地包 `dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip`，SHA-256 `12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09`；sidecar/manifest/ZipFile.testzip/11 成员的路径、大小、SHA 和源码对应均独立核查通过，SKILL YAML、版本、中英各三问及解压运行路径核查。catalog `active_version=0.2.7` 为本地工厂登记，绝非 WorkBuddy 平台发布。旧 0.2.3/0.2.5/0.2.6 SHA 依次为 `5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce` / `69e1a9f2ef0698e40a174faf711e1eb627aecc68fb1106c567a506d063493c06` / `1c18b43f8cb465eb261ae4ccdc950259399f64b9c70477496809e3102dd4753a`，实物未变。开发提交源码 SHA 与 ZIP 内脚本相同。
- 用 `qa-audit-r1-new-027-probe.py` 在 profile scratch `q06_independent_027_rerun1` 干净解压精确 ZIP，逐例创建真实 TXT/MD/CSV/XLSX 输入，清除 PYTHONPATH，调用解压包正式 `scripts/check_response.py`，每例空输出目录；53 例 CLI 全部 exit 0、各生成 XLSX+MD，实际重开 XLSX 五表、核验四维/缺口/来源/概览统计和 MD 覆盖分类、无公式单元格。沿用先于运行冻结的旧 41 例断言，额外事先声明 12 个新等义正反、时间、跨对象、材料文本变体：旧 41/41 PASS，新 6/12 PASS，**共 47 PASS / 6 FAIL**；CLI exit0 ≠ 业务通过。
- 每例实际命令 argv、cwd、退出码、stdout/stderr、真实输入输出 SHA、预期与实际、五表行及完整 MD 见 `qa-audit-r1-new-027-results.json`；实际原件及两输出见 `qa-audit-r1-new-027-fixtures-outputs.zip`（260 件，SHA-256 `a791979b9e6d83b36b8e533cde7f65ab1ac3267ced9a909512827413dbc3c986`），非 Skill ZIP。

## 阻断问题与精确复现

下面每项的文件路径是证据 ZIP 内 `cases/<ID>/`，使用 `--tender tender.txt --mode check --response response.md --output-dir out --project 虚构核验<ID>`；材料案例额外传入所列 `--evidence-file`。各文件 UTF-8，行号 L1；按报告 JSON 中 argv 可精确重跑。判定仅为本次提供文本，不认证公司证照真伪或运营环境。

### Q02-not-available-yet

- 实际输入：`tender.txt:1` `1. 必须支持自动备份。` (SHA-256 `cbf4dd72c1e1f9f768a4e4c5d56ad909491a2e6ab2a1cf0975be27dedaa7f9ea`)；`response.md:1` `1. 自动备份还未投入使用。` (SHA-256 `96547c3dacb5a49ef3cccf085c6a1c1e7b244422e24cb5c89d31802a15711f03`)
- 独立预期四维：`['已定位', '可能不充分', '不适用', '不适用']`；明确否定/未启用须有缺口与来源并不得列 MD 已覆盖，明确占位/非证书须记录文本反证而非支持或含糊待确认。
- 实际（CLI exit 0）：`1:1:1` 已定位 / 已覆盖（文本层面） / 不适用 / 不适用；缺口 `None`；证据位置 `None`；来源 `tender.txt:1`
- 逐格缺陷：1:1:1 条件覆盖状态 expected 可能不充分 actual 已覆盖（文本层面）；mandatory gap/source/evidence missing
- 输出 SHA-256：`{'虚构核验Q02-not-available-yet-投标响应检查.xlsx': 'b68716e72f85be11b1284b0417a94f9f3394c1245ac7f35488dd3b4fdd875a59', '虚构核验Q02-not-available-yet-提交前核对清单.md': 'b3f4b78df5a8c4c7acb1cbc31bc3132ff72937ac19444eaa7c911c4f9f52aafb'}`；XLSX 五表和 MD 全文见结果 JSON/证据 ZIP。

### Q03-proposed-future

- 实际输入：`tender.txt:1` `1. 必须支持自动备份。` (SHA-256 `cbf4dd72c1e1f9f768a4e4c5d56ad909491a2e6ab2a1cf0975be27dedaa7f9ea`)；`response.md:1` `1. 自动备份已纳入后续研发计划，现阶段无法提供。` (SHA-256 `35718df5673e73d6e12e45febc4b1430b2b33769e9d289aa1755c8cb520bed8f`)
- 独立预期四维：`['已定位', '可能不充分', '不适用', '不适用']`；明确否定/未启用须有缺口与来源并不得列 MD 已覆盖，明确占位/非证书须记录文本反证而非支持或含糊待确认。
- 实际（CLI exit 0）：`1:1:1` 已定位 / 已覆盖（文本层面） / 不适用 / 不适用；缺口 `None`；证据位置 `None`；来源 `tender.txt:1`
- 逐格缺陷：1:1:1 条件覆盖状态 expected 可能不充分 actual 已覆盖（文本层面）；mandatory gap/source/evidence missing
- 输出 SHA-256：`{'虚构核验Q03-proposed-future-投标响应检查.xlsx': '67f0d325d71cc6dcbb0c5c8b3b97b63c319de57f9b8c2a30a84bbce804439c9d', '虚构核验Q03-proposed-future-提交前核对清单.md': '634952d06c009261b11d9d766a378f8e8d31de6fa2d83b206c16824fa98308a9'}`；XLSX 五表和 MD 全文见结果 JSON/证据 ZIP。

### Q05-no-cross-subject

- 实际输入：`tender.txt:1` `1. 必须支持自动备份。
2. 必须支持离线查询。` (SHA-256 `d24f3fc06a09c62aa47d77f45a85b418a1c16a86be9ab43fa615df50a9b431c9`)；`response.md:1` `1. 目前尚无法提供自动备份。
2. 离线查询现已投入使用。` (SHA-256 `332c1ff6925656b4a0e7fb6887fe422a047a5a1440a473feb7f18fe43f31297a`)
- 独立预期四维：`[['已定位', '可能不充分', '不适用', '不适用'], ['已定位', '已覆盖（文本层面）', '不适用', '不适用']]`；明确否定/未启用须有缺口与来源并不得列 MD 已覆盖，明确占位/非证书须记录文本反证而非支持或含糊待确认。
- 实际（CLI exit 0）：`1:1:1` 已定位 / 已覆盖（文本层面） / 不适用 / 不适用；缺口 `None`；证据位置 `None`；来源 `tender.txt:1`；`1:2:2` 已定位 / 已覆盖（文本层面） / 不适用 / 不适用；缺口 `None`；证据位置 `None`；来源 `tender.txt:2`
- 逐格缺陷：1:1:1 条件覆盖状态 expected 可能不充分 actual 已覆盖（文本层面）；mandatory gap/source/evidence missing
- 输出 SHA-256：`{'虚构核验Q05-no-cross-subject-投标响应检查.xlsx': '4de2f042792f4922ff0f5b49851708c74e03f96024f4b1febe0ae71294860e61', '虚构核验Q05-no-cross-subject-提交前核对清单.md': 'd7836aa90624308c3392350f5849ca8783ee61c507f62ee1df975e4dda9c5aba'}`；XLSX 五表和 MD 全文见结果 JSON/证据 ZIP。

### Q06-evidence-not-issued

- 实际输入：`tender.txt:1` `1. 必须提供营业执照。` (SHA-256 `e15882d7f3447a02d456f4f078005fc5a4146b83cfbbdba4ca9077455bb1a00f`)；`response.md:1` `1. 营业执照已递交。` (SHA-256 `33fa9875ce94aca9157134e19de901d19bc2e0b572a87c8b313d5ef38d34291a`)；`营业执照.txt:1` `营业执照尚未颁发；此为申请材料，不是营业执照。` (SHA-256 `c3e2a14b0b7d9499b98cc82fd51160b5f6a4b1f6f43672807aa0efb4de4c7c13`)
- 独立预期四维：`['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']`；明确否定/未启用须有缺口与来源并不得列 MD 已覆盖，明确占位/非证书须记录文本反证而非支持或含糊待确认。
- 实际（CLI exit 0）：`1:1:1` 已定位 / 已覆盖（文本层面） / 已提供（可读文本） / 支持（文本层面）；缺口 `None`；证据位置 `营业执照.txt:1`；来源 `tender.txt:1`
- 逐格缺陷：1:1:1 条件覆盖状态 expected 可能不充分 actual 已覆盖（文本层面）；1:1:1 内容支持状态 expected 不支持（文本层面） actual 支持（文本层面）；mandatory gap/source/evidence missing
- 输出 SHA-256：`{'虚构核验Q06-evidence-not-issued-投标响应检查.xlsx': '4c2d3ce24f9eb167930c86e48ad144f373dde90bd7114a3e83d6c78f7600269a', '虚构核验Q06-evidence-not-issued-提交前核对清单.md': '1c57a54bcf0d7ea85e47be3fdb9cc88ef68e61ba0d6895e2102654186e6cb968'}`；XLSX 五表和 MD 全文见结果 JSON/证据 ZIP。

### Q07-evidence-empty-wrapper

- 实际输入：`tender.txt:1` `1. 须提供certificate.txt资质证明。` (SHA-256 `e9b4e631e301ed1f617fee9dbd97fdb10842ecffa09b2a90a29f06e51cef544e`)；`response.md:1` `1. 附件certificate.txt为资质证明。` (SHA-256 `258e398e75ac3b61479621273b8544333a0b48d446498d998ce9c38491aea981`)；`certificate.txt:1` `certificate.txt：此文件仅作为示意，不包含任何证照正文。` (SHA-256 `cfa10bbd73bef5eac3c9010c57169cfdd4d3ab91a2cf43cf32a2ffead8d0b0bb`)
- 独立预期四维：`['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']`；明确否定/未启用须有缺口与来源并不得列 MD 已覆盖，明确占位/非证书须记录文本反证而非支持或含糊待确认。
- 实际（CLI exit 0）：`1:1:1` 已定位 / 待确认 / 已提供（可读文本） / 待确认；缺口 `None`；证据位置 `certificate.txt:1`；来源 `tender.txt:1`
- 逐格缺陷：1:1:1 条件覆盖状态 expected 可能不充分 actual 待确认；1:1:1 内容支持状态 expected 不支持（文本层面） actual 待确认；mandatory gap/source/evidence missing
- 输出 SHA-256：`{'虚构核验Q07-evidence-empty-wrapper-投标响应检查.xlsx': '472003f8ae837a16d7b6d1b307121b53a3b8341e2cf67b7db30da4452f6421f1', '虚构核验Q07-evidence-empty-wrapper-提交前核对清单.md': 'b1933305542b20c87af58a2001fbb2d8556929b4b0e0482a0c598544664dbc66'}`；XLSX 五表和 MD 全文见结果 JSON/证据 ZIP。

### Q10-cross-object-negative

- 实际输入：`tender.txt:1` `1. 必须提供甲类资质证明。
2. 必须提供乙类资质证明。` (SHA-256 `42b4bb00e61589066ff72cd25ba2fb53969b1d846856fc9d3015afc245b1bdf7`)；`response.md:1` `1. 甲类证明已提交。
2. 乙类证明已提交。` (SHA-256 `874ba128515d094c46697b46772fecf82471dcc420c7735f667b95868961f2fb`)；`乙类.txt:1` `乙类证明尚在申请；本文件不是乙类证明。` (SHA-256 `04716470b524100a8addaeceadaaf8d84bdf71ad58f395d0b0d5930ce46ffaa8`)
- 独立预期四维：`[['已定位', '可能不充分', '未提供（限已提供材料）', '未核验'], ['已定位', '可能不充分', '已提供（可读文本）', '不支持（文本层面）']]`；明确否定/未启用须有缺口与来源并不得列 MD 已覆盖，明确占位/非证书须记录文本反证而非支持或含糊待确认。
- 实际（CLI exit 0）：`1:1:1` 已定位 / 可能不充分 / 未提供（限已提供材料） / 未核验；缺口 `明确条件未获得完整文本支持：必须提供甲类资质证明；要求 必须提供甲类资质证明；在已提供材料中未找到实际文件，需补交或明确关联`；证据位置 `None`；来源 `tender.txt:1`；`1:2:2` 已定位 / 待确认 / 已提供（可读文本） / 待确认；缺口 `None`；证据位置 `乙类.txt:1`；来源 `tender.txt:2`
- 逐格缺陷：1:2:2 条件覆盖状态 expected 可能不充分 actual 待确认；1:2:2 内容支持状态 expected 不支持（文本层面） actual 待确认
- 输出 SHA-256：`{'虚构核验Q10-cross-object-negative-投标响应检查.xlsx': '181d5564776c4fcb772bc79b8c7cfdc689fd1444c125869289906941c3de53ce', '虚构核验Q10-cross-object-negative-提交前核对清单.md': '159da3de503f28d397ad1f4c3682253857e0b2557075a7f00b418afb371d908a'}`；XLSX 五表和 MD 全文见结果 JSON/证据 ZIP。

## 其他验证与边界

- 旧 `scripts/analyze_tender.py --input examples/fictional-tender.txt` 从 0.2.7 解压包 exit 0；解析 stdout 与原 0.2.3 ZIP 内 **原始** `fictional-tender.expected.json` 相等，未改预期。正式错误 6/6：缺响应、非法 UTF-8、PDF、损坏 XLSX 目录、输出路径逃逸各 exit 2/无成功输出；正向 exit 0/两文件，详情 `qa-audit-r1-new-027-errors.json`。
- `python -m pytest -q tests/test_tender_response_audit.py tests/test_tender_analyzer.py --basetemp=C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_pytest_027_final` exit 0（42 passed, 1 Windows 实体 symlink skipped）；`python -m tooling.products validate --id wangbin-tender-analyzer` exit 0；`python -m tooling.products verify --id wangbin-tender-analyzer` exit 0；`python -m zipfile -t` 两份 ZIP exit 0，均不能抵消 L3 业务失败。
- `python -m tooling.products release-check --id wangbin-tender-analyzer` **exit 1 / BLOCKED**：许可证文件不存在及依赖合法分发待定；相似性人工 `REVIEW_REQUIRED`；WorkBuddy 安装/对话/审核 `NOT_TESTED`。L4 Hermes 宿主三轮因 L3 FAIL **NOT_TESTED**，L5 WorkBuddy **NOT_TESTED**；证书真实性 NOT_VERIFIED；Windows 物理 symlink 安全性 SKIPPED，openpyxl 隔离重装及平台依赖可用性 NOT_TESTED；完整旧 A02–A14 独立 L3 NOT_TESTED；0.1.0 实物 NOT_VERIFIED。
- 未改业务代码、历史报告、许可证、旧 ZIP；未 push、merge、rebase、上传或发布。只有本产品 `qa-audit-r1-new-027-*` QA-only 证据文件。

**结论：0.2.7 精确 ZIP 的本地独立 L3 为 FAIL，六个新发现变体存在可复现业务误判；本轮自动返工额度 2/2 已用尽，不建立第三轮修复。已通知经理 `t_0237b1ca` 如实报告，不得宣称六包全部独立 QA 合格。**
