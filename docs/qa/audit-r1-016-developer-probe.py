"""Developer-only black-box 0.1.5 PRE-QA ZIP probe; fictional files, no repository imports."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from docx import Document
from openpyxl import Workbook, load_workbook


def main():
    archive, result_path = map(Path, sys.argv[1:])
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    sidecar = archive.with_name(archive.name + '.sha256').read_text(encoding='ascii')
    manifest = json.loads(archive.with_name(archive.name + '.manifest.json').read_text(encoding='utf-8'))
    cases = [
        ('denied-and-max', '同一测试场景下并发登录人数不得低于73人。', '同一压测场景不支持74人并发登录，最大仅支持72人并发登录。', 'NONCONFORMING', '.md'),
        ('denied-only', '同一测试场景下并发登录人数不得低于73人。', '同一压测场景无法支持74人并发登录。', 'PENDING_CONFIRMATION', '.docx'),
        ('denied-max-other-order', '同一测试场景下并发登录人数不得低于73人。', '同一压测场景最大只能支持72人并发登录；不能达到74人并发登录。', 'NONCONFORMING', '.xlsx'),
        ('denied-but-73-supported', '同一测试场景下并发登录人数不得低于73人。', '同一压测场景不支持74人并发登录；实测支持73人并发登录。', 'EVIDENCE_FOUND', '.md'),
        ('conflicting-74', '同一测试场景下并发登录人数不得低于73人。', '同一压测场景支持74人并发登录；不支持74人并发登录。', 'PENDING_CONFIRMATION', '.md'),
        ('72', '同一测试场景下并发登录人数不得低于73人。', '同一压测场景最大支持72人并发登录。', 'NONCONFORMING', '.md'),
        ('73', '同一测试场景下并发登录人数不得低于73人。', '同一压测场景最大支持73人并发登录。', 'EVIDENCE_FOUND', '.xlsx'),
        ('74', '同一测试场景下并发登录人数不得低于73人。', '同一压测场景最大支持74人并发登录。', 'EVIDENCE_FOUND', '.md'),
        ('omitted-abnormal', '全部登录测试用例通过。', '共执行41项登录用例，成功41项，失败0项；但是登录异常路径尚未执行。', 'PENDING_CONFIRMATION', '.txt'),
        ('omitted-boundary', '全部登录测试用例通过。', '共执行57项登录用例，成功57项，失败0项；登录边界场景没测。', 'PENDING_CONFIRMATION', '.docx'),
        ('omitted-security', '全部登录测试用例通过。', '共执行53项登录用例，成功53项，失败0项；登录安全流程未覆盖。', 'PENDING_CONFIRMATION', '.xlsx'),
        ('omitted-login', '全部登录测试用例通过。', '共执行41项登录用例，成功41项，失败0项，但高并发登录用例没有执行。', 'PENDING_CONFIRMATION', '.docx'),
        ('omitted-coverage', '全部登录测试用例通过。', '共执行41项登录用例，成功41项，失败0项；高并发登录测试尚未覆盖。', 'PENDING_CONFIRMATION', '.xlsx'),
        ('complete', '全部登录测试用例通过。', '共执行41项登录用例，成功41项，失败0项。', 'EVIDENCE_FOUND', '.md'),
        ('failed-one', '全部登录测试用例通过。', '共执行41项登录用例，成功40项，失败1项。', 'NONCONFORMING', '.docx'),
        ('os-deploy', '提供 Debian 13 部署说明。', 'Debian 13 部署说明：安装服务、配置参数、启动服务、验证健康状态。', 'EVIDENCE_FOUND', '.docx'),
        ('compound', '提供接口文档和部署说明。', '接口文档：端点 /sample。', 'PARTIAL_EVIDENCE', '.md'),
    ]
    observed = []
    scratch = Path.home() / 'AppData/Local/hermes/profiles/wb-developer/cache/scratch'
    with tempfile.TemporaryDirectory(prefix='acc016-preqa-', dir=scratch) as temporary:
        base = Path(temporary)
        with zipfile.ZipFile(archive) as zipped:
            names = zipped.namelist()
            assert zipped.testzip() is None and len(names) == len(set(names))
            assert all(n.startswith('wangbin-project-acceptance-check/') and '..' not in Path(n).parts for n in names)
            members = [{'path': n, 'sha256': hashlib.sha256(zipped.read(n)).hexdigest(), 'size': len(zipped.read(n))} for n in names]
            assert members == manifest['members'] and manifest['version'] == '0.1.5'
            assert manifest['sha256'] == sha and sidecar == f'{sha}  {archive.name}\n'
            zipped.extractall(base / 'extract')
        script = base / 'extract/wangbin-project-acceptance-check/scripts/check_acceptance.py'
        assert hashlib.sha256(script.read_bytes()).hexdigest() == next(m['sha256'] for m in members if m['path'].endswith('/scripts/check_acceptance.py'))
        for label, scope, material, expected, ext in cases:
            folder = base / label
            folder.mkdir()
            (folder / 'scope.md').write_text('R01：' + scope, encoding='utf-8')
            src = 'material' + ext
            if ext == '.docx':
                doc = Document()
                doc.add_paragraph('R01 ' + material)
                doc.save(folder / src)
            elif ext == '.xlsx':
                book = Workbook()
                book.active.append(['关联要求', '证据原文'])
                book.active.append(['R01', material])
                book.save(folder / src)
            else:
                (folder / src).write_text('R01 ' + material + '\n', encoding='utf-8')
            out = folder / 'out'
            out.mkdir()
            cmd = [sys.executable, str(script), '--project-name', '虚构项目', '--authorized-input-root', str(folder), '--output-dir', str(out), '--scope-source', 'scope.md', '--effective-version-ref', 'scope.md', '--evidence-source', src]
            env = os.environ.copy()
            env.pop('PYTHONPATH', None)
            p = subprocess.run(cmd, cwd=folder, env=env, capture_output=True, text=True, encoding='utf-8')
            assert p.returncode == 0, (label, p.returncode, p.stderr)
            snap = json.loads((out / '虚构项目-核查快照.json').read_text(encoding='utf-8'))
            req = snap['requirements'][0]
            book = load_workbook(out / '虚构项目-验收资料核对.xlsx', read_only=True)
            report = Document(out / '虚构项目-验收准备报告.docx')
            paragraphs = '\n'.join(x.text for x in report.paragraphs)
            sheetnames = book.sheetnames
            tracking_status = book['要求追踪']['H2'].value
            sheet_coverage = book['核查概览']['B2'].value
            gap_text = book['要求追踪']['K2'].value or ''
            comparison_text = book['要求追踪']['M2'].value or ''
            book.close()
            table_text = '\n'.join(c.text for table in report.tables for row in table.rows for c in row.cells)
            if label.startswith('omitted-'):
                assert req['results'][0]['pending'] and not req['results'][0]['support']
                assert any(src + '/' in source for gap in snap['findings'] for source in gap['sources'])
                assert '登录' in gap_text and src + '/' in comparison_text
                assert '登录' in table_text and src + '/' in table_text
            assert sheet_coverage == snap['coverage']
            assert len(sheetnames) == 6 and tracking_status == req['status']
            assert req['status'] in paragraphs and '已验收通过' not in paragraphs
            assert req['status'] == expected, (label, req['status'], expected)
            assert snap['coverage'] == ('1/2' if expected == 'PARTIAL_EVIDENCE' else '1/1' if expected == 'EVIDENCE_FOUND' else '0/1'), (label, snap['coverage'])
            assert req['results'][0]['sources'] and req['results'][0]['sources'][0].startswith(src + '/')
            observed.append({'id': label, 'input_type': ext, 'material': material, 'expected': expected, 'actual': req['status'], 'coverage': snap['coverage'], 'comparison': req['results'][0]['comparisons'], 'sources': req['results'][0]['sources'], 'gaps': snap['findings'], 'cmd': cmd, 'exit': p.returncode, 'input_sha256': {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()}, 'output_sha256': {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}, 'xlsx_sheets': sheetnames, 'xlsx_status': tracking_status, 'xlsx_coverage': sheet_coverage, 'xlsx_gap': gap_text, 'xlsx_comparison': comparison_text, 'docx_status': req['status'] in paragraphs})
    result = {'product_id': 'wangbin-project-acceptance-check', 'task_id': 't_cc77b45d', 'archive_sha256': sha, 'archive': str(archive), 'version': manifest['version'], 'members': members, 'python': sys.version.split()[0], 'case_count': len(observed), 'cases': observed, 'all_pass': True, 'scope': 'developer PRE-QA, not independent QA'}
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sha256': sha, 'case_count': len(observed), 'all_pass': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
