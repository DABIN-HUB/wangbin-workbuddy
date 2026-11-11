# Phase 7L-R13：公式兼容性专项与有限排版收口

**状态：REVIEW_REQUIRED / PDF_FORMULA_COPY_SEARCH_BLOCKED / 未发布。** 起点为本地 `11408c001abceb8a544d9a51d544c7a325685249`；未更改计算引擎、冻结公式/术语/字段/映射、两案 canonical、原始工作簿、R8—R12 原件或正式 PDF 生成链。R13 是隔离的审阅候选，不是完整版预可研或已获批准的投资方案。

## 1. R12 基线与原件

开始时 `main`、HEAD 为上述提交，工作区无改动。读取了 R12 阶段说明、交付回执、逐页判据、公式文字层和 157 条目录映射。R12 两案各 61 页、各 103 个 U+FFFD（物理 54—58 页为 14/33/27/12/17）。原始生成/经 WPS 保存的 DOCX、PDF、两案四份原工作簿的磁盘 SHA-256 均与 `.runtime/solar-pv/phase7l-r12-reader-review-v4/delivery-receipt.json` 相符；两份 R12 `*candidate.zip` 的 SHA sidecar 及 ZIP CRC 验证通过。现行 `dist` 的 Skill/Connector 两份候选 ZIP、许可证成员及 SHA sidecar 核对通过，仍被 Git 忽略。此处的字节核对不是专业内容验收。

## 2. 数学专项：证据边界

开发侧独立逐个比对两案原始 `initial-docx/` 与 WPS 保存 DOCX 的 6 个 OMML。DSCR、动态回收期、LCOE、NPV、静态回收期的数学文字和相应结构未见保存时变化；`F-IRR-PROJECT` 的第一个数学字符由 **带 script 样式的 `R`** 变为 **`ℛ`**，对应冻结式的花体根集。下标 P、搜索域内求根、`y=0…N` 求和、分式及 `=0` 的可见结构未见丢失；**不能称字符逐字一致**。独立质量审阅指出多字母符号下标和折现幂在 OMML 节点级的绑定存在解释风险，因此仅能确认 WPS 保存过程未观察到新的运算/范围变化；完整数学语义须公式负责人对照冻结定义签审，不把本次静态检查冒充专业通过。`F-UNIT-COST-WP-KWP` 冲突未改。

两案实际 PDF 的 CambriaMath `/ToUnicode` 映射都有 `<0000>` 与孤立 `<D835>`；公式标题可检索，但正文字符损坏，`NPV_b(r_b)` 和 `DSCR_y=CFADS_y/DS_y` 不能按原 Unicode 复制/检索。既有 R11 两式最小复现与本轮 R12 六式 scratch 最小复现一致：对原始可编辑 DOCX 直接 `ExportAsFixedFormat`，以及保存后 `SaveAs(FileFormat=17)`；各独立受控进程上限 75 秒、退出码均 0，两个单页 PDF 各有 103 个 U+FFFD。两接口仍使用同一 WPS PDF 引擎，**不能**作为两个独立渲染器的成功对照；`pdftotext` 不显示 U+FFFD 也不能证明字符正确，其输出丢失/错配数学字符。定位为 WPS 公式 PDF 输出的字体/Unicode 映射路径，未找到兼具 Word 可编辑 OMML 与 PDF 正确复制检索的已验证方案，停止额外试错。证据：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/r12-omml-audit/{audit.json,audit-summary.json,export-evidence.json}`；独立 QA 复核 R12 原件与实际 PDF。

## 3. 有限排版与 R13 单次候选

仅在读者预览显示层处理地面物理 15 页 `550 W`、16 页 `50 V`/`1,000 V`/`1,100 V` 的单位空格，以及公式说明中冻结原文结尾句号与连接分号叠加形成的“。；”（屋顶 57、58 页，地面公式说明同类情形）。不改冻结定义文本。屋顶 31 页财务表密度、地面 42 页续表留白、60 页表 34 续表标识、61 页终页留白未作分页风险不明的调整；资料路径缺失时未编造路径。封面仍保留**本报告内容仅供参考，正式使用时需根据实际情况调整。**

仅生成一次 `.runtime/solar-pv/phase7l-r13-formula-layout-candidate/`；有界 WPS 命令退出码 0。交付回执分别记录原始生成 DOCX、WPS 保存 DOCX、PDF 的 SHA-256。屋顶最终 DOCX `55c04784755ae47edb1db55834a6093665fa751b2719603741e62ab69ff3b58e`、PDF `71667642c35e6bdd0cde580348f86b321c3a5f6f13803b0f05893a734eb19aec`；地面最终 DOCX `ce61884241ec9a6d88c480d1b5548302ae0621efe735a11cee9f2fde1f13f87d`、PDF `081612b1778668f18594fb04682126bdc5ca69f3e493f1fa472a23646958ecab`。两案仍各 61 页、35 表、6 个可编辑 OMML、157 条刷新目录；原两套测算模型与来源工作簿的 SHA 与 R12 逐件相同、canonical 身份不变。与 R12 PDF 对比仅屋顶物理 16/54—58 页、地面 15/16/55—58 页的提取文字有变化，非修复页文字未移动；屋顶 31、地面 42/60/61 页仍是原缺陷。**新两案 PDF 各 103 个替换字符及 `/ToUnicode` 缺陷原样存在**，不得沿用 R12 的逐页视觉判据作 R13 独立签收。

## 4. 有界回归与未关闭门禁

修改后在最终源码执行相关 `test_report_r9_presentation.py` 读者预览/公式导航与 `test_report_word_styles.py` 完整公式结构三组参数化专项：`6 passed, 0 failed, 1 anyio/pytest 弃用警告`，上限 480 秒、真实退出码 0；JUnit 与退出码保留于 `.runtime/solar-pv/phase7l-r13-layout-focused-{junit.xml,exit.txt}`。R13 单次报告生成上限 480 秒、退出码 0，回执于候选目录，退出码 `.runtime/solar-pv/phase7l-r13-generation-exit.txt`。`python tooling/solar_pv_workspace_hygiene.py --check` 上限 90 秒、退出码 0，未跟踪文件 0；未执行全仓 4,609 项回归。完整 89 式 Word 身份未因预览 6 式获批；R12 的全仓回归 `ABORTED / NOT_PASSED` 不提升。真实权属、工程、交易与政策资料、专业审批、正式完整版范围和平台发布仍阻断。

独立 R13 成品 QA 已读回：两案最终 DOCX/PDF SHA 与回执一致，原 canonical 文件 SHA 与 R12 相同；两份 DOCX 的 6 棵数学 XML 树与各自 R12 保存版一致，两案封面免责声明均在 DOCX 和 PDF 保留。新 PDF 的正文标题与刷新目录逐项对应 **157/157**，物理页偏移为 +8。R12/R13 的 122 页去除定点空格、换行和标点差异后，提取文字逐页一致；指定页及近邻共 25 组有界栅格比较，未发现文字越出纸张，屋顶 31 页、地面 42/60/61 页及其近邻像素与 R12 相同。**这只是定点 QA，不是 R13 全部 122 页的独立逐页视觉签审**；旧页级 PASS/PARTIAL 不迁移至新 PDF。独立 QA 建议保留有限排版补丁，但明确公式文字层、数学专业语义、资料、完整版身份及发布门禁仍阻断。
