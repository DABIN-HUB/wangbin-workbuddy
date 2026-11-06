"""Local-only draft evaluation and extracted report checks; not a platform validator."""
import json
import sys
from pathlib import Path
from openpyxl import load_workbook

root = Path(__file__).parent / 'evaluation'
header = json.loads((root / 'header.json').read_text(encoding='utf-8'))
dims = {d['key'] for d in header['profile']['dimensions']}
assert sum(d['weight'] for d in header['profile']['dimensions']) == 1
cases = [json.loads(line) for line in (root / 'cases.jsonl').read_text(encoding='utf-8').splitlines() if line]
assert len(cases) == 4
for case in cases:
    assert {'case_name', 'user_question', 'expected', 'checklist_by_dim'} <= case.keys()
    assert set(case['checklist_by_dim']) == dims
    for file in case.get('input_files', []):
        rel = Path(file['rel'])
        assert rel.parts[0] == 'workspace' and '..' not in rel.parts
        assert (root / rel).is_file(), rel
receipt = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
assert receipt['status'] == 'PARTIAL'
assert (receipt['input_records'], receipt['findings'], receipt['affected_records'], receipt['duplicate_groups']) == (4, 4, 3, 1)
assert {(f['line'], f['category']) for f in receipt['finding_details']} == {(2, 'DUPLICATE_KEY'), (3, 'DUPLICATE_KEY'), (3, 'NOT_IN_REFERENCE'), (5, 'MISSING_REQUIRED_FIELD')}
report = Path(sys.argv[1])
assert Path(receipt['outputs']['report']).resolve() == report.resolve()
assert report.is_file()
wb = load_workbook(report, read_only=False, data_only=False)
assert wb.sheetnames == ['检查概览', '字段映射', '问题明细', '变更记录', '未检查项']
assert wb['问题明细'].max_row == 5
assert wb['变更记录'].max_row == 1
assert all(cell.data_type != 'f' for sheet in wb for row in sheet for cell in row)
print(f'LOCAL_EVAL_JSON_OK cases={len(cases)} input_files={sum(len(c.get("input_files", [])) for c in cases)}')
print(f'EXTRACTED_REPORT_OK sheets={len(wb.sheetnames)} findings={wb["问题明细"].max_row-1}')
