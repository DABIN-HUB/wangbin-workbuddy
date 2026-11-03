# P2-4B/C 回归编排规则的当前执行证据

- 本目录为新规则的**快速验证与历史数据核对**，不是新一轮 L3、不是当前候选的 L2-from-L3 正式覆盖证书；不重复运行长时 E2E 或求根。
- `collection/receipt.json`、`output.log`：当前候选关联 L2 仅收集、未执行；60 个带参数后缀的测试 node ID，exit 0、gate 0。无 JUnit，因为没有运行测试。
- `fast/receipt.json`、`junit.xml`、`output.log`：与上述收集同一运行前后代码／测试／配置 SHA-256，64 passed、0 failed/error/skipped，pytest exit 0、gate 0。
- `affected/receipt.json`、`junit.xml`、`output.log`：价格选择 17 passed、0 failed/error/skipped，pytest exit 0、gate 0；**执行时回归工具尚未加上最后的归档审计／证据搬运逻辑**，其工具身份与本目录 `collection`、`fast` 不相同，不能合并成同一候选 L3 证书；底层财务生产代码、测试均未因此修改。
- `historical-overlap.json`：复核已归档 P2-4B/C L2／光伏 L3 的真实 XML 内容哈希，60/60 个 L2 ID（含参数）均在旧 L3 中，记录旧 L2 墙钟 `15332.98` 秒；结论明确仅为 `HISTORICAL_ID_MATCH_ONLY`。未针对当前工具改动执行 L3，不能因此填发新候选覆盖证书、已实现的加速或新的 L3 PASS。
- 每次运行的 `receipt.json` 内保存实际 Python／pytest 命令列表、退出码、耗时、源码输入 SHA-256 清单和环境指纹、日志 SHA-256、JUnit SHA-256 与 skip 明细。最初运行目录位于独立 scratch；本目录是其原始文件字节复制，不在仓库中保存 pytest 临时工作区。
- 原 P2-4B/C 正式结果仍为非数值 `BLOCKED_MISSING_INPUT`；没有修改冻结公式、D2/D3 或正式结果 Schema。
