"""Independent cross-file accounting checks; no product tests or source writes."""
import collections,json,pathlib
from decimal import Decimal
def verify(root):
 root=pathlib.Path(root)
 def load(p):return json.loads((root/p).read_text())
 def rows(p):return [json.loads(x) for x in (root/p).read_text().splitlines() if x]
 s=load('analysis/summary.json');p=load('analysis/pricing.json');x=load('analysis/scope-exclusions.json')
 users=rows('analysis/user-classifications.jsonl');us=rows('analysis/usage-by-response.jsonl')
 assert len(users)==s['requests']
 keys=[(u['original_message_identity']['session_id'],u['original_message_identity']['message_id_or_ordinal']) for u in users]
 assert len(set(keys))==len(keys),'duplicate native user message'
 assert set(u['posthoc']['category'] for u in users)<={'오류 정정','정책 결정','신규 요청','환경 지원','상태 질문','미확인'}
 assert all(u['posthoc']['reason'] and u['posthoc']['provenance']=='POSTHOC_AGENT_REVIEW' for u in users)
 excluded={r['event_id'] for r in x['previous_30_requests']['excluded']}
 assert len(excluded)==8 and not excluded&{u['canonical_event_id'] for u in users}
 assert x['previous_30_requests']['harness_requests']==7 and x['previous_30_requests']['environment_injection']==1
 assert s['original_30_scope']['retained_count']+len(excluded)==30
 assert sum(s['original_30_scope']['posthoc_categories'].values())==22
 excluded_usage={r['event_id'] for r in x['mixed_request_usage_excluded']}
 assert not excluded_usage&{r['event_id'] for r in us}
 assert len({(r['session_id'],r['response_id']) for r in us})==len(us)==s['usage_responses']
 mixed_requests={u['canonical_event_id'] for u in users if u['posthoc'].get('mixed_scope')}
 assert all(not (mixed_requests&set(r['request_event_ids'])) or r['original_binding_event_ids'] for r in us)
 for r in us:
  assert r['actual_billed_usd']=='UNKNOWN'
  if not r['token_math_valid']:continue
  assert r['normal_input_tokens']>=0 and r['cached_input_tokens']>=0
  assert r['normal_input_tokens']+r['cached_input_tokens']==r['raw_usage']['input_tokens']
  # Sum the disjoint token classes, never inclusive input plus cache.
  assert r['normal_input_tokens']+r['cached_input_tokens']+r['output_tokens']==r['raw_usage']['total_tokens']
  for scenario,rate in p['scenarios'].items():
   expected=sum(Decimal(r[k])*Decimal(str(rate[n])) for k,n in [('normal_input_tokens','normal_input'),('cached_input_tokens','cached_input'),('output_tokens','output')])/Decimal(1000000)
   if r['model']==p['model']:assert Decimal(r['api_equivalent_usd_'+scenario])==expected
 fields=['normal_input_tokens','cached_input_tokens','output_tokens','total_tokens']
 for st in s['stage_totals']:
  bucket=[r for r in us if r['stage']==st['stage']]
  assert len(bucket)==st['responses']
  for f in fields:
   measured=sum((r['normal_input_tokens']+r['cached_input_tokens']+r['output_tokens']) if f=='total_tokens' else r[f] for r in bucket if r['token_math_valid'])
   assert measured==st[f],(st['stage'],f)
 for f in fields+['responses']:
  assert sum(t[f] for t in s['task_stage_totals'])==s['total_observed_scoped'][f]
  assert sum(t[f] for t in s['stage_totals'])==s['total_observed_scoped'][f]
 # Rework buckets are disjoint subsets, not an added cost component.
 accounted=set()
 for bucket in s['rework_subsets']:
  rs=[r for r in us if (len(r['rework_episodes'])>1 if bucket['episode']=='MULTI_EPISODE_UNALLOCATED' else r['rework_episodes']==[bucket['episode']] and r['rework_link_strength']==bucket['strength'])]
  ids={r['event_id'] for r in rs};assert not accounted&ids;accounted|=ids
  assert len(rs)==bucket['responses']
 assert s['whole_v1_usage']==s['whole_v1_cost']==s['actual_billed_usd']=='UNKNOWN'
 return {'result':'PASS','requests':len(users),'responses':len(us),'scope_exclusions':8,'mixed_usage_exclusions':len(excluded_usage),'checks':['native message identity uniqueness','six category schema with reasons and posthoc labels','old30=22 retained+8 excluded','mixed turn usage absent unless explicitly task bound','response identity uniqueness','cache decomposition and inclusive token reconciliation','per-response Decimal cost formula','stage and task-stage partitions','rework is disjoint subset, never additional total','actual bill and whole-v1 totals remain UNKNOWN'],'limit':'Accounting and export consistency, not proof of semantic classification accuracy or complete collection'}
if __name__=='__main__':
 import sys
 print(json.dumps(verify(sys.argv[1]),ensure_ascii=False,indent=2))
