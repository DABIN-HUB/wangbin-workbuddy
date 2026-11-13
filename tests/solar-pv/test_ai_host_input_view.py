"""Shared input codec and native lifecycle. NOT_AI / NOT_HOST_E2E; no calculation."""
from pathlib import Path
import importlib
import pytest
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from test_ai_report_engine import catalog, registry, model, protocol_fixture
from test_ai_host_session_r2 import provenance
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import dumps, digest
from wangbin_solar_pv.reporting import chapter_writer as writer, host_session as session
from wangbin_solar_pv.reporting.host_workspace import HostWorkspace
from wangbin_solar_pv.reporting.llm_provider import ModelConfig
from wangbin_solar_pv.reporting.host_output import NOT_EXPOSED


@pytest.fixture
def native(tmp_path, model, catalog, registry):
    raw = (ROOT / 'tests/fixtures/solar-pv/phase7l-r2-delivery' / model.result['pv_type'] / 'canonical.json').read_bytes()
    (tmp_path / 'canonical.json').write_bytes(raw)
    cfg = ModelConfig('protocol-fixture-only', max_request_bytes=2097152, max_output_bytes=262144,
                      timeout_seconds=3600, max_attempts_per_chapter=1, max_requests=1)
    from wangbin_solar_pv.reporting.evidence_pack_builder import source_ids
    grant = {'schema_version': 'host-authorization/2.0', 'canonical': 'canonical.json',
             'canonical_sha256': sha256(raw).hexdigest(), 'pv_type': model.result['pv_type'],
             'authorized_source_ids': sorted(source_ids(model.result)), 'host_processing_authorized': True,
             'model_config': cfg.to_dict(), 'input_view_policy': codec().POLICY.copy()}
    ws = Workspace(tmp_path); ws.create('grant.json', grant)
    def run(action, rid=None):
        return session.execute(action, ws, 'native', 'grant.json', catalog, rid)
    return ws, run, cfg, model, registry


def make_draft(store, request):
    response = {'request_hash': request['request_hash'], 'model_id': request['model_id'],
                'host_call_id': NOT_EXPOSED, 'output': protocol_fixture(request['evidence_pack'])}
    store.create('CH08-1-draft.json', response)
    store.create('CH08-1-provenance.json', provenance(request, response))
    return response


def test_new_native_lifecycle(native):
    ws, run, cfg, model, registry = native
    item = run('prepare-r2-shared')
    store = HostWorkspace(ws.root / 'native')
    request = store.read('CH08-1-request.json')[0]
    assert request['input_view_policy'] == codec().POLICY
    assert item['input_view_file'].endswith('CH08-1-input-view.json')
    make_draft(store, request)
    assert run('publish', 'CH08-1')['status'] == 'PUBLISHED_NOT_ACCEPTED'
    accepted = run('accept', 'CH08-1')
    assert accepted['host_record']['model_execution'] == 'PROTOCOL_REPLAY'
    restored, pack = writer.resume(store, 'CH08-1', model, registry, cfg)
    assert restored['chapter_output_hash'] == accepted['chapter_output_hash']
    assert session.checkpoint(store, model, registry, cfg, request['binding']['authorized_sources'],
                              input_view_policy=codec().POLICY)['requests'][0]['status'] == 'ACCEPTED_REVALIDATED'

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / '.runtime/solar-pv/r2-client-552-20261113-132354/workspaces'


def codec():
    return importlib.import_module('wangbin_solar_pv.reporting.host_input_view')


@pytest.mark.parametrize('kind,run', [('industrial_rooftop', 'roof-primary'), ('utility_scale_ground', 'ground-primary')])
def test_historical_exact_roundtrip(kind, run):
    c = codec()
    raw = (OLD / kind / run / 'CH08-1-request.json').read_bytes()
    view = c.build_view(raw)
    assert c.decode_view(view, raw) == raw
    assert c.build_view(raw) == view
    assert len(c.file_bytes(view)) < len(raw)
    assert view['pool']


from copy import deepcopy
from wangbin_solar_pv.errors import ContractError


@pytest.fixture(scope='module')
def history():
    c = codec()
    return [(p.read_bytes(), c.build_view(p.read_bytes())) for p in (
        OLD / 'industrial_rooftop/roof-primary/CH08-1-request.json',
        OLD / 'utility_scale_ground/ground-primary/CH08-1-request.json')]


def reseal(view):
    view['view_hash'] = digest({k: v for k, v in view.items() if k != 'view_hash'})
    return view


@pytest.mark.parametrize('mutation', ['unknown-metric', 'unknown-claim', 'duplicate-source', 'same-source-other-section',
    'drop-fact', 'source', 'status', 'number', 'lexeme', 'unit', 'period', 'boundary', 'location',
    'schema', 'six-tasks', 'risk', 'upstream', 'table-row', 'table-order'])
def test_resealed_full_fidelity_and_qa_f01(history, mutation):
    c = codec()
    for raw, view in history:
        obj = c._parse(raw)
        pack = obj['evidence_pack']; sec = pack['sections']['CH08.01']
        fact = next(iter(pack['facts'].values()))
        if mutation == 'unknown-metric': sec['metric_refs'].append('UNKNOWN_METRIC')
        elif mutation == 'unknown-claim': sec['claim_ids'].append('UNKNOWN_CLAIM')
        elif mutation == 'duplicate-source': sec['source_refs'].append(sec['source_refs'][0])
        elif mutation == 'same-source-other-section':
            other = next(f for f in pack['facts'] if f not in sec['fact_refs'] and
                         set(pack['facts'][f]['source_ids']) <= set(sec['source_refs']))
            sec['fact_refs'].append(other)
        elif mutation == 'drop-fact': pack['facts'].pop(next(iter(pack['facts'])))
        elif mutation == 'source': fact['source_ids'] = []
        elif mutation == 'status': fact['status'] = 'VERIFIED'
        elif mutation == 'number': fact['value'] = c._Number('999999')
        elif mutation == 'lexeme':
            numeric = next(f for f in pack['facts'].values() if isinstance(f['value'], c._Number))
            numeric['value'] = c._Number(str(numeric['value']) + '0' if '.' in str(numeric['value']) else str(numeric['value']) + '.0')
        elif mutation in {'unit', 'period', 'boundary'}: fact[mutation] = 'CHANGED'
        elif mutation == 'location': fact['source_location'] = 'CHANGED'
        elif mutation == 'schema': obj.pop('output_schema')
        elif mutation == 'six-tasks': obj['chapter_spec']['sections'].pop()
        elif mutation == 'risk': obj['writing_guidance'].pop()
        elif mutation == 'upstream': obj['upstream'][next(iter(obj['upstream']))]['status'] = 'COMPLETE'
        elif mutation.startswith('table'):
            table = next(t for t in pack['tables'].values() if len(t.get('fact_ids', [])) > 1)
            if mutation == 'table-row': table['fact_ids'].pop()
            else: table['fact_ids'].reverse()
        changed = c.build_view(c._exact(obj).encode('utf8') + b'\n')
        assert changed['view_hash'] == digest({k: v for k, v in changed.items() if k != 'view_hash'})
        with pytest.raises(ContractError, match='HOST_INPUT_TRUSTED_MISMATCH'):
            c.decode_view(changed, raw)


def test_exact_sentinels_and_noncanonical():
    c = codec()
    raw = b'{"a":[null,0,false,{},[],900719925474099312345,1e+02,-0,-0.0],"statuses":["UNKNOWN","ASSUMED","SYNTHETIC","CALCULATED"]}\n'
    assert c.decode_view(c.build_view(raw), raw) == raw
    for bad in (b'{ "a":1}', b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":"\xff"}', b'{"$shared":"S0001"}', b'{"a":1}\r\n'):
        with pytest.raises(ContractError): c.build_view(bad)


@pytest.mark.parametrize('mutation', ['protocol', 'mapping', 'mode', 'unknown-key', 'dangling', 'pool-cycle',
    'unused', 'duplicate-pool', 'bad-index', 'replay'])
def test_view_protocol_reseal_rejections(history, mutation):
    c = codec(); raw, original = history[0]; v = deepcopy(original)
    if mutation == 'protocol': v['protocol'] = 'unknown'
    elif mutation in {'mapping', 'mode'}: v['policy'][mutation] = 'unknown'
    elif mutation == 'unknown-key': v['unknown'] = True
    elif mutation == 'dangling': v['tree'] = {'$shared': 'S9999'}
    elif mutation == 'pool-cycle': v['pool'][next(iter(v['pool']))] = {'$shared': next(iter(v['pool']))}
    elif mutation == 'unused': v['pool']['S9999'] = ['UNUSED']
    elif mutation == 'duplicate-pool': v['pool']['S9999'] = deepcopy(next(iter(v['pool'].values())))
    elif mutation == 'bad-index': v['tree'] = {'$shared': ['S0001']}
    else: v = deepcopy(history[1][1])
    reseal(v)
    with pytest.raises(ContractError): c.decode_view(v, raw)
    if mutation != 'replay':
        with pytest.raises(ContractError): c.expand(v)


def nest(value, depth):
    for _ in range(depth): value = {'n': value}
    return value


def test_cache_subtree_insertion_depth_counterexample():
    c = codec(); v = c.build_view(b'{"a":1}')
    v['pool'] = {'S0001': nest({'leaf': True}, 38)}
    v['tree'] = {'first': {'$shared': 'S0001'}, 'second': nest({'$shared': 'S0001'}, 38)}
    reseal(v)
    # Encoded input is shallow enough; first reference warms cache; second must fail before copy.
    with pytest.raises(ContractError, match='HOST_INPUT_DEPTH'): c.expand(v)


def test_resource_boundaries_include_keys_utf8_and_punctuation(monkeypatch):
    c = codec(); v = c.build_view(b'{"a":1}')
    v['pool'] = {'S0001': {'key': '中' * 30}}
    v['tree'] = [{'$shared': 'S0001'}] * 200
    reseal(v)
    monkeypatch.setattr(c, 'MAX_BYTES', len(c.file_bytes(v)) + 1)
    with pytest.raises(ContractError, match='HOST_INPUT_RESOURCES'): c.expand(v)
    monkeypatch.setattr(c, 'MAX_BYTES', 4 * 1024 * 1024)
    monkeypatch.setattr(c, 'MAX_REFS', 1)
    with pytest.raises(ContractError, match='HOST_INPUT_REFERENCE_LIMIT'): c.expand(v)
    monkeypatch.setattr(c, 'MAX_REFS', 16384)
    monkeypatch.setattr(c, 'MAX_NODES', 10)
    with pytest.raises(ContractError, match='HOST_INPUT_RESOURCES'): c.expand(v)


def test_byte_budget_original_lf_and_no_clobber(tmp_path):
    c = codec(); store = Workspace(tmp_path)
    request = {'request_id': 'CH08-1', 'input_view_policy': c.POLICY,
               'binding': {'model_config': {'max_request_bytes': 10000}}}
    store.create('CH08-1-request.json', request)
    raw = store.path('CH08-1-request.json').read_bytes()
    assert c._original(store, request, len(raw)-1) == raw
    with pytest.raises(ContractError): c.create_files(store, request, len(raw)-2)
    with pytest.raises(ContractError, match='HOST_INPUT_DELIVERY_BUDGET'):
        c.create_files(store, request, len(raw)-1)
    c.create_files(store, request, 10000)
    before = store.path('CH08-1-input-view.json').read_bytes()
    with pytest.raises(ContractError, match='OUTPUT_EXISTS'): c.create_files(store, request, 10000)
    assert store.path('CH08-1-input-view.json').read_bytes() == before
    assert c.verify_files(store, request)['view_file_sha256'] == sha256(before).hexdigest()
    store.path('CH08-1-input-manifest.json').unlink()
    with pytest.raises(ContractError, match='HOST_INPUT_INCOMPLETE'): c.verify_files(store, request)


def test_cached_upstream_must_revalidate_shared_request(tmp_path, monkeypatch):
    store = Workspace(tmp_path)
    store.create('CH08-1-request.json', {'input_view_policy': codec().POLICY})
    accepted = {'output': {'sections': [], 'chapter_intro': '', 'chapter_findings': [],
                'decision_implications': [], 'decision_state': 'NOT_EVALUATED'},
                'identity': {}, 'chapter_output_hash': 'h', 'evidence_hash': 'e',
                'professional_review': 'PENDING_REVIEW'}
    def reject(*args, **kwargs):
        raise ContractError('HOST_INPUT_TRUSTED_MISMATCH')
    monkeypatch.setattr(writer, '_request', reject)
    state = {'requests': [{'chapter_id': 'CH08', 'request_id': 'CH08-1'}]}
    store.create('CH08-1-result.json', accepted)
    with pytest.raises(ContractError, match='HOST_INPUT_TRUSTED_MISMATCH'):
        writer._upstream(store, state, {'dependencies': ['CH08']}, None, None, None,
                         {'CH08-1': (accepted, {'facts': {}})})


def test_source_lifecycle_failure_guards(tmp_path, catalog, registry, monkeypatch):
    """One roof snapshot; real production guards, no finance or host calls."""
    from wangbin_solar_pv.report_export import ReportModel
    from wangbin_solar_pv.serialization import loads
    from wangbin_solar_pv.reporting import host_output
    raw = (ROOT / 'tests/fixtures/solar-pv/phase7l-r2-delivery/industrial_rooftop/canonical.json').read_bytes()
    model = ReportModel.from_result(loads(raw), catalog)
    ws, run, cfg, _, _ = native.__wrapped__(tmp_path, model, catalog, registry)
    run('prepare-r2-shared'); store = HostWorkspace(ws.root / 'native')
    request = store.read('CH08-1-request.json')[0]
    response = make_draft(store, request)
    vpath = store.path('CH08-1-input-view.json'); mpath = store.path('CH08-1-input-manifest.json')
    view_raw, manifest_raw = vpath.read_bytes(), mpath.read_bytes()
    bad = store.read('CH08-1-input-view.json')[0]
    bad['tree']['execution_state'] = 'FORGED'
    reseal(bad)
    vpath.write_bytes(codec().file_bytes(bad))
    mpath.write_bytes(codec().file_bytes(codec().manifest(store.path('CH08-1-request.json').read_bytes(), bad)))
    # Even a mutually resealed view+manifest is not a trusted-original identity.
    for action in ('checkpoint', 'publish', 'accept', 'resume'):
        with pytest.raises(ContractError, match='HOST_INPUT_TRUSTED_MISMATCH'): run(action, 'CH08-1')
    for invoke in (
        lambda: writer.resume(store, 'CH08-1', model, registry, cfg),
        lambda: host_output.verify_publication(store, request),
        lambda: host_output.publish_response(store, request, request['evidence_pack'], registry.chapter('CH08'), cfg)):
        with pytest.raises(ContractError, match='HOST_INPUT_TRUSTED_MISMATCH'): invoke()
    vpath.write_bytes(view_raw); mpath.write_bytes(manifest_raw)
    for target in (vpath, mpath):
        saved = target.read_bytes(); target.unlink()
        with pytest.raises(ContractError, match='HOST_INPUT_INCOMPLETE'): codec().verify_files(store, request)
        target.write_bytes(b'{')
        with pytest.raises(ContractError): codec().verify_files(store, request)
        target.write_bytes(saved)
    # Same grant cannot silently select the legacy mode or get a fresh reservation.
    with pytest.raises(ContractError, match='HOST_INPUT_POLICY'): run('prepare-r2')
    with pytest.raises(ContractError, match='MODEL_REQUEST_BUDGET_EXHAUSTED'): run('prepare-r2-shared')
    with store.lock('host-operation.json'):
        with pytest.raises(ContractError, match='HOST_OPERATION_LOCKED|STATE_LOCKED'): run('checkpoint')
    run('publish', 'CH08-1'); run('accept', 'CH08-1')
    future = datetime.fromisoformat(request['expires_at']) + timedelta(seconds=1)
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return future if tz is not None else future.replace(tzinfo=None)
    monkeypatch.setattr(session, 'datetime', Clock)
    monkeypatch.setattr(host_output, 'datetime', Clock)
    monkeypatch.setattr(writer, '_now', lambda: future)
    assert run('resume', 'CH08-1')['chapter_output_hash'] == digest(response['output'])
    # Accepted cache hits continue to check the original view, even after expiry.
    vpath.write_bytes(codec().file_bytes(bad))
    with pytest.raises(ContractError, match='HOST_INPUT_TRUSTED_MISMATCH'):
        writer._upstream(store, store.read('state.json')[0], {'dependencies': ['CH08']}, model, registry, cfg,
                         {'CH08-1': (store.read('CH08-1-result.json')[0], request['evidence_pack'])})
    vpath.write_bytes(view_raw)
    run('cancel')
    with pytest.raises(ContractError, match='HOST_RUN_CANCELLED'): run('resume', 'CH08-1')


def test_flat_limits_and_cache_defensive_copy(monkeypatch):
    c = codec(); raw = b'{"a":[1,2,3],"b":[1,2,3]}'
    v = c.build_view(raw); v['tree'].clear()
    assert c.decode_view(c.build_view(raw), raw) == raw
    monkeypatch.setattr(c, 'MAX_POOL', 0)
    v = c.build_view(b'{"a":1}'); v['pool'] = {'S0001': []}; reseal(v)
    with pytest.raises(ContractError, match='HOST_INPUT_POOL_LIMIT'): c.expand(v)
    with pytest.raises(ContractError): c.build_view(b' ' * (c.MAX_BYTES + 1))
    with pytest.raises(ContractError): c.build_view([])


@pytest.fixture
def roof_native_clock(tmp_path, catalog, registry, monkeypatch):
    """Fresh NOT_AI roof grant; control time, never request/hash/expiry bytes."""
    from wangbin_solar_pv.report_export import ReportModel
    from wangbin_solar_pv.serialization import loads
    from wangbin_solar_pv.reporting import host_output
    raw = (ROOT / 'tests/fixtures/solar-pv/phase7l-r2-delivery/industrial_rooftop/canonical.json').read_bytes()
    roof = ReportModel.from_result(loads(raw), catalog)
    clock = {'now': datetime.now(timezone.utc)}
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock['now'].astimezone(tz) if tz is not None else clock['now'].replace(tzinfo=None)
    monkeypatch.setattr(session, 'datetime', Clock)
    monkeypatch.setattr(host_output, 'datetime', Clock)
    monkeypatch.setattr(writer, '_now', lambda: clock['now'])
    return (*native.__wrapped__(tmp_path, roof, catalog, registry), clock)


def test_shared_unaccepted_expiry_rejects_first_native_publish(roof_native_clock):
    """QAI-R1-01: one roof run; first publish after expiry cannot publish."""
    ws, run, cfg, roof, registry, clock = roof_native_clock
    run('prepare-r2-shared')
    store = HostWorkspace(ws.root / 'native')
    request = store.read('CH08-1-request.json')[0]
    original = store.path('CH08-1-request.json').read_bytes()
    reserved = store.read('state.json')[0]['requests']
    assert request['input_view_policy'] == codec().POLICY
    assert len(reserved) == cfg.max_requests == cfg.max_attempts_per_chapter == 1
    make_draft(store, request)
    clock['now'] = datetime.fromisoformat(request['expires_at']) + timedelta(seconds=1)
    with pytest.raises(ContractError) as rejected:
        run('publish', 'CH08-1')
    assert rejected.value.code == 'MODEL_REQUEST_EXPIRED'
    assert store.path('CH08-1-request.json').read_bytes() == original
    assert store.read('state.json')[0]['requests'] == reserved
    failure = store.read('CH08-1-failure.json')[0]
    assert (failure['code'], failure['status']) == ('MODEL_REQUEST_EXPIRED', 'FAILED')
    for suffix in ('response', 'publication-intent', 'publication', 'result', 'host-record'):
        assert not store.path('CH08-1-' + suffix + '.json').exists()


def test_shared_unaccepted_expiry_rejects_native_and_core_accept(roof_native_clock, tmp_path):
    """QAI-R1-01: publish while valid, then reject both acceptance entrypoints."""
    from shutil import copytree, ignore_patterns
    ws, run, cfg, roof, registry, clock = roof_native_clock
    run('prepare-r2-shared')
    store = HostWorkspace(ws.root / 'native')
    request = store.read('CH08-1-request.json')[0]
    original = store.path('CH08-1-request.json').read_bytes()
    reserved = store.read('state.json')[0]['requests']
    assert request['input_view_policy'] == codec().POLICY
    assert len(reserved) == cfg.max_requests == cfg.max_attempts_per_chapter == 1
    response = make_draft(store, request)
    assert clock['now'] < datetime.fromisoformat(request['expires_at'])
    assert run('publish', 'CH08-1')['status'] == 'PUBLISHED_NOT_ACCEPTED'
    assert not store.path('CH08-1-result.json').exists()
    assert not store.path('CH08-1-failure.json').exists()
    published = {suffix: store.path('CH08-1-' + suffix + '.json').read_bytes()
                 for suffix in ('response', 'publication')}
    # Branch only this test's fresh, fully validated, published run BEFORE closure.
    # The copy is NOT a new authorization: all request/binding/expiry bytes stay intact.
    # Independent branches avoid deleting a failure or getting ALREADY_CLOSED instead.
    copytree(store.root, tmp_path / 'core-accept', ignore=ignore_patterns('*.host-lock'))
    core_store = HostWorkspace(tmp_path / 'core-accept')
    clock['now'] = datetime.fromisoformat(request['expires_at']) + timedelta(seconds=1)
    for target, invoke in (
        (store, lambda: run('accept', 'CH08-1')),
        (core_store, lambda: writer.accept(core_store, 'CH08-1', response, roof, registry, cfg)),
    ):
        assert target.path('CH08-1-request.json').read_bytes() == original
        with pytest.raises(ContractError) as rejected:
            invoke()
        assert rejected.value.code == 'MODEL_REQUEST_EXPIRED'
        assert not target.path('CH08-1-result.json').exists()
        assert not target.path('CH08-1-host-record.json').exists()
        assert target.path('CH08-1-request.json').read_bytes() == original
        assert target.read('state.json')[0]['requests'] == reserved
        failure = target.read('CH08-1-failure.json')[0]
        assert (failure['code'], failure['status']) == ('MODEL_REQUEST_EXPIRED', 'FAILED')
        for suffix, raw in published.items():
            assert target.path('CH08-1-' + suffix + '.json').read_bytes() == raw
