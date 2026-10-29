"""Versioned local time-series bundles; independent of Phase 2's 32 MiB JSON API."""
from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from functools import wraps
import os
from pathlib import Path
import shutil
from zoneinfo import ZoneInfo
from dataclasses import dataclass
import math

from .errors import ContractError
from .serialization import dumps, digest, MAX_JSON_BYTES
from .timeseries_tokens import loads
from .schemas import StrictValidator, format_checker
from .validation import validate_record, validate_project, iter_records, _schema
from .categories import validate_category
from .intake import IntakeSession
from .timeseries_private import Meter, checked_read, write_file, local_target, identity_index

HARD_MAX_INPUT_BYTES = 2 * 1024**3
HARD_MAX_DISK_BYTES = 4 * 1024**3
HARD_MAX_ROWS = 1_000_000
HARD_MAX_SECONDS = 3600
HARD_MAX_MEMORY_BYTES = 2 * 1024**3


@dataclass(frozen=True, slots=True)
class BundleBudget:
    max_input_bytes: int = 512 * 1024**2
    max_disk_bytes: int = 1024**3
    max_rows: int = 100_000
    max_seconds: float = 600
    max_memory_bytes: int = 512 * 1024**2

    def __post_init__(self):
        for name, ceiling in (('max_input_bytes', HARD_MAX_INPUT_BYTES),
                ('max_disk_bytes', HARD_MAX_DISK_BYTES), ('max_rows', HARD_MAX_ROWS),
                ('max_seconds', HARD_MAX_SECONDS), ('max_memory_bytes', HARD_MAX_MEMORY_BYTES)):
            value = getattr(self, name)
            if (type(value) not in ((int, float) if name == 'max_seconds' else (int,))
                    or not 0 < value <= ceiling or not math.isfinite(value)):
                raise ContractError('BUNDLE_BUDGET')


VERSION = 'solar-pv-timeseries-bundle/1.0.0'
DATASET_IDS = ('resource.timeseries', 'load.series', 'tariff.market_series')
MAX_ROW_BYTES = 1024**2
MAX_CHUNK_BYTES = 4 * 1024**2
MAX_MANIFEST_BYTES = 8 * 1024**2
MAX_CHUNKS = 8192
MAX_ROWS_PER_CHUNK = 4096
# Never trust an exception's arbitrary text/prefix from a caller-owned iterator.
_ERROR_CODES = frozenset('BUNDLE_' + name for name in '''
MEMORY_UNAVAILABLE TIME_LIMIT MEMORY_LIMIT INPUT_LIMIT DISK_LIMIT ROW_LIMIT
LOCAL_PATH PARENT_REQUIRED UNSAFE_FILE FILE_LIMIT FILE_CHANGED SCRATCH_REQUIRED
DUPLICATE_ID UPSTREAM_MISSING BUDGET INVALID DEPTH_LIMIT ATOM_INVALID BASE_VERSION
BASE_MISMATCH TIME_INVALID SITE_TIMEZONE INTERVAL ATOM_CONTEXT DATASET HEADER
PERIOD ROW_SCHEMA ROW_FIELDS NEGATIVE_PRICE_RULE ROW_ID CONTINUITY POWER_ENERGY
INCOMPLETE MANIFEST CONTENT_HASH EXTRA_FILE MISSING_FILE CHUNK_LIMIT OUTPUT_EXISTS
DATASET_ALREADY_IN_BASE FILE_HASH CHUNK_ROWS NONCANONICAL NOT_VALIDATED CLOSED
MANIFEST_CHANGED BYTE_LIMIT DATASET_HASH
'''.split())


def _safe(fn):
    @wraps(fn)
    def call(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ContractError as e:
            raise ContractError(e.code if e.code in _ERROR_CODES else 'BUNDLE_INVALID') from None
        except Exception:
            raise ContractError('BUNDLE_INVALID') from None
    return call


def _budget(budget):
    if type(budget) is not BundleBudget:
        raise ContractError('BUNDLE_BUDGET')
    budget.__post_init__()
    return Meter(budget)


def _encode(value, limit):
    # Stream canonical tokens into a bounded buffer. Calling legacy dumps first
    # would allocate an arbitrarily large temporary before discovering the cap.
    out = bytearray()
    def put(token):
        if len(out)+len(token) > limit:
            raise ContractError('BUNDLE_FILE_LIMIT')
        out.extend(token)
    def emit(item, depth=0):
        if depth > 64:
            raise ContractError('BUNDLE_DEPTH_LIMIT')
        if isinstance(item, str):
            if len(item) > limit-len(out):
                raise ContractError('BUNDLE_FILE_LIMIT')
            put(dumps(item).encode('utf-8'))
        elif isinstance(item, list):
            if len(item) > (limit-len(out))//2:
                raise ContractError('BUNDLE_FILE_LIMIT')
            put(b'[')
            for n,child in enumerate(item):
                if n: put(b',')
                emit(child,depth+1)
            put(b']')
        elif isinstance(item, dict):
            if len(item) > (limit-len(out))//4 or any(not isinstance(k,str) for k in item):
                raise ContractError('BUNDLE_FILE_LIMIT')
            put(b'{')
            for n,key in enumerate(sorted(item)):
                if n: put(b',')
                emit(key,depth+1); put(b':'); emit(item[key],depth+1)
            put(b'}')
        else:
            put(dumps(item).encode('utf-8'))
    emit(value)
    return bytes(out)


@_safe
def canonical_array_hash(rows) -> str:
    """Exact legacy digest(list(rows)), streamed under bounded private defaults."""
    meter = _budget(BundleBudget())
    state = hashlib.sha256(b'[')
    for row in rows:
        meter.rows += 1; meter.check()
        payload = _encode(row, MAX_ROW_BYTES)
        meter.input += len(payload)+1; meter.check()
        if meter.rows > 1:
            state.update(b',')
        state.update(payload)
    state.update(b']')
    return state.hexdigest()


def _errors(issues):
    if any(i.severity == 'ERROR' for i in issues):
        raise ContractError('BUNDLE_ATOM_INVALID')


def _revalidate_base(exported, catalog):
    # Full Phase 2 re-export, never a dummy root with empty dataset arrays.
    if exported.get('input_module_version') not in {'0.2.0','0.3.0'}:
        raise ContractError('BUNDLE_BASE_VERSION')
    session = IntakeSession.from_dict(exported['project'], catalog)
    _errors(validate_project(session.project, catalog))
    _errors(validate_category(session.project, catalog))
    for candidate in session.project.candidates.values():
        for record, scalar in iter_records({candidate['field_id']: candidate}, catalog):
            _errors(validate_record(record, catalog, scalar_item=scalar))
    # Phase 2 source snapshots intentionally hash their record-list order. JSON
    # object keys are canonical-sorted on disk, so recover the ROOT traversal
    # order from that frozen list, then regenerate/compare the entire export.
    root_instances = {r['field_instance_id'] for r in session.project.values.values()}
    order = [r['field_id'] for r in exported['source_snapshot']['records']
             if r['field_instance_id'] in root_instances]
    if len(order) != len(set(order)) or set(order) != set(session.project.values):
        raise ContractError('BUNDLE_BASE_MISMATCH')
    rank = {r['field_instance_id']:i for i,r in enumerate(exported['source_snapshot']['records'])}
    def restore(records):
        ordered = dict(sorted(records.items(), key=lambda item:rank.get(item[1]['field_instance_id'],len(rank))))
        for record in ordered.values():
            field = catalog.fields[record['field_id']]
            if field['type'] == 'array' and isinstance(record['value'],list) and field['constraints']['items']['type'] == 'object':
                for row in record['value']:
                    row['fields'] = restore(row['fields'])
        return ordered
    session.project.values = restore({fid:session.project.values[fid] for fid in order})
    regenerated = session.export()
    # Explicit producer compatibility only; old input/source hashes stay original.
    regenerated['input_module_version'] = exported['input_module_version']
    if dumps(exported) != dumps(regenerated):
        raise ContractError('BUNDLE_BASE_MISMATCH')
    return session.project


def _known(project, fid):
    r = project.values.get(fid, {})
    return r.get('value') if r.get('status') not in {'UNKNOWN', 'CONFLICT'} else None


def _stamp(value, zone):
    if not isinstance(value, str):
        raise ContractError('BUNDLE_TIME_INVALID')
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.utcoffset() is None:
        raise ContractError('BUNDLE_TIME_INVALID')
    local = stamp.astimezone(zone)
    if (local.replace(tzinfo=None) != stamp.replace(tzinfo=None)
            or local.utcoffset() != stamp.utcoffset()):
        raise ContractError('BUNDLE_SITE_TIMEZONE')
    return stamp.astimezone(timezone.utc)


def _fraction(value):
    if isinstance(value, (str, bool)) or value is None:
        raise ContractError('BUNDLE_INTERVAL')
    result = Fraction(str(value))
    if result <= 0:
        raise ContractError('BUNDLE_INTERVAL')
    return result


def _atom_context(record, project):
    # Relevant global validate_project rules, without materializing a full table.
    if record['status'] == 'CONFLICT' and (len(record['candidate_ids']) < 2
            or any(cid not in project.candidates for cid in record['candidate_ids'])):
        raise ContractError('BUNDLE_ATOM_CONTEXT')
    currency = (record['normalization'] or {}).get('currency') or (record['economic_basis'] or {}).get('currency')
    project_currency = _known(project, 'project.currency')
    if isinstance(record['unit'], str) and record['unit'].startswith('currency') and currency and project_currency and currency != project_currency:
        raise ContractError('BUNDLE_ATOM_CONTEXT')


class _Sequence:
    def __init__(self, fid, header, catalog, project, meter, index):
        self.fid = fid; self.catalog = catalog; self.project = project
        self.meter = meter; self.index = index; self.header = deepcopy(header)
        if fid not in DATASET_IDS or fid not in catalog.fields:
            raise ContractError('BUNDLE_DATASET')
        definition = _schema(catalog)['$defs'][fid]
        properties = {k: v for k,v in definition['properties'].items() if k not in {'value','original_value'}}
        meta_schema = {'type':'object','additionalProperties':False,'properties':properties,'required':list(properties)}
        if next(StrictValidator(meta_schema, format_checker=format_checker()).iter_errors(header), None):
            raise ContractError('BUNDLE_HEADER')
        self.zone_name = _known(project, 'site.timezone')
        if fid == 'load.series' and _known(project, 'load.timezone') not in {None, self.zone_name}:
            raise ContractError('BUNDLE_SITE_TIMEZONE')
        self.zone = ZoneInfo(self.zone_name)
        period = header['measurement_period']
        if (not isinstance(period, dict) or set(period) != {'start','end','timezone','interval_minutes','coverage'}
                or period['timezone'] != self.zone_name or isinstance(period['coverage'], bool)
                or period['coverage'] != 1):
            raise ContractError('BUNDLE_PERIOD')
        self.start = _stamp(period['start'], self.zone); self.end = _stamp(period['end'], self.zone)
        self.interval = _fraction(period['interval_minutes'])
        micros = self.interval * 60_000_000
        if micros.denominator != 1 or micros > 366*86400*1_000_000:
            raise ContractError('BUNDLE_INTERVAL')
        self.step = timedelta(microseconds=micros.numerator)
        if self.start >= self.end or (self.end-self.start) % self.step != timedelta(0):
            raise ContractError('BUNDLE_PERIOD')
        self.next = self.start; self.count = self.atoms = 0
        self.hash = hashlib.sha256(b'[')
        self.allowed = set(catalog.fields[fid]['constraints']['items']['field_ids'])
        row_shape = deepcopy(definition['properties']['value']['anyOf'][0]['items'])
        # Shape checks only at row level: every atom's complete strict schema AND
        # semantics run below through validate_record. Do not validate schemas
        # twice per atom or replace semantics with a field-presence fast path.
        for child in row_shape['properties']['fields']['properties']:
            row_shape['properties']['fields']['properties'][child] = {'type':'object'}
        self.row_validator = StrictValidator(row_shape, format_checker=format_checker())
        self.units = {}

    def add(self, row, payload):
        self.meter.rows += 1; self.meter.check()
        if next(self.row_validator.iter_errors(row), None):
            raise ContractError('BUNDLE_ROW_SCHEMA')
        fields = row['fields']
        required = {self.fid+'.'+name for name in ('row_id','timestamp','interval_minutes')}
        if not required <= fields.keys() or not fields.keys() <= self.allowed:
            raise ContractError('BUNDLE_ROW_FIELDS')
        if not self.count:
            # Only a transient real first-row SHARD checks container metadata.
            # No truncated root array is exported, hashed, or substituted in base.
            _errors(validate_record({**self.header, 'value':[row], 'original_value':None}, self.catalog))
            _atom_context(self.header, self.project)
            self.index.add('atom', self.header['field_instance_id'])
            for upstream in self.header['upstream_instance_ids']:
                self.index.ref(upstream)
        self.index.add('row:'+self.fid, row['row_id'])
        for key, record in fields.items():
            if record['field_id'] != key:
                raise ContractError('BUNDLE_ROW_FIELDS')
            _errors(validate_record(record, self.catalog))
            _atom_context(record, self.project)
            self.index.add('atom', record['field_instance_id'])
            for upstream in record['upstream_instance_ids']:
                self.index.ref(upstream)
            self.atoms += 1; self.meter.atoms += 1
            self.units[key] = record['unit']
            if (key.startswith('tariff.') and isinstance(record['value'], (int,float,Decimal))
                    and not isinstance(record['value'], bool) and record['value'] < 0
                    and not (_known(self.project, 'tariff.negative_price_rule')
                             and _known(self.project, 'tariff.contract_id'))):
                raise ContractError('BUNDLE_NEGATIVE_PRICE_RULE')
        def val(name):
            r = fields.get(self.fid+'.'+name, {})
            return r.get('value') if r.get('status') not in {'UNKNOWN','CONFLICT'} else None
        if val('row_id') != row['row_id']:
            raise ContractError('BUNDLE_ROW_ID')
        point = _stamp(val('timestamp'), self.zone)
        if point != self.next:
            raise ContractError('BUNDLE_CONTINUITY')
        if _fraction(val('interval_minutes')) != self.interval:
            raise ContractError('BUNDLE_INTERVAL')
        if point >= self.end:
            raise ContractError('BUNDLE_PERIOD')
        self.next += self.step
        if self.fid == 'load.series' and val('power') is not None and val('energy') is not None:
            if Fraction(str(val('power')))*self.interval/60 != Fraction(str(val('energy'))):
                raise ContractError('BUNDLE_POWER_ENERGY')
        if self.count:
            self.hash.update(b',')
        self.hash.update(payload); self.count += 1
        if self.count % 256 == 0:
            self.index.check()

    def finish(self):
        if not self.count or self.next != self.end:
            raise ContractError('BUNDLE_INCOMPLETE')
        self.hash.update(b']'); self.index.check()
        return {'row_count':self.count, 'atom_count':self.atoms,
            'canonical_array_hash':self.hash.hexdigest(), 'metadata':{
                'start':self.header['measurement_period']['start'], 'end':self.header['measurement_period']['end'],
                'interval_minutes':self.header['measurement_period']['interval_minutes'],
                'timezone':self.zone_name, 'units':dict(sorted(self.units.items()))}}


def _content_hash(manifest):
    return digest({'schema_version':VERSION, 'base_export_hash':manifest['base_export']['sha256'],
        'datasets': {fid:{k:v for k,v in ds.items() if k != 'chunks'} for fid,ds in manifest['datasets'].items()}})


def _seed_index(index, project, catalog):
    for record, _ in iter_records(project.values, catalog):
        index.add('atom', record['field_instance_id'])
        for upstream in record['upstream_instance_ids']:
            index.ref(upstream)


def _manifest_schema():
    sha = {'type':'string','pattern':'^[0-9a-f]{64}$'}
    count = {'type':'integer','minimum':1,'maximum':HARD_MAX_ROWS}
    def obj(properties):
        return {'type':'object','additionalProperties':False,'properties':properties,'required':list(properties)}
    file = obj({'file':{'type':'string','pattern':'^(?:base\\.json|d[0-2]-c[0-9]{6}\\.jsonl)$'},
                'bytes':{'type':'integer','minimum':1,'maximum':MAX_JSON_BYTES}, 'sha256':sha})
    chunk = deepcopy(file); chunk['properties']['rows'] = count; chunk['required'].append('rows')
    metadata = obj({'start':{'type':'string'}, 'end':{'type':'string'}, 'timezone':{'type':'string'},
        'interval_minutes':{'type':'number','exclusiveMinimum':0},
        'units':{'type':'object','additionalProperties':{'type':['string','null']}}})
    dataset = obj({'header':{'type':'object'}, 'row_count':count,
        'atom_count':{'type':'integer','minimum':1,'maximum':HARD_MAX_ROWS*10},
        'canonical_array_hash':sha, 'metadata':metadata,
        'chunks':{'type':'array','minItems':1,'maxItems':MAX_CHUNKS,'items':chunk}})
    return obj({'schema_version':{'const':VERSION}, 'complete':{'const':True}, 'base_export':file,
        'datasets':{'type':'object','minProperties':1,'additionalProperties':False,
            'properties':{fid:dataset for fid in DATASET_IDS}}, 'content_hash':sha})


def _manifest_valid(manifest):
    if next(StrictValidator(_manifest_schema()).iter_errors(manifest), None):
        raise ContractError('BUNDLE_MANIFEST')
    if manifest['base_export']['file'] != 'base.json':
        raise ContractError('BUNDLE_MANIFEST')
    names = ['manifest.json', 'base.json']; chunks = 0
    for ds in manifest['datasets'].values():
        for c in ds['chunks']:
            if c['bytes'] > MAX_CHUNK_BYTES or c['file'] == 'base.json' or c['rows'] > MAX_ROWS_PER_CHUNK:
                raise ContractError('BUNDLE_MANIFEST')
            names.append(c['file']); chunks += 1
    if chunks > MAX_CHUNKS or len(set(names)) != len(names):
        raise ContractError('BUNDLE_MANIFEST')
    if _content_hash(manifest) != manifest['content_hash']:
        raise ContractError('BUNDLE_CONTENT_HASH')
    return set(names)


def _inventory(path, expected):
    from .local_files import _unlinked
    _unlinked(path)
    with os.scandir(path) as entries:
        names = set()
        for entry in entries:
            if entry.name not in expected or entry.name in names:
                raise ContractError('BUNDLE_EXTRA_FILE')
            names.add(entry.name); _unlinked(Path(entry.path))
        if names != expected:
            raise ContractError('BUNDLE_MISSING_FILE')


@_safe
def write_bundle(path, *, base_export, datasets, catalog, budget, rows_per_chunk=256) -> dict:
    """Publish a new private directory; manifest is the last atomic no-clobber write.

    Header contains every original root-envelope property except value and
    original_value. measurement_period is explicit [start,end), coverage=1.
    """
    from .local_files import Workspace
    meter = _budget(budget)
    if type(rows_per_chunk) is not int or not 1 <= rows_per_chunk <= MAX_ROWS_PER_CHUNK:
        raise ContractError('BUNDLE_CHUNK_LIMIT')
    if not isinstance(datasets, dict) or not datasets or not datasets.keys() <= set(DATASET_IDS):
        raise ContractError('BUNDLE_DATASET')
    root = local_target(path)
    if root.exists():
        raise ContractError('BUNDLE_OUTPUT_EXISTS')
    base_bytes = _encode(base_export, MAX_JSON_BYTES)
    meter.input += len(base_bytes); meter.check()
    base_export = loads(base_bytes)
    project = _revalidate_base(base_export, catalog); meter.check()
    if datasets.keys() & project.values.keys():
        raise ContractError('BUNDLE_DATASET_ALREADY_IN_BASE')
    root.mkdir(mode=0o700); published = False
    try:
        manifest = {'schema_version':VERSION, 'complete':True,
            'base_export':write_file(root/'base.json', base_bytes, meter), 'datasets':{}}
        total_chunks = 0
        with identity_index(meter) as index:
            _seed_index(index, project, catalog)
            for fid in sorted(datasets):
                ds = datasets[fid]
                if not isinstance(ds, dict) or set(ds) != {'header','rows'}:
                    raise ContractError('BUNDLE_DATASET')
                head_bytes = _encode(ds['header'], MAX_ROW_BYTES)
                meter.input += len(head_bytes); meter.check()
                head = loads(head_bytes)
                seq = _Sequence(fid, head, catalog, project, meter, index)
                chunks = []; buffer = bytearray(); count = 0
                def flush():
                    nonlocal buffer, count, total_chunks
                    if not count:
                        return
                    total_chunks += 1
                    if total_chunks > MAX_CHUNKS:
                        raise ContractError('BUNDLE_CHUNK_LIMIT')
                    name = f'd{DATASET_IDS.index(fid)}-c{len(chunks):06d}.jsonl'
                    chunks.append({**write_file(root/name, buffer, meter), 'rows':count})
                    buffer = bytearray(); count = 0
                for row in ds['rows']:
                    meter.check()
                    payload = _encode(row, MAX_ROW_BYTES)
                    meter.input += len(payload)+1; meter.check()
                    row = loads(payload, max_bytes=MAX_ROW_BYTES)
                    seq.add(row, payload)
                    if count and (count >= rows_per_chunk or len(buffer)+len(payload)+1 > MAX_CHUNK_BYTES):
                        flush()
                    buffer.extend(payload); buffer.extend(b'\n'); count += 1
                flush()
                manifest['datasets'][fid] = {'header':head, **seq.finish(), 'chunks':chunks}
            index.finish()
        manifest['content_hash'] = _content_hash(manifest)
        _manifest_valid(manifest)
        payload = _encode(manifest, MAX_MANIFEST_BYTES)
        meter.input += len(payload); meter.check()
        write_file(root/'.manifest.tmp', payload, meter)
        _inventory(root, {'base.json', '.manifest.tmp', *(c['file'] for ds in manifest['datasets'].values() for c in ds['chunks'])})
        os.link(root/'.manifest.tmp', root/'manifest.json')
        (root/'.manifest.tmp').unlink()
        Workspace._sync_directory(root)
        published = True
        return deepcopy(manifest)
    finally:
        if not published:
            shutil.rmtree(root)


def _file(root, descriptor, limit, meter):
    payload = checked_read(root/descriptor['file'], limit, meter)
    if len(payload) != descriptor['bytes'] or hashlib.sha256(payload).hexdigest() != descriptor['sha256']:
        raise ContractError('BUNDLE_FILE_HASH')
    return payload


def _chunk_rows(payload, count):
    if not payload.endswith(b'\n') or payload.count(b'\n') != count:
        raise ContractError('BUNDLE_CHUNK_ROWS')
    import io
    with io.BytesIO(payload) as lines:
        for line in lines:
            row_bytes = line[:-1]
            if not row_bytes or len(row_bytes) > MAX_ROW_BYTES:
                raise ContractError('BUNDLE_ROW_LIMIT')
            row = loads(row_bytes, max_bytes=MAX_ROW_BYTES)
            canonical = _encode(row, MAX_ROW_BYTES)
            if canonical != row_bytes:
                raise ContractError('BUNDLE_NONCANONICAL')
            yield row, canonical


class TimeSeriesBundle:
    """read_bundle validates ALL files/atoms before this result is created.

    Dict properties are copies. Iteration rechecks manifest, membership and each
    whole file hash before yielding that file. Finish iteration before publishing
    results. Local ACLs must prevent hostile directory races; no OS sandbox claim.
    """
    def __init__(self, root, base, manifest, stats, budget, token):
        if token is not _VALIDATED:
            raise ContractError('BUNDLE_NOT_VALIDATED')
        self._root = root; self._base = base; self._manifest = manifest
        self._stats = stats; self._budget = budget; self._closed = False

    @property
    def base_export(self):
        return deepcopy(self._base)

    @property
    def manifest(self):
        return deepcopy(self._manifest)

    @property
    def stats(self):
        return deepcopy(self._stats)

    @property
    def dataset_ids(self):
        return tuple(sorted(self._manifest['datasets']))

    @property
    def content_hash(self):
        return self._manifest['content_hash']

    def _open(self):
        if self._closed:
            raise ContractError('BUNDLE_CLOSED')

    def rows(self, field_id):
        try:
            self._open()
            if field_id not in self._manifest['datasets']:
                raise ContractError('BUNDLE_DATASET')
            meter = _budget(self._budget)
            expected = _manifest_valid(self._manifest); _inventory(self._root, expected)
            raw = checked_read(self._root/'manifest.json', MAX_MANIFEST_BYTES, meter)
            if raw != _encode(self._manifest, MAX_MANIFEST_BYTES):
                raise ContractError('BUNDLE_MANIFEST_CHANGED')
            _file(self._root, self._manifest['base_export'], MAX_JSON_BYTES, meter)
            for chunk in self._manifest['datasets'][field_id]['chunks']:
                self._open()
                payload = _file(self._root, chunk, MAX_CHUNK_BYTES, meter)
                for row, _ in _chunk_rows(payload, chunk['rows']):
                    self._open(); meter.rows += 1; meter.check()
                    yield row
            _inventory(self._root, expected)
        except ContractError as e:
            raise ContractError(e.code if e.code in _ERROR_CODES else 'BUNDLE_INVALID') from None
        except Exception:
            raise ContractError('BUNDLE_INVALID') from None

    def close(self):
        self._closed = True

    def __enter__(self):
        self._open(); return self

    def __exit__(self, *exc):
        self.close()


_VALIDATED = object()


@_safe
def read_bundle(path, *, catalog, budget) -> TimeSeriesBundle:
    meter = _budget(budget); root = local_target(path)
    raw = checked_read(root/'manifest.json', MAX_MANIFEST_BYTES, meter)
    manifest = loads(raw, max_bytes=MAX_MANIFEST_BYTES)
    expected = _manifest_valid(manifest); _inventory(root, expected)
    total_bytes = sum(d['bytes'] for ds in manifest['datasets'].values() for d in ds['chunks']) + manifest['base_export']['bytes'] + len(raw)
    total_rows = sum(ds['row_count'] for ds in manifest['datasets'].values())
    if total_bytes > budget.max_input_bytes or total_bytes > budget.max_disk_bytes:
        raise ContractError('BUNDLE_BYTE_LIMIT')
    if total_rows > budget.max_rows:
        raise ContractError('BUNDLE_ROW_LIMIT')
    if raw != _encode(manifest, MAX_MANIFEST_BYTES):
        raise ContractError('BUNDLE_NONCANONICAL')
    base = loads(_file(root, manifest['base_export'], MAX_JSON_BYTES, meter))
    project = _revalidate_base(base, catalog); meter.check()
    if manifest['datasets'].keys() & project.values.keys():
        raise ContractError('BUNDLE_DATASET_ALREADY_IN_BASE')
    with identity_index(meter) as index:
        _seed_index(index, project, catalog)
        for fid, ds in manifest['datasets'].items():
            seq = _Sequence(fid, ds['header'], catalog, project, meter, index)
            for chunk in ds['chunks']:
                payload = _file(root, chunk, MAX_CHUNK_BYTES, meter)
                for row, canonical in _chunk_rows(payload, chunk['rows']):
                    seq.add(row, canonical)
            computed = seq.finish()
            if any(ds[key] != value for key, value in computed.items()):
                raise ContractError('BUNDLE_DATASET_HASH')
        index.finish()
    _inventory(root, expected)
    again = checked_read(root/'manifest.json', MAX_MANIFEST_BYTES, meter, account=False)
    if again != raw:
        raise ContractError('BUNDLE_MANIFEST_CHANGED')
    return TimeSeriesBundle(root, base, manifest, meter.stats(), budget, _VALIDATED)
