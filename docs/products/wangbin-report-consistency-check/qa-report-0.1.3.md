# Q05 T03-RERUN-1 独立 QA｜0.1.3 本地 PASS

- product_id=`wangbin-report-consistency-check`; task_id=`t_2087a218`; workspace=`F:/ideaWorkSpace/wangbin-workbuddy-report-consistency-check`; branch=`skill/report-consistency-check`; base_commit=`387e782dbb0a6d1878439f5f1ec9c92f277a5a70`（待本报告提交前 HEAD，亦为开发候选提交）；result_commit 见独立提交日志。
- 精确候选 `dist/wangbin-report-consistency-check-0.1.3-skill-candidate.zip`，SHA-256 `549111865465d3feb9faf5aaedf69738be6efd48094b1f61dd127e0b29ed9b38`。`ZipFile.testzip() is None`；四个成员与 manifest 逐个 SHA-256、长度、干净解压文件和仓库同版源文件逐字节一致；sidecar SHA/manifest version 0.1.3 匹配。旧 0.1.2 ZIP SHA-256 仍为 `4bf56c5786343c65c38dfa1aa4ecfde722bac861e7574432d8881d005457f0f8`；旧失败报告、旧探针和旧逐格证据未改。工厂完整性不替代业务 QA。
- 执行命令（上述 workspace）：`uv run --no-project --with openpyxl --with python-docx python docs/products/wangbin-report-consistency-check/qa_rerun_probe_0_1_3.py` → exit **0**，**44/44** 案例断言 PASS，**36** 次产品 CLI exit 0、**8** 次预期错误 CLI exit 2。探针在 wb-quality profile scratch 新目录 `q05-qa-*` 解压候选，所有业务子进程只调用解压后的 `scripts/check_report.py`；输入 XLSX/DOCX 由探针实际创建，成功输出均以 openpyxl 重开并逐表核查五表 `核查概览/指标对应/差异明细/待确认口径/未覆盖项`，且无输出公式，44 次调用源件字节 hash 不变。逐案原始 stdout/stderr、完整五表逐格内容、预期与检查结果留于 `qa-evidence-0.1.3.json`，新探针为 `qa_rerun_probe_0_1_3.py`。`python -m tooling.products verify --id wangbin-report-consistency-check` → exit 0/PASS（只核完整性）；`python -m tooling.products validate --id wangbin-report-consistency-check` → exit 0/PASS。

## 修复独立复验

| 缺陷/新输入（均为虚构） | 独立预期 | 实际（重开输出/错误 JSON） |
|---|---|---|
| D1 原失败变体：`数据!A2=100` 表头收入/CNY/元、`B2=100` 收入/USD/元；DOCX 收入200元人民币；明确规则 sum(A2,B2)、exact | NOT_COMPARABLE，差额空，禁止 MATCH/0 | `REP-X02-cross-currency`: NOT_COMPARABLE/待确认，差异明细无误称已核实 |
| D1 新 fixture 70 CNY+30 USD、70 USD+30 CNY；报告收入100元人民币，确认 sum(A2,B2) | 两种操作数顺序都 NOT_COMPARABLE，不计算差额 | `D1-CNY-USD`、`D1-USD-CNY` 均 NOT_COMPARABLE，待确认表留空差额 |
| D1 新 fixture 70 CNY+30 未标币种及相反顺序 | 无法证明同币种，PENDING_CONFIRMATION，无数值差额 | 两例均 PENDING_CONFIRMATION，未错误填零 |
| D1 新独立身份/量纲 fixture：跨青禾/云杉主体（context 显式 subjects）、本月/累计、实际/预算、未税/含税、金额/% | 五项不能求和 | 五例分别 NOT_COMPARABLE、差额空；未标主体字词不冒充已识别的主体 |
| D2 非 ZIP 内容伪装 XLSX、DOCX；有效 DOCX/XLSX 对照 | `UNSUPPORTED_OR_SPOOFED`, exit 2，不能产成功五表 | 两例 exit 2、错误码吻合、无输出 |
| D2 `PK\x03\x04broken archive` 真正损坏 ZIP 格式 XLSX、DOCX | `UNREADABLE_OR_ENCRYPTED`, exit 2 | 两例 exit 2、错误码吻合、无输出；此例不声称模拟了加密 OOXML |

旧 31 例重新运行：CORE A/B/C/D 单位/差额、舍入500元、百分点2与相对20%；REP-A05–A16（A09双错误、A13 初次两候选/确认后 C2、A14 图片未覆盖、A15 排除章节号、A16 -30000元）；REP-X01–X06 求和、比例、非数值、三次重传变化（RESOLVED/NEW）、注入文字不写出公式、40000格资源限额；缺文件/冒牌和非 ZIP 文档均符合本版错误分类。`ERR-bad-docx` 的旧探针输入为 `not docx`，并非真正损坏 OOXML，故新版预期改为 `UNSUPPORTED_OR_SPOOFED`；新 D2-BROKEN 两例专门覆盖损坏归类。保留的旧开发测试 `test_spoofed_input_and_forbidden_output` 仍断言已失效的旧错误码，未经修改且其直接执行失败；这是遗留测试维护风险，不作为新版业务合同成功证据。

## 门禁与剩余风险

**仅对上述精确 0.1.3 候选放行 T04 本地候选复核，不是发布批准。** REP-A13 的初次/确认是两个独立 fixture，不是同一文件先后补映射；同源文件补映射的状态演进 NOT_TESTED。真实加密 OOXML、Windows symlink 越界（旧轮权限不足）、输出目录权限/逃逸、网络监测、极端压缩/性能、复杂合并表头和未知量纲组合 NOT_TESTED。实际 WorkBuddy Skill 六句中英模型对话、平台安装/运行/审核、版权许可/依赖权利与相似性人工审查、上传/发布均 **NOT_TESTED**。未 push、未覆盖旧 ZIP 或失败证据；不得将本地 PASS 说成平台通过。blocked_reason=null；残余风险如上。