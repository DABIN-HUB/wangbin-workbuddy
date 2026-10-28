# 光伏 Phase1 研究与完整需求冻结：最终评审及验收

日期：2026-10-28。范围仅Phase0/Phase1；**Phase2未启动，光伏产品不可运行，未生成四份最终交付，不提交平台。**

## 一、阶段结论

- Phase0：`PASS_WITH_RECORDED_LIMITATIONS`，已提交 `f55cba2bc0e40aa009d48e49b9eed8b6e094e19b`；详见phase0-acceptance.md。
- Phase1：`BASELINE_FROZEN_WITH_OPEN_RESEARCH_ITEMS`。用户原文完整归档，研究及全部要求持久化、机器引用闭合、独立审阅四项问题已修订；尚未取得的标准全文、许可、工程/税/协议方法与平台证据不伪装完成。
- 原始代码基线：main / `c9b73291200e904a875ec2e2642f7492bd311036`。初始远端main读回`5407d86b990633753ae577a9e799640da93f4c54`，本地领先1，未pull/reset/checkout覆盖。Phase1提交前HEAD为上述Phase0提交；本报告不预写自己的未来commit SHA，最终本地SHA/工作区由实际git读回并向用户交付，可用 `git log -1 -- docs/solar-pv` 复核。
- 收尾再次执行git ls-remote时网络命令180秒超时，未得到新的远端SHA；上述远端关系明确只指首次成功采样，不声称收尾时远端没有变化。已通过的本地暂存检查仍有效，网络复查不作为本地文档commit的前置；本轮无push。

## 二、冻结交付与可追溯范围

统一入口 `docs/solar-pv/README.md`，原始总提示词全文（第0–11节、213行）在 `00-original-user-baseline.md`，`00-baseline-manifest.json`记录源文件及规范化SHA-256。原始附件SHA-256：`4af609040ca4e800b16d561b86a8a33c54226d175581b54aa00110158c5d09f2`。未修改原文，只在各专题作补充分解与消歧。

用户指定的`00-repo-audit.md`、`00-reuse-matrix.md`及`01`至`11`全部指定文档/CSV已落盘，另有机器JSON、公式/术语扩展、输入与公式域绑定、同源结果契约和只读校验器。以下数量来自最终执行输出而不是人工估计：

| 项 | 冻结结果 | 不代表什么 |
|---|---:|---|
| 追踪矩阵记录 | 1208 | 非1208项已完成功能 |
| 原文非空正文行追踪 | 140 | 标题/空行/围栏不计正文条款，全文仍213行完整保留 |
| 输入字段记录 | 469 | 446标量＋22对象数组＋1前置ID标量数组，非首轮长表单 |
| 公式 | 89 | 77基础＋12扩展；数值测试PLANNED，适用标准方法仍需核对 |
| 公式域字段绑定 | 281 | 引用闭合不代表运行时转换或计算图已实现 |
| 中英术语 | 189 | 含22最低必需缩写及公式名称；正式报告首次释义仍需未来渲染检查 |
| 未来/基线验收规格 | 1207 | 不是1207项已运行数值或E2E测试 |
| 正文/附录 | 18章100子项、13附录26子项 | 不是已生成18章真实报告 |
| 分类 | 9 | 当前全部NOT_IMPLEMENTED，P0/P1/P2不可互借验收 |
| 工作表 | 29 | 测算19＋来源10，仍未生成XLSX；逻辑变量/术语词典映射物理变量-术语词典 |
| 保护既有文件 | 288 | 本轮复算变化0，旧风险并未因此消除 |

本轮矩阵只关闭 `WORK-P0-AUDIT`、`WORK-P1-FREEZE` 两项基线工作；1206条PRODUCT记录仍NOT_IMPLEMENTED。章节、字段、公式、术语、分类和工作表逐条有test_id及验收断言，未执行的功能证据保留NOT_TESTED。不得把FROZEN替换成产品PASS。

关键路径：
- 18章细纲/逐子项：`docs/solar-pv/02-report-outline-18-chapters.md`。
- 输入与来源信封：`03-input-data-dictionary.md` / `03-input-fields.json`。
- 研究：`04-source-registry.md` / `04-sources.json` / `04-source-chapter-comparison.csv`。
- 公式与符号：`05-formula-registry.md`、`05-formulas.json`、`05-formula-extensions.json`、`05-extension-formulas.md`；字段/非恒等单位与账簿映射见`05-field-bindings.json`、`05-unit-and-field-bindings.md`。
- 双语词表：`06-glossary-zh-en.md`、`06-glossary.json`及extensions。
- 分类隔离：`07-category-boundaries.md`；全类型逐章矩阵在02。
- 可执行矩阵/规格：`08-requirement-traceability.csv`、`08-baseline-contract.json`、`08-acceptance-cases.json`及derived、`08-field-contract-digests.json`。
- 四文件：`10-four-file-acceptance.md`，统一计算结果契约在12，逐Phase路线在11。

## 三、实际研究结果及边界

合并来源索引49条：专业cohort37＋平台/政策/更新索引11＋公式损失帮助页1，三集合有明确ID和访问范围，未把数量相加伪称49份工程报告。

专业cohort机械统计：发现登记37、正文或标准元数据有效30、结构提取26；严格完整文本可读11（6 PDF＋5技术/API HTML），具体真实项目来源12，严格完整真实工程可研3；7项受阻或仅JS壳，31项许可REQUIRES_REVIEW。公开工程示例报告0；API公开样例不能算工程报告。实际可抽文字页和物理页计数不是人工逐页精读声明。

种子两项NB/T编号/名称/现行元数据已核，**授权标准全文取得0**，未编造条款/目录。IFC、PVWatts、GSA、NASA POWER、PVGIS、IRENA、国内工程/EPC及海外真实可研按实际可读范围登记；新版IRENA本次只有执行摘要，不冒充全本；历史成本/异地电量不作为本站默认。NASA/PVGIS两个公开样例真实返回成功，仅作接口研究，不是生产适配器验收。

父任务重新GET 6项关键原站并核对标准元数据/报告封面和物理页数，见`phase1-parent-source-recheck.json`。WorkBuddy当前官方网页四页直连读取，官方可选skills/dependencies与仓库prompt-only严格规则的差异写在`00-platform-recheck.md`；没有放松旧Expert规则。中国2025年以来政策及省级差异按POL-*单列，不把任何省的历史机制价设为全国/本站默认。

工具限制如实保留：当前未提供可调用web.run，web_extract因后端只支持检索失败；实际采用公开检索＋原站匿名HTTP/HTTPS＋PDF解析。无伪造工具结果、数据响应、全文获取或页码。未把第三方报告整本放入仓库/商用包，未知许可仍待审。

## 四、独立评审与修订

见`phase1-independent-review.md`。四项P2问题均经主任务读取真实字段后修订：C类投资金额血缘、负荷/无债务条件必填、日内时间合法范围、无前置任务的唯一ID数组及逐元素provenance。同步MD、JSON、矩阵和验收规格；原field_id/requirement_id/test_id不变，不删功能。最终校验增加对应静态/正则检查和字段摘要以防再次漂移。它不等于Phase2输入解析器已实现。

## 五、真实执行和验收证据

### 5.1 文档完整性与引用

在目标仓库执行：

```text
python docs/solar-pv/verify_baseline.py
exit=0; 19209 checks passed; 0 failed
python docs/solar-pv/verify_baseline.py --release
exit=1; BLOCKED
```

`phase1-final-baseline-check.json`与`phase1-final-release-check.json`为实际stdout。19209项是文档/索引/引用/保护检查计数，**不是光伏数值单元测试数**。发布非零是正确行为，因为产品六门禁和实现需求都未通过；不能把这个预期BLOCKED算成功发布或改为exit0。

### 5.2 最终仓库回归

将当前新增文档/校验器同步进受保护的scratch源码副本后，使用已安装归档CLI与依赖的独立Python3.12.0环境，运行未修改的既有根测试＋软件顾问包内测试：

```text
cwd=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/repo-baseline
C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/verify-venv/Scripts/python.exe -m pytest tests packages/experts/wangbin-software-consultant/tests -ra --basetemp=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/pytest-phase1-final --junitxml=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/phase1-final-junit.xml
exit=0; collected150; 145 passed, 0 failed, 5 skipped
```

完整日志`phase1-final-regression-pytest.txt`，JUnit为`phase1-final-regression-junit.xml`。5项均Windows符号链接能力未开放，不能记安全PASS。首次开发环境缺CLI发行元数据造成的144通过/1失败/5跳过仍在Phase0证据中保留；安装已有wheel后复跑真实通过，不改旧代码/测试/依赖来消除失败。隔离副本防止旧CLI测试改写原仓库reports/validate.*和归档。

### 5.3 变更/隐私/保护

定向凭据模式扫描docs/solar-pv与reports/solar-pv无发现，未读.env或凭据文件；模式扫描非完整隐私/安全认证。git diff --check及显式暂存后的diff审查是提交前门禁。288保护文件hash变化0；catalog/metrics、旧Skill/Expert/Connector、模板/许可证与全部旧ZIP/wheel未改。所有变更仅新增本项目docs/reports和基线校验器，未改产品工厂核心或新增测试依赖。

## 六、四文件与六门禁：单独判定

| 维度 | 当前状态 | 本轮结论 |
|---|---|---|
| 冻结文档/矩阵完整性 | PASS（基线层） | 不推导实际报告结构通过 |
| 实际报告文档完整性 | NOT_IMPLEMENTED | 无DOCX/PDF/XLSX实物 |
| 计算正确性 | NOT_IMPLEMENTED | 无光伏确定性引擎数值验收 |
| 本站数据真实性 | NOT_TESTED | 无具体站址真实资料评价；研究样例不冒充本站 |
| 运行环境兼容性 | NOT_TESTED | 旧CLI的Windows回归不是新渲染依赖或跨平台通过 |
| WorkBuddy安装调用 | NOT_TESTED | 未上传、安装、召唤、调用或取回文件 |
| 平台审核 | NOT_TESTED | 未提交审核/发布，不把本地commit当平台回执 |
| 四文件交付 | NOT_STARTED / BLOCKED | 四件均尚未生成，不用Markdown冒充 |
| 发布 | BLOCKED | 缺产品实现/数值/数据/渲染/许可/安全/平台证据 |

最终四文件仍不可删减：项目名称-光伏预可研报告.docx、同名.pdf、项目名称-测算模型.xlsx、项目名称-资料来源与假设清单.xlsx。后续完整L2/L3必须同canonical JSON、五标识一致、真实可打开并经数值/结构/视觉验收；PDF依赖失败不得假文件或部分成功。

## 七、已知风险及下一阶段依赖

- 标准正文及商业使用授权、各项目适用税制/融资协议/设备与温度子模型需要专业核验；当前方法冻结不是标准认证。
- GSA JS、部分WAF/网络受阻、当前成本范围/含税/甲供边界、部分资料授权冲突继续保留；不以删除来源或假默认消除风险。
- 旧附件解析器不是OS沙箱，Windows资源硬限制/后代进程/XLSX主进程/竞态/ZIP静态缺陷等不在本轮修复，公共不可信解析仍有阻断。
- 发现PATH和两个常见安装路径未见LibreOffice/soffice；不宣称所有转换器均不存在。Phase5前须选定可靠转换器/中文字体/许可并真实渲染。
- Phase2如继续，只实现已冻结数据契约、输入/单位/来源/冲突/分级及受限解析；优先工业屋顶，不提前注册空壳产品，不借屋顶模型宣称地面/农渔/储能/P2通过。标准/方法未核实部分保持命名阻断，不要求为做Schema就补造站址数值。

本轮停在Phase1，本地审查后提交，不push、不上传、不审核、不公开部署。后续会话以README→完整原文manifest→矩阵→最新阶段报告→实际git/代码/保护哈希恢复，不因上下文丢失降低范围。
