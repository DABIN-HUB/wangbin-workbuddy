# Phase 7L-R12：两案读者预览报告定点整改与独立复核

**状态：REVIEW_REQUIRED / 未发布。** R12 v4 是审阅候选，不是正式投资批准、完整版 L2/L3 交付或 WorkBuddy 平台发布。最终两案 PDF 共 122 个物理页的独立 180 dpi AI 图像审阅为 **106 PASS、16 PARTIAL、0 FAIL**（屋顶 51/10/0、地面 55/6/0）；这些是逐页原始判定，不能冒充真人专业签收。两案的数学公式 PDF 文本复制/检索均 **BLOCKED：各 103 个 U+FFFD**。内容/资料/方法负责人及发布门禁仍阻断。

## 1. 基线、候选、不可变边界

- 起点 `27408546e143e699bead90c4cb0cb59592793c10`，原始 R11 v10 `.runtime/solar-pv/phase7l-r11-reader-review-v10/`、默认完整版 `.runtime/solar-pv/phase7l-r11-default-full-guard-v10/` 均未覆盖；历史 R8—R11 与 `dist/` 原件保留。R11 的逐页原始依据为 `qa/v10-per-page-independent-image-verdicts.json`，原判 **6 FAIL、21 PARTIAL**。R12 v1—v3 是中间试排，不是当前最终候选。
- 最终读者预览四文件与证据仅在 `.runtime/solar-pv/phase7l-r12-reader-review-v4/`；`delivery-receipt.json` 登记最终 WPS 保存 DOCX/PDF、原两工作簿的逐件哈希。未重算 canonical、未修改 469 字段、89 冻结公式、281 映射、189 术语、原始财务数字和来源 Excel。源代码只改 `services/solar-pv-engine/src/wangbin_solar_pv/report_export.py` 的读者展示与分页；默认完整 Word 模式另行守护。
- 屋顶 canonical `result_hash=ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f`；地面 `result_hash=69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138`。`qa/v4-canonical-five-identity-readback.json` 重新从原 canonical、模型 M01 第 2—6 行与来源 S01 第 3—7 行逐项比对五字段，两案均一致。附录 M 的读者页只是索引，**不包含 Word 内完整五值**。

| 类型 | WPS 保存的读者 DOCX SHA-256 | WPS PDF SHA-256 / 物理页 | 原测算模型 / 原来源清单 SHA-256 |
|---|---|---|---|
| 工商业屋顶 | `f9f30b404861e1e21e112fb4402195d1ddcd2f447b9cec07a68fa209020b77c2` | `191903d0fe49071dd52d556928d1e5904b1c6faa79412c3140ac5bd534e06b9f` / 61 | `09aa27780264a11ceb187b6248c488668deadba46758b1e971d796e24f93a3ff` / `d028575c517b74ffd1800451cd5be03ead95a57439e100546b570528c9656cdb` |
| 集中式地面 | `ece13f91ccb89a2f210e0e5e06d6c31ea24c541cf1d2a5612843fd7c13fdbc74` | `906c520dd76f865091945c9de7dc3c8ce9d71191830c51f30b48fa87a690b34a` / 61 | `39e32eba13ea3259dc0a8d89104b153b0d9e80e239be780edf60107801c50c51` / `c4694fb461c07d3b6122872102dea7b8713debee2165b0787a65a40f3c8a31f4` |

两份读者 DOCX 均为 18 章、13 附录、157 个有效标题/刷新目录项、35 表、6 个可编辑 OMML；DOCX 到 WPS 保存前后表形状与单元格文字不变。表 7 的 GHI/DNI/DHI/POA 辐照单位统一置于题注，消除四个窄表头对 `kWh/㎡` 的折断；表 14 的计划付款日期以 `YYYY.MM.DD` 同单元格连续显示。正文的 `2052 年 12 月 31 日`、面积单位与两位百分比已从真实 PDF 图复核；读者版未显示 `APP06.01`，两案封面均逐字保留“本报告内容仅供参考，正式使用时需根据实际情况调整。”。图像图题改为同页，章节和短附录分页仅在 reader_preview 调整，不缩字号、不删 126 个子项、不改稳定身份。

## 2. R11 全部 27 个遗留页逐项归因与 R12 落点

下列**物理页码**按两份实际 PDF。映射使用 R11/R12 对应页面的文字四字组相似度定位候选页，随后逐页检查最终 R12 的真实图片；近邻页也在完整 122 页审阅中覆盖。原问题、修复边界、复核方法及 PDF/页面 SHA 见 `qa/r11-v10-issues-to-r12-v4-candidate-pages.json`，**不能由自动相似度自身推出视觉 PASS**。下表 R12 是图像可读性判定，不表示内容证据关闭。

| 案例 | R11 页/原判及问题 | R12 v4 对应页/图像判定 | 修复或保留界限 |
|---|---|---|---|
| 屋顶 | 9 PARTIAL `25/年` 折断 | 9 PASS | 数字单位显示与页内排版 |
| 屋顶 | 12 FAIL `2052-12-/31` | 11 PASS | 正文日期改连续中文表达 |
| 屋顶 | 13 FAIL `3,000/㎡` | 12 PASS | 面积与单位同排可辨 |
| 屋顶 | 27 PARTIAL 计划表密集 | 23 PASS | 表 2 分页且表头重复，23—24 均复核 |
| 屋顶 | 30 FAIL CAPEX 短尾 | 25 PASS | 章节不再强制逐章起页 |
| 屋顶 | 67 PARTIAL 附录 M 仅给索引 | 61 PASS（**内容仍阻断**） | 五项实际值另于 canonical、M01、S01 核对；预览 Word 仍不满足完整版身份合同 |
| 地面 | 9 PARTIAL 数值单位紧贴 | 9 PASS | 常用单位显示调整 |
| 地面 | 10 PARTIAL 阶段建议独页 | 10 PASS | 章节自然续排 |
| 地面 | 12 FAIL `2052-/12-31` | 11 PASS | 日期可读，12 页第二次出现亦复核 |
| 地面 | 14 PARTIAL 辐照数值单位 | 13 PASS | 行内空格 |
| 地面 | 15 PARTIAL 温度风速及留白 | 14 PASS | 资源单位修正，章间流转 |
| 地面 | 16 PARTIAL 容量/距离单位 | 15 PARTIAL | 原处部分改善，但 **550W** 仍缺空格 |
| 地面 | 18 PARTIAL 第七章短尾 | 16 PARTIAL | 孤立短尾已消；**50V/1,000V/1,100V** 仍缺空格 |
| 地面 | 21 PARTIAL 第八章短尾 | 19 PASS | 章间自然衔接 |
| 地面 | 26 PARTIAL 表 2 密集 | 23 PASS | 六列表头和五任务同行页完整 |
| 地面 | 29 PARTIAL CAPEX 孤页 | 25 PASS | 与 OPEX 自然衔接 |
| 地面 | 39 PARTIAL 表 10 仅起始 1—4 月 | 34 PASS | 先排 1—9 月，35 页续表 |
| 地面 | 40 PARTIAL 表 10 续页留白 | 35 PASS | 重列表头和 10—12 月，无漏行；尚无独立续表题注 |
| 地面 | 51 PARTIAL 股东现金流缺结果 | 46 PASS（**内容仍阻断**） | 仅可读，股东现金流独立结果仍缺 |
| 地面 | 53 PARTIAL 独立敏感性缺结果 | 48 PASS（**内容仍阻断**） | 仅可读，情景未执行 |
| 地面 | 54 PARTIAL 政策未获外部核验 | 49 PASS（**内容仍阻断**） | 原文文号/有效期等仍待证 |
| 地面 | 55 PARTIAL 权属/工程/交易缺证 | 50 PASS（**内容仍阻断**） | 真正资料仍待补 |
| 地面 | 56 PARTIAL 索引非完整公式审定 | 51 PASS（**范围仍阻断**） | 预览 6 式不替代完整版 89 式 |
| 地面 | 59 PARTIAL DSCR 释义跨页 | 54 PASS | 公式和表 28 清晰，54—55 连续审阅 |
| 地面 | 60 PARTIAL 式 3 符号表下页 | 55 PASS | 公式、续表可辨；不据此宣称 PDF 复制通过 |
| 地面 | 62 FAIL NPV 式后大量留白 | 57 PASS | 公式 5/表 32 清楚，后接公式页 |
| 地面 | 63 FAIL 回收式孤立短尾 | 58 PASS | 公式 6/表 33 后附录 L 同页起始 |

R11 六个 FAIL 对应页在 v4 图像均为 PASS，27 个原问题对应页为 **25 PASS、2 PARTIAL、0 FAIL**；整份 v4 仍有新/不同问题导致 **16 个原始逐页 PARTIAL**，不能用“旧缺陷已闭合”替代全本真实结论。屋顶第 8 页在 v3 一审曾误判为第 7 页重复；二审看两张不同图片核实实际为附录 K—M 目录，原始初判保留为已纠正的审阅记录，v4 独立图像仍按自身判定。

## 3. 数学文字层阻断、最小复现及完整范围隔离

`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wps_omml_repro.py` 只在 scratch 中抽取 R11 实际可编辑 OMML 的 DSCR、NPV 两式，附普通文本、窄表日期/单位对照，经 **WPS 12.0** 保存并分别用 `ExportAsFixedFormat` 和 `SaveAs(FileFormat=17)` 输出真正的一页 PDF；两种方式均出现 **26 个** U+FFFD。复现 JSON：`.../scratch/wps-omml-r11-probe/evidence.json`。OOXML 数学对象保存后仍在，但实际 WPS PDF 的 CambriaMath 子集 `/ToUnicode` 包含 `<0000>` 与孤立的 `<D835>` 映射。最终 v4 两案 `qa/r12-v4-wps-formula-text-layer.json` 各在物理 **54—58 页**测得 **14、33、27、12、17**，总计各 103；实图六式可辨，**不能因此宣称数学字符能正确复制、搜索或语义已复核**。WPS 保存时 `F-IRR-PROJECT` 的数学文字与初稿存在变动，仍应专业核对。未将公式转图片、未伪造隐藏层、未更换正式 WPS PDF 输出链。`F-UNIT-COST-WP-KWP` 方法冲突仍待负责人裁定。

默认完整版另由最终源码重新导出到 `.runtime/solar-pv/phase7l-r12-default-full-guard-v4/`，两案各读回 **89 个正式公式 ID / 89 个可编辑 OMML、189 条完整词典行和 Word 五身份原值**；屋顶 DOCX SHA `ff65dacf8ef578c311c22cd54d49ccd9e1c893b7bbae4d0f43b211482ad468b9`，地面 `e2f2e6b43758e664b1622ec1feef8ce18dcf2a58e0ac5ce150d11857f78037ab`。这只是本地 Word 结构守护，内容版本仍 `phase7l-r10-reader-review`，**未**经 WPS 导出完整版 PDF、未独立审核 89 式数学语义或获得正式范围批准。读者预览的 35 表、6 式、短词表和附录 M 索引绝不冒充已满足完整版 Word 合同。

## 4. 最终页级复核与剩余缺陷

最终原图 `.runtime/solar-pv/phase7l-r12-reader-review-v4/qa/{industrial_rooftop,utility_scale_ground}-180dpi/page-001..061.jpg`，每条 verdict 与 PDF SHA、图像 SHA、独立审阅原始轨迹对应于 `qa/v4-per-page-independent-image-verdicts.json`。生成栅格图不等于逐页签审；本轮两案 **122 页全部**重新审阅。最终正文 157 条刷新目录各自逐一与实际 PDF 标题物理页比对，屋顶/地面均 **157/157 对应**，证据 `qa/v4-toc-vs-actual-pdf-pages.json`。屋顶目录 3—8 页审阅者因单张图无法证实落点而标 6 个 PARTIAL，保留原始判定及上述另行页码核对，不以文字检测改写其图像原判。地面封面一审的 PARTIAL 涉未定义的“单列法定提示”充分性；实物有用户指定完整提示且 PDF 可检索，原判保留，不据此声称法律专业签认。

- 屋顶原判 51 PASS / 10 PARTIAL / 0 FAIL：除了目录六页的落点待外部定位，31 页表 4—6 稍密、32 页索引仅工作簿号缺文件定位，以及 57—58 页两处可见“。；”重复标点。图 1/2 与各自图题同页；物理 38 页表 14 日期连续。
- 地面原判 55 PASS / 6 PARTIAL / 0 FAIL：物理 1 页为上述法律提示充分性疑虑；15—16 页数值与 `W/V` 空格仍未规范；42 页表 20 续表只有五行导致下半页留白；60 页表 34 两行短尾且无续表题注；61 页终页较短。以上没有被涂改成 PASS。地面第 30 页表 3 原来就是**五列**，v3 审阅误以为必须有第六列；v4 重新图像检查五列均可读，不接受未授权的第六列验收条件。
- 专业与资料阻断独立保留：合成资料不是实际权属、结构荷载/地勘、接网批复、交易结算、工程量报价、政策生效依据；股东现金流、独立敏感性和部分成本/偿债指标无可用结果。封面日期、预排任务日期须由真实项目负责人确认其时点一致性；不得把图像视觉 PASS 写成投资结论。

## 5. 回归、仓库卫生与交付状态

最终源码专项命令：`WANGBIN_SOLAR_PV_PANDOC=<本地pandoc-3.13> PYTHONPATH=services/solar-pv-engine/src python -m pytest -q tests/solar-pv/test_report_*.py tests/solar-pv/test_phase7l_r2*.py tests/solar-pv/test_app06_full_annual_bridge.py --junitxml=.runtime/solar-pv/phase7l-r12-reader-review-v4-focused-junit.xml`。退出码 0；实读 JUnit **226 tests = 220 passed、6 skipped、0 failures、0 errors**，耗时约 594 秒，`anyio` 一项弃用警告。v3 先前 216 pass/4 fail 是被取代的中间候选回执，四个年度标签空格断言已修正并在 v4 专项复跑，不可掩盖历史失败。**全仓回归 ABORTED / NOT_PASSED**：收集到 4609 用例，运行约 3.12 小时仅推进至 56%，实时输出已出现 `F.EEEE..F`，但未生成最终 JUnit，故无法确认这些失败/错误对应的具体用例或最终总数。因已异常耗时且已出现失败/错误，人工停止进程，随后核对父子进程均已退出。不能把前 56% 或专项回归替代全仓通过；后续须按失败模块隔离复现并单独治理，不能将此作发布门禁 PASS。

`python tooling/solar_pv_workspace_hygiene.py --check` 已运行：无未跟踪文件、无本轮已暂存变更、无可清理标记；报告列出的历史大文件/日志不能未经引用核查擅自删除。原 `dist/wangbin-solar-pv-cli-0.1.2-connector-candidate.zip` 与 `dist/wangbin-solar-pv-prestudy-0.1.3-skill-candidate.zip` 的 ZIP 完整性、许可证成员、manifest 和 SHA sidecar 均读回匹配，仍被 Git 忽略。不自动 push/merge/rebase/发布/部署/上传；全仓回归终止及上述阻断未关闭，**不把当前候选标为验收完成或发布就绪**。未完成的人类专业签收、PDF 公式文字层和正式预览/完整版范围批准继续标为 BLOCKED。
