# Git 安全与团队推送授权
创建任何 worktree 前检查路径、分支、worktree 登记、可信 base commit 和主仓库未提交改动。禁止切换主仓库分支，禁止 fetch/gc/worktree prune/reset --hard/clean/rebase/强推。仅显式列举文件 git add，检查 diff、提交范围和秘密后本地 commit。

每个 Skill 必须使用独立 worktree 和独立产品分支。阶段开发、QA 修复或必要验收证据通过必要检查并成功本地 commit 后，允许自动向该产品对应远程分支执行普通 `git push`；首次推送使用 `git push -u origin HEAD`。该授权不需要逐次用户确认，但只适用于当前产品分支，不得覆盖其他产品分支。

push 前必须核对实际 HEAD、工作区、remote、分支和跟踪关系。push 冲突、权限异常或远程状态异常时保留本地和远程原状并报告，不执行 reset、改写远程历史、force push、merge、rebase 或删除分支。禁止自动修改 main/master。不得因 Git push 授权上传、审核、发布、部署 WorkBuddy；继续保留既有许可证、ZIP、SHA-256 和历史证据，不得访问或干扰光伏工作树。
