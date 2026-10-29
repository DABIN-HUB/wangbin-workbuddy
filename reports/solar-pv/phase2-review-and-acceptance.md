# 光伏 Phase 2 最终评审与验收

验收日期：**2026-10-29（UTC+08:00）**。用户任务全文：`docs/solar-pv/13-phase2-user-task.md`。最终结论：**PHASE2_INPUT_CONTRACT_PASS（私有本地、有界输入能力范围；5项环境跳过单列，不是全部平台/安全测试通过）**。

本轮只完成Phase2A—2E。已修复独立审阅发现的P1，最终全套和旧回归重新执行通过；**不进入Phase3**。发电/财务/真实项目/四文件/WorkBuddy/发布全部独立未通过。发布保持**BLOCKED**。

## 1. 实际仓库与边界

2026-10-28实际初始main/HEAD为`b475c5e5b3d107625acb8e531a623d142060a194`，不是仅采信用户描述。收尾前HEAD为Phase2D `0fe02688cefe5a2e3f851a8aa27bbb3261b3c74f`。本报告与源码/矩阵一同进入Phase2E提交；该提交的准确SHA在交付消息及`git log -1`读取，不在被提交文件内部制造自引用哈希。

新增独立包`services/solar-pv-engine/`，同一仓库内，无新数据库/微服务/产品注册打包工厂。旧产品、源码、测试、许可证、catalog与dist归档未修改。所有用例为明确SYNTHETIC资料，无实际商业附件上传/公开。没有push、平台试传、审核提交或公网部署。

## 2. 实现与覆盖

| 模块 | 实际能力与边界 |
|---|---|
| catalog/models/schemas/serialization | 469/469字段定义、严格JSON Schema、类型/枚举/范围/格式、数组行/元素信封、版本和12冻结文件SHA-256；拒绝重复键、未来版本、非有限数和漂移 |
| units | Decimal/Fraction精确转换、反向/边界/异常、DC/AC/功率/电量/金额/面积/温度/日期时刻时区隔离；非终止小数必须显式舍入，不猜单位/税含/价格年 |
| provenance/validation/consistency | 六来源及U/D/C/显式AI解释边界；原值/规范值、位置/时点/许可/人工核验、候选冲突、金额血缘、融资、账单/时序/任务数组与循环 |
| categories/scenarios | 九类独立输入契约；94专用字段隔离，屋顶/地面负荷/租赁/销售边界；storage八种非递归基座，未知不默认屋顶；所有分类计算仍NOT_IMPLEMENTED |
| conditions/applicability/quality/completeness | 97条件字段/13显式规则T/F/U，按父/行核验；受控不适用证据、九轴L1/L2/L3、缺口/冲突/假设及下一问；输入证据等级不等于报告或审批 |
| parsers/attachment_security | DOCX/PDF/XLSX/CSV/TXT/Markdown六格式受限读取与实际定位，10类明确标签资料、逐单元候选；宏/公式/嵌入/外链/危险PDF/压缩与路径攻击拒绝，未做OCR/复杂版式推断 |
| intake/local_files/cli | 本地多轮JSON，幂等submission_id、revision CAS、原子事务、修订/移除/冲突选择、独立review、附件accept与规范导出；下一轮最多5问，目标不生成结果 |
| formula_bindings | 89/89公式查询、281/281冻结域映射、448次符号定义（46次索引/求根变量无field_id原样保留）；每输入类型/单位/来源/必需条件、缺失实例、适用/边界；不执行数值/聚合/账簿 |

JSON Schema产物：`services/solar-pv-engine/schemas/project-input.schema.json`。字段15类元数据来自原469目录，并关联来源信封/版本/公式映射；没有新建第二套不兼容字段ID。

`ASSUMPTION+provenance_kind=AI`仅允许原目录22个许可AI的解释性字段，需假设元数据并保持ASSUMED；不能核实成客观事实，物理参数拒绝AI来源。计算C类仅验证实际声明的公式/版本/run及上游血缘，本轮不执行发电/财务公式。

金额/输入已知不等于来源已核实；相同金额不同税含/价格年保留冲突。UNKNOWN填null不填0；新增未知不擦除已知，资料补齐不误判冲突。L2/L3基于声明证据加本地一致性检查，不声称已经向权属、电网或气象机构独立认证。

## 3. 真实测试结果

测试解释器：
`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-phase2-20261028/verify-venv/Scripts/python.exe`

### 3.1 最终新增功能套件

```text
<verify-python> -m pytest tests/solar-pv -q -rs --tb=short
  --basetemp=.../pytest-phase2-final
  --junitxml=.../phase2-final-junit.xml
exit=0
3014 passed / 0 failed / 0 errors / 5 skipped（3019 total）
```

原始证据：`phase2-final-pytest.txt`、`phase2-final-junit.xml`。所有3019项逐条状态在JUnit，不将文档检查条数当功能测试，不与中间测试重复相加。

| 用户测试组 | 验收范围与主要执行文件 |
|---|---|
| A | 全469 Schema/元数据/UNKNOWN往返与类型拒绝，test_field_contract_coverage、test_catalog_schema |
| B | 全标量枚举/范围及97条件字段，test_boundaries_and_records、test_conditions、test_metadata_formats |
| C | 348项单位/时间正常、反向、异常及精度，test_units；XLSX原数值token精度另验 |
| D/E | 223分类边界项含屋顶/地面双向拒绝、其他七类及storage基座，test_categories |
| F | test_provenance_validation/source_merge/ai_origin；958项来源/信封主体及补充边界 |
| G | test_completeness/applicability/quality；声明型L2/L3正反例，不是真实工程 |
| H | test_intake/cli/intake_boundaries/context_reactivation；补充、修订、回选、幂等、原子性与并发 |
| I/J | test_parsers/parser_security/parser_precision/parser_intake；六真实格式/定位/危险文件/根范围/编码/限额，5项symlink环境跳过 |
| K | test_formula_bindings的375项覆盖89公式、281映射及5专项缺口；test_formula_cli真实入口 |
| L | 独立旧回归145/0/5、288保护hash及12基线引用 |
| M/N | UNKNOWN无参数、目标不反推、候选不自动核实、版本拒绝、精确JSON/反序列化及规范export |

5项新测试跳过全部因为Windows无创建symlink权限：CLI文件/祖先/workspace三项，parser文件/root两项。硬链接、junction及并发CAS/Windows实际共享冲突已运行；跳过不计PASS。跨环境真实symlink与Windows强制隔离仍未完成，公开不可信服务BLOCKED。

中间首次全套180秒超时、被终止，无完整JUnit，不采纳为通过；以600秒上限重跑并最终修复后332.27秒完成的记录为准。阶段RED/GREEN及失败日志保留，不删除失败事实或修改旧断言。

### 3.2 旧产品完整回归

在不含.git的scratch当前源码快照执行，避免旧测试改写真实仓库dist/reports：

```text
<verify-python> -m pytest tests packages/experts/wangbin-software-consultant/tests
  --ignore=tests/solar-pv -q -rs --tb=short
  --basetemp=.../pytest-accepted-legacy
  --junitxml=.../phase2-final-legacy-junit.xml
exit=0
145 passed / 0 failed / 0 errors / 5 skipped（150 total）
```

证据：`phase2-final-legacy.txt`/JUnit。5项均旧symlink环境跳过，与初始145/0/5一致。只跑根tests会少36项Expert测试，故另外执行上述完整路径并以其作为最终结果；不把较窄109项当完整旧回归。

### 3.3 CLI与编译

Phase2D实际5轮new/submit/retry/status/export见`phase2d-cli-observed.json`，规范输出为L1_DRAFT、没有财务结果。Phase2E真实formula子进程exit0见`phase2e-formula-cli-observed.json`：查询F-DC-CAPACITY，写出完整3符号定义，calculation_status=NOT_IMPLEMENTED。首次从Hermes Python kernel继承PYTHONPATH导致rpds ABI导入失败；清除子进程PYTHONPATH/PYTHONHOME后使用实际verify-venv成功，未更改代码伪造结果。

生产目录compileall exit0；精确命令见`phase2-compile.json`，缓存定向scratch，不新增测试依赖/旧公共配置。

## 4. 独立审阅与P1闭环

只读审阅发现：站址变更仅降级活动记录，历史VERIFIED候选可在resolve恢复旧核验。真实回归先RED复现，再统一修复候选注册/回选的激活校验；保留历史候选不变，在失效事件绑定candidate_ids，嵌套原子递归降级，旧history按事件顺序兼容，新review可形成新有效候选。失效事件进入source_snapshot/hash。

7项上下文/无物理单位序号回归在最终全套通过；独立审阅过程、限制与修复详见`phase2-independent-review.md`，RED/GREEN留档。该P1不再未关闭；本报告不保证没有未知缺陷，也不把只读推导声称动态验证。

## 5. 需求追踪、基线与保护

- 原1208条矩阵、140条原文非空正文行、469字段、89公式、281映射、189术语、18章、13附录、29核心sheet完整保留。
- 仅升级469字段输入契约及8个窄范围输入负向用例；原2项基线PASS不变，现479 PASS/729 NOT_IMPLEMENTED。机器映射见`phase2-traceability-execution.json`；原acceptance expected不变。
- 类别E2E、89公式数值、四文件、章节/sheet及平台行没有提前PASS；矩阵output_file/sheet仅未来消费者关联。
- baseline verifier为20,163/20,163文档完整性检查、exit0；新增PASS带执行引用所以多于Phase1的19,209，不是新增功能测试条数。release模式exit1/BLOCKED为预期，六产品门禁不变。
- 288个保护文件hash变化0；273个本轮初始跟踪文件仅4个允许文档变化（README、矩阵、两组执行规格），旧代码/测试/产品/归档变化0。详见`phase2-protection-final.json`。
- 新包源码/Schema实际SHA-256见`phase2-production-manifest.json`。范围与敏感扫描、diff/staged检查在提交前执行；发现值必须[REDACTED]，本次无凭据模式命中，不将其等同专业DLP认证。

## 6. 提交记录

| 阶段 | 已读取的本地提交 |
|---|---|
| Phase2A | 936428fa28ee2fb783f2800d80b2c9df4e6c7c5b |
| Phase2B | a30dcd37912ffdce3e636732c3892f8f6cf07a15 |
| Phase2C | 9114bf3d643f6041e918c8bd9c4b0f7b82c27809 |
| Phase2D | 0fe02688cefe5a2e3f851a8aa27bbb3261b3c74f |
| Phase2E | 本报告随`feat(solar-pv): Phase 2E formula input bindings and verified closure`提交；准确SHA以完成后git rev-parse HEAD及最终交付为准，不自引用 |

所有提交均本地，不push。未执行pull/reset/checkout覆盖用户文件。

## 7. Phase 3接口与未关闭事项

详见`docs/solar-pv/15-phase3-input-interface.md`及`14-phase2-architecture.md`。export是`solar-pv-input-export/1.0.0`，含完整project、normalized_inputs、逐原子来源、source_snapshot_id、input_hash、scenario_config及输入成熟度；不是canonical calculation result，没有run_id/result_hash或伪财务指标。Phase3必须重新校验版本/基线/分类/来源后独立执行模型、生成结果和验收；不能以目标收益倒推客观输入。

未关闭边界：

1. Windows硬内存/后代进程/目录竞态/ACL与真实symlink跨环境验证；公开不可信服务仍BLOCKED。
2. 无OCR、复杂表格/多环几何和代表性负荷映射不自动伪造。默认20,000解析cell、8MiB文本/worker输出、32MiB JSON，超限拒绝；全年15分钟大曲线流式/分块与性能在后续另验，不减少长期要求。
3. 资源/电价/政策/并网/权属/结构及设备真实材料和外部适配未取得项目级验证；全部工程测试数据为SYNTHETIC。
4. 标准授权全文、31项研究来源许可、税制/合同适用性、账簿详细运行时类型/算法、PDF渲染/字体/四文件一致性仍未关闭。
5. 新包最终分发许可与WorkBuddy依赖/安装/调用/审核未验；本轮源码本地运行不等于独立平台产品可用。

## 8. 独立门禁与停止

| 门禁 | 状态 |
|---|---|
| Phase2本地有界输入契约 | PHASE2_INPUT_CONTRACT_PASS，5项环境跳过明确保留 |
| 光伏发电量数值 | NOT_IMPLEMENTED / NOT_TESTED |
| 财务计算正确性 | NOT_IMPLEMENTED / NOT_TESTED |
| DOCX/PDF/测算XLSX/来源XLSX四文件 | NOT_IMPLEMENTED |
| 真实项目数据 | NOT_TESTED |
| WorkBuddy安装与调用 | NOT_TESTED |
| 平台审核/发布 | NOT_TESTED / BLOCKED |

**本轮在Phase2验收和本地提交后停止。没有执行Phase3。**
