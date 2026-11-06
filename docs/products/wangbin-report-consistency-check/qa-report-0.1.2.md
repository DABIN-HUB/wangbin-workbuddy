# Q05 T03 独立 QA：0.1.2 候选 **FAIL**

- product_id: `wangbin-report-consistency-check`; task_id: `t_8a2a459d`; workspace: `F:/ideaWorkSpace/wangbin-workbuddy-report-consistency-check`; branch: `skill/report-consistency-check`; base_commit: `d874e90a0dc02610fb13afa41e64ccc9579e3404`; tested developer commit: `64a3157def5c8bb6beff0c6cd48e1b83a247e1b4`。独立报告 commit 见本报告所附提交；业务源码、旧 ZIP 和原件均不改。
- 候选：`dist/wangbin-report-consistency-check-0.1.2-skill-candidate.zip`; SHA-256 `4bf56c5786343c65c38dfa1aa4ecfde722bac861e7574432d8881d005457f0f8`。sidecar/manifest 同值；`ZipFile.testzip() is None`，四个成员与 manifest 各字节哈希、原始源码各字节哈希一致。解压至 wb-quality profile scratch 新目录后仅执行其中 `scripts/check_report.py`。manifest 版本 0.1.2、scope `local archive integrity only`，不代表平台成功。
- 验证命令（工作目录为上述 workspace）：`uv run --no-project --with openpyxl --with python-docx python docs/products/wangbin-report-consistency-check/qa_independent_probe.py` → exit 0（探针自身完成，不表示产品 PASS）；每个实际 CLI 子进程的 exit/stdout/stderr、输入、五表逐格输出及预期见 `qa-evidence-0.1.2.json`。`python -m tooling.products verify --id wangbin-report-consistency-check` → exit 0 / PASS，只代表工厂完整性。全部 31 次独立探针：27 次 CLI exit 0、4 次 exit 2；27 个可重开的 XLSX 均恰有五表 `核查概览/指标对应/差异明细/待确认口径/未覆盖项`，未出现可执行输出公式，31 次输入源件 hash 均未被本次调用修改。数值由虚构 XLSX 数值格及 DOCX 正文/普通表格独立构造；未复用开发自测预期。

## 阻断缺陷 D1：确认规则跨币种求和却判 MATCH（高优先）

复现：使用 `qa_independent_probe.py` 中 `REP-X02-cross-currency`，XLSX `数据!A1=收入/CNY/元, A2=100; B1=收入/USD/元, B2=100`，DOCX 段落1“收入200元人民币”，context `{"rules":{"收入":{"op":"sum","cells":["数据!A2","数据!B2"],"unit":"元"}},"exact":true}`。命令为证据 JSON 中解压路径的 `python scripts/check_report.py --input-root <case>/in --source-xlsx <case>/in/source.xlsx --report-docx <case>/in/report.docx --output-dir <case>/out --context <case>/in/context.json`。预期：币种 CNY 与 USD 不可直接求和；NOT_COMPARABLE/明确拒绝且差额未计算，绝不可宣称已核实。实际 CLI exit 0；差异明细记录 `数据!A2,数据!B2`、`INDEPENDENT_RULE_RESULT`、来源比较值 200、报告 200、`MATCH`、差额 `0元`，只记录首个来源币种 CNY。违反 REP-02/04、输入输出契约 §判定2–3，产生虚假的跨币种已核实结论。对照相同构造把 USD 放在第一格时会返回 NOT_COMPARABLE，说明是首操作数决定结果而非所有操作数验证。需修复所有参与运算币种/主体/期间/税/实际预算和量纲相容性，并重产不可覆盖新版 ZIP，独立 QA 重测旧回归和新缺陷。

## 缺陷 D2：伪造 .xlsx 返回损坏码（次优先，合约失败）

复现 `ERR-spoofed`：有效 docx，`source.xlsx` 实际字节 `not xlsx`。预期 contract §错误/有限模式 `UNSUPPORTED_OR_SPOOFED`，exit 非0，无成功输出。实际 exit 2，无输出，但 stderr 为 `{"error":"UNREADABLE_OR_ENCRYPTED","message":"cannot read OOXML container"}`。须与损坏或加密 OOXML 分类区分；`ERR-bad-docx` 损坏文档返回 UNREADABLE_OR_ENCRYPTED 符合预期。

## 逐案结果摘要（逐格证据 JSON 保留实际与独立期望）

| 用例 | 实际关键结果与判定 |
|---|---|
| CORE-A/B/C/D | A MATCH 0；B MISMATCH -30000元；C 2.00pp 与相对20.0%；D 显示舍入 MATCH 但原始差额 +500元，均符合预期。 |
| REP-A05/A06/A07/A08 | 累计≠本月、预算≠实际、USD≠CNY 各 NOT_COMPARABLE 且差额留空；不明“本公司”双候选 AMBIGUOUS_MAPPING，符合。 |
| REP-A09 两种、A10 | ZERO_DENOMINATOR、MISSING_OPERAND、UNVERIFIED_FORMULA_CACHE 各自阻断并空差额，符合。 |
| REP-A11/A12/A13/A14/A15/A16 | 双位置 MATCH 与 -10000 MISMATCH；无规则 +500 仅 RAW_DIFFERENCE_ROUNDING_PENDING；双候选后指定 C2 才 MATCH；正文 MATCH、实际内嵌图片未覆盖；章节号不当指标；A16 -30000，符合。A13 的确认是独立同值 fixture，非同一重传快照；确认前后状态来源可见，真正同文件多轮映射转变 NOT_TESTED。 |
| REP-X01/X02/X03 | 三格求和130 MATCH、非数值阻断；净额75与占比25%两条 MATCH；同报告源90k→100k→80k：MISMATCH +10000→MATCH RESOLVED→MISMATCH +20000 NEW，符合。跨币种规则额外子例 FAIL D1。 |
| REP-X05/X06 | 不可信 `=HYPERLINK`/`+cmd` 文字输出无公式；限制超过 40000 格返回 RESOURCE_LIMIT exit 2；阈值内常规小表 PASS。未观察外网行为仅确认未主动网络调用路径；网络监测 NOT_TESTED。 |
| ERR-missing/spoofed/bad-docx | 缺源 INPUT_MISSING；伪装 D2；损坏 DOCX UNREADABLE_OR_ENCRYPTED；各无成功 XLSX。 |

静态核对：`SKILL.md` 中英各三条推荐问法与 `requirements.md` §输出、对话逐字相同；CLI 参数 `--input-root/--source-xlsx/--report-docx/--output-dir/--context/--prior-run` 与 contract 必需/可选语义吻合。真实 Skill 自然语言入口/六问实际对话 NOT_TESTED，不能把静态检查/CLI 等同模型成功。未测试加密文档、symlink 越界（Windows 创建 symlink WinError 1314）、输出目录权限/逃逸、ZIP 膨胀/极限性能和多币种跨期间组合。许可证/依赖权利、产品相似性人工审查、WorkBuddy 运行/审核/上架及发布均 NOT_TESTED。**本地 QA FAIL，禁止 T04 将本候选视为 QA-PASS，未 push/上传/发布。**
