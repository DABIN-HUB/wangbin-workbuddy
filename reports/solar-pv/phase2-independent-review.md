# Phase 2 独立审阅与缺陷闭环

审阅日期2026-10-29；只读审阅子任务deleg_e7a3d15f，前置HEAD 0fe02688cefe5a2e3f851a8aa27bbb3261b3c74f。审阅本身未执行测试，发现基于代码调用链；动态复现及修复由主任务另外执行，不能将只读审阅冒充运行验收。

## P1：已失效的VERIFIED候选回选复活（已关闭）

原调用链：intake._invalidate_context仅降级活动values；provenance.resolve_conflict从历史candidates深复制原VERIFIED；完整度将其视为可靠输入。公开API依次提交SITE-A/GRID-A→人工review→改SITE-B→提交GRID-B产生冲突→选原VERIFIED候选，可恢复旧站址核验状态。

实际RED：phase2e-context-red.txt记录4条公开/底层/旧history/直接候选重放回归确实失败在VERIFIED≠UNVERIFIED；另一个嵌套测试最初用了不存在的roof.faces，随后依真实目录改resource.monthly，未改变期望行为。其构造还暴露数值序号unit=null无法通过Intake的问题，按冻结定义允许无物理单位的月份整数，拒绝伪造单位，不猜度量单位。

修复：

- 保留candidates历史记录原样；失效事件显式记录当时受影响candidate_ids及字段。
- register_candidate与resolve_conflict共享_activation_record；候选曾失效则只在激活副本中将容器与逐原子VERIFIED降到UNVERIFIED、移除reviewer，不替换原数值或历史许可。
- 兼容旧Phase2D无candidate_ids的失效事件，以history先后关系判断而非用户可控日期；新人工review生成新候选可保留重新核验状态。
- 站址/分类变更同时登记已移除字段的历史候选、全部site/资源/接入/负荷/电价/政策及实际分类专属字段，防止只覆盖活动values或遗漏非roof前缀分类。
- source_snapshot包含context_invalidations，失效依据进入快照/hash，不仅留在不参与摘要的旁支日志。

验证：phase2e-context-green.xml先验证984项相邻路径；最终phase2-final-junit.xml含7项上下文/单位回归（公开Intake、底层resolve、register重放、旧history、单独新review、嵌套数组、非法序号单位）全通过。最终全部新测试3014 passed/0 failed/5 skipped，跳过原因单列。未删除旧断言或放宽完整度标准。

## 其余审阅结论与限制

审阅覆盖来源、Intake、完整度、解析、安全、CLI及序列化；未发现另一项同等确定的新重大问题，不以此保证无缺陷。Windows强制资源隔离/目录竞态、无OCR/复杂表格、symlink权限、输入限额等为公开未关闭边界，不能宣称已经修复。本地输入验收不提升发电、财务、四文件、真实项目、平台或发布门禁。
