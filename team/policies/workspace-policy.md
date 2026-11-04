# 工作空间
主仓库 `F:/ideaWorkSpace/wangbin-workbuddy` 只读，用其 Git worktree 登记识别现有目录。严禁四 Bot 读取 `F:/ideaWorkSpace/wangbin-workbuddy-dev` 的业务内容或修改、测试、清理该目录；仅可见 worktree 清单中的路径/分支。团队配置为独立分支 `team/skill-factory-v1` 的 worktree；未来每个产品独立 worktree + 分支，同一产品业务源码同一时刻仅一写入者。分析师仅需求文档写入；QA 只写隔离报告/候选。SOUL 与目录白名单只提供 SOFT_ISOLATION_ONLY，当前账号有 OS 级写权限；没有修改 NTFS ACL。
