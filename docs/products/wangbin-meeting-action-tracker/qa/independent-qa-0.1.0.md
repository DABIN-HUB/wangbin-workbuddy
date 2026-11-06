# Q04 T03 独立 QA：0.1.0 候选 **FAIL**

- product_id: `wangbin-meeting-action-tracker`; task_id: `t_e573aad9`; workspace: `F:/ideaWorkSpace/wangbin-workbuddy-meeting-action-tracker`; branch: `skill/meeting-action-tracker`; base_commit/tested source commit: `0e01c1bc063ad05a1d67f6d53d4ada57cb8c1927`; result_commit: 见本报告提交的 Git commit；changed_files: 本报告、`qa/independent_probe.py`、`qa/qa-evidence-0.1.0.json`。
- 固定候选：`dist/wangbin-meeting-action-tracker-0.1.0-skill-candidate.zip` SHA-256 `e9ce10c7979bdd510e08b20e1bb877fc28f7e66ef437c05b5e1a19117c0eac20`；内含 `scripts/track.py` SHA-256 `52f29ebee99c8fdb6e7dbf01fc05df8f9b0c68b89c1a63ea89391652c5fd8cc3`。ZipFile `testzip()`=None，3 个成员路径/大小/SHA-256 均匹配 manifest 与源码，sidecar 摘要一致；在临时独立目录解压并调用 **ZIP 内脚本**，没有调用产品源码。版本 0.1.0；不覆盖候选。
- 命令/退出码：工作目录本产品 worktree；`python docs/products/wangbin-meeting-action-tracker/qa/independent_probe.py` → **1**，38 个独立断言中 36 PASS、2 FAIL；脚本用 `sys.executable` 按各例构造 `python <clean-extract>/wangbin-meeting-action-tracker/scripts/track.py --meeting-file <fixture> --project-name 蓝桥演练 --response-mode export --output-dir <new-empty-dir> [--previous-tasks <old.csv>]`，每例临时隔离并重开 XLSX。逐案预期/实际在 `qa-evidence-0.1.0.json`；测试代码内给出完整虚构原文、CSV 行、各模式参数及执行断言。`sha256sum` 对候选/源/证据 → 0；`git rev-parse HEAD` → 0，源如上。Python `3.14.9`，openpyxl/python-docx 在本地可导入，确切包版本 NOT_TESTED（当前虚拟环境 `python -m pip show` 返回 1，未以猜测填写）。

## D1 / 阻断：明确取消误判成“仅提议”

**重现**：旧 CSV 表头与 `input-output-contract.md` 当前任务表头一致，两行 T01=整理演练清单/王工已确认/进行中/截止 2026-11-05，T02=准备演练培训/待执行；会议 MD 原文 `2026-11-06 蓝桥演练例会。T02 经会议明确取消，原因：模拟需求撤回。新增事项：检查演练接口 T03；建议由李工负责，尚未获其接受。`；不传 `check_date`，按上述命令导出，打开 `当前任务`、`待确认事项`、`状态历史`。**预期**：T01 不变、T02 执行状态=取消且取消事件留原值待执行/新值取消/来源；T02 不在逾期未完成项；新事项负责人建议而非已确认。**实际**：CLI 返回 0，四表可重开，但 T02=`待执行`、最近变更=`无新增进展`、逾期=`无法判断`，无取消事件；待确认事项错误写 `T02 经会议明确取消，原因：模拟需求撤回` 为“仅为取消提议”。新增项建议状态及 T01 保留通过。报告中 `CORE old/new proposal` 与 `A11 missing check date and canceled` 两项 FAIL 均是同一根因，不虚增为两个独立缺陷。源码 `apply()` 取消分支以 `re.search('考虑|建议|拟', segment)` 将普通词 **模拟** 内的“拟”当成提议；应限定否定/提议词的语义位置，而不是全句子串。原始 ZIP 与历史证据均保留；禁止把未修版本称为合格。

## 已覆盖的正例和边界

独立 ZIP 调用覆盖 A02 已确认负责人、新任务与来源；A03 同字节重导、双任务重排稳定 ID/event；A04 相似但不同对象；A05 负责人更换原/新值；A06 明天按会议日换算；A07 缺基准待确认；A08 口头完成 vs E-7 证据及旧历史；A09 两顺序的相互冲突；A10 取消后明确/仅考虑重开；A11 明确核查日的 T01 逾期；A12 一句回复；A13 E-9 仅作用 T02；A14 假 DOCX、错误后缀、无效 CSV、空会议均返回代码 2 与相应状态且 CSV 哈希不变。DOCX 文本输入、四表次序/表头和重开、公式文本不生成公式单元格、建议人不覆盖已确认负责人、明确期限更正、重复旧 ID、输出已存在不覆盖、显式草稿及六句推荐问法的静态逐字匹配均实测。CSV 旧表 SHA-256 前后相同。失败的 `A14 invalid CSV` 首次运行是夹具误把 CSV 当 meeting-file；已修正**独立 QA harness** 并重跑，本次最终结果该例 PASS；未篡改生产实现或历史测试。

## 未覆盖/剩余风险

§17.7 最小核心 FAIL，**本地候选不得流转 T04 为 QA PASS**。未全面覆盖模糊任务多候选、所有日期/时区输入、资源极限/压缩炸弹、跨系统文件权限/原子替换故障注入、恶意 OOXML 关系与真实外联、模拟网络探针。安全单元格仅抽样公式前缀。自然语言抽取依赖启发式，边界外表达另需测试。真实 WorkBuddy 模型/平台运行与审核、目标端依赖、许可/权利核验、跨产品相似度及发布：**NOT_TESTED**，不因本地通过而推断合格。无 push、无安装/发布。修复必须升级不可覆盖候选版本，重新交付新独立 QA，而非修改此冻结 ZIP、源历史或本报告。
