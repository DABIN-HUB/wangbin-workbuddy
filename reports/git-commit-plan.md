# 首次 Git 提交方案（只提供命令，不执行）

项目 `F:/ideaWorkSpace/wangbin-workbuddy`；`main`，目前零提交、无暂存内容。Git 工作区与安全分级细节见 `git-review.md`。本阶段**不提交、不推送、不发布**。下列命令仅供本人审阅决定后复制运行。

## 建议加入

- 基础：`.gitignore`、`README.md`、`pyproject.toml`、`requirements.txt`、`requirements-dev.txt`。根工程 `1.0.0` 仅用于工具链；用户产品 wheel 的元数据以 `services/document-engine/pyproject.toml` 中的 `1.2.0` 为准。
- `services/document-engine/`：MIT 许可证、构建元数据、CLI 与引擎全部 `.py`（包括 JSON IPC、私有输入快照、跨进程锁、Excel 资源限制和无覆盖导出）。
- `packages/skills/`、`packages/connectors/`、`packages/experts/`：候选 Skill/Connector 的原始清单、资源和参考说明以及历史模板；Expert 模板 `author.email` 已替换为非个人示例地址。初次打包所需成员均在源码区，两个 1.2.0 ZIP 能从这些文件重新生成。
- `tooling/`：校验器、Phase 1/2 归档工具与 `phase3_packager.py`，干净源码树没有旧 `dist/` 时照样能构建并记录 `phase2_artifacts_available=false`；本机有 1.1.0 三个旧包时会逐项比对原 SHA-256，不覆盖历史。
- `tests/`：全部真实格式夹具、已有回归、`test_phase3_security_limits.py` 八个新增真实回归及生成夹具脚本；没有必要新增测试依赖。
- `docs/`、`reports/`：Phase 1/2 历史验收与许可证清单、六份 Phase 3 历史报告、`git-review.md`、本方案。旧测试输出留原样，旧 wheel 哈希已标为失效，**不要将旧哈希用于发布清单**。报告是脱敏的文本证据，不是公开用户数据仓库。
- `.github/workflows/phase3-cross-platform.yml`：供本人在真实 macOS/CI 环境后续验证，**首次提交若推送到配置了 Actions 的仓库可能自动触发跨平台 CI**；现在没有 CI/macos 执行记录。
- `.github/workflows/phase3-pypi-publish.yml`：仅手动 `workflow_dispatch`，本轮未触发；首次提交前必须由本人决定是否立即纳入。即使纳入，未配置受保护 `pypi` Environment/受信 Publisher 且未完成安全与许可证审查时**绝不能手动运行**。如不想将发布按钮提交到仓库，请从下方 `git add` 命令删掉此单个路径，其余源码重建不受影响。

## 建议继续忽略，不要强制加入

`dist/` 下旧/新 wheel、ZIP、清单和 `.sha256`（仅本地产物；可从提交中的源码重建新的 1.2.0 候选，历史 1.1.0 二进制不是现有源码的可再生输出）；`.venv/`、任意虚拟环境、`__pycache__/`、`.pytest_cache/`、`*.pyc`、egg-info、`services/document-engine/build/`、`.runtime/`、`output/`、`reports/raw/`、`tests/fixtures/generated/`、日志和 IDE 文件。**不要执行 `git add -f dist/`**；`output/` 可能含用户文件，不作发布附件。已审查的 129 个候选文件均小于 1 MiB，无需要入 Git 的被误忽略源码；新增两份报告后预期为 131 个文件，以临提交前 Git 输出为准。

## 可复制命令（本轮均**未执行**）

```bash
cd F:/ideaWorkSpace/wangbin-workbuddy
git status
git diff
git diff --cached
git ls-files --others --exclude-standard
git add .gitignore README.md pyproject.toml requirements.txt requirements-dev.txt services/ packages/ tooling/ tests/ docs/ reports/ .github/workflows/phase3-cross-platform.yml .github/workflows/phase3-pypi-publish.yml
git diff --cached --check
git diff --cached --stat
git diff --cached
git status
# 人工审阅每个暂存文件、报告、许可证与敏感信息后，且只有本人决定提交时：
git commit -m "feat: initialize wangbin WorkBuddy toolkit and document engine"
```

不建议 `git add .`，避免意外纳入日后产生的隐私文件；不要用 `-f` 强制添加忽略的包。不要执行 `git push`、`git reset`、`git checkout` 或 `git switch` 作为本方案的一部分。

## 重建、许可与发布边界

首次提交中的 `services/document-engine/` 与 `tooling/phase3_packager.py` 足以重建 wheel，`packages/` 与打包器足以重建 Skill ZIP/Connector ZIP；从干净源码复制到 scratch、无 `dist/`/虚拟环境实际运行了 `uv build` 与打包器，三项 package-structure 检查和 sidecar 校验均通过。**最新** wheel SHA-256 为 `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa`；Skill ZIP 为 `38133ee51a91db38091032c60ecb4b84db9e3c63e9953307575b13b7a649de2f`；Connector ZIP 为 `be64b3b619382cbc74686fef6bd64a402f15f380487bde61e41620df66feb0e7`。这些是**本地候选**，不在建议 Git 提交文件内。如果再次改动任何包输入，应重建并重新计算三份实际 SHA-256，不能复制本报告的旧值。

静态扫描未发现待加入文本中的真实凭据、非示例邮箱或大文件，但人工审查仍必需。`SECURITY_PASS=BLOCKED`（Windows/Excel OS 硬资源、进程树、权限边界等），第三方许可证/NOTICE 未全部核实；WorkBuddy 没有真实安装/端到端验收，可信公开分发不存在。提交源码**不是**授权发布或宣称安全通过。其他门禁及实际 Windows/Linux 结果以 `git-review.md` 为准。
