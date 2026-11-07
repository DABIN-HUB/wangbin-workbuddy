# Q06 FIX-6 · 独立开发前预冻结（非产品 QA PASS）

- `product_id=wangbin-tender-analyzer`；`task_id=q06-fix6-evidence-first/Q0`；工作树 `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；分支 `skill/tender-response-check`；写前本地及远端 HEAD `4fe1e9cd4bc88fc608c6af19e3b788fc4f42fed5`，业务脚本 `packages/skills/wangbin-tender-analyzer/scripts/check_response.py` blob `468a06be4f50cf45d21940daa3a05c8052d9747c`。分析合同三份 SHA-256 分别 `1c62e43487ab69427a882a3a96cc994880b293dd70764df762a5c85bf1e81323`、`24277bb430db6cda0371980aae8bf33dfcd4b020c811a34e7fae0b7ab41bbc6f`、`56426e34d9c1ad4a9ca4fd757b1b884bbb6defac58e404e20bb5b45493b75dd0`，**在任何业务源码变更前先单独提交** `4d2cb6c1023096937bb06bbfccdc714338d97e4f`（仅三文档）。
- 独立冻结 `qa-fix6-prefreeze-cases.json`：15 个机制变体，UTF-8 原文/逐义务来源/四维 expected/确定缺口或人工确认/MD 分区；SHA-256 `1b5163a58173b2382b9020b569d8526c7232814b84c0cba35372ee8707448109`。`qa-fix6-prefreeze-sha.json` 对 36 份实际 fixture 逐文件锁 SHA；清单 SHA-256 `0ed79b688e2b631d8c7d4d177df43a85e90e0a2c7b6d3cb491cd6903a722e74e`；`qa-fix6-prefreeze-materialize.py` 只在文件不存在时物化及复核，不导入业务代码/不运行 CLI。**不得重新物化覆盖、编辑 expected、用程序实际结果改期望。**
- V01/V02/V03/V04 分别检验未知、现况否定加未来计划、仅未来计划缺现况、现况正控；V05/V06 交换同对象矛盾的正反顺序及编号；V07/V08 交换跨对象来源、故意制造编号撞车以证事实按对象隔离。V09/V10 是缺证照正文两种语序，V11/V12 为仅标题与部分摘录歧义，V13 为明确正文正控，V14 为同一材料正文正反矛盾，V15 限已给材料缺文件；未沿袭 FIX-5 原句。每个 expected 均独立于被测程序 actual，不能以全 UNKNOWN 伪过。

## 新 ZIP 后续独立判定方法（本 Q0 未运行）

1. 核对该候选精确 ZIP/manifest/sidecar/成员、ZipFile CRC 和源字节，再在质量角色 scratch 干净解压，仅执行 ZIP 内 CLI 且移除 `PYTHONPATH`；逐案核对清单 `inputs` 每个 SHA，保存 argv/cwd/exit/stdout/stderr、两产物 SHA。五份既有失败源输入/真实输出、原 53+FIX-3 13+FIX-4 16+FIX-5 12 的全部**94 项旧输入/expected**，错误五项及成功正控、旧 `analyze_tender.py --input` JSON 快照必须保持不变、全部重验；旧 0.2.10 结果 53/53、13/13、16/16、7/12，整体 `LOCAL_QA_FAIL`，不能被 Q0 改名为通过。
2. 成功案必须 exit 0 恰生 `{项目}-投标响应检查.xlsx` 与 `{项目}-提交前核对清单.md`；重新打开 XLSX，sheet 顺序严格 `核查概览 / 要求响应矩阵 / 附件核对 / 补遗与版本 / 待确认事项`。矩阵每个 tender 义务恰一行，按 JSON `rows` 原顺序比较四维；要求编号不等于响应编号（不可仅凭编号强绑定），`source` 对应 `来源`，`response_sources` 必在 `响应位置`，`excluded_sources` 不得出现在该行的响应位置/响应内容/事实理由中。对冲突不只是位置列两行：矩阵响应摘录/判定理由、待确认事项、MD 必须呈现肯定和否定两边原句或可审计摘录及两个真实源行；行号必须为原文件 1-based。
3. `gap` 非 null：矩阵缺口写明事实而非空泛提醒，`来源` 含本义务 tender 行，`响应位置` 或 `证据位置` 含触发反证；MD 同义务位于“确定需要补资料（已提供范围）”及“未覆盖范围（仅已提供材料）”，不得进入“已覆盖范围”；该行不得仅以待确认替代确定缺口。`pending` 非 null：矩阵原因、待确认表与 MD“需要人工确认”必须包含义务及原因/触发来源、人工动作；不得列入确定缺口或已覆盖。`md_section=已覆盖范围` 仅对应当前明确肯定，无冲突且无缺口。MD 每个义务仅入适当区，不把多对象混为同一对象。
4. 材料案 `evidence_sources` 逐项在矩阵 `证据位置` 及所绑定的 `附件核对` 行材料行证据中出现；文件存在必保持“已提供（可读文本）”，同时**单独**判断支持。V09/V10 附件和矩阵都“不支持（文本层面）”并引用明确反证 L2；V11/V12 均待确认不推定否定；V13 内容支持且四维为正控；V14 两侧正文冲突均待确认且双源行可见；V15 未提供仅指已提供范围，内容未核验，不断言企业无证。补遗表在无正式替换关系时不生成虚构替换。概览四维各状态计数须逐维等于矩阵实际计数、每维合计等于义务数；检查单元格非公式及无私有绝对路径。
5. 旧错误探针：缺回应、非法 UTF-8、不支持 PDF、损坏 XLSX 目录、输出路径逃逸仍应 exit 2、对应 `ERROR <CODE>` 且无貌似成功的两产物；成功正控 exit 0 生两产物，旧入口 JSON 精确快照相同。所有本次变体、旧 94 项、错误正控和旧入口全部满足才能在新 ZIP 实测后给**本地有限** QA PASS；本次尚无 ZIP 及 CLI 实测，不宣称平台运行、许可证/相似性审核或发布。

## 冻结证据及风险

FIX-5 原 `qa-fix5-0210-{independent-report.md,fresh-predeclared.json,independent-results.json,independent.py}` SHA 依次为 `e7f8bb2e09bc2cba9a8f7fbdab6ad01c1e75babbd416ea97a8d84fffd698dd75` / `b9bfcc519934afd18ad65ae48c98c476ab3cea8ea8fe78fba8cfb69ecb78bca2` / `a7886ea08aba45199332a8477f24ed9f5bc518af6db48de138d1fa4a56e90656` / `0a9c6989fd29e34e8b4aa64281141bc694c343d652b9c8ef8518a03b5fc47bdc`；五失败 F01/F02/F04/F05/F08 原文件及真实 XLSX/MD SHA 已重算，与 `fix6-acceptance-cases.md` 逐案相符。原 F04 XLSX 将肯否双方位置列出却只取肯定摘录且覆盖；F08 已提供文件 L2 缺正文却输出待确认；这些失败为真实阻断而非预期调整。

Q0 仅文档/独立 QA 预冻结：开发实现、下一版精确 ZIP/业务输出、宿主/WorkBuddy、授权许可证/相似性/发布 `NOT_TESTED`；仅限文本证据不认证物理证书或法律效力。后续开发绝不可改上述冻结原件或以词交集虚假覆盖。此报告中提交/远端状态以交接 metadata 的实际 read-back 为准。
