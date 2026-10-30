# Phase 3C 独立只读审查与父任务复现记录

## 范围和证据资格

独立审查批次 `deleg_329d4c67`：只读核验本轮 `generation_evidence.py`、`tariffs.py`、`revenue.py` 链；不改代码、不作提交、不运行数值算例。原始审查指出两项 P1 核心正确性缺陷，不能把子任务状态 completed 当作验收 PASS。父任务随后实际复现并修复；未修改冻结公式、469 原始字段或 Phase 3B 发电模型。

另一个批次 `deleg_77282d3e` 是九原子内核的代码实施，并非独立全链验收。其 497 项专项已由父任务另行复验，见 `phase3c-kernel-parent-review.md`。

## P1-1：春季跳时边界漏检价格变化

- 复现：`America/New_York`；2026-03-08 01:30:00−05:00 至 03:15:00−04:00，真实持续 45 分钟。两条价格规则分别覆盖 00:00–02:00、02:00–24:00，价格不同。
- 原因：只枚举墙钟规则端点；不存在的 02:00 被时区往返校验剔除，遗漏实际 UTC（Coordinated Universal Time，协调世界时）偏移跳变。
- 风险：整段按起点旧价格计算，造成收入偏差。
- 修复：检查起点、结束前一微秒、真实墙钟规则边界和实际偏移跳变；没有子时段电量证据时返回 `TARIFF_INTERVAL_CROSSES_PRICE_CHANGE`，不按时长伪分配电量。
- 证据：本轮 scratch 的 `review-red.xml` 保留真实失败；`review-green.xml` 为修复后组合；最终完整候选回归另行汇总，不用专项数代替全量数。

## P1-2：新增或替换资源与固定 3B 物理来源冲突

- 原因：仅比较上游已有的输入键，遗漏当前新增的物理资源及 D3（有界本地时序包）资源身份。固定 3B 结果哈希只能证明指定结果的完整性，不能自动证明另一份资源与之相容。
- 父任务首次复现：全年 3B 源配新增 24 小时内联资源仍被接受；`source-mismatch-red.json` 保留该现象。修复后 `source-mismatch-green.json` 实际返回 `GENERATION_RESOURCE_INPUT_CONFLICT`。
- 修复：校验新增物理字段、既有物理方法、内联资源或每个 D3 资源数据集的 canonical（规范化）内容哈希及原始 header/source（头部/来源）元数据；结算专用包可新增负荷或价格，不要求整个包哈希等于旧发电包。
- 进一步真实反例：同一 header、同一 8,760 行、仅将一条原 1,000 W/m² 的合成辐照记录改成 900 W/m²，生成完整合法 D3 包，再调用冻结候选的公开屋顶计算 API（Application Programming Interface，应用程序编程接口）。实际返回 `GENERATION_RESOURCE_INPUT_CONFLICT`，未发布结果，失败创建的输出目录已清理。原发电数据未改。
- 该反例证据：本轮 `adversarial-source-v1/acceptance.json`、`resource-conflict-final1.log`、`verify_resource_conflict.py`；正式归档位置由最终执行证据给出。

## 父任务当前结论

两项实际缺陷已修复且有真实反例阻断证据，不再是未处理阻断。两类 25 年合成案例已完成真实 API 与 CLI（Command-Line Interface，命令行接口）计算，结果内容哈希一致，并以不调用本轮生产消纳核的 Fraction（精确有理数）算法核对。8,760、8,784、35,040、35,136 行的完整消纳数值容量案例也已分别通过独立参考。

本记录不代替最终完整光伏回归、旧产品含 Expert 回归、持久证据复制核验或提交后保护校验。整轮正式结论以 `phase3c-review-and-acceptance.md` 和 `phase3c-final-execution-evidence.json` 为准；在这些闭环完成前仍为 PARTIAL（部分完成），不宣称发布通过。

## 保留边界

- 本轮全部业务案例为 SYNTHETIC（合成数据），不是实测企业、实际工程、真实政策或商业授权证明。
- 更换年份等沿用 3B 已声明的等效时序情景；本轮同区间均值电量匹配不是实际更换日期或区间内部瞬时负荷事实。
- 逻辑预算与进程内存采样不是 Windows 操作系统硬隔离。
- 投资、折旧、融资、现金流及后续财务指标仍未实现，不自动进入 Phase 3D。
