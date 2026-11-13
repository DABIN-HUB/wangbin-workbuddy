#!/usr/bin/env python3
"""NOT_FOR_HOST / NOT_AI / PROPOSED: whole-chapter transparent offline codecs.
Standard library only; no product imports, prose generation or model calls.
Numbers retain exact original lexemes. Trusted original bytes are always required.
View hashes prove neither authentication nor model reading/retention/semantics.
"""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import csv
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
import time

VERSION='offline-whole-chapter/1'
MAPPING='json-pointer-fields-and-number-lexemes/1'
LABEL='NOT_FOR_HOST|NOT_AI|PROPOSED'
MAX_BYTES=8*1024*1024
NUMBER=re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z')
class AuditError(ValueError): pass

def need(ok,code):
    if not ok: raise AuditError(code)

@dataclass(frozen=True)
class Num:
    token: str
    def __post_init__(self):
        need(len(self.token)<=1024 and NUMBER.fullmatch(self.token),'NUMBER_LEXEME')

def pairs(items):
    out={}
    for k,v in items:
        need(k not in out,'DUPLICATE_JSON_KEY'); out[k]=v
    return out

def bad_constant(_): raise AuditError('NON_FINITE_NUMBER')

def loads(b):
    if isinstance(b,str): b=b.encode('utf8')
    need(len(b)<=MAX_BYTES,'JSON_SIZE_LIMIT')
    try:
        v=json.loads(b.decode('utf8'),parse_int=Num,parse_float=Num,
                     object_pairs_hook=pairs,parse_constant=bad_constant)
        def check(x,n=0):
            need(n<=64,'JSON_DEPTH_LIMIT')
            if isinstance(x,dict):
                for k,y in x.items(): k.encode('utf8'); check(y,n+1)
            elif isinstance(x,list):
                for y in x: check(y,n+1)
            elif isinstance(x,str): x.encode('utf8')
        check(v); return v
    except AuditError: raise
    except (ValueError,UnicodeError,RecursionError) as exc: raise AuditError('INVALID_JSON') from exc

def text(v):
    if isinstance(v,Num): return v.token
    if v is None: return 'null'
    if type(v) is bool: return 'true' if v else 'false'
    if type(v) is int: return str(v)
    if isinstance(v,str): return json.dumps(v,ensure_ascii=False)
    if isinstance(v,list): return '['+','.join(text(x) for x in v)+']'
    if isinstance(v,dict):
        need(all(isinstance(k,str) for k in v),'STRING_KEYS_REQUIRED')
        return '{'+','.join(text(k)+':'+text(v[k]) for k in sorted(v))+'}'
    raise AuditError('NON_EXACT_JSON_TYPE')

def raw(v): return text(v).encode('utf8')
def sha(b): return hashlib.sha256(b).hexdigest()
def same(a,b): return raw(a)==raw(b)
def ptr(p): return '/'+ '/'.join(str(x).replace('~','~0').replace('/','~1') for x in p) if p else ''

def walk(v,p=()):
    yield p,v
    if isinstance(v,dict):
        for k,x in v.items(): yield from walk(x,p+(k,))
    elif isinstance(v,list):
        for i,x in enumerate(v): yield from walk(x,p+(i,))

def typ(v):
    if isinstance(v,Num): return 'number-lexeme'
    if v is None: return 'null'
    if type(v) is bool: return 'boolean'
    if isinstance(v,str): return 'string'
    if isinstance(v,list): return 'array'
    if isinstance(v,dict): return 'object'
    raise AuditError('TYPE')

def shared_payload(root):
    occurrence=defaultdict(list)
    for p,v in walk(root):
        if isinstance(v,(dict,list)):
            need(not (isinstance(v,dict) and '$shared' in v),'RESERVED_REFERENCE_KEY')
            b=raw(v)
            if len(b)>=80: occurrence[b].append(p)
    candidates={b for b,ps in occurrence.items() if len(ps)>1 and (len(ps)-1)*len(b)>80+len(ps)*24}
    pool=[]; known={}
    def encode(v,p,skip=None):
        b=raw(v) if isinstance(v,(dict,list)) else None
        if b in candidates and b!=skip:
            if b not in known:
                known[b]='S'+str(len(known)+1).zfill(4)
                value=encode(v,p,skip=b); pool.append({'id':known[b],'value':value})
            return {'$shared':known[b]}
        if isinstance(v,dict): return {k:encode(x,p+(k,)) for k,x in v.items()}
        if isinstance(v,list): return [encode(x,p+(i,)) for i,x in enumerate(v)]
        return v
    tree=encode(root,())
    points=[{'path':ptr(p),'index':ident,'original_value_bytes':len(b),
             'reason':'Exact readable recursive container equality; retains every semantic field. Index is not a formal fact/source ID and grants no permission.'}
            for b,ident in known.items() for p in occurrence[b]]
    return {'pool':sorted(pool,key=lambda r:r['id']),'tree':tree},points

def expand_shared(payload):
    need(isinstance(payload,dict) and set(payload)=={'pool','tree'},'SHARED_KEYS')
    need(isinstance(payload['pool'],list),'POOL_TYPE'); pool={}
    for entry in payload['pool']:
        need(isinstance(entry,dict) and set(entry)=={'id','value'},'POOL_ENTRY_KEYS')
        i=entry['id']; need(isinstance(i,str) and re.fullmatch(r'S[0-9]{4}',i),'INDEX_FORMAT')
        need(i not in pool,'DUPLICATE_INDEX'); pool[i]=entry['value']
    used=set(); cached={}; remaining=MAX_BYTES
    def decode(v,active=(),depth=0):
        nonlocal remaining
        need(depth<=64,'VIEW_DEPTH_LIMIT')
        if isinstance(v,dict) and '$shared' in v:
            need(set(v)=={'$shared'},'REFERENCE_UNKNOWN_KEY'); i=v['$shared']
            need(isinstance(i,str) and i in pool,'DANGLING_INDEX'); need(i not in active,'CYCLIC_INDEX'); used.add(i)
            if i not in cached: cached[i]=decode(pool[i],active+(i,),depth+1)
            remaining-=len(raw(cached[i])); need(remaining>=0,'EXPANSION_SIZE_LIMIT')
            return deepcopy(cached[i])
        if isinstance(v,dict): return {k:decode(x,active,depth+1) for k,x in v.items()}
        if isinstance(v,list): return [decode(x,active,depth+1) for x in v]
        remaining-=len(raw(v)); need(remaining>=0,'EXPANSION_SIZE_LIMIT')
        return v
    result=decode(payload['tree']); need(used==set(pool),'UNUSED_INDEX')
    need(len({raw(v) for v in cached.values()})==len(cached),'DUPLICATE_POOL_VALUE')
    return result

def flattened(v,p=()):
    # Arrays stay ordered and complete. Empty objects/arrays/null/false/0 remain distinct.
    if isinstance(v,dict) and v:
        return [(q,y) for k,x in sorted(v.items()) for q,y in flattened(x,p+(k,))]
    return [(p,v)]

def row_payload(root):
    tree=deepcopy(root); facts=tree['evidence_pack'].pop('facts'); shapes=defaultdict(list)
    for fid,f in facts.items():
        flat=flattened(f); shape=tuple((p,typ(v)) for p,v in flat)
        shapes[shape].append((fid,[v for p,v in flat]))
    groups=[]
    for shape,rows in sorted(shapes.items(),key=lambda x:repr(x[0])):
        cols=[{'path':['$fact_id'],'type':'string','mode':'cell'}]; variable=[]
        for i,(p,t) in enumerate(shape):
            c={'path':list(p),'type':t,'mode':'cell'}
            if len(rows)>1 and all(same(r[1][i],rows[0][1][i]) for r in rows): c.update(mode='constant',value=rows[0][1][i])
            else: variable.append(i)
            cols.append(c)
        groups.append({'columns':cols,'rows':[[fid]+[vals[i] for i in variable] for fid,vals in rows]})
    return {'tree_without_facts':tree,'fact_groups':groups}

def expand_rows(payload):
    need(isinstance(payload,dict) and set(payload)=={'tree_without_facts','fact_groups'},'ROW_KEYS')
    tree=deepcopy(payload['tree_without_facts']); groups=payload['fact_groups']
    need(isinstance(tree,dict) and isinstance(groups,list),'ROW_TYPE')
    need('facts' not in tree.get('evidence_pack',{}),'ROW_DUPLICATE_FACTS'); facts={}; remaining=MAX_BYTES
    for g in groups:
        need(isinstance(g,dict) and set(g)=={'columns','rows'},'GROUP_KEYS'); cols=g['columns']; rows=g['rows']
        need(isinstance(cols,list) and cols and isinstance(rows,list) and rows,'GROUP_TYPE')
        need(same(cols[0],{'path':['$fact_id'],'type':'string','mode':'cell'}),'FACT_ID_COLUMN'); paths=[]
        for c in cols[1:]:
            need(isinstance(c,dict) and c.get('mode') in ('cell','constant'),'COLUMN_MODE')
            need(set(c)==({'path','type','mode','value'} if c['mode']=='constant' else {'path','type','mode'}),'COLUMN_KEYS')
            need(isinstance(c['path'],list) and c['path'] and all(isinstance(x,str) for x in c['path']),'COLUMN_PATH')
            need(c['type'] in ('string','null','boolean','number-lexeme','array','object'),'COLUMN_TYPE')
            p=tuple(c['path']); need(not any(p==q[:len(p)] or q==p[:len(q)] for q in paths),'DUPLICATE_OR_OVERLAP_COLUMN'); paths.append(p)
            if c['mode']=='constant': need(typ(c['value'])==c['type'],'CONSTANT_TYPE')
        width=sum(c['mode']=='cell' for c in cols)
        for row in rows:
            need(isinstance(row,list) and len(row)==width,'ROW_WIDTH'); fid=row[0]
            need(isinstance(fid,str) and fid not in facts,'DUPLICATE_FACT_INDEX'); fact={}; index=1
            for c in cols[1:]:
                item=c['value'] if c['mode']=='constant' else row[index]
                remaining-=len(raw(item)); need(remaining>=0,'EXPANSION_SIZE_LIMIT')
                v=deepcopy(c['value']) if c['mode']=='constant' else row[index]
                if c['mode']=='cell': index+=1
                need(typ(v)==c['type'],'CELL_TYPE'); dest=fact
                for k in c['path'][:-1]: dest=dest.setdefault(k,{})
                dest[c['path'][-1]]=v
            facts[fid]=fact
    tree['evidence_pack']['facts']=facts
    return tree

def bind(r,b):
    return {'file_sha256':sha(b),'request_hash':r['request_hash'],'identity':r['binding']['identity'],
            'spec_hash':r['binding']['spec_hash'],'evidence_hash':r['evidence_pack']['evidence_hash'],
            **{k:r[k] for k in ('generation_run_id','request_id','report_spec_version','prompt_version','model_id','expires_at')}}

def seal(v):
    v.pop('view_hash',None); v['view_hash']=sha(raw(v)); return v

def encode_view(source,mode):
    r=loads(source); need(mode in ('shared-objects','typed-fact-rows'),'VIEW_MODE')
    payload=shared_payload(r)[0] if mode=='shared-objects' else row_payload(r)
    return seal({'version':VERSION,'mapping_version':MAPPING,'mode':mode,'label':LABEL,'binding':bind(r,source),'payload':payload})

def decode_view(v,source):
    need(isinstance(v,dict) and set(v)=={'version','mapping_version','mode','label','binding','payload','view_hash'},'VIEW_UNKNOWN_KEYS')
    need(v['version']==VERSION,'VIEW_VERSION'); need(v['mapping_version']==MAPPING,'MAPPING_VERSION')
    need(v['label']==LABEL,'OFFLINE_LABEL'); need(v['mode'] in ('shared-objects','typed-fact-rows'),'VIEW_MODE')
    need(v['view_hash']==sha(raw({k:x for k,x in v.items() if k!='view_hash'})),'VIEW_HASH')
    r=loads(source); need(same(v['binding'],bind(r,source)),'ORIGINAL_REQUEST_BINDING')
    decoded=expand_shared(v['payload']) if v['mode']=='shared-objects' else expand_rows(v['payload'])
    need(same(decoded,r),'ORIGINAL_SEMANTIC_MISMATCH')
    need(same(v,encode_view(source,v['mode'])),'NON_CANONICAL_MAPPING')
    return decoded

RISK_TASKS={
 'CH08.01':['预测非实绩','资源→转换→损失→计量点；上游方法未审'],
 'CH08.02':['月份天数/资源期间','损失顺序/已含标志；ASSUMED/SYNTHETIC'],
 'CH08.03':['退化、更换、停机重复扣减','全周期预测非实绩；付款非预算'],
 'CH08.04':['PR/等效小时/容量因子的分母、单位、期间','空值/未知不补零'],
 'CH08.05':['不可利用、限发、交付次序及计量边界','交付非收入/现金回款'],
 'CH08.06':['资源代表性/来源许可有效期/损失证据','不编造置信度；合成假设局限']}

def risk_coverage(ack):
    missing=[s for s in RISK_TASKS if ack.get(s)!=RISK_TASKS[s]]
    return {'status':'COVERAGE_INSUFFICIENT' if missing else 'CHECKLIST_PRESENT_SEMANTICS_UNVERIFIED','missing_sections':missing}

def closure(r):
    p=r['evidence_pack']; authorized=set(p['authorization_source_ids']); errors=[]; sections=[]
    if set(p['sections'])!={s['section_id'] for s in r['chapter_spec']['sections']}: errors.append('SECTION_COVERAGE')
    for spec in r['chapter_spec']['sections']:
        sid=spec['section_id']; scope=p['sections'][sid]; bad=[]
        for key,pool in [('fact_refs',p['facts']),('formula_refs',p['formulas']),('table_refs',p['tables']),('figure_refs',p['figures'])]:
            if len(scope[key])!=len(set(scope[key])) or set(scope[key])-set(pool): bad.append(key+':UNKNOWN_OR_DUPLICATE')
        if set(scope['source_refs'])-authorized: bad.append('SOURCE_AUTHORIZATION')
        for fid in scope['fact_refs']:
            if fid in p['facts'] and set(p['facts'][fid]['source_ids'])-set(scope['source_refs']): bad.append('SECTION_SOURCE_LINEAGE:'+fid)
        if scope['formula_refs']!=spec['formula_ids']: bad.append('FORMULA_PERMISSION_MAPPING')
        if scope['table_refs']!=[t['table_id'] for t in spec['tables']]: bad.append('TABLE_PERMISSION_MAPPING')
        for tid in scope['table_refs']:
            if tid in p['tables'] and set(p['tables'][tid].get('fact_ids',[]))-set(scope['fact_refs']): bad.append('TABLE_FACT_SCOPE:'+tid)
        errors.extend(sid+':'+x for x in bad); sections.append({'section_id':sid,'scope':scope,'pointer':ptr(('evidence_pack','sections',sid)),'problems':bad})
    return {'status':'REFERENCE_CLOSURE_VALID' if not errors else 'REFERENCE_CLOSURE_INSUFFICIENT','errors':errors,'sections':sections,
            'formula_policy':'Permission set, not mandatory use of every formula; claims pool is not quota.',
            'source_metadata_gap':'Complete source descriptor license/expiry is not carried for each fact; source authorization is not proof of validity.',
            'professional_semantics':'NOT_TESTED'}

def selfcheck():
    assert callable(globals().get('encode_view')), 'whole-chapter transparent reversible codec is not implemented'
    assert callable(globals().get('decode_view')), 'strict original-bound decoder is not implemented'
    checks=[]; v=loads(b'{"n":9007199254740993,"d":1.2300e-40,"z":-0,"f":false,"null":null,"empty":[],"object":{}}')
    need(text(v['n'])=='9007199254740993' and text(v['d'])=='1.2300e-40' and text(v['z'])=='-0','EXACT_NUMBERS')
    need(not same(Num('0'),False) and not same(None,[]) and not same({},[]),'DISTINCT_SENTINELS')
    checks.append({'case':'large_integer_exponent_negative_zero_null_false_empty_missing','status':'PASS'})
    for name,b in [('duplicate_json_key',b'{"a":1,"a":2}'),('nan',b'NaN'),('infinity',b'Infinity'),('invalid_number',b'01'),('invalid_utf8',b'"\xff"'),('trailing_data',b'{}{}')]:
        try: loads(b)
        except AuditError as exc: checks.append({'case':name,'status':'REJECTED','code':str(exc)})
        else: raise AuditError('SELF_CHECK_ACCEPTED:'+name)
    # Synthetic sentinel coverage is explicitly NOT-AI and never a project fact.
    synthetic={'request_hash':'SYNTHETIC_SELF_CHECK','binding':{'identity':{'model_version':'SYNTHETIC','run_id':'SYNTHETIC','input_hash':'SYNTHETIC','source_snapshot_id':'SYNTHETIC','result_hash':'SYNTHETIC'},'spec_hash':'SYNTHETIC'},
      'generation_run_id':'SYNTHETIC','request_id':'SYNTHETIC','report_spec_version':'SYNTHETIC','prompt_version':'SYNTHETIC','model_id':'NOT_AI','expires_at':'UNCHANGED_SYNTHETIC',
      'evidence_pack':{'evidence_hash':'SYNTHETIC','facts':{}}}
    values=[None,Num('0'),False,[],{},Num('-0'),Num('9007199254740993'),Num('1.2300e-40'),'UNKNOWN','ASSUMED','SUPPORTED','SYNTHETIC','NOT_APPLICABLE','CONFLICT']
    for i,value in enumerate(values):
        synthetic['evidence_pack']['facts']['SYNTHETIC:'+str(i)]={'value':value,'status':str(i),'period':None}
    synthetic['evidence_pack']['facts']['SYNTHETIC:missing']={'status':'UNKNOWN'}
    for mode in ('shared-objects','typed-fact-rows'):
        source=raw(synthetic); decoded=decode_view(loads(raw(encode_view(source,mode))),source)
        need(same(decoded,synthetic),'SYNTHETIC_SENTINEL_CODEC')
        checks.append({'case':'synthetic_all_sentinels_and_status_strings_roundtrip','mode':mode,'status':'PASS_NOT_AI'})
    return checks

def negative_checks(source):
    r=loads(source); cases=[]; facts=r['evidence_pack']['facts']; first=next(iter(facts)); numeric=next(k for k,v in facts.items() if isinstance(v.get('value'),Num))
    def reject(name,v,mode):
        try: decode_view(v,source)
        except AuditError as exc: cases.append({'case':name,'mode':mode,'result':'REJECTED','code':str(exc)})
        else: raise AuditError('NEGATIVE_ACCEPTED:'+name+':'+mode)
    mutations=[
      ('delete_fact',lambda x:x['evidence_pack']['facts'].pop(first)),
      ('remove_source',lambda x:x['evidence_pack']['facts'][first].update(source_ids=[])),
      ('change_status',lambda x:x['evidence_pack']['facts'][first].update(status='VERIFIED')),
      ('change_exact_number',lambda x:x['evidence_pack']['facts'][numeric].update(value=Num('9007199254740993.0000000000000001'))),
      ('change_unit',lambda x:x['evidence_pack']['facts'][numeric].update(unit='WRONG_UNIT')),
      ('change_period',lambda x:x['evidence_pack']['facts'][first].update(period={'year':Num('2099')})),
      ('wrong_project',lambda x:x['binding']['identity'].update(run_id='WRONG_PROJECT')),
      ('cross_section_permission',lambda x:x['evidence_pack']['sections']['CH08.01']['fact_refs'].append(next(f for f in facts if f not in x['evidence_pack']['sections']['CH08.01']['fact_refs']))),
      ('missing_table_row',lambda x:next(t for t in x['evidence_pack']['tables'].values() if t.get('fact_ids'))['fact_ids'].pop()),
      ('unknown_original_key',lambda x:x['evidence_pack']['facts'][first].update(unknown_key='not allowed')),
      ('remove_research_task',lambda x:x['chapter_spec']['sections'][0]['analysis_tasks'].pop()),
      ('remove_schema',lambda x:x.pop('output_schema')),
      ('remove_risk_guidance',lambda x:x['writing_guidance'].pop(4))]
    for mode in ('shared-objects','typed-fact-rows'):
        base=encode_view(source,mode)
        # Rebuild/reseal modified views to test the semantic guard, not just hash mismatch.
        for name,mutate in mutations:
            changed=deepcopy(r); mutate(changed); v=encode_view(raw(changed),mode); v['binding']=deepcopy(base['binding']); seal(v); reject(name,v,mode)
        for name,k,val in [('wrong_version','version','offline-whole-chapter/0'),('wrong_mapping','mapping_version','wrong/1'),('unknown_envelope_key','unknown',True)]:
            v=deepcopy(base); v[k]=val; seal(v); reject(name,v,mode)
        v=deepcopy(base); v['view_hash']='0'*64; reject('view_tampering',v,mode)
        v=deepcopy(base); v['binding']['generation_run_id']='OLD_VIEW'; seal(v); reject('old_view_impersonation',v,mode)
        if mode=='shared-objects':
            need(bool(base['payload']['pool']),'NEGATIVE_NEEDS_POOL')
            v=deepcopy(base); v['payload']['pool'].append(deepcopy(v['payload']['pool'][0])); seal(v); reject('duplicate_index',v,mode)
            v=deepcopy(base); v['payload']['tree']={'$shared':'S9999'}; seal(v); reject('dangling_index',v,mode)
            v=deepcopy(base); v['payload']['pool'][0]['value']={'$shared':v['payload']['pool'][0]['id']}; seal(v); reject('cyclic_index',v,mode)
            v=deepcopy(base); v['payload']['pool'][0]['unknown']=True; seal(v); reject('unknown_pool_key',v,mode)
        else:
            v=deepcopy(base); g=v['payload']['fact_groups'][0]; g['rows'].append(deepcopy(g['rows'][0])); seal(v); reject('duplicate_index',v,mode)
            v=deepcopy(base); v['payload']['fact_groups'][0]['rows'][0].pop(); seal(v); reject('dangling_row_cell',v,mode)
            v=deepcopy(base); v['payload']['fact_groups'][0]['columns'][1]['path']=['wrong','mapping']; seal(v); reject('incorrect_column_mapping',v,mode)
            v=deepcopy(base); v['payload']['fact_groups'][0]['columns'][1]['unknown']=True; seal(v); reject('unknown_column_key',v,mode)
    insufficient=risk_coverage({}); need(insufficient['status']=='COVERAGE_INSUFFICIENT','RISK_COVERAGE_MUST_NOT_PASS')
    cases.append({'case':'risk_coverage_insufficient','result':'COVERAGE_INSUFFICIENT','missing_sections':insufficient['missing_sections']})
    return cases

def percent(a,b): return str((Decimal(a)*100/Decimal(b)).quantize(Decimal('.0001')))

def profile(source,readable):
    r=loads(source); p=r['evidence_pack']; leaves=[]; duplicates=defaultdict(list); buckets=Counter()
    for path,v in walk(r):
        if isinstance(v,(dict,list)): duplicates[raw(v)].append(ptr(path))
        if not isinstance(v,(dict,list)) or not v:
            s=ptr(path); leaves.append({'path':s,'type':typ(v),'value_utf8_bytes':len(raw(v)),'key_utf8_bytes':len(raw(str(path[-1]))) if path and isinstance(path[-1],str) else 0})
            tag='other'
            if s.startswith('/evidence_pack/facts/'):
                tag='fact_other'
                for name,part in [('source_locator','/source_location'),('source_ids','/source_ids/'),('status','/status'),('numeric_value','/value'),('provenance','/provenance/')]:
                    if part in s: tag=name; break
            elif s.startswith('/evidence_pack/formulas'): tag='formulas'
            elif s.startswith('/evidence_pack/tables'): tag='tables'
            elif s.startswith('/output_schema'): tag='schema'
            elif s.startswith(('/instructions','/writing_guidance')): tag='guidance'
            buckets[tag]+=len(raw(v))
    repeat=[{'value_sha256':sha(b),'value_bytes':len(b),'occurrences':len(ps),'paths':ps} for b,ps in duplicates.items() if len(ps)>1]
    result={'file_bytes':len(source),'file_sha256':sha(source),'request_hash':r['request_hash'],'readable_bytes':len(readable),'readable_sha256':sha(readable),'readable_lines':len(readable.splitlines()),'readable_exact_semantic_equal':same(r,loads(readable)),
      'original_serializer_plus_lf_matches_bytes':raw(r)+b'\n'==source,
      'top_level':{k:{'value_bytes':len(raw(v)),'share_of_file_percent':percent(len(raw(v)),len(source))} for k,v in r.items()},
      'component_value_bytes':{k:len(raw(p[k])) for k in ('facts','formulas','tables','terms','sections')},
      'leaf_value_categories_bytes_nonoverlapping':dict(buckets),'leaf_note':'Leaf values exclude keys/punctuation. Top-level/nested values overlap; do not add them.',
      'fact_count':len(p['facts']),'formula_count':len(p['formulas']),'table_count':len(p['tables']),'term_count':len(p['terms']),
      'identity':r['binding']['identity'],'model_config':r['binding']['model_config'],
      'sections':{sid:{'fact_count':len(s['fact_refs']),'facts_object_bytes':len(raw({f:p['facts'][f] for f in s['fact_refs']}))} for sid,s in p['sections'].items()},
      'status_counts':dict(Counter(f['status'] for f in p['facts'].values())),'token_count':'UNKNOWN_NO_AUTHORIZED_HY4_TOKENIZER','closure':closure(r)}
    return result,leaves,repeat

def coverage_rows(r,case):
    p=r['evidence_pack']; rows=[]
    for i,spec in enumerate(r['chapter_spec']['sections']):
        sid=spec['section_id']; s=p['sections'][sid]
        facts=[{'fact_id':fid,'pointer':ptr(('evidence_pack','facts',fid)),'source_ids':p['facts'][fid]['source_ids'],'source_location':p['facts'][fid].get('source_location'),'status':p['facts'][fid]['status'],'period':p['facts'][fid].get('period'),'boundary':p['facts'][fid].get('boundary')} for fid in s['fact_refs']]
        common={'case':case,'section_id':sid,'section_title':spec['section_title'],'task_pointer':ptr(('chapter_spec','sections',i,'analysis_tasks')),
          'facts_and_source_locators':text(facts),'scope_pointer':ptr(('evidence_pack','sections',sid)),'source_ids':text(s['source_refs']),
          'source_license_expiry_gap':'Complete per-source descriptor/expiry not carried; authorization != validity.',
          'formula_permission_ids_not_quota':text(s['formula_refs']),'formula_pointers':text([ptr(('evidence_pack','formulas',x)) for x in s['formula_refs']]),
          'table_ids_and_pointers':text([{'id':x,'pointer':ptr(('evidence_pack','tables',x)),'ordered_fact_ids':p['tables'][x].get('fact_ids',[])} for x in s['table_refs']]),
          'audit_risk_checklist_not_production_rule':text(RISK_TASKS[sid]),'risk_origin':'User task reviewer checklist, not a generated finding or new production rule.',
          'risk_original_pointers':text([ptr(('chapter_spec','sections',i,'output_acceptance')),'/writing_guidance','/evidence_pack/constraints']),
          'original_missing_evidence':text(s['missing_evidence']),'missing_behavior':spec['missing_evidence_behavior'],
          'output_requirements':text(spec['output_acceptance']),'output_schema_pointer':'/output_schema',
          'upstream_unfinished':text(r['upstream_status']),'closure':'REFERENCE_CLOSURE_VALID','professional_semantics':'NOT_TESTED'}
        for task in spec['analysis_tasks']: rows.append({**common,'research_task':task})
    return rows

def write_new(p,b):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f: f.write(b)

def run(original_root,out):
    started=time.monotonic(); out=Path(out); need(not out.exists(),'OUTPUT_ALREADY_EXISTS'); out.mkdir(parents=True)
    profiles={}; validations={}; rows=[]
    for case,run_name in [('industrial_rooftop','roof-primary'),('utility_scale_ground','ground-primary')]:
        base=Path(original_root)/'workspaces'/case; rp=base/run_name/'CH08-1-request.json'; cp=base/'CH08-request-readable.json'
        source=rp.read_bytes(); readable=cp.read_bytes(); r=loads(source); p,leaves,repeat=profile(source,readable)
        p.update(original_path=str(rp),readable_path=str(cp)); p['views']={}
        for mode in ('shared-objects','typed-fact-rows'):
            v=encode_view(source,mode); encoded=raw(v)+b'\n'; decoded=decode_view(loads(encoded),source); file=out/(case+'-'+mode+'.json'); write_new(file,encoded)
            p['views'][mode]={'bytes':len(encoded),'file_sha256':sha(encoded),'view_hash':v['view_hash'],'version':VERSION,'mapping_version':MAPPING,
              'semantic_equal_with_number_lexemes':same(decoded,r),'reconstructed_original_bytes_equal':raw(decoded)+b'\n'==source,
              'saved_bytes':len(source)-len(encoded),'reduction_percent':percent(len(source)-len(encoded),len(source)),'path':str(file)}
        for suffix,data in [('leaves',leaves),('duplicate-containers',repeat),('shared-paths-and-reasons',shared_payload(r)[1])]: write_new(out/(case+'-'+suffix+'.json'),raw(data)+b'\n')
        row_map=[]
        for gi,g in enumerate(row_payload(r)['fact_groups']):
            for row in g['rows']:
                cell=1
                for ci,c in enumerate(g['columns'][1:],1):
                    row_map.append({'original_path':ptr(('evidence_pack','facts',row[0],*c['path'])),
                      'view_group':gi,'view_column':ci,'type':c['type'],'mode':c['mode'],
                      'row_cell':cell if c['mode']=='cell' else None,
                      'reason':'Explicit typed column; identical constant is printed once in header, otherwise original value remains in its row. No formal ID or section permission changes.'})
                    if c['mode']=='cell': cell+=1
        write_new(out/(case+'-typed-row-field-mapping.json'),raw(row_map)+b'\n')
        detail_rows=coverage_rows(r,case)
        write_new(out/(case+'-coverage-detail.json'),raw(detail_rows)+b'\n')
        sub=deepcopy(r); sub['evidence_pack']['facts']={f:r['evidence_pack']['facts'][f] for f in r['evidence_pack']['sections']['CH08.02']['fact_refs']}
        p['CH08.02_hotspot_only_not_a_model_call']={'facts':len(sub['evidence_pack']['facts']),'original_facts_bytes':len(raw(sub['evidence_pack']['facts'])),
          'standalone_shared_facts_representation_bytes':len(raw(shared_payload(sub['evidence_pack']['facts'])[0])),
          'typed_fact_groups_bytes':len(raw(row_payload(sub)['fact_groups'])),'note':'Overlapping attribution only; never subsection host calls.'}
        profiles[case]=p; validations[case]={'positive':{'both_modes':'EXACT_SEMANTIC_EQUAL_LEXEMES_PRESERVED','five_identity_spec_all_states_references_schema_and_six_tasks':'UNCHANGED_BY_EXACT_TREE_COMPARISON'},
          'negative':negative_checks(source),'source_inputs':[{'path':str(rp),'bytes':len(source),'sha256':sha(source)},{'path':str(cp),'bytes':len(readable),'sha256':sha(readable)}]}
        compact_rows=deepcopy(detail_rows)
        for entry in compact_rows:
            sid=entry['section_id']; scope=r['evidence_pack']['sections'][sid]
            entry['facts_and_source_locators']=text({'fact_ids':scope['fact_refs'],
              'original_fact_pointer_prefix':'/evidence_pack/facts/',
              'source_locator_fields':['source_ids','source_location','provenance'],
              'complete_period_boundary_status_and_source_mapping':str(out/(case+'-coverage-detail.json')),
              'fact_count':len(scope['fact_refs'])})
        rows.extend(compact_rows); need(p['readable_exact_semantic_equal'] and p['closure']['status']=='REFERENCE_CLOSURE_VALID','INPUT_CLOSURE_OR_READABLE_MISMATCH')
    report={'label':LABEL,'decoder_version':VERSION,'mapping_version':MAPPING,'python_executable':sys.executable,'python_version':sys.version,'status':'PASS_AUTHOR_OFFLINE_SELF_CHECK_ONLY','independent_qa':'NOT_RUN_PENDING','product_tests':'NOT_RUN','professional_semantics':'NOT_TESTED',
      'primitive_checks':selfcheck(),'cases':validations,'seconds':str(Decimal(str(time.monotonic()-started))),
      'limitations':['No model capacity, safety policy resolution, context retention or professional correctness proved.','Decoder requires trusted original bytes; unsigned hashes are not authentication.','Audit risk checklist is not natural-language validation; production optional risk_assertions unchanged.','No host, prepare, publish, accept, resume, finance, Word, dependency installation or pytest.']}
    write_new(out/'REQUEST_PROFILE.json',raw(profiles)+b'\n'); write_new(out/'OFFLINE_VALIDATION.json',raw(report)+b'\n')
    with (out/'CH08_COVERAGE.csv').open('x',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(text({'status':report['status'],'measurements':{k:{'original_bytes':v['file_bytes'],'views':v['views'],'hotspot':v['CH08.02_hotspot_only_not_a_model_call']} for k,v in profiles.items()},
                'negative_cases':{k:len(v['negative']) for k,v in validations.items()},'coverage_rows':len(rows),'seconds':report['seconds'],'independent_qa':'NOT_RUN_PENDING'})); return 0

def inspect_readonly(original_root):
    """Independent QA entry: recompute everything in memory; writes no files."""
    start=time.monotonic(); results={}
    for case,run_name in [('industrial_rooftop','roof-primary'),('utility_scale_ground','ground-primary')]:
        base=Path(original_root)/'workspaces'/case
        source=(base/run_name/'CH08-1-request.json').read_bytes()
        r=loads(source); view_results={}
        need(r['request_hash']==sha(raw({k:v for k,v in r.items() if k!='request_hash'})),'REQUEST_HASH')
        pack=r['evidence_pack']
        need(pack['evidence_hash']==sha(raw({k:v for k,v in pack.items() if k!='evidence_hash'})),'EVIDENCE_HASH')
        for mode in ('shared-objects','typed-fact-rows'):
            view=encode_view(source,mode); encoded=raw(view)+b'\n'
            decoded=decode_view(loads(encoded),source)
            view_results[mode]={'bytes':len(encoded),'file_sha256':sha(encoded),'view_hash':view['view_hash'],
                               'semantic_equal':same(decoded,r),'reconstructed_original_bytes_equal':raw(decoded)+b'\n'==source}
        p,leaves,repeat=profile(source,(base/'CH08-request-readable.json').read_bytes())
        need(p['readable_exact_semantic_equal'] and p['closure']['status']=='REFERENCE_CLOSURE_VALID','QA_CLOSURE_OR_READABLE')
        results[case]={'file_sha256':sha(source),'request_hash':r['request_hash'],'original_bytes':len(source),
          'views':view_results,'closure':p['closure'],'negative_cases':negative_checks(source),
          'fact_count':len(pack['facts']),'coverage_rows':len(coverage_rows(r,case)),
          'leaf_count':len(leaves),'duplicate_container_groups':len(repeat)}
    return {'status':'PASS_OFFLINE_CHECKS_CALLER_INDEPENDENCE_NOT_ASSERTED','writes':False,
      'python_executable':sys.executable,'python_version':sys.version,
      'script_sha256':sha(Path(__file__).read_bytes()),'version':VERSION,'mapping_version':MAPPING,
      'primitive_checks':selfcheck(),'cases':results,'seconds':str(Decimal(str(time.monotonic()-start))),
      'professional_semantics':'NOT_TESTED','host_capacity_safety_root_cause':'UNKNOWN'}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('run'); p.add_argument('--original-root',required=True); p.add_argument('--out',required=True)
    p=sub.add_parser('verify'); p.add_argument('--request',required=True); p.add_argument('--view',required=True)
    p=sub.add_parser('readonly'); p.add_argument('--original-root',required=True)
    sub.add_parser('selfcheck'); a=parser.parse_args(argv)
    try:
        if a.action=='readonly': print(text(inspect_readonly(a.original_root))); return 0
        if a.action=='run': return run(a.original_root,a.out)
        if a.action=='selfcheck': print(text({'checks':selfcheck(),'status':'PASS_AUTHOR_SELF_CHECK_ONLY'})); return 0
        source=Path(a.request).read_bytes(); v=loads(Path(a.view).read_bytes()); decoded=decode_view(v,source)
        print(text({'status':'VERIFIED_AGAINST_ORIGINAL','view_hash':v['view_hash'],'file_sha256':sha(source),'request_hash':decoded['request_hash'],
                    'semantic_equal_with_number_lexemes':True,'original_bytes_equal':raw(decoded)+b'\n'==source,'closure':closure(decoded)['status'],'professional_semantics':'NOT_TESTED'})); return 0
    except (AuditError,OSError,KeyError,TypeError,IndexError,RecursionError) as exc:
        print(text({'status':'REJECTED','code':str(exc) if isinstance(exc,AuditError) else type(exc).__name__})); return 2

if __name__=='__main__': raise SystemExit(main())
