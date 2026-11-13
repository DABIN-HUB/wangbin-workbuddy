"""Offline candidate generator and fail-closed validator. No acquisition/install code.

The immutable input capsule is LOCAL ONLY (original public metadata may contain
contacts). Candidate verification rebuilds pins, file choices and graph from its
bytes, not from candidate flags, candidate edges, or a pre-filled expected result.
Python 3.12+; existing packaging required. Exit 0 = research integrity only.
"""
import argparse
import base64
from collections import defaultdict
from email.parser import BytesParser
from email.policy import default
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import cpython_tags, compatible_tags
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import Version

TASK = 'SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01'
BASE = '177951690bab2f0a11a75be15e2204be4820409c'
ANCHOR_SHA = '171656d7edd77345ba25edc333c2450db000dbbc38fdd30242531ecbad19f5e9'
U = '.runtime/solar-pv/' + TASK + '/'
OLD = '.runtime/solar-pv/SOLAR-PV-R2-ENGINE-ARTIFACT-01/'
SCHEMA = 'solar-pv-dependency-candidate/1'
EMAIL = re.compile(r'[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf8')


def clean(obj):
    if isinstance(obj, str):
        return EMAIL.sub('[REDACTED_PUBLIC_EMAIL]', obj)
    if isinstance(obj, list):
        return [clean(v) for v in obj]
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    return obj


def capsule(path):
    data = Path(path).read_bytes()
    if digest(data) != ANCHOR_SHA:
        raise ValueError('FROZEN_INPUT_CAPSULE_IDENTITY_MISMATCH')
    records = json.loads(data)['items']
    result = {}
    for name, row in records.items():
        b = base64.b64decode(row['base64'], validate=True)
        if len(b) != row['bytes'] or digest(b) != row['sha256']:
            raise ValueError('FROZEN_ITEM_IDENTITY_MISMATCH: ' + name)
        result[name] = b
    return result, [{'path': k, 'bytes': len(v), 'sha256': digest(v)} for k, v in sorted(result.items())]


def rp_ok(text, python):
    return not text or SpecifierSet(text).contains(python, prereleases=True)


def platform_condition(platform, target):
    if platform == 'any':
        return {'family': 'any', 'minimum': [], 'conditional': False}
    if target.startswith('Windows'):
        return {'family': 'windows', 'minimum': [], 'conditional': False} if platform == 'win_amd64' else None
    if target.startswith('Linux'):
        legacy = {'manylinux1_x86_64': [2, 5], 'manylinux2010_x86_64': [2, 12], 'manylinux2014_x86_64': [2, 17]}
        m = re.fullmatch(r'manylinux_(\d+)_(\d+)_x86_64', platform)
        minimum = list(map(int, m.groups())) if m else legacy.get(platform)
        return {'family': 'glibc', 'minimum': minimum, 'conditional': True} if minimum else None
    m = re.fullmatch(r'macosx_(\d+)_(\d+)_(x86_64|arm64|universal2)', platform)
    if not m:
        return None
    major, minor, arch = m.groups()
    arm = 'arm64' in target
    if arch not in ({'arm64', 'universal2'} if arm else {'x86_64', 'universal2'}):
        return None
    minimum = [int(major), int(minor)]
    if arm:
        minimum = max(minimum, [11, 0])
    return {'family': 'macos', 'minimum': minimum, 'conditional': True}


@lru_cache(maxsize=2000)
def allowed_tags(minor, platform):
    return {str(t) for t in cpython_tags((3, minor), abis=['cp3' + str(minor)], platforms=[platform])} | {
        str(t) for t in compatible_tags((3, minor), interpreter='cp3' + str(minor), platforms=[platform])}


def assess(file, target, env, info):
    reasons, matches = [], []
    if file['yanked']:
        reasons.append('YANKED')
    if not re.fullmatch('[0-9a-f]{64}', file['sha256'] or ''):
        reasons.append('OFFICIAL_SHA256_MISSING')
    for text in (info.get('requires_python'), file.get('requires_python')):
        if not rp_ok(text, env['python_full_version']):
            reasons.append('REQUIRES_PYTHON')
    for tag in file['tags']:
        _, _, platform = tag.split('-', 2)
        if tag not in allowed_tags(int(env['python_version'].split('.')[1]), platform):
            continue
        condition = platform_condition(platform, target)
        if condition is not None:
            matches.append({'tag': tag, **condition})
    if not matches:
        reasons.append('PYTHON_ABI_PLATFORM_LIBC_INCOMPATIBLE')
    best = min(matches, key=lambda m: (m['family'] != 'any', m['minimum'], 'abi3' not in m['tag'], m['tag'])) if matches else None
    return reasons, best


def rank(option):
    file, condition = option
    return condition['family'] != 'any', condition['minimum'], 'abi3' not in condition['tag'], file['filename']


def release_files(info, urls, source):
    result = []
    for row in urls:
        if row['packagetype'] != 'bdist_wheel':
            continue
        name, version, _, tags = parse_wheel_filename(row['filename'])
        if canonicalize_name(info['name']) != name or Version(info['version']) != version:
            raise ValueError('OFFICIAL_FILENAME_IDENTITY_MISMATCH')
        loc = urlsplit(row['url'])
        if loc.scheme != 'https' or loc.hostname != 'files.pythonhosted.org' or loc.username or loc.password:
            raise ValueError('UNKNOWN_OFFICIAL_FILE_SOURCE')
        result.append({'name': name, 'version': str(version), 'filename': row['filename'], 'url': row['url'],
                       'sha256': row['digests']['sha256'], 'size': row['size'], 'tags': sorted(map(str, tags)),
                       'requires_python': row.get('requires_python'), 'upload_time': row.get('upload_time_iso_8601'),
                       'yanked': bool(row.get('yanked')), 'yanked_reason': row.get('yanked_reason'), 'official_source': source})
    return result


def metadata(msg):
    return {'name': canonicalize_name(msg['Name']), 'version': msg['Version'],
            'requires_python': msg.get('Requires-Python'), 'requires_dist': msg.get_all('Requires-Dist', []),
            'provides_extra': msg.get_all('Provides-Extra', [])}


def graph(pins, metas, root, env):
    reached, extras = {root}, defaultdict(set)
    for iteration in range(200):
        before = (len(reached), sum(map(len, extras.values())))
        for parent in sorted(reached.copy()):
            for raw in metas[parent]['requires_dist'] or []:
                req = Requirement(raw)
                if req.marker and not any(req.marker.evaluate({**env, 'extra': e}) for e in [''] + sorted(extras[parent])):
                    continue
                name = canonicalize_name(req.name)
                if name in pins:
                    reached.add(name)
                    extras[name].update(req.extras)
        if before == (len(reached), sum(map(len, extras.values()))):
            break
    else:
        raise ValueError('FIXED_POINT_BOUND_EXCEEDED')
    edges, issues = [], []
    for parent in sorted(reached):
        meta = metas[parent]
        if meta.get('requires_dist') is None:
            issues.append({'package': parent, 'reason': 'UNKNOWN_REQUIRES_DIST'})
        if not rp_ok(meta.get('requires_python'), env['python_full_version']):
            issues.append({'package': parent, 'reason': 'REQUIRES_PYTHON'})
        unknown = extras[parent] - set(meta.get('provides_extra') or [])
        if unknown:
            issues.append({'package': parent, 'reason': 'UNDEFINED_EXTRA', 'extras': sorted(unknown)})
        for raw in meta['requires_dist'] or []:
            req = Requirement(raw)
            values = {e: not req.marker or req.marker.evaluate({**env, 'extra': e}) for e in [''] + sorted(extras[parent])}
            dep = canonicalize_name(req.name)
            active = any(values.values())
            satisfied = dep in pins and req.specifier.contains(pins[dep], prereleases=True) and not req.url
            edge = {'from': parent, 'to': dep, 'raw': raw, 'specifier': str(req.specifier),
                    'extras': sorted(req.extras), 'marker': str(req.marker) if req.marker else None,
                    'contexts': values, 'active': active, 'constraint_satisfied': bool(satisfied) if active else None}
            edges.append(edge)
            if active and not satisfied:
                issues.append({'from': parent, 'to': dep, 'reason': 'MISSING_OR_CONFLICTING_TRANSITIVE_REQUIREMENT', 'raw': raw})
    return {'reached': sorted(reached), 'extras': {k: sorted(v) for k, v in sorted(extras.items()) if v},
            'edges': edges, 'issues': issues}


def rebuild(path):
    inputs, identities = capsule(path)
    load = lambda name: json.loads(inputs[name])
    observed = load(U + 'source-research/observed-inputs.json')
    original = load(OLD + 'analyst/dependency-closure.json')
    binding = load(OLD + 'final-wheel-binding.json')
    licenses = load(U + 'license-identity/license-matrix.json')
    docs = load(U + 'license-identity/document-identity.json')
    runtime = load(U + 'manager-target-runtime.json')
    # Reconcile all twelve historical graphs, not just a convenient first graph.
    for old, derived in zip(original['matrices'], observed['matrices'], strict=True):
        oldpins = {(n['name'], n['selected_observed_version']) for n in old['nodes']}
        assert old['id'] == derived['id'] and old['marker_environment'] == derived['marker_environment']
        assert oldpins == {(n['name'], n['version']) for n in derived['nodes']}
        assert set(next(b for b in binding['matrices'] if b['id'] == old['id'])['remaining_missing_names']) == {
            n['name'] for n in derived['nodes'] if n['missing_third_party']}
    releases, pep = {}, {}
    prefix = U + 'source-research/official-metadata/raw/'
    for name, b in inputs.items():
        if name.startswith(prefix):
            raw = json.loads(b)
            info = raw['info']
            key = canonicalize_name(info['name']) + '==' + info['version']
            source = 'https://pypi.org/pypi/' + key.replace('==', '/') + '/json'
            assert name.rsplit('/', 1)[1] == key.replace('==', '--') + '.body'
            releases[key] = {'info': info, 'files': release_files(info, raw['urls'], source), 'source': source}
        elif name.startswith(U + 'source-research/pep658/raw/'):
            msg = BytesParser(policy=default).parsebytes(b)
            fn = Path(name).name
            # Raw filenames are the wheel filename plus .metadata.body (index resolves exact spelling).
            pep[fn] = metadata(msg)
    pep_index = load(U + 'source-research/shared/pep658-metadata-index.json')
    byfile = {}
    pep_sources = {}
    for row in pep_index:
        rawpath = row['raw_identity']['path'].replace('\\', '/')
        relative = rawpath[rawpath.index('.runtime/'):]
        assert row['http_status'] == 200 and digest(inputs[relative]) == row['raw_identity']['sha256']
        byfile[row['filename']] = metadata(BytesParser(policy=default).parsebytes(inputs[relative]))
        pep_sources[row['filename']] = {'kind': 'PEP658_METADATA_NOT_WHEEL', 'url': row['source_url'],
                                      'sha256': row['raw_identity']['sha256'], 'index_expected_digest_verified': False}
    license_bykey = {d['name'] + '==' + v['version']: v for d in licenses['dependencies'] for v in d['versions']}
    variants, allfiles, targets, nodes = {}, {}, [], {}
    root = binding['name']
    for matrix in observed['matrices']:
        tid, env = matrix['id'], matrix['marker_environment']
        pins = {n['name']: n['version'] for n in matrix['nodes']}
        metas, target_nodes = {}, []
        for n in matrix['nodes']:
            name, version = n['name'], n['version']
            key = name + '==' + version
            chosen, condition, gap = None, None, None
            if n['missing_third_party']:
                release = releases[key]
                options, research_only = [], []
                for file in release['files']:
                    reasons, matched = assess(file, tid, env, release['info'])
                    if not reasons:
                        options.append((file, matched))
                    if set(reasons) <= {'YANKED'} and file['filename'] in byfile:
                        research_only.append((file, matched))
                options.sort(key=rank)
                if options:
                    chosen, condition = options[0]
                else:
                    gap = 'NO_COMPATIBLE_NON_YANKED_OFFICIAL_WHEEL'
                meta_file = chosen or (min(research_only, key=rank)[0] if research_only else None)
                if meta_file and meta_file['filename'] in byfile:
                    meta = byfile[meta_file['filename']]
                    provenance = {**pep_sources[meta_file['filename']], 'research_yanked_only': chosen is None}
                else:
                    info = release['info']
                    meta = {k: info.get(k) for k in ['name', 'version', 'requires_python', 'requires_dist', 'provides_extra']}
                    meta['name'] = name
                    provenance = {'kind': 'EXACT_RELEASE_JSON_NOT_FILE_SPECIFIC', 'url': release['source']}
                if chosen and not rp_ok(meta['requires_python'], env['python_full_version']):
                    raise ValueError('FILE_METADATA_REQUIRES_PYTHON_CONFLICT')
                license = license_bykey[key]
                nodes[key] = {'name': name, 'version': version, 'source': release['source'],
                              'requires_python': release['info'].get('requires_python'),
                              'license_expression_declared': release['info'].get('license_expression'),
                              'license_interpretation': license['project_text_interpretation'],
                              'license_text_status': license['source_text_status'], 'license_review': 'BLOCKED',
                              'artifact_acquired': False, 'actual_hash_verified': False}
            else:
                meta = ({'name': root, 'version': binding['version'], 'requires_python': binding['requires_python'],
                         'requires_dist': binding['requires_dist'], 'provides_extra': []}
                        if name == root else n['installed_metadata'])
                provenance = {'kind': 'ACTUAL_LOCAL_ROOT_METADATA' if name == root else 'INTERNAL_DOCUMENT_METADATA_IDENTITY_UNRESOLVED'}
                meta = {k: meta.get(k) for k in ['name', 'version', 'requires_python', 'requires_dist', 'provides_extra']}
            metas[name] = meta
            vid = digest(encoded(meta))
            variants[vid] = meta
            fid = None
            if chosen:
                fid = digest(encoded([chosen['filename'], chosen['sha256'], chosen['url']]))
                if fid not in allfiles:
                    allfiles[fid] = {**chosen, 'targets': [], 'license_key': key, 'license_review': 'BLOCKED',
                                     'artifact_acquired': False, 'actual_hash_verified': False,
                                     'official_hash_status': 'OFFICIAL_HASH_RECORDED', 'local_status': 'ARTIFACT_NOT_ACQUIRED'}
                allfiles[fid]['targets'].append(tid)
            target_nodes.append({'key': key, 'metadata_id': vid, 'provenance': provenance,
                                 'file_id': fid, 'platform_condition': condition, 'gap': gap})
        evaluated = graph(pins, metas, root, env)
        if evaluated['issues'] or set(evaluated['reached']) != set(pins):
            raise ValueError('OFFICIAL_GRAPH_NOT_CLOSED_AT_METADATA_LEVEL: ' + tid)
        for node in target_nodes:
            name = node['key'].split('==')[0]
            node['active_extras'] = evaluated['extras'].get(name, [])
            node['parents'] = sorted({e['from'] for e in evaluated['edges'] if e['active'] and e['to'] == name})
        targets.append({'id': tid, 'marker_environment': env, 'runtime_observed': False,
                        'marker_patch_assumption': 'Representative .0, not observed deployed patch',
                        'standard_gil_only': True, 'nodes': sorted(target_nodes, key=lambda n: n['key']),
                        'graph': evaluated, 'dependency_closure': 'BLOCKED'})
    for file in allfiles.values():
        name = file['name']
        file['dependency_parents_by_target'] = {t['id']: sorted({e['from'] for e in t['graph']['edges'] if e['active'] and e['to'] == name})
                                                 for t in targets if t['id'] in file['targets']}
    pure = sum(all(tag.endswith('-none-any') for tag in f['tags']) for f in allfiles.values())
    counts = {'names': len({n['name'] for n in nodes.values()}), 'name_versions': len(nodes), 'targets': len(targets),
              'unique_files': len(allfiles), 'pure_files': pure, 'platform_files': len(allfiles) - pure,
              'assignments': sum(len(f['targets']) for f in allfiles.values()),
              'gaps': sum(n['gap'] is not None for t in targets for n in t['nodes']),
              'third_party_local_artifacts': 0, 'actual_wheel_hashes_verified': 0}
    backend = [{'name': b['name'], 'version': b['version'], 'scope': 'BUILD_BACKEND_NOT_RUNTIME42',
                'source': releases[b['name'] + '==' + b['version']]['source'],
                'files': releases[b['name'] + '==' + b['version']]['files'], 'dynamic_requires': 'NOT_EXECUTED_UNKNOWN',
                'artifact_acquired': False, 'actual_hash_verified': False} for b in observed['build_backend']]
    value = {'schema': SCHEMA, 'status': 'PROPOSED_NOT_INSTALLABLE', 'dependency_closure': 'BLOCKED',
             'source_head': BASE, 'input_capsule_sha256': ANCHOR_SHA, 'input_identities': identities,
             'formal_first_target': runtime['formal_first_target'], 'conditional_first_target': 'Windows-AMD64-CPython3.12',
             'nodes': nodes, 'metadata_variants': variants, 'files': allfiles, 'targets': targets, 'counts': counts,
             'backends_separate': backend, 'document_cli_identity': {'status': docs['verdict'], 'artifacts': [
                 {k: d[k] for k in ['path', 'bytes', 'sha256', 'member_count']} for d in docs['documents']]},
             'root_artifact': binding['wheel'], 'license_summary': licenses['summary'],
             'limitations': ['No third-party artifact acquired; official SHA is not local-byte verification.',
                            'PEP658 index expected digest not checked; metadata bytes do not verify wheel bytes.',
                            'Linux glibc/minimum and macOS minimum are conditional and must be observed.',
                            'All redistribution and runtime gates BLOCKED; research integrity is a separate gate.']}
    return clean(value)


def differences(actual, expected, path='$', errors=None):
    if errors is None:
        errors = []
    if len(errors) >= 30:
        return errors
    if type(actual) is not type(expected):
        errors.append(path + ': TYPE_MISMATCH')
    elif isinstance(expected, dict):
        for key in sorted(set(actual) ^ set(expected)):
            errors.append(path + '.' + key + ': KEY_SET_MISMATCH')
        for key in sorted(set(actual) & set(expected)):
            differences(actual[key], expected[key], path + '.' + key, errors)
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            errors.append(path + ': LENGTH_MISMATCH')
        for i, (a, b) in enumerate(zip(actual, expected)):
            differences(a, b, path + '[' + str(i) + ']', errors)
    elif actual != expected:
        errors.append(path + ': FROZEN_RECONSTRUCTION_MISMATCH')
    return errors[:30]


def validate(candidate, input_path):
    # Does not trust candidate graph, markers, flags, metadata, source URLs or hashes.
    expected = rebuild(input_path)
    return differences(candidate, expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['generate', 'validate'])
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    if args.mode == 'generate':
        result = rebuild(args.inputs)
        p = Path(args.candidate)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(encoded(result))
        print(json.dumps({'integrity': 'GENERATED_NOT_QA', 'counts': result['counts'], 'sha256': digest(p.read_bytes())}))
    else:
        candidate = json.loads(Path(args.candidate).read_bytes())
        errors = validate(candidate, args.inputs)
        print(json.dumps({'integrity': 'REJECTED' if errors else 'VALID_RESEARCH_CANDIDATE_NOT_INSTALLABLE',
                          'errors': errors, 'dependency_closure': 'BLOCKED', 'independent_qa': False}))
        return int(bool(errors))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
