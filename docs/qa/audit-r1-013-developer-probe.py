"""Developer L3 check of a clean immutable acceptance candidate (fictional input only).

Run with isolated Python 3.11 + python-docx/openpyxl, passing ZIP and authorized scratch dir.
Never imports from the repository source tree.
"""
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from docx import Document
from openpyxl import load_workbook


def main():
    archive, root = map(Path, sys.argv[1:])
    assert not root.exists(), 'choose a new clean scratch directory'
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        names = zipped.namelist()
        assert len(names) == len(set(names))
        assert all(name.startswith('wangbin-project-acceptance-check/') and '..' not in Path(name).parts for name in names)
        root.mkdir(parents=True)
        zipped.extractall(root)
    script = root / 'wangbin-project-acceptance-check/scripts/check_acceptance.py'
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    cases = [
        ('low-colon', '同一测试场景下至少支持10000个并发登录。', '同一测试场景下实测最大支持10个并发登录。', 'evidence', 'NONCONFORMING', True),
        ('high-space', '同一测试场景下至少支持10000个并发登录。', '同一测试场景下实测最大支持12000个并发登录。', 'evidence', 'EVIDENCE_FOUND', False),
        ('other-os', '提供 Fedora 40 部署说明。', 'Ubuntu 22.04 部署说明：安装软件配置端口启动服务验证健康状态。', 'delivery', 'NO_EVIDENCE_FOUND', False),
        ('right-os', '提供 Fedora 40 部署说明。', 'Fedora 40 部署说明：安装软件配置端口启动服务验证健康状态。', 'delivery', 'EVIDENCE_FOUND', False),
        ('zero-failed', '全部登录测试用例通过。', '共执行37项登录用例，成功37项，失败0项。', 'evidence', 'EVIDENCE_FOUND', False),
        ('one-failed', '全部登录测试用例通过。', '共执行37项登录用例，成功36项，失败1项。', 'evidence', 'NONCONFORMING', False),
        ('scope-unknown', '全部登录测试用例通过。', '未发现失败。', 'evidence', 'PENDING_CONFIRMATION', False),
    ]
    observed = []
    for label, scope, material, role, expected, colon in cases:
        folder = root / label
        folder.mkdir()
        (folder / 'scope.md').write_text('R01：' + scope, encoding='utf-8')
        (folder / 'material.md').write_text(('R01：' if colon else 'R01 ') + material, encoding='utf-8')
        out = folder / 'out'
        out.mkdir()
        cmd = [sys.executable, str(script), '--project-name', '虚构项目', '--authorized-input-root', str(folder),
               '--output-dir', str(out), '--scope-source', 'scope.md', '--effective-version-ref', 'scope.md',
               '--delivery-source' if role == 'delivery' else '--evidence-source', 'material.md']
        process = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
        assert process.returncode == 0, (label, process.stderr)
        snap = json.loads((out / '虚构项目-核查快照.json').read_text(encoding='utf-8'))
        req = snap['requirements'][0]
        assert req['status'] == expected, (label, req['status'], expected)
        assert req['results'][0]['sources'] == (['material.md/行1'] if expected != 'NO_EVIDENCE_FOUND' else [])
        workbook = load_workbook(out / '虚构项目-验收资料核对.xlsx', read_only=True)
        doc = Document(str(out / '虚构项目-验收准备报告.docx'))
        assert len(workbook.sheetnames) == 6
        assert workbook['要求追踪']['H2'].value == expected
        assert expected in '\n'.join(p.text for p in doc.paragraphs)
        assert req['source'] in ' '.join(c.text for row in doc.tables[0].rows for c in row.cells)
        workbook.close()
        observed.append({'case': label, 'exit': process.returncode, 'expected': expected, 'actual': req['status'],
                         'coverage': snap['coverage'], 'source': req['results'][0]['sources'],
                         'comparison': req['results'][0]['comparisons']})
    print(json.dumps({'archive_sha256': digest, 'python': sys.version.split()[0], 'case_count': len(observed),
                      'cases': observed}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
