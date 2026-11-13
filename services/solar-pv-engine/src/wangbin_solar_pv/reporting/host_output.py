"""Opt-in R2 draft publication; validates/serializes, never authors or repairs text."""
from datetime import datetime, timezone
from hashlib import sha256

from ..errors import ContractError
from ..serialization import digest, dumps
from .claim_validator import validate_chapter

PROTOCOL = 'host-draft-publication/2.0-r2'
NOT_EXPOSED = 'NOT_EXPOSED_BY_HOST'
GUIDANCE = (
    '正文用自然读者语言；章节、表格、方法状态等内部ID留在元数据。'
    '本章/上游章节/待审公式不是数值；正式注册也不允许裸数字ID出现在正文。'
    '仅使用当前允许的fact槽及已注册term槽，不将金额、率、年份改写成中文数词规避校验。',
    'scope.claim_ids是允许ID池，claims.maxItems是上限而非配额。只写覆盖实际段落的必要主张，'
    'claim_ids与实际claims同序；不要写满许可池或逐字段复述。每节围绕研究问题自然成文，不固定段数。',
    '每条claim.fact_refs必须覆盖其text/conditions及每个paragraph_indexes所指段落的全部事实槽；'
    'source_refs覆盖这些事实真实source_ids，不能只因同源而漏事实。各段都须被真实主张覆盖。'
    '混合输入与指标的段落不得冒充单一INPUT_FACT/CALCULATED_METRIC；如实选择主张类型或自然拆段。',
    'SUPPORTED仅用于有事实且全部为CALCULATED/VERIFIED的既有证据；含ASSUMED、缺失或未审时'
    '使用LIMITED/UNVERIFIED，不改变事实状态。已计算不等于实测、批准或专业签审。',
    'risk_assertions声明主张实际含义而非仅匹配关键词；预算不是PAID_FEE，假设零不是已计算ZERO_VALUE。'
    '不得删除应声明风险来通过校验；无法满足既有风险证据要求就报告阻断，不输出确定性结论。',
    '保留全部必需节、表格、指标、公式与审阅信息，但避免重复claims和免责声明。'
    '完整响应只写本请求的-draft.json，不能直接写-response.json或完成标记；'
    '由已安装引擎publish严格校验后原子发布。半写失败保留原件，下一次生成必须重新prepare-r2并受原预算约束。',
)


def _require(request):
    if request.get('host_delivery') != PROTOCOL:
        raise ContractError('HOST_DELIVERY_PROTOCOL_REQUIRED')


def require_active(store):
    if store.path('host-cancelled.json').exists():
        raise ContractError('HOST_RUN_CANCELLED')


def _intent(request, raw_hash, response):
    return {'protocol': PROTOCOL, 'request_hash': request['request_hash'],
            'raw_draft_sha256': raw_hash, 'response_hash': digest(response)}


def _receipt(request, raw_hash, response, response_hash):
    output = response['output']
    return {**_intent(request, raw_hash, response), 'response_sha256': response_hash,
            'output_hash': digest(output), 'model_id': request['model_id'],
            'identity': request['binding']['identity'],
            'evidence_hash': request['evidence_pack']['evidence_hash'],
            'paragraph_sha256': {s['section_id']: [sha256(p.encode('utf8')).hexdigest()
                                                  for p in s['paragraphs']]
                                 for s in output['sections']},
            'status': 'PUBLISHED_NOT_ACCEPTED', 'semantic_gate': 'NOT_VERIFIED'}


def verify_publication(store, request):
    """Read-back verification; never repairs a receipt or trusts a status string."""
    _require(request)
    rid = request['request_id']
    try:
        draft, raw_hash = store.read(rid + '-draft.json')
        response, response_hash = store.read(rid + '-response.json')
        intent, _ = store.read(rid + '-publication-intent.json')
        receipt, _ = store.read(rid + '-publication.json')
    except FileNotFoundError:
        raise ContractError('INCOMPLETE_OUTPUT') from None
    if (draft != response or intent != _intent(request, raw_hash, response)
            or receipt != _receipt(request, raw_hash, response, response_hash)):
        raise ContractError('HOST_PUBLICATION_CHANGED')
    return receipt


def publish_response(store, request, pack, chapter, config):
    """Caller holds host-operation lock and has revalidated request/authorization."""
    _require(request)
    require_active(store)
    rid = request['request_id']
    if store.path(rid + '-failure.json').exists():
        raise ContractError('CHAPTER_ATTEMPT_ALREADY_CLOSED')
    if store.path(rid + '-publication.json').exists():
        return verify_publication(store, request)
    if store.path(rid + '-result.json').exists():
        raise ContractError('CHAPTER_ATTEMPT_ALREADY_CLOSED')
    try:
        if datetime.now(timezone.utc) > datetime.fromisoformat(request['expires_at']):
            raise ContractError('MODEL_REQUEST_EXPIRED')
        try:
            draft_path = store.path(rid + '-draft.json')
            if draft_path.stat().st_size > config.max_output_bytes:
                raise ContractError('MODEL_OUTPUT_BUDGET_EXCEEDED')
            response, raw_hash = store.read(draft_path)
            if draft_path.stat().st_size > config.max_output_bytes:
                raise ContractError('MODEL_OUTPUT_BUDGET_EXCEEDED')
        except FileNotFoundError:
            raise ContractError('INCOMPLETE_OUTPUT') from None
        except ContractError as exc:
            if exc.code == 'INVALID_JSON':
                raise ContractError('INCOMPLETE_OUTPUT') from None
            raise
        if (not isinstance(response, dict)
                or set(response) != {'request_hash', 'model_id', 'host_call_id', 'output'}):
            raise ContractError('MODEL_RESPONSE_ENVELOPE')
        if (response['request_hash'] != request['request_hash']
                or response['model_id'] != config.model_id
                or response['host_call_id'] != NOT_EXPOSED):
            raise ContractError('MODEL_RESPONSE_IDENTITY')
        if len((dumps(response) + '\n').encode('utf8')) > config.max_output_bytes:
            raise ContractError('MODEL_OUTPUT_BUDGET_EXCEEDED')
        intent_name = rid + '-publication-intent.json'
        intent = _intent(request, raw_hash, response)
        if store.path(intent_name).exists():
            if store.read(intent_name)[0] != intent:
                raise ContractError('HOST_PUBLICATION_CHANGED')
        else:
            if store.path(rid + '-response.json').exists():
                raise ContractError('OUTPUT_EXISTS')
            store.create(intent_name, intent)
        validate_chapter(response['output'], pack, chapter)
        # Re-read before publication: a concurrent writer cannot silently swap the draft.
        if store.read(rid + '-draft.json')[1] != raw_hash:
            raise ContractError('HOST_PUBLICATION_CHANGED')
        target = rid + '-response.json'
        if store.path(target).exists():
            if store.read(target)[0] != response:
                raise ContractError('HOST_PUBLICATION_CHANGED')
        else:
            store.create(target, response)
        published, response_hash = store.read(target)
        if published != response:
            raise ContractError('HOST_PUBLICATION_CHANGED')
        receipt = _receipt(request, raw_hash, response, response_hash)
        store.create(rid + '-publication.json', receipt)
        return verify_publication(store, request)
    except ContractError as exc:
        store.create(rid + '-failure.json', {'request_id': rid, 'code': exc.code,
                                           'status': 'FAILED',
                                           'recorded_at': datetime.now(timezone.utc).isoformat()})
        raise


def publication_state(store, request):
    rid = request['request_id']
    if store.path(rid + '-publication.json').exists():
        verify_publication(store, request)
        return 'OUTPUT_PUBLISHED_NOT_ACCEPTED'
    if store.path(rid + '-publication-intent.json').exists():
        return 'OUTPUT_PUBLICATION_INTERRUPTED'
    if store.path(rid + '-draft.json').exists() or store.path(rid + '-response.json').exists():
        return 'INCOMPLETE_OUTPUT'
    return 'AWAITING_AUTHORIZED_HOST'
