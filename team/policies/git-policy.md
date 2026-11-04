# Git 安全
创建任何 worktree 前检查路径、分支、worktree 登记、可信 base commit 和主仓库未提交改动。禁止切换主仓库分支，禁止 fetch/gc/worktree prune/reset --hard/clean/rebase/强推。仅显式列举文件 git add、检查 diff 与秘密后本地 commit；默认不 merge/push。已有 ZIP、哈希、版本和历史证据不可覆盖。
