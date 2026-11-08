# 光伏项目当前版本清理回执与未关闭门禁

## 边界与读数口径

仅清理光伏预可研及直接关联文件，未删除其他产品文件；未 push、merge、上传、审核、发布或启动 Phase 8。Git 数量和大小取对应提交树的 blob 原始字节；`reports/solar-pv` 和未跟踪恢复件取本地文件实测字节。清理前为原件恢复后、首次历史产物清理前快照；清理后为 `f8ad3ca`（恢复29件被引用证据后的净清理树）及随即工作树读数。后续新增工具/文档与仍在整改的报告源码会改变最终 Git 文件总大小，最终 HEAD 精确读数见本轮最终答复。本回执不将旧阶段的机器通过结论等同于报告视觉或专家签收。

| 指标 | 清理前 | 净清理后（`f8ad3ca`读回） |
|---|---:|---:|
| Git 已跟踪文件数／blob 总大小 | 1,403／732,218,652 B | 1,150／611,702,846 B |
| `reports/solar-pv` 本地文件数／大小 | 1,261／981,008,834 B | 643／589,425,837 B |
| 未跟踪历史恢复件数／大小 | 365／270,983,768 B | 0（49件／44,402,610 B 原字节迁至已忽略的受控目录，其余确认为多余并删除） |
| 本地实际释放字节 | — | 576,617,749 B，排除49件原件的位置迁移 |
| 净移出 Git 当前版本的历史文件 | — | 253件（188件旧目录＋65件旧日志）；Git blob 减少120,515,806 B |
| 删除的废弃源码／测试 | — | 0／0；静态引用及动态入口审计未证实存在可安全删除项 |
| 保留有效 dist ZIP 数 | — | 2（各另存 manifest 与 SHA-256 sidecar；均被忽略且未入 Git） |

## 实际清理与保护

- 首轮从 Git 当前版本移除5个完整旧交付目录共188件、118,489,925 B Git blob；随后从顶层旧回归日志中净删除65件／2,015,451 B 本地字节，其余29件因冻结合同、验收说明或回执引用，以普通新增提交复原原路径和字节；不改写历史。不能把先删后恢复的29件算成净删除。
- 从恢复的未跟踪历史中删除316件／226,581,158 B；原 R2 25件与 v7 24件原字节保留并由 SHA-256 核验后迁入 `.runtime/solar-pv/protected-r2-recovery/`，当前本地仍为49件／44,402,610 B，另有逐文件 inventory。受控 R2 测试 fixture 10件独立留在 Git 中。受保护 R3-final-v5、469字段、89公式及其他产品未移除。
- 从已忽略的 `.runtime/solar-pv` 删除6个经标记的可重建分页实验目录，6份卫生工具回执合计433件／228,981,545 B；保留唯一 R4 v2 审阅候选的 WPS PDF、逐页图和审阅记录。旧 dist 删除15件／455,817 B，仅保留两件当期 ZIP及四个 sidecar。
- 仍保留大型历史材料：R1、R2完整25年案例分别由报告/回归测试读取，封存独立输入及 D3；R3 final-v5 是历史有效版本身份；fee-v4为交易费对照 canonical；Phase3D修复前后案例为财务回归/历史证据；Phase3E根认证和逐年审计材料在冻结验收说明中被引用。`phase7l-synthetic-review` 具有独立三年部分案例说明。未证实无价值的目录不盲删。
- `products/catalog.json` 仍指向已删除的五套历史 dist 候选；这些是旧版本记录而非当前可读包，旧版本归档索引尚未迁移。用户如需离线恢复旧版本，不能从本地 dist 完成；不以当前 ZIP 假冒旧版本字节。

## 验证结果及未完成项

- 当前有效 ZIP 均通过实际 ZIP `testzip()`、成员数、包内 LICENSE、外部 manifest 和 SHA-256 sidecar 校验；`git check-ignore -v` 对两个现行候选均命中 `.gitignore:9:dist/`，`git ls-files -- dist` 为空。
- R3 final-v5 的 `PACKAGE-MANIFEST.json` 全部39个成员按路径、字节数和 SHA-256 读回一致；三份 R3 ZIP 的 `testzip()` 均返回 `None`。这证明现存 R3 本地字节身份，不升级视觉或专业门禁。
- 受控 R2 导出、R3叙事与报告业务语义专项：`71 passed, 2 skipped`，退出0；交易费支付来源专项退出0；交易费现金流专项退出0；财务指标专项 `17 passed`，退出0；图表字体专项 `2 passed`，退出0。完整 L3 未执行。CLI 专项 `8 failed, 39 passed, 3 skipped`：解析路径在本机 Python 环境缺少 `wangbin_document_engine` 时返回 `LOCAL_OPERATION_FAILED`，另有一项旧断言要求入口显示“ 不计算、不联网 ”，但现有入口明确支持计算。CLI文件及解析器未在本次清理中删除或更改；失败不能算回归通过，也不能为使测试绿而弱化断言或伪称测试已通过。R2输入专项曾达到工具超时，没有最终通过回执。
- `tooling/solar_pv_workspace_hygiene.py --check` 实际运行成功；`--clean` 对六个逐项标记的可重建目录产生逐文件哈希/大小删除回执，对已删目录返回 `ALREADY_ABSENT`，受保护 R2 和未标记 R4 v2 不清理。此为已执行的 CLI 行为核验，不冒充新增单元测试。
- R4 v2 的两案 PDF 已通过本地 WPS 实际转换，但111页 AI审阅仍有 ISSUE／UNCERTAIN，专业工程/财务/投资人员未签收，`PDF_VISUAL_REVIEW`、`FOUR_FILE_GATE` 与 `WORKBUDDY_PLATFORM_TEST` 均不能标为 PASS。此时在 `main` 保留 R4 内容展示的源码修改只意味着非发布开发记录。

| 门禁 | 状态 | 说明 |
|---|---|---|
| TRACKED_ARTIFACT_CLEANUP | PASS_SCOPED | 净删除253件，其中最终65件顶层日志经再次引用复核；保留其余证据。 |
| UNTRACKED_ARTIFACT_CLEANUP | 待最终提交复核 | 原件已迁入忽略位置，需确认新源码和本回执提交后 untracked 为0。 |
| DIST_PRESERVATION | PASS_LOCAL_ONLY | 两候选原字节保留、忽略、可解压；不代表平台可安装。 |
| SOURCE_AND_TEST_PROTECTION | PASS_SCOPED | 有效源码/测试/冻结合同/fixture未删；29件证据恢复。 |
| REGRESSION_TESTS | NOT_PASSED | CLI 8项失败，R2输入专项超时；不得宣称全部相关专项通过。 |
| AUTO_CLEANUP_POLICY | PARTIAL | 有可运行的受限卫生工具和本地提交规范；后续仍需逐轮执行，未建立强制 Git hook。 |
| LOCAL_GIT_COMMIT | 待最终提交 | 仅本地提交，不自动 push。 |

本轮删除原因调查仍为**删除原因未确定**，只确认原历史材料集中进入回收站，不归责任何特定 Bot、人或命令。最终提交 SHA 和原始 `git status --short --untracked-files=all` 输出另在最终答复中给出；本文件不虚构尚未执行的回执。
