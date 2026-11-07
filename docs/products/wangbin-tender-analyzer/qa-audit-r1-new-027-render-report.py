"""Render independently recorded QA evidence into a human-readable final FAIL report."""
import json
from pathlib import Path
root=Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check/docs/products/wangbin-tender-analyzer')
scratch=Path('C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_independent_027_rerun1')
cases=json.loads((root/'qa-audit-r1-new-027-results.json').read_text(encoding='utf-8'))['cases']
failed=[x for x in cases if x['issues']]
assert len(failed)==6
lines=['# AUDIT-R1 Q06 · 0.2.7 最终独立 ZIP L3 复验：FAIL 47/53',
'', 'product_id `wangbin-tender-analyzer` · task_id `t_b7703b65` · workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check` · branch `skill/tender-response-check` · base_commit `f246cd88522fbb9a0ec7c5c2514409eaa648cf51`。本轮返工 2/2 已用尽；历史 0.2.5 29/32 FAIL 与 0.2.6 36/41 FAIL 保持不变。',
'', '## 锁定候选与范围',
'', '- 本地包 `dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip`，SHA-256 `12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09`；sidecar/manifest/ZipFile.testzip/11 成员的路径、大小、SHA 和源码对应均独立核查通过，SKILL YAML、版本、中英各三问及解压运行路径核查。catalog `active_version=0.2.7` 为本地工厂登记，绝非 WorkBuddy 平台发布。旧 0.2.3/0.2.5/0.2.6 SHA 依次为 `5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce` / `69e1a9f2ef0698e40a174faf711e1eb627aecc68fb1106c567a506d063493c06` / `1c18b43f8cb465eb261ae4ccdc950259399f64b9c70477496809e3102dd4753a`，实物未变。开发提交源码 SHA 与 ZIP 内脚本相同。',
'- 用 `qa-audit-r1-new-027-probe.py` 在 profile scratch `q06_independent_027_rerun1` 干净解压精确 ZIP，逐例创建真实 TXT/MD/CSV/XLSX 输入，清除 PYTHONPATH，调用解压包正式 `scripts/check_response.py`，每例空输出目录；53 例 CLI 全部 exit 0、各生成 XLSX+MD，实际重开 XLSX 五表、核验四维/缺口/来源/概览统计和 MD 覆盖分类、无公式单元格。沿用先于运行冻结的旧 41 例断言，额外事先声明 12 个新等义正反、时间、跨对象、材料文本变体：旧 41/41 PASS，新 6/12 PASS，**共 47 PASS / 6 FAIL**；CLI exit0 ≠ 业务通过。',
'- 每例实际命令 argv、cwd、退出码、stdout/stderr、真实输入输出 SHA、预期与实际、五表行及完整 MD 见 `qa-audit-r1-new-027-results.json`；实际原件及两输出见 `qa-audit-r1-new-027-fixtures-outputs.zip`（260 件，SHA-256 `a791979b9e6d83b36b8e533cde7f65ab1ac3267ced9a909512827413dbc3c986`），非 Skill ZIP。',
'', '## 阻断问题与精确复现',
'', '下面每项的文件路径是证据 ZIP 内 `cases/<ID>/`，使用 `--tender tender.txt --mode check --response response.md --output-dir out --project 虚构核验<ID>`；材料案例额外传入所列 `--evidence-file`。各文件 UTF-8，行号 L1；按报告 JSON 中 argv 可精确重跑。判定仅为本次提供文本，不认证公司证照真伪或运营环境。', '']
for x in failed:
 ident=x['id'];folder=scratch/'cases'/ident
 inputs=[]
 for name in ('tender.txt','response.md','营业执照.txt','certificate.txt','乙类.txt'):
  p=folder/name
  if p.exists():inputs.append(f'`{name}:1` `{p.read_text(encoding="utf-8")}` (SHA-256 `{x["input_sha"][name]}`)')
 actual=[]
 for row in x['actual']:
  actual.append('`'+str(row['唯一ID'])+'` '+ ' / '.join(str(row.get(k)) for k in ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态'))+f'；缺口 `{row.get("缺口")}`；证据位置 `{row.get("证据位置")}`；来源 `{row.get("来源")}`')
 lines.extend([f'### {ident}', '', '- 实际输入：'+'；'.join(inputs),'- 独立预期四维：`'+str(x['expected'])+'`；明确否定/未启用须有缺口与来源并不得列 MD 已覆盖，明确占位/非证书须记录文本反证而非支持或含糊待确认。','- 实际（CLI exit '+str(x['exit'])+'）：'+'；'.join(actual),'- 逐格缺陷：'+'；'.join(x['issues']),'- 输出 SHA-256：`'+str(x['output_sha'])+'`；XLSX 五表和 MD 全文见结果 JSON/证据 ZIP。', ''])
lines.extend(['## 其他验证与边界','','- 旧 `scripts/analyze_tender.py --input examples/fictional-tender.txt` 从 0.2.7 解压包 exit 0；解析 stdout 与原 0.2.3 ZIP 内 **原始** `fictional-tender.expected.json` 相等，未改预期。正式错误 6/6：缺响应、非法 UTF-8、PDF、损坏 XLSX 目录、输出路径逃逸各 exit 2/无成功输出；正向 exit 0/两文件，详情 `qa-audit-r1-new-027-errors.json`。','- `python -m pytest -q tests/test_tender_response_audit.py tests/test_tender_analyzer.py --basetemp=C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_pytest_027_final` exit 0（42 passed, 1 Windows 实体 symlink skipped）；`python -m tooling.products validate --id wangbin-tender-analyzer` exit 0；`python -m tooling.products verify --id wangbin-tender-analyzer` exit 0；`python -m zipfile -t` 两份 ZIP exit 0，均不能抵消 L3 业务失败。','- `python -m tooling.products release-check --id wangbin-tender-analyzer` **exit 1 / BLOCKED**：许可证文件不存在及依赖合法分发待定；相似性人工 `REVIEW_REQUIRED`；WorkBuddy 安装/对话/审核 `NOT_TESTED`。L4 Hermes 宿主三轮因 L3 FAIL **NOT_TESTED**，L5 WorkBuddy **NOT_TESTED**；证书真实性 NOT_VERIFIED；Windows 物理 symlink 安全性 SKIPPED，openpyxl 隔离重装及平台依赖可用性 NOT_TESTED；完整旧 A02–A14 独立 L3 NOT_TESTED；0.1.0 实物 NOT_VERIFIED。','- 未改业务代码、历史报告、许可证、旧 ZIP；未 push、merge、rebase、上传或发布。只有本产品 `qa-audit-r1-new-027-*` QA-only 证据文件。','','**结论：0.2.7 精确 ZIP 的本地独立 L3 为 FAIL，六个新发现变体存在可复现业务误判；本轮自动返工额度 2/2 已用尽，不建立第三轮修复。已通知经理 `t_0237b1ca` 如实报告，不得宣称六包全部独立 QA 合格。**',''])
out=root/'qa-audit-r1-new-027.md';assert not out.exists();out.write_text('\n'.join(lines),encoding='utf-8');print(out,len(failed),'failures')
