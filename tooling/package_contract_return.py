"""Single-product deterministic local packager/validator; never includes contracts or QA data.

python tooling/package_contract_return.py validate
python tooling/package_contract_return.py package --output dist/qa-synthetic/contract-return-safe.zip
python tooling/package_contract_return.py verify --output dist/qa-synthetic/contract-return-safe.zip
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
NAME = 'wangbin-contract-return-check'
SOURCE = ROOT / 'packages' / 'skills' / NAME
MEMBERS = ('SKILL.md', 'manifest.json', 'scripts/compare_contracts.py')
STAMP = (1980, 1, 1, 0, 0, 0)


def checked_source(relative):
    path = SOURCE / relative
    if any(p.is_symlink() or (p.exists() and (stat.S_ISLNK(p.lstat().st_mode) or (hasattr(p, 'is_junction') and p.is_junction()))) for p in (path, *path.parents)):
        raise ValueError('linked input path forbidden')
    if not path.is_file() or path.resolve() != path.absolute():
        raise ValueError(f'bad source member {relative}')
    return path.read_bytes()


def validate():
    data = {p: checked_source(p) for p in MEMBERS}
    manifest = json.loads(data['manifest.json'].decode('utf-8'))
    catalog = json.loads((ROOT / 'products/catalog.json').read_text(encoding='utf-8'))
    if len(catalog['products']) != 1 or catalog['products'][0]['id'] != NAME:
        raise ValueError('catalog is not isolated to this product')
    entry = catalog['products'][0]
    version = manifest['version']
    text = data['SKILL.md'].decode('utf-8')
    for key, value in {'name': NAME, 'version': version, 'display_name_en': 'Returned Contract Change Check'}.items():
        if not re.search(r'^' + key + r':\s*' + re.escape(value) + r'\s*$', text, re.M):
            raise ValueError(f'SKILL metadata mismatch: {key}')
    if manifest['id'] != NAME or version != '0.1.5' or entry['active_version'] != version:
        raise ValueError('manifest/catalog id or version mismatch')
    if set(manifest['runtime_dependencies']) != {'python-docx>=1.2,<2', 'openpyxl>=3.1,<4', 'defusedxml>=0.7,<1'}:
        raise ValueError('runtime requirements drift')
    requirements = (ROOT / 'requirements.txt').read_text(encoding='utf-8').splitlines()
    if set(requirements) != set(manifest['runtime_dependencies']):
        raise ValueError('requirements mismatch')
    versions = entry['versions']
    if [v['version'] for v in versions] != ['0.1.0', '0.1.1', '0.1.2', '0.1.3', '0.1.4', '0.1.5']:
        raise ValueError('history metadata drift')
    if any(v['candidate'] != 'UNKNOWN' or v['sha256'] != 'UNKNOWN' for v in versions):
        raise ValueError('excluded historical candidate referenced')
    return data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(path, source=None):
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('archive CRC mismatch')
        infos = archive.infolist()
        expected = [f'{NAME}/{member}' for member in MEMBERS]
        if [info.filename for info in infos] != expected:
            raise ValueError('unexpected or missing ZIP member')
        if any(info.date_time != STAMP or info.is_dir() for info in infos):
            raise ValueError('non-deterministic archive metadata')
        measured = {}
        for info, member in zip(infos, MEMBERS):
            payload = archive.read(info)
            if len(payload) != info.file_size or (source is not None and payload != source[member]):
                raise ValueError('length or source mismatch')
            measured[member] = {'length': len(payload), 'sha256': sha(payload)}
    return {'zip_sha256': sha(path.read_bytes()), 'members': measured}


def package(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError('refusing to overwrite any existing archive')
    created = False
    try:
        with path.open('xb') as target:
            created = True
            with ZipFile(target, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
                for member in MEMBERS:
                    info = ZipInfo(f'{NAME}/{member}', date_time=STAMP)
                    info.compress_type = ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, data[member], compress_type=ZIP_DEFLATED, compresslevel=9)
        return verify(path, data)
    except Exception:
        if created:
            path.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description='minimal isolated Q03 archive check')
    parser.add_argument('action', choices=['validate', 'package', 'verify'])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    data = validate()
    if args.action == 'validate':
        print(json.dumps({'status': 'VALID', 'id': NAME, 'source_sha256': {p: sha(b) for p, b in data.items()}}, ensure_ascii=False, indent=2))
        return
    if args.output is None:
        parser.error('--output required for package/verify')
    result = package(args.output, data) if args.action == 'package' else verify(args.output, data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
