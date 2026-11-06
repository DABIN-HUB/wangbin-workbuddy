# Q02 T03-RERUN-1 — 独立复验 0.1.2 本地候选 PASS

- product_id: `wangbin-project-acceptance-check`; task_id: `t_088fe016`; workspace: `F:/ideaWorkSpace/wangbin-workbuddy-project-acceptance-check`; branch: `skill/project-acceptance-check`。
- base_commit/source_commit: `54e0fd900cfd9cb2c71f9256e22dd23f25244660`；本报告 result_commit 以提交日志为准。首轮 FAIL 证据提交 `88cbdd74e0a4bdf6079128adca9477f237c57bd8`、原 ZIP `0.1.1` SHA-256 `74210b2a9e35074f247173f71909848acddb615da40fb39fa24eff74bb99d958` 原样保留，**不能追溯改写成 PASS**。
- 被测不可变候选：`dist/wangbin-project-acceptance-check-0.1.2-skill-candidate.zip`，SHA-256 `5117bd7202cd6a322c3aae8246dad79edeb4cd9a876cbcae800ee78ad2a9df57`。独立校验 sidecar/manifest 哈希、9 个不重复安全路径成员逐个 SHA-256 和大小、`ZipFile.testzip() == None`、包成员逐字节等于产品目录源码；干净解压并仅调用包内 `scripts/check_acceptance.py`。manifest 的 `platform=BLOCKED`、`scope=local archive integrity only`，不是平台通过。
- 冻结依据：`docs/products/wangbin-project-acceptance-check/{requirements,input-output-contract,acceptance-cases}.md`；首轮独立 FAIL：`docs/qa/wangbin-project-acceptance-check-q02-t03.md`。新脚本 `docs/qa/wangbin-project-acceptance-check-q02-t03-rerun-probe.py` 自行构造虚构输入、调用 ZIP 解压入口、对照冻结预期；`...-rerun-run.json` 含各案真实命令参数、输入 SHA、退出码、stdout/stderr、快照、实际由 openpyxl/python-docx 重新读取的六表/DOCX 文字与逐项判定。临时输入和输出运行后清理；JSON 中的临时路径是采集时路径，不是持久交付文件。

## 实际执行与业务数值

- `python docs/qa/wangbin-project-acceptance-check-q02-t03-rerun-probe.py` → **exit 0**；输出的布尔检查均为 true（包含 ZIP 校验、退出码校验）；A01–A11、A13–A14、B01、B02、B04-formula 退出 0；A12、B04-traversal、B04-limit 退出 3；A12-all-bad 退出 2 且 stderr `INVALID_INPUT: no readable material`、未生成完整报告。每案原文文件散列和具体参数见 JSON。
- **D1/A01/A09**：虚构 R01/R02/R03 在 A01 分别 `EVIDENCE_FOUND/NONCONFORMING/NO_EVIDENCE_FOUND`，覆盖 **3/5**；R01 端点/请求参数/返回字段三条件有 interface.md/行1，R02 明确负证据 `deploy.md/行1`，同时保留独立 `NONCONFORMING` 和 `MISSING`，R03 缺培训记录。A09 添加培训记录后变为 `EVIDENCE_FOUND/NONCONFORMING/EVIDENCE_FOUND`，原 R01/R02/R03 ID 不变，R03 缺口标 `RESOLVED` 并引用新证据，R02 仍不符合。六表和 DOCX 都显示正确状态、ID 和来源。
- **D2/B02**：一条“Windows Server 2019 部署说明和培训记录”拆成两个条件；Ubuntu-only 原文使部署子条件 `NONCONFORMING`，培训子条件 `NO_EVIDENCE_FOUND`，主 `NONCONFORMING`，覆盖 **0/2**；独立 `NONCONFORMING` 与 `MISSING` 同时进入快照/六表/DOCX，负证据位置 `deploy.md/行1`。
- **D3/A12**：损坏 ZIP 签名字节的 broken.docx 报 `UNREADABLE_SOURCE`，纯文本 fake.docx 与 PDF 报 `UNSUPPORTED_FORMAT`；有效 scope/test.csv 仍保留，混合退出 3；全坏仅单个 broken.docx 退出 2，不误报成功。
- A02 两条件覆盖 1/2 且 `PARTIAL_EVIDENCE`；A03 同名双版本 `CONFLICT`、`VERSION_CONFLICT`、覆盖 N/A；A04 双 R01 来源分别独立 ID 并列重复冲突；A05 仅文件名 `LISTED_ONLY` 不提升状态；A06 开发声明 `CLAIM_ONLY` 不提升状态；A07 两个相近测试候选都 `PENDING_CONFIRMATION`、覆盖 0/2；A08 未确认新增范围只列冲突不改旧三条；A10 通过/失败相反证据 `CONFLICT` 且双来源；A11 实际 DOCX 表格读到 `scope.docx/表1/行2/列2`；A13 八章节、两张可编辑表、六工作表及快照的逐要求状态/ID/缺口一致；A14 抽取 A01/A03/A07/A10/A11 中全部快照要求、子条件证据位置与冲突位置，逐项验证引用属于给定来源，并核查 XLSX/DOCX 内出现；证据索引的 MD/TXT 行号逐行对原始文字核验、源 SHA 对输入复算一致。未以 JSON 自称而替代文档读取。
- B01 无范围覆盖 N/A、`NO_SCOPE_SOURCE`；B04 目录穿越拒绝（PARTIAL 3）、超过 4,000,000 字节拒绝（PARTIAL 3）、`=HYPERLINK(...)` 在 XLSX 中保留文本且所有单元格 `data_type != f`。源文件未被改动。
- `python -m tooling.products verify --id wangbin-project-acceptance-check` → **exit 0**, `status=PASS`, SHA 与 ZIP 一致；`python -m pytest -q tests/test_project_acceptance_check.py` → **exit 0**, 17 passed / 1 skipped（symlink 创建不可用），第三方 anyio/pytest 弃用警告。开发单测与工厂验证只作补充，不代替上述独立核查。

**结论仅为精确 0.1.2 ZIP/源码的本地隔离场景 PASS，可交经理解除原 T03 阻断并推进 T04 本地复核；不表示正式验收或发布许可。** 若 T04 更动安装包负载须重新定版/重测。真实 symlink 越权、完整恶意 Office/ZIP 宏外链矩阵、输出目录写失败、B03/B05/B06/B07 复杂变体、资源极限、全量逐来源原文语义和 WorkBuddy 真实多轮仍 `NOT_TESTED`；真实 WorkBuddy 安装/运行、平台审核/评测/上架、许可证权属均 `NOT_TESTED/BLOCKED`。本卡没有 push、merge、rebase、上传或发布；没有访问 dev 工作树业务内容。
