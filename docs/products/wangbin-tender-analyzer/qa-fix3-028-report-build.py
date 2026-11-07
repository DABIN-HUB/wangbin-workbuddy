"""Format independent 0.2.8 QA evidence from real result JSON; never edit candidate/source or historical QA."""
import hashlib
import json
import shutil
from pathlib import Path
root=Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check/docs/products/wangbin-tender-analyzer')
results=json.loads((root/'qa-fix3-028-independent-results.json').read_text(encoding='utf-8'))
old=json.loads((root/'qa-audit-r1-new-027-results.json').read_text(encoding='utf-8'))
by={r['id']:r for r in results['cases']}
prior={r['id']:r for r in old['cases']}
assert len(by)==66 and results['summary']['frozen_pass']==53 and results['summary']['variant_pass']==11
p=lambda x:str(x or '').replace('|','\\|').replace('\n','<br>')
lines=['# Q06 FIX-3 0.2.8 ZIP 独立验收：FAIL（原53/53；新变体11/13）','','- `product_id=wangbin-tender-analyzer`；`task_id=t_03cbcafd`；workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch `skill/tender-response-check`；QA 基线 commit `99d8ce34072fe3751be30f62c526cf0a7ddbfa70`。本结论独立于开发自测，**不放行业务**：两项新增独立歧义反例误升已覆盖/支持。**STOP；NO FIX-4；NO PUSH。**','- 新包 `dist/wangbin-tender-analyzer-0.2.8-skill-candidate.zip` SHA-256 `'+results['package']['new_sha256']+'`，旧包 0.2.7 SHA-256 `'+results['package']['old_sha256']+'` 不变；原输入证据 ZIP SHA-256 `'+results['package']['fixture_sha256']+'`。包内 11 文件，全成员对 manifest SHA/长度、源码同路径字节相等，CRC/testzip、相对路径、无重复/敏感路径、sidecar、SKILL frontmatter 0.2.8、catalog 0.2.8 已核；仅本地完整性。','- 独立脚本 `python docs/products/wangbin-tender-analyzer/qa-fix3-028-independent.py`（无 `PYTHONPATH`，从 0.2.8 ZIP 干净解压，原 53 原始输入逐字节取原冻结证据 ZIP、原 JSON expected 不变）；首次 QA 探针自身将 JSON 四维列表误当多行、并将响应位置误查来源（无业务失败定论），更正探针后在全新 profile scratch `q06_fix3_independent_028_r2` 重跑，并以最终脚本在全新 `q06_fix3_independent_028_r3` 再复核同结论。首次探针发现独立歧义反例并在重跑前将 Z10 输入明确为“是否构成正式执照尚待核实”；历史原预期、ZIP、业务代码均未改。记录当前逐案原始实际结果及命令、cwd、退出码、stdout/stderr、输入输出 SHA 于 `qa-fix3-028-independent-results.json`。','- 原 53：**53/53** 原四维与五表行数/概览逐状态计数、MD 已覆盖/缺口、部分附件关联、无公式、真实 XLSX/MD 通过；六项旧失败 Q02/Q03/Q05/Q06/Q07/Q10 均在原件上关闭。新变体：**11/13**，Z04/Z10 两项 FAIL（精确见下）。旧 JSON CLI 与旧 ZIP 内 expected 结构快照相同；prepare、check、正式补遗（原 V09）均实际执行；错误输入 5 项预期 exit 2 / 稳定错误码 / 无伪输出，正控 exit 0 / 两文件。','- **门禁：本地 L3 QA FAIL**。宿主自然语言多轮与 WorkBuddy 安装/平台审核 NOT_TESTED；许可证/分发权利 NOT_VERIFIED/BLOCKED；Windows 物理 symlink NOT_TESTED；企业现实资质真实性和政府核发 NOT_TESTED。0.2.8 不应作为已验收候选发布/上传。','','## 六旧失败的前后对比（四维顺序：响应/条件/附件/内容）','','| 案例 | 原 0.2.7 四维 | 本次 0.2.8 四维 | 结果 |','|---|---|---|---|']
for id in ('Q02-not-available-yet','Q03-proposed-future','Q05-no-cross-subject','Q06-evidence-not-issued','Q07-evidence-empty-wrapper','Q10-cross-object-negative'):
    a=[[r.get(k) for k in ('响应存在状态','条件覆盖状态','附件实际提供状态','内容支持状态')] for r in prior[id]['actual']]
    b=by[id]['actual'];lines.append('| '+id+' | '+p(a)+' | '+p(b)+' | '+('PASS' if not by[id]['issues'] else 'FAIL')+' |')
lines += ['','## 新增失败：精确复现','','两项均为 CLI exit 0 且生成五表，不能以退出码当业务 PASS；目标不要求认证现实证件真伪，只要求不要把明确“不知道”变成确定已满足。','']
for id in ('Z04-unknown-status','Z10-license-uncertain'):
 r=by[id];d=Path(r['cwd']); row=r['matrix_rows'][0]
 lines += ['### '+id,'','- 招标 `tender.txt`: '+(d/'tender.txt').read_text(encoding='utf-8').replace('\n',' / ')+'；回应 `response.md`: '+(d/'response.md').read_text(encoding='utf-8').replace('\n',' / ')]
 for n in ('营业执照.txt',):
    if (d/n).exists():lines.append('- 实际材料 `'+n+'`: '+(d/n).read_text(encoding='utf-8'))
 lines += ['- 预期（四维）：`'+p(r['expected'][0])+'`；实际：`'+p(r['actual'][0])+'`；实测差异：`'+p(r['issues'])+'`。','- `缺口`：`'+p(row.get('缺口'))+'`；`来源`：`'+p(row.get('来源'))+'`；`响应位置`：`'+p(row.get('响应位置'))+'`；`证据位置`：`'+p(row.get('证据位置'))+'`。','- 原输入 SHA-256：`'+p(r['input_sha'])+'`；输出 SHA-256：`'+p(r['output_sha'])+'`。','- 执行 `'+p(' '.join(r['argv']))+'`；cwd `'+str(d)+'`；exit `'+str(r['exit'])+'`；stdout `'+p(r['stdout'])+'`；stderr `'+p(r['stderr'])+'`。','- 修复预期仅为下次经理决策参考，本卡不启动返工：未知是否上线不能推出已上线；仅登记信息且“是否构成正式营业执照尚待核实”不应推出材料支持或条件已覆盖。','']
 lines.insert(len(lines)-2,'- 待确认表：`'+p(r['pending_rows'])+'`；附件核对表：`'+p(r['attachment_rows'])+'`；MD 已覆盖分段：`'+p(r['md_text'].split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0])+'`。')
lines += ['## 全案摘要（详见可执行脚本与原始 JSON）','','| ID | 类型 | 比对结果 | 四维实际 |','|---|---|---|---|']
for r in results['cases']:lines.append('| '+r['id']+' | '+r['origin']+' | '+('FAIL: '+p(r['issues']) if r['issues'] else 'PASS')+' | '+p(r.get('actual'))+' |')
lines += ['','## 实物与限制','','- `qa-fix3-028-independent.py` 为从 ZIP 重放的可执行证据；`qa-fix3-028-independent-results.json` 为逐行四维、gap/provenance、完整五表行、MD 全文、所有输入输出 SHA 与错误探针原始返回。','- `qa-fix3-028-examples/` 是原 CLI 实际生成的两个案例（一个原失败已闭合，一个新增歧义失败）的 XLSX+MD。输入留在 profile-owned scratch，逐字节 hash 见 JSON；报告含复现输入原文。','- 原 0.2.7 QA 47/53 FAIL 的历史结果不改写；本次失败数是 **新增独立变体 2/13**，不是原 53 回归失败。确认矩阵不等于平台运行与许可证授权。','']
examples=root/'qa-fix3-028-examples'; examples.mkdir(exist_ok=True)
for id in ('Q06-evidence-not-issued','Z10-license-uncertain'):
    files=list((Path(by[id]['cwd'])/'out').iterdir());assert len(files)==2
    for f in files:
        dst=examples/(id+f.suffix); assert hashlib.sha256(f.read_bytes()).hexdigest()==by[id]['output_sha'][f.name]
        shutil.copyfile(f,dst)
        assert hashlib.sha256(dst.read_bytes()).hexdigest()==by[id]['output_sha'][f.name]
report=root/'qa-fix3-028-independent-report.md';report.write_text('\n'.join(lines),encoding='utf-8')
print('REPORT',report,'cases',len(by),'original',results['summary']['frozen_pass'],'variants',results['summary']['variant_pass'],'examples',len(list(examples.iterdir())))
