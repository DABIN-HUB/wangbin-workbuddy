# 交接格式与检查
完成卡必须包括 product_id / task_id / workspace / branch / base_commit / result_commit / changed_files / artifacts / verification_commands / verification_results / blocked_reason / residual_risks。目录与哈希必须是真实值；没有改变提交时 result_commit 写 NOT_APPLICABLE。命令与退出码照实记录，未执行项 NOT_TESTED。下游读取 parent handoff 前验证相应文件与提交存在；同一产品只允许一个业务写入者。每次失败保留证据与阻塞理由，不重放不确定的写操作。
