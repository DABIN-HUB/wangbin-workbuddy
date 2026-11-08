# Git 安全与团队推送授权
创建任何 worktree 前检查路径、分支、worktree 登记、可信 base commit 和主仓库未提交改动。禁止切换主仓库分支，禁止 fetch/gc/worktree prune/reset --hard/clean/rebase/强推。仅显式列举文件 git add，检查 diff、提交范围和秘密后本地 commit。

## 所有 Skill / Expert 的文件归属与停跟踪门槛
- **A 必须跟踪**：源码、SKILL.md / Expert 配置、冻结需求/输入输出合同/验收条件、自动化测试与 QA 脚本、固定输入/expected 和回放必需 fixtures（即使扩展名为 PDF、DOCX、XLSX、ZIP 或 JSON）。按内容和引用判定，不按扩展名一刀切；保留已有版权及历史候选。
- **B 生成物不作为源码跟踪**：实际运行输出、QA 原始结果/证据包、候选及历史 ZIP 与 sidecar/manifest。对已跟踪 B，先在产品隔离的历史/失败证据目录归档，若目标同名先比较哈希、不得覆盖；读回 SHA-256、ZIP CRC 和 manifest，确认原有自动回放路径可用、已验收候选和历史失败证据无损，再仅对逐件确认的路径执行 `git rm --cached -- <精确路径>`，保留工作树原件。语义未明、混合输入输出或被脚本引用的文件先列 B-review 暂缓，不得误删 A。新增 `.gitignore` 仅限已核实的生成物规则，用 `git check-ignore -v -- <A路径>` / `git ls-files -ci --exclude-standard` 复查不会屏蔽 A；忽略规则不使已跟踪文件自动停跟踪。
- **C 可验证缓存**：可重建且确认非唯一证据的 `__pycache__` / `.pyc` 等缓存。先确认来源及引用，避免把必要 fixtures 或回放材料当缓存；未跟踪缓存不需要 `git rm --cached`。T00 只读审计 `reports/six-git-t00-audit.md` 和逐路径账本位于六 Skill 交付区，列明 Q01 历史 ZIP 引用、Q03 旧 QA 输出、Q06 混合 input/output ZIP 等暂缓案例；该审计仅为规则佐证，不是批量停跟踪授权。

## 每次提交与远端核验
在**当前授权产品** worktree 先执行 `git status --short --branch`、`git diff --name-status`、`git diff --cached --name-status`、`git ls-files -- <产品路径>`，必要时核对忽略中的跟踪文件；识别其他任务 dirty、已暂存和本地领先提交。仅对已批准的精确路径 `git add -- <路径1> <路径2>`（停跟踪按上文逐路径 `git rm --cached`），禁止 `git add .` / `git add -A`、宽泛目录暂存及混入他人改动。提交前逐项核 `git diff --cached --stat`、`git diff --cached --check`、`git diff --cached --name-status` 及内容/秘密；按 `docs(<scope>): ...`、`fix(<scope>): ...` 等规范 scope 写独立提交，记录完整 commit 哈希、实际测试和未测项。QA FAIL 可在隔离位置备份证据及失败 ZIP 并保留 SHA/来源，但绝不可进入 qa-passed 候选、冒充通过或发布。

每个 Skill / Expert 必须使用独立 worktree 和独立产品分支。阶段开发、QA 修复或必要验收证据通过必要检查并成功本地 commit 后，允许自动向该产品对应远程分支执行普通 `git push`；首次推送使用 `git push -u origin HEAD:refs/heads/<当前分支>`（仅当精确远端分支不存在，建立同名 upstream）。该授权不需要逐次用户确认，但只适用于当前产品分支，不得覆盖其他产品分支。push 前核对实际 HEAD、dirty、remote、分支与跟踪关系，使用 `git ls-remote --heads origin refs/heads/<当前分支>` 查精确远端 HEAD（空输出只表示尚无精确分支），核对待推提交列表及其授权范围；存在非本轮/未授权 ahead 提交时先报告并暂停 push，不通过改写或跳过提交规避。推送后再次读取该精确远端 HEAD，对照本地完整哈希；未推送或无法核验标记 NOT_VERIFIED，不以本地 upstream 推断成功。

分别记录 `SOURCE_COMMIT_PASS`（必要源码与固定输入已精确提交）、`GIT_PUSH_PASS`（普通 push 退出成功且精确远端 HEAD 等于本地完整哈希）、`GIT_HYGIENE_PASS`（生成物/缓存跟踪与可回放性）、`LOCAL_QA_PASS`（实际本地测试）和 `WORKBUDDY_PUBLISH_READY`（独立平台发布门禁）；不得互相代替，未执行记 `NOT_TESTED`。卫生例外或 QA 失败不无条件阻断必要源码提交及 push，但不能据此声称卫生、QA 或发布通过。任何**新提交**仍须精确范围暂存并检查 cached stat/check/name-status、内容及敏感信息；不得新提交候选 ZIP、实际输出或缓存。已在本地祖先中的旧构件，须审查待推历史的秘密、隐私、真实客户及禁止上传内容，记录旧构件路径、当前 HEAD 与遗留卫生风险；确认非敏感且待推提交获授权时可普通推送，不以卫生 PARTIAL 为由一概禁止，也不改写历史。疑似敏感或来源无法确认则停推并上报，不强推。自动 push 使用明确目标 `git push origin HEAD:refs/heads/<当前分支>`（首次按上文加 `-u`），完成后必须精确核验远端引用；发布另行授权与验证。

push 冲突、权限异常或远程状态异常时保留本地和远程原状并报告，不执行 reset、改写远程历史、force push、merge、rebase 或删除分支。禁止自动修改 main/master。不得因 Git push 授权上传、审核、发布、部署 WorkBuddy；继续保留既有许可证、ZIP、SHA-256 和历史证据，不得访问或干扰光伏工作树。
