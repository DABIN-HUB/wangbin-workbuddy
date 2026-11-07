"""Developer PRE-QA replay: 94 frozen originals and 15 Q0 variants, never QA acceptance.

Read old runners' AST declarations only, never execute their one-shot QA side effects.
Writes generated XLSX/MD solely to this profile's scratch and checks frozen SHA.
"""
import ast
from collections import Counter
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(__file__).resolve().parent
ARCH = Path(sys.argv[1]).resolve() if sys.argv[1] != '--source' else None
SCRATCH = Path.home() / 'AppData/Local/hermes/profiles/wb-developer/cache/scratch'
DIMS = ('响应存在状态', '条件覆盖状态', '附件实际提供状态', '内容支持状态')
SHA = lambda data: hashlib.sha256(data).hexdigest()
BASE = json.loads((DOC / 'qa-fix5-0210-independent-results.json').read_text(encoding='utf-8'))
assert len(BASE['cases']) == 94
assert SHA((DOC / 'qa-fix5-0210-independent-results.json').read_bytes()) == 'a7886ea08aba45199332a8477f24ed9f5bc518af6db48de138d1fa4a56e90656'
Q0 = json.loads((DOC / 'qa-fix6-prefreeze-cases.json').read_text(encoding='utf-8'))
Q0_SHA = json.loads((DOC / 'qa-fix6-prefreeze-sha.json').read_text(encoding='utf-8'))
assert SHA((DOC / 'qa-fix6-prefreeze-cases.json').read_bytes()) == Q0_SHA['case_file_sha256']


def frozen_declarations(script, variables):
    declarations = {}
    for stmt in ast.parse(script.read_text(encoding='utf-8')).body:
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            continue
        name = stmt.targets[0].id
        if name not in variables:
            continue
        def read(expr):
            if isinstance(expr, ast.Name):
                return declarations[expr.id]
            if isinstance(expr, (ast.List, ast.Tuple)):
                values = [read(x) for x in expr.elts]
                return tuple(values) if isinstance(expr, ast.Tuple) else values
            if isinstance(expr, ast.Dict):
                return {read(k): read(v) for k, v in zip(expr.keys, expr.values)}
            return ast.literal_eval(expr)
        declarations[name] = read(stmt.value)
    return declarations


old = frozen_declarations(DOC / 'qa-fix4-029-independent.py',
                          {'P', 'N', 'E_NEG', 'E_POS', 'E_UNK', 'variants', 'holdouts'})
new = frozen_declarations(DOC / 'qa-fix5-0210-independent.py',
                          {'P', 'N', 'E_NEG', 'E_POS', 'E_UNK', 'U', 'E_ABS', 'variants', 'holdouts', 'fresh'})
variants = {v['id']: v for v in old['variants'] + old['holdouts'] + new['fresh']}
assert len(variants) == 41
counts = Counter()
issues = []
with tempfile.TemporaryDirectory(prefix='fix6-developer-preqa-', dir=SCRATCH) as temporary:
    folder = Path(temporary)
    if ARCH is not None:
        with zipfile.ZipFile(ARCH) as archive:
            assert archive.testzip() is None
            archive.extractall(folder / 'extract')
        script = folder / 'extract/wangbin-tender-analyzer/scripts/check_response.py'
    else:
        script = ROOT / 'packages/skills/wangbin-tender-analyzer/scripts/check_response.py'
    with zipfile.ZipFile(DOC / 'qa-audit-r1-new-027-fixtures-outputs.zip') as original:
        for record in BASE['cases']:
            ident = record['id']
            case = folder / 'inputs' / ident
            case.mkdir(parents=True)
            if ident in variants:
                v = variants[ident]
                for name, text in [('tender.txt', v['t']), ('response.md', v['r']), *v.get('e', {}).items()]:
                    (case / name).write_text(text, encoding='utf-8')
            else:
                for name in record['input_sha']:
                    (case / name).write_bytes(original.read('cases/' + ident + '/' + name))
            expected_sha = record['input_sha']
            assert {p.name: SHA(p.read_bytes()) for p in case.iterdir()} == expected_sha, ident
            out = folder / 'out' / ident
            out.mkdir(parents=True)
            argv = record['argv']
            cmd = [sys.executable, str(script)]
            for i, entry in enumerate(argv):
                if entry in ('--tender', '--response', '--attachment-catalog', '--evidence-file', '--amendment'):
                    cmd.extend((entry, str(case / Path(argv[i + 1]).name)))
                elif entry == '--project':
                    cmd.extend((entry, argv[i + 1]))
                elif entry == '--mode':
                    cmd.extend((entry, argv[i + 1]))
                elif entry == '--output-dir':
                    cmd.extend((entry, str(out)))
            result = subprocess.run(cmd, cwd=case, capture_output=True, text=True, encoding='utf-8', timeout=45,
                                    env={k: v for k, v in os.environ.items() if k != 'PYTHONPATH'})
            problem = []
            files = list(out.iterdir())
            if result.returncode != 0 or len(files) != 2 or {p.suffix for p in files} != {'.md', '.xlsx'}:
                problem.append(f'exit={result.returncode} outputs={len(files)} stderr={result.stderr}')
            else:
                with closing(load_workbook(next(p for p in files if p.suffix == '.xlsx'), read_only=True)) as book:
                    if book.sheetnames != ['核查概览', '要求响应矩阵', '附件核对', '补遗与版本', '待确认事项']:
                        problem.append('five sheets/order')
                    grid = list(book['要求响应矩阵'].values)
                    rows = [dict(zip(grid[0], row)) for row in grid[1:]]
                    expected = record['expected']
                    if expected and isinstance(expected[0], str):
                        expected = [expected]
                    if expected is None:
                        expected = [None] * len(rows)
                    if len(rows) != len(expected):
                        problem.append('row count')
                    for row, want in zip(rows, expected):
                        actual = tuple(row[d] for d in DIMS)
                        if want and any(w is not None and w != a for w, a in zip(want, actual)):
                            problem.append(f'{row["唯一ID"]} expected={want} actual={actual}')
                    for dim in DIMS:
                        tally = Counter(row[dim] for row in rows)
                        overview = {line[1]: line[2] for line in book['核查概览'].values if line[0] == dim and line[1] != '状态'}
                        if dict(tally) != overview:
                            problem.append('overview mismatch ' + dim)
                    md = next(p for p in files if p.suffix == '.md').read_text(encoding='utf-8')
                    for row in rows:
                        covered = md.split('## 已覆盖范围（仅文本层面）')[-1].split('## 未覆盖范围')[0]
                        if row['缺口'] and row['唯一ID'] in covered:
                            problem.append('gap in covered MD')
                    if ident == 'F04-same-object-conflict':
                        if not all(source in str(rows[0]['响应位置']) + str(rows[0]['建议']) for source in ('response.md:1', 'response.md:2')) or rows[0]['缺口']:
                            problem.append('F04 conflict provenance')
                    if ident == 'F08-explicit-no-body' and '营业执照.txt:2' not in str(rows[0]['缺口']):
                        problem.append('F08 negative evidence')
            counts[(record['origin'], 'total')] += 1
            counts[(record['origin'], 'pass' if not problem else 'fail')] += 1
            if problem:
                issues.append((ident, problem))
    for case_record in Q0['cases']:
        ident = case_record['id']
        case = DOC / 'qa-fix6-prefreeze-fixtures' / ident
        assert {p.name: SHA(p.read_bytes()) for p in case.iterdir()} == Q0_SHA['inputs'][ident]
        out = folder / 'out' / ident
        out.mkdir()
        cmd = [sys.executable, str(script), '--tender', str(case / 'tender.txt'), '--response', str(case / 'response.md'),
               '--mode', 'check', '--project', ident, '--output-dir', str(out)]
        for name in case_record['inputs']:
            if name not in ('tender.txt', 'response.md'):
                cmd.extend(('--evidence-file', str(case / name)))
        result = subprocess.run(cmd, cwd=folder, capture_output=True, text=True, encoding='utf-8', timeout=45)
        problem = []
        if result.returncode != 0:
            problem.append(f'exit={result.returncode} {result.stderr}')
        else:
            with closing(load_workbook(out / (ident + '-投标响应检查.xlsx'), read_only=True)) as book:
                grid = list(book['要求响应矩阵'].values)
                rows = [dict(zip(grid[0], row)) for row in grid[1:]]
                if len(rows) != len(case_record['rows']):
                    problem.append('row count')
                for row, want in zip(rows, case_record['rows']):
                    actual = [row[d] for d in DIMS]
                    if actual != want['expected'] or not all(source in row['响应位置'] for source in want['response_sources']):
                        problem.append((actual, want['expected'], row['响应位置']))
                for dim in DIMS:
                    tally = Counter(row[dim] for row in rows)
                    overview = {line[1]: line[2] for line in book['核查概览'].values if line[0] == dim and line[1] != '状态'}
                    if dict(tally) != overview:
                        problem.append('overview mismatch ' + dim)
        counts[('Q0', 'total')] += 1
        counts[('Q0', 'pass' if not problem else 'fail')] += 1
        if problem:
            issues.append((ident, problem))
    legacy = subprocess.run([sys.executable, str(script.with_name('analyze_tender.py')), '--input',
                             str(script.parent.parent / 'examples/fictional-tender.txt')], cwd=folder,
                            capture_output=True, text=True, encoding='utf-8', timeout=45)
    legacy_expected = json.loads((script.parent.parent / 'examples/fictional-tender.expected.json').read_text(encoding='utf-8'))
    legacy_ok = legacy.returncode == 0 and json.loads(legacy.stdout) == legacy_expected
    error_root = folder / 'error-probes'
    error_root.mkdir()
    (error_root / 'tender.txt').write_text('1. 必须支持自动备份。', encoding='utf-8')
    (error_root / 'response.md').write_text('1. 我方支持自动备份。', encoding='utf-8')
    (error_root / 'bad.md').write_bytes(b'\xff\xfe')
    (error_root / 'bad.pdf').write_text('unsupported', encoding='utf-8')
    (error_root / 'bad.xlsx').write_bytes(b'not a spreadsheet')
    probes = [('missing', [], 'MISSING_RESPONSE'),
              ('utf8', ['--response', str(error_root / 'bad.md')], 'INVALID_UTF8'),
              ('type', ['--response', str(error_root / 'bad.pdf')], 'INPUT_TYPE_UNSUPPORTED'),
              ('catalog', ['--response', str(error_root / 'response.md'), '--attachment-catalog', str(error_root / 'bad.xlsx')], 'CATALOG_READ_FAILED'),
              ('escape', ['--response', str(error_root / 'response.md'), '--project', '../outside'], 'OUTPUT_PATH_INVALID'),
              ('positive', ['--response', str(error_root / 'response.md')], None)]
    probe_results = {}
    for name, options, code in probes:
        output = error_root / name
        output.mkdir()
        proc = subprocess.run([sys.executable, str(script), '--tender', str(error_root / 'tender.txt'),
                               '--mode', 'check', '--output-dir', str(output), *options],
                              cwd=folder, capture_output=True, text=True, encoding='utf-8', timeout=45)
        files = list(output.iterdir())
        correct = ((proc.returncode == 2 and 'ERROR ' + code in proc.stderr and not files)
                   if code else proc.returncode == 0 and {file.suffix for file in files} == {'.md', '.xlsx'})
        probe_results[name] = {'exit': proc.returncode, 'expected': code or 'success', 'ok': correct}
        if not correct:
            issues.append(('error-probe-' + name, proc.stderr))
    print('DEVELOPER PRE-QA COUNTS', dict(counts), 'legacy_json', legacy_ok,
          'error_probes', probe_results, 'issues', issues, flush=True)
    sys.exit(bool(issues) or not legacy_ok)
