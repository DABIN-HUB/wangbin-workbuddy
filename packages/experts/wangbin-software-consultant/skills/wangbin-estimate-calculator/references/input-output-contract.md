# wangbin-estimate-calculator｜版本化输入、输出与失败合同

## 现行增强合同 2.0（第四批 B4-B01～06，所有者 Q16～Q31）

同一正式 Expert 的包内 Python 标准库 Decimal CLI，不是另一产品。此节定义本批新增路径；下列历史 0.1.0 合同原文仍用于无 `schema_version` 的旧输入版本，不把旧版限制套到新路径。用户输入自然语言，Agent 整理内部 JSON；有授权执行及有效回执才称实际覆盖值已核算。计算器不证明业务范围、来源真实性、估时合理、接口获权、排期可行或平台安装。禁止读取其他数据、外部网络、自动采购、汇率/税率推断、交易或持久化项目后台。

### 2.0-A 输入结构（严格封闭 JSON）

`schema_version` 必须是字符串 `"2.0"`；存在该键而值不支持时拒绝，不回退。缺失该键沿用旧 `estimate` 四档 `tier`/五档 `membership` 分流，旧有效输出形状与公式不变。所有对象仅接受以下定义字段；必需字段缺失属于非法输入，业务数据未知用明确状态表达。数字均为非负有限 Decimal 字符串（非 JSON number/bool），精确运算，超精度预算或舍入异常拒绝；low≤base≤high（仅比较已知相邻/端点）。不以数值文本冒充来源。

**来源文本的 2.0 封闭格式**（仅本版本）：有据输入的 `source` 统一填写 `TURN:<正整数>`（例如 `TURN:3`，明确对话话轮）、`FILE:<文件定位名>:<正整数>`（例如 `FILE:requirements.md:12`，明确文件行），或 `SYNTHETIC: <具体依据>`、`ASSUMED: <具体依据>`、`ASSUMED_CONDITIONAL: <具体依据>`（明确合成、假设或条件依据；冒号后一个空格和非空单行实际依据）。话轮及行号为无前导零的正整数；文件定位名非空，无首尾空白、冒号或控制字符，不能仅为 `.` 或 `..`；脚本不读取所指文件。已知/明确不适用值、包及费用来源、至少一类覆盖已完整或已明确不适用的 coverage 使用上述格式；单纯数字、无定位的自由文本、空依据、纯状态占位和明确否定许可的占位陈述均不构成有据来源。UNKNOWN 值（及两类覆盖均 PARTIAL）的 `source` 可用非空说明表达缺口。混合补价的 `permission_source` 必须单独采用 `AUTHORIZED: TURN:<正整数>` 或 `AUTHORIZED: FILE:<文件定位名>:<正整数>`，只在确有当前角色补价许可时填写；普通来源、假设、未知或否定许可不满足。格式校验不认证材料、自然语言含义或实际用户授权；调用端仍须依据真实来源和最新许可构造输入，不能把有格式的字符串当作授权证明，也不能把假设提升为确认事实。

- 顶层必需：`schema_version, scope_version, quote_version, request, role_catalog, work_packages, coverage, buffers, pricing, fees`；可选 `previous_scope_version, scope_changed`（沿用旧版变更配对约束）、`reported`。版本均非空字符串，所有当前工作包/费用的 `scope_version` 与顶层一致；改单价可保留范围版但须新报价版/新输入快照。脚本不自行读取或改写历史。
- `request` 必需 `mode,money`，`money` 为 `none/labor/external/all`，分别表示不报任何金额、只人工、只外费、两者均允许。`mode=full` 固定五档；`mode=tiers` 另须 `tiers` 非空且无重复的正式档位 ID；`mode=scope` 另须 `scope_id`（非空且不是五档名）、`package_ids`（明确的无重复 ID 列表），可选 `role_ids` 非空唯一角色 ID 过滤列表。各模式不接受其他模式字段。局部的 `package_ids` 允许明确空集，未知范围通过 coverage PARTIAL 表达，不造成员；引用不存在的实际 ID 属结构错误。目标键为所请求档位或 scope_id。
- `role_catalog` 为 `{id,name}` 列表，稳定唯一角色 ID、非空名称，空目录仅在无角色工作时合法；同名角色须明确统一身份（按 trim/casefold 拒绝重复名称或冲突 ID）；不固定角色列数或自动猜同义词。Agent 规范常用 PM/BA/UI/FE/BE/DB/QA/OPS/集成/AI/OT 等角色和项目专项。实际角色可扩展，不能因同一人跨角色就把不同分派任务抹掉。
- `work_packages` 为 `{id,function,source,scope_version,assignments_complete,assignments}` 列表，`assignments_complete` 布尔，表示本次所请求适用分派是否已穷尽（scope 角色过滤时明确所求边界）；每条 `assignments` 为 `{id,role,effort}`，`id` 是全快照唯一分派任务，`role` 引用目录；一个包/角色可有多个任务。`effort` 是下述情景值对象。空分派只有显式完整不适用任务或未完整覆盖的真实包才有意义。重复完全相同包或同包同 ID 任务只计一次，冲突内容或跨包复用同一分派 ID 拒绝。每包 `source` 为可定位用户/文件或明示合成/示意来源。档位模式每包还必需 `membership`，须恰为 M/S/F/I 四种完整成员集之一（见下表），不能只因为查询单档删掉真实成员标签；scope 模式不需要也不虚构 membership，允许可据的原成员保留但若提供须为合法全集。全档计算如声称有基础开发且范围完整须有真实 M；范围未全则可空/部分，不以缺包伪造完整。局部仅处理指定包/角色；其他已声明包、来源不得被算入请求范围。
- `coverage` 是目标键→`{work,external,source}`，键集与所求目标完全一致。`work` 为 `COMPLETE/PARTIAL/NOT_APPLICABLE`，表示输入者对该目标的工作包覆盖声明；N/A 须有来源且无实际适用分派；`external` 同三状态，表示目标的全部所需外部费用覆盖（N/A 须无需独立计入的外费且有依据）。COMPLETE 是声明而非引擎认证客户范围；任一输入或上游子项未知仍阻止完整计算。不能把缺少费用行当作 N/A；如果 COMPLETE 且没有独立有据费用行，必须明确 N/A（已含人工/明确排除/历史项不作为独立外费）。对未请求外费可声明 PARTIAL，不因此阻断人工/人天。

对每个所求目标（包含 scope 的角色过滤），若无任何适用任务（空包集/空分派/全部任务明确 N/A/仅有未请求角色），不能声明 `coverage.work=COMPLETE`；已确认所求范围没有工作且适用分派已完整时使用 `NOT_APPLICABLE`，尚不清楚或分派未闭合时用 `PARTIAL`，否则拒绝矛盾输入。实际适用的有据 `"0"` 或 UNKNOWN 任务仍为适用任务，不把它们视为无工作；有其他适用任务的目标内，已确认单个包在所求角色范围无分派仍可独立为 N/A，不影响目标的实际工作核算。

**情景值对象**：`{low,high,base?}`，low/high 必需，base 缺省表示无独立基准。每个值为 `{status,source,value?}`，status 为 `CONFIRMED/ASSUMED/ASSUMED_CONDITIONAL/SYNTHETIC/UNKNOWN/NOT_APPLICABLE`。已知四类须 value 为合法 Decimal 字符串、有上述可定位或明确依据来源，不能把明确未知、未批准来源作为已知；UNKNOWN 或 NOT_APPLICABLE 不给数值（可明确 null），有说明来源。NOT_APPLICABLE 用于确知整项不适用，各情景一致，非零数值不得与之混用；明确适用且耗时/价格为零用有据的 `"0"`。缺 base 不阻断 low/high。尚未确定任何数值时以 UNKNOWN 表示，不能擅填中点或零。缓冲率限 [0,1]。固定价格/明确固定外费可按其真实同值依据适用所有情景，独立基准人天和缓冲依据仍各自必需。

- `buffers` 为 `{default,overrides?}`，default 是情景值对象，overrides 为所求档位名→完整情景值对象，仅档位模式可用。档未提供 override 则使用 default；档已显式覆盖时逐情景采用该档状态（缺 base 为未知，不悄悄回填）；全档同一情景各角色共享该缓冲。无适用工作时不硬造缓冲影响；真实未知不能默认为零。不自动为 B/Full 增加率。
- `pricing` 必需 `mode,tax_basis`；`tax_basis=INCLUDED/EXCLUDED/UNKNOWN` 仅描述人工价格税口径。mode=`refused/reference/fixed/role/mixed`。`refused` 不附价格；`reference` 可选独立 `base` 值对象，固定沿用低 1000、高 1500，缺 base 不取中点；`fixed` 必需 `rate` 为单个值对象（固定价独立来源）；`role` 必需 `rates` 对象，键为真实角色 ID，值为下述 rate 对象；`mixed` 必需 `rates, fallback, fallback_roles, permission_source`，fallback 为明确授权的统一固定价或参考价，fallback_roles 为非空、唯一且不与 rates 重叠的角色 ID，permission_source 为明确补价依据。其余缺价角色保持未知。角色 `rate` 为 `{kind:"fixed",value}` 单个值对象，或 `{kind:"range",values}` 情景值对象；fallback 另允许 `{kind:"reference",base?}`。全请求同一价格快照，按角色各自单价和适用档风险计算；如不同档有不同实际人工计价合同，分独立请求/报价版。不补造批准/默认价格。`reference` 与显式 fallback reference 仅在真实 R5 允许时采用；拒参考价但有实际固定/角色价按有效价计。`money=none` 不计算/返回任何货币值；`external` 禁人工；`labor` 禁外费及项目总价；`all` 且 pricing refused 只可计算有据外费，完整人工/总价不成立。未经许可的货币数据即使在输入也不得通过回执泄露（不回显 pricing/fees 原文）。
- `fees` 为 `{id,account_id,description,source,scope_version,targets,work_package_ids,interface_only,category,period,currency,tax_basis,cost_state,disposition,calculation,period_count?}` 列表。`targets` 是非空唯一所求目标 ID 集合（各请求只带实际所求目标），`work_package_ids` 是唯一真实包 ID 关联列表，项目级费用可为空；每个适用目标须包含全部声明关联包；实际 I 专属费用以 `interface_only=true` 或关联 I 包认定，在档位模式只能进 B 两档。`id` 完全相同重复仅一次，冲突拒绝；同一个 `account_id` 的不同金额/套餐可用于不相交目标，但一个目标内不允许重复独立计费，不因档位高低累计外费。`category=third_party/deployment/service/maintenance/tax`，`period=once/month/year`（deployment 一次性），`currency` 为原始大写三字母币种代码（人工 CNY 统一；仅语法验证，不换汇），`tax_basis=INCLUDED/EXCLUDED/UNKNOWN/SEPARATE`（tax 行必须 SEPARATE，其他不许 SEPARATE），`cost_state=PLANNED/INCURRED/COMMITTED/UNKNOWN`，`disposition=quote/included_in_labor/excluded`，显式限定本版计价范围，不按历史状态推断付款或节省；已含人工的费用可追踪但不重复加价，excluded 行保留依据不入总计，included_in_labor 需真实包关联。若用户确认整个计费项目不适用，使用全情景 N/A；来源保留，不填历史欠款或抵扣。
- `calculation` 为 `{mode:"amount",amount}` 或 `{mode:"quantity_price",quantity,unit_price,unit}`，其中 amount/quantity/unit_price 都是情景值对象，unit 为有据计费单位；按给定对应情景乘积，不自动推导数量单价或基准。单个计费项目有多个方案金额可分相同 account_id 的不相交目标行。`period_count` 可选情景值对象，仅 month/year，表示按该单位已明确计费的期数（允许有依据的小数期，不从日期/天数私自折算）；每期金额与指定期限金额分别列，未知期数不阻断每期，不把期限或维护加入一次性价。明确不适用须与数量/单价计算一致，不用一个未知操作数及另一个零掩盖所缺依据；若需要手算完整已知外费固定值，用真实同值低高、基准有固定依据时可同值。
- 可选 `reported` 为所求目标→可选的 `B,R,E,labor,roles` 声称值，前四为情景键→严格 Decimal 字符串，`roles` 角色 ID→同样的 B 情景声称值；只对已完整可核的相同范围/情景比较，缺口不得声称完整，任何不符拒绝。无 reported 则按内部唯一行、角色和校核；用户表示的业务完整性不由它认证。

### 2.0-B 核算语义与回执

五档成员固定 `M=(MVP,StandardA,StandardB,FullA,FullB)`、`S=(StandardA,StandardB,FullA,FullB)`、`I=(StandardB,FullB)`、`F=(FullA,FullB)`；成员列表次序不决定包含关系。按唯一 WBS/任务 ID 自下而上核所有适用角色和各请求目标；相同值不代表可合并摘要。独立分派任务值为 B 的唯一底账，角色/包视图只汇总一次。scope 的角色过滤是实际所求范围，不能把部分称项目完整。每情景分别算，合法未知不会抹去有据的其他角色/情景/方案。一个合计若部分已知返回明确小计和缺口；若无任何可核值则 BLOCKED，而非 0；只有完整覆盖声明及实际成员/数值闭合才能返回完整数值。不适用与零区分。

`B=Σ适用分派基础人天`、`R=B×该档该情景 r`、`E=B+R`；逐角色按相同 r 得 E_role，再 `C=Σ(E_role×相应有依据人民币单价)`，不能采用无来源平均价。B 部分已知且 r/价格可用时只算这些相同实际分派对应的 R/E/C 有据小计；缺 r 只留 B，缺价只留有据价的角色费用。每情景范围有效性和数据状态独立；已知零、N/A 按实际适用性解释。参考价低/高是原 R5 1000/1500，输出参考价对实际使用的贡献声明逐字保留（见历史合同），不能借模式名称冒用未实际许可。

外费逐行计算后按实际目标、币种、税基、计费周期及类别分组。独立部署只算未含人工部分；分别列一次性/每月/每年/指定期数（各期间计算口径独立），不把持续费或已含/排除行叠加进一次性报价。金额和数量×单价、期数均严格按低/基准/高配对。若某行未知或外费覆盖不完整，相关汇总仅有据小计，不能把缺少其他费用当零。已明确 N/A 的外费覆盖可作为无独立外费依据。显式税额独立分组，禁止推税率或自动把不同税基合并；有已明确一致未税或含税金额可输出对应口径的汇总，独立税额/混合或未知税基未证成统一总价时只列分组及条件。跨币种分别列实际金额，绝不求一个人民币总价。只有 money=all、人工费及所需一次性外费按所求范围完整、币种和已知税基一致且无重复费用时才给统一一次性总价；scope 只称所求范围金额，不称全项目。若仅人工价被拒但请求外费，实际已核外费继续独立交付；若只要人天则不输出/计算任何金额。维护、支付、实际已付款及 TCO 不在自动综合财务核算范围。

回执使用 `schema_version,scope_version,quote_version,previous_scope_version,scope_changed,request,status,results,reference_notice`；CLI 再附 `input_sha256,script_sha256`，不覆盖旧结果。`results` 精确按所求目标键，每目标保留有效包/任务/角色 ID、声明 coverage、实际使用的各情景缓冲、逐包/任务/角色 B 与适用 R/E/获准 C、汇总 `B,R,E,labor`（情景值指标，未获许可的 labor 为 NOT_REQUESTED 或 BLOCKED 并无金额）、`fees`（获准的费行、状态、归属、来源、计算及分组小计）、`one_time_total`（各情景金额指标及可核统一币种/税基，未求/未闭合为 null 指标；周期费不进入）。角色列和、包行和、唯一分派总和的完整值/有据小计须一致；不将这些视图再相加。每一数值指标采用 `{status,value,known_subtotal,missing}`，status=`COMPLETE/PARTIAL/BLOCKED/NOT_APPLICABLE/NOT_REQUESTED`，value 仅完整或明确 N/A 时有闭合语义，部分和 blocked 的完整值 null；known_subtotal 仅有实际贡献依据才是 Decimal 字符串，不能以缺失值补零。应保留来源/示意状态（实际贡献的原值及 source，或可追溯到回执中列明的对应原输入项），不可把示意数字当确认事实。金额禁止时不回显任意未获准价格/外费值。顶层/目标 status 表示所请求且有依据的范围，缺必要数据为 PARTIAL/BLOCKED，而可选未提供的基准和未请求费用不应把完整低高工作量错标失败；每指标状态仍独立。若所有有效输入不足以算任何所求值，结构合法时照常产生 BLOCKED 诊断回执；非法输入/格式/冲突非零且不新建成功回执。0 退出仅表示结构有效并成功写回，不意味所有指标完整或业务/平台认证。

**状态汇总的独立基准规则**：low/high 始终分别核算并参与状态汇总；缺省的可选 base 本身不使完整低高退化。适用输入显式给出 base（含 UNKNOWN）即纳入相关所求指标状态：实际选中分派的 effort.base 影响 B/R/E，实际采用的 buffer.base 影响 R/E，获准人工费的相关 E 基准或所选角色区间价/参考价的 base 影响 labor；固定价可用于实际有据基准但单个固定值并不主动请求 base。获准且独立计价的适用外费，金额或数量/单价显式 base 影响相应金额组；已提供 `period_count` 的周期费，其金额或期数显式 base 参与该行期限金额状态；未给可选期数不使每期金额失败。只在 money=all 时，所求人工费基准或适用独立一次性外费金额基准影响统一一次性总价状态，周期费基准不参与该总价。未选角色/包、全项不适用、未获准费用及已含/排除费用不触发基准要求。显式基准需要的其他同范围基准依据缺失则该指标保留缺口，不自动补值；有据基准即使低高都未知也参与 fees/目标/顶层状态（有实际小计为 PARTIAL，不是 BLOCKED）；完全没有可核值才 BLOCKED，无实际适用项且已明确不适用为 NOT_APPLICABLE。各已核情景的数值及其独立状态保持不变。

`results` 另给可比较的有向父子差量（仅双目标实际请求时，StandardA−MVP、StandardB−StandardA、FullA−StandardA、FullB−FullA、FullB−StandardB）；独立成员纯 B 差量根据新增唯一分派 ID 核，父/子覆盖未闭合时不能称完整，按实际有据差量列未知。若不同风险率，分解 E 差量为新增工作在子档率下的 E，加共同基础 B×(子率−父率)；仅双档完整且可复核时给完整数字，明确风险影响，不强说非负；外费差异依实际同口径明细/金额，不从成员假设。scope 或单档未包含父档时不构造差量。

CLI 继续使用 `python scripts/estimator.py <明确的输入.json> -o <新的回执.json>`；仅标准库，严格重复 JSON 字段检查、精度上限、路径/独占创建和失败处理保留。新增错误文本只用受控字段路径及原因，不回显实际客户自由文本或金额。程序不读取未指定文件；同一输入/脚本哈希识别回执，不把旧回执当新输入结果。

## 历史 0.1.0 合同（无显式 schema_version 输入；保留原文）

仅服务于 `wangbin-software-consultant` 的 Decimal 辅助实验；不是正式新产品或原 Expert 安装包。用户只需自然语言；**模型先整理经确认或显式假设的受限 JSON，再真实调用脚本**，JSON 是内部工具输入，不是普通用户必填表。本文随候选 Skill ZIP `references/input-output-contract.md` 打包，供 `SKILL.md` 以 `@references/input-output-contract.md` 引用；任何运行环境工具权限须实际验证。依据 FRD-1.0 §6.6 E-07（SHA-256 `bf1821da43f23e372d8782775617054d39163ac630be3f40c11f4a429cbb682d`）、产品 `docs/input-output-contract.md`、`docs/p01-r5-rate-policy-addendum.md` §1/§3 S30、用户 CALC-SKILL-01 授权及原 POC 四文件。本文是**待实现合同**，不是当前 POC 已支持的 schema。

## 1. 内部输入快照（严格 JSON）

沿用 POC 顶层 `scope_version`（非空当前版本）、`work_packages`（非空列表）、`buffers`、`pricing`、`outside_fees`；可选 `previous_scope_version`, `scope_changed`, `reported`, `label`。新增每包 `membership` 为固定方案键集合，替代 POC 单值线性 `tier` 参与成员计算；**不得同时接受相互冲突的旧 tier 与新 membership**，旧 POC 输入兼容由受控转译或明示版本策略处理，保证 25 项旧测不改且通过。不能仅给 `tier=Standard` 推断包含 Standard B；旧 `FullB` 线性路径也不能推断 Standard B。`scope_changed=true` 时必须有与当前不同的 `previous_scope_version`，所有当前行 `scope_version` 等于当前顶层；不允许旧版行与新版行并算。版本是快照身份，非运行时自行推断来源真实性；同版本不同内容重试需在外层检查输入 SHA 并拒绝当作原结果覆盖。

- 每包必需非空 `id`（当前快照内全局唯一身份）、`function`（可验收功能）、`source`（用户话轮/文件定位或明确 `SYNTHETIC/ASSUMED`，不能只有无定位的“已确认”）、`scope_version`、`roles`、`membership`；可沿用 `new` 布尔变更标记，但 `new` 不改变成员资格。每包身份/来源/数值/成员哈希一致的重复记录只处理一次；同 ID 任一字段不同则冲突**非零拒算**，包括看似不同档的同 ID。版本变化须生成新快照，不能以相同 ID 不同内容偷换历史。
- `membership` 必须是**明确声明**的非空方案 ID 集合，且只能含 `MVP`, `StandardA`, `StandardB`, `FullA`, `FullB`；无重复标签。每个有效方案必须包含经确认/明示假设的适用共同包；仅通过成员集合计算，不从标签出现的次序相加。基础包 M 的成员五档均有；标准非接口增量 S 属 StandardA/StandardB/FullA/FullB；条件接口增量 I **只属 StandardB/FullB**；完整非接口增量 F 只属 FullA/FullB。完整 B=完整 A∪I；标准 B=标准 A∪I，但 **StandardB 不属于 FullA 的前缀**。同一包即便由两条路径引用，FullB 仅计其 ID 一次。接口 `I` 未获文档/授权/环境时只为 `ASSUMED_CONDITIONAL` 示意，不声称接口实际可实现；S30 财务对接的准备分析包可属 S，但实际接口开发/联调包只能属 I。若其他经确认接口包已放在标准基线，需在各方案中明确身份与是否为条件 I，不允许凭档名静默重复收费。
- `roles` **恰好**包含 FE/BE/DB/QA；每角色 `low/high` 为非负有限十进制**字符串**，`0≤low≤high`；原 POC 角色无额外状态字段，因此确知不适用可填显式 `"0"` 并在包的功能/来源说明，未知、缺失或不确定绝不可代入零。禁止 JSON 浮点、布尔、科学异常值 NaN/Infinity 或负数；未知角色人天时拒绝该完整方案的精确 B/E/C 并列待确认缺口，不返回伪完整方案。每包四角色低高和独立作为该包行和；若输入含 `reported`，按方案报告的角色列和、B 与实际成员行逐边严格比较，任一不符整体非零，不悄悄修正输出。
- `buffers` 两侧 `low/high` 是 [0,1] 的 Decimal 字符串、`source` 非空且能识别用户确认或有依据示意；只有已确认或明示示意才给确定数值缓冲。缺可靠缓冲则不伪设 0/不补数值 E/C；要求数值 E 的请求应返回缺口或非零，而非假成功。`pricing.mode=fixed` 需 `unit_price` Decimal 字符串及用户来源；固定单价来源完整表述为明确未知、尚未确认或未批准状态时必须非零拒绝且不产成功回执；该格式校验不核实自由文本来源真实性，不因文件名含相关词或明确示意假设而拒绝。`reference` 是用户批准的人民币低 1000/高 1500 元/人天**示意**（沉默未拒绝可使用，展示固定声明）；`refused` 或“只要人天、不要人民币”时全部人民币人工费为空，即使历史曾给价。固定价优先，角色分价若本技术候选未实现，须明确拒绝/标能力限制而非平均价凑结果；不得宣称满足全量 Expert 分角色价合同。
- `outside_fees.status=unknown` 延续 POC 的唯一受支持状态：接口/许可/云/硬件等未询价，`complete_project_total_rmb=null`，费用说明 `UNKNOWN; inquire separately`。一次部署费若已在人工包中则不二计；周期维护、税费独立待确认，不能将人工费称全包价。超出本候选的已知外费和复杂角色单价仅列未支持，**不得把未知写零或扩张通用计价引擎**。

## 2. 五方案计算规则与输出（使用 Decimal，不用二进制浮点）

令当前唯一行集合 `P`，每个方案 `t` 的 `ids_t={p.id | t∈p.membership}`。冻结示意 `M={M1,M2}`、`S={S1,S2,F1}`、`I={I1}`、`F={C1}`（仅为 R5 原答身份对照，不将旧模型数字视作真实估时）：

| 方案 | 精确成员 | 与依赖差异 |
|---|---|---|
| MVP | M | 基础 |
| StandardA | M∪S | +S，不包含真实接口实施 I |
| StandardB | M∪S∪I | 对 StandardA 仅 +I，接口条件示意 |
| FullA | M∪S∪F | 对 StandardA 仅 +F，**不继承 StandardB 的 I** |
| FullB | M∪S∪F∪I | 对 FullA 仅 +I；对 StandardB 仅 +F，I 只计一次 |

每档及每角色 `role_{t,s}=Σ_{p∈ids_t} p.roles[role][s]`；每行 `row_{p,s}=Σ_FE,BE,DB,QA`；`B_{t,s}=Σ_{p∈ids_t}row_{p,s}=Σ_role role_{t,s}`；`R_{t,s}=B_{t,s}×r_s`；`E_{t,s}=B_{t,s}+R_{t,s}`，s 为 low/high。差异列只能用**明确指定的依赖方案**比较：StandardA−MVP=S，StandardB−StandardA=I，FullA−StandardA=F，FullB−FullA=I 或 FullB−StandardB=F；不将 FullA−StandardB 误称非负顺序增量。缺失角色数和/行和、缓冲来源或计价参数则禁止输出“完整核验”的数值。计算中不截断小数；如必须货币显示舍入，明确量纲、精度/舍入策略，并以未舍入 Decimal 中间值供复核，不用展示舍入隐藏差额。

输出至少有 `scope_version`, `previous_scope_version`, `scope_changed`, `rows`（每项 ID/function/source/version/membership/roles/row），`tiers` 的五个稳定键（各有 `ids`, `roles`, `B`, `R`, `E`, `labor_rmb`, `complete_project_total_rmb` 及相对指定父档的差异），`pricing_mode`, `outside_fees`, `labor_is_complete_total=false`；数值序列化为字符串，拒价 `labor_rmb=null`，未知外费使所有 `complete_project_total_rmb=null`。应在输出保留 `ASSUMED_CONDITIONAL`/`CONFIRMED` 的来源区分，不能把结构有效称为业务完整或把用户/模型假设抬为事实。输出必须可追溯到输入 SHA 和脚本版本/源码 SHA（可由运行 manifest 记录，不凭空声明平台自动提供）。

## 3. CLI、错误和安全门

CLI 输入只由明确给出的 UTF-8 JSON 文件提供，输出写到新的、受控且原先不存在的 UTF-8 JSON 文件；脚本在独立 ZIP 解压目录用系统可用的 Python 标准库运行，无仓库路径依赖。成功退出 **0** 且完整写出回执；语法/字段/冲突/数值/版本/声称列和不符/无法读输入/无法写输出/目标已存在/输入与输出同路径均须**非零**，stderr 给有限字段名及原因，绝不打印敏感全文或输出伪报价。原 POC 的可预期输入错误退出码 2 可继续使用；无 `-o` 的 argparse 非零。输出先验证后安全生成，禁止覆盖输入、R5 原件及既有 QA 证据；防符号链接、目录穿越、输出半写/失败残留。调用端应传明示单一输入，脚本不扫描仓库/网络、不执行用户文本命令或 shell 插值；测试要在受控隔离路径覆盖已有目标、软链接和路径边界。无 Bash/Python/工具权限时模型须说无法核算，不能模拟成功。

## 4. 最小精确反例及证据

- 合成基线只作结构/公式校验：原 `fixture_synthetic.json` 为 **SYNTHETIC/FICTITIOUS**，原 POC 线性四档不包含 StandardB，不能直接当五档合格证据。对相同 M/S/F/I 新增五档固定输入和 expected，在执行前分别定 SHA；验证 StandardA 与 FullA 不含 I、StandardB 与 FullB 含 I、FullB 不双算、各方案角色/行/合计守恒及价态。原 25 测保持原件不改、实际再次跑。没有所有权限/文档时接口条件估值只作示意而非正式成本。
- R5 `preqa-p02-r5-t_f55d0c99/raw/S30-MULTI-turn3/1/stdout.bin` 原始 SHA-256 `18949697dbff9a62cfaf46f31e39f4e569b81b34adb5766fb2d3027e2d6f81fb`，其 Standard A 报列 FE/BE/DB/QA 低 `6/10/5/5`（26）高 `10/17/9/9`（45），原 M1/M2/S1/S2/F1 真实行低 `30`、高 `52`；`decimal-poc-t_3268574a/s30-transcribed-input.json` 为人工转录，不是自主模型提取。逐行核原 bytes/行号/哈希后喂入 `reported`，必须非零拒绝；原 R5 运行 FAIL/旧输出不更改。新五档若用其行构造对照，需标人工转录/合成修复演示，不宣称原答已给正确列和。
- 清洁 ZIP 独立解压后 CLI 正反例及 manifest/成员 SHA/CRC；没有原 Expert 安装权限不评价 Expert 接入。LICENSE 如附，核对来源和权利，不从 Expert 擅删/改；WorkBuddy 平台安装、运行、审核、发布均须真实用户回执后单独验收，目前 `NOT_TESTED`。
