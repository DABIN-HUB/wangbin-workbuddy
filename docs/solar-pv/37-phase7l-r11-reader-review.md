# Phase 7L-R11：读者预览版定点收口（未发布）

状态：**REVIEW_REQUIRED / 非正式 L2/L3 交付；PDF_VISUAL_REVIEW=PARTIAL、PDF 公式复制检索=BLOCKED、RELEASE_READY=BLOCKED**。仅改报告展示层及对应的逐表断言；冻结字段、公式注册表、词典、稳定章节 ID、模型和 canonical 原件未改。R10 v7 基线提交为 `f88359c2752254020ab70fff9ca9016b5b932732`，原目录 `.runtime/solar-pv/phase7l-r10-reader-review-v7/` 不覆盖。当前 R11 候选另存 `.runtime/solar-pv/phase7l-r11-reader-review-v10/`，含 `delivery-receipt.json`、初次生成 DOCX 副本、两案共 133 张从最终 WPS PDF 生成的 180dpi 页面图、`qa/r11-v10-structural-identity-and-copy-gates.json`、`qa/v10-page-diff-v8.json` 和 `qa/v10-per-page-independent-image-verdicts.json`。v1—v9 为中间试排与审阅候选，不能把旧版结论冒充 v10 新审阅。两案均是合成示例，真实权属、接网、报价及现场资料仍待核验。

## 原件、根因及定点源码

- 在动笔前按 R10 回执重新计算两案四文件 SHA-256 与大小，全部匹配；屋顶 DOCX 为 `7f4789f282c941ec78f3e0dc15fbeadefe21ccc0630d5106627e19166b73c04c`，地面为 `3b8668f9122340ad0a308c4dee122539c51c7fdf7b8d80bb800b8222423fe5b6`。两案原 `result_hash` 分别为 `ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f` 和 `69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138`；R11 回执及保留工作簿与之相同。WPS COM 版本 `12.0`，Pandoc `3.13`。
- **R11-TABLE-HEADER** 根因是 `report_export.py::_add_table` 首次赋值时按 `continuation_identity` 把 `\n表N` 直接追加进首列表头，非 PDF 提取合字或 WPS 注入；R10 最终 DOCX 两案各 13 张表污染。长期生成器改为仅填列名。v6 `qa/r11-v6-structural-and-page-inventory.json` 逐表保存 R10 最终、R11 初稿及 WPS 保存后表头 `w:t`，13 张变化表为 10、12、16、17、19—25、27、34；其余 22 张未出现此污染。两案各 35 张表所有首行零 `表N`，WPS 保存前后单元格文字、行列形状一致。`tests/solar-pv/test_report_r9_presentation.py` 的已有读者预览检查已改为逐查 35 张表首行和行列数，不再断言旧污染。
- **R11-TABLE4-PAGINATION** 对短财务决策表增加相邻行同页关系，保持表题、表头与数据行，未移走动态回收期或缩字号。WPS PDF 文本反向定位屋顶物理第 36 页、地面第 35 页：表 4 标题和动态回收期同页；表 5 标题分别始于下一物理页。该文本定位不能替代逐页视觉审阅。
- **R11-DISPLAY** 年度金额列单独按元保留两位、小数 HALF_UP、千分位格式展示；税费及项目现金桥的独立舍入差额按同样显示精度重新列示，不记为付款。两案各 25 个年度的税费、运营收支、年度桥在显示精度下逐行对账无错，26 期项目流仍含建设期；原账簿、模型工作簿、来源清单未改。决策表的 26 期概览改为附录 F/模型 M14 索引，附录 26 期仍逐行保留；回收期叙事按两位显示。
- **R11-APPENDIX-C** 读者预览表 11 使用专业中文设备标签、方案值及参数类别三列，原字段 ID 留配套模型 M05；表 12/13 的损失类别、直流/交流/送出边界、顺序、已含标志、固定损失率和期间按实际枚举解释，原比值乘 100 显示百分数，原代码与原比值不动。未知枚举不臆译。资本支出指标短名及附录金额单位空格另有定点展示修改。
- **R11-IDENTITY** 读者版附录 M 明确将五身份定位至配套模型 M01 第 2—6 行、来源清单 S01 第 3—7 行；两工作簿逐项相等，且两案分别对应原 canonical。读者版与完整默认模式不合并：本轮从最终源码重新独立导出两份**默认完整版 Word**，实物按哈希读回并受控保留在 `.runtime/solar-pv/phase7l-r11-default-full-guard-v10/`，屋顶 SHA-256 `ee69b46b253d852782065c1bb738a08cbea83f6a0169e1fbce28396e140d9dcf`、地面 `d4d55971aaa9f4b9aa27f797ed0ff395aebc9939c92b3f93e945cbad9b9fb6d9`；两份均读回 89 个正式公式 ID / 89 个可编辑数学段、189 条完整词典行和 Word 中的五项实际身份，内容版本仍为 `phase7l-r10-reader-review`。这是本地 Word 结构核验，未将完整版重新经 WPS 转成 PDF，也不等于全本视觉或正式 L2/L3 交付验收。读者版仍只有 6 个 OMML、24 条常用词条，原完整版 Word 条款保持 **NOT_SATISFIED_READER_PREVIEW**；`F-UNIT-COST-WP-KWP` 源定义冲突未改，待方法负责人裁定。

## R11 实物及门禁

下表是**R11 v2 中间候选**的保留哈希，不能用于最终交付：

| 类型 | 文档 / SHA-256 | WPS PDF / SHA-256 / 页数 | 测算模型 SHA-256 | 来源清单 SHA-256 |
|---|---|---|---|---|
| 工商业屋顶 | `工商业屋顶光伏示例项目-光伏预可研报告-读者预览版.docx` / `e3ae167b742e534afdd7f48a7570db2fc7c6714538a3ab7e4705a156b8e23681` | `工商业屋顶光伏示例项目-光伏预可研报告-读者预览版.pdf` / `fbeca6b52514135ee5a3f8e44e4513401a036a7293dbf040954d79dafd4a43bc` / 67 | `09aa27780264a11ceb187b6248c488668deadba46758b1e971d796e24f93a3ff` | `d028575c517b74ffd1800451cd5be03ead95a57439e100546b570528c9656cdb` |
| 集中式地面 | `集中式地面光伏示例项目-光伏预可研报告-读者预览版.docx` / `5fbe1af007cf5d61569891baf88402d57feceed4585c31b68431c6590a8b5f25` | `集中式地面光伏示例项目-光伏预可研报告-读者预览版.pdf` / `d15d9f43f39ae43743658f91002e5f9bf1390c0ed92448d0957f9467a345ff0e` / 66 | `39e32eba13ea3259dc0a8d89104b153b0d9e80e239be780edf60107801c50c51` | `c4694fb461c07d3b6122872102dea7b8713debee2165b0787a65a40f3c8a31f4` |

**R11 v3 中间候选**（路径前缀 `.runtime/solar-pv/phase7l-r11-reader-review-v3/`；文件名与上表同，完整字节数在 v3 的 `delivery-receipt.json`）：

| 类型 | WPS保存DOCX SHA-256 | WPS PDF SHA-256 / 页数 | 测算模型 SHA-256 | 来源清单 SHA-256 |
|---|---|---|---|---|
| 工商业屋顶 | `a0ef81f33886badddcb3a31c3226f9baea8055a0cc0594d851ddb8304259a585` | `2611d2423449bf0d68d7211238ef90c4528e1f91af85f17141cced24a7533c0b` / 67 | `09aa27780264a11ceb187b6248c488668deadba46758b1e971d796e24f93a3ff` | `d028575c517b74ffd1800451cd5be03ead95a57439e100546b570528c9656cdb` |
| 集中式地面 | `2b5a2848bbdcacdd38c35a790a2faec2b5582998acfd87c02f2960483a1b3d5a` | `53496281253af2f289b68c1d0ffbfc9896724872bb67488503666722dfb25ef9` / 66 | `39e32eba13ea3259dc0a8d89104b153b0d9e80e239be780edf60107801c50c51` | `c4694fb461c07d3b6122872102dea7b8713debee2165b0787a65a40f3c8a31f4` |

**R11 v5 中间候选**（实际路径前缀 `.runtime/solar-pv/phase7l-r11-reader-review-v5/`；文件名同 v2 表，两案四文件的字节数及完整哈希均在 v5 回执）：

| 类型 | WPS保存DOCX SHA-256 | WPS PDF SHA-256 / 页数 | 测算模型 SHA-256 | 来源清单 SHA-256 |
|---|---|---|---|---|
| 工商业屋顶 | `83d72e856df8ade987f64c40084bb28057eee2d78fcbb86077eb8719e651a65a` | `c08c09199a16cf0dac9841f430c54b7f463d7f3e6b6a15fe8b5dc419cbe9e321` / 67 | `09aa27780264a11ceb187b6248c488668deadba46758b1e971d796e24f93a3ff` | `d028575c517b74ffd1800451cd5be03ead95a57439e100546b570528c9656cdb` |
| 集中式地面 | `a7298eb9cb3c45ae82840e2785fffc235d10c10712c79971f618cae99f872263` | `f1436d56665d065032c8fbb05639e27b0a86e5142fe4d1920f9bead67b78ca2a` / 66 | `39e32eba13ea3259dc0a8d89104b153b0d9e80e239be780edf60107801c50c51` | `c4694fb461c07d3b6122872102dea7b8713debee2165b0787a65a40f3c8a31f4` |

**R11 v6 中间候选**（实际路径前缀 `.runtime/solar-pv/phase7l-r11-reader-review-v6/`；同一文件名，字节数及哈希由 `delivery-receipt.json` 逐件复算匹配）：

| 类型 | WPS保存DOCX SHA-256 | WPS PDF SHA-256 / 页数 | 测算模型 SHA-256 | 来源清单 SHA-256 |
|---|---|---|---|---|
| 工商业屋顶 | `f192168d00bb6f362e5ff493cfceb81520af2e291b8a165e28856ebbaecff5d2` | `a46aebff433c70417f38fc5057f1a6db218ed3f7c740f9ec0e21bec3c38f0e22` / 67 | `09aa27780264a11ceb187b6248c488668deadba46758b1e971d796e24f93a3ff` | `d028575c517b74ffd1800451cd5be03ead95a57439e100546b570528c9656cdb` |
| 集中式地面 | `3bedf76405d8daa3a028603f67f61e4c3ffbeec46161e326490305f631857d28` | `1eda05abdcf150fa5413fd22b1100097b12ca4e3bf3b36ceda0068a2d8985c71` / 66 | `39e32eba13ea3259dc0a8d89104b153b0d9e80e239be780edf60107801c50c51` | `c4694fb461c07d3b6122872102dea7b8713debee2165b0787a65a40f3c8a31f4` |

**R11 v8 中间候选**（路径前缀 `.runtime/solar-pv/phase7l-r11-reader-review-v8/`；文件名同上，逐件字节数见 `delivery-receipt.json`，以下 SHA-256 已从保存后的实际文件复算）：

| 类型 | WPS保存 DOCX SHA-256 | WPS PDF SHA-256 / 页数 | 测算模型 SHA-256 | 来源清单 SHA-256 |
|---|---|---|---|---|
| 工商业屋顶 | `fb82d438eddfc0b1b0a72f86d76b8ec8fff3568d1ba113dd58da274700fcd162` | `8329d1b2de75e08e6e27adbb847b602d17a39492a30dfea1acf25397e4a0f7b1` / 67 | `09aa27780264a11ceb187b6248c488668deadba46758b1e971d796e24f93a3ff` | `d028575c517b74ffd1800451cd5be03ead95a57439e100546b570528c9656cdb` |
| 集中式地面 | `be02cd0fdd799a7ebe4e5d59e840de8246f42cbff69ae7f3a781463754d514d5` | `76e225f51e1418783657953c5bd184cc85dce6b4718c47031220036152080212` / 66 | `39e32eba13ea3259dc0a8d89104b153b0d9e80e239be780edf60107801c50c51` | `c4694fb461c07d3b6122872102dea7b8713debee2165b0787a65a40f3c8a31f4` |

**R11 v10 当前候选**（路径 `.runtime/solar-pv/phase7l-r11-reader-review-v10/`；文件名同上，哈希按最终 WPS 保存和 PDF 实物重新计算）：

| 类型 | WPS保存 DOCX SHA-256 | WPS PDF SHA-256 / 页数 | 测算模型 SHA-256 | 来源清单 SHA-256 |
|---|---|---|---|---|
| 工商业屋顶 | `ff0fe9d0e70424f0eb399ba18e94a2a0b9e1ce3c2f52ddbad5414208934e88d6` | `59465c7ed4780a8db1d5cb0a74fde0b60a239a6d35de5d195de0266f0efaffb2` / 67 | `09aa27780264a11ceb187b6248c488668deadba46758b1e971d796e24f93a3ff` | `d028575c517b74ffd1800451cd5be03ead95a57439e100546b570528c9656cdb` |
| 集中式地面 | `7968a259b2378da6b277e93f27119dc3ec44e82cfaac5535b35900d517d55577` | `d7117a67a992b5e7412bb093d0162c4f891f1f34d1a7c92070d704cad67ef536` / 66 | `39e32eba13ea3259dc0a8d89104b153b0d9e80e239be780edf60107801c50c51` | `c4694fb461c07d3b6122872102dea7b8713debee2165b0787a65a40f3c8a31f4` |

两案均是 157 标题、157 个 WPS 刷新目录项、35 张表、6 OMML；DOCX 生成前后表形不变，35 表标题一对一且行列形状与 R10 相同。两套 XLSX 按原 R10 字节复制，非新计算。PDF 页码与文字层已逐页提取、180dpi 图在 `qa/<pv_type>-180dpi/`；**生成图片不是人工逐页签审**。v10 WPS PDF 数学文字层每案仍有 103 个 U+FFFD：屋顶物理 60—64 页分别 14、33、27、12、17；地面 59—63 页对应同数。替换字符均落于 CambriaMath 字体的数学文本段，NPV、IRR、回收、LCOE 等数学区域复制/检索缺陷尚在；视觉字形和 OMML 语义须独立核验，此项 **PARTIAL/BLOCKED**，不以 LibreOffice 对照替换正式 WPS 链。

专项回归首次运行：**216 passed、4 failed、6 skipped**（退出码 1）；四项均为 `test_app06_full_annual_bridge.py` 保留的整数元字符串精确断言与本次明确要求的两位金额展示冲突。未削弱现金事件或账簿核对，改为对同一已冻结数值逐项比较两位展示字符串，该模块独立复跑 **10 passed、0 failed**；基于 v2 源码的整组复跑 **220 passed、0 failed、6 skipped**（退出码 0，v2 `qa/report-focused-final-junit.xml`）。v3 源码整组复跑 **220 passed、0 failed、6 skipped**（退出码 0，`.runtime/solar-pv/phase7l-r11-reader-review-v3-focused-junit.xml`）。v4 的整组运行因发现后续读者展示问题而主动中止，不属于通过。v5、v6、v8 三轮源码整组各自均为 **220 passed、0 failed、6 skipped、1 个依赖弃用警告**（退出码 0，对应 `.runtime/solar-pv/phase7l-r11-reader-review-v{5,6,8}-focused-junit.xml`）。**v10 最终源码专项**独立运行命令为 `WANGBIN_SOLAR_PV_PANDOC=<本地 pandoc> PYTHONPATH=services/solar-pv-engine/src python -m pytest -q tests/solar-pv/test_report_*.py tests/solar-pv/test_phase7l_r2*.py tests/solar-pv/test_app06_full_annual_bridge.py --junitxml=.runtime/solar-pv/phase7l-r11-reader-review-v10-focused-junit.xml`，退出码 0；JUnit 实读 226 tests，**220 passed、0 failed、0 errors、6 skipped**，耗时 661.08 秒，另有 `anyio` 的 `CallSpec2` 弃用警告。后续发现同时启动了相同命令、写同一路径的重复运行，已中止该重复进程；以上计数以已完成运行和已读回 JUnit 为准，不累加重复进程的部分进度。

v2 的独立视觉审阅已覆盖屋顶物理 **1—67 页**：表 4/5/6 各自同页，表 10/12/17/20/23/25 的续页表头可见，六式视觉上可辨；物理 2、12、13、19、22、30、40、64 页标 **PARTIAL**（摘要换行偏紧、日期/面积单位断行、部分正文/续文大面积留白及表 10 跨批次边界），其余 59 页 PASS。地面 v2 物理 **1—66 页**也已分批逐页查看：物理 35 页表 4（包括动态回收末行）同页，36 页表 5/6 各自同页；跨页表 10 续页重复表头但没有独立“续表10”题注，39—40 页 PARTIAL；物理 45 页表 18 首列孤字换行 PARTIAL；公式（1）—（6）图像可辨但部分释义跨页、物理 63 页续文很短。地面目录物理 4、7、8 页及正文第 15 页因冻结章节题名中“降级”“血缘”“哈希”“审阅边界”等内部流程口吻判 **FAIL**，第 6 页 PARTIAL；物理 9—14、16 页连续断词/断日期均 PARTIAL。物理 18、21、26、29、39、40、45、55、59、60、62、63、66 页另有排版或可核边界 PARTIAL，其余地面页 PASS。这些页级视觉判断不等于 PDF 文字层、准确数学语义或专业结论通过；冻结题名同时存在于 `02-report-outline-18-chapters.md`，读者显示别名不得修改稳定 ID/源合同。**不能把 v2 的页级结论套用到任何后续候选**。

另外两案 v2 实际 DOCX 的财务表 14/21 金额列曾在 `TECHNICAL_DETAIL_TABLE` 布局下左对齐；这与本轮“金额列数字右对齐”尚不一致，须改长期布局并重新出件。未执行的全仓回归标 **NOT_RUN**，R10 旧版的 99 failed / 58 errors 不能当作本轮新失败或本轮已通过。真实项目授权、公式负责人裁定、原完整版与预览双轨交付范围及 WorkBuddy 安装/平台审核均待独立批准；本地候选不发布、不自动 push。

v3 新增读者预览标题显示别名（仅展示层，冻结大纲与稳定 ID 未改）、表14/18短题注及表18首列扩宽；最终 DOCX 的表14/21货币单元格已读回右对齐。`qa/v3-page-diff-v2.json` 对两案每个同序页重算 **文字与180dpi原始像素**：屋顶53页、地面52页两者完全一致；屋顶14页、地面14页发生变化，已从v3 PDF单独栅格化并委托逐页重新目视检查。额外逐表比对发现：v2/v3 的读者表11相对 R10 表11从 **21×3 改成21×2**，虽然是为去掉程序字段而做的展示收缩，但与本轮“各表实际行列无变化”的严格要求冲突；因此 v3 **暂不得视为最后候选**，须保留3列且不暴露内部字段，再生成隔离版本并对新哈希重做相关门禁。

v5 恢复表11为 **21×3**，第三列为专业“参数类别”，不再直出程序字段；两案全部35表的行列形状均与R10逐表相同，原生DOCX到WPS保存稿的全部单元格文字与形状也一致。表6未声明的投资目标计量单位显示“待确定”；两案年度金额和展示尾差均按元两位小数单独列示，13个附录引言分别说明实际主题及证据限制。额外改写五处读者版小标题别名及“交易费/运维费分账”的自然中文，原冻结章节/附录ID及题名表、公式和模型不动。`qa/v5-page-diff-v3.json` 对最终两案 **每一物理页**比对文字及180dpi原始像素：屋顶40页、地面42页两者一致；屋顶27页、地面24页变化且已从v5 PDF重新取图，最终页级独立审阅与表4/跨页表仍须按v5自身哈希记录。v5仍每案103处公式文字层替换；不能把章节可读或Word公式可编辑当作WPS PDF精确复制检索已经通过。

v5 实际变化页已委托独立图像审阅；屋顶物理38页附录A引言“验。”独占一行标 **FAIL**，物理37页表6单位“元/kWh”拆行为 **PARTIAL**，地面物理37页同样孤行、36页单位换行也为 **PARTIAL**；另有两案表格短尾、续页缺独立题注及原有日期/面积单位断行的 **PARTIAL**。不能用 `220 passed` 替代页面视觉判定。v6 仅缩短附录A引言、给表6单位列从实际1.51 cm扩为1.88 cm（相应缩短结果列），并防止其单位值换行。v6与v5的WPS保存DOCX逐段逐表文本比较：两案均仅第418段引言文字变化，全部35表单元格文字原样；PDF逐页比较提取文字及180dpi原始像素：屋顶65页、地面64页完全一致，屋顶物理37、38页与地面36、37页为仅有变化页，已提交v6实图重新独立审阅。原v5的其余图像结论仅在逐页双重完全一致的范围内沿用，**不宣称为v6全本重新签审**。两案公式文字层仍各103处替换，完整Word所需89式/189词/正文身份条款、独立情景、真实资料与平台验收仍未满足；本轮不可写`RELEASE_READY=PASS`。

v8 曾完成两案全部 133 张 180dpi 实图独立逐页审阅；地面物理 63 页仅余公式短尾、几乎整页留白，视觉标 **FAIL**，不能因此升为最终候选。v10 仅对第六个正式公式起始段落加 `page_break_before`，不改公式、词典、冻结注册表、模型或金额计算。新 WPS 实物仍为屋顶 67 页、地面 66 页；第六公式、表 33 和释义按文本定位均落在同一物理页（屋顶 64、地面 63），但**文本定位不能代替新的 133 页逐页视觉复核**。`qa/v10-page-diff-v8.json` 逐页对比 v8→v10 的完整 PDF 文字及 180dpi 像素：屋顶 65 页、地面 64 页双重完全一致，仅屋顶 63/64、地面 62/63 发生页级变化；该对比仅作变更归因，不用于把 v8 视觉结论无条件转移至 v10。v10 逐页审阅及最终专项回归结果分别见下文和上述 JUnit 回执；前者未达全 PASS，门禁保持 **REVIEW_REQUIRED**。

v10 屋顶物理 1—67 页已按最终 PDF SHA `59465c7ed4780a8db1d5cb0a74fde0b60a239a6d35de5d195de0266f0efaffb2` 逐页从实图独立复核：P0 财务短表 4/5/6、附录 A 四条索引、跨页表头及物理 63→64 页第六公式均可见且没有断裂；**视觉并非全 PASS**，最终逐页计 **61 PASS、3 PARTIAL、3 FAIL**。第 12 页权利到期日 `2052-12-` / `31`、第 13 页面积 `3,000` / `㎡` 断行及第 30 页只放 CAPEX 第六小节一段、其余近整页留白，视觉审阅标 **FAIL**；第 9 页 `25` / `年` 断行、第 27 页计划表密集换行标 **PARTIAL**。第 67 页身份指引本身清楚，但该页不列出五项身份原值，视觉审阅的身份内容结论 **PARTIAL**，须以配套 M01/S01 实际值交叉验证，不能从图片臆断通过。第 22 页初审将 `0kWh` 误读为 `0kW`，经另一个审阅者放大 **PDF 页图像**核对，`W` 后的 `h` 确实可见，判为 **PASS**，并非靠 PDF 提取文本代替目视，二审原始轨迹附于逐页回执。此处的 FAIL/PARTIAL 属未修排版/展示风险，应保留 `PDF_VISUAL_REVIEW=PARTIAL`；不应为美化本轮结论擅自改冻结数据或大范围改分页。

v10 地面物理 1—66 页按最终 PDF SHA `d7117a67a992b5e7412bb093d0162c4f891f1f34d1a7c92070d704cad67ef536` 新图像逐页审阅：表 4 的**九行全部同页**、表 5/6 分表清楚；四条来源索引、两幅图、表 10/12/17/20/23/25 的跨页表头和金额列、附录 M 指引均可辨。**不能判视觉全通过，逐页计 45 PASS、18 PARTIAL、3 FAIL**：物理 12 页到期日期 `2052-` / `12-31` 断行 **FAIL**；公式 5 在物理 62 页中部结束、公式 6 移至物理 63 页完整呈现但后半页留白，两页均经独立审阅标为短尾排版 **FAIL**（原 v8 第 63 页近全空白的极端短尾已改善，但不应称已完全修复）。物理 9/14/15/16 页数值与单位间距、10/18/21/29 页短章跨页留白、26 页表 2 密集、39/40 页表 10 跨页、59/60 页 DSCR 释义及符号表跨页等为 **PARTIAL**；49—56 页中 51/53/54/55/56 页另被审阅者按尚无股东现金流、独立敏感性、政策/权属材料和完整公式审定判为**内容证据 PARTIAL**，其页面文字清晰，并非裁切缺字。全部原图与逐页 AI 审阅轨迹按 PDF/页面 SHA 保存在 `qa/v10-per-page-independent-image-verdicts.json`；此清单不代替真人视觉和专业财务、工程签收，`CONTENT_QA=REVIEW_REQUIRED`、`PDF_VISUAL_REVIEW=PARTIAL`、`RELEASE_READY=BLOCKED`。
