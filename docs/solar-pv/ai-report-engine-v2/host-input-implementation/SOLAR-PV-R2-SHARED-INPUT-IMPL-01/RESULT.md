# SOLAR-PV-R2-SHARED-INPUT-IMPL-01 · R1独立QA后测试整改候选

**当前仍为 PARTIAL / 非发布wip / NOT_AI / NOT_HOST_E2E。** 独立R1已完成：审查提交 `44c26c972ca1a23eab6f56888d9ed014e8df5367`，134个唯一pytest用例通过及独立边界探针通过；原32秒未接受过期组合probe为TIMEOUT/124，不判PASS。R1未确认生产逻辑缺陷，唯一必验阻断QAI-R1-01仍待闭合。完整原文/身份/命令见QA_INDEX，原报告不改。

本次只追加两个屋顶正式测试：首次native publish过期拒绝；有效期publish后native/core accept过期拒绝。每例独立新NOT_AI授权及生产prepare-r2-shared，不使用参数化双案；第二例只将本例新建且已验证的published run原字节分支，隔离两条accept的失败封口，不改期限/hash、不冒充新授权、不删除failure。**作者未执行这两个新测试，状态NOT_TESTED_PENDING_INDEPENDENT_QA**；不将静态语法/快照/Git检查当产品测试通过。生产与Skill七文件相对R1原字节不变，新的八文件集合见 `RUN/developer-source-snapshot-r2.json`；新增测试差异与整改交接见 `RUN/developer-fix-r2.diff`、`RUN/developer-fix-report-r2.md`。本轮不封装、不审核最终共享payload。

以下开发首轮结果为历史实测，R1新增结论与整改待验状态优先；两次开发生命周期组合TIMEOUT原证保留，最终拆批3通过不改写原超时。

## 实现与身份

基线main `9cf8cdae81402119ccc76d697346289b1b361e89`；授权、保护及未批范围见PLAN。历史EXC006仍PROPOSED_NOT_APPROVED，未改旧审计。新增 `reporting/host_input_view.py`；必要接入chapter_writer/host_session/host_output；Skill源码仅SKILL.md与host-orchestration.md说明。wrapper已有通用透传，未改其sys.executable -I或环境清理。

新增动作 `prepare-r2-shared`；严格可选grant policy进入新授权、state、request绑定。默认prepare/prepare-r2无新字段；新模式不能静默回退或原run换模式。request/canonical/授权/规格/模型与重建pack是可信原件；公共_request在原链之后校验确定性view/manifest；首次制备在锁内先基础重建，再独占派生与完整校验。host_output额外接公共派生校验，原因是publish_response和verify_publication可被直接调用，不能只靠宿主prepare。缓存上游也重新进入公共_request，避免缓存跳过完整性。

共享pool平坦、只替换完全相同对象/数组；数字用显式$number保留原词法，不经float重格式化。S索引不进入正式引用。固定资源上限与先计量后复制阻断缓存深度77反例；不复制offline_view_audit整份脚本，不接类型行、不改领域权限生产者/validator/Schema。

R1被审源码/测试/Skill八文件原字节集合SHA256 `c5fe505dcd32b6d18d2553dc8d8d4dde419d1d7abce1ad9345b308e1722bc22f`，算法与逐件SHA见RUN/developer-source-snapshot.json（含未改wrapper）。当前测试整改候选另存RUN/developer-source-snapshot-r2.json，只有测试文件变化；不是Git tree对象。首轮commit/status原证RUN/developer-final-state.json保留，新commit/status另存RUN/developer-final-state-r2.json，避免自引用。当前冻结后等待quality对改变的测试及相应风险独立复验。

## 实测新表示

| expired历史codec输入 | 原file B | 新view B（含reading/封套/LF） | pool | 还原 |
|---|---:|---:|---:|---|
| 屋顶 |343018|236999|36|原字节含LF完全一致|
| 地面 |343904|237669|36|原字节含LF完全一致|

每view内部570 B阅读语法已计入；detached manifest分别1948/1952 B，是程序校验材料，不要求模型读取。比旧递归原型稍大，是平坦共享/明确数字词法包装和完整阅读封套造成，不追求原228621/229291 B。数据/hash/视图/manifest原件见RUN/developer-measurements.json及双案production-codec文件。这两份仍是过期codec输入，不是新授权，未改expires_at。真正新授权/新request/新view来自独立NOT_AI临时workspace，完整保留在RUN/pytest-lifecycle-bounded双案目录。

## 验证、保护与未完成

- codec-risks：35通过（两案重seal、QA-F01四类、语法/资源/预算等）；最终small gates：12通过（含原wrapper回归）；双案新生产生命周期批：3通过。各批重叠不相加。JUnit与真实命令见VALIDATION；full repository/财务/Office完全未执行。
- 开发首轮预算420s、实测409.14940179884434368s（原冻结记录）；source_lifecycle_failure_guards等开发未跑项已由R1独立QA按其原文范围补验，包括legacy四组byte/hash、strict、先验证再派生/真实初次崩溃与授权变异。唯一未闭合的必验覆盖为共享模式未接受过期publish/accept；新增两个正式测试待quality首跑，不能把原409s当本轮剩余预算。全轮900s含所有角色与最终保护/封装；此次不重跑昂贵生命周期。
- 1674项基线保护逐字节核对，只有5项授权既有源码/Skill变更，无意外；已安装22文件全hash不变（21包载荷+元信息）；规格LF SHA不变。旧审计/原请求/canonical/dist原件无变化。R8–R13继续仅继承元信息口径，不说成全内容hash证明。
- 卫生--check真实exit0；无本轮生成物入Git，未删除旧资产，净删除0文件/0B、释放空间0。新增tracked只授权源码/测试及本轮必要文档；当前dist完整、忽略且未替换。早期pytest默认系统临时目录证据未清，后续使用本RUN basetemp；不清未知缓存。最终status与文件计数由final-state读回。
- **本地共享实现R1独立QA=PARTIAL_NOT_AI_NOT_HOST_E2E；QAI-R1-01=TESTS_ADDED_PENDING_INDEPENDENT_QA；SOURCE_REVIEW_CANDIDATE=PARTIAL。** QAI-R1-02是已有完整独立诊断的建议，未扩大源码；最终payload/脱敏确认仍未完成。本轮没有新wheel或Skill候选，不编造SHA或安装成功。

## 继承门禁（逐值）

```text
WORKBUDDY_552_CLIENT_VERIFIED = PASS
WORKBUDDY_R2_SKILL_IMPORTED = PASS
WORKBUDDY_R2_HOST_NEW_ROOF_CH08 = BLOCKED_NO_DRAFT
WORKBUDDY_R2_HOST_NEW_GROUND_CH08 = NOT_TESTED_BLOCKED_BY_STOP_GATE
ROOF_JSON_SCHEMA_VALID = NOT_TESTED_NO_DRAFT
GROUND_JSON_SCHEMA_VALID = NOT_TESTED_NO_DRAFT
ROOF_STRICT_CHAPTER_VALID = NOT_TESTED_NO_DRAFT
GROUND_STRICT_CHAPTER_VALID = NOT_TESTED_NO_DRAFT
INSTALLED_R2_ENGINE_AND_DEPENDENCIES = UNVERIFIED_BLOCKED
WORKBUDDY_R2_PUBLISH_ACCEPT_RESUME_DOCX = BLOCKED_NOT_EXECUTED
WORKBUDDY_R2_HOST_E2E = BLOCKED
R2_REAL_MODEL_CONTENT_ACCEPTANCE = BLOCKED_NOT_PASS
INDEPENDENT_QA = PARTIAL_PREVIOUS_EXECUTED_UNCHANGED
PROFESSIONAL_SEMANTIC_REVIEW = NOT_TESTED
PHASE_D_CONTENT_REVIEW = USER_REVIEW_REQUIRED
TRUSTED_ENGINE_INSTALL = BLOCKED_UNVERIFIED
WORKBUDDY_INSTALLED_HOST_E2E = BLOCKED
THIS_AUDIT_INDEPENDENT_QA = PARTIAL
```

候选终期现金合法重绑定、SCENARIO_COMPARISON BLOCKED/ranking空、基准独立交易费实付缺口、会计盈利/经营现金/股东回收裁定、PDF公式复制检索/真实资料/专业签审、同canonical五身份正式四文件、STATIC_SNAPSHOT披露、全仓回归/Expert/发布均不关闭，不移AFTER_V2。Phase D仍双案CH05/08/10/14/15/16/17/18，本轮仅CH08输入；无宿主新内容/CH10或16解锁。

下一条件：quality对r2冻结候选的两个新增测试分别有界首跑，不扩大原32秒单命令上限，不重跑昂贵全量；仅在真实完成后追加新独立结论。manager随后处理固定payload审阅与SOURCE/REVIEW ONLY归档，本作者不处理。受信R2构件依赖、精确Skill替换、官方支持输入路径与一次全新屋顶CH08分别另批，地面仍受屋顶停止门限制。本次未模型/网络外发/安装/构建/打包/财务重算/新客户端任务/push；历史门禁逐值不变。
