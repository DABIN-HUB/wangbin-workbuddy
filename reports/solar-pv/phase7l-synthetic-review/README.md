# Phase 7L 可审阅中间成果（未通过完整验收）

**结论：本目录是 PARTIAL 草稿和输入缺口审计，不是模式一的高覆盖度完整测试成果，更不是正式预可研、真实投资建议或 WorkBuddy 平台验收。** 两个新合成案例独立执行了 Phase 2 → D3 → 3B → 3C → 3D → 3E → 3G，采用 3 年评价期；来源为 `SYNTHETIC/ASSUMED`，不存在经过签章的业主、供应商、电网、地勘或审批证明。`partial_rooftop`、`partial_ground` 是旧的 25 年资料不足运行，仅用于**模式二**复核，不是从新案例重算的完整项目；既有封存输入未被改写。

| 案例 | 冻结字段中适用 | L2 定义 REQUIRED 已提供/未提供 | L2 定义 CONDITIONAL 已提供/未提供 | OPTIONAL 已提供 | 计算状态 | 实质审查 |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 新合成工商业屋顶 | 386 | 125/167（292） | 35/50（85） | 0/9 | PARTIAL：54 CALCULATED，20 BLOCKED_MISSING_INPUT，1 NOT_IMPLEMENTED，1 UNDEFINED | NOT_REVIEWED |
| 新合成集中式地面 | 375 | 121/160（281） | 29/56（85） | 0/9 | PARTIAL：51 CALCULATED，20 BLOCKED_MISSING_INPUT，3 NOT_APPLICABLE，1 NOT_IMPLEMENTED，1 UNDEFINED | NOT_REVIEWED |
| 模式二旧屋顶 | 386 | 139/153（292） | 42/43（85） | 0/9 | PARTIAL；非新合成项目 | NOT_REVIEWED |
| 模式二旧地面 | 375 | 134/147（281） | 36/49（85） | 0/9 | PARTIAL；非新合成项目 | NOT_REVIEWED |

L2 表中按**冻结定义**计数；逐行矩阵另列项目类型、条件真值、重复子字段与生效义务。新案例的若干 CONDITIONAL 因条件未知维持 `PENDING_CONDITION`，并非一概按必填计；数组子字段必须核查母记录，不以“缺子字段”统一阻断。新案例均有两组经 D3 逐行读取的 8,760 行时序（屋顶资源/负荷；地面资源/市场价格）；不是 25 年资源观测，也不能据此宣称 469 字段高覆盖。新屋顶 125/292、地面 121/281，**甚至低于模式二旧实例的 139/292、134/281**；模式一目标未达到。L1/L2/L3 生效成熟度、条件真值、来源、缺失与计算/报告消费列在各自 `input-coverage-matrix.json`。

两个新项目分别使用新计算输入 `fixtures/solar_pv_calculation/`，再以单独的 `fixtures/solar_pv_editorial/phase7l/` 绑定报告背景。计算实例中新增设备数量/功率、面积、CAPEX 四个合成分类费用、OPEX、首年资源、逐时负荷或市场价格等；编辑资料仅包含 CH01–CH18 的 `background/proposal/verification` 文字与项目别名，**没有**作为 Phase 2/D3 输入或正式来源记录。审计矩阵可查具体字段与消费状态：屋顶 `tariff.negative_price_rule`、`tax.loss_carryforward_years`、`finance.cashflow_timing`，地面后两项虽已录入，但无计算消费报告。所有来源仍为合成假设，真实成熟度 `NOT_VERIFIED`。

新项目同次运行身份（不得与模式二或历史第一版合成运行拼接）：

| 类型 | run_id | input_hash | source_snapshot_id | result_hash |
| --- | --- | --- | --- | --- |
| 屋顶 | `9a5397d4-db41-41cb-b343-6b7c50c09ccd` | `c459d80eae8ddc92422fb47c62eadeeab7e8abdc6114fba65123b03893e81483` | `33015f0a1b850ca52b76b1395bc6e58fe6308ebf1ff11a23ebf5cc276ef7b740` | `49d912248ba2ba511983ce318882685444a75b9585588b3978af3bfe52e73454` |
| 地面 | `f4f08b00-3585-4c8c-8c48-f39e07f886b4` | `e4a14cbce5a5b501a4ee7ddb855372e961fc52ef5c1e7961ddfd46d6adffdaeb` | `407b071fc506c3f164237cef279ba08aa0c2635405060b7c12e07403b2f1b1cc` | `69c8cec70cf8fd50d7f991770f41370d583219630e034bc0cde270c226081685` |

**未解除的财务阻断：** 两案例各 20 项 `BLOCKED_MISSING_INPUT`，包括项目/股东现金流、NPV、IRR、静态/动态回收期、名义折现率、CFADS、日期化 NPV、全期成本及 LCOE、盈亏平衡电价、目标差距等。根因分别涉及缺终期实际现金事件、所有者出资/分配与融资日期事件、现金流定义和方法参数、同边界重算及用户目标；详见 `calculation-and-source-evidence.json` 和 `canonical.json` 的逐指标 `status/reason/details`。并无以 0 补齐九项公式，也没有把账面残值充作现金回收。新项目 DC=165/330 kWp、AC=150/300 kW，面积为 3500−500=3000 / 10000−1000=9000 ㎡，CAPEX 四项求和分别为 467000 / 950000 元；月度发电加总、年度交付的自用+上网分解及首年收益分项在 Decimal 精度下核对（差异仅序列尾数），但这些物理与经济恒等式不是报价、并网或场址可建证明。

**正文与内容门禁：** 每份 DOCX 保持 18 章/100 子项、13 附录/26 子项；126 条论点 ID 与核心问题唯一，绑定本次 canonical；结构绑定检查 `CENTRAL_CLAIM_CONTRACT=PASS`，人工实质审查仍为 `DOCUMENT_CONTENT_REVIEW=NOT_REVIEWED`。对新案例的每章首两子项做了逐段抽查，并专项查看 CH04/05/07/08/09/10/11/14/16/18；发现并修正 CH04.01 虚称已录入坐标边界、CH11.02 跨屋顶/地面混写、Word 财务表原始指标名/同名年度费用堆叠和原始单位 token。CH14/16 等章节仍主要是一句限制性判断和少量指标，没有完成用户要求的全部重点子项逐一专业内容审核，也没有充分的造价/现金流因果论证；不得判为内容 PASS。旧报告中投资主体错引设备缺口、资源来源错引发电量等在本轮各自采用独立的章节字段绑定，Word 与 checklist 均可核对；不能仅凭这些局部修复宣布全部十项专项回归成功。

**产物及校验：** 每个子目录均有 DOCX、19 表计算快照 XLSX、10 表来源/假设 XLSX、`canonical.json`、469 行 `input-coverage-matrix.json`、126 条 `content-checklist.json`、逐项 `central-claim-review.json`、`calculation-and-source-evidence.json` 与 `manifest.json`。XLSX 是已计算的**静态快照（工作表内不含 Excel 公式）**，不是可以在表内改输入就重新计算的模型。下表为最终文件字节数和 SHA-256；其余文件可按本目录实际文件重新 `sha256sum`。DOCX 包验证无损坏，Excel ZIP/工作表结构、哈希身份及来源数值经过静态复核，未运行耗时 L3 或创建测试代码。

| 子目录 | 文件 | 字节 | SHA-256 |
| --- | --- | ---: | --- |
| industrial_rooftop | 光伏预可研报告.docx | 66889 | `9cf44378be775d07365e3b589625ad3b4782111aad11efdaf183cf0373fa4986` |
| industrial_rooftop | 测算模型.xlsx | 71004 | `0cd9f8e6827be1b79376d3864e722027f30de49f786bac0c6bc0e409560d71a8` |
| industrial_rooftop | 资料来源与假设清单.xlsx | 108867 | `201ea927015b1d834faaf1fad0d90f10169a2a051a8eb5199ce5b2746268584f` |
| utility_scale_ground | 光伏预可研报告.docx | 66956 | `9fa2f13b438257b3f86d00d531e6bc188497d03fad57b5a2cce587bd59a850c0` |
| utility_scale_ground | 测算模型.xlsx | 70547 | `19848f862fa8d43fac6a55cf185c3fce00f1ec08eba80db8e52160707124f599` |
| utility_scale_ground | 资料来源与假设清单.xlsx | 104966 | `65e6e98618788ee8c61242c219233415f653139a13910b9be7537200edf97700` |
| partial_rooftop | 光伏预可研报告.docx | 70749 | `95b5c05a5ae51a23ad3c557491c02487d1fe3fb3f060fd79d17a68ddddbfe75d` |
| partial_rooftop | 测算模型.xlsx | 113172 | `2b3e1bc646a026d7ce1b9465288a96a182655c08d8b26d8411edd34a449266dc` |
| partial_rooftop | 资料来源与假设清单.xlsx | 103738 | `ab8fdaa80d0e5ae3e78ec9c565fe3083b896dd4ddae3eb3548d74edc31dbb371` |
| partial_ground | 光伏预可研报告.docx | 70753 | `a1af91be8c8a6a586833e58b4f5ff3f5d30b7e3254163e542d1eea3ec01b5955` |
| partial_ground | 测算模型.xlsx | 112792 | `385c5f1ba0f8b9d2a330a2728f030366c5339cb376f42e6e15db9c06d2f17925` |
| partial_ground | 资料来源与假设清单.xlsx | 114567 | `662f4ea74b22e734694fa11e698166beacc3c2b9a33a2f7144e9e954946355e7` |

PDF 转换器未验证可用，Word COM 探测超时；因此**没有 PDF**，目录页码刷新、逐页溢出/图表可读性检查、D 风格视觉验收和四文件/平台验收均 `BLOCKED` 或 `NOT_TESTED`。被冻结的本地字段字典与已知历史定义均为 469；未找到可逐 `field_id` 对照的 486 原始清单，不能编造 17 项差异，见 `../phase7l-input-coverage/README.md`。不得自动发布或递交平台。
