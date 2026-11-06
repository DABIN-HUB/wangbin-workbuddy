# Q06 T03-RERUN-1 独立复验：0.2.3 本地 QA PASS

- product_id=`wangbin-tender-analyzer`；task_id=`t_5e507d47`；workspace=`F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch=`skill/tender-response-check`；base_commit/tested_commit=`27b14faf57a77e20ffdf68034f0f028004c49d2a`；result_commit=见本报告提交后的 Kanban handoff。
- 不可覆盖候选 `dist/wangbin-tender-analyzer-0.2.3-skill-candidate.zip`，SHA-256 `5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce`。sidecar/manifest 同值，版本及 catalog 登记为 0.2.3；ZipFile.testzip() 返回 None；11 个不重复、无路径穿越成员，成员 SHA/大小及源文件逐字节比对 11/11 PASS。清洁解压而非调用工作树业务脚本；仅新增 QA 所有探针、JSON 逐案证据及本报告。旧 0.2.1/0.2.2 FAIL 报告与证据不改；实测旧 0.2.0/0.2.1/0.2.2 ZIP SHA 分别为 `e442b3c06c014dc957e73a5a892a23a4c8a009a6394e5da18ea890253fdc52dd`、`1b2d07f43da301a3d78cf1a996a5f9987920b16000271f326608ea10d33255dc`、`42c3abdb1b757dc2ae937e143a31b0579f088ab406958107107f5b65550178e2`；历史 0.1.0 物理 ZIP NOT_TESTED。

## 实际命令、退出码和业务结果

| 命令 | exit | 结果 |
|---|---:|---|
| `sha256sum dist/wangbin-tender-analyzer-0.2.{0,1,2,3}-skill-candidate.zip` | 0 | 四包 SHA 如上；历史包未覆盖 |
| `uv run --no-project --with openpyxl --python .venv/Scripts/python.exe python docs/products/wangbin-tender-analyzer/qa_0_2_3_independent_probe.py` | 0 | **43/43 PASS**；CRC、成员、源字节、catalog、干净解压 CLI、五表/MD、错误输入与旧 CLI；逐案输入/命令/实际值见 `qa-0.2.3-evidence.json` |
| `uv run --with pytest --with openpyxl python -m pytest -q tests/test_tender_analyzer.py tests/test_tender_bid_response.py tests/test_tender_evidence_linkage.py` | 0 | 28 passed / 1 skipped（Windows symlink 不可创建），只是附加开发测试，非独立业务证明 |
| `uv run --with openpyxl python -m tooling.products validate --id wangbin-tender-analyzer && uv run --with openpyxl python -m tooling.products verify --id wangbin-tender-analyzer` | 0 | 两段均返回 PASS；verify SHA 与上值一致；归档验证不代替业务 QA |

BID-A04 虚构 UTF-8 输入：`tender.txt:1` 为 `4. 提供有效期覆盖2027年的资质证明。`，`response.txt:1` 为 `4. 资质有效期覆盖2027年，见 certificate.txt。`，`certificate.txt:1` 为 `本证明有效期至2026年12月31日。`。从解压目录运行 `python <QA_SCRATCH>/extract/wangbin-tender-analyzer/scripts/check_response.py --tender <QA_SCRATCH>/a04/tender.txt --output-dir <QA_SCRATCH>/a04 --response <QA_SCRATCH>/a04/response.txt --evidence-file <QA_SCRATCH>/a04/certificate.txt`，实际 exit 0。重新打开 XLSX `要求响应矩阵` 得 `唯一ID=1:1:4`、`响应位置=response.txt:1`、`证据位置=certificate.txt:1`、四维 `已定位 / 可能不充分 / 已提供（可读文本） / 不支持（文本层面）`；`附件核对` 一行 `certificate.txt`、`certificate.txt:1`、`已提供（可读文本）`、`不支持（文本层面）`。MD 的三条 `1:1:4` 清单均有 `响应 response.txt:1；材料 certificate.txt:1`、四维状态及人工核验提示；修复先前 D2 缺行证据。该文本冲突不是证书真实性认证。跨编号反例两条均保守 `待确认`，未擅自把证书应用第二要求。

CORE 仅登记 CSV 附件时实际四维中 `附件实际提供状态=仅目录登记`、`内容支持状态=未核验`、`条件覆盖状态=可能不充分`，未冒充实物；A11 未取得资质文本不误判支持。冻结 A02–A14（包括 A05 正式补遗、A06 冲突、A07 重编号、A08 关键词误命中、A09 准备/核查、A14 不编造）与重复编号、非正式替换、XLSX/CSV、矩阵与概览计数、MD 同步检查通过；检查模式缺响应 exit 2 `MISSING_RESPONSE`；无效 UTF-8、PDF、损坏 XLSX、路径逃逸分别 exit 2 并有 `INVALID_UTF8`、`INPUT_TYPE_UNSUPPORTED`、`CATALOG_READ_FAILED`、`OUTPUT_PATH_INVALID`，公式注入未生成公式单元格。解压后旧 `analyze_tender.py` 对原样例 exit 0 JSON 与 expected 完全一致、缺文件 exit 2 `INPUT_NOT_FOUND`。正常成功均从真实 XLSX 五表重开；逐案详细证据见 JSON。

**结论：仅 0.2.3 精确 SHA 的本地独立 QA PASS，可交 T04 做本地候选复核；旧 0.2.1/0.2.2 FAIL 不撤销。** blocked_reason=null。残余风险：中文语义/年份启发式误判或漏判、重复编号/歧义需人工复核、证书真伪未证实；Windows symlink 测试跳过；0.1.0 物理 ZIP 未见故 NOT_TESTED；WorkBuddy 平台运行/自然对话与模型路由/许可权利/人工相似性均 NOT_TESTED。无 push、上传、发布。
