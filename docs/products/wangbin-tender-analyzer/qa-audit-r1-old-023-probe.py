"""Independent immutable 0.2.3 ZIP L3 baseline. Run with a Python containing openpyxl.
Only writes under the Hermes profile scratch directory; never loads source-tree code.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / 'dist/wangbin-tender-analyzer-0.2.3-skill-candidate.zip'
EXPECTED_HASH = '5ebba11d8a750d4807c88e715b5458a3cf449672f9b8dd5d7df3eb37d5c977ce'
SCRATCH = Path(os.environ['LOCALAPPDATA']) / 'hermes/profiles/wb-quality/cache/scratch/q06-old-023-t_f728459a-v5'
EXTRACT = SCRATCH / 'unpacked'
CASES = SCRATCH / 'cases'
SCRIPT = EXTRACT / 'wangbin-tender-analyzer/scripts/check_response.py'
LEGACY = EXTRACT / 'wangbin-tender-analyzer/scripts/analyze_tender.py'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return path


def run_case(label, tender, response=None, catalog=None, evidence=None, legacy=False):
    home = CASES / label
    home.mkdir(parents=True, exist_ok=True)
    t = fixture(home / 'requirement.txt', tender)
    r = fixture(home / 'reply.md', response) if response is not None else None
    out = home / 'result'
    out.mkdir()
    command = [sys.executable, str(LEGACY if legacy else SCRIPT)]
    if legacy:
        command += ['--input', str(t)]
    else:
        command += ['--tender', str(t), '--mode', 'check' if r else 'prepare', '--output-dir', str(out), '--project', label]
        if r:
            command += ['--response', str(r)]
        if catalog:
            if isinstance(catalog, (tuple, list)):
                c = home / 'catalog.xlsx'
                book = Workbook()
                sheet = book.active
                assert sheet is not None
                sheet.append(['附件名称', '关联要求编号'])
                for row in catalog:
                    sheet.append(list(row))
                book.save(c)
            else:
                c = fixture(home / 'catalog.csv', catalog)
            command += ['--attachment-catalog', str(c)]
        for i, (filename, content) in enumerate(evidence or []):
            p = fixture(home / ('evidence_' + str(i)) / filename, content)
            command += ['--evidence-file', str(p)]
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    proc = subprocess.run(command, cwd=EXTRACT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    record = {'case': label, 'command': command, 'cwd': str(EXTRACT), 'exit': proc.returncode,
              'stdout': proc.stdout, 'stderr': proc.stderr, 'inputs': {str(p.relative_to(home)): digest(p) for p in home.rglob('*') if p.is_file()}}
    if legacy:
        if proc.returncode == 0:
            record['legacy_json'] = json.loads(proc.stdout)
    else:
        paths = sorted(out.iterdir())
        record['outputs'] = {p.name: digest(p) for p in paths}
        xlsx = next((p for p in paths if p.suffix == '.xlsx'), None)
        md = next((p for p in paths if p.suffix == '.md'), None)
        if xlsx:
            book = load_workbook(xlsx, read_only=True, data_only=False, keep_links=False)
            record['sheets'] = {sheet.title: [[cell for cell in row] for row in sheet.values] for sheet in book}
            book.close()
        if md:
            record['md'] = md.read_text(encoding='utf-8')
    return record


def main():
    assert digest(ARCHIVE) == EXPECTED_HASH
    if SCRATCH.exists():
        raise RuntimeError('refusing to erase previous baseline; remove only this owned scratch directory manually')
    EXTRACT.mkdir(parents=True)
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert len(names) == len(set(names)) and all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
        z.extractall(EXTRACT)
        members = {n: hashlib.sha256(z.read(n)).hexdigest() for n in names}
    records = []
    add = lambda *args, **kw: records.append(run_case(*args, **kw))
    add('date_expired_2028', '1. 必须提供资质证书，资质有效期覆盖2028-01-01至2028-12-31。', '1. 我方提供资质证书certificate.txt，资质有效期覆盖2028-01-01至2028-12-31。', catalog='附件名称,关联要求编号\ncertificate.txt,1\n', evidence=[('certificate.txt', '资质证书：有效期2026-01-01至2027-12-31。')])
    add('date_signed_valid', '1. 必须提供资质证书，资质有效期覆盖2027-01-01至2027-12-31。', '1. 我方提供资质证书certificate.txt，资质有效期覆盖2027-01-01至2027-12-31。', catalog='附件名称,关联要求编号\ncertificate.txt,1\n', evidence=[('certificate.txt', '资质证书：2026年签发，有效期2026-06-01至2028-12-31。')])
    add('date_issue_only', '1. 必须提供资质证书，资质有效期覆盖2027-01-01至2027-12-31。', '1. 我方提供资质证书certificate.txt，资质有效期覆盖2027-01-01至2027-12-31。', catalog='附件名称,关联要求编号\ncertificate.txt,1\n', evidence=[('certificate.txt', '资质证书：签发日期为2026-06-01。')])
    add('date_two_certs', '1. 必须提供甲类资质证书，资质有效期覆盖2028-01-01至2028-12-31。', '1. 我方提供甲类资质证书certificate.txt，资质有效期覆盖2028-01-01至2028-12-31。', catalog='附件名称,关联要求编号\ncertificate.txt,1\n', evidence=[('certificate.txt', '甲类资质证书：有效期2026-01-01至2027-12-31。\n乙类资质证书：有效期2026-01-01至2030-12-31。')])
    add('date_shift_2032', '1. 必须提供资质证书，资质有效期覆盖2032-01-01至2032-12-31。', '1. 我方提供资质证书certificate.txt，资质有效期覆盖2032-01-01至2032-12-31。', catalog='附件名称,关联要求编号\ncertificate.txt,1\n', evidence=[('certificate.txt', '资质证书：有效期2030-01-01至2031-12-31。')])
    add('response_negated', '1. 必须支持自动备份。', '1. 我方不支持自动备份。')
    add('response_positive', '1. 必须支持自动备份。', '1. 我方支持自动备份。')
    add('response_double_negative', '1. 不使用外部云存储。', '1. 本方案不使用外部云存储。')
    add('response_conditional', '1. 必须支持自动备份。', '1. 若采购方另行采购模块，我方才支持自动备份。')
    add('license_missing', '1. 必须提供营业执照。', '1. 我方提供营业执照。')
    add('license_catalog_csv', '1. 必须提供营业执照。', '1. 我方提供营业执照。', catalog='附件名称,关联要求编号\n营业执照.txt,1\n')
    add('license_catalog_xlsx', '1. 必须提供营业执照。', '1. 我方提供营业执照。', catalog=[('营业执照.txt', '1')])
    add('license_actual', '1. 必须提供营业执照。', '1. 我方提供营业执照。', catalog='附件名称,关联要求编号\n营业执照.txt,1\n', evidence=[('营业执照.txt', '营业执照：统一社会信用代码为虚构示例。')])
    add('license_duplicate', '1. 必须提供营业执照。', '1. 我方提供营业执照。', catalog='附件名称,关联要求编号\n营业执照.txt,1\n营业执照.txt,1\n', evidence=[('营业执照.txt', '营业执照：虚构示例，仅为文本。')])
    add('filename_only', '1. 必须提供certificate.txt。', '1. 我方提供certificate.txt。', evidence=[('certificate.txt', '交付文档：本文件不含证书信息。')])
    add('filename_empty_conditions', '1. 必须提供certificate.txt。', '1. 我方提供certificate.txt。', catalog='附件名称,关联要求编号\ncertificate.txt,1\n', evidence=[('certificate.txt', 'certificate.txt：仅为目录占位，不含证书。')])
    add('legacy_json', '1. 必须提供营业执照。\n2. 必须支持自动备份。', legacy=True)
    example = EXTRACT / 'wangbin-tender-analyzer/examples/fictional-tender.txt'
    expected = EXTRACT / 'wangbin-tender-analyzer/examples/fictional-tender.expected.json'
    proc = subprocess.run([sys.executable, str(LEGACY), '--input', str(example)], cwd=EXTRACT,
                          env={k: v for k, v in os.environ.items() if k != 'PYTHONPATH'},
                          capture_output=True, text=True, timeout=60)
    sample_check = {'command': [sys.executable, str(LEGACY), '--input', str(example)], 'exit': proc.returncode,
                    'stderr': proc.stderr, 'expected_sha256': digest(expected),
                    'matches_expected_json': proc.returncode == 0 and json.loads(proc.stdout) == json.loads(expected.read_text(encoding='utf-8'))}
    payload = {'archive': str(ARCHIVE), 'sha256': EXPECTED_HASH, 'members_sha256': members, 'python': sys.executable,
               'cases': records, 'legacy_original_example': sample_check}
    location = SCRATCH / 'results.json'
    location.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    for rec in records:
        print(rec['case'], 'exit', rec['exit'], 'matrix', (rec.get('sheets', {}).get('要求响应矩阵') or [[], []])[1][9:14] if rec.get('sheets', {}).get('要求响应矩阵') else 'LEGACY/NO_OUTPUT', 'outputs', list(rec.get('outputs', {})))
    print('EVIDENCE', location)
    print('ORIGINAL_LEGACY_SNAPSHOT', sample_check)

if __name__ == '__main__':
    main()
