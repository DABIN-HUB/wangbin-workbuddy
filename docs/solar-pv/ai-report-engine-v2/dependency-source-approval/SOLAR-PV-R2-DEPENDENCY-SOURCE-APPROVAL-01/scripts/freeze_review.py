"""Freeze exact review allowlists and a directory payload, never a ZIP.

Sources are bounded to the prior 129-file approved inventory, this task's
explicit docs/candidates, source analyst's sharing allowlist, and selected
license/manager evidence. Original public raw metadata stays local-only.
"""
import argparse
import ast
from collections import Counter
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys

HERE = Path(__file__).resolve().parent
R = HERE.parents[5]
D = HERE.parent
TASK = D.name
U = R / '.runtime/solar-pv' / TASK
OLD = R / '.runtime/solar-pv/SOLAR-PV-R2-ENGINE-ARTIFACT-01'
BASE = '177951690bab2f0a11a75be15e2204be4820409c'
H = lambda b: hashlib.sha256(b).hexdigest()
EMAIL = re.compile(r'[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
USERPATH = re.compile(r'C:[/\\]+Users[/\\]+[^/\\\s"<>]+', re.I)
SECRET = re.compile(r'''(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|private[_-]?key|password)\b\s*[:=]\s*["']([^"']+)["']''')
SAFE = {'', 'example', 'changeme', 'your-token', 'your_api_key', '${service_token}', '[redacted]'}


def load(p):
    return json.loads(p.read_bytes())


def identity(path, data=None):
    b = path.read_bytes() if data is None else data
    return {'path': path.relative_to(R).as_posix(), 'bytes': len(b), 'sha256': H(b)}


def output(path, obj):
    with path.open('x', encoding='utf8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=True, indent=2)
        f.write('\n')


def redact(value):
    if isinstance(value, str):
        return USERPATH.sub('[LOCAL_USER_HOME]', EMAIL.sub('[REDACTED_PUBLIC_EMAIL]', value))
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', default='')
    args = parser.parse_args()
    if args.revision and not re.fullmatch('[a-z0-9-]+', args.revision):
        raise ValueError('PATH_FREE_REVISION_REQUIRED')
    suffix = '.' + args.revision if args.revision else ''
    payload = U / ('review-payload' + suffix)
    privacy_path = U / ('developer-privacy-findings' + suffix + '.json')
    index_path = U / ('developer-freeze-index' + suffix + '.json')
    if payload.exists():
        raise ValueError('NO_CLOBBER_PAYLOAD')
    payload.mkdir()
    entries, destinations, findings = [], set(), []

    def add(path, destination, purpose, derivative=False):
        path = Path(path)
        p = PurePosixPath(destination)
        if p.is_absolute() or '..' in p.parts or destination in destinations:
            raise ValueError('UNSAFE_OR_DUPLICATE_PAYLOAD_DESTINATION')
        assert path.is_file() and not path.is_symlink()
        original = path.read_bytes()
        data = original
        if derivative:
            if path.suffix.lower() == '.json':
                data = (json.dumps(redact(json.loads(original)), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf8')
            else:
                data = redact(original.decode('utf8')).encode('utf8')
        target = payload / p
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(data)
        destinations.add(destination)
        entries.append({'path': destination, 'bytes': len(data), 'sha256': H(data), 'purpose': purpose,
                        'source': identity(path, original), 'source_head': BASE,
                        'identity': 'PRIVACY_REDACTED_DERIVATIVE_NOT_RAW' if derivative else 'EXACT_SOURCE_BYTES',
                        'redaction': 'public emails/home path; JSON canonical reserialization' if derivative else 'NONE'})
        text = data.decode('utf8', errors='replace')
        for kind, pattern in [('EMAIL', EMAIL), ('LOCAL_HOME', USERPATH), ('SECRET_PATTERN', SECRET),
                               ('PRIVATE_KEY', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'))]:
            for match in pattern.finditer(text):
                if kind == 'SECRET_PATTERN' and match.group(1).strip().lower() in SAFE:
                    continue
                findings.append({'path': destination, 'file_sha256': H(data), 'kind': kind,
                                 'line': text.count('\n', 0, match.start()) + 1, 'matched_value_sha256': H(match.group(0).encode('utf8'))})
    required = {'PLAN.md','RESULT.md','BASELINE_AND_ARTIFACT_IDENTITY.md','TARGET_RUNTIME_MATRIX.md',
                'DEPENDENCY_SOURCE_MATRIX.csv','THIRD_PARTY_LICENSE_MATRIX.md','DEPENDENCY_RESOLUTION.json',
                'CANDIDATE_LOCK.json','WHEELHOUSE_AND_INSTALL_PLAN.md','DOCUMENT_CLI_ARTIFACT_IDENTITY.md',
                'QUALITY_REPORT.md','NEXT_GATE.md'}
    assert required <= {p.name for p in D.iterdir() if p.is_file()}
    ast_paths = []
    for path in sorted(D.rglob('*')):
        if path.is_file():
            if path.suffix == '.py':
                ast.parse(path.read_text(encoding='utf8'), filename=str(path))
                ast_paths.append(path.relative_to(R).as_posix())
            add(path, 'docs/' + path.relative_to(D).as_posix(), 'CURRENT_FORMAL_DOC_OR_AUDIT_SCRIPT')
    rows = list(csv.DictReader(io.StringIO((D / 'DEPENDENCY_SOURCE_MATRIX.csv').read_text(encoding='utf8'))))
    assert len(rows) == 504 and set(Counter(r['target'] for r in rows).values()) == {42}
    candidate = load(U / 'candidate/CANDIDATE_LOCK.full.json')
    manifest = load(D / 'CANDIDATE_LOCK.json')
    assert manifest['full_candidate'] == identity(U / 'candidate/CANDIDATE_LOCK.full.json')
    assert manifest['download_plan'] == identity(U / 'candidate/download-plan.json')
    source_snapshot = load(OLD / 'snapshot-files.json')
    for name, row in source_snapshot.items():
        path = R / row['source_path']
        b = path.read_bytes()
        assert len(b) == row['bytes'] and H(b) == row['sha256']
        add(path, 'approved-source/' + row['source_path'], 'APPROVED_129_SOURCE_IDENTITY_UNCHANGED')
    assert len(source_snapshot) == 129
    shared = load(U / 'source-research/sharing-index.final.json')
    assert len(shared['files']) == 185
    for row in shared['files']:
        path = Path(row['path'])
        b = path.read_bytes()
        assert len(b) == row['bytes'] and H(b) == row['sha256']
        add(path, 'evidence/source/' + path.relative_to(U / 'source-research').as_posix(), 'SOURCE_ANALYST_APPROVED_SHARING_DERIVATIVE')
    add(U / 'source-research/sharing-index.final.json', 'evidence/source/sharing-index.final.json', 'SOURCE_SHARING_ORIGINAL_INDEX')
    for path in sorted((U / 'candidate').iterdir()):
        if path.is_file():
            add(path, 'candidate/' + path.name, 'GENERATED_MACHINE_CANDIDATE_NOT_INSTALLABLE')
    # Selected license bodies are already explicit derivatives; never copy whole raw directories.
    license_dir = U / 'license-identity'
    selected = ['LICENSE_IDENTITY_REPORT.md', 'license-matrix.json', 'license-matrix.md',
                'shared-official-sources.json', 'document-identity.json', 'external-resource-plan.json',
                'historical-input-identities.json', 'final-evidence-verification.json']
    for name in selected:
        add(license_dir / name, 'evidence/license/' + name, 'LICENSE_IDENTITY_RESOURCE_EVIDENCE', derivative=True)
    license_sources = load(license_dir / 'shared-official-sources.json')
    body_paths = set()
    for req in license_sources['requests']:
        row = req.get('shared_derivative')
        if row:
            path = Path(row['path'])
            if path in body_paths:
                continue
            assert H(path.read_bytes()) == row['sha256']
            body_paths.add(path)
            add(path, 'evidence/license/texts/' + path.name, 'PUBLIC_LICENSE_TEXT_DERIVATIVE_NOT_LEGAL_NOTICE', derivative=True)
    for name in ['manager-preflight-summary.json','manager-target-runtime.json', 'manager-reused-source-document-binding.json',
                 'manager-analyst-readback.json', 'manager-official-docs-index.json']:
        add(U / name, 'evidence/manager/' + name, 'MANAGER_READBACK_NOT_INDEPENDENT_QA', derivative=True)
    for row in load(U / 'manager-official-docs-index.json'):
        path = R / row['body_path']
        assert row['status'] == 200 and H(path.read_bytes()) == row['sha256']
        add(path, 'evidence/official-docs/' + path.name, 'OFFICIAL_DOCUMENT_NOT_INSTALL_SCRIPT', derivative=True)
    # Existing prior documents are protected; share privacy derivatives with original identities.
    for row in load(U / 'manager-reused-source-document-binding.json')['old_docs']:
        add(R / row['path'], 'evidence/previous-docs/' + Path(row['path']).name, 'PRIOR_APPROVED_DOCUMENT_IDENTITY', derivative=True)
    # Preserve evidence locally; allow only minimal receipts as future sharing derivatives.
    for path in sorted((U / 'commands').glob('developer-*.json')):
        add(path, 'evidence/developer-commands/' + path.name, 'DEVELOPER_SELF_CHECK_RECEIPT_NOT_QA', derivative=True)
    output(privacy_path, {'schema': 'task-payload-privacy-scan/1', 'files': len(entries),
                                                  'findings': findings, 'raw_inputs_excluded': True,
                                                  'scanner_scope': 'EXACT_ALLOWLIST_PAYLOAD_ONLY_NO_GLOBAL_SECRET_DISCOVERY'})
    index = {'schema': 'frozen-source-doc-evidence-allowlist/1', 'source_head': BASE,
             'scope': 'CANDIDATE_PENDING_INDEPENDENT_QA_NOT_ZIP_NOT_INSTALLABLE',
             'files': sorted(entries, key=lambda e: e['path']), 'payload_count': len(entries),
             'payload_bytes': sum(e['bytes'] for e in entries),
             'tree_sha256': H(b''.join(e['path'].encode('utf8') + b'\0' + e['sha256'].encode('ascii') + b'\n' for e in sorted(entries, key=lambda e: e['path']))),
             'local_only_inputs': [identity(U / 'frozen-inputs.json')],
             'local_raw_evidence': 'source raw/response metadata and original license sources remain in RUN, excluded from sharing; QA reads actual originals locally',
             'not_included': ['.env/credentials/models', 'venvs/caches', 'unredacted raw', 'historical assets/wheels/dist', 'quality output not yet produced'],
             'source_files_count': len(source_snapshot), 'source_sharing_original_count': len(shared['files']),
             'license_derivative_bodies': len(body_paths), 'ast_checked_scripts': ast_paths,
             'csv_rows': len(rows), 'independent_qa': 'NOT_RUN',
             'review_payload_directory': payload.relative_to(R).as_posix(), 'archive_created': False,
             'privacy_report': identity(privacy_path)}
    output(index_path, index)
    print(json.dumps({'index': identity(index_path), 'payload_count': len(entries),
                      'tree_sha256': index['tree_sha256'], 'privacy_findings': len(findings), 'ast_scripts': len(ast_paths), 'csv_rows': len(rows)}))
    if findings:
        raise SystemExit('PAYLOAD_REQUIRES_FINDING_TRIAGE_NO_QA_APPROVAL')


if __name__ == '__main__':
    main()
