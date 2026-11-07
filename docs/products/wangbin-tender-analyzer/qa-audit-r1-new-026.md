# AUDIT-R1 Q06 · 0.2.6 新 ZIP 独立复验：FAIL

product_id `wangbin-tender-analyzer`；task_id `t_0a81f71d`；workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch `skill/tender-response-check`；测试前 HEAD `e56d8946b431f6f07e78c0021bddcb081bae6f5a`（父 0.2.5 QA-only `6d04436d378daff815a6fb92fa971022b00e39a8`）。只写本报告、QA 脚本及 QA 证据，没有修改业务源码/历史预期/旧 ZIP/许可证。

## 锁包与独立运行

- 精确新候选 `dist/wangbin-tender-analyzer-0.2.6-skill-candidate.zip` SHA-256 `1c18b43f8cb465eb261ae4ccdc950259399f64b9c70477496809e3102dd4753a`；sidecar 相等，manifest `id/version=wangbin-tender-analyzer/0.2.6`，11 个 ZIP 成员 `ZipFile.testzip()` 无坏成员，成员路径无重复/绝对/遍历，size/SHA 与 manifest 和产品源码逐件相同，包内 `check_response.py` SHA `c687c1f81e348fd573997a96719726f362e76dffe71cb62818ec54b11460c4db`。SKILL YAML 可解析，name/version 对应，中英各三问，写出 Python 3.11+ 和 `openpyxl>=3.1,<4` 依赖及解压执行路径。catalog 的本地 `active_version=0.2.6` 是工厂版本选择，**非 WorkBuddy 安装或发布激活**。旧 0.2.3 ZIP SHA `5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce` 和失败 0.2.5 ZIP SHA `69e1a9f2ef0698e40a174faf711e1eb627aecc68fb1106c567a506d063493c06` 均独立重算未变；0.1.0 实物 NOT_VERIFIED。
- `python docs/products/wangbin-tender-analyzer/qa-audit-r1-new-026-probe.py` 在 profile scratch **全新**目录 `q06_independent_026_rerun1` 解压新 ZIP；各案例写实际 `tender.txt`、`response.md`、证据 TXT/CSV/XLSX，不带工作树 PYTHONPATH，子进程执行解压包自己的 `scripts/check_response.py`，专用空输出目录。先声明旧 32 个 ID 的预期、R18 明确唯一实际提交却不支持、以及新增 N01–N09 的正反/无目录/错配变体，再调用。41 个案例都返回 CLI exit 0、有两件输出；逐例重新打开 XLSX 的 `核查概览/要求响应矩阵/附件核对/补遗与版本/待确认事项` 五表、MD，核查四维、缺口、来源/证据位置、概览计数、MD 分类/ID，输出无公式单元格。每案例真实 argv、cwd、stdout/stderr、输入/输出 SHA、期望/实际、五表数据及 MD 内容保存在 `qa-audit-r1-new-026-results.json`；203 个真实输入/输出在 `qa-audit-r1-new-026-fixtures-outputs.zip`（QA 证据，**不是** Skill 包），SHA-256 `2bd0fa6850981db7fad6ba7ce62521cbe7ef56e51df1b552d61ed7f6575d2000`，`python -m zipfile -t` exit 0。
- **旧 32/32 在新 ZIP 上符合本探针断言；新增 9 项 4 PASS、5 FAIL，总计 36/41 PASS、5 FAIL。** 0.2.5 历史 29/32 FAIL 不改写。R18 的四维现在为 `已定位 / 可能不充分 / 已提供（可读文本） / 不支持（文本层面）`、证据 `certificate.txt:1`，是这次真正修好的旧缺陷；V04/V06 固定原句也修好，但下面等义表达仍失败。R03/R09/R10/N03/N06/N09 确定正向没有被全面降级为待确认；N07 无实物控制正确报未提供/未核验。

## 阻断缺陷及复现（所有原件/输出在证据 ZIP 的 `cases/<ID>/`）

1. **N01 BID-F02/F04 能力否定等义**：`tender.txt:1` `1. 必须支持自动备份。`，`response.md:1` `1. 对自动备份，我们目前做不到。`。预期编号定位但明确不能履行，条件 `可能不充分`，冲突/缺口非空且 MD 不列已覆盖；实际 exit 0，矩阵 `1:1:1` 为 `已定位 / 已覆盖（文本层面） / 不适用 / 不适用`，缺口空，MD 错列已覆盖。
2. **N02 BID-F02/F04 仅设计且当前无能力**：同 tender，response `1. 自动备份仅处于方案设计阶段，目前尚不具备该能力。`。预期同 N01，实际同样 `已覆盖（文本层面）`、缺口空、MD 错列已覆盖。不能把“设计阶段”当上线支持。
3. **N04 BID-F02 否定范围隔离**：tender L1 自动备份必需、L2 离线查询必需；response L1 `1. 自动备份功能尚未启用。`，L2 `2. 我方支持离线查询。`。预期第 1 项定位/条件不足且来源 `response.md:1`、第 2 项已覆盖；实际两项都已覆盖，第一项缺口空并进 MD 已覆盖。不能用第 2 项肯定冲淡第 1 项限制。
4. **N05 BID-F03/F04 明确已给文件正文为示例占位**：tender `1. 须提供certificate.txt资质证明。`，response `1. 证书见certificate.txt。`，显式 `--evidence-file certificate.txt`，正文 `certificate.txt：这是示例占位文件，并非真正证书。`，**无目录**。预期唯一文件已提供但当前材料明确为占位，不支持提供证书声明，条件不足、确定缺口及 `certificate.txt:1`；实际 `已定位 / 待确认 / 已提供（可读文本） / 待确认`，MD 只列“材料提及相近对象，但缺完整可核对声明”的人工确认，不列确定需补。此处只核材料是否包含证书，不对假设的真证书做行政真伪认证；因此不应将明确“示例占位文件”当作普通不明内容。
5. **N08 BID-F03 跨要求显式实物关联**：tender L1 必须提供甲类资质证明，L2 必须提供乙类资质证明；response L1 `1. 甲类证明已提交。`，L2 `2. 乙类证明已提交。`；唯一显式 `--evidence-file 乙类.txt` 正文 `乙类证明文本：乙类有效。`，无目录。预期甲类未提供/未核验，乙类实际可读且其文本支持对应乙类的有限声明（不能认证真伪），附件/内容 `已提供（可读文本） / 支持（文本层面）`；实际甲类正确，但乙类亦 `未提供（限已提供材料） / 未核验`，丢失 `乙类.txt:1` 关联，条件也 `可能不充分`。不能把目录缺失等同实际未提供，也不得将乙类错配甲类。

以上每例详细 expected/actual、真实命令、全部内容与 SHA 均可由包外 JSON/证据 ZIP 复核。`python` 探针进程本身 exit 0 表示已完成记录，**不是** 41 项业务通过；真实业务判定以 5 条 issues 为准。N05 文本与证书真实性的边界需按冻结材料义务裁决，不能以“未认证原件”为由将明确占位文件说成证书材料已满足。

## 其他回归与门禁

- 新包旧 JSON `scripts/analyze_tender.py --input examples/fictional-tender.txt` exit 0，stdout 与旧 0.2.3 ZIP 内**原始** `fictional-tender.expected.json` 解析相等，未从 actual 改写 expected。`python docs/products/wangbin-tender-analyzer/qa-audit-r1-new-026-errors-probe.py` exit 0，6/6：缺响应、非法 UTF-8、不支持 PDF、损坏清单、路径越界各 exit 2 且无成功文件；正向 exit 0 双文件，明细见 `qa-audit-r1-new-026-errors.json`。完整旧 A02–A14 独立 L3 为 NOT_TESTED。
- `python -m pytest -q tests/test_tender_response_audit.py tests/test_tender_analyzer.py --basetemp=C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_pytest_026_r1` exit 0：33 passed、Windows symlink 创建不可用 1 skipped；不抵消以上独立业务失败。`python -m tooling.products verify --id wangbin-tender-analyzer` exit 0/PASS 为归档结构检验；`python -m tooling.products release-check --id wangbin-tender-analyzer` **exit 1/BLOCKED**，许可证文件缺失/依赖分发权未核实，人工相似性 `REVIEW_REQUIRED`、WorkBuddy 安装/对话/审核 `NOT_TESTED`。隔离环境重装依赖 NOT_TESTED；现有宿主已提供 openpyxl。L4 真正 Hermes 宿主三轮因 L3 业务 FAIL 本次 **NOT_TESTED**（不能以脚本回放冒充模型执行）；L5 WorkBuddy 平台 **NOT_TESTED**；证书真实性 NOT_VERIFIED，路径符号链接在 Windows 真机 SKIPPED，静态代码检查不能代替它。

**最终结论：0.2.6 精确 ZIP 本地 L3 业务 FAIL，不能放行、不能把旧 32/32 预核或工厂 PASS 当全部验收。** 已向经理卡 `t_0237b1ca` 反馈；本轮第 1 次退回后的 QA 再发现问题，是否使用唯一剩余的 return-2 由经理按上限组织，QA 不自行修业务/重打包/推送/上传/发布。