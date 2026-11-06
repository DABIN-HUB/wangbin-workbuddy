# Q01 T03 第二轮独立 QA — 本地候选 PASS（发布 BLOCKED）

- product_id=`wangbin-import-precheck`；task_id=`t_4edbd8f5`；workspace=`F:/ideaWorkSpace/wangbin-workbuddy-import-precheck`；branch=`skill/import-precheck`；base_commit=`03b7a4797c309af56788cd342a09db215e720aa9`；冻结合同 commit=`87d4be0df3ff400a8b175d3a33a3b01d8990600b`。验收预期取权威 V2 §09–14 与冻结 acceptance-cases.md；旧报告 `qa-independent-v2.md` / commit `5f58321` 保留原样，不改业务源码/开发测试/原候选。第二轮 QA 脚本来自首轮独立 QA 夹具的**独立副本**，只修适配多表 NEEDS_INPUT 无 outputs 的 harness、把 A12 显式接旧报告及新候选版本；不是开发者的自测。
- 包：`dist/wangbin-import-precheck-0.1.4-skill-candidate.zip`，实际 SHA-256 `536763a9c5d64d5b5b53364f5e6e7be93c13457351624b544a0b722b07955d3c`；`zipfile.testzip() = None`，`python -m zipfile -t` exit 0；仅 `wangbin-import-precheck/README.md` (1400 bytes)、`SKILL.md` (5521)、`references/rules.md` (1862)、`scripts/precheck.py` (30251)。ZIP 脚本 SHA `0e634321ebd7a172aab89aaf0cd105f04dd07af0a82a8d0e489cabaae73e9b34` 与干净解压运行脚本及工作树脚本一致；manifest version 0.1.4、成员 SHA/size 与上述相符，工厂 verify exit 0；历史 0.1.2 ZIP SHA `01f919ab6d4dd89ef0c6e934b0a95569b1ec59d7a28b892a283453de5bdde7e3` 未变。包完整性不等于 WorkBuddy 宿主验收。
- 独立回执与全部真实输入/解压产物：`C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa-import-v2-r101/{results.json,security-results.json,extra-results.json}`；测试脚本同 scratch 的 `qa_import_precheck_r101.py`、`qa_import_security_r101.py`、`qa_import_extra_r101.py`、`qa_import_inspect_r101.py`。注意脚本仍放 profile scratch（会定期清理）；此报告保留关键可复验输入和断言。

## 本轮独立业务实测

真实 CSV 核心四行：表头 customer_code/customer_name/region；原行2 `00123,甲客户,R01`，3 `00123,乙客户,R99`，4 `123,丙客户,R02`，5 `00007,,R01`；规则文本编码必填且唯一、name 必填、参考地区 R01/R02，region 必填未明示保留 UNKNOWN。CSV 与 XLSX 两次各 exit 0/PARTIAL、输入4、发现4（行2/3 DUPLICATE_KEY，行3 NOT_IN_REFERENCE，行5 MISSING_REQUIRED_FIELD）、问题记录3、重复组1；`00123` 与 `123` 不合并。源 SHA 前后 `6535ebf0e3904c138b482a7563490ceec245938e6623cfdd5bbbeff75c35c89b` 相同。主报告用 openpyxl 真实重开，五表顺序：检查概览、字段映射、问题明细、变更记录、未检查项；列名对应合同，问题明细4条，变更记录只有表头，所有表均有冻结窗格和筛选范围，无公式单元格。人工 Excel 视觉渲染 NOT_TESTED。

|合同/用例|第二轮回执（执行进程退出码均独立保存）|
|---|---|
|IMP-01/03/04/06/07，A01|CSV/XLSX 均 exit 0，4/4/3/1；文本前导零保留，原件不变、无无授权删除。|
|IMP-02，A02/A03|exit 0/PARTIAL；缺目标说明列 `TARGET_RULES_UNKNOWN`，映射争用列明 `客户名称,名称` 要确认，未默选。|
|IMP-01，A04|exit 0/NEEDS_INPUT，列出 `客户,客户备份`，没有虚构完成报告；**D3 已修**。|
|IMP-05，A05/A06|缺参考 exit 0/PARTIAL、参考成员规则未检查且没有把 R99 判无效；重复参考 R01 exit 0/PARTIAL，`REFERENCE_AMBIGUITY` 明确 `duplicate-ref.csv` 原行2、描述同时列行2/3，不随机选；**D4 已修**。|
|IMP-03，A07/A08|文本 `0`、空、`NULL` 输入 exit 0，只空值触发必填；`03/04/2026` 日期 exit 0/PARTIAL，day/month vs month/day 未检查；XLSX 实数0 与文本 NULL 混合样例 NOT_TESTED。|
|IMP-06，A09|XLSX 长数值编号 exit 0，`TEXT_ENCODING_RISK` 与 `PRECISION_RISK`，不声称复原；数值123显示 `00000` 仍记录数值123、文本风险。|
|IMP-04，A10|两行 country 空、code A，exit 0/PARTIAL，各必填发现，重复组0且两行列未检查比较键。|
|IMP-08，A11|授权分流 exit 0/PARTIAL，候选只含原行4 `123`，隔离行2/3/5 为 `00123,00123,00007`；row_id 无交集、合计4，原件未动；未授权 split exit 2/REJECTED。|
|IMP-09，A12|显式 `--previous-report <A01 旧报告>` + 新参考 R99，exit 0/PARTIAL、发现3/受影响3/重复组1；comparison resolved=1（行3 R99）、continuing=3、new=0，旧/新参考 SHA 与旧报告 SHA 写入五表概览及 JSON，旧报告哈希不变；**D1 已修**。不同源字节旧报告 exit 2/REJECTED，不伪造可比性。|
|IMP-07/08/04，D2|两编码 ` A ` 与 `A`，授权 strip+split 后 exit 0，发现2/受影响2/重复组1，候选0行、隔离2行；相同转换仅 `--candidate` 不分流 exit 2/REJECTED `TRANSFORMED_UNIQUE_COLLISION`；**D2 阻断缺陷已修**。|
|IMP-09，A13/A14|四种公式样式字面值 CSV -> 报告+候选 XLSX exit 0，重开公式单元格0；输入真 Excel 公式 exit 2/REJECTED；相同输入同规则重跑 exit 0，问题类别/行及数量相同，旧运行未覆盖。CSV 格式导出 NOT_TESTED（当前输出仅 XLSX）。|
|边界|坏 XLSX、伪扩展/宏 xlsm、无授权输出 exit 2/REJECTED；来源多工作表和参考多工作表都 exit 0/NEEDS_INPUT，显式参考 sheet 选择后可执行；不一致旧报告拒绝。任意字符串 `--authorization` 被程序当授权输入，CLI 无法自行证明真实用户身份，必须由模型/宿主会话确认并限权。|

### 实际执行命令与退出码

工作目录均为本产品 worktree；下述 `uv` 调起的 QA/安全脚本均**从 ZIP 解压目录**运行产品程序：

- `uv run --no-project --with 'openpyxl>=3.1,<4' python C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/qa_import_precheck_r101.py`：exit 0，17 个场景回执及 17/17 独立断言为 true；早期一次因 harness 误以为 NEEDS_INPUT 必含 outputs 导致 KeyError/exit 1，修正 harness 后重跑，没有放宽业务预期。实际子进程退出码见 results.json。
- 同前运行 `qa_import_security_r101.py`：exit 0，输出包含 D2 的真实发现与候选/隔离回读、坏 XLSX、Excel 公式拒绝及 symlink 探针 NOT_TESTED。脚本退出 0 仅指探针执行完成，不表示其所有探针都业务通过。
- 同前运行 `qa_import_extra_r101.py`：exit 0，参考多表、显式选择、不分流碰撞、异源历史报告与不支持格式回执见 extra-results.json。
- 同前运行 `qa_import_inspect_r101.py`：exit 0，五表列头、行数、旧新 diff 原文、候选和隔离表结构、zip 成员及脚本一致性现场打印核查。
- `uv run --no-project --with 'openpyxl>=3.1,<4' --with pytest --with pyyaml python -m pytest -q --tb=short --basetemp C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/import-precheck-r101-regression tests/test_import_precheck.py`：exit 0，20 passed；这是受影响旧能力回归的补证，不替代上列独立 QA。`python -m tooling.products validate --id wangbin-import-precheck` exit 0/PASS；`python -m tooling.products verify --id wangbin-import-precheck` exit 0/PASS；`sha256sum ...` 与 `python -m zipfile -t ...` exit 0。

## 对话、授权与残余风险

权威 V2 §14.9 三条中文和三条英文提问与 `SKILL.md` 的 examples_zh/en 静态字面逐条一致（静态文案 PASS）；推荐1绑定完整预检、推荐2绑定参考表、推荐3须前置确认映射并明确授权，不可单独评估为连续对话 PASS。真实模型调用、多轮补资料/追问、自然语言直接抽取业务规则、WorkBuddy 宿主安装及平台评测 **NOT_TESTED**，不能用 CLI 内部 JSON 夹具或静态对话场景冒充。openpyxl/et_xmlfile 非 ZIP 内置，宿主依赖可用性未知。symlink 探针因 Windows WinError 1314 无创建权限 **NOT_TESTED**；超 20 MiB/5万行边界、大压缩炸弹、输出路径越界、外链、CSV 导出公式防护、人工视觉审查 NOT_TESTED，不能推定安全全部覆盖。产品专属 LICENSE、资源权利与平台商业许可无证据，**发布 BLOCKED**；没有 push、merge、上传、部署或平台登录。本次本地已执行范围 PASS，仅放行后续 T04 对候选和评测材料做复核，不代表发布门禁解除。
