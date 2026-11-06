# Q02 T03 独立 QA — 首轮 FAIL（不得放行 T04）

- product_id: `wangbin-project-acceptance-check`; task_id: `t_83900262`; workspace: `F:/ideaWorkSpace/wangbin-workbuddy-project-acceptance-check`; branch: `skill/project-acceptance-check`; base_commit: `db31fb8f2d4981b497f031785a6d830867db037a`; result_commit: `PENDING_QA_REPORT_COMMIT`。
- 冻结合同：`docs/products/wangbin-project-acceptance-check/{requirements,input-output-contract,acceptance-cases}.md`；实际被测源码只读，未修改。预 QA ZIP `dist/wangbin-project-acceptance-check-0.1.1-skill-candidate.zip` SHA-256 `74210b2a9e35074f247173f71909848acddb615da40fb39fa24eff74bb99d958`；ZipFile `testzip()` 通过，9 成员逐个 SHA-256/大小与 manifest 一致，隔离解压调用包内 `scripts/check_acceptance.py`，非生产源码入口。sidecar SHA 一致。完整逐案真实命令参数、退出码、JSON 快照与重新读取的六表/DOCX 内容见 `wangbin-project-acceptance-check-q02-t03-run.json`；可重建虚构输入的独立脚本 `wangbin-project-acceptance-check-q02-t03-repro.py`，临时输入/生成物运行后清理，不以其路径为持久附件。
- 执行 `python docs/qa/wangbin-project-acceptance-check-q02-t03-repro.py`：进程退出 0 仅表示**测试采集器成功记录结果，不代表产品 PASS**；断言字典 A01/A09/A12/B02 为 false，其余采样 true。`python -m tooling.products verify --id wangbin-project-acceptance-check` 退出 0；`python -m pytest -q tests/test_project_acceptance_check.py` 退出 0（14 passed, 1 skipped，symlink 无权限，1 个第三方弃用警告）。既有单测/工厂结构门禁不能替代本轮业务核查。

## 阻断缺陷与复现

**D1（P0，ACC-A01/A09）：明确的异构部署环境不符合被判无证据，误导核心结论。** 从上述 repro 运行 `A01`：`scope.md` 三行依次 `R01：提供包含端点、请求参数和返回字段的接口文档。`、`R02：提供 Windows Server 2019 部署说明。`、`R03：提供本项目培训记录。`；`interface.md` 写 `/demo/items`、`请求参数：item_id`、`返回字段：name`；`deploy.md` 一行 `D02：仅 Ubuntu 部署步骤，未提供 Windows Server 2019 步骤。`。入口传入 `--scope-source scope.md --delivery-source interface.md --delivery-source deploy.md --effective-version-ref scope.md`。预期 R01/R02/R03 分别 `EVIDENCE_FOUND/NONCONFORMING/NO_EVIDENCE_FOUND`，R02 引用 deploy.md/行1 且同时保留明确不符及缺 Windows 步骤；实际退出 0，却为 `EVIDENCE_FOUND/NO_EVIDENCE_FOUND/NO_EVIDENCE_FOUND`，R02 `sources=[]`、仅 MISSING，六表与 DOCX 同步写入错误结论。A09 显式提供 A01 快照及新 `training.md` 后 R03 转 `EVIDENCE_FOUND`、缺口 RESOLVED，但 R02 错误状态仍保留。定位：`check_acceptance.py` 的 `evaluate_condition` 相关词匹配不认“部署步骤”与“部署说明”的异词负证据。

**D2（P1，B02）：一般复合要求未拆子条件，独立不符与缺失被吞。** repro `B02`：`scope.md` 为 `R01：提供 Windows Server 2019 部署说明和培训记录。`；`deploy.md` 为 `R01：仅 Ubuntu 部署步骤，未提供 Windows Server 2019 步骤。`；同样传 scope/delivery/version。预期按复合要求拆部署/培训至少两子条件，主 `NONCONFORMING`，发现同时包含 NONCONFORMING 与 MISSING；实际退出 0、只有一个合并条件，主 `NO_EVIDENCE_FOUND`、仅 MISSING，覆盖 `0/1`。与 D1 有关联，但还需普遍拆分及逐条件计数，不能只修匹配词。

**D3（P2，ACC-A12 错误分类）：损坏 OOXML 与纯文本伪扩展名未区分。** repro `A12` 传 `broken.docx` 字节 `PK\x03\x04broken`，`fake.docx` 普通文本，另传 `diagram.pdf` 与可读 scope/test.csv；预期损坏文档 `UNREADABLE_SOURCE`，伪扩展名/不支持文件 `UNSUPPORTED_FORMAT`，混合材料 PARTIAL(3)；实际 PARTIAL(3) 与可读材料保留，但 `broken.docx` 被归为 `UNSUPPORTED_FORMAT (fake docx)`，没有 `UNREADABLE_SOURCE`。全坏单文件 INVALID(2) 正常；需按文档签名/损坏性质准确分类。

## 通过采样及不能继承的边界

- A02 两条件部分支持；A03 同名 v1/v2 冲突且覆盖 N/A；A04 重复 ID 分来源保留；A05 目录仅 LISTED_ONLY；A06 开发声明不当证据；A07 无唯一引用列候选；A08 未确认范围隔离；A10 相反测试结果 CONFLICT；A11 DOCX 普通表格 `表1/行2/列2`；A13 六表及实际 DOCX 重新打开、要求状态与 ID 可见；A14 只抽样核实 A03/A07/A10/A11 来源，未穷尽逐项；B01 无范围覆盖 N/A；B04 代表性 `../secret`、4000001 字节文件以及 XLSX 公式单元格类型防护均采样通过。详细字典字段不等于全合同覆盖。
- ZIP 路径遍历/归档成员完整性、表格公式文字性和文件上限采样已测；真实 symlink 越权、恶意 ZIP 炸弹/Office 外链及宏的完整矩阵、路径输出逃逸/写失败、B03/B05/B06/B07 复杂变体、无有效版本但指定 ref 的权威性、外部快照篡改、自然语言双语三问在 WorkBuddy 的真实多轮行为，均 `NOT_TESTED`。中文/英文推荐问句逐字在 SKILL.md 六条已人工读到，但平台调用为 `NOT_TESTED`。许可证权属审核、真实 WorkBuddy 安装、依赖供给、平台评测/审核/上架均 `BLOCKED/NOT_TESTED`，不得称本地验收通过或正式签收。
- 冻结文档的 Markdown 硬换行尾部空格为父卡已知非通过项，不更改。测试结果不许可覆盖历史失败记录。

**结论：LOCAL FAIL；阻断此 QA 卡，要求独立定向修复并生成新版本不可变 ZIP，再由新的 Worker 独立复验 D1–D3 与受影响的 A01–A14/B02/A12；不可将原 0.1.1 ZIP 的本地结论改写为 PASS。** 未 push、上传、发布、merge 或 rebase。
