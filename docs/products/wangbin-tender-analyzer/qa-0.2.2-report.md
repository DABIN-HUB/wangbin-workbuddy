# Q06 T03-RERUN-1 独立 QA：0.2.2 候选 FAIL（D2：MD 缺证书证据位置）

- product_id=`wangbin-tender-analyzer`；task_id=`t_5e507d47`；workspace=`F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch=`skill/tender-response-check`；base_commit/tested_commit=`6c08aaa7bea8662b62ca46c60d7c0ce61bb7cec9`。
- 精确新候选 `dist/wangbin-tender-analyzer-0.2.2-skill-candidate.zip`：SHA-256 `42c3abdb1b757dc2ae937e143a31b0579f088ab406958107107f5b65550178e2`；`ZipFile.testzip() is None`，11 个不同安全成员、每项 manifest SHA/大小、源文件字节、sidecar、catalog 0.2.2 均匹配。旧 0.2.1 ZIP SHA `1b2d07f43da301a3d78cf1a996a5f9987920b16000271f326608ea10d33255dc` 保留；0.2.0 SHA `e442b3c06c014dc957e73a5a892a23a4c8a009a6394e5da18ea890253fdc52dd`。0.1.0 物理 ZIP 本工作树未见，完整性 NOT_TESTED。
- 新 QA 探针 `qa_0_2_2_independent_probe.py` 从新 ZIP 每次清洁解压、运行解压后的 CLI、重开五表 XLSX、读取 MD；独立断言 **40/41 PASS，1 FAIL**。旧 `qa_independent_probe.py` 和 `qa-0.2.1-*` FAIL 证据未改。输入、逐案命令（`<QA_SCRATCH>` 占位符）、预期、真实单元格、MD、退出码见 `qa-0.2.2-evidence.json`。探针本身 exit **1** 是 QA 判定失败，并非 CLI 崩溃。

## D2 阻断：A04 MD 未列出实际证书行号

复现：从上述新 ZIP 解压运行 `python <extract>/wangbin-tender-analyzer/scripts/check_response.py --tender <QA_SCRATCH>/a04/tender.txt --response <QA_SCRATCH>/a04/response.txt --evidence-file <QA_SCRATCH>/a04/certificate.txt --output-dir <QA_SCRATCH>/a04`。虚构输入 UTF-8：

```text
tender.txt:1      4. 提供有效期覆盖2027年的资质证明。
response.txt:1    4. 资质有效期覆盖2027年，见 certificate.txt。
certificate.txt:1 本证明有效期至2026年12月31日。
```

预期：冻结 `acceptance-cases.md` BID-A04、`input-output-contract.md` 对 MD 的追溯要求——输出须列 `response.txt:1` 与 `certificate.txt:1` 对照，四维附件已提供、内容不支持，且不能宣称证书真实性。实际 CLI exit **0**，创建 XLSX/MD：`要求响应矩阵` `唯一ID=1:1:4` 的 `响应位置=response.txt:1`、`证据位置=certificate.txt:1`、`附件实际提供状态=已提供（可读文本）`、`内容支持状态=不支持（文本层面）`；`附件核对` 行含 `certificate.txt:1`——**上一轮 D1 修复已在 XLSX 中奏效**。但 MD 三条有关 `1:1:4` 的清单只写 `tender.txt:1；响应 response.txt:1` 和四维状态/“实际材料内容与声明矛盾或未支持；需人工核验”，**全文未见 `certificate.txt:1`**。人工仅看提交前 MD 无法定位实际冲突证书，冻结的跨文件证据对照未满足。应保留既有 XLSX 状态和行号，在 MD 对应缺口/待核实条目列真实证书来源行；不得编造或凭目录宣称真伪。具体逐案原文在 JSON 的 `A04_conflicting_certificate` 和失败项 `A04_MD_and_provenance`。

额外反例 `A04_no_cross_requirement_leak`：两条要求、响应只指第1条时，两个矩阵行均标附件/内容`待确认`，未错误跨编号断言第2条“已提供”；PASS（保留歧义而非证明材料不相关）。CORE 目录仅登记不等于实际提供、A02/A03/A05–A09/A11/A14、重号、无正式关系补遗、CSV/XLSX、准备模式、编码/PDF/损坏 XLSX/路径逃逸错误码、注入公式以及旧 CLI JSON 精确样例/exit2 均 PASS。正常业务 CLI exit 0，错误 CLI exit 2；五表 `核查概览/要求响应矩阵/附件核对/补遗与版本/待确认事项` 已逐案重开；具体单元格与 MD 见 JSON。旧 0.2.1 业务 FAIL 保持历史原样，不重释为通过。

## 实际执行与门禁

| 命令 | exit | 结果 |
|---|---:|---|
| `uv run --no-project --with openpyxl --python .venv/Scripts/python.exe python -c '<ZipFile/manifest/sidecar/catalog/源字节独立检查>'` | 0 | SHA 如上；CRC None；11 成员；源字节 PASS |
| `uv run --no-project --with openpyxl --python .venv/Scripts/python.exe python docs/products/wangbin-tender-analyzer/qa_0_2_2_independent_probe.py` | 1 | 41 项中 40 PASS，`A04_MD_and_provenance` FAIL；干净解压 |
| `uv run --with pytest --with openpyxl python -m pytest -q tests/test_tender_analyzer.py tests/test_tender_bid_response.py tests/test_tender_evidence_linkage.py` | 0 | 28 passed / 1 skipped（Windows symlink 不可建） |
| `uv run --with openpyxl python -m tooling.products validate --id wangbin-tender-analyzer` | 0 | 结构 PASS，不等于业务 PASS |
| `uv run --with openpyxl python -m tooling.products verify --id wangbin-tender-analyzer` | 0 | 归档完整性 PASS，不等于业务 PASS |
| `sha256sum dist/wangbin-tender-analyzer-0.2.{0,1,2}-skill-candidate.zip` | 0 | 三包哈希如上，旧版未覆盖 |

**LOCAL_QA_FAIL，禁止 T04 按 0.2.2 QA-PASS 流转。** 仅允许最多下一轮开发修复新版本不可覆盖 ZIP 后再次独立 QA；本轮不改业务源码、候选和旧失败证据，不 push/上传/发布。风险：中文语义/年份启发式及证明真伪未认证，重复编号/歧义需人工核对；Windows symlink 跳过；历史 0.1.0 ZIP 物理校验 NOT_TESTED；WorkBuddy 平台运行、自然语言六问模型路由、许可/权利、人工相似性 NOT_TESTED。
