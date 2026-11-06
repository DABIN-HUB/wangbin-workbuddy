# Q06 T04 本地候选复核（不等于发布批准）

- product_id=`wangbin-tender-analyzer`; task_id=`t_22fbfa72`; workspace=`F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`; branch=`skill/tender-response-check`; base_commit=`fa0ab70690de9c70a18532482161d27908c368eb`; result_commit=以本文件的本地提交及 Kanban handoff 为准。
- 仅对独立 QA `t_5e507d47` 已判 **LOCAL_PASS 43/43** 的精确 0.2.3 ZIP 做复核：`dist/wangbin-tender-analyzer-0.2.3-skill-candidate.zip`，SHA-256 `5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce`；QA 报告及逐案证据见 `qa-0.2.3-report.md`/`qa-0.2.3-evidence.json`，QA commit `fa0ab70690de9c70a18532482161d27908c368eb`。本轮不修改 ZIP、源、manifest、sidecar 或 catalog。

## 实际执行（工作树根目录，命令退出码）

| 命令 | exit | 现场结果 |
|---|---:|---|
| `git status --short; git branch --show-current; git rev-parse HEAD; git worktree list --porcelain` | 0 | 写前工作树干净、指定产品分支和 QA HEAD；受保护 `wangbin-workbuddy-dev` 仅识别 worktree 登记，未读取其业务内容 |
| `sha256sum dist/wangbin-tender-analyzer-0.2.{0,1,2,3}-skill-candidate.zip` | 0 | 四个文件实际哈希分别为下表值 |
| `uv run --with openpyxl python -m tooling.products validate --id wangbin-tender-analyzer && uv run --with openpyxl python -m tooling.products verify --id wangbin-tender-analyzer` | 0 | validate PASS，verify PASS，SHA 与 QA 精确值相同；未调用 package 以免重写冻结包 |
| `uv run --no-project --with openpyxl --python .venv/Scripts/python.exe python docs/products/wangbin-tender-analyzer/qa_0_2_3_independent_probe.py` | 0 | 从清洁解压执行 QA 探针 **43/43 PASS**，覆盖 A02–A14/错误输入及旧 CLI。重跑后原 QA 证据 `git diff` 为空；探针的测试输入/逐案命令与重开结果见已提交的 evidence JSON |
| `uv run --no-project --with openpyxl --python .venv/Scripts/python.exe python C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/tender-t04-verify.py` | 0 | T04 临时只读审计：四版各 11 个成员，CRC、sidecar、manifest、catalog 的 hash/version 一致；0.2.3 的 11 个成员另与当前源逐字节匹配；解压后独立实跑 TXT+CSV 与 MD+XLSX 的 check，以及 MD 的 prepare；五表 XLSX 重开、MD 和 A04 冲突证书行均 PASS；旧入口的 JSON 与旧 fixture 精确一致。临时探针与虚构输入/输出均仅在本 profile scratch 下，不提交业务载荷 |

| 已留存的版本 | 实际 ZIP SHA-256 | 本地业务 QA 资格 |
|---|---|---|
| 0.2.0 | `e442b3c06c014dc957e73a5a892a23a4c8a009a6394e5da18ea890253fdc52dd` | 保留，非本轮放行包 |
| 0.2.1 | `1b2d07f43da301a3d78cf1a996a5f9987920b16000271f326608ea10d33255dc` | **FAIL** D1；证书年份冲突被误标“不适用”，原 QA 证据不撤销 |
| 0.2.2 | `42c3abdb1b757dc2ae937e143a31b0579f088ab406958107107f5b65550178e2` | **FAIL** D2；MD 遗漏证书真实行，原 QA 证据不撤销 |
| 0.2.3 | `5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce` | **LOCAL QA PASS** 43/43，且本次 T04 再核，仅此精确 SHA |

历史 catalog 仍登记 0.1.0 (`2e68809033301c97b02ec7c7fd59f7b477fcd2f1f86d515d69b5fc7b20146bc7`)；但本产品工作树中**没有该物理 ZIP**，其实际哈希、sidecar 与物理保全一律 **NOT_TESTED/NOT_VERIFIED**。旧入口 `analyze_tender.py` 与原 expected JSON 在 0.2.3 的解压包内实跑一致，不等同于 0.1.0 物理包检查。

0.2.3 catalog `active_version=0.2.3`、各候选记录和非平台状态未提升；ZIP 内 SKILL 有 `display_name_en`、中英双语说明与各三条静态示例及明确版本和本地 CLI 路由边界。六条提示文本存在 **不等于** WorkBuddy 自然语言路由验证。T04 另用虚构材料核验 TXT/MD、CSV/XLSX，响应引用 certificate.txt:1（文本有效至 2026）与要求 2027 冲突，XLSX 正确为“已提供（可读文本）/不支持（文本层面）”，MD 同时引用 response:1 与 certificate:1；准备模式标“响应未核查”。

**结论：0.2.3 精确 ZIP 仅本地候选复核通过；未 push、上传或发布。** blocked_reason=null。残余风险：中文语义、年份启发式及歧义/重号需人工复核；证书真伪、授权与权利/许可、人工相似性均未证实；Windows symlink 测试跳过；WorkBuddy 平台安装/运行、自然对话/模型路由 **NOT_TESTED**，不能推出平台试用或发布门禁 PASS。T05 须独立核对提交后源和 ZIP 是否仍未变化。
