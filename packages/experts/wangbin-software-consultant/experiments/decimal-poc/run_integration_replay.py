"""Hermes local A/B replay: model chooses tools in B, never pre-run Python for it.

Only pre-frozen synthetic fixtures are referenced; all raw traces remain outside Git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = Path('F:/ideaWorkSpace/wangbin-workbuddy-software-consultant')
EVIDENCE = Path('F:/ideaWorkSpace/wangbin-workbuddy-delivery/experts/wangbin-software-consultant/calc-integration-01')
AGENT = ROOT / 'packages/experts/wangbin-software-consultant/agents/wangbin-software-consultant.md'
LAYER = HERE / 'integration-instructions.md'
SCRIPT = HERE / 'skill-preview/wangbin-estimate-calculator/scripts/estimator.py'
ZIP = HERE / 'dist/wangbin-estimate-calculator-0.1.0-licensefix1.zip'
MAP = {'E2E-01': 'WB-01', 'E2E-02': 'WB-02', 'E2E-03': 'WB-04', 'E2E-04': 'WB-06', 'E2E-05': 'WB-02'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def put(path, data):
    with path.open('xb') as output:
        output.write(data)


def prompts(case, frozen):
    user = frozen['prompt']
    if case == 'E2E-02':
        return [
            'SYNTHETIC 第一轮：ERP 做采购和库存；先给初步范围。工作包见冻结 WB-02 输入中的 M1、M2，角色人天是示意假设。',
            'SYNTHETIC 第二轮：新增多仓审批和财务对接，旧需求保留。S1、S2 是新增，F1 为财务映射准备，I1 真正接口仍无授权/文档。沿用虚构工作包。',
            'SYNTHETIC 第三轮：按当前同一会话范围给五方案 MVP/StandardA/StandardB/FullA/FullB 工作包、角色、B/R/E 和人工费；固定 1200 元/人天、缓冲 10%/20% 均是虚构用户演示参数，未知接口/许可费待询价。冻结文件 WB-02-input.json 包含完整逐角色数；你须真实自行选择计算工具且核对回执，不能假装已有授权。'
        ]
    if case == 'E2E-04':
        return ['SYNTHETIC 无效工作包测试：冻结 WB-06-input.json 中 M1 的 QA.low 是 unknown。请尝试调用计算器并只报告真实错误，不要补 0 或编造人工费。']
    if case == 'E2E-05':
        return ['SYNTHETIC 不可用工具测试：计算器执行权限没有被授予，本轮禁止调用任何 terminal/脚本；即使看到 WB-02 冻结虚构工作包，绝不可称已使用 Decimal 工具验证。请说清缺哪一步、哪些金额不应给定价。']
    return [user]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=MAP)
    parser.add_argument('arm', choices=('A', 'B'))
    parser.add_argument('repeat', choices=('1', '2'))
    args = parser.parse_args()
    frozen = json.loads((EVIDENCE / 'frozen-before-model.json').read_text(encoding='utf-8'))
    item = frozen['cases'][MAP[args.case]]
    if sha((EVIDENCE / item['input']).read_bytes()) != item['input_sha256']:
        raise SystemExit('frozen input changed')
    session_dir = EVIDENCE / 'raw' / (args.case + '-' + args.arm + '-' + args.repeat)
    session_dir.mkdir(parents=True, exist_ok=False)
    original = AGENT.read_bytes()
    layer = LAYER.read_bytes()
    script = SCRIPT.read_bytes()
    zip_bytes = ZIP.read_bytes()
    metadata = {'case': args.case, 'arm': args.arm, 'repeat': args.repeat, 'model_requested': 'gpt-6-sol',
                'provider_requested': 'openai-codex', 'agent_sha256': sha(original),
                'layer_sha256': sha(layer) if args.arm == 'B' else None,
                'script_sha256': sha(script), 'zip_sha256': sha(zip_bytes),
                'frozen_manifest_sha256': sha((EVIDENCE/'frozen-before-model.json').read_bytes()),
                'frozen_input_sha256': item['input_sha256'], 'turns': [], 'classification': 'MODEL_REPLAY_PENDING'}
    session_id = None
    for index, user in enumerate(prompts(args.case, item), 1):
        # First turn embeds the original bytes unchanged as text; subsequent turns resume
        # the *same* session. Never inject a precomputed calculator receipt into the query.
        if index == 1:
            context = ('The following is the unchanged formal Expert Agent source. Apply it as your consulting rules. '
                       'It is NOT a claim of installation in WorkBuddy. SHA-256: ' + sha(original) + '\n'
                       '<FORMAL_AGENT>\n' + original.decode('utf-8') + '\n</FORMAL_AGENT>\n')
            if args.arm == 'B':
                context += '\n<ISOLATED_EXPERIMENT_LAYER>\n' + layer.decode('utf-8') + '\n</ISOLATED_EXPERIMENT_LAYER>\n'
            context += ('\nCurrent synthetic fixture location: ' + str(EVIDENCE / item['input']) +
                        '\nExact calculator script (B only, available if tool permitted): ' + str(SCRIPT) +
                        '\nUse the frozen fixture as supplied fictional source. Write any NEW receipt only within this distinct session directory: ' + str(session_dir) +
                        '\nNo real client data and no other file edits.\n')
        else:
            context = ''
        prompt = context + '\n<USER_TURN>\n' + user + '\n</USER_TURN>\n'
        query = session_dir / f'turn-{index}-query.txt'
        put(query, prompt.encode('utf-8'))
        cmd = ['hermes', '-p', 'wb-developer', 'chat', '--query-file', str(query),
               '--format', 'stream-json', '--ignore-rules', '--ignore-user-config',
               '-m', 'gpt-6-sol', '--provider', 'openai-codex',
               '--in', str(ROOT), '-t', 'terminal,file' if args.arm == 'B' and args.case != 'E2E-05' else 'web']
        if session_id:
            cmd += ['--resume', session_id]
        else:
            cmd += ['--max-turns', '12']
        print(args.case, args.arm, args.repeat, 'turn', index, 'launch', flush=True)
        try:
            process = subprocess.run(cmd, capture_output=True, timeout=240)
            rc = process.returncode
            stdout, stderr = process.stdout, process.stderr
        except subprocess.TimeoutExpired as exc:
            rc = 'TIMEOUT'
            stdout, stderr = exc.stdout or b'', exc.stderr or b''
        out_path = session_dir / f'turn-{index}.jsonl'
        err_path = session_dir / f'turn-{index}.stderr.bin'
        put(out_path, stdout)
        put(err_path, stderr)
        events = []
        for raw_line in stdout.splitlines():
            try:
                events.append(json.loads(raw_line))
            except (ValueError, UnicodeDecodeError):
                pass
        results = [e for e in events if e.get('type') == 'result']
        result = results[-1] if results else {}
        found = result.get('session_id')
        if found:
            if session_id and found != session_id:
                metadata['session_mismatch'] = [session_id, found]
                rc = 'SESSION_MISMATCH'
            session_id = found
        uses = [e for e in events if e.get('type') == 'tool_use']
        returns = [e for e in events if e.get('type') == 'tool_result']
        metadata['turns'].append({'turn': index, 'user': user, 'user_sha256': sha(user.encode('utf-8')),
                                  'query_sha256': sha(prompt.encode('utf-8')), 'command': cmd,
                                  'outer_cli_rc': rc, 'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr),
                                  'session_id': found, 'raw_init': next((e for e in events if e.get('type')=='system' and e.get('subtype')=='init'), None),
                                  'raw_result': result, 'tool_use_count': len(uses), 'tool_result_count': len(returns),
                                  'terminal_use_count': sum(e.get('name')=='terminal' for e in uses),
                                  'answer_sha256': sha(result.get('text','').encode('utf-8'))})
        print('turn', index, 'rc', rc, 'session', found, 'tools', len(uses), 'results', len(returns), 'answer_chars', len(result.get('text','')), flush=True)
        if rc != 0 or not found:
            break
    metadata['session_id'] = session_id
    metadata['classification'] = 'RAW_MODEL_REPLAY_RECORDED_NOT_YET_RECONCILED'
    put(session_dir / 'run.json', (json.dumps(metadata, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print('evidence', session_dir, flush=True)


if __name__ == '__main__':
    main()
