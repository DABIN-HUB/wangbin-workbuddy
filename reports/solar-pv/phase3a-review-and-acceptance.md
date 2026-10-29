# Phase 3A 独立审阅与基础契约验收

## 1. 本阶段结论与严格范围

**Phase3A基础契约按用户明确批准的已验证隔离快照本地验收通过，仅提交光伏范围，排除4个其他任务文件。不是PHASE3_CALCULATION_ENGINE_PASS，不是正式预可研报告可用或WorkBuddy审核通过。**

用户已确认packages/skills/wangbin-receivable-analyzer/SKILL.md、同目录manifest.json、products/catalog.json、reports/workbuddy-upload-list.md来自其其他任务，并明确授权按已验证隔离快照验收Phase3A、仅提交光伏且排除这4处。确认原文及历史阻断保留于phase3a-precommit-blocker.json，复核收据见phase3a-isolated-acceptance.json。隔离快照288保护文件逐项哈希无变化，基线复跑exit0；当前工作区仅这4个保护文件不同，保留且不暂存。当前工作区20159/20163及exit1的历史证据不删除，也不改写成工作区保护PASS。验收边界是隔离快照，不是豁免或重写原冻结保护基线。

本阶段完成批准的六项版本化勘误、受控方法配置、有界时序基础、计算输入/图/执行映射和唯一结果Schema。保留原469字段、281域、89公式、原始方程及12份冻结哈希。起始HEAD为`554c08859489d5fa2d8447f94c6494c9ed4bdb2a`；本报告与3A实现执行同一次本地提交，提交后准确SHA从git log读回，不把尚未生成的SHA写作事实。不push、上传、发布或部署。

| 公式/项目统计 | 当前实际状态 |
|---|---|
| 注册公式 | 89 |
| Phase3适用 | 82 |
| 已实现且专业数值验收 | **0** |
| 本阶段适用但尚未实现 | 82，仍NOT_IMPLEMENTED |
| Phase8储能保留 | 7，仍NOT_IMPLEMENTED，不伪装不适用/通过 |
| 项目不适用/待方法审阅/数值未过 | 尚未进行项目计算，不能以注册统计替代项目评估 |
| 工商业屋顶完整SYNTHETIC项目 | 尚未实现/计算 |
| 集中式地面完整SYNTHETIC项目 | 尚未实现/计算 |

真实公式数值、两个完整项目及最终专业验收继续属于已批准3B—3G，不以本阶段测试数量替代。

## 2. 已交付生产契约

- D1有效版本`solar-pv-formula-definitions/1.0.1`，hash `617a2e9d314c095bd2ec893939c930a2323be6fd7805da12bf6d6fdd70274808`。同一Catalog显式区分frozen/effective；正式errata/lock/严格Schema/信任锚/旧输入兼容及旧结果须重算规则齐备。E01—E06各有真实RED与GREEN日志，E02首次GREEN失败也保留，没有改旧断言掩盖失败。
- D2方法Schema独立版本，67项受控选择/参数，有类型、单位、中文/英文、来源、状态、版本、分类及边界。部分配置有效不等资料齐全；缺方法/金额不补默认。方法进入复合输入、来源快照及结果hash。旧469字段和281域不是复制到第二套参数系统。
- D3默认32MiB保留；新bundle独立版本，完整原子信封、时间/时区/重复/缺口/顺序/单位及来源校验，资源硬上限，流式/完整canonical数组摘要一致，layout-independent content身份，manifest最后原子无覆盖发布。失败产物不能被认为完整有效。
- 小输入唯一计算入口完整重验Phase2导出；JSON排序不改变旧source记录顺序身份，组合入口复验可变包装对象。bundle必须是真实验证句柄，再完整遍历复验后发布复合身份，不接受任意自称已验证摘要字典。
- 图显式区分期间、物理边界、方法与依赖；89条有效公式/符号/单位/来源/条件/原字段/拟模块完整保存，空壳登记不能获得IMPLEMENTED_TESTED。
- 唯一结果Schema与hash、部分数值身份、指标血缘、有效定义漂移及未来版本拒绝均实现。新配置/结果拒绝二进制float及不稳定整数token负零，不更改旧序列化身份。
- CLI新增calculation-schema、method-schema、calculation-formulas，仅导出契约，不运行项目或升级发布门禁。私有安装wheel版本0.3.0，旧输入Schema版本未改。

架构详见docs/solar-pv/20-phase3-calculation-architecture.md；执行映射见本目录phase3a-effective-execution-mapping.json；结构化状态见phase3a-state.json。

## 3. 真实运行证据

| 验证 | 实际结果 | 证据 |
|---|---|---|
| 最终冻结源码完整光伏suite | **3277 passed / 0 failed / 6 skipped，exit0**；1188.05秒 | phase3a-evidence/3a-final3.log/.xml、run-receipt及source-hashes |
| 修复相关子集 | 89 passed / 0 failed | 3a-negative-zero-green.log/.xml |
| 隔离旧产品完整suite | 145 passed / 0 failed / 5 skipped；包含Expert36项 | 3a-legacy.log/.xml；仓库外无.git副本 |
| 生产Python编译 | 33个文件通过，未向工作区写pyc | 3a-production-and-wheel-source.json |
| 实际安装wheel与源码 | Python模块逐字节一致，静态Schema等于动态生成器，原/有效锁等资源齐全 | 3a-final2-wheel-receipt.json及生产源码比对 |
| 冻结文档/保护完整性 | 已验证隔离快照重新运行exit0；实时工作区4个其他任务文件变化，不宣称实时保护PASS | phase3a-isolated-acceptance.json及phase3a-precommit-blocker.json；保留原失败证据 |
| 发布门禁 | **BLOCKED，真实--release exit1** | 3a-complete-release.json |
| 旧资产保护 | 隔离快照288文件哈希全部不变；实时工作区只存在4个用户确认的其他任务变化，本次提交明确排除 | phase3a-isolated-acceptance.json；不覆盖历史证据或其他任务文件 |

所有3277条通过来自完整final3实际运行，不是把单项重跑与原失败套件拼成假全量通过。源码在运行前后及与当前工作区比较无漂移。6项skip均Windows symlink权限不足，不计PASS；NTFS junction/hardlink另有真实执行。旧suite自己的5项同类skip独立计数，不能把两组简单相加当独立缺陷数。

### 失败及环境修复留痕

早期180秒超时和被后续源码修复取代的运行不计PASS。final2完整运行真实为3276 passed/1 failed/6 skipped，唯一失败是无.git快照不能执行固定历史Catalog的git show。未改测试或断言，另建独立scratch裸对象库，仅从本地读取固定554c0885历史，逐字节核对历史文件；仅向验证子进程设置GIT_DIR，不暴露用户真实Git配置、不向用户仓库写入。失败用例单独实际重跑通过后，再完整运行final3得到上述3277/0/6。原final2失败日志/收据仍保留。

初始pip wheel因环境没有pip/setuptools/wheel/build失败，后改用已有uv离线构建/安装成功，没有伪造pip成功或引入新生产依赖。最终私有wheel SHA256为`6a61426f631ad6bc8a16501cdf53c726cb51b805806503fd7b2be98fbc020087`；仅本地安装验证，不是公开可下载发布。

## 4. D3最终源码实际容量与吞吐

全部为完整SYNTHETIC负荷表，写入和完整读取均逐原子验证，随后再逐行求和；不是只测JSON长度，不是全年光伏发电或财务模型。最终源码哈希与容量收据逐项一致。

| 行数 | 每次写/读校验原子数 | 实际磁盘bytes | 写秒 | 全读校验秒 | 再遍历求和秒 | 写/读MiB/s | 求和kWh |
|---|---|---|---|---|---|---|---|
| 8760 | 52560 | 54153998 | 42.16 | 39.45 | 11.15 | 1.225 / 1.309 | 21900.00 |
| 35040 | 210240 | 216813204 | 152.68 | 153.80 | 46.66 | 1.354 / 1.344 | 21900.000 |

数据来源为phase3a-evidence/capacity-8760.json和capacity-35040.json。完整suite进程的Windows OS生命周期峰值456712192bytes（435.55MiB），低于容量用例512MiB授权预算；不是容量操作独占分配，不能与较早独立D3进程98.06MiB峰值混同。写/读资源预算在检查点协作式执行，不能抢占阻塞调用者/native调用，也不是OS沙箱。

## 5. 独立审阅闭环

- deleg_9286198d发现P1：PARTIAL数值跳过来源/输入身份；P2：四类metric悬空引用、binary float往返hash漂移、消费者未接有效定义完整性。
- 父任务逐项真实回归并修复；deleg_512dc00a只读复核确认原4项按发现范围关闭，同时新增Decimal整数token负零P2。
- 负零回归真实2 failed/19 passed→修复；相关suite89 passed。deleg_9007a866静态确认仅拒不稳定-0，不拒可稳定往返的-0.0/-0E+3，新增P2关闭。
- 以上是独立静态契约审查，不冒充独立专业数学计算审查。3G仍须再做完整独立审阅及数值验收。

## 6. 未关闭边界与后续

1. 82条数学执行器、真实发电/消纳/投资/税费/融资/现金流/财务指标/敏感性和两完整项目尚未完成，不升级公式/项目门禁。
2. 6项symlink权限分支未执行；真实项目来源/许可/税制/融资/设备参数适用性仍需证据。历史标准全文/外部来源许可缺口不因本阶段关闭。
3. D3当前跨数据集时间对齐、逐组DC分配、损失覆盖台账和实际全年工程/财务计算仍由3B—3G消费端落实；大表求和不替代它们。
4. 真实项目、四文件、18章正式报告、WorkBuddy运行/安装/审核均未通过；六发布门禁及总release保持BLOCKED。
5. 3B只读准备见21号文档。核查没有要求扩大D1批准范围：原式已定义逐组逆变限幅；PF已有严格正质量阻断；排放单位桥已在现有units与绑定支持；月度/时序状态明确分开。若实际实现还需改变冻结数学/关键用户数据契约，必须另报差异，不能借这份准备自行批准。

本阶段本地提交并读回SHA后继续原批准3B—3G；3G最终全量/独立/数值/保护验收报告完成后停止，不自动进入Phase4。
