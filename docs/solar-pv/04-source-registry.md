# Phase 1 光伏专业资料来源登记与章节对照

> 父任务复核：6项关键原站已重新GET并核对标准元数据/报告封面、物理页数；证据见`reports/solar-pv/phase1-parent-source-recheck.json`。工具环境未提供web.run，保留原实际检索/原站读取方法，不伪造工具路径。此工具限制不否定有记录的原站访问，但也不等于标准全文、真实站址数据或专业方法已验收。公开工程“示例报告”本研究cohort未取得，数量为0；API公开样例不是工程报告。下面统计仍保持37项专业来源口径，额外政策/平台及单条损失帮助页分集登记。

> 研究基准日：2026-10-28（中国标准时间）。快照：`solar-pv-phase1-20261028-tech-v1`。仅交付技术研究索引，不代表产品引擎、四文件生成或整期 Phase 1 验收完成。

本文件、`04-sources.json` 与 `04-source-chapter-comparison.csv` 同源生成。外部文档只保存事实摘要、字段/公式/表格定位与URL；没有把受保护PDF、整篇正文、完整表格或图片并入仓库。父代理的 `00-official-access.json` 中 POL-001..007 与 WorkBuddy 来源不纳入本台账计数。

## 1. 精确统计与口径

| 项目 | 数量 | 口径 |
|---|---:|---|
| 登记发现来源 | 37 | 去重后实际尝试原站访问的逻辑资料；分卷不重复 |
| 有效正文或元数据来源 | 30 | 包含3份标准元数据；不是30份工程报告 |
| 严格完整出版物全文文本可读 | 11 | 6份PDF + 5份原生技术/API HTML；摘要/公告/目录不充全文 |
| 其中完整PDF全文文本可读 | 6 | 全部物理页可抽文字；空白/图片页保守不通过 |
| 结构已提取 | 26 | 真实来源目录/条款/API章节的局部结构，不是全条款已摘录 |
| 具体真实项目来源 | 12 | 8份一手 + 4份二手项目摘要；不证明全已建成 |
| 严格完整真实工程可研 | 3 | 中国新疆、美国污染地、澳大利亚填埋场各1份 |
| 真实项目完成评价 | 1 | World Bank ICR；受限标签待澄清 |
| 取得PDF逻辑来源/实际PDF资产 | 13 / 14 | 含摘要和分卷，均仅内存取阅、不归档原文 |
| 可抽文字页 / 下载物理页 | 1326 / 1347 | 不包括HTML“页数”；不是人工逐页精读量 |
| 阻断或仅JS壳 | 7 | 4个WAF、2个JS壳、1个网络错误 |
| 许可仍REQUIRES_REVIEW | 31 | 公开可访问≠可整本商业再分发 |
| 实际成功的公开API样例端点 | 2 | NASA POWER Daily、PVGIS v5_3；非生产适配器验收 |
| 授权标准全文取得 | 0 | 标准正文门禁仍BLOCKED |
| 原生web.run核验条数 | 0 | 子代理未暴露该工具；不得伪装已用web.run |

共执行 37 次真实检索；检索返回去重URL 101 个（含噪声和未选项，**不计有效来源**）。登记发现数仅指上表37项；原站访问成功、全文、结构及真实项目是不同集合，不能相加或互换。

**工具路径阻断必须保留：**本子代理没有可调用的 `web.run` schema；`hermes web_extract` 实际返回“search-only backend cannot extract”。研究实际使用 `hermes_tools.web_search` 检索、匿名 `requests.get` 访问原始站点、`pypdf`逐物理页抽取。全部 `web_run_verified=false`。若总验收强制 `web.run`，须父代理补核，不能把本索引改称已满足该工具路径。

## 2. 种子标准编号、名称和状态核实

| 来源ID | 实际官方条目 | 访问时状态 | 发布/实施 | 正文/目录情况 |
|---|---|---|---|---|
| SRC-PV-001 | [NB/T 32044-2018 光伏发电工程**预可行性**研究报告编制规程](https://hbba.sacinfo.org.cn/stdDetail/d000c5b3cf7353ac4eb7f9219d1d031b) | 现行 | 2018-06-06 / 2018-10-01 | 仅官方备案元数据；标准正文未取得 |
| SRC-PV-002 | [NB/T 32043-2018 光伏发电工程**可行性**研究报告编制规程](https://hbba.sacinfo.org.cn/stdDetail/926f539f12644210fae18d9b5e9a8b02) | 现行 | 2018-06-06 / 2018-10-01 | 仅官方备案元数据；标准正文未取得 |
| SRC-PV-034 | [IEC 61724-1:2021 性能监测](https://webstore.iec.ch/en/publication/65561) | 已核2021版商品元数据；是否后版替代未完全核实 | 2021-07-21；Edition 2.0 | 商品宣称136页≠本次可读136页；正文未取得 |

前两条编号和名称**没有反转**。官网页面的状态流程同时包含“废止”等标签，应读取标题实际状态“现行”，不能把流程选项误当已废止。IEC商品页的“Stability date 2026”不是自动失效日。以上都不能用我方18章去冒充标准实际目录。[SRC-PV-001][SRC-PV-002][SRC-PV-034]

## 3. 多地域、不同资料类型与真实项目边界

| 地域/来源 | 实际资料 | 阅读范围及可用性 | 不能推出的结论 |
|---|---|---|---|
| 中国新疆 SRC-PV-016 | 2014年20MWp真实地面电站可研 | 202/202文字页；15个实际主章 | 预测不是实测；旧电价/税费/单位投资不能做2026默认 |
| 中国湖南 SRC-PV-017 | 2025公共屋顶可研批复 | 198.45kW、面积、总投资、模式的正式公开摘要 | 批复不是可研正文，kW的AC/DC未明 |
| 江西/湖北 SRC-PV-018/019 | 2026一手EPC候选/结果公示 | 真实候选报价或中标总额 | 无完整范围/税/容量边界不算确定元/Wp |
| 天津/江苏/重庆/河北 SRC-PV-020..023 | 2026水域/渔光/农光采购媒体摘要 | 项目特征及合同边界的二手线索 | 不能冒充一手招标全文或通用全投资基准 |
| 马尔代夫 SRC-PV-024 | 2009实际屋顶/配网可研Final Report (Summary) | 2分卷120物理页/110文字页；同一来源只计1 | SUMMARY不是完整主报告；45kWp为示范详细设计非全岛总规模 |
| 尼日利亚 SRC-PV-025 | 2007国家太阳能规划及试点摘要 | 122/122文字页 | 真实规划不等于单站完整可研，未计单项目数 |
| 美国 SRC-PV-032 | 2013污染地Kerr McGee场址真实可研 | 47/47文字页，包含SAM经济比较 | 可研不等于建成；旧PPA/补贴不可迁中国 |
| 澳大利亚 SRC-PV-033 | Wollert填埋场100kW试点可研/经验 | 32/32文字页，2019-12-19正文日期 | FINANCES以定性讨论为主，无完整IRR/NPV模型证据 |
| 中亚/印度 SRC-PV-026..028 | ADB漂浮项目准备/TA | 已发现，但原站403，无正文 | 不能把候选水库或准备活动充作已建项目或已取可研 |
| 马尔代夫 SRC-PV-029 | 2026 ASPIRE项目完成评价 | 48/48文字页，含结果、成本、效率附录 | 同时出现公开/Official Use Only标签，许可待澄清 |
| 巴西 SRC-PV-037 | World Bank太阳辐射/PV潜力数据目录 | 目录正文可读，更新日2023-01-19 | 未下载栅格，不能当站点气象/真实工程报告 |

## 4. 最新性、技术手册与资源接口核验

- **IRENA**：本次检索发现2026/Jul的《Renewable power generation costs in 2025》；主报告入口WAF403，仅官方**12页执行摘要**正文成功，不能声称2025主报告全本已取。2024年成本的216页完整版也取得，但明确是历史对照，不再称最新。摘要图S1–S4提供统计趋势，不是中国站点报价。[SRC-PV-013][SRC-PV-014][SRC-PV-015]
- **PVWatts**：2014 V5手册20页可抽文字；Eq8、9和10–11分别定位DC功率、乘积损失和逆变/限幅。V8官方API页面另行核实为当前版本，不能把V5全部方法当V8逐条规范；V8仅文档核实，未提供key，不声称API调用通过。[SRC-PV-004][SRC-PV-005]
- **Global Solar Atlas**：地图方法页和中国下载页HTTP200只给JS壳；搜索摘要提及的CC BY4.0附加条款没有冒充已读。2019技术报告另行取得39页/38文字页，提供GHI/DNI/DIF/GTI/PVOUT/TEMP等数据层及模拟边界。报告正文非商业复制条款与地图栅格许可必须分开。[SRC-PV-006][SRC-PV-007][SRC-PV-008]
- **NASA POWER**：Daily/Hourly官方文档可读；用公开Phoenix示例坐标、2024-01-01至02、GHI/温度/2m风速的真实请求返回200。响应API为v2.10.1、UTC，来源MERRA2/SYN1DEG/POWER，缺测标记-999。只证明这个请求成功；没有上传客户位置、账单或负荷。LST是太阳时，不是法定UTC+8，日平均不能用于逐时真实自用率。[SRC-PV-009][SRC-PV-010]
- **PVGIS**：官方手册当前默认5.3，API版本显式固定v5_3；公开lat45/lon8、1kWp和14%文档式样例真实返回200及12个月记录，响应自报SARAH3、ERA5与2005–2023。地形horizon不等于屋顶近物遮挡调查；样例参数不是本站真实工程默认。官方限流30 calls/s/IP及429/529必须在适配器设计保留。[SRC-PV-011][SRC-PV-012]
- **漂浮/近岸不能混用**：2019内陆漂浮手册与2026年9月近岸手册为不同技术边界。近岸手册的成本表6.1注明early2022马尔代夫初步假设，不能因2026出版就认成2026中国报价；“渔光互补”也不必然等于浮体电站。[SRC-PV-030][SRC-PV-031]

### 4.1 实际资源请求（完整精确URL）

- [SRC-PV-009 实测请求](https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN,T2M,WS2M&community=RE&longitude=-112.0740&latitude=33.4484&start=20240101&end=20240102&format=JSON&time-standard=UTC)：HTTP 200，访问 `2026-10-28T09:23:57+08:00`。响应元数据、schema及哈希登记在JSON；只存摘要、不固化为真实项目气象。
- [SRC-PV-011 实测请求](https://re.jrc.ec.europa.eu/api/v5_3/PVcalc?lat=45&lon=8&peakpower=1&loss=14&outputformat=json)：HTTP 200，访问 `2026-10-28T09:23:57+08:00`。响应元数据、schema及哈希登记在JSON；只存摘要、不固化为真实项目气象。

### 4.2 后续适配设计（未实现）

坐标最小化与明确授权；版本/数据集/单位/时标全部入缓存键；连接与读取超时、有限退避，按429/529和供应商配额排队；缓存TTL分来源与用途，不统一硬设。校验-999、缺测、时间完整性及辐照度/辐照量。覆盖/许可失败时返回UNKNOWN/DATA_UNAVAILABLE，允许用户授权替代数据，不生成“模拟真实资源”。离线fixture须显式SYNTHETIC。该设计不是已运行适配器的验收结果。

## 5. 中国工程成本：先核合同边界，再看单价

| 来源 | 已核事实 | 成本边界及使用限制 |
|---|---|---|
| SRC-PV-018 国能一手候选公示 | 第一候选1619.729630万元 | 未披露本项目容量及完整范围/税；不能拿投标人业绩容量当分母 |
| SRC-PV-019 湖北一手结果 | 中标12895130.75元，标题2.6MW | AC/DC和税/甲供未知，保留总额，不自动算元/Wp |
| SRC-PV-020 天津媒体摘要 | 506098276.60元 / 249.9868MWp = **2.0245元/Wp** | 明确不含组件、逆变器；不能当全投资，不能用200MWac标题作分母 |
| SRC-PV-022 重庆媒体候选摘要 | 300MWac/480MWp、2.434–2.567元/W候选区间 | 原始范围/图片公告及税未取得；不当正式合同价 |
| SRC-PV-023 廊坊媒体摘要 | 179580654.94元 / 188MWp = **0.955216元/Wp** | 排除多项甲供设备与送出；0.955不是含组件、逆变器、储能、送出的全投资 |

上述两项除法由实际Python执行核验，保留分母DC口径。所有EPC候选/中标总额仍非竣工结算成本；本索引不生成新项目CAPEX默认值。屋顶加固、租赁、开发费、接入/送出、储能、预备费、建设期利息及增值税必须另查项目范围。[SRC-PV-018..023]

## 6. 真实目录与我方18章的主题交叉对照

CSV每条来源保留自己的原章节标识与定位，再对照`chapter_01`..`chapter_18`。`TOPIC_ONLY`只表示相关主题被观察，不是完整覆盖；`NOT_OBSERVED_IN_SELECTED_REVIEW`不是断言原书没有；正文未取为`UNVERIFIED_NO_BODY_OR_ONLY_METADATA`。

### 6.1 原来源目录结构，不把我方目录冒充外部目录

| 来源 | 已取到的真实结构 | 与本项目关系 |
|---|---|---|
| SRC-PV-003 IFC | 原文15章；资源/产能/选址/设计/许可/EPC/建设/运维/PPA/融资/财务；附录4为屋顶专题 | 以实际章节号映射，非“原书18章” |
| SRC-PV-016 新疆 | 实际15章：总论、资源、地质、规模、系统、 电气、总平面布置、土建、施工、管理、环保、劳动安全、节能、概算、财务 | 与我方18章拆分合并不同；不得机械重编号 |
| SRC-PV-024 JICA | 实际Ch1背景、Ch2技术、Ch3经济财务、Ch4详细设计/技术转移、Ch5并网推广制度与行动计划建议 | 两分卷同一Summary，不算两个全本 |
| SRC-PV-030 内陆漂浮 | 9章，并有故障测试、成本、供应商附录 | 水体、浮体/锚固和电气安全专门约束 |
| SRC-PV-031 近岸 | 10章；附录A资料要求、B马尔代夫技术环境核查 | 近岸与内陆不同；并非P0现有能力 |
| SRC-PV-032 美国 | 6个实际主章：背景、污染地开发、系统、站点资料、经济绩效、结论 | 场址和融资结构可对照，旧制度不移植 |
| SRC-PV-033 澳大利亚 | 9章（另有引言），含项目、技术、基础比选、财务讨论、经验、总结 | 财务章节存在不等于完整DCF模型 |
| SRC-PV-001/002/034 标准 | 未取得标准正文目录 | 标准结构空数组，不从标题补造章节 |

### 6.2 十八章检索到的主题证据

| 我方章 | 来源中已观察到的相关主题（不等于满足本章所有验收） |
|---|---|
| 01 执行摘要与初步结论 | SRC-PV-003, SRC-PV-016, SRC-PV-029 |
| 02 总论与编制依据 | SRC-PV-003, SRC-PV-008, SRC-PV-011, SRC-PV-012, SRC-PV-015, SRC-PV-016, SRC-PV-024, SRC-PV-025, SRC-PV-030, SRC-PV-031, SRC-PV-032 |
| 03 工程概况及建设必要性 | SRC-PV-003, SRC-PV-016, SRC-PV-017, SRC-PV-021, SRC-PV-024, SRC-PV-025, SRC-PV-029, SRC-PV-030, SRC-PV-031, SRC-PV-032, SRC-PV-033 |
| 04 选址及建设条件 | SRC-PV-003, SRC-PV-016, SRC-PV-017, SRC-PV-021, SRC-PV-024, SRC-PV-025, SRC-PV-030, SRC-PV-031, SRC-PV-032, SRC-PV-033 |
| 05 太阳能资源与气象 | SRC-PV-003, SRC-PV-005, SRC-PV-008, SRC-PV-009, SRC-PV-010, SRC-PV-011, SRC-PV-012, SRC-PV-016, SRC-PV-024, SRC-PV-025, SRC-PV-030, SRC-PV-031, SRC-PV-032, SRC-PV-037 |
| 06 工程任务、规模与方案比选 | SRC-PV-003, SRC-PV-005, SRC-PV-011, SRC-PV-012, SRC-PV-016, SRC-PV-017, SRC-PV-020, SRC-PV-021, SRC-PV-022, SRC-PV-024, SRC-PV-025, SRC-PV-032, SRC-PV-033 |
| 07 光伏系统初步设计 | SRC-PV-003, SRC-PV-004, SRC-PV-005, SRC-PV-008, SRC-PV-011, SRC-PV-012, SRC-PV-016, SRC-PV-024, SRC-PV-025, SRC-PV-030, SRC-PV-031, SRC-PV-032, SRC-PV-033 |
| 08 发电量预测与效率评价 | SRC-PV-003, SRC-PV-004, SRC-PV-005, SRC-PV-008, SRC-PV-011, SRC-PV-012, SRC-PV-016, SRC-PV-024, SRC-PV-029, SRC-PV-030, SRC-PV-031, SRC-PV-032 |
| 09 电气系统与电网接入 | SRC-PV-003, SRC-PV-016, SRC-PV-020, SRC-PV-022, SRC-PV-023, SRC-PV-024, SRC-PV-030, SRC-PV-031, SRC-PV-032 |
| 10 电力消纳与电价售电方案 | SRC-PV-003, SRC-PV-010, SRC-PV-011, SRC-PV-012, SRC-PV-017, SRC-PV-024, SRC-PV-032 |
| 11 总平面与土建施工条件 | SRC-PV-003, SRC-PV-016, SRC-PV-020, SRC-PV-021, SRC-PV-024, SRC-PV-030, SRC-PV-031, SRC-PV-032, SRC-PV-033 |
| 12 环境、生态、安全及社会影响 | SRC-PV-003, SRC-PV-016, SRC-PV-017, SRC-PV-024, SRC-PV-025, SRC-PV-029, SRC-PV-030, SRC-PV-031, SRC-PV-032, SRC-PV-033 |
| 13 实施组织与建设计划 | SRC-PV-003, SRC-PV-016, SRC-PV-017, SRC-PV-018, SRC-PV-019, SRC-PV-020, SRC-PV-022, SRC-PV-023, SRC-PV-024, SRC-PV-025, SRC-PV-029, SRC-PV-030, SRC-PV-031, SRC-PV-033 |
| 14 工程投资估算CAPEX | SRC-PV-003, SRC-PV-014, SRC-PV-015, SRC-PV-016, SRC-PV-017, SRC-PV-018, SRC-PV-019, SRC-PV-020, SRC-PV-022, SRC-PV-023, SRC-PV-024, SRC-PV-029, SRC-PV-030, SRC-PV-031, SRC-PV-032, SRC-PV-033 |
| 15 运营费用OPEX与折旧税费 | SRC-PV-003, SRC-PV-014, SRC-PV-015, SRC-PV-016, SRC-PV-024, SRC-PV-025, SRC-PV-030, SRC-PV-031, SRC-PV-032, SRC-PV-033 |
| 16 财务效益与投资回报 | SRC-PV-003, SRC-PV-014, SRC-PV-015, SRC-PV-016, SRC-PV-024, SRC-PV-025, SRC-PV-029, SRC-PV-030, SRC-PV-031, SRC-PV-032 |
| 17 敏感性、情景与风险 | SRC-PV-003, SRC-PV-008, SRC-PV-014, SRC-PV-015, SRC-PV-016, SRC-PV-024, SRC-PV-029, SRC-PV-030, SRC-PV-031, SRC-PV-032, SRC-PV-033 |
| 18 综合结论及后续工作 | SRC-PV-003, SRC-PV-016, SRC-PV-017, SRC-PV-024, SRC-PV-025, SRC-PV-029, SRC-PV-031, SRC-PV-032, SRC-PV-033 |

## 7. 十三项必需附录对照

附录轴是我方强制输出要求，外部资料只有相关内容也仅标`PARTIAL_TOPIC_OBSERVED`。所有13项均保留；没有任何一份来源被宣称已完整提供全部附录。外部标准未取得时不得补造其附录。

| 我方附录ID | 必需内容 | 实际可定位的部分主题来源 |
|---|---|---|
| A01 | 项目资料索引 | SRC-PV-003（参考资料/术语与章节引用）；SRC-PV-016（Ch1 编制依据（部分）） |
| A02 | 12个月气象与发电量 | SRC-PV-005（monthly outputs schema）；SRC-PV-008（Table1.1及资源层）；SRC-PV-009（逐日资源字段）；SRC-PV-010（逐时数据结构）；SRC-PV-011（monthly/hourly schemas）；SRC-PV-012（monthly/hourly/TMY）；SRC-PV-024（part01 2.11）；SRC-PV-037（数据目录（不是项目月度气象）） |
| A03 | 设备及损失参数 | SRC-PV-003（Ch3,5,7）；SRC-PV-004（Table6）；SRC-PV-005（Inputs）；SRC-PV-008（Ch3）；SRC-PV-011（PVcalc inputs）；SRC-PV-012（PV system losses）；SRC-PV-016（Ch5 p41–59）；SRC-PV-024（part01 2.9/2.12）；SRC-PV-030（Ch3–4）；SRC-PV-031（Ch4–5）；SRC-PV-032（Ch3/4）；SRC-PV-033（Ch4–6） |
| A04 | CAPEX明细 | SRC-PV-003（Ch15）；SRC-PV-014（Figure S1,S4 统计口径）；SRC-PV-015（Solar photovoltaics）；SRC-PV-016（Ch14 p156–172）；SRC-PV-017（批复四 总投资非分项表）；SRC-PV-018（候选人表总额，非CAPEX分项）；SRC-PV-019（中标结果总价，范围待核）；SRC-PV-020（报道合同金额及甲供排除）；SRC-PV-022（报价区间仅媒体证据）；SRC-PV-023（合同范围/排除项）；SRC-PV-024（part01 2.16）；SRC-PV-029（Annex3）；SRC-PV-030（Annex B）；SRC-PV-031（Table6.1）；SRC-PV-032（Table7） |
| A05 | OPEX/折旧/更换/税费 | SRC-PV-003（Ch11,15）；SRC-PV-015（O&M costs subsection）；SRC-PV-016（Ch15 p173–183）；SRC-PV-024（part02 3.2）；SRC-PV-025（Ch3.6 维护组织而非完整OPEX明细）；SRC-PV-030（Ch9）；SRC-PV-031（Ch10）；SRC-PV-032（Ch5） |
| A06 | 全周期年度项目与资本金现金流 | SRC-PV-003（Ch15）；SRC-PV-016（Ch15 p187–197）；SRC-PV-032（Appendix E Table E-2 汇总（非完整项目/资本金双表）） |
| A07 | 有债务时偿债明细 | SRC-PV-003（Ch14）；SRC-PV-016（Ch15 p184–186） |
| A08 | 敏感性数据 | SRC-PV-003（Ch5,15）；SRC-PV-014（跨年份/市场趋势）；SRC-PV-016（Ch15 p175–176）；SRC-PV-024（part02 Ch3）；SRC-PV-029（Annex4）；SRC-PV-030（Ch5 风险分析）；SRC-PV-031（Ch6风险/情景）；SRC-PV-032（Ch5系统/财务方案对比（非完整单因素敏感性）） |
| A09 | 政策适用性 | SRC-PV-003（Ch12（历史海外））；SRC-PV-016（Ch1/15 历史引用（非当期政策清单））；SRC-PV-024（part02 Ch3/Ch5 制度与推广建议（2009历史）） |
| A10 | 未完成事项 | SRC-PV-017（批复六至八 条件）；SRC-PV-024（part02 Ch5.2.3 Future Issues / Ch5.5 Action Plan）；SRC-PV-025（Conclusions and Recommendations）；SRC-PV-029（正文V）；SRC-PV-030（各章核查表）；SRC-PV-031（Annex A/B）；SRC-PV-033（Ch8–9 lessons/checks） |
| A11 | 公式逐符号字典 | SRC-PV-003（Ch5,15（方法非完整符号注册表））；SRC-PV-004（Eq8–11）；SRC-PV-015（Methodology）；SRC-PV-016（Ch5/15 方法（非完整符号字典）） |
| A12 | 全部术语中英词典 | SRC-PV-003（缩略语表PDF p7–9）；SRC-PV-004（模型符号/输入描述）；SRC-PV-005（参数说明）；SRC-PV-008（Table1.1）；SRC-PV-009（参数单位说明）；SRC-PV-010（UTC/LST）；SRC-PV-011（参数单位说明）；SRC-PV-012（参数释义） |
| A13 | 版本与数据质量说明 | SRC-PV-014（年份与来源说明）；SRC-PV-015（统计方法与年份）；SRC-PV-031（明确假设年份） |

特别缺口：**完整公式逐符号字典、全部术语中英词典、统一版本/数据质量说明**仍必须由本项目独立建设；来源有公式或英文缩略语不等于这三项已满足。12个月资源与发电量、项目/资本金两套全周期现金流、偿债和税费也须用同一确定性模型与具体输入生成，不能把海外图表拼贴充输出。

## 8. 许可、可访问性与安全

- 未确认商业再利用权限全部记`REQUIRES_REVIEW`。IFC2015保留全部权利；2019 GSA技术报告和2019漂浮手册的非商业复制说明，不能外推成商用分发许可。[SRC-PV-003][SRC-PV-008][SRC-PV-030]
- 2026近岸手册版权页明确CC BY3.0 IGO与第三方例外；IRENA许可允许署名使用而保留第三方材料限制。宽松许可仍不意味着本任务应把整本报告收入商业包。[SRC-PV-014][SRC-PV-015][SRC-PV-031]
- PVGIS手册声明结果免费且不限用途；EC自有网页一般CC BY4.0，第三方数据、图件、个人权利和单独声明例外。不能用这一条给NASA/GSA/IEC或中国招标正文一并授权。[SRC-PV-011][SRC-PV-012][SRC-PV-036]
- World Bank ICR同时带公开水印与Official Use Only，标注冲突并阻断商用打包；未因原站公开可读就忽略限制。[SRC-PV-029]
- GSA两页“200成功”仍只是应用壳；403页和网络错误不记正文有效。标准商品页标页数不记可读页数。下载在研究内存完成，不保存/提交第三方整本文本。[SRC-PV-006][SRC-PV-007][SRC-PV-034]
- 外部文档只作不可信资料，网页/文档内操作指令不执行。没有向外上传用户附件或商业秘密。研究不实施平台提交、部署、购买标准或获取受限凭证。

## 9. 待补核与阻断

| 阻断ID | 状态 | 事项 |
|---|---|---|
| BR-TECH-01 | BLOCKED | 指定web.run工具路径：父代理用可用web.run逐一补核关键原站；不得把本次工具路径写成web.run。 |
| BR-TECH-02 | BLOCKED | 标准正文与授权：取得合法标准全文后逐条核对原目录、公式及版本，不用本方18章代填标准目录。 |
| BR-TECH-03 | BLOCKED | GSA静态访问只有JS壳：用合法浏览器验证页面正文、当前栅格版本和CC BY附加条款；不得逆推未公开商业API。 |
| BR-TECH-04 | BLOCKED | WAF和网络受阻：改用官方可读副本/合规浏览器；IRENA2025当前仅12页摘要成功，不能替代全本。 |
| BR-TECH-05 | REQUIRES_REVIEW | 公开与受限标签并存：World Bank公开原站PDF同时有Official Use Only；向发布方确认后才允许更广再利用。 |
| BR-TECH-06 | PENDING_VERIFICATION | 合同范围/税与ACDC未清：取得一手完整招标文件/合同及含税和甲供设备边界；候选报价不等于结算总投资。 |
| BR-TECH-07 | PENDING_VERIFICATION | 生产资源适配器尚未实现：按实际覆盖、许可和单位/时区开发并验收；本次仅两个公开样例端点成功，不等同全区域稳定性门禁。 |
| BR-TECH-08 | PENDING_VERIFICATION | PDF非文本页与解析保护：必要时合法逐页视觉/OCR复核；SRC-PV-030物理p28 token预算拒绝，不关闭防护以换取全文声明。 |

**完成边界：**本次三份研究文件可复核，发现不足保留阻断；并未宣称授权标准正文、2025 IRENA主报告、受阻ADB资料、生产资源适配器或WorkBuddy运行链已验收。政策/电价适用性由父代理官方来源单列，不将本索引历史工程政策表当现行规则。

## 10. 可更新机器字段与自检

JSON每条都有唯一`SRC-PV-*`、作者/日期/精确URL、地域/类型/容量、license与证据、访问时间、HTTP尝试、可读/总页、原有章节、输入、公式、表格、18章和13附录主题对照、provenance和质量边界。`chapters/inputs/formulas/tables`均为**非穷尽摘要**，字段`*_extraction_complete=false`防止当完整条款库。

更新流程：重新访问原站→核正文/日期/范围→保留失败访问→核许可→按逻辑报告/分卷去重→只登记实际看到的结构→重算各布尔统计→校验CSV轴和引用ID。不能通过把`UNKNOWN`换成推测值关闭门禁。

自检状态：内存断言 `ARTIFACT_PRECHECK_PASS`；落盘独立读取后 **32项通过、0项失败**（JSON/CSV解析、ID与URL去重、必填字段、18章/13附录轴、统计重算、跨文件标志、原目录回查及标准编号/状态等）。另有首轮23项通过、0项失败，含两项成本归一化数值核验。目录回查修正了新疆原第7章为“总平面布置”、JICA原第5章为推广制度/行动计划建议，并同步JSON和CSV。没有将文档自检冒充仓库完整回归或产品运行验收。

## 11. 全部登记来源（精确URL及可访问范围）

页列格式：可抽文字页/物理PDF页；HTML无稳定PDF页码记`HTML`；无正文记`—`。许可缩写仅表格展示，JSON保留完整状态和解释。

| ID与原站链接 | 类型/地域 | 发布日期 | 页数 | 访问状态 | 全文/结构/具体项目 | 许可 |
|---|---|---|---|---|---|---|
| [SRC-PV-001 NB/T 32044-2018 光伏发电工程预可行性研究报告编制规程](https://hbba.sacinfo.org.cn/stdDetail/d000c5b3cf7353ac4eb7f9219d1d031b) | `industry_standard_metadata` / 中国 | 2018-06-06 | HTML | `METADATA_VERIFIED` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-002 NB/T 32043-2018 光伏发电工程可行性研究报告编制规程](https://hbba.sacinfo.org.cn/stdDetail/926f539f12644210fae18d9b5e9a8b02) | `industry_standard_metadata` / 中国 | 2018-06-06 | HTML | `METADATA_VERIFIED` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-003 Utility-Scale Solar Photovoltaic Power Plants: A Project Developer’s Guide](https://documents1.worldbank.org/curated/en/690161467992462412/pdf/99396-WP-Box393199B-PUBLIC-IFC-Solar-Report-Web-08-05.pdf) | `technical_guide` / 全球/新兴市场 | 2015-06 | 215/216 | `PARTIAL_TEXT_VERIFIED` | 否/是/否 | `REQUIRES_REVIEW` |
| [SRC-PV-004 PVWatts Version 5 Manual; NREL/TP-6A20-62641](https://docs.nlr.gov/docs/fy14osti/62641.pdf) | `technical_manual` / 美国/模型通用 | 2014-09 | 20/20 | `BODY_VERIFIED` | 是/是/否 | `REQUIRES_REVIEW` |
| [SRC-PV-005 PVWatts V8 API documentation](https://developer.nlr.gov/docs/solar/pvwatts/v8/) | `resource_api_documentation` / 覆盖由气象数据集决定 | 未核实 | HTML | `BODY_VERIFIED` | 是/是/否 | `REQUIRES_REVIEW` |
| [SRC-PV-006 Global Solar Atlas methodology](https://www.globalsolaratlas.info/support/methodology) | `resource_methodology` / 全球 | 未核实 | — | `JS_SHELL_ONLY` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-007 Global Solar Atlas China map/data downloads](https://www.globalsolaratlas.info/download/china) | `resource_dataset_catalog` / 中国 | 未核实 | — | `JS_SHELL_ONLY` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-008 Global Solar Atlas 2.0 Technical Report 170-14/2019](https://documents1.worldbank.org/curated/en/529431592893043403/pdf/Global-Solar-Atlas-2-0-Technical-Report.pdf) | `technical_report` / 全球 | 2019 | 38/39 | `PARTIAL_TEXT_VERIFIED` | 否/是/否 | `REQUIRES_REVIEW` |
| [SRC-PV-009 NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) | `resource_api_documentation` / 全球（源数据网格分辨率） | 未核实 | HTML | `BODY_VERIFIED` | 是/是/否 | `REQUIRES_REVIEW` |
| [SRC-PV-010 NASA POWER Hourly API](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/) | `resource_api_documentation` / 全球 | 未核实 | HTML | `BODY_VERIFIED` | 是/是/否 | `REQUIRES_REVIEW` |
| [SRC-PV-011 PVGIS API non-interactive service](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/getting-started-pvgis/api-non-interactive-service_en?prefLang=de) | `resource_api_documentation` / 全球多数地区；数据库依覆盖选择 | 未核实 | HTML | `BODY_VERIFIED` | 是/是/否 | `PERMITTED_WITH_ATTRIBUTION_REVIEW_THIRD_PARTY` |
| [SRC-PV-012 PVGIS 5 user manual](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/using-pvgis-5/pvgis-5-user-manual_en) | `technical_manual` / 全球多数地区 | 未核实 | HTML | `BODY_VERIFIED` | 是/是/否 | `PERMITTED_WITH_ATTRIBUTION_REVIEW_THIRD_PARTY` |
| [SRC-PV-013 Renewable power generation costs in 2025 (publication landing page)](https://www.irena.org/Publications/2026/Jul/Renewable-Power-Generation-Costs-in-2025) | `statistical_report_landing` / 全球 | 2026-07 | — | `BLOCKED_WAF` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-014 Renewable power generation costs in 2025: Executive summary](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2026/Jul/IRENA_TEC_RPGC_2025_Executive_summary_2026.pdf) | `statistical_report_summary` / 全球 | 2026-07 | 12/12 | `PARTIAL_TEXT_VERIFIED` | 否/是/否 | `PERMITTED_WITH_ATTRIBUTION_REVIEW_THIRD_PARTY` |
| [SRC-PV-015 Renewable power generation costs in 2024](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2025/Jul/IRENA_TEC_RPGC_in_2024_2025.pdf) | `statistical_report` / 全球 | 2025-07 | 216/216 | `BODY_VERIFIED` | 是/是/否 | `PERMITTED_WITH_ATTRIBUTION_REVIEW_THIRD_PARTY` |
| [SRC-PV-016 新疆天富热电股份有限公司20兆瓦光伏并网电站项目可行性研究报告](http://static.cninfo.com.cn/finalpage/2014-05-09/64002859.PDF) | `real_project_feasibility_report` / 中国/新疆石河子 | 2014-05 | 202/202 | `BODY_VERIFIED` | 是/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-017 水口镇塘肚村村委会办公楼屋顶分布式光伏电站可研批复](https://www.jh.gov.cn/jhfgj/0200/202505/4b8e405436a34dc8a07decb987486d2b.shtml) | `real_project_public_approval_summary` / 中国/湖南江华 | 2025-04-30 | HTML | `BODY_VERIFIED` | 否/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-018 景德镇学院屋顶一般工商业分布式光伏EPC候选人公示 CEZB260607155001](https://www.chnenergybidding.com.cn/bidweb/001/001005/001005002/20260920/ed062ca8-b407-4110-b8dd-3bf18e8cabdc.html) | `epc_primary_notice` / 中国/江西景德镇 | 2026-09-20 | HTML | `BODY_VERIFIED` | 否/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-019 孝南静脉产业园2.6MW屋顶分布式光伏EPC中标结果 HBXN-202607QG-014001001](https://www.hbbidcloud.cn/xiaonan/jyxx/004005/004005006/20260904/f4089155-5031-4a0e-aec7-b9cad51855f3.html) | `epc_primary_notice` / 中国/湖北孝感 | 2026-09-04 | HTML | `BODY_VERIFIED` | 否/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-020 天津宝坻200MW/249.9868MWp EPC结果媒体摘要](https://news.solarbe.com/202610/27/50031000.html) | `epc_secondary_summary` / 中国/天津宝坻 | 2026-10-27 | HTML | `BODY_VERIFIED` | 否/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-021 射阳恒正350.08MW渔光互补项目EPC招标摘要](https://news.solarbe.com/202610/26/50030935.html) | `epc_secondary_summary` / 中国/江苏盐城射阳 | 2026-10-26 | HTML | `BODY_VERIFIED` | 否/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-022 重庆江津大京300MWac/480MWp农光互补候选公示摘要](https://news.solarbe.com/202610/23/50030834.html) | `epc_secondary_summary` / 中国/重庆江津 | 2026-10-23 | HTML | `BODY_VERIFIED` | 否/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-023 三峡河北廊坊150MW农光互补设计施工总承包结果摘要](https://news.solarbe.com/202610/22/50030796.html) | `epc_secondary_summary` / 中国/河北廊坊 | 2026-10-22 | HTML | `BODY_VERIFIED` | 否/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-024 Feasibility Study for Application of Photovoltaic Power on Male’ and Hulhumale’ Islands: Final Report (Summary)](https://openjicareport.jica.go.jp/pdf/11972536_01.pdf) | `real_project_feasibility_summary` / 马尔代夫/马累及胡鲁马累 | 2009-11 | 110/120 | `PARTIAL_TEXT_VERIFIED` | 否/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-025 Master Plan Study for Utilization of Solar Energy in Nigeria: Final Report Volume 1 Summary](https://openjicareport.jica.go.jp/pdf/11846649.pdf) | `real_programme_masterplan_summary` / 尼日利亚/农村多州 | 2007-02 | 122/122 | `PARTIAL_TEXT_VERIFIED` | 否/是/否 | `REQUIRES_REVIEW` |
| [SRC-PV-026 Floating Solar Energy Development in Tajikistan: Technical Assistance Report 58416-002](https://www.adb.org/sites/default/files/project-documents/58416/58416-002-tar-en.pdf) | `project_preparation_report_unverified` / 塔吉克斯坦 | 2025-11 | — | `BLOCKED_WAF` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-027 Preparing West Bengal Floating Solar Project: Readiness Financing Report 56334-002](https://www.adb.org/sites/default/files/project-documents/56334/56334-002-prfr-en.pdf) | `project_preparation_report_unverified` / 印度/西孟加拉 | 未核实 | — | `BLOCKED_WAF` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-028 Floating Solar Project at Hydropower Plant 5 (Activity 4)](https://www.adb.org/projects/documents/kgz-57037-008-dpta) | `project_preparation_report_unverified` / 吉尔吉斯斯坦 | 2025-12 | — | `BLOCKED_WAF` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-029 ASPIRE Maldives P145482 Implementation Completion and Results Report ICR00856](https://documents1.worldbank.org/curated/en/099062826202046929/pdf/BOSIB-83cf4f0c-f5c1-484b-95b8-673952a3bb09.pdf) | `real_project_completion_report` / 马尔代夫 | 2026-06-28 | 48/48 | `BODY_VERIFIED` | 是/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-030 Where Sun Meets Water: Floating Solar Handbook for Practitioners](https://documents1.worldbank.org/curated/en/418961572293438109/pdf/Where-Sun-Meets-Water-Floating-Solar-Handbook-for-Practitioners.pdf) | `technical_guide` / 全球/内陆水体 | 2019 | 154/155 | `PARTIAL_TEXT_VERIFIED` | 否/是/否 | `REQUIRES_REVIEW` |
| [SRC-PV-031 Where Sun Meets Water: A Nearshore Floating Solar Handbook for Practitioners](https://documents1.worldbank.org/curated/en/099100826165042316/pdf/P506442-d5c40a86-886c-4392-bffd-a00616ea10c1.pdf) | `technical_guide` / 全球/近岸；附录马尔代夫 | 2026-09 | 110/118 | `PARTIAL_TEXT_VERIFIED` | 否/是/否 | `CC_BY_3_0_IGO_WITH_THIRD_PARTY_EXCEPTIONS` |
| [SRC-PV-032 Feasibility Study of Economics and Performance of Solar Photovoltaics at the Kerr McGee Site in Columbus, Mississippi; NREL/TP-7A30-57251](https://docs.nlr.gov/docs/fy13osti/57251.pdf) | `real_project_feasibility_report` / 美国/密西西比州Columbus | 2013-01 | 47/47 | `BODY_VERIFIED` | 是/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-033 Pilot Landfill Solar Project: Feasibility Study Report 3027-FS-1219](https://arena.gov.au/assets/2017/02/pilot-landfill-solar-report-feasibility-study.pdf) | `real_project_feasibility_report` / 澳大利亚/维多利亚Wollert | 2019-12-19 | 32/32 | `BODY_VERIFIED` | 是/是/是 | `REQUIRES_REVIEW` |
| [SRC-PV-034 IEC 61724-1:2021 Photovoltaic system performance – Part 1: Monitoring](https://webstore.iec.ch/en/publication/65561) | `international_standard_metadata` / 国际 | 2021-07-21 | HTML | `METADATA_VERIFIED` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-035 典型省份分布式光伏发展模式研究](https://wri.org.cn/sites/default/files/2025-09/25_rpt_study-on-development-models-of-distributed-photovoltaics-in-typical-provinces_cn.pdf) | `research_report_unverified` / 中国/典型省份 | 2025-09 | — | `NETWORK_ERROR` | 否/否/否 | `REQUIRES_REVIEW` |
| [SRC-PV-036 European Commission Legal notice / reuse policy](https://commission.europa.eu/legal-notice_en) | `license_terms` / 欧盟 | 未核实 | HTML | `BODY_VERIFIED` | 否/否/否 | `CC_BY_4_0_UNLESS_OTHERWISE_NOTED` |
| [SRC-PV-037 Brazil – Solar irradiation and PV power potential map](https://datacatalog.worldbank.org/search/dataset/0039861/brazil-solar-irradiation-and-pv-power-potential-map) | `resource_dataset_catalog` / 巴西 | 2023-01-19 | HTML | `BODY_VERIFIED` | 否/是/否 | `REQUIRES_REVIEW` |

SRC-PV-024的第二分卷及备用访问URL、每条精确访问时刻、页面/响应哈希、无文本物理页、解析错误、部分资料的许可定位、API完整请求URL均见JSON同一ID；不是额外发现数。SRC-PV-033的原页面路径含2017/02，但正文报告日期2019-12-19，已按正文而非URL年份登记。

---
本研究不替代有资质的工程设计、结构/消防检测、电网接入审查、法律税务意见或项目正式审批；历史/海外案例仅供方法与边界对照。
