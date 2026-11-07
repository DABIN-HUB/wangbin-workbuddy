"""Read-only reproducible archive/version/source metadata checks."""
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath
import yaml

root = Path('F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check')
base = root / 'dist/wangbin-tender-analyzer-0.2.6-skill-candidate.zip'
manifest = json.loads(Path(str(base)+'.manifest.json').read_text(encoding='utf-8'))
sha = lambda data: hashlib.sha256(data).hexdigest()
archive_sha = sha(base.read_bytes())
assert archive_sha == manifest['sha256'] == '1c18b43f8cb465eb261ae4ccdc950259399f64b9c70477496809e3102dd4753a'
assert archive_sha in Path(str(base)+'.sha256').read_text(encoding='utf-8')
assert manifest['version'] == '0.2.6' and manifest['id'] == 'wangbin-tender-analyzer'
with zipfile.ZipFile(base) as z:
    assert z.testzip() is None
    names = z.namelist()
    assert names == [m['path'] for m in manifest['members']] and len(names) == len(set(names)) == 11
    for member in manifest['members']:
        name = member['path']
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in name
        assert name.startswith('wangbin-tender-analyzer/')
        data = z.read(name)
        assert len(data) == member['size'] and sha(data) == member['sha256']
        source = root / 'packages/skills' / name
        assert source.is_file() and sha(source.read_bytes()) == member['sha256']
        assert not any(token in name.lower() for token in ('/.git/', '/.env', 'private', '__pycache__'))
    skill = z.read('wangbin-tender-analyzer/SKILL.md').decode('utf-8')
    front = yaml.safe_load(skill.split('---', 2)[1])
    assert front['name'] == manifest['id'] and front['version'] == manifest['version']
    assert len(front['examples_zh']) == len(front['examples_en']) == 3
    assert 'openpyxl>=3.1,<4' in skill and '<解压目录>/wangbin-tender-analyzer/scripts/check_response.py' in skill
catalog = json.loads((root / 'products/catalog.json').read_text(encoding='utf-8'))
products = catalog if isinstance(catalog,list) else catalog.get('products',[])
product = next(p for p in products if p.get('id') == manifest['id'])
print(json.dumps({'archive_sha256':archive_sha,'version':manifest['version'],'members':len(manifest['members']),'examples_zh':len(front['examples_zh']),'examples_en':len(front['examples_en']),'catalog_active':product.get('active_version'),'catalog_candidate':product.get('candidate_version'),'catalog_keys':list(product)},ensure_ascii=False))
