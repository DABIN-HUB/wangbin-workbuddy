# AUDIT-R1 Q06 B：旧 0.2.3 精确 ZIP 独立基线（阻断旧版业务放行）

- product_id `wangbin-tender-analyzer`；task_id `t_f728459a`；branch `skill/tender-response-check`；执行前 HEAD `3ab9869eaab792e03ac9360913596cc4988465a3`，工作树干净。原 V2 附件19 §19.3–19.9 对应本树 `requirements.md` BID-01–08 和 `input-output-contract.md`；增补需求为本轮用户文件 §11 BID-F01–F05，§12–20。旧 0.1.0 ZIP 物理原件依然 `NOT_VERIFIED`。
- **冻结原包**：`dist/wangbin-tender-analyzer-0.2.3-skill-candidate.zip`，SHA-256 `5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce`；`python -m zipfile -t` exit 0 (`Done testing`)，成员 11 个、无重复/越界路径，成员 SHA-256 见逐案 JSON。ZIP 从未修改。
- **执行层级**：L3，从 ZIP 解压到 `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06-old-023-t_f728459a-v5/unpacked`；`.venv/Scripts/python.exe docs/products/wangbin-tender-analyzer/qa-audit-r1-old-023-probe.py` exit 0；探针清除 `PYTHONPATH`，调用解压包脚本 `scripts/check_response.py` / `scripts/analyze_tender.py`，实际 TXT/MD、CSV、XLSX 目录，逐例重开五表 XLSX 和 Markdown。可复跑的完整参数数组、每例 stdout/stderr/exit、输入输出 SHA、**五个表的全部单元格**和 MD 全文：同 scratch 的 `results.json`。其哈希指的是运行中的实际文件而不是手造预期。17 个正式 CLI 均 exit 0；其中 16 个检查模式文件案例、1 个旧 JSON 入口案例，另有包内原样例快照复查。正式 CLI exit 0 仅表示文件生成成功，**不表示业务通过**。命令执行过程中探针第一版在 XLSX 目录 fixture 类型判断发生 `TypeError`，修正仅探针 `tuple/list` 判断后从新的干净解压目录完整重跑；早期 v2/v3/v4 探针输出不作最终证据。

## 逐案输入、独立预期与实际（下列每行源文件均在 `cases/<case>/`，要求 `requirement.txt:1`、响应 `reply.md:1`；每例同名 `result/*.xlsx|*.md`）

| BID | case / 核心输入（省略每行编号1） | 独立预期 | 旧 ZIP 实际 / 判定 |
|---|---|---|---|
| F01 | `date_expired_2028`：要求有效期覆盖 2028-01-01..2028-12-31；响应宣称覆盖；CSV目录 + certificate.txt:1 仅到 2027-12-31 | 材料截止不足，内容不支持、缺口不可为空 | `已提供 / 待确认`，缺口空、清单“已覆盖”；**FAIL**，未识别明确过期 |
| F01 | `date_signed_valid`：要求覆盖 2027 全年，证书签发2026年且有效期2026-06-01..2028-12-31 | 有效期覆盖，不能把签发年当作矛盾 | `不支持（文本层面）`、伪冲突缺口；**FAIL** |
| F01 | `date_issue_only`：仅签发日期2026-06-01，不给有效期限，要求覆盖2027 | 有效性未知，须说明缺失有效期，不能由签发年断言不支持 | `不支持（文本层面）`；**FAIL** |
| F01 | `date_two_certs`：甲类到2027-12-31、乙类到2030-12-31，要求甲类覆盖2028 | 甲类不足，乙类不得替代 | `待确认`且缺口为空；**FAIL**（无对象关联及到期解释；没有声称其选择乙类） |
| F01 | `date_shift_2032`：要求2032全年、证书到2031年末 | 同结构不能支持；不得固定年份 | `待确认`、缺口空；**FAIL** |
| F02 | `response_negated`：必须支持自动备份 / 我方**不支持**自动备份 | 回应已定位但明确冲突，覆盖不得通过 | `已覆盖（文本层面）`、缺口空；MD“已覆盖范围”；**FAIL** |
| F02 | `response_positive`：必须支持 / 我方支持自动备份 | 文本覆盖 | `已覆盖（文本层面）`；**PASS（仅此文本维度）** |
| F02 | `response_double_negative`：不使用外部云存储 / 本方案不使用外部云存储 | 相同禁止语义，不应误判冲突 | `已覆盖（文本层面）`；**PASS（仅此文本维度）** |
| F02 | `response_conditional`：必须支持自动备份 / 若另行采购模块才支持 | 不可无条件认定满足 | `已覆盖（文本层面）`、缺口空；**FAIL** |
| F03 | `license_missing`：必须提供营业执照 / 我方提供营业执照，未给目录/材料/文件名 | 明确材料义务；限本次资料未找到，附件不能“不适用” | `不适用 / 不适用`、无缺口；**FAIL** |
| F03 | `license_catalog_csv`, `license_catalog_xlsx`：同要求，目录登记营业执照.txt，未提交实际文件 | 仅目录，不是实物，不支持内容 | 两格式均 `仅目录登记 / 未核验` 并给缺口；**PASS（仅此维度）** |
| F03 | `license_actual`：同要求 + 目录及营业执照.txt 文本“营业执照：统一社会信用代码为虚构示例” | 可读材料应认定已提供；具体法律真实性不能认证 | `已提供 / 支持（文本层面）`，仅**有限文本关联 PASS**；内容不足以证明证照真实有效，且实现只凭词语共现，不可推广 |
| F03 | `license_duplicate`：目录两条同名 + 单份实际文本 | 歧义须保留 | `待确认 / 待确认`；**PASS** |
| F04 | `filename_only`：要求提供 certificate.txt、实际文本没有证书信息且无目录 | 不应以文件名/词语当作证明 | `待确认 / 未核验`；**未完整复现 all([])**（关联歧义使该路径未进入材料内容比对） |
| F04 | `filename_empty_conditions`：同名目录明确编号 + 实际文本 `certificate.txt：仅为目录占位，不含证书` | 文件虽然可读，却明确不含证书，内容不得支持、应指出缺口 | `已提供 / 支持（文本层面）`、缺口空、MD列“已覆盖”；**FAIL**。该例目录提供唯一关联以进入内容路径；`MATERIAL` 过滤条件后 `all([])` 为真；相关性仅同名 token |
| F05 | `legacy_json`：旧 `--input`，虚构两条招标规则 | JSON 可解析、退出0，保留单文件入口 | exit0、JSON 可解析；**PASS（入口层面）** |
| F05 | 原包附带 `examples/fictional-tender.txt` 对原包附带 expected JSON | 原样保持正确的既有快照，不由实际输出反推新预期 | 直接 CLI exit0，结构化 JSON 与原快照完全相等；**PASS（此样例）**。SKILL.md:99 写“预期 JSON 必须由上述命令的实际输出更新”是 **L1 文档缺陷**，独立预期必须从需求和证据先确定 |

## 四表/MD一致性、根因与交接

五张表均可重开，名称依次为 `核查概览`、`要求响应矩阵`、`附件核对`、`补遗与版本`、`待确认事项`；`核查概览`四维计数来自同一个矩阵状态，Markdown 每条四维字符串与矩阵一致，**机械一致性 PASS**。但 `response_negated` 与 `filename_empty_conditions` 的错误状态进入“已覆盖范围”，而 `date_signed_valid` 同条目既列“确定需要补资料”又列“已覆盖范围”；这是**业务语义一致性 FAIL**，不是 XLSX 损坏。`附件核对` 无材料义务时不产生对应行，`license_missing` 错误“不适用”连锁影响四维及 MD。

源码位置以**解压包相对路径**为准：`scripts/check_response.py:25` 的 `MATERIAL` 只抓 .txt/.md 文件名；`:82–90 covered()` 从词语共现得覆盖，未处理否定/条件；`:93–97 conditions()`；`:100–112 requirements()` 所需材料只来自 `MATERIAL.findall`；`:228–230` 覆盖状态；`:253–269` 材料状态，其中 `:260` 固定 `'2027' in requirement and '2026' in material`，`:261–263` 材料条件剔除文件名后 `all(...)` 空集真值；`:271–279` 未将日期未覆盖/无名材料义务列为缺口；`:323–379 write_outputs()` 四维/五表/MD 复制上述业务状态。`SKILL.md:26–34` 主要演示完整仓库路径（仅后来附带解压替换说明）；`:91–99` 错误预期快照循环。原包内容检查是 L1，所有上述正式 CLI 与文件回读是 L3，**未使用 monkeypatch/mock，不是 L4 模型对话，更不是 L5 WorkBuddy**。

旧 0.2.3 本轮新反例证明业务范围不可放行；旧历史 QA 结论仍保留，不撤销其针对原测试集的运行事实。新候选、修复和独立复验 `NOT_TESTED`；PDF/OCR、真伪认证、平台、许可及相似性审核 `NOT_TESTED/REVIEW_REQUIRED`。分析师应区分响应文本覆盖、附件真实提供与内容支持，并修复日期的角色/对象关系，不能把全部可比情况改成待确认。QA 后续从**新 ZIP**另用未硬编码年份/措辞/文件名的变体验证。本卡不改生产代码/历史快照/旧 ZIP、不 push/发布。
