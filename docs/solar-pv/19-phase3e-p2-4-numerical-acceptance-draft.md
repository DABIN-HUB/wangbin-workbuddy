# F-BREAK-EVEN-PRICE 工程数值验收契约草案

**独立标识：**`solar-pv-break-even-numerical-acceptance/draft-0.2`。**状态：**审批草案；不是 D2/D3、冻结公式或正式结果 Schema 的修订，也不是求根证明／通过凭据。已批准条款和待审批条款分开标识。严格保留冻结定义 `P*={p∈P : NPV_b(CF_b(p),r_b)=0}`，其中 `P*` 是整个允许域的精确根集合（元素元/kWh），`CF_b(p)` 是只改变指定电价原子后完整重算的同口径现金流；不能以样本插值、一个近零售价或有限扫描替代完整根集。[`docs/solar-pv/05-formula-registry.md:3290-3336`]

## 已批准：适用边界与责任

| 事项 | 草案约束 | 责任与核验输入 |
|---|---|---|
| 域／端点 | **已批准：**使用原 D2 的 `break_even.minimum_price`、`break_even.maximum_price` 构成连续闭区间 `[L,U]`，两端都必须分类检查；`L<U`，绝不从采样序列暗设新报价网格。负价只能通过已有 `settlement.negative_price_treatment` 与带来源的 `tariff.negative_price_rule`；任何不能合法结算的区间阻断而非悄悄裁剪。 | 方法配置的参数值／单位／来源状态和原子选择的 `field_id`、`row_id`、实例 ID、原价哈希；逐价全链重算产生者执行，证书审核者验证整个区间每个分支均合法。[`calculation/method_config.py:114-129`; `calculation/break_even_execution.py:128-169`] |
| 价格表示 | **已批准：**`break_even.price_tolerance` 单位 `currency/kWh`，仅约束已证明根隔离区间的宽度 `b-a`，不是步长、货币残差或业务报价最小单位；本独立 SYNTHETIC 案例沿用 D2 的 `0.000001 元/kWh`，不得推广给其他案例。 | 记录 `L/U` 的原始十进制字符串、Decimal 精度与舍入模式、每个候选的十进制字符串及精确有理解释（有限小数本身是有理数），检查端点、区间与候选身份；现有 D2 案例 `precision.digits=60`，参考价格由 100 位 Decimal 生成，**两种精度不能混写成同一已证明的执行误差界**。[`tests/solar-pv/energy_case_support.py:73`; `reports/solar-pv/phase3e-p2-4b-c-synthetic-predeclaration.json:24-37`; `calculation/common.py:84-93`] |
| 来源／口径 | **已批准：**项目、场景、原始输入与源快照、D2 参数及来源、D3 内容、3B 发电、3C 收益、3D 账簿、终期交易原字节与排重、3E F-NPV、公式版本和执行文件身份均绑定同一项目／日期／币种／税前后与项目或股权口径。真实项目不得借用 SYNTHETIC 源或阈值。 | 会话每次校验原价已发布件与来源，候选逐价经真实生产者；复核原始字节和结果侧车。文件 SHA 不单独证明 Python 内存中已导入函数的身份，更不是抗恶意并发写入沙箱。[`calculation/break_even_project_session.py:95-175,217-253`; `calculation/break_even_certification.py:16-57`] |
| 证明门禁 | **已批准：**仅当认证器提供覆盖**完整闭区间**、全部适用税务／结算／收款／终期分支及端点的可审计证书时，才允许声称完整精确根集合。有限 Decimal 回放的数学误差和分支边界须另证，预算耗尽不是无根证明。 | 证书明确模型版本、源身份、每个分支适用区间与完整覆盖证明、每个根的隔离或零平台区间、排除其余零点的理由；证据缺口返回非数值阻断。[`docs/solar-pv/05-formula-registry.md:3315-3324`; `calculation/break_even_certification.py:58-83`] |

## 工程候选与精确根集严格隔离

- **理想数学层：**以固定来源和精确有理算术求 `F_ideal(p)` 及集合；只认证明示的理想模型，不自动认证财务生产者的有限精度 `F_exec(p)`。
- **工程数值层：**候选 `p_dec` 必须记录原始 Decimal 字节/字符串、算术精度和舍入、隔离区间 `[a,b]⊆[L,U]`、宽度 `b-a`（元/kWh）、真实全链 NPV 残差 `|F_exec(p_dec)|`（元），以及独立证明的 `F_ideal` 与 `F_exec` 的相关误差界。两个残差门禁互不替代；单点 `0E-22 元` 不意味着误差界为零。
- **完整性层：**证书须证明整个 `[L,U]` 的适用模型分支没有遗漏根、跳跃、不合法负价或舍入零平台。诊断结构（不写入正式结果 Schema）可分别列 `isolated_roots`、`zero_intervals`、`excluded_intervals` 与 `proof_coverage`，同时记录来源／精度。**证明全域无根**、**多个孤立根**、**零平台（可能伴随孤立根）**和**无法认证**分别给出诊断；证据不足绝不改报 `NO_ROOT`。如精确根有无限个而正式 Schema 只允许数字／数字数组，必须阻断并另报表示差异，不截断为任意一个根。[`calculation/result_contract.py:26-34`]
- **正式发布层：**只有用户批准单独的数值验收语义、区间／货币残差、证明范围及与既有正式结果表示的映射，且源身份与完整性同时满足，才可讨论输出正式数值；草案阶段绝不调用旧 `financial_metrics._break_even()` 的分段样本插值作正式证明。当前真实入口 `certify_project_root_set()` 固定返回已封存的 `value=null`、`BLOCKED_MISSING_INPUT / BLOCKED_ROOT_SET_COMPLETENESS_UNPROVEN`，诊断候选另存于项目回放件，不能复制到正式指标。[`calculation/financial_metrics.py:381-412`; `calculation/break_even_certification.py:16-85`]

## 独立 SYNTHETIC 一期的可复核算例（**不是**正式全域证书）

项目 `SYNTHETIC-BC-INDEPENDENT-ROOT` 事前声明：`NO_DISPOSITION`、项目税后名义年末 CNY、折现率 `1/10`、售电量 `87600 kWh`、收款比 `3/4`、CAPEX `1130 元`、OPEX `180000 元`、营运资金 `200 元`、自用节省 `140160 元`，域 `[0,2]` 元/kWh。其理想模型在该域内 VAT 最大销项 `2277600/113` 小于进项 `2354690/113`、所得税基最大 `1684600/113` 小于期初亏损 `34000`，所以**对该理想模型**两个现金税分支为零；上述结论不可无证据推广到可执行 Decimal 的所有输入／项目。[`reports/solar-pv/phase3e-p2-4b-c-synthetic-predeclaration.json:1-40`; `reports/solar-pv/phase3e-p2-4b-c-root-certification-review.md:22-30`]

独立有理计算：`F_ideal(p)=-1330+(65700p+140160-180000+200)/(11/10)` 元；`F_ideal(0)=-411030/11` 元、`F_ideal(2)=902970/11` 元，斜率 `657000/11` 元/(元/kWh)>0，故唯一**理想**根 `4567/7300` 元/kWh。该分母含非 2／5 因子，不能被有限小数精确表示。已归档候选的 100 位价格字符串 `p_dec` 与理想根相差 `<10^-100` 元/kWh；仅在理想模型里，`|F_ideal(p_dec)| < (657000/11)×10^-100 元`。归档的真实完整链在这一点记录 `NPV=0E-22 元`，两端分别为负／正；**未取得**从理想函数到可执行函数的全域误差上界或隔离区间，不能以这些数值断言实算全根集合。[`reports/solar-pv/phase3e-p2-4b-c-root-certification-evidence.json:129-208`]

**待用户单独批准的提议（仅 SYNTHETIC）：**另设 `|F_exec(p_dec)| ≤ 1 元` 的货币残差候选阈值。理由仅限独立一期理想模型：`1e-6 元/kWh` 的整段价格宽度对理想 NPV 的最大影响是 `657/11000 元`，小于 `1 元`；但 `1 元` 在理想斜率下对应 `11/657000 元/kWh` 的价差，**反而大于价格区间容差**。故 1 元最多作为**与区间宽度并行**的审查门，不能单独定位根，也不能覆盖未证明的实算舍入／税费误差；更不能用于真实项目或默认 D2。即便批准 1 元，也仍须全域精确根集证书与正式数值表示的独立批准。现阶段记录 `proposed_monetary_residual_yuan=1`、`approval_status=PENDING_USER`，正式证书的 `approved_monetary_root_tolerance_yuan` 保持 `null`。

## 待用户批准的差异／停机条件

1. **货币阈值审批：**是否批准且仅限该事前声明项目的 `1 元`、`≤` 比较口径、币种及舍入边界？未批准时禁止作为 PASS 判据；真实项目阈值必须由其独立来源和口径另行决策。
2. **认证模型／误差证明：**具体全域分支模型、精确式与 Decimal 执行式的联系、误差包络和零平台表示；未取得证明即 `NOT_PROVEN`，不能因为 D2 方法名含 `CERTIFIED` 宣称认证。
3. **正式输出语义：**是只允许冻结的精确根集，还是允许已证区间的工程近似代表价；把代表价写入正式数值 `value` 或表示区间／零平台、以及任何冻结公式／正式 Schema 修改，均另需用户批准。现在不修改 469 字段、89 公式、281 绑定、D2/D3 或正式结果 Schema。

**最小后续实施方案（非本轮授权）：**先审批以上差异，再独立制定有版本的证书与全域分支证明材料；构建审核器时只读取同一身份的真实回放，缺少任一来源／误差／证明即拒绝；经批准且能够在旧正式结构准确表示的场景才考虑接入正式入口。所有临时工程候选保留在标明 `DIAGNOSTIC_ONLY` 的报告／证据中，不修改正式指标。当前停止于 `BLOCKED_MISSING_INPUT`；不执行长时间求根，不进入 P2-5 或 Phase 3F。
