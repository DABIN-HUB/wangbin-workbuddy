# R10 对外读者版候选：范围变更与审阅回执

状态：**REVIEW_REQUIRED / 未发布**。本轮是 R9 报告展示层的读者化预览，不是原冻结合同的全量 DOCX 验收，不是项目投资意见，也不代表真实工程已核验。基线为远端 `8f0017fa83609446f64ece5fdb2ba52176777cc3`；本地 R9 v11 原件保留在 `.runtime/solar-pv/phase7l-r9-final-v11/`，原件哈希已按其 `delivery-receipt.json` 在生成前逐文件读回比对。WPS 实测 COM 版本 `12.0`；Pandoc `3.13`（由 `WANGBIN_SOLAR_PV_PANDOC` 显式指定）。

## 候选与身份

当前目录：`.runtime/solar-pv/phase7l-r10-reader-review-v7/`；`delivery-receipt.json` 记录本次文件身份、文件名及哈希，不记录绝对路径。目录后缀 v7 是**导出迭代**，报告内容版标识仍为 `phase7l-r10-reader-review`，不是另一个计算版本。之前各中间件只保留为独立审阅的历史证据，不可把旧 PDF 视觉结论笼统转移给已变化的 v7 页面。两案均为**合成示例项目**，不是实际站址实勘数据；`reader_preview` 对非该类未核验合成项目直接拒绝，不能将本次示例文案套用到已核验真实项目。报告只显示统一声明“本报告内容仅供参考，正式使用时需根据实际情况调整。”一次，同时醒目说明资料待核验、暂不具备投资决策条件。

| 类别 | DOCX SHA-256 | PDF SHA-256 / 实测页数 | 测算模型 SHA-256 | 资料来源 SHA-256 | canonical result_hash |
| --- | --- | --- | --- | --- | --- |
| 工商业屋顶 | `7f4789f282c941ec78f3e0dc15fbeadefe21ccc0630d5106627e19166b73c04c` | `3831588d6e9d8348d08cb4551f98becea0fe30e1105a12552feb4f9d4d0a226f` / 67 | `09aa27780264a11ceb187b6248c488668deadba46758b1e971d796e24f93a3ff` | `d028575c517b74ffd1800451cd5be03ead95a57439e100546b570528c9656cdb` | `ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f` |
| 集中式地面 | `3b8668f9122340ad0a308c4dee122539c51c7fdf7b8d80bb800b8222423fe5b6` | `81f61a7ac6ef3c1fc704b3040a066ff1057640de69c31bff7595474f25ecdd42` / 66 | `39e32eba13ea3259dc0a8d89104b153b0d9e80e239be780edf60107801c50c51` | `c4694fb461c07d3b6122872102dea7b8713debee2165b0787a65a40f3c8a31f4` | `69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138` |

文件名前缀分别为 `工商业屋顶光伏示例项目-`、`集中式地面光伏示例项目-`，四文件后缀分别为 `光伏预可研报告.docx`、`光伏预可研报告.pdf`、`测算模型.xlsx`、`资料来源与假设清单.xlsx`。两个 XLSX 是 R9 原件的**字节复制**，读回哈希一致；没有重算财务或改写来源。R9 PDF 实测为屋顶 150 页、地面 149 页。

## 冻结范围差异——需要用户明确批准

原 `00-original-user-baseline.md` 与 `02-report-outline-18-chapters.md` 要求 Word 附录 K **全部公式逐符号定义**、附录 L **完整术语词典**；当前受控注册表/R9 产物分别为 89 式、189 词，本候选各只展示 6 条常用公式 OMML、24 条适用的常用术语和单位表。`10-four-file-acceptance.md` 还要求五项测算身份出现在 DOCX 中；本版仅在内部回执及配套工作簿保留这些内部标识，不在客户版 Word 列出。**原冻结 DOCX 全量内容与 Word 身份条款均未满足**；回执分别标为 `NOT_SATISFIED_READER_PREVIEW`，不得以此候选取代原 R9 完整交付或把旧门禁改写为 PASS。保留 R9 原件，等待用户明确批准读者版与完整技术版的双轨交付范围。配套原样 XLSX 的 `变量-术语词典` 仍有 89 条 `FORMULA_SPEC`（含 `latex`、`text_equation`、`every_symbol_definition`、来源及适用边界）和 189 条 `GLOSSARY` 完整定义；`F-UNIT-COST-WP-KWP` 冻结 `latex=c_kWp=c_Wps` 与 `text_equation=c_kWp = c_Wp × s` 不一致，**仍须专业方法负责人裁定**，本轮未改写正式定义。

原报告 120 表到本版 35 表的两案逐表去向在 v6 `qa/r9-to-r10-120-table-lineage.json`：1—27 表编号不变；R9 第 28—116 表按 F-ID 对应到本版 6 张核心符号表或保留于工作簿 `FORMULA_SPEC`；R9 第 117 表常用术语对应本版第 34 表，第 118 表完整词典保留于工作簿 `GLOSSARY`，第 119 表单位边界对应本版第 35 表，第 120 表身份/版本在新回执及配套工作簿保存。原 R9 文件全部未覆盖。v6 回执中的 `qa/v1-to-v2-docx-content-delta.json`、`qa/v2-to-v3-physical-page-and-word-delta.json`、`qa/v3-to-v4-physical-page-and-word-delta.json`、`qa/v4-to-v5-physical-page-and-word-delta.json` 与 `qa/v5-to-v6-physical-page-and-word-delta.json` 保留各轮 Word 和分页差异；v3/v4 局部视觉复核曾发现并处理资源说明孤字，表10/12仍存在续页身份不够明确的改进项。v5 发现表35末行孤页，v6 调整列宽后九条单位释义留在同页；v6 两案分别变动五页。新版附录 M 分别由 v5 物理第68/67页前移至第67/66页，目录同步更新。v6→v7 `qa/v6-to-v7-physical-page-and-word-delta.json` 显示两案均只改动附录K公式索引的一段：屋顶物理第57页、地面第56页的文字及180dpi图像变化，其他 **66**／**65** 页图像字节相同，表格单元格均未改。像素相同仅证明当页内容未变，不等于重新人工签审。默认完整 Word 另恢复每式原始 LaTeX 记法（保留文字表达），读者版在附录K增加单位换算冲突的可读提示；冻结公式源未更改。

## 已执行的客观复核与不能升级的门禁

- 结构：两案 WPS 保存后 DOCX 各含 157 个标题、157 个刷新 TOC 条目、35 张表和 6 个可编辑 OMML。v6 `qa/final-automated-verification.json` 对 157/157 个目录条目按目标物理页逐一核对；v7 同序标题与目录条目匹配，除同页公式索引提示外，其余页图像字节相同，v7 的 `qa/final-automated-verification.json` 明确记录这一**继承依据**，并非逐条重新核对目标页。机器核对不等于目录视觉签审。报告正文及表格未检出“测试报告”“开发样件”“测试假设”“阶段验收”“SYNTHETIC-”“UNKNOWN”等指定残留；但词句质量仍需人工逐段审校。
- 表格：v7 的 35 表单元格文字与 v6 逐格相同；表35的“元/kWp”最后一行已由机器文本读回定位在表题同页（屋顶物理第66页、地面第65页），不再生成孤独的单行续页；这两页在 v6 已获独立目视判定且 v7 图像字节未变。12 个月月表、25 年账簿和建设期行保留。独立内容审阅（旧哈希）限定核对两案各 581 个财务展示单元格、26 期桥接；不变数值可作为同源参考，**不是逐页阅读清晰度的证明**。
- 页面：v7 `qa/automated-page-and-table-inventory.json` 记录了 **67+66** 页文本层、页眉、越界框、禁用词与全部 35 表表题/表头/首尾行；每页另输出 **180dpi** JPEG 至 `qa/<类别>-180dpi/`，未发现文字框越过纸张边界，报告内容区屋顶 60 页、地面 59 页提取到本项目类型页眉（包括附录及正文），封面及目录前 8 页不以普通正文页眉判错。**自动栅格化/文本检查不等于 133 页逐页人工视觉审阅**，不能据此给 `PDF_VISUAL_REVIEW=PASS`。
- 变化页独立目视：v6 `qa/v6-independent-changed-pages-visual.json` 将其 PDF 与两案各 5 张 180dpi 图片哈希绑定；屋顶物理 **2、8、33、66、67**、地面 **2、8、32、65、66** 页各获所看图范围内 PASS，日志留于 v6 `qa/v6-independent-changed-pages-reviewer-*.log`。v7 对上述十页 JPEG 字节逐一比对相同。v7 `qa/v7-independent-changed-pages-visual.json` 另绑定新 PDF、屋顶 **57** 页和地面 **56** 页图片哈希及独立审阅日志，两页提示可读、未与本页**表27**重叠、页眉页码完整；**表28并不在这两张图中，不能宣称审过表28**。这些局部判定不等于最终 **133页全本视觉签审**，跨页表10/12续页身份不够明确等改进项仍在。
- 核心数学对象专项：旧候选局部可见字形结论只在逐页像素及文本完全相同的页面保留限定证据；v7 PDF 公式区域的文字层每案仍有 **103 个 `�`**（屋顶 60—63 页、地面 59—62 页），整式精确复制/检索**未通过**；`F-IRR-PROJECT` 花体 `𝒟` 的精确字形仍未确认，需方法负责人及 WPS 字符映射专项核定。
- 财务与现场：当前项目 NPV、IRR 等只作为合成预测；未取得真实权属、结构鉴定/地勘、接网、有效交易和融资材料。股东回报及部分指标无可用结果不得称为已计算，投资决策仍应暂缓；平台未安装或实际运行。

回归真实状态：全仓 `pytest -q` 的一次执行为 **4434 passed、99 failed、58 errors、16 skipped**（退出码1，运行约1小时29分）；多数能源时序和候选回放失败伴随 `BUNDLE_MEMORY_LIMIT`，一条代表性失败在单独进程中复跑通过，但这**不等于全仓回归通过**，且未在 v7 源码快照下重跑全仓。旧版报告专项一次为 **212 passed、6 failed、6 skipped**，6 项旧版完整 Word 文字表达/净现值说明回归随后不削弱断言修正生产代码并单独重跑 **6 passed**；另外5项旧版显示回归修正后单独重跑 **5 passed**。v6 源码下专项复跑 **218 passed、6 skipped**。本轮 v7 修改后首次两次定向运行均因 Pandoc 路径未传入进程而分别出现 **2 failed、2 passed、2 errors**；明确设置 `WANGBIN_SOLAR_PV_PANDOC` 后定向 **6 passed**。首次 v7 导出误用缺 `pymupdf` 的项目虚拟环境而失败；改用具备依赖的 Python 环境并显式设置 `PYTHONPATH`、Pandoc 路径后两案生成成功。**最终 v7 源码**的报告专项命令 `pytest -q tests/solar-pv/test_report_*.py tests/solar-pv/test_phase7l_r2*.py tests/solar-pv/test_app06_full_annual_bridge.py --junitxml=.runtime/solar-pv/phase7l-r10-reader-review-v7/qa/report-focused-junit.xml` 为 **220 passed、6 skipped、0 failed，退出码0**（11分55秒；原始 XML 在候选 QA 目录）。这只证明选定报告模块，并不覆盖全仓失败。待补：公式文字层与花体字形、剩余版式改进、真人业务语义复审，以及全仓回归失败的独立根因核定。本轮交付状态仍为 `REVIEW_REQUIRED`；未 push、未发布。
