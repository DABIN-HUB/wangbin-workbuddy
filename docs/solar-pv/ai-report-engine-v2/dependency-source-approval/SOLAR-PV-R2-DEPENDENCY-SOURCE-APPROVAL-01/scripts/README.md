# 本任务审计脚本

这些脚本不是产品运行代码，不包含构件下载/安装/打包ZIP动作，不需要新依赖。使用已确认的 `F:/ideaWorkSpace/wangbin-workbuddy/.venv/Scripts/python.exe`（CPython 3.12.0、packaging 26.3）；不能用缺少 packaging 的 Hermes Python 代替。

## 输入与身份

- `INPUTS.json`：原输入胶囊路径/size/SHA、177件数量、来源 HEAD。
- `locktool.py` 内置该胶囊 SHA 信任锚；胶囊每件还核 SHA/size。胶囊含公开原元数据的联系字段，**LOCAL_ONLY**，不得直接分享。
- 原图12目标/全部42缺失集合、原wheel binding、43官方release JSON（backend另2）/121 PEP658字节、license/document/resources/runtime输入均冻结；大 JSON 与执行快照只留 RUN。
- `CANDIDATE_LOCK.json` 是正式精简入口，所指 `RUN/candidate/CANDIDATE_LOCK.full.json` 才是完整机器候选（schema `solar-pv-dependency-candidate/1`）。不把兆级生成 JSON 入Git；正式入口绑定其路径、大小、完整SHA和下载计划。
- 完整 schema 字段：43 `nodes`、去重 `metadata_variants`、115 `files`、12 `targets`（marker环境、逐节点metadata_id/file_id/gap/parents/active_extras、全部声明及求值边）、`input_identities`、`backends_separate`、dual document身份、counts和门禁。

## 调用（经回执包装器；不是联网安装代码）

仓库根工作目录。下面 `<...>` 必须替换为**新输出路径**或已冻结实际输入；不能覆盖历史候选。实际命令回执在 RUN/commands/developer-*，`record_command.py` 的 `--input` 保留执行前原字节。单次 timeout≤120秒；developer累计220秒、全任务1200秒含失败。

```text
<absolute-python> -I -B <RUN>/record_command.py --role developer --label <unique-label> --timeout 45 --input <DOC>/scripts/locktool.py --input <RUN>/frozen-inputs.json -- <absolute-python> -I -B <DOC>/scripts/locktool.py generate --inputs <RUN>/frozen-inputs.json --candidate <new-output>

<absolute-python> -I -B <RUN>/record_command.py --role quality --label <unique-label> --timeout 45 --input <DOC>/scripts/locktool.py --input <RUN>/frozen-inputs.json --input <candidate> -- <absolute-python> -I -B <DOC>/scripts/locktool.py validate --inputs <RUN>/frozen-inputs.json --candidate <candidate>
```

`generate` 独占创建；`validate` 退出0仅表示**研究候选完整性**，输出 `VALID_RESEARCH_CANDIDATE_NOT_INSTALLABLE`，不代表独立QA、实际构件hash、许可、闭包、安装或WorkBuddy通过。拒绝退出1并提供最多30个差异路径；原输入损坏则非零异常，不能降级为PASS。

验证时不信候选自己的图、flags、source、hash或marker。每次从冻结原始元数据重新解析官方filename/name/version、Requires-Python、标准GIL/ABI/platform/tag/条件OS，按exact filename+URL+SHA去重，重求Requires-Dist/extras/marker固定点，再逐类型/字段/键全集与候选比对。删边、删节点、改target marker或metadata引用也会被拒绝。没有预置负向结果；正式负向变异/回执由独立quality执行，不能把作者自检移植成QA。

`build_delivery.py` 为本轮一次性生成器：只创建本任务正式文档和RUN/candidate派生计划，已经存在的文件拒绝覆盖；保留英文许可义务原文以避免翻译放宽。它不修改PLAN、生产源码或旧报告；后续正式审查收口由唯一writer定点编辑，不复跑以覆盖原件。

`freeze_review.py` 只创建显式允许的目录payload和外置冻结index，**从不封ZIP**。含原/新SHA与必要脱敏身份；选定129批准源码、185来源派生和逐项许可证据，拒绝路径越界/重复，不复制cache/env/raw/二进制。`--revision <path-free-label>` 可独占保留失败预检，空revision才写正式 `developer-freeze-index.json`。末次QA后新增文档/证据必须新payload并限定复审；不能把旧scope的结果迁移。

阶段本地commit与保护读回另由RUN里的有界脚本记录，避免自引用commit循环；不允许push/merge/reset/rebase。正式首目标仍未确认，所有再分发许可/依赖闭包/安装/实际宿主门禁保持原状态。
