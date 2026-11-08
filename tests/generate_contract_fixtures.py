"""Generate a bounded fictional DOCX pair from reviewed expected text; never overwrite files.

Run: python tests/generate_contract_fixtures.py --case core --output-dir dist/qa-synthetic/core
The JSON expected text is frozen data, NOT a claim that the implementation passes it.
"""
import argparse
import hashlib
import json
from pathlib import Path
from docx import Document

EXPECTED = Path(__file__).resolve().parent / 'fixtures/contract-return.expected.json'


def generate(case: str, directory: Path) -> dict:
    cases = json.loads(EXPECTED.read_text(encoding='utf-8'))['cases']
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
        if 'table' in spec:
            rows = spec['table']
            table = doc.add_table(rows=0, cols=len(rows[0]))
            for row in rows:
                cells = table.add_row().cells
                for cell, text in zip(cells, row):
                    cell.text = text
        doc.save(str(path))
    return {role: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            for role, path in paths.items()}


def main():
    parser = argparse.ArgumentParser(description='create a fresh synthetic DOCX pair for local testing')
    parser.add_argument('--case', choices=tuple(json.loads(EXPECTED.read_text(encoding='utf-8'))['cases']), required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({'case': args.case, 'files': generate(args.case, args.output_dir)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
