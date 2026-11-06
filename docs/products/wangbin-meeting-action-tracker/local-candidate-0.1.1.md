# Q04 T04 — 0.1.1 本地候选复核与评测草案

- product_id=`wangbin-meeting-action-tracker`; task_id=`t_7acd844c`; workspace=`F:/ideaWorkSpace/wangbin-workbuddy-meeting-action-tracker`; branch=`skill/meeting-action-tracker`; base_commit=`f73006cd00cb8a2f8a92c5ab96dcfcad882f1651`; result_commit=以本报告的提交哈希为准。
- 独立 QA 门禁：`t_14e21282` / `independent-qa-0.1.1.md` 在精确 ZIP SHA-256 `5f5f0bc86ca469c89d758010194d8768e27badc96584791495e4b71c8ef745ae` 上 47/47 PASS；0.1.0 `e9ce10c7979bdd510e08b20e1bb877fc28f7e66ef437c05b5e1a19117c0eac20` 为历史 QA FAIL，不能交付为通过候选。此次仅在 QA 后追加本目录探针与报告，**不修改包内内容、原有 sidecar/manifest 或 QA 证据**。
- 候选：`dist/wangbin-meeting-action-tracker-0.1.1-skill-candidate.zip`；同名 `.zip.sha256` 和 `.zip.manifest.json`；三成员 SHA-256 分别为 SKILL.md `07a6ee5e23ec7d534fd08416c39166c7db2b4b93d7360d18a194787010033c90`、manifest.json `3fda62f1bc062b1dbeae32dce51575e6a09c51ba13f94cab72bd8854d65a632c`、scripts/track.py `95a253c224fd2c16c41c452ec2053d6223572cf6ff8c2a5737f703c1a1f16a7d`。三个成员大小/摘要/源字节相同，ZIP CRC 全检无错；manifest `status=PASS` 仅表示本地包完整性，`platform=BLOCKED`。
- 版本/目录：SKILL 前置元数据和包内 manifest 均为 `0.1.1`；产品 catalog active_version=`0.1.1`、status=`DEVELOPING`、review_status=`NOT_TESTED`，保留旧 `0.1.0` 历史版本索引。三条中文与三条英文推荐问法逐字对齐冻结需求和 ZIP 内 SKILL.md。Python 3.11+ / `openpyxl` / `python-docx` 需目标运行环境另外核实。

## 实际运行与范围

在产品 worktree 执行：

1. `python docs/products/wangbin-meeting-action-tracker/candidate_probe_0_1_1.py` → **exit 0**：从原 ZIP 干净解压至隔离临时目录，对虚构会议及旧 CSV 运行 ZIP 内 CLI（`--meeting-file meeting.md --previous-tasks previous.csv --project-name 蓝桥演练 --response-mode export --output-dir out`）→ CLI exit 0；重新打开 XLSX 为 `当前任务`、`本次新增与变化`、`待确认事项`、`状态历史`，数据行数分别 3/3/1/3；T02 取消并有取消事件，T01 维持进行中；CSV 原始 SHA 前后相同；本地包/成员/目录与六句推荐语均断言通过。此脚本不写 QA 证据，临时输入/输出退出时销毁。
2. `python -m tooling.products verify --id wangbin-meeting-action-tracker` → **exit 0**，`status=PASS`、上述 0.1.1 SHA-256。
3. `sha256sum dist/wangbin-meeting-action-tracker-0.1.1-skill-candidate.zip dist/wangbin-meeting-action-tracker-0.1.0-skill-candidate.zip` → **exit 0**，精确匹配本报告两值。

## 后续评测草案（不是平台提交格式）

- 上传前在获授权目标 WorkBuddy 试运行时，另测安装和两项依赖可用性，再运行冻结 `acceptance-cases.md` 的 MTG-A02–A14、§17.7 D1 明确取消及真实提议对照；用输入 SHA、返回码、四表原文件及事件溯源逐项记证。当前独立 QA 结论只适用于本地 Python/ZIP，不可替代模型处理或平台包识别。
- 建议逐项记录：输入类型与明确假数据标识、预期/实际状态迁移、未提及旧项不变、建议负责人未接受、日期/逾期缺值、重导入幂等、冲突/错误返回码、四表可重开及安全边界；是否由官方平台允许的评测结构承载，需要平台实际 schema 核验。
- WorkBuddy 平台/模型/安装依赖：**NOT_TESTED**；许可/依赖权利/平台协议：**NOT_TESTED/BLOCKED**；跨产品源码相似度：**NOT_TESTED**；上传、发布：**NOT_TESTED/BLOCKED**。恶意 OOXML、极限资源、跨系统原子失败与未采样自然语言均是残余风险。未 push、未上传、未发布；本地候选完整性通过不构成平台认证。
