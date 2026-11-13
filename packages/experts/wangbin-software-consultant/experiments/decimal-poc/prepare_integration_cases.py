"""Freeze fictional manual/model cases before replay; never overwrite evidence."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DEST = Path('F:/ideaWorkSpace/wangbin-workbuddy-delivery/experts/wangbin-software-consultant/calc-integration-01')
SCRIPT = HERE / 'skill-preview/wangbin-estimate-calculator/scripts/estimator.py'
BASE = json.loads((HERE / 'fixture_branches_synthetic.json').read_text(encoding='utf-8'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save_new(path, data):
    with path.open('xb') as file:
        file.write(data)


def variant(case):
    data = copy.deepcopy(BASE)
    if case == 'WB-01':
        data['work_packages'] = data['work_packages'][:2]
    elif case == 'WB-03':
        data['pricing'] = {'mode': 'fixed', 'unit_price': '1350', 'source': 'SYNTHETIC WB-03 user changes 1200 to 1350'}
    elif case == 'WB-04':
        data['pricing'] = {'mode': 'refused'}
    elif case == 'WB-05':
        data['previous_scope_version'] = 'synthetic-v1'
        data['scope_version'] = 'synthetic-v2'
        data['scope_changed'] = True
        data['work_packages'] = [row for row in data['work_packages'] if row['id'] != 'S2']
        for row in data['work_packages']:
            row['scope_version'] = 'synthetic-v2'
    elif case == 'WB-06':
        data['work_packages'][0]['roles']['QA']['low'] = 'unknown'
    return data


PROMPTS = {
    'WB-01': 'SYNTHETIC 演练：采购 M1 和库存 M2 两个工作包，角色 FE/BE/DB/QA 低高人天逐项采用随附冻结输入文件。缓冲低 10%、高 20% 为示意，固定 1200 元/人天。请核逐行、逐角色低高合计、MVP 的 B/R/E/人工费，外部费未知。不要把示意人天当客户工时。',
    'WB-02': 'SYNTHETIC ERP 演练：采用随附冻结输入的 M1、M2、S1、S2、F1、I1、C1 角色人天。采购库存→多仓审批和财务字段准备；真实财务接口 I1 文档及授权未知，只作为条件示意。缓冲 10%/20%、固定单价 1200。请比较 MVP、StandardA、StandardB、FullA、FullB 的成员、FE/BE/DB/QA、B/R/E、人工费；I1 只进两种 B 且不得双算，外费待询价。',
    'WB-03': 'SYNTHETIC 演练：在 WB-02 完全相同的工作包与 10%/20% 缓冲下，只把人工固定单价由 1200 改为 1350 元/人天。请比较新的各档 B/R/E 和人工费；不得修改工时，接口仍未知，外部费待询。',
    'WB-04': 'SYNTHETIC 演练：使用 WB-02 相同七项工作包与 10%/20% 缓冲；明确只要人天，不要人民币金额，拒绝参考单价。请实际复核五档角色 B/R/E，保留接口条件分支，不输出任何人民币金额。',
    'WB-05': 'SYNTHETIC 范围变更：WB-02 原范围 synthetic-v1 有审批 S2；现版本 synthetic-v2 删除 S2，其余六包保留，原版本不得暗改。沿用 10%/20% 和固定 1200。请分别说明过期审批包、当前五档成员及逐角色 B/R/E/条件人工费；真实接口费用仍未知。',
    'WB-06': 'SYNTHETIC 错误演练：随附输入采购 M1 的 QA.low 是 unknown，不是零。请尝试计算并告知脚本实际退出码/错误；若脚本或权限不可用，请说明没有核算回执。另有接口/许可等外部费用未知，不能写零或称完整报价。',
}


def main():
    if DEST.exists():
        existing = list(DEST.iterdir())
        if existing:
            raise SystemExit('refusing to overwrite existing delivery evidence')
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = {'status': 'FROZEN_BEFORE_MODEL', 'source_fixture_sha256': digest((HERE / 'fixture_branches_synthetic.json').read_bytes()), 'script_sha256': digest(SCRIPT.read_bytes()), 'cases': {}}
    for case, prompt in PROMPTS.items():
        data = (json.dumps(variant(case), ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        input_path = DEST / (case + '-input.json')
        output_path = DEST / (case + '-expected.json')
        save_new(input_path, data)
        command = [sys.executable, '-B', str(SCRIPT), str(input_path), '-o', str(output_path)]
        proc = subprocess.run(command, capture_output=True)
        stderr_path = DEST / (case + '-stderr.bin')
        save_new(stderr_path, proc.stderr)
        expected_rc = 2 if case == 'WB-06' else 0
        if proc.returncode != expected_rc or (proc.returncode == 0 and not output_path.exists()):
            raise SystemExit(f'{case}: unexpected calculator rc {proc.returncode}; evidence retained')
        manifest['cases'][case] = {'prompt': prompt, 'prompt_sha256': digest(prompt.encode('utf-8')), 'input': input_path.name, 'input_sha256': digest(data), 'command': command, 'calculator_rc': proc.returncode, 'stderr_sha256': digest(proc.stderr), 'output': output_path.name if output_path.exists() else None, 'output_sha256': digest(output_path.read_bytes()) if output_path.exists() else None, 'expected': json.loads(output_path.read_text(encoding='utf-8'))['tiers'] if output_path.exists() else None, 'prohibited': 'No unsupported complete project total, no fabricated tool event, no treating UNKNOWN as 0; no unconditional interface authorization.'}
    save_new(DEST / 'frozen-before-model.json', (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print('frozen_manifest_sha256=' + digest((DEST / 'frozen-before-model.json').read_bytes()))
    for case, entry in manifest['cases'].items():
        print(case, 'rc', entry['calculator_rc'], 'input', entry['input_sha256'], 'output', entry['output_sha256'])


if __name__ == '__main__':
    main()
