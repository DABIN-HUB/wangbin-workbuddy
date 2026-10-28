# Phase 2 冻结契约审计与保守执行澄清

2026-10-28。只读独立审计deleg_f849e79d已返回，父任务全量解码复核469字段、97条件字段、13显式条件ID、274非repeat_group项；03 Markdown/JSON字段ID一致。子任务所列b475c5e工作区只指其审计采样，不代替父任务现在的Git状态。未改写原始目录/公式或删字段。

## 采用的执行规则（Phase2C实现并测试后才可声称完成）

1. 运行时结构、输入合法性、条件/适用性、证据等级、产品可计算和真实L2/L3报告分别输出。全部469定义保留不表示每类每项无条件必填；首轮五概念不是等级自动通过器。
2. 条件采用T/F/U；U不等于F。对所有97条件字段建立显式条件归属/父数组继承，不能仅用13个conditional_rule_id漏掉其余字段；不能靠“没有协议”推无债。已知债务计划优先于比例0并产生冲突。
3. 首轮project.name/has_storage可暂缺不阻断收集，但目录R/R/R不被偷偷豁免：缺事实项目名/配储声明时仍列等级缺口，不生成假项目名或默认false。
4. grid.power_factor目录minimum=0而其验证文字要求严格正：保留冻结Schema原约束；零值可作为待核记录保留，但语义层禁止进入依赖的计算/高等级。
5. 价格行sale_price的R按“有上网结算”适用；无上网不补造售电价。实际合同/时序价格模型未知时保持U，不把periods与market_series同时豁免。PPA按真实结算/负荷边界，不因标签自动造企业负荷收益。
6. 不适用与证据状态分离。若增加适用性记录，必须给规则ID、触发证据、理由、复核者，且仅允许明确的业务豁免，不能给UNKNOWN加NOT_APPLICABLE来绕过安全/权属/真实资源。
7. L2基本并网情景不等于正式并网许可；附件/permit冻结必需项缺失时保守保留缺口，绝不自动升级confirmed。L2非关键假设仍受具体字段substitutable.max_maturity=L1的更严上限。
8. L3边界附件与顶点保留原义务；未有专项不适用证据不能擅改成二选一。resource.monthly空数组只可存草稿，不能代表12个月完整。
9. 屋顶、地面与七扩展类型分别有数据契约；storage.base_pv_type必须八种非储能分类之一并组成数据schema，计算能力仍NOT_IMPLEMENTED。BIPV/车棚子型不明确不得默认屋顶。
10. 目标约束、严重未决与否决按原基线，不实现财务/发电值，不出投资可行结论；未来六类产品门禁继续独立未通过。

主要依据：03-input-data-dictionary.md §§1—4及IN-C01..13；03-input-fields.json required_level_semantics/conditional_rules及各field_id；07-category-boundaries.md §§2、4；01-product-requirements.md；08-baseline-contract.json。完整用户任务在13-phase2-user-task.md，不以本澄清替代原要求。
