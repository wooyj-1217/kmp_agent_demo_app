"""Evidence-labelled retrospective classifications and token/cost analysis."""
import collections,csv,datetime,hashlib,json,pathlib,re
from decimal import Decimal
from html.parser import HTMLParser
from study_annotations import A,EXCLUDED
STAGES=['기획','디자인','구현','검증','수정','보고서','귀속 불명']
class Visible(HTMLParser):
 def __init__(self):super().__init__();self.skip=0;self.text=[]
 def handle_starttag(self,t,a):
  if t in {'script','style'}:self.skip+=1
 def handle_endtag(self,t):
  if t in {'script','style'}:self.skip-=1
 def handle_data(self,d):
  if not self.skip:self.text.append(d)
def enrich(R,OUT,events,tasks,read,write,jsonl,clean):
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 read('tools/v1-report/study_annotations.py');read('tools/v1-report/study_enrichment.py')
 byid={e['event_id']:e for e in events}
 def identity(e):
  s=e.get('source',{});n=s.get('native_ids',{}); sid=s.get('session_id','UNKNOWN')
  mid=n.get('id') or e.get('observed',{}).get('message_id')
  return (sid,mid or 'ordinal:'+str(s.get('record_ordinal',e['event_id'])))
 def turn(e):
  o=e.get('observed',{});return (e.get('source',{}).get('session_id') or o.get('thread_id'),o.get('session_turn_id') or o.get('turn_id'))
 users={}; duplicates=[]
 for e in events:
  if e['event_type']!='session_message' or e.get('observed',{}).get('role')!='user' or e['event_id'] not in A:continue
  k=identity(e)
  if k in users:duplicates.append({'duplicate_event_id':e['event_id'],'canonical_event_id':users[k]['event_id'],'identity':k});continue
  users[k]=e
 intervention_events=[e for e in events if e['event_type'] in {'human_intervention','human_intervention_pending'}]
 classified=[];turn_annotations=collections.defaultdict(list)
 for k,e in users.items():
  a=dict(A[e['event_id']]);o=e['observed'];text='\n'.join(c.get('text','') for c in o.get('content',[]) if isinstance(c,dict))
  text=re.sub(r'<INSTRUCTIONS>.*?</INSTRUCTIONS>|<environment_context>.*?</environment_context>','[OMITTED]',text,flags=re.S)
  originals=[]
  for i in intervention_events:
   q={**i.get('agent_summary',{}),**i.get('observed',{})}
   if q.get('source_event_id')==e['event_id'] or (q.get('source_session_id')==k[0] and q.get('source_message_id')==k[1]):
    originals.append({'event_id':i['event_id'],'event_type':i['event_type'],'classification':i.get('agent_summary',{}).get('classification','UNKNOWN'),'basis':i.get('agent_summary',{}).get('basis',i.get('agent_summary',{}).get('text','UNKNOWN')),'task_id':i.get('task_id'),'agent_run_id':i.get('agent_run_id'),'pending_event_id':i.get('agent_summary',{}).get('pending_event_id','UNKNOWN')})
  classified.append({'canonical_event_id':e['event_id'],'original_message_identity':{'session_id':k[0],'message_id_or_ordinal':k[1]},'source':e['source'],'occurred_at':o.get('occurred_at'),'turn_id':turn(e)[1],'request_excerpt':text[:20000],'original_classifications':originals or 'UNKNOWN','posthoc':a,'task_link_status':'POSTHOC_CONTEXT_NOT_ORIGINAL_BINDING','analyst':'Codex retrospective review','classified_at':now})
  turn_annotations[turn(e)].append((e,a))
 jsonl('analysis/user-classifications.jsonl',classified)
 # Read only filtered native call metadata; never copy arguments, reasoning or session files.
 native={}; native_provenance=[]
 for e in events:
  if e['event_type']!='model_usage':continue
  p=e.get('source',{}).get('path')
  if not p or p in native:continue
  path=pathlib.Path(p)
  if not path.is_file():native[p]=None;continue
  blob=path.read_bytes(); rows=[json.loads(l) for l in blob.splitlines() if l.strip()]
  native_provenance.append({'source_path':clean(p),'source_sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob),'copied':False})
  segments={}; calls=[]
  for line,d in enumerate(rows,1):
   q=d.get('payload',{})
   if d.get('type')=='response_item' and q.get('type') in {'custom_tool_call','function_call'}:
    calls.append({'line':line,'call_id':q.get('call_id'),'tool':q.get('name'),'text':str(q.get('input',q.get('arguments','')))})
   if d.get('type')=='token_usage_record':
    segments[q.get('response_id')]=(line,calls);calls=[]
  native[p]=segments
 bindings=collections.defaultdict(list)
 for e in events:
  if e['event_type']=='usage_attributed' and e.get('task_id') in tasks:
   o=e['observed'];bindings[(o.get('session_id'),o.get('response_id'))].append(e)
 task_episodes={'V1-DESIGN-CONFORMANCE':'DESIGN_CONFORMANCE','V1-AGREEMENT-REVIEW':'AGREEMENT_DEVIATION','V1-SETTINGS-ALIGNMENT':'TARGET_SETTINGS_CORRECTION'}
 def infer_task(paths,text):
  candidates=set(re.findall(r'\b(?:V1-[A-Z][A-Z-]+|TASK-00[1-5])\b',text)) & tasks.keys()
  for p in paths:
   if p.startswith('androidApp/'):candidates.add('V1-ANDROID')
   if p.startswith('iosApp/'):candidates.add('V1-IOS')
   if p.startswith('server/'):candidates.add('V1-SERVER')
   if p.startswith('shared/'):candidates.add('V1-SHARED')
   if p.startswith('web/'):candidates.add('V1-WEB')
  return sorted(candidates)
 def path_stage(p,correction):
  if p.startswith(('tools/v1-report/','reports/')):return '보고서'
  if re.search(r'AcceptanceTest|UITests|src/.*[Tt]est|/(?:test|verify|acceptance|control_fixture)[^/]*\.py|\.harness/v1/.*(?:summary|review|verification|acceptance)',p):return '검증'
  if p.startswith(('androidApp/','iosApp/','server/','shared/','web/')):return '수정' if correction else '구현'
  if 'design' in p and p.endswith(('.md','.html','.css','.json')):return '수정' if correction else '디자인'
  return None
 usage_rows=[]; seen={}; usage_duplicates=[]; mixed_usage_excluded=[]
 for e in events:
  if e['event_type']!='model_usage':continue
  o=e['observed'];s=e.get('source',{});key=(s.get('session_id'),o.get('response_id'))
  anns=turn_annotations.get(turn(e),[]);bs=bindings.get(key,[])
  if not anns and not bs:continue
  if any(a.get('mixed_scope') for _,a in anns) and not bs:
   mixed_usage_excluded.append({'event_id':e['event_id'],'session_id':key[0],'response_id':key[1],'request_event_ids':[q['event_id'] for q,a in anns],'reason':'mixed product/harness request; no explicit product task usage binding; excluded from token and cost totals'})
   continue
  if not all(key) or 'UNKNOWN' in key:continue
  if key in seen:
   usage_duplicates.append({'event_id':e['event_id'],'canonical_event_id':seen[key],'response_id':key[1]});continue
  seen[key]=e['event_id']
  entry=(native.get(s.get('path')) or {}).get(key[1]);calls=entry[1] if entry and entry[0]==s.get('line') else []
  text='\n'.join(c['text'] for c in calls)
  # Decode escaped patch line breaks only, without evaluating any tool code.
  decoded=text.replace('\\\\n','\n').replace('\\n','\n')
  paths=[p.strip().strip('"').removeprefix(str(R)+'/') for p in re.findall(r'\*\*\* (?:Add|Update|Delete) File: ([^\n]+)',decoded)]
  matched_tasks=infer_task(paths,text)
  btasks=sorted({b['task_id'] for b in bs});atasks=sorted({t for _,a in anns for t in a['tasks']})
  taskids=btasks or matched_tasks or atasks
  link_basis='CONTEMPORANEOUS_EXPLICIT_PARTIAL' if bs else ('POSTHOC_TOOL_ARTIFACT_CONTEXT' if matched_tasks else 'POSTHOC_REQUEST_CONTEXT')
  # Keep report-only work out of product task-cost assignments when paths merely cite product code.
  hints={a['stage_hint'] for _,a in anns if a['stage_hint']!='UNKNOWN'}
  episodes={task_episodes[t] for t in taskids if t in task_episodes}
  episodes.update(a['rework_episode'] for _,a in anns if a['rework_episode'])
  mixed=any(a.get('mixed_scope') for _,a in anns)
  correction=bool(episodes-{'DESIGN_CHANGE_REQUEST'})
  candidates={x for p in paths if (x:=path_stage(p,correction))}
  reasons=[]
  if hints=={'보고서'}:candidates={'보고서'};reasons.append('요청 전체가 보고서/분석 범위; 내부 표시 검증 포함')
  elif not candidates:
   if re.search(r'acceptance|xcresult|connectedDebugAndroidTest|(?:gradle|gradlew)[^\n]{0,180}(?:test|Test)|xcodebuild[^\n]{0,180}test|(?:verify|test)\.py',text,re.I):candidates={'검증'};reasons.append('응답 경계 내부 도구에 시험/검증 명령 근거')
   elif len(hints)==1 and not mixed:candidates=hints;reasons.append('단일 요청 단계 문맥; 세부 응답 단계 직접 관측 아님')
   elif btasks and all(tasks[t].get('role')=='planning' for t in btasks):candidates={'기획'};reasons.append('명시적 작업의 기획 역할')
  else:reasons.append('응답 경계 내 patch 대상의 제품/시험/보고서 파일 구분')
  if not candidates or len(candidates)>1 or (mixed and not bs):stage='귀속 불명'
  else:stage=next(iter(candidates))
  if mixed and not bs:reasons.append('공통 하네스/제품 혼합 요청: 제품 단계에 강제 귀속하지 않음')
  if len(candidates)>1:reasons.append('한 응답에 여러 단계가 섞여 임의 비율 배분하지 않음')
  if not reasons:reasons=['명시적 작업/단계 연결이 충분하지 않음']
  u=o.get('usage',{});it=u.get('input_tokens');ct=u.get('cached_input_tokens');ot=u.get('output_tokens');cw=u.get('cache_write_input_tokens',0)
  valid=all(isinstance(x,int) and x>=0 for x in [it,ct,ot]) and ct<=it and cw==0 and o.get('usage_semantics')=='per_response_increment'
  normal=it-ct if valid else 'UNKNOWN'
  rework='RESPONSE_PATCH_EVIDENCE' if episodes and paths and stage in {'수정','보고서','디자인','검증'} and not mixed else ('EPISODE_CONTEXT_ONLY' if episodes and not mixed else 'UNKNOWN')
  row={'event_id':e['event_id'],'session_id':key[0],'response_id':key[1],'turn_id':turn(e)[1],'occurred_at':o.get('occurred_at'),'model':o.get('model','UNKNOWN'),'stage':stage,'stage_candidates':sorted(candidates),'stage_reason':reasons,'task_ids':taskids or ['UNKNOWN'],'task_link_basis':link_basis,'original_binding_event_ids':[b['event_id'] for b in bs],'request_event_ids':[q['event_id'] for q,a in anns],'call_evidence':[{'call_id':c['call_id'],'source_line':c['line'],'tool':c['tool'],'payload_sha256':hashlib.sha256(c['text'].encode()).hexdigest()} for c in calls],'matched_artifact_paths':paths,'source':s,'raw_usage':u,'normal_input_tokens':normal,'cached_input_tokens':ct,'output_tokens':ot,'token_math_valid':valid,'rework_episodes':sorted(episodes),'rework_link_strength':rework,'actual_billed_usd':'UNKNOWN','actual_billing_route':'UNKNOWN','actual_service_tier':'UNKNOWN','cost_basis':'API_EQUIVALENT_SCENARIO_NOT_CODEX_SUBSCRIPTION_OR_ACTUAL_BILL'}
  usage_rows.append(row)
 # Pricing source verified live this run; no historical or account billing assertions.
 reference=json.loads(read('tools/v1-report/study-pricing-reference.json'))
 pricing={'verified_at':reference['verified_at'],'rate_reference_date':reference['rate_reference_date'],'historical_execution_date_rates':'UNKNOWN','currency':'USD','per_tokens':1000000,'model':reference['model'],'source_url':reference['source_urls']['api'],'codex_scope_source':reference['source_urls']['codex'],'route_and_tier_observed':'UNKNOWN','scenarios':{s:reference[s] for s in ['standard_short_base','fast_short_base']},'formula':'(normal_input_tokens * normal_input_rate + cached_input_tokens * cached_input_rate + output_tokens * output_rate) / 1000000','normal_input_formula':'input_tokens - cached_input_tokens','assumptions':['API text-token base scenario only; not a claim about Codex subscription/credits billing','Historical tier, long-context applicability, regional surcharges, discounts, taxes, tools and account plan are not established','Output includes reasoning tokens; cached input is not added to inclusive input again','Nonzero cache-write tokens or inconsistent/missing counts => UNKNOWN; no silent zero substitution'],'page_sha256':reference['page_sha256'],'codex_billing_note':'Official Codex guidance separates API token prices from subscription usage; these calculations are comparative API scenarios, not included-task estimates.'}
 write('analysis/pricing.json',pricing)
 def cost(row,scenario):
  if row['model']!='gpt-6.1-sol' or not row['token_math_valid']:return 'UNKNOWN'
  rate=pricing['scenarios'][scenario]
  return str((Decimal(row['normal_input_tokens'])*Decimal(str(rate['normal_input']))+Decimal(row['cached_input_tokens'])*Decimal(str(rate['cached_input']))+Decimal(row['output_tokens'])*Decimal(str(rate['output'])))/Decimal(1000000))
 for row in usage_rows:
  for scenario in pricing['scenarios']:row['api_equivalent_usd_'+scenario]=cost(row,scenario)
 def aggregate(rows):
  valid=[r for r in rows if r['token_math_valid']]
  return {'responses':len(rows),'valid_token_responses':len(valid),'normal_input_tokens':sum(r['normal_input_tokens'] for r in valid),'cached_input_tokens':sum(r['cached_input_tokens'] for r in valid),'output_tokens':sum(r['output_tokens'] for r in valid),'inclusive_input_tokens':sum(r['normal_input_tokens']+r['cached_input_tokens'] for r in valid),'total_tokens':sum(r['normal_input_tokens']+r['cached_input_tokens']+r['output_tokens'] for r in valid),'invalid_usage_response_ids':[r['response_id'] for r in rows if not r['token_math_valid']],'api_equivalent_usd':{s:str(sum((Decimal(r['api_equivalent_usd_'+s]) for r in rows if r['api_equivalent_usd_'+s]!='UNKNOWN'),Decimal(0))) if all(r['api_equivalent_usd_'+s]!='UNKNOWN' for r in rows) else 'UNKNOWN' for s in pricing['scenarios']},'actual_billed_usd':'UNKNOWN'}
 stage_summary=[{'stage':s,**aggregate([r for r in usage_rows if r['stage']==s])} for s in STAGES]
 task_stage=[]
 for t in list(tasks)+['UNKNOWN','MULTI_TASK_CONTEXT']:
  for s in STAGES:
   rows=[r for r in usage_rows if r['stage']==s and (r['task_ids']==[t] if t not in {'MULTI_TASK_CONTEXT'} else len(r['task_ids'])>1)]
   if rows:task_stage.append({'task_id':t,'stage':s,**aggregate(rows)})
 rework=[]
 for ep in sorted({ep for r in usage_rows for ep in r['rework_episodes']}):
  for strength in ['RESPONSE_PATCH_EVIDENCE','EPISODE_CONTEXT_ONLY']:
   rows=[r for r in usage_rows if r['rework_episodes']==[ep] and r['rework_link_strength']==strength]
   if rows:rework.append({'episode':ep,'strength':strength,'interpretation':'사용량이 연결된 재작업/디자인 변경 활동; 모든 토큰이 오류로 인한 추가 비용이라는 인과 추정 아님','subset_of_stage_totals':True,**aggregate(rows)})
 multi_rework=[r for r in usage_rows if len(r['rework_episodes'])>1]
 if multi_rework:rework.append({'episode':'MULTI_EPISODE_UNALLOCATED','strength':'UNKNOWN','subset_of_stage_totals':True,**aggregate(multi_rework)})
 # Compare the same original 30 selected requests separately from expanded scope.
 oldpath='reports/memo-v1-study-logs-20261021T080448Z/user-messages.jsonl'
 old=[json.loads(l) for l in read(oldpath).splitlines() if l.strip()]
 oldids={m['event_id'] for m in old}
 old_counts=collections.Counter(A[i]['category'] for i in oldids if i in A)
 excluded=[{'event_id':i,'reason':EXCLUDED[i],'classification_provenance':'POSTHOC_SCOPE_REVIEW','original_zip_preserved':True} for i in oldids if i in EXCLUDED]
 assert len(excluded)==8 and len(old_counts)>0
 assert not any(r['event_id'] in {e['event_id'] for e in mixed_usage_excluded} for r in usage_rows)
 write('analysis/scope-exclusions.json',{'previous_30_requests':{'excluded_count':8,'harness_requests':7,'environment_injection':1,'retained_product_or_mixed_policy_requests':22,'excluded':excluded},'mixed_request_usage_excluded':mixed_usage_excluded,'policy':'Mixed request text retained for decisions only; full-turn tokens/cost excluded without an explicit product response binding. Scope-exclusion records are audit metadata, not product interventions.'})
 result={'generated_at':now,'scope':'memo product + historical precursor planning/design; content-reviewed request scope, mixed harness requests remain unallocated','requests':len(classified),'posthoc_categories':dict(collections.Counter(c['posthoc']['category'] for c in classified)),'request_duplicate_records_removed':duplicates,'original_30_scope':{'count':len(oldids),'posthoc_categories':dict(old_counts),'note':'Old 28 UNKNOWN counted absent formal source-event links, not 28 reviewed undecidable classifications'},'usage_responses':len(usage_rows),'usage_duplicates_removed':usage_duplicates,'contemporaneous_explicit_binding_responses':sum(bool(r['original_binding_event_ids']) for r in usage_rows),'posthoc_only_responses':sum(not r['original_binding_event_ids'] for r in usage_rows),'stage_totals':stage_summary,'task_stage_totals':task_stage,'rework_subsets':rework,'total_observed_scoped':aggregate(usage_rows),'whole_v1_usage':'UNKNOWN','whole_v1_cost':'UNKNOWN','actual_billed_usd':'UNKNOWN','current_response_stop':'NOT_YET_OBSERVABLE','unavailable_native_sources':[clean(p) for p,v in native.items() if v is None],'missing_annotation_events':[i for i in A if i not in byid],'unclassified_source_users_not_all_v1':sum(e['event_type']=='session_message' and e.get('observed',{}).get('role')=='user' and e['event_id'] not in A for e in events),'native_sources_read_only':native_provenance}
 result['original_30_scope']['excluded_count']=8
 result['original_30_scope']['retained_count']=22
 result['mixed_usage_responses_excluded']=len(mixed_usage_excluded)
 result['scope']='memo product and historical precursor planning/design; mixed requests retain policy text only, whole-turn usage excluded absent explicit product binding'
 result['models']=dict(collections.Counter(r['model'] for r in usage_rows))
 # Invariants: stage buckets partition records and tokens; task-stage buckets don't multiply multi-task responses.
 total=result['total_observed_scoped']
 for field in ['responses','normal_input_tokens','cached_input_tokens','output_tokens','total_tokens']:
  assert sum(x[field] for x in stage_summary)==total[field],field
  assert sum(x[field] for x in task_stage)==total[field],field
 assert len({(r['session_id'],r['response_id']) for r in usage_rows})==len(usage_rows)
 assert all(r['normal_input_tokens']+r['cached_input_tokens']==r['raw_usage']['input_tokens'] for r in usage_rows if r['token_math_valid'])
 jsonl('analysis/usage-by-response.jsonl',usage_rows);write('analysis/summary.json',result)
 for filename,rows in [('stages.csv',stage_summary),('tasks-stages.csv',task_stage),('rework.csv',rework)]:
  if not rows:continue
  flat=[]
  for r in rows:
   item={k:(json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v) for k,v in r.items() if k!='api_equivalent_usd'}
   item.update({'api_equivalent_usd_'+s:v for s,v in r['api_equivalent_usd'].items()})
   flat.append(item)
  with (OUT/'analysis'/filename).open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in flat for k in r)));w.writeheader();w.writerows(flat)
 with (OUT/'analysis'/'requests.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['event_id','message_identity','posthoc_category','reason','tasks','original_classifications','request_excerpt'])
  for c in classified:w.writerow([c['canonical_event_id'],str(c['original_message_identity']),c['posthoc']['category'],c['posthoc']['reason'],';'.join(c['posthoc']['tasks']),json.dumps(c['original_classifications'],ensure_ascii=False),clean(c['request_excerpt'][:250])])
 md=['# 단계·개입·재작업 보강 분석',f"단가 기준일: {pricing['rate_reference_date']} / 분석 생성: {now} / 사후 분석. 원본 이벤트·분류·사용량 귀속은 덮어쓰지 않았습니다.",'',f'사용자 요청 {len(classified)}건: '+', '.join(f'{k} {v}' for k,v in result['posthoc_categories'].items()),'','## 단계별 관측 토큰과 API 환산 시나리오','|단계|응답|일반 입력|캐시 입력|출력|API Standard 환산 USD|','|---|---:|---:|---:|---:|---:|']
 for x in stage_summary:md.append(f"|{x['stage']}|{x['responses']}|{x['normal_input_tokens']:,}|{x['cached_input_tokens']:,}|{x['output_tokens']:,}|{Decimal(x['api_equivalent_usd']['standard_short_base']):.4f}|" if x['api_equivalent_usd']['standard_short_base']!='UNKNOWN' else f"|{x['stage']}|{x['responses']}|UNKNOWN|UNKNOWN|UNKNOWN|UNKNOWN|")
 md+=['','일반 입력 = inclusive input − cached input. 캐시 입력을 기존 input에 다시 더하지 않습니다. output 안의 reasoning을 다시 더하지 않습니다. 0응답은 관측/귀속된 응답이 없다는 뜻이며 실제 작업 비용 0이라는 뜻이 아닙니다.','',f"명시적 당시 부분 귀속 {result['contemporaneous_explicit_binding_responses']}개, 사후 문맥/도구 근거 {result['posthoc_only_responses']}개. 후자는 당시 확정 귀속으로 승격하지 않습니다. 한 응답에 여러 단계/작업이 섞이면 귀속 불명/MULTI_TASK_CONTEXT로 유지합니다. 시간 구간만으로 귀속하거나 균등 배분하지 않았습니다.",'','## 비용의 의미','공식 gpt-6.1-sol API Standard 표시 기본 단가: 일반 입력 $2 / 캐시 입력 $0.10 / 출력 $10 (각 100만 토큰). Fast 비교 시나리오: $4 / $0.20 / $20. 기준일 현재 표시 단가를 적용한 API 환산이며 실행일 과거 단가·실제 요금제·서비스 티어·컨텍스트 할증·도구료·세금·할인을 확인하지 못했습니다. 실제 Codex 구독/크레딧 비용이나 실제 청구 추정으로 해석하면 안 됩니다. 실제 청구액과 전체 v1 비용은 UNKNOWN입니다.','공식 근거: https://developers.openai.com/api/docs/pricing 및 https://developers.openai.com/codex/pricing . pricing.json에 단가·문서 SHA·수식·가정을 남겼습니다.','', '## 재작업 해석','rework.csv는 단계 합계의 부분집합입니다. 단계 합계에 다시 더하지 마세요. 디자인 취향/범위 변경(DESIGN_CHANGE_REQUEST)과 실제 누락·합의 이탈 정정을 구분했습니다. RESPONSE_PATCH_EVIDENCE는 해당 응답에 변경 파일 근거가 있고, EPISODE_CONTEXT_ONLY는 관련 요청/작업의 문맥 관측입니다. 모두 순수한 오류 추가 비용을 입증하지는 않습니다. 여러 원인이 섞인 응답은 MULTI_EPISODE_UNALLOCATED로 분리합니다.','', '## 요청 분류 해석','원본 메시지(session + message ID, 없으면 원본 ordinal)로 중복 제거했습니다. 동일 문구라도 원본 ID가 다르면 별도 요청입니다. 한 메시지는 주 분류 하나만 세며, 복합 요구는 이유에 표시했습니다. 당시 human_intervention/pending은 original_classifications에 원문 분류와 상태를 보존했고, posthoc는 이번 에이전트의 사후 해석이며 사용자 승인이나 당시 기록이 아닙니다. 정책 선택·신규 요청·환경 지원·상태 질문을 오류 개입 수로 합치지 마세요. 계속/재개처럼 모호한 요청은 미확인입니다.','', '## 범위·누락','이전 추출본의 30건과 이번 확대 범위를 별도 집계했습니다. 전체 원본 대화가 제품 전용이 아니므로 하네스 전용 요청은 추가하지 않았고 혼합 요청은 정책 근거만 남기고 명시적 제품 응답 귀속이 없는 턴 전체 사용량은 집계에서 제외했습니다. native source의 토큰 응답 경계 사이 도구 메타데이터를 읽어 SHA/라인/call ID/파일 경로만 추출했으며 원본 인자·암호화 추론·세션 파일은 ZIP에 복사하지 않았습니다. 요청/사용량 수집 누락·분류 불명·종료 후 Stop·청구 연동 부재 때문에 전체 개입 횟수/전체 비용은 확정 불가입니다. 검증 요약 추가와 비용 분석은 제품 검증 통과/전환 구현이 아닙니다.']
 (OUT/'ANALYSIS.md').write_text('\n'.join(md)+'\n')
 with (OUT/'ANALYSIS.md').open('a') as f:
  f.write('\n## 이전 추출 범위 정정\n이전 ZIP은 보존했습니다. 이전 30건 중 하네스 요청 7건과 환경 지침 주입 1건은 제품 요청 집계에서 제외했습니다. 남은 22건의 재분류와 확대된 제품 요청 범위를 분리합니다. analysis/scope-exclusions.json에 8건의 원본 이벤트 ID·제외 이유와 혼합 요청의 사용량 제외 ID를 남겼습니다. 혼합 요청의 정책 문장은 근거로 보존하되, 제품 작업의 명시적 응답 귀속이 없는 턴 전체 사용량은 관측 토큰·환산 비용 합계에서 제외했습니다.\n')
 return {'analysis_summary':'analysis/summary.json','classified_requests':len(classified),'analyzed_responses':len(usage_rows),'posthoc_unknown_requests':sum(c['posthoc']['category']=='미확인' for c in classified),'original_intervention_record_linked_requests':sum(c['original_classifications']!='UNKNOWN' for c in classified),'stages_partition':'PASS','normal_plus_cached_equals_inclusive_input':'PASS','actual_bill':'UNKNOWN'}
