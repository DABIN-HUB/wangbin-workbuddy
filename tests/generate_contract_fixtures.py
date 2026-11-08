"""Generate a bounded fictional DOCX pair from reviewed expected text; never overwrite files.

Run: python tests/generate_contract_fixtures.py --case core --output-dir dist/qa-synthetic/core
The JSON expected text is frozen data, NOT a claim that the implementation passes it.
"""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from docx import Document

EXPECTED = Path(__file__).resolve().parent / 'fixtures/contract-return.expected.json'
MATRIX = EXPECTED.with_name('contract-return.matrix.json')


def all_cases():
    old = json.loads(EXPECTED.read_text(encoding='utf-8'))['cases']
    new = json.loads(MATRIX.read_text(encoding='utf-8'))['cases']
    if set(old) & set(new):
        raise ValueError('fixture case name collision')
    return {**old, **new}


def mutate(path: Path, operation: str):
    if operation == 'invalid_bytes':
        path.write_bytes(b'not a docx')
    elif operation == 'oversize':
        # This fixture is deliberately over the frozen 10 MiB input boundary.
        path.write_bytes(b'x' * (10 * 1024 * 1024 + 1))
    elif operation == 'many_units':
        doc = Document(str(path))
        paragraph = doc.paragraphs[0]._p
        parent = paragraph.getparent()
        from copy import deepcopy
        for _ in range(2001):
            parent.append(deepcopy(paragraph))
        doc.save(str(path))
    elif operation == 'long_text':
        doc = Document(str(path))
        doc.add_paragraph('甲' * 100001)
        doc.save(str(path))
    else:
        with ZipFile(path) as archive:
            parts = {member.filename: archive.read(member.filename) for member in archive.infolist()}
        xml = parts['word/document.xml']
        if operation == 'revision_insert':
            xml = xml.replace(b'</w:p>', b'<w:ins w:id="1"/></w:p>', 1)
        elif operation == 'drawing':
            xml = xml.replace(b'</w:p>', b'<w:drawing/></w:p>', 1)
        elif operation == 'textbox':
            xml = xml.replace(b'</w:p>', b'<w:pict><v:shape xmlns:v="urn:schemas-microsoft-com:vml"><v:textbox/></v:shape></w:pict></w:p>', 1)
        elif operation == 'xml_entity':
            xml = b'<!DOCTYPE document [<!ENTITY bad SYSTEM "file:///fictional">]>' + xml
        elif operation != 'zip_traversal':
            raise ValueError(f'unsupported fictional mutation: {operation}')
        parts['word/document.xml'] = xml
        with ZipFile(path, 'w') as archive:
            for name, payload in parts.items():
                archive.writestr(name, payload)
            if operation == 'zip_traversal':
                archive.writestr('../escape', b'fictional')


def generate(case: str, directory: Path) -> dict:
    cases = all_cases()
    if case not in cases:
        raise ValueError(f'unknown fictional case: {case}')
    spec = cases[case]
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    paths = {role: directory / f'{role}.docx' for role in ('original', 'returned')}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('refusing to overwrite synthetic input; choose a fresh directory')
    for role, path in paths.items():
        if role == 'original' and 'invalid_original_bytes' in spec:
            with path.open('xb') as stream:
                stream.write(spec['invalid_original_bytes'].encode('ascii'))
            continue
        doc = Document()
        for text in spec[role]:
            doc.add_paragraph(text)
        rows = spec.get(f'{role}_table', spec.get('table'))
        if rows:
            table = doc.add_table(rows=0, cols=len(rows[0]))
            for row in rows:
                cells = table.add_row().cells
                for cell, text in zip(cells, row):
                    cell.text = text
        doc.save(str(path))
        if role in spec.get('mutations', {}):
            mutate(path, spec['mutations'][role])
    return {role: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            for role, path in paths.items()}


def main():
    parser = argparse.ArgumentParser(description='create a fresh synthetic DOCX pair for local testing')
    parser.add_argument('--case', choices=tuple(all_cases()), required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({'case': args.case, 'files': generate(args.case, args.output_dir)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
