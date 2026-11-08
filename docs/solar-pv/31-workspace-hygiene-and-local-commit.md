# 光伏项目：工作区卫生与本地提交约定

本约定仅适用于 `wangbin-solar-pv-prestudy`、`solar-pv-engine`、对应 `tooling/solar_pv_*`、`tests/solar-pv`、`tests/fixtures/solar-pv` 与 `reports/solar-pv`。不得据此删除其他 WorkBuddy 产品。每轮**已验证的**光伏开发完成后执行以下闭环，除非该轮明确只读或被外部阻断：

1. 核对实际分支、HEAD、`git status --short --untracked-files=all` 和已有未提交工作；不覆盖他人修改。代码/文档完成后运行受影响专项验证，失败和超时不计通过。
2. 将中间运行、缓存、日志、DOCX/PDF/XLSX、PNG、临时 canonical 和 ZIP 放到已忽略的 `.runtime/` 或 `output/`；只保留一套有明确身份的本地有效候选。正式不可重建证据、冻结合同、有效 fixture 不按生成物盲删。
3. 运行 `python tooling/solar_pv_workspace_hygiene.py --check`，核对已跟踪生成日志、未跟踪文件、大型报告、潜在重复内容、`dist` ZIP 状态及本轮新增跟踪文件大小。此命令不修改文件，也不自动判定任何文件已废弃。
4. 清理已确认无用途的**已跟踪**历史生成物时，逐项检查生产/测试/Skill/文档引用、原字节证据与重新生成能力；用显式路径 `git rm -- <路径>` 从当前版本和工作区删除，绝不能只靠 `.gitignore` 或 `git rm --cached` 掩盖。对未知用途、封存案例、冻结469字段/89公式及原件保持保护。
5. `.runtime/solar-pv` 下废弃的独立运行目录，只有审核其全量文件后、为该目录写入 `.solar-pv-disposable.json`（内容为 `{"kind":"REGENERABLE_SOLAR_PV_RUN","scope":"<目录名>"}`），才能使用 `python tooling/solar_pv_workspace_hygiene.py --clean .runtime/solar-pv/<目录名>`。工具拒绝工作区根、`.`/`..` 越界、符号链接和 junction、Git 已跟踪文件、受保护 R4 v2 与 R2 恢复原件；逐文件保留哈希、大小和删除回执于已忽略的 `.runtime/solar-pv/hygiene-receipts/`。删除前先写 `PENDING` 记录，目录完整删除后才转为 `DELETED`；异常可核验余下文件并安全重试，目录已不存在但回执仍为 `PENDING` 时明确阻断人工复核。重复清理返回 `ALREADY_ABSENT`。**标记前确认目录没有独立证据或当前有效候选**。
6. `dist/` 保留当前有效本地候选，但通过 `git check-ignore -v <实际路径>` 验证忽略，验证 ZIP、LICENSE、manifest及哈希；只在确认无独立留存需要时删除过期光伏候选，绝不清空其他产品 dist。
7. 仅显式暂存本轮授权的源码、必要配置、合同、fixture、简洁回执和文档，运行 `git diff --cached --check` 并审查暂存清单；创建描述实际内容的**本地**提交（必要时把历史文件清理和工具/规范拆成两个提交），不能用 `git add -A`、`git add .`、空提交或自动 push。
8. 提交后核对 `git status --short --untracked-files=all`、`git diff --check`、`git log -3 --oneline`、`git ls-files`、dist 忽略和受保护案例。报告实际文件数量/字节数变化、释放空间、回归通过数、提交SHA及未完成门禁。代码测试未通过时不能标记为可用；仅在明确标注非发布状态时保存诊断提交。

此约定不触发自动合并、远程 push、WorkBuddy 上传/审核/发布、Phase 8 或修改冻结计算合同；本地代码提交也不等于 R4 报告视觉/专业验收通过。人工专业签收和平台执行各自独立。

## 本轮处理边界

- 首次筛查曾删除已跟踪 `reports/solar-pv/` 顶层94个旧 pytest/JUnit/红绿输出记录；再次逐文件审查发现其中29个被验收说明、冻结追踪表或归档回执引用，立即以普通新增提交**恢复原字节及原路径**。最终净删除65个无仓库内路径/文件名引用的顶层输出；历史验收文字、公式数值证据和被引用的回归原件继续保留。Phase 3B–3E 深层案例/根认证、R1/R2 两套25年原始计算树和交易费来源有独立回归用途，继续保留。
- 旧 R2 25个与 v7 24个恢复原件，经 SHA-256 复核后迁至被忽略的 `.runtime/solar-pv/protected-r2-recovery/`；保留独立 `recovery-inventory.json`。这是本地原件留存，非云备份或新 Git fixture。当前受控10文件 R2 fixture 原样保留。
- 分页试验版本 `phase7l-r4-final`、`final-v3/v4/v5/v6/v8` 经标记后由卫生工具删除；`phase7l-r4-final-v2` 为当前唯一有完整 WPS PDF、逐页图像与待审回执的本地候选，原样保留。其视觉问题未关闭，不得称为正式可用交付。
- `dist` 仅保留本地、已忽略的 `wangbin-solar-pv-prestudy-0.1.3-skill-candidate.zip` 与 `wangbin-solar-pv-cli-0.1.2-connector-candidate.zip` 及各自 manifest/sha256；旧5套光伏候选已经逐一校验并删除，不触及其他 WorkBuddy 产品。
- `products/catalog.json` 中旧版本的 `candidate`/`archive_evidence` 字段仍是历史版本元数据，原旧 ZIP 已不在本地；这些字段不能再解释为当前可用文件。仅两套现行版本可以进行本机 ZIP 读回。目录本身尚未进行旧版本归档索引迁移，相关可用性保持限定。
