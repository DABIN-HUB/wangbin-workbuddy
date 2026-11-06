# Q06 T03 独立 QA：0.2.1 候选 FAIL

- product_id: `wangbin-tender-analyzer`；task_id: `t_cec0dcc0`；workspace: `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch: `skill/tender-response-check`。
- tested commit/base_commit: `d62d4193870fca5ac77e431be4e3c78a68b95537`；tested ZIP: `dist/wangbin-tender-analyzer-0.2.1-skill-candidate.zip`；SHA-256 `1b2d07f43da301a3d78cf1a996a5f9987920b16000271f326608ea10d33255dc`。未改候选。
- 独立从该 ZIP 清洁解压，直接运行解压脚本，重开 XLSX 五表并读 MD；`qa_independent_probe.py` 39 个断言，38 PASS / 1 FAIL。ZIP CRC、11 项成员哈希/大小/源码字节、sidecar、manifest 一致。源侧 24 passed/1 skipped 不替代 ZIP 业务验收。

## D1 阻断：A04 实际证书的内容矛盾未进入附件维度

重现（在 `qa_independent_probe.py` 的 `a04` 独立夹具中生成下列 UTF-8 文件，`<QA_SCRATCH>` 表示临时目录；使用 ZIP 解压脚本）：

```text
tender.txt:1   4. 提供有效期覆盖2027年的资质证明。
response.txt:1 4. 资质有效期覆盖2027年，见 certificate.txt。
certificate.txt:1 本证明有效期至2026年12月31日。
```

命令：`python <解压目录>/wangbin-tender-analyzer/scripts/check_response.py --tender <QA_SCRATCH>/a04/tender.txt --response <QA_SCRATCH>/a04/response.txt --evidence-file <QA_SCRATCH>/a04/certificate.txt --output-dir <QA_SCRATCH>/a04`。CLI 实际 exit **0**、两文件创建；XLSX `要求响应矩阵` ID `1:1:4` 的「附件实际提供状态」=`不适用`、「内容支持状态」=`不适用`、「支持材料/证据位置」为空，`附件核对`无行；MD 同样写两项 `不适用`。预期按 BID-A04/冻结合同 §四维：已显式提供的 `certificate.txt` 有可读内容，至少应建立与第4条响应证据的受控关联，附件=`已提供（可读文本）`、内容=`不支持（文本层面）`，证据应指 `response.txt:1` 与 `certificate.txt:1`；若文本关联身份不能安全确定，必须列出候选并标 `待确认`，不得无解释断言不适用。附件源与响应源已经明确指定，证书年份明确冲突，不可认证证书真假。源码仅 `r['materials']`（招标原句中 `.txt/.md` 名）及目录编号匹配实际附件，不读响应原句中 `certificate.txt` 的身份关联，详见 `scripts/check_response.py` 218–235 行。另需要确保修复不会把任意响应文件名自动确认为某条要求的证据：须限定关联并保留歧义。

精确逐案输入、命令、预期/实际单元格与 MD 摘录见 `qa-0.2.1-evidence.json` 的 `A04_conflicting_certificate`；从仓库根目录运行 `uv run --no-project --with openpyxl --python .venv/Scripts/python.exe python docs/products/wangbin-tender-analyzer/qa_independent_probe.py` 可复现，退出码 **1**（QA 断言失败，非脚本错误）。修复需升版本生成不可覆盖新 ZIP，保留原失败包和独立证据，新 QA 重新从干净解压验证，切勿直接改 QA 预期。

## 覆盖和边界

实际独立测试：§19.7/CORE；BID-A02–A11（A10 的编码/PDF/损坏清单，A11 附件新增）、A14；BID-A12（旧 CLI 完整样例 JSON 与 expected 精确相等、旧 INPUT_NOT_FOUND exit 2）；BID-A13 的统计与 MD 状态一致性；重号 ID；无证明的“最终版”不替换；CSV/XLSX 清单、五表顺序、公式单元格；`../` 项目名错误；ZIP 完整性。A04 失败，故整体 FAIL。`uv run --with pytest --with openpyxl python -m pytest -q tests/test_tender_analyzer.py tests/test_tender_bid_response.py` exit 0：24 passed、1 skipped（Windows symlink 不能创建）；`uv run --with openpyxl python -m tooling.products validate --id wangbin-tender-analyzer` exit 0 PASS；同环境 `verify` exit 0 PASS，均非独立业务验收替代。错误样例均 CLI exit 2、稳定码且 stderr 不含私有绝对路径；实际 XLSX 仅探测 formula cells，未宣称已审计所有可嵌入外链格式。

六句推荐中文/英文在 SKILL.md 与冻结 requirements.md 静态字面核对；**自然语言模型路由、WorkBuddy 平台运行、许可权利与人工相似性未测试**；similarity-check 的开发结果 `REVIEW_REQUIRED` 不是通过。对补遗正式性、纯文本证明内容关联、中文改写误报/漏报仍有启发式残余风险，实际证书真伪不属于本地工具能力。历史 0.1.0 ZIP 本工作树无物理文件，**旧物理 ZIP 未核验**；0.2.0 保留但本次没有业务复验。新 0.2.1 中旧 CLI 回归与上述旧 pytest 已实跑。输出临时夹具运行完清理，仅独立报告、探针与 JSON 证据入库；未 push、上传或发布。

## 验证命令/结果

| 命令 | exit | 实际 |
|---|---:|---|
| `uv run --no-project --with openpyxl --python .venv/Scripts/python.exe python docs/products/wangbin-tender-analyzer/qa_independent_probe.py` | 1 | 39 项 38/39，A04 FAIL；包括干净解压/逐单元格重开及旧 CLI |
| `uv run --with pytest --with openpyxl python -m pytest -q tests/test_tender_analyzer.py tests/test_tender_bid_response.py` | 0 | 24 passed/1 skipped |
| `uv run --with openpyxl python -m tooling.products validate --id wangbin-tender-analyzer` | 0 | 工厂结构 PASS |
| `uv run --with openpyxl python -m tooling.products verify --id wangbin-tender-analyzer` | 0 | 本地包完整性 PASS |

blocked_reason: D1 阻断当前 0.2.1 本地业务 QA；T04 不得将该包当 QA-PASS。result_commit/QA 变更文件见本任务交付元数据。残余风险及 NOT_TESTED 如上。
