# 独立 QA 报告（冻结候选限定）

## 裁定与边界

**PASS_LIMITED_DEPENDENCY_SOURCE_CANDIDATE_QA_WITH_LIMITATIONS**

本报告由独立quality执行环境重新读取真实本地来源、完整候选及历史图得出；没有导入作者rebuild函数。原CLI仅作为被挑战的拒绝入口，不构成独立重算证据。

- 审核HEAD：`1567fe5efb9cfe688047a16fa8c813fce8f48f32`；分支`main`；工作区干净、index空。
- 唯一审核对象：`RUN/developer-freeze-index.json` SHA `58dece4fc2903572776786076f70388273ec85bf8c601c265befe789588f5bab`。
- 冻结目录由索引字段读取：`RUN/review-payload`，451件、19381431字节，tree SHA `35f9d78d3305462c02f6249691f8f27bf6514954f5cbac3f416bf11ad66f4afd`。
- 候选锁SHA `65031b05cd22337b3e036c9d419cf1931b898068d4d90e82e6fd92fbabf10867`；download-plan SHA `4ac8f6281f24ed69ff0e64fd974dabc8efb9d21fa6e79a271d95e2502a0691bd`。
- 本地胶囊177项逐件解码并与当前原件比对；SHA `171656d7edd77345ba25edc333c2450db000dbbc38fdd30242531ecbad19f5e9`。胶囊及其原联系字段不得共享；本QA只输出身份，不复制原内容。

## 实测数量（不是pytest或测试类）

- 独立主要判定条目4360项；初次21项CSV字面不等，全部以真实specifier语义复核关闭。附加支持审计313项，失败0；另504 CSV行全字段复核504通过。上述有交叉覆盖，不相加冒称唯一测试用例数。
- 12完整目标图、每图44节点；全部2496条声明边，active 754、inactive 1742；到达集合、extras、marker上下文及版本约束逐项匹配。
- 42名称/43精确版本；43官方runtime exact JSON HTTP200；2backend单列；926官方runtime wheel记录；121 PEP658 metadata不是wheel，index期望摘要仍未核。
- 115唯一非yanked候选：34 pure、81平台件；486目标分配、18缺口。第三方构件已取得0、本地实际wheel摘要通过0。
- 16个互异负向案例全部观察到实际退出1及拒绝路径；1个正常候选观察到退出0。负向实际调用17次（含1次超时后的同案例重试），不是17个唯一样例；保留1次负向超时，不将其计为拒绝。另支持审计有1次wrapper超时，已独立重算收回，原stdout/stderr/exit124保留。
- 3458保护文件、705348461字节重新计算SHA且不变；安装Skill22件exact set/SHA不变；R8-R13 2638件仅size/mtime未变，不冒称全部内容哈希。

## 用户第13节18项逐条证据

|项|核查|结果与限制|本目录证据|
|---|---|---|---|
|1|42缺失名称与历史图一致|十二旧图逐一读取，42名称/43版本；tzdata Windows2026.5、其他2026.6。|`independent-graphs.json`|
|2|传递依赖|十二图各44节点含2内部节点；全部到达集、边和版本约束独立重算。|`independent-graphs.json`|
|3|extras|按请求extras传播队列至固定点，含markitdown四extras；未激活extras不混入。|`independent-graphs.json`|
|4|environment marker|从原METADATA/官方所指文件元数据重求上下文与active，逐边比较。|`independent-graphs.json`|
|5|版本冲突|全部active约束满足；未换pin弥补wheel缺口。|`independent-graphs.json`|
|6|Python tag|独立解析wheel标签，手写标准GIL CPython/pure/abi3判定；真实错误标签负向拒绝。|`negative-results.json`|
|7|ABI|cp312/313/314普通ABI与abi3分开；t ABI不等同普通GIL，负向拒绝。|`negative-results.json`|
|8|平台|Windows AMD64、Linux x86_64、macOS双架构及universal2条件逐项核；错误架构拒绝。|`independent-graphs.json`|
|9|Requires-Python|官方release、file与所指METADATA范围；504 CSV行逐字段语义复核。|`csv-all-fields-independent-verification.json`|
|10|官方/实际摘要分离|926官方runtime wheel记录，115唯一非yanked候选；第三方实际wheel摘要验证0。|`official-and-pep658-verification.json`|
|11|yanked|pypdfium2==5.15.1全12目标拒选；没有用yanked消除缺口。|`independent-graphs.json`|
|12|来源混用|43runtime exact JSON+2backend单列；121 PEP658的Name/Version、file URL/SHA和响应体身份核对。|`official-and-pep658-verification.json`|
|13|许可证|123请求原证重新分类，39名称/40版本exacttag文本；3项精确文本未闭合，全部42再分发仍BLOCKED。|`support-v2-license-independent-verification.json`|
|14|document双SHA|两本地wheel原字节、成员CRC/RECORD核对，13py相同，METADATA/WHEEL/RECORD及LICENSE不同；不任选。|`support-v2-document-independent-verification.json`|
|15|READY/closure|真实负向拒绝unknown-source READY、unknown-license PASS、unacquired actualhash PASS及缺件closure PASS。|`negative-results.json`|
|16|未越权改动|HEAD仅18个DOC新增442443字节；已提交blob与工作区逐件一致，3458保护件SHA不变。|`support-v2-protection-independent-verification.json`|
|17|已安装Skill|22件exact set及SHA不变；R8-R13另2638件仅元信息未变，不宣称逐SHA。|`support-v2-protection-independent-verification.json`|
|18|隐私/交付全集|451件类型/路径/唯一性/大小/SHA/来源及脱敏身份重算；冻结payload秘密/邮箱/用户家目录模式零命中，原胶囊不共享。|`payload-verification.json`|

## Findings与关闭状态

1. **QA-OBS-01（CLOSED，审计字面比较过严而非产品缺陷）**：CSV中cryptography九目标、six十二目标的Requires-Python次序/空格不同，共21行。原字符串全部保留；`SpecifierSet`的集合表达与候选完全等价。504行附加复核同时检查name/version、URL/SHA、标签、yanked、条件、状态及获取/摘要边界，无实际不一致。未修改CSV或候选。
2. **QA-EXEC-01（CLOSED_WITH_RETAINED_TIMEOUT）**：同版本不同SHA负向首尝试8秒超时，不算拒绝；同一变异输入再次真实CLI执行退出1并指出`$.files...sha256`不匹配。独立案例数仍16，原超时回执与输入均保留。
3. **QA-EXEC-02（CLOSED_WITH_RETAINED_TIMEOUT）**：支持审计第一次35秒上限超时；使用同一审计逻辑重新计算许可证/文档/资源检查，保护件改为有界六线程流式读取。313项完整实测失败0，3458件完整SHA复核结束；旧失败保留，不替写成PASS。
4. **原阻断（OPEN，不是本轮QA失败）**：pypdfium2==5.15.1所有发行yanked，12目标拒选；macOS x86_64的三Python目标各缺cryptography==50.0.2与onnxruntime==1.31.1。不得改版本填洞。
5. **许可与身份阻断（OPEN）**：beautifulsoup4 docs标题4.14.3/body4.15.0不是精确pin许可；cobble 0.1.4/v0.1.4的LICENSE/txt 404；protobuf已取得v36.2 LICENSE但7.36.2至tag/官方关联仍未证。lxml含iconv LGPL2.1、Pillow MIT-CMU。全部42再分发及wheel内LICENSE/NOTICE仍BLOCKED/ARTIFACT_NOT_ACQUIRED，工程初审不是法律批准。document两个1.2.0 wheel缺精确源码提交/构建环境充分绑定，不选择、不重打。
6. **后续唯一writer行动（OPEN，超出本QA写权限）**：把本报告原文绑定并写入正式QA入口，然后冻结新的文档/新payload，安排范围限定复审。当前确认不能迁移给未来payload或ZIP。当前冻结DOC中的PENDING_QA是历史快照状态，不由本审查员覆写。

## 保留门禁

`DEPENDENCY_CLOSURE=BLOCKED`；`LICENSE_REVIEW=BLOCKED`；`ISOLATED_INSTALLATION=NOT_TESTED`；`WORKBUDDY_SKILL_RUNTIME=NOT_TESTED`；`WORKBUDDY_HOST_E2E=BLOCKED`；`PROFESSIONAL_SEMANTIC_REVIEW=NOT_TESTED`。首正式目标仍UNCONFIRMED；Windows AMD64 CPython3.12只是条件研究建议，不是WorkBuddy实际解释器证据。Linux libc/minimum与macOS最低系统版本UNKNOWN。

外置12基线NOT_SELF_CONTAINED、optional11 NOT_BUNDLED、历史5回执/4原输入PARTIALLY_NOT_REPLAYABLE不变；未重放或生成替代输入。没有下载wheel/sdist/安装脚本，没有安装、改环境、改生产/Connector/Skill、旧证据、宿主调用、CH08、Word/PDF、Git写入、发布或封ZIP。本报告的隐私结论仅覆盖451冻结allowlist，不等于全机无秘密。

## 命令与预算

全部实际校验使用现有绝对CPython3.12解释器`-I -B`并经`RUN/record_command.py --role quality`录制，命令/精确输入快照/解释器/起止/stdout/stderr/退出码均在`RUN/commands/quality-*`；负向每次子进程另有独立receipt。现有主要5条wrapper已实耗157.095秒（含失败与超时），本报告生成及最后seal的实际耗时另见各自回执；最终总以`final-command-budget.json`及seal回执为准。质量角色总上限200秒，全任务1200秒；已知任务其他角色prestart保守20秒不抹为0，本QA无prestart失败。
