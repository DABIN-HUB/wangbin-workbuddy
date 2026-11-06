# Q04 T03-RERUN-1 独立 QA：0.1.1 本地候选 PASS

- product_id=`wangbin-meeting-action-tracker`; task_id=`t_14e21282`; workspace=`F:/ideaWorkSpace/wangbin-workbuddy-meeting-action-tracker`; branch=`skill/meeting-action-tracker`; base_commit=`bad64254669b072475d4ffd50f6792a50fb2dd3f`; source_commit=`f774349c7e405ef4c7486357801d0bd54a5d4006`; result_commit=见本报告的提交。只对新版 0.1.1 作独立结论；旧 0.1.0 FAIL 报告与证据原样保留。
- 0.1.1 ZIP SHA-256=`5f5f0bc86ca469c89d758010194d8768e27badc96584791495e4b71c8ef745ae`，与 sidecar 逐字和 manifest 摘要相符；ZipFile.testzip() 返回 None，成员集合/大小/SHA-256/源文件字节一致，干净解压后调用包内 `track.py`。ZIP 内 `track.py` SHA-256=`95a253c224fd2c16c41c452ec2053d6223572cf6ff8c2a5737f703c1a1f16a7d`；源码文件 git blob `c9bf21be6797c1547eb55491c0998bc26f666fa9` 与源提交对应 blob 一致。工厂 verify 返回 PASS/exit 0。旧 ZIP SHA-256 仍为 `e9ce10c7979bdd510e08b20e1bb877fc28f7e66ef437c05b5e1a19117c0eac20`。
- `python docs/products/wangbin-meeting-action-tracker/qa/independent_rerun_0_1_1.py` → exit **0**，47/47 PASS（历史独立探针 38 条在新版干净解压重新运行，加 9 条新版专项）；逐案 `qa-evidence-0.1.1.json` 列明 expected/actual。新探针调用历史探针的测试逻辑但替换候选路径，**不执行其旧版写证据入口**，新增专项为独立虚构输入及断言。每案使用独立输出目录，实际重开 XLSX 四表及表头。历史 0.1.0 两项 FAIL 均未被编辑或改判。

## D1 修复复验与合同回归

输入旧 CSV：T01 整理演练清单/王工确认/2026-11-05/进行中，T02 准备演练培训/待执行；会议 `2026-11-06 蓝桥演练例会。T02 经会议明确取消，原因：模拟需求撤回。新增事项：检查演练接口 T03；建议由李工负责，尚未获其接受。`。实际 T02=`取消`，逾期=`否`，取消事件原值=`待执行`、新值=`取消` 且有来源；T01 不因未提及而变更，新事项的负责人不伪造已确认。三个对照逐项另跑 `T02 拟取消，尚未最终决定。`、`T02 考虑取消，尚未最终决定。`、`T02 建议取消，尚未最终决定。`：T02 均保持待执行，无取消事件，各有待确认项。旧版把“模拟”误作“拟”的 D1 在此候选上未重现。

原独立 38 项重新实跑覆盖 MTG-A02–A14：新增确认、同字节/重排幂等、区分相似事项、负责人变更、会议日期相对期限、缺基准、口头完成/后补证据、双顺序冲突、取消/重开、逾期、单句、范围内补充、损坏 DOCX/格式/CSV/空会议错误；另有 DOCX 输入、错误返回码、重复 ID、不覆盖既有输出、公式注入单元格、明确更正与负责人提议、仅按显式要求生成未发送草稿，六句中英推荐问法在 SKILL/冻结需求逐字匹配。旧 CSV 和新版专项 CSV 的 SHA-256 前后均相同；输出四表用 openpyxl 重开且检查列。原探针断言粒度与 `qa-evidence-0.1.1.json` 一致，不推断未覆盖的变体。

命令：`python docs/products/wangbin-meeting-action-tracker/qa/independent_rerun_0_1_1.py` exit 0；`python -m tooling.products verify --id wangbin-meeting-action-tracker` exit 0；`git rev-parse HEAD` → 基线提交；`git diff f774349c7e405ef4c7486357801d0bd54a5d4006 bad64254669b072475d4ffd50f6792a50fb2dd3f -- packages/skills/wangbin-meeting-action-tracker` 无差异（该两提交间 catalog 候选索引确有更新）；`git diff --check` exit 0。旧版报告 SHA-256=`2e09f3c220184af7e9429060449c4b21bf014bd68cdb18218a20ecf20e896886`，旧证据 SHA-256=`1b33ab6ab63f6acf3f6b14f953c098bc0b33d6fedaea85889ed4244403e3639d`。

**门禁范围**：只允许 T04 对该精确候选作本地复核，不代表 WorkBuddy 平台运行/模型效果、真实依赖环境、许可证与权利、相似度、发布通过；上述均 NOT_TESTED。自然语言其他未抽样表述、资源上限、压缩炸弹/恶意 OOXML、跨平台权限与原子故障注入仍是风险。本轮未 push、不部署、不上传。blocked_reason=null（本地候选 QA）。
