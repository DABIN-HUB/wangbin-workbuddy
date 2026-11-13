# wangbin-estimate-calculator 0.1.0｜输入、输出与失败合同（技术候选）

仅服务于 `wangbin-software-consultant` 的 Decimal 辅助实验；不是正式新产品或原 Expert 安装包。用户只需自然语言；**模型先整理经确认或显式假设的受限 JSON，再真实调用脚本**，JSON 是内部工具输入，不是普通用户必填表。本文随候选 Skill ZIP `references/input-output-contract.md` 打包，供 `SKILL.md` 以 `@references/input-output-contract.md` 引用；任何运行环境工具权限须实际验证。依据 FRD-1.0 §6.6 E-07（SHA-256 `bf1821da43f23e372d8782775617054d39163ac630be3f40c11f4a429cbb682d`）、产品 `docs/input-output-contract.md`、`docs/p01-r5-rate-policy-addendum.md` §1/§3 S30、用户 CALC-SKILL-01 授权及原 POC 四文件。本文是**待实现合同**，不是当前 POC 已支持的 schema。

## 1. 内部输入快照（严格 JSON）

沿用 POC 顶层 `scope_version`（非空当前版本）、`work_packages`（非空列表）、`buffers`、`pricing`、`outside_fees`；可选 `previous_scope_version`, `scope_changed`, `reported`, `label`。新增每包 `membership` 为固定方案键集合，替代 POC 单值线性 `tier` 参与成员计算；**不得同时接受相互冲突的旧 tier 与新 membership**，旧 POC 输入兼容由受控转译或明示版本策略处理，保证 25 项旧测不改且通过。不能仅给 `tier=Standard` 推断包含 Standard B；旧 `FullB` 线性路径也不能推断 Standard B。`scope_changed=true` 时必须有与当前不同的 `previous_scope_version`，所有当前行 `scope_version` 等于当前顶层；不允许旧版行与新版行并算。版本是快照身份，非运行时自行推断来源真实性；同版本不同内容重试需在外层检查输入 SHA 并拒绝当作原结果覆盖。

- 每包必需非空 `id`（当前快照内全局唯一身份）、`function`（可验收功能）、`source`（用户话轮/文件定位或明确 `SYNTHETIC/ASSUMED`，不能只有无定位的“已确认”）、`scope_version`、`roles`、`membership`；可沿用 `new` 布尔变更标记，但 `new` 不改变成员资格。每包身份/来源/数值/成员哈希一致的重复记录只处理一次；同 ID 任一字段不同则冲突**非零拒算**，包括看似不同档的同 ID。版本变化须生成新快照，不能以相同 ID 不同内容偷换历史。
- `membership` 必须是**明确声明**的非空方案 ID 集合，且只能含 `MVP`, `StandardA`, `StandardB`, `FullA`, `FullB`；无重复标签。每个有效方案必须包含经确认/明示假设的适用共同包；仅通过成员集合计算，不从标签出现的次序相加。基础包 M 的成员五档均有；标准非接口增量 S 属 StandardA/StandardB/FullA/FullB；条件接口增量 I **只属 StandardB/FullB**；完整非接口增量 F 只属 FullA/FullB。完整 B=完整 A∪I；标准 B=标准 A∪I，但 **StandardB 不属于 FullA 的前缀**。同一包即便由两条路径引用，FullB 仅计其 ID 一次。接口 `I` 未获文档/授权/环境时只为 `ASSUMED_CONDITIONAL` 示意，不声称接口实际可实现；S30 财务对接的准备分析包可属 S，但实际接口开发/联调包只能属 I。若其他经确认接口包已放在标准基线，需在各方案中明确身份与是否为条件 I，不允许凭档名静默重复收费。
- `roles` **恰好**包含 FE/BE/DB/QA；每角色 `low/high` 为非负有限十进制**字符串**，`0≤low≤high`；原 POC 角色无额外状态字段，因此确知不适用可填显式 `"0"` 并在包的功能/来源说明，未知、缺失或不确定绝不可代入零。禁止 JSON 浮点、布尔、科学异常值 NaN/Infinity 或负数；未知角色人天时拒绝该完整方案的精确 B/E/C 并列待确认缺口，不返回伪完整方案。每包四角色低高和独立作为该包行和；若输入含 `reported`，按方案报告的角色列和、B 与实际成员行逐边严格比较，任一不符整体非零，不悄悄修正输出。
- `buffers` 两侧 `low/high` 是 [0,1] 的 Decimal 字符串、`source` 非空且能识别用户确认或有依据示意；只有已确认或明示示意才给确定数值缓冲。缺可靠缓冲则不伪设 0/不补数值 E/C；要求数值 E 的请求应返回缺口或非零，而非假成功。`pricing.mode=fixed` 需 `unit_price` Decimal 字符串及用户来源；`reference` 是用户批准的人民币低 1000/高 1500 元/人天**示意**（沉默未拒绝可使用，展示固定声明）；`refused` 或“只要人天、不要人民币”时全部人民币人工费为空，即使历史曾给价。固定价优先，角色分价若本技术候选未实现，须明确拒绝/标能力限制而非平均价凑结果；不得宣称满足全量 Expert 分角色价合同。
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
