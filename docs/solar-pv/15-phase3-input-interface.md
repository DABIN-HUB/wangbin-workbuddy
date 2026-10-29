# Phase 3 输入接口与未关闭事项（本轮不执行 Phase 3）

日期2026-10-29。Phase 2仅交付输入数据、来源/单位/分类/资料成熟度/受限解析/多轮事务与公式输入查询；最终验收见`reports/solar-pv/phase2-review-and-acceptance.md`。不得据本接口宣称发电、财务或正式四文件可用。

## 1. 可运行入口和约束

源码入口`services/solar-pv-engine/solar_pv.py`，模块入口`python -m wangbin_solar_pv`，新包entry point为`wangbin-solar-pv-input`。使用已安装新包声明依赖的Python >=3.12,<3.15；测试使用仓库外verify-venv，不修改用户环境。安装包后需`--baseline-dir`指向完整冻结`docs/solar-pv`；源码入口按自身位置定位，不以当前工作目录猜目录。未生成WorkBuddy产品或上传ZIP。

所有JSON读写均在调用方显式授权且已存在的私有`--workspace`内；源附件另用`--input-root`授权。输出不覆盖；重复请求使用同submission_id与同内容，修改必须换请求ID并指定当前revision。数值须给明确unit，JSON精确数值不使用数字字符串。

示例（SYNTHETIC，仅展示已存在CLI的参数；实际运行证据另见phase2d-cli-observed.json及Phase2E CLI/JUnit）：

```text
python services/solar-pv-engine/solar_pv.py --workspace <已存在私有目录> new --project-id SYNTHETIC-CASE --pv-type industrial_rooftop --state project.json
python services/solar-pv-engine/solar_pv.py --workspace <同目录> submit --state project.json --input round1.json --expected-revision 0
python services/solar-pv-engine/solar_pv.py --workspace <同目录> status --state project.json
python services/solar-pv-engine/solar_pv.py --workspace <同目录> export --state project.json --output normalized.json
python services/solar-pv-engine/solar_pv.py --workspace <同目录> formula --formula-id F-DC-CAPACITY --state project.json --output formula-query.json
```

round1.json的确定格式：

```json
{"submission_id":"round1","updates":[{"field_id":"site.total_area","value":1000,"unit":"m2"},{"field_id":"targets.payback_years","value":5,"unit":"year"}]}
```

并非实际项目事实，不会因此生成投资额、直流容量或回收期结果。其他命令为`revise/resolve/review/remove/parse/accept`，准确payload见各命令`--help`。`review`是用户另行明确的人工复核及许可声明，不是独立向产权/电网机构认证。parse正常提取exit0，PARTIAL/无候选exit3，NEEDS_OCR exit4，失败/阻断exit2；普通命令错误exit2，固定错误码不输出原文/路径/凭据。超时、超限明确失败，不截断冒充完整。

## 2. 移交输入，不是 canonical calculation result

`IntakeSession.export()`输出`schema_version=solar-pv-input-export/1.0.0`：

| 键 | 含义 |
|---|---|
| project | 可由`ProjectData.from_dict(data,catalog)`重新校验的完整`solar-pv-project/1.0.0`项目；含values、candidates、resolutions、history、revision、submission_ids、applicability与冻结文件哈希 |
| normalized_inputs | 已提供输入的规范值；对象数组保留row_id/完整字段ID，未知仍null；不补齐469个空/零值 |
| provenance_records | 已选输入逐原子信封；原始值/单位、位置、来源、有效期、许可和声明血缘 |
| source_snapshot/source_snapshot_id | 选中记录、候选/人工选择、附件完整SHA-256及快照摘要；私有资料，不自动写公开日志/仓库 |
| input_hash | `sha256/solar-pv-input-v1`覆盖规范输入、schema/基线/分类、来源快照与适用性；不使用导出时墙钟，往返可复现 |
| scenario_config | pv_type、显式storage基座、独立输入契约ID；九类calculation_status仍NOT_IMPLEMENTED |
| input_maturity | INPUT_EVIDENCE_ONLY的L1_DRAFT/L1/L2/L3及缺口/条件/假设/冲突；非报告等级或工程审批 |
| calculation_status/result_contract_status | NOT_IMPLEMENTED / NOT_CREATED |

没有run_id、result_hash、NPV/IRR/发电量结果。未来引擎须先重新验证版本与基线、来源/单位/条件/分类、input_hash与source_snapshot，执行独立数值模型后才能创建`12-canonical-result-contract.md`规定的结果JSON。不得用本输入export冒充计算成功，不得用目标回收期/IRR反推真实成本、资源或收入。

## 3. 公式输入查询

`FormulaBindings(catalog).describe(formula_id,project=None,level='L2')`读取原89条公式；`describe_field(formula_field_id,...)`读取原281条映射，不建立第二套ID。返回每符号中文定义/单位、下标/上标/集合/范围、源字段类型/来源/必需与条件义务、场景适用、边界/假设、实际缺失实例及计算状态。省略project时是NOT_EVALUATED，不能把未评价误称“资料缺失”。

共有448次符号定义，其中46次是field_id=null的索引或求根变量，保留原定义；例如r/p不是向用户索取的“真实IRR/盈亏电价”。281个域包括104个输入/显式变换映射、88个计算/验证输出、86个账簿状态和3个定义常量。后两类账簿及输出始终NOT_COMPUTED；支持输入存在不等于已完成聚合、单位变换或数值方法。未核对的STC温度常量保持CONSTANT_UNVERIFIED，不补25°C。冻结文件未定义账簿运行时类型时明确NOT_DECLARED_IN_FROZEN_MAPPING；未来模型需补独立类型/形状而非从支持输入类型猜算输出。

缺少数量、单价、现金流等列出真实field_id/实例；无债务的条件字段不索要，未知条件不豁免。显式AI辅助解释仅可在冻结允许AI的字段用source_kind=ASSUMPTION、provenance_kind=AI及假设元数据，保持ASSUMED，不能伪装用户事实或VERIFIED；关键物理参数拒绝AI来源。六种来源类别不因此新增第七种。

## 4. 后续独立门禁和限制

1. Phase 3先实施并独立验收工商业屋顶/地面两套确定性模型、月度与逐时边界、资产税费/融资/现金流及全部89公式。不能把本查询的输入存在误作模型可执行；所有分类计算仍未实现。
2. 现场资源/电价/并网/权属/结构/设备及客户数据必须另获授权、核对有效期与适用性；当前所有测试均SYNTHETIC，无真实项目验证通过。31项研究来源许可、标准授权全文、税制/合同细则未因输入层开发而关闭。
3. 四文件同源、18章、29工作表、渲染/编辑/重算/视觉和整集发布均后续单独验收；目前没有正式四文件。
4. 本地私有目录不是OS沙箱；Windows强制内存/后代进程/目录竞态/ACL、缺symlink权限未解决，公开不可信服务保持BLOCKED。失败与环境跳过不标成通过。
5. 默认20,000解析单元格、8MiB文本/子进程输出、32MiB JSON；大型全年15分钟数据须受控分块/流式方案后另验收吞吐，不减少长期时序要求。无OCR/复杂表格重建，不代表原资料不存在。
6. 新包依赖及最终分发许可仍须在产品打包/平台阶段独立审核；本轮未注册产品、不push、不部署、不试传、不提交审核。
