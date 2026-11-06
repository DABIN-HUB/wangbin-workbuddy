# Q05 T04｜0.1.3 本地候选封装复核（非发布批准）

- `product_id=wangbin-report-consistency-check`; `task_id=t_44fad71d`; `workspace=F:/ideaWorkSpace/wangbin-workbuddy-report-consistency-check`; `branch=skill/report-consistency-check`; `base_commit=27602df5eb32b22430507741b4fca021d9a09f05`；本报告及附随探针提交的完整 `result_commit` 见 Git 日志与看板交接。
- **唯一放行的 QA-PASS 候选**：`dist/wangbin-report-consistency-check-0.1.3-skill-candidate.zip`，SHA-256 `549111865465d3feb9faf5aaedf69738be6efd48094b1f61dd127e0b29ed9b38`。仅本产品 0.1.3 ZIP；不是 WorkBuddy 安装包兼容性或平台准入结论。旧 0.1.2 ZIP 及其独立 QA FAIL 证据原样保留，不能混作 PASS。

## 工厂和包来源

在本产品独立 worktree 下实际运行：

| 命令 | 实际退出/结果 |
|---|---|
| `python -m tooling.products validate --id wangbin-report-consistency-check` | exit 0，status PASS，findings 空 |
| `python -m tooling.products verify --id wangbin-report-consistency-check` | exit 0，status PASS，返回精确 ZIP SHA-256 |
| `python -m tooling.products release-check --id wangbin-report-consistency-check` | exit **1**，status **BLOCKED**；local_validation/local_tests/archive/local_candidate PASS；平台安装/对话/审核 NOT_TESTED，许可/依赖 BLOCKED，相似性人工审查 REVIEW_REQUIRED，publication BLOCKED。工厂在此命令调用的产品局部测试为 12 passed、1 skipped（未设置 `REPORT_CANDIDATE_ZIP`），有 1 条 pytest 警告。不能将工厂局部测试等同独立 QA 或发布检查通过。 |
| `uv run --no-project --with openpyxl --with python-docx python docs/products/wangbin-report-consistency-check/local_candidate_probe_0_1_3.py` | exit 0；下述成员、静态文本及干净解压实跑断言全部通过 |

探针 `local_candidate_probe_0_1_3.py` 在 QA 通过后独立复核：ZIP 实际 SHA、`ZipFile.testzip()`、无重复/越界成员、sidecar、manifest 中 id/version/status/每成员大小与 SHA，以及对应源文件字节 SHA；四个解压后成员与 manifest 一致。manifest payload snapshot SHA-256=`6ead35080726785e13309d3420fa13f1e089d9951596ad1fc103ea561daff0d4`（工厂 verify 验证快照）；`products/catalog.json` 只有一条本产品记录且 `active_version=0.1.3`、该版本 candidate 路径和 SHA 精确匹配；仍为 DEVELOPING、非 PUBLISHED。四成员：

| 成员（前缀均为 `wangbin-report-consistency-check/`） | SHA-256 |
|---|---|
| `SKILL.md` | `0b05bc65ddd9b256081583683b7e8d5f14561bc68cb67dbf5ce63f5882682882` |
| `manifest.json` | `11e7d15ae0a04a3315db3854d8a15d08df8b8267e1f4b1f04ae28b494c5cc676` |
| `scripts/check_report.py` | `7e1cc8d84afb40780696b0112a2c5f0a92ab1df9d3d129d8e0e86cba3c6bb334` |
| `templates/context.example.json` | `a4134427363c6e7821fdd58fe6cae451a2e8c711dd8c6ca4c37408d5f43de49e` |

## 干净解压的实际虚构样本

探针在开发者私有 scratch 创建临时目录、干净解压上述精确 ZIP，只运行解压后的 `scripts/check_report.py`；用 openpyxl 生成含 `数据!B2=1280000`、表头 `青禾公司6月实际未税收入/CNY/元` 的 XLSX，用 python-docx 生成 `青禾公司6月实际未税收入125万元` 的 DOCX，context 明确 `exact=true`。输入根和独立输出目录均实际存在，执行 CLI exit 0；其真实状态为 **PARTIAL**（有一条未覆盖信息），不是全报告已审计；差异状态 MISMATCH、报告减来源 `-30000` 元，溯源 `数据!B2`。输出 XLSX 用 openpyxl 重开，五表按序为 `核查概览/指标对应/差异明细/待确认口径/未覆盖项`，无公式单元格；DOCX/XLSX/context 输入哈希前后相同，输出目录仅产生 XLSX 和 snapshot JSON。虚构样本在 scratch 完成后清理，未进入 ZIP 或仓库。独立 QA 已在同一精确 ZIP 上从干净解压运行 44/44 案例与五表逐格重开（`qa-report-0.1.3.md`、`qa-evidence-0.1.3.json`；该 QA 的原始内容/旧 FAIL 证据未由 T04 修改）。

## 展示、推荐、参数和限制

静态比对同版 `SKILL.md` 与冻结 `requirements.md`：中文三句及英文三句推荐问法逐字一致，中文/英文展示名和简介均存在；catalog active_version 为 0.1.3；脚本及 SKILL.md 均标出四个必需参数 `--input-root`、`--source-xlsx`、`--report-docx`、`--output-dir`，两个可选参数 `--context`、`--prior-run`。第三句重传推荐仅做静态核对，真实 WorkBuddy 多轮对话 **NOT_TESTED**；不得将字符串一致性解释为模型理解能力。manifest 标 `license_status=NOT_VERIFIED`，缺少已核实的许可声明；仅打包携带 `runtime` 描述，不宣称 WorkBuddy 运行环境已具备依赖。

## 门禁与剩余风险

`LOCAL_CANDIDATE_READY` 仅对以上 SHA 的本地候选和虚构数据 PASS；`WORKBUDDY_TRIAL_READY`、`PUBLISH_READY` **NOT_VERIFIED/BLOCKED**。WorkBuddy 平台安装、真实 Skill/六句模型对话、权利/依赖许可、相似性人工审查、平台审核、上传与发布 **NOT_TESTED**（工厂相似性仅 REVIEW_REQUIRED）。旧版失败案例中的跨币种和冒牌 OOXML 已在 0.1.3 独立复验通过，但旧开发测试中仍有历史错误码断言，QA 明示其直接运行失败；同源增量补映射、加密文档、symlink 越界、输出权限/逃逸、网络监测和资源极端值均未完整独立覆盖。此次**不修改 QA 已测试的四成员源文件、catalog、ZIP、manifest 或 sidecar**，不覆盖旧候选、不 push、不上传、不发布。任何后续载荷改动需升版本并重新独立 QA。`blocked_reason=null`（仅本地复核无阻；发布门禁仍阻断）。
