#!/usr/bin/env python3
"""Read-only source export: compact, redacted memo-v1 study evidence."""
import collections,csv,datetime,hashlib,io,json,pathlib,re,tempfile,zipfile
from study_annotations import A
R=pathlib.Path(__file__).resolve().parents[2]
NOW=datetime.datetime.now(datetime.timezone.utc)
NAME='memo-v1-study-logs-'+NOW.strftime('%Y%m%dT%H%M%SZ')
OUT=R/'reports'/NAME; OUT.mkdir()
inputs={}; omissions=collections.Counter(); redactions=collections.Counter()
def read(p):
 b=(R/p).read_bytes(); inputs[p]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}; return b
def clean(x,key=''):
 if isinstance(x,dict):
  d={}
  for k,v in x.items():
   if k.lower() in {'files','files_start','files_end','changed_files','code_state_start','code_state_end','submission_code_state','tested_files','additional_artifact_hashes','protected_files','thread_token_usage','turn_token_usage','info','stdout','stderr','argv','arguments','environment','env','headers','body','memo_body','password','authorization','access_token','refresh_token','api_key','secret','cookie','cookies'}:
    omissions[k]+=1; continue
   d[k]=clean(v,k)
  return d
 if isinstance(x,list):return [clean(v,key) for v in x]
 if isinstance(x,str):
  x=re.sub(r'/Users/[^/\s]+','/Users/REDACTED',x)
  x=re.sub(r'(?i)\b(?:Bearer\s+)[A-Za-z0-9._~+/=-]+','Bearer [REDACTED]',x)
  x=re.sub(r'\b(?:sk-[A-Za-z0-9_-]{16,}|AKIA[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{20,})\b','[REDACTED_CREDENTIAL]',x)
  x=re.sub(r'(?i)((?:password|api[_-]?key|access[_-]?token|secret)\s*[=:]\s*)[^\s,;"\x27]+',r'\1[REDACTED]',x)
  x=re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b','[REDACTED_EMAIL]',x)
  return x
 return x
def write(p,d):
 f=OUT/p; f.parent.mkdir(parents=True,exist_ok=True)
 f.write_text(json.dumps(clean(d),ensure_ascii=False,indent=2)+'\n')
def jsonl(p,rows):
 f=OUT/p;f.parent.mkdir(parents=True,exist_ok=True)
 f.write_text(''.join(json.dumps(clean(e),ensure_ascii=False)+'\n' for e in rows))
events=[json.loads(l) for l in read('.harness/logs/events.jsonl').splitlines() if l.strip()]
state=json.loads(read('.harness/tasks/tasks.yaml')); tasks={k:v for k,v in state['tasks'].items() if v.get('feature_id') in {'MEMO-MVP','FEAT-001','FEAT-002'}}
byid={e['event_id']:e for e in events}; seed=[e for e in events if e.get('task_id') in tasks or e.get('feature_id') in {'MEMO-MVP','FEAT-001','FEAT-002'}]
runs={e['run_id'] for e in seed if e.get('run_id') not in {None,'UNKNOWN'}}
seed += [e for e in events if e.get('run_id') in runs and e.get('work_type')=='PRODUCT' and not str(e['event_type']).startswith('session_') and e['event_type'] not in {'model_usage','usage_snapshot'}]
selected={e['event_id']:e for e in seed}
docs=['docs/feedback.md','docs/retrospective.md','docs/agreement-review.md','docs/settings-alignment-result.md','docs/v1-acceptance-status.md','docs/design-conformance.md']
referenced=set()
for p in docs:
 text=read(p).decode(); referenced.update(i for i in byid if i in text)
 f=OUT/'context'/pathlib.Path(p).name; f.parent.mkdir(exist_ok=True); f.write_text(clean(text))
def ids(value):
 if isinstance(value,dict):
  for v in value.values():yield from ids(v)
 elif isinstance(value,list):
  for v in value:yield from ids(v)
 elif isinstance(value,str):yield value
for e in seed:
 referenced.update(v for v in ids(e) if v in byid)
for i in referenced:selected[i]=byid[i]
def turn(e):
 s=e.get('source',{}); o=e.get('observed',{}); return (s.get('session_id') or o.get('thread_id'),o.get('session_turn_id') or o.get('turn_id'))
turns={turn(e) for e in selected.values() if e['event_type']=='session_message' and e.get('observed',{}).get('role')=='user'}
turns={t for t in turns if all(t) and 'UNKNOWN' not in t}
# Declared source-turn links are explicit contextual links, not task-cost attribution.
for e in seed:
 for d in [e.get('observed',{}),e.get('agent_summary',{})]:
  t=(d.get('source_session_id'),d.get('source_turn_id'))
  if all(t) and 'UNKNOWN' not in t:turns.add(t)
response_bindings=collections.defaultdict(list)
turns={turn(e) for e in events if e['event_id'] in A and not A[e['event_id']].get('mixed_scope')}
for e in seed:
 if e['event_type']=='usage_attributed':
  o=e.get('observed',{}); response_bindings[(o.get('session_id'),o.get('response_id'))].append(e)
for e in events:
 if e['event_type'] in {'session_message','session_task_started','session_task_complete','session_turn_aborted','model_usage','session_item_timing'} and turn(e) in turns:
  if e['event_type']!='session_message' or e.get('observed',{}).get('role')=='user':selected[e['event_id']]=e
 if e['event_type']=='model_usage' and (e.get('source',{}).get('session_id'),e.get('observed',{}).get('response_id')) in response_bindings:selected[e['event_id']]=e
linked_sessions={s for s,t in turns}
content_selected=set()
for e in events:
 if e['event_type']!='session_message' or e.get('observed',{}).get('role')!='user':continue
 if e['event_id'] in A:
  if e['event_id'] not in selected:content_selected.add(e['event_id'])
  selected[e['event_id']]=e
selected=sorted(selected.values(),key=lambda e:e['sequence'])
# No tool payloads, assistant transcript, environment injection, or cumulative token snapshots.
excludedtypes={'usage_snapshot','session_tool_event'}
export=[]; users=[]; usage=[]; seen_usage={}; duplicate_usage=[]
for e in selected:
 if e['event_type'] in excludedtypes:continue
 if e['event_type']=='session_message':
  if e['event_id'] not in A:continue
  o=e.get('observed',{}); text='\n'.join(c.get('text','') for c in o.get('content',[]) if isinstance(c,dict))
  text=re.sub(r'<environment_context>.*?</environment_context>','[ENVIRONMENT OMITTED]',text,flags=re.S)
  text=re.sub(r'<INSTRUCTIONS>.*?</INSTRUCTIONS>','[INSTRUCTIONS OMITTED]',text,flags=re.S)
  users.append({**{k:e.get(k,'UNKNOWN') for k in ['event_id','sequence','recorded_at','run_id','task_id','agent_run_id']},'source':e.get('source'),'session_turn_id':o.get('session_turn_id'),'occurred_at':o.get('occurred_at'),'text':text,'classification':'original event binding UNKNOWN unless linked; retrospective classification in analysis/user-classifications.jsonl','scope_basis':'content-reviewed memo product request; mixed request policy only, no whole-turn usage attribution'})
  continue
 export.append(e)
 if e['event_type']=='model_usage':
  o=e['observed']; s=e.get('source',{}); k=(s.get('session_id'),o.get('response_id'))
  if not all(k) or 'UNKNOWN' in k:continue
  if k in seen_usage:
   duplicate_usage.append({'event_id':e['event_id'],'canonical_event_id':seen_usage[k]['event_id'],'same_usage':o.get('usage')==seen_usage[k]['observed'].get('usage')});continue
  seen_usage[k]=e
  bs=response_bindings.get(k,[])
  usage.append({'event_id':e['event_id'],'session_id':k[0],'response_id':k[1],'session_turn_id':o.get('session_turn_id'),'occurred_at':o.get('occurred_at'),'usage':o.get('usage','UNKNOWN'),'usage_semantics':o.get('usage_semantics','UNKNOWN'),'model':o.get('model','UNKNOWN'),'cost':o.get('cost','UNKNOWN'),'attribution':'EXPLICIT_PARTIAL' if bs else 'RELATED_TURN_CONTEXT_ONLY','bindings':[{'event_id':b['event_id'],'task_id':b.get('task_id'),'agent_run_id':b.get('agent_run_id'),'run_id':b.get('run_id'),'basis':b.get('agent_summary')} for b in bs],'source':s})
jsonl('events.jsonl',export);jsonl('user-messages.jsonl',users)
jsonl('interventions.jsonl',[e for e in export if e['event_type'] in {'human_intervention','human_intervention_pending','development_change_registered','integration_observation'}])
jsonl('usage.jsonl',usage)
taskrows=[]; executions=[]; reviews=[]
for k,t in tasks.items():
 taskrows.append({x:t.get(x,'UNKNOWN') for x in ['task_id','feature_id','role','title','state','dependencies','blocked_reason','validation_status','scope']})
 for ex in t.get('executions',[]):executions.append({'task_id':k,**{x:ex.get(x,'UNKNOWN') for x in ['agent_run_id','run_id','feature_id','role','kind','execution_mode','execution_scope','started_at','ended_at','baseline','result','usage','usage_refs','review_snapshot']}})
 for rv in t.get('reviews',[]):reviews.append({'task_id':k,'review':rv,'validity_now':t.get('validation_status','UNKNOWN'),'notice':'historical verdict only; no current target-compliance inheritance'})
write('tasks.json',taskrows);jsonl('executions.jsonl',executions);jsonl('task-reviews.jsonl',reviews)
# Compact test/review summaries, including failed attempts. Preserve source identity and hash,
# not binaries, captures, raw SDK logs or full source/file snapshots.
evidence=[]; duplicates={}; seen_hash={}
for p in sorted((R/'.harness/v1').rglob('*.json')):
 rel=p.relative_to(R).as_posix()
 if any(x in p.parts for x in ['history','Build','Index.noindex','build','ios-derived']):continue
 if not (p.name=='summary.json' or p.name.endswith('-summary.json') or p.name in {'review.json','verification.json','acceptance-review.json'} or p.parent.name in {'reviews','defects'}):continue
 if p.stat().st_size>750000:omissions['large_evidence_file']+=1;continue
 try:d=json.loads(read(rel))
 except (ValueError,UnicodeError):continue
 digest=inputs[rel]['sha256']
 if digest in seen_hash:
  evidence.append({'source_path':rel,'source_sha256':digest,'duplicate_of':seen_hash[digest]});continue
 dest='verification/'+rel.removeprefix('.harness/v1/')
 write(dest,{'source_path':rel,'source_sha256':digest,'data':d,'validity':'historical evidence; current impact/target compliance not automatically established'})
 seen_hash[digest]=dest;evidence.append({'source_path':rel,'source_sha256':digest,'package_path':dest})
write('verification-index.json',evidence)
def totals(rows):
 c=collections.Counter(); n=0
 for u in rows:
  if u['usage_semantics']!='per_response_increment' or not isinstance(u['usage'],dict):continue
  n+=1
  for k,v in u['usage'].items():
   if isinstance(v,int):c[k]+=v
 return {'responses':n,'tokens':dict(c),'note':'cached input is subset of input; reasoning output subset of output; do not add subsets again'}
explicit=[u for u in usage if u['attribution']=='EXPLICIT_PARTIAL']
context=[u for u in usage if u['attribution']=='RELATED_TURN_CONTEXT_ONLY']
missing_bindings=[{'session_id':k[0],'response_id':k[1],'binding_event_ids':[e['event_id'] for e in bs]} for k,bs in response_bindings.items() if k not in seen_usage]
unlinked_users=[e for e in events if e['event_type']=='session_message' and e.get('observed',{}).get('role')=='user' and e['event_id'] not in {x['event_id'] for x in users}]
summary={'generated_at':NOW.isoformat(),'source_cutoff_sequence':events[-1]['sequence'],'source_cutoff_recorded_at':events[-1]['recorded_at'],'source_events_scanned':len(events),'exported_events':len(export),'user_messages':len(users),'tasks':len(tasks),'executions':len(executions),'historical_reviews':len(reviews),'verification_sources':len(evidence),'event_types':dict(collections.Counter(e['event_type'] for e in export)),'collection_recorded_at_range':[min(e['recorded_at'] for e in selected),max(e['recorded_at'] for e in selected)],'explicit_partial_usage':totals(explicit),'related_turn_context_usage_separate_not_task_cost':totals(context),'whole_v1_tokens':'UNKNOWN','whole_v1_cost':'UNKNOWN','missing_bound_responses':missing_bindings,'duplicate_usage':duplicate_usage,'unlinked_user_messages_in_source_excluded_not_all_v1':len(unlinked_users),'unclassified_exported_user_messages':sum(not any(m['event_id']==i.get('observed',{}).get('source_event_id') for i in export if i['event_type']=='human_intervention') for m in users),'current_response_stop':'NOT_YET_OBSERVABLE','current_packaging_usage':'UNKNOWN','product_v1_completion':'BLOCKED','omissions':dict(omissions)}
write('summary.json',summary)
relations=[]
for e in export:
 relations.append({'event_id':e['event_id'],'sequence':e['sequence'],'type':e['event_type'],'run_id':e.get('run_id'),'task_id':e.get('task_id'),'agent_run_id':e.get('agent_run_id'),'session_id':e.get('source',{}).get('session_id'),'turn_id':e.get('observed',{}).get('session_turn_id'),'response_id':e.get('observed',{}).get('response_id'),'source_event_ids':[v for v in ids(e.get('observed',{})) if v in byid]})
write('id-links.json',relations)
readme=f'''# 메모 앱 v1 스터디 분석 로그

생성: {NOW.isoformat()} / 수동 시점 스냅샷. 원본을 변경하지 않은 파생 추출본입니다.

## 범위와 읽는 순서
- summary.json: 수량·토큰 집계·누락. 수집 시각 범위이며 실제 실행 시각은 occurred_at/started_at/ended_at을 사용하세요.
- tasks.json / executions.jsonl / events.jsonl: MEMO-MVP v1 및 그 선행 메모 목록·작성 기획/디자인 FEAT-001·002. TODO는 실행 횟수에 포함하지 않습니다.
- user-messages.jsonl / interventions.jsonl: 명시적인 원본 이벤트·턴 참조가 있는 사용자 요청과 당시 선언된 개입 분류. 분류는 에이전트 판단이며 사용자 승인과 같지 않습니다. pending과 linked 기록을 개입 두 건으로 더하지 말고 pending_event_id/source_message_id/request_item으로 묶으세요.
- task-reviews.jsonl / verification/: 실패 시도도 포함한 당시 검증 요약. 과거 PASS와 현재 RECHECK_REQUIRED/BLOCKED 및 기술 합의 준수는 별개입니다. 제품 시험을 재실행하지 않았습니다.
- usage.jsonl: session_id+response_id로 중복 제거한 실제 per_response_increment. EXPLICIT_PARTIAL만 명시적 작업 부분 귀속입니다. RELATED_TURN_CONTEXT_ONLY는 명시적으로 연결된 요청 턴의 문맥 사용량이며 작업별/전체 v1 비용이 아닙니다. 두 부분은 서로 겹치지 않게 분리했지만 원본 누락으로 전체 합계는 UNKNOWN입니다. 누적 usage_snapshot/thread/turn 총량은 제외했습니다.
- id-links.json: event/run/task/agent_run/session/turn/response 연결. 원본 UNKNOWN은 그대로 유지했습니다.
- verification-index.json / provenance.json: 원본 경로·SHA와 포함 파일 대응. source_path는 원본 추적용이며 ZIP 안에 모든 원본이 있는 뜻이 아닙니다. 동일 내용 요약은 한 번만 포함합니다.
- context/: 사용자 개입·미검증 상태·설정 정정의 기존 문서. 승인 목표 변경 근거로 테스트 PASS를 승계하지 않습니다.

## 선택 방법과 공백
작업 feature/task ID → 해당 PRODUCT run → 실제 source_event/source_turn/문서에 인용된 event ID를 따라 선택했습니다. 추가 사용자 요청은 연결된 세션 안에서 메모/v1/보고서/플랫폼/합의 등 제품 관련 내용이 명시된 경우만 내용 기준으로 선별하고 scope_basis에 구분했습니다. 해당 내용 선별만으로 task/사용량 귀속이나 개입 분류를 추정하지 않았습니다. 짧은 계속/수락 등 연결 불명 요청은 제외될 수 있습니다. 과거 제품·공통 하네스 혼합 요청은 결정 맥락으로 남지만 하네스 실행 전체를 포함하지 않습니다. 같은 세션이라는 이유만으로 모든 기록을 포함하지 않았습니다. 전체 사용량·비용, 개입 전체 건수는 확정할 수 없습니다. 원본에서 분류가 안 된 연결 요청은 UNKNOWN입니다. PRE-v1 기획 근거는 포함하되 실제 실행 날짜/feature_id로 구분하세요.

현재 응답의 Stop과 패키징 완료 후 이벤트는 이 ZIP에 들어갈 수 없어 NOT_YET_OBSERVABLE입니다. 훅 진단 원문은 제외했으며 본 묶음의 존재는 전체 자동 수집 성공 증거가 아닙니다. 실측 훅/명령/검토 관련 이벤트가 있는 범위만 확인 가능합니다.

확인된 검증 공백: 확인창 C-DISCARD-CONFIRM의 세 플랫폼 상태 비교, 보조기술·일부 탐색 및 최신 변경 영향, 승인 CMP/Ktor/모듈 목표에 대한 전환 후 검증은 완료로 취급하지 않습니다. 자세한 범위는 context와 기존 상태 문서에 있습니다. 과거 HTTP 보조 상세 링크 목록 1개 복구 불가(UNKNOWN), 당시 요약/불변 검토는 별개 보존입니다.

## 개인정보·제외
DB/메모 본문 데이터, 빌드·SDK 산출물, 대용량 코드/환경/파일 스냅샷, 모든 캡처, 도구 인자·stdout/stderr 원문, 원본 Codex 세션 파일, 개인 설정·인증 파일과 설치 하네스는 포함하지 않습니다. 텍스트의 로컬 사용자명·이메일과 알려진 인증정보 패턴을 마스킹했습니다. 비밀 키 필드와 HTTP 본문 필드를 제거했습니다. ID·시각·코드 기준 해시·검증 결과는 분석용으로 유지합니다. 자동 패턴 검사로 모든 비정형 민감정보 부재를 증명하는 것은 아닙니다.

## 재생성·검증
프로젝트 루트에서 `rtk proxy python3 -B tools/v1-report/study_logs.py` (수동 재생성).
별도 실행 환경 없이 JSON/JSONL/Markdown을 열면 됩니다. JSONL은 한 줄에 하나의 JSON입니다. ZIP 옆의 .verification.json은 실제 ZIP 추출 후 파일 SHA·JSON 구문·ID 연결·제외 자산 검사 결과입니다. 원본 세션이나 DB는 필요하지 않습니다.
'''
(OUT/'README.md').write_text(readme)
from study_enrichment import enrich
read('tools/v1-report/study_logs.py');read('tools/v1-report/verify_study_analysis.py')
analysis=enrich(R,OUT,events,tasks,read,write,jsonl,clean)
summary['retrospective_enrichment']=analysis
summary.pop('unclassified_exported_user_messages',None)
summary['original_intervention_record_linked_requests']=analysis['original_intervention_record_linked_requests']
summary['posthoc_unknown_requests']=analysis['posthoc_unknown_requests']
write('summary.json',summary)
with (OUT/'README.md').open('a') as f:
 f.write('\n## 단계·개입·비용 보강본\n\n먼저 ANALYSIS.md를 읽으세요. analysis/에 원본 메시지별 사후 분류, 응답별 단계/작업/재작업 연결, 일반·캐시·출력 토큰, 공식 기준일 API 환산 시나리오와 CSV를 추가했습니다. 루트 요약과 사후 분석은 같은 기록을 다른 관점으로 집계하므로 합산하지 않습니다. 당시 분류/귀속과 사후 해석은 분리되어 있으며 실제 청구액·전체 비용은 UNKNOWN입니다. 재생성은 저장된 기준일 단가를 재사용하고 공식 가격을 새로 확인한 것으로 표시하지 않습니다.\n')
 f.write('\n이전 30건 중 하네스 요청 7건·환경 지침 주입 1건은 범위 제외했습니다. 8건의 ID·제외 이유는 analysis/scope-exclusions.json에 있습니다. 제품·하네스 혼합 요청은 정책 문장만 보존하고 명시적인 제품 응답 귀속이 없는 턴 전체 토큰·비용은 두 집계 모두에서 제외했습니다. 이전 ZIP과 원본은 보존했습니다. 기존 unclassified_exported_user_messages 값은 실제 분류 불가 수가 아니어서 제거하고, 당시 개입 기록 연결 수와 사후 미확인 요청 수를 별도 필드로 제공합니다.\n')
write('provenance.json',{'generated_at':NOW.isoformat(),'inputs':inputs,'scope_rule':'explicit task/feature + PRODUCT run + source-event/turn references; no whole-session inference','transformation':'structured projection + sensitive field omission + path/email/credential masking','source_preservation':'read-only inputs; automatic hooks may append independently','schema':'derived study export v1'})
from verify_study_analysis import verify
write('analysis/invariants.json',verify(OUT))
manifest={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file()}
write('manifest.json',manifest)
zip_path=OUT.with_suffix('.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,NAME+'/'+str(p.relative_to(OUT)))
tmp=pathlib.Path(tempfile.mkdtemp(prefix='memo-study-verify-'))
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert all(not pathlib.Path(n).is_absolute() and '..' not in pathlib.Path(n).parts for n in z.namelist())
 z.extractall(tmp)
ex=tmp/NAME
assert verify(ex)['result']=='PASS'
for p,h in manifest.items():assert hashlib.sha256((ex/p).read_bytes()).hexdigest()==h,p
for p in ex.rglob('*'):
 if not p.is_file():continue
 assert p.suffix in {'.md','.json','.jsonl','.csv'},str(p)
 if p.suffix=='.json':json.loads(p.read_text())
 if p.suffix=='.jsonl':
  for l in p.read_text().splitlines():json.loads(l)
 text=p.read_text()
 assert not re.search(r'\b(?:AKIA[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b',text),'credential pattern '+str(p)
 assert not re.search(r'/Users/(?!REDACTED)[^/\s]+',text),'unmasked home path '+str(p)
assert len({u['session_id']+'|'+u['response_id'] for u in usage})==len(usage)
assert all(e['task_id'] in tasks or e['task_id'] in {None,'UNKNOWN'} for e in export)
validation={'result':'PASS','zip':str(zip_path.relative_to(R)),'zip_sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest(),'bytes':zip_path.stat().st_size,'files':len(manifest)+1,'extracted_to':str(ex),'checks':['ZIP CRC and safe paths','all manifest SHA256','all JSON/JSONL parse','unique usage response identity','task identity links','allowed file types only; no binary/database/capture/build artifacts','known credential and home-path pattern scan'],'scope':'export integrity only; no product/hook completeness claim'}
zip_path.with_suffix('.verification.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
# Validation is adjacent to archive to avoid self-referential ZIP hashes.
print(json.dumps({'validation':validation,'summary':summary},ensure_ascii=False,indent=2))
