#!/usr/bin/env python3
"""Render the agreement review, preserving the previous report byte for byte."""
from pathlib import Path
from html.parser import HTMLParser
import json,html,re,hashlib,datetime
R=Path(__file__).resolve().parents[2];O=R/'reports/v1/agreement-review';O.mkdir(parents=True,exist_ok=True)
def e(s):return html.escape(str(s))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
text=(R/'docs/agreement-review.md').read_text(); start=json.loads((R/'.harness/v1/agreement-review/start.json').read_text())
issues=[];hashes={}
def source(p):
 path=R/p
 if not path.is_file():issues.append(p);return '<strong>근거 누락 '+e(p)+'</strong>'
 assert not any(x in p for x in ['logs/','session','local.properties','.codex/','.kmp-agent/','data/memos'])
 relative='evidence/'+p+'.html';f=O/relative;f.parent.mkdir(parents=True,exist_ok=True); hashes[p]=digest(path)
 f.write_text('<!doctype html><html lang=ko><meta charset=utf-8><meta name=viewport content="width=device-width"><title>'+e(p)+'</title><style>body{font:15px/1.7 system-ui;margin:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>'+e(p)+'</h1><p>현재 읽기용 사본 · SHA-256 '+hashes[p]+'</p><pre>'+e(path.read_text())+'</pre>')
 return '<a target=_blank rel=noopener href="'+relative+'">'+e(p)+'</a>'
def section(name):
 begin=text.index('## '+name); end=text.find('\n## ',begin+4)
 return text[begin:end if end>=0 else None]
def table(section_text):
 result=[]
 for line in section_text.splitlines():
  if line.startswith('|'):
   cells=[x.strip() for x in line.strip('|').split('|')]
   if all(re.fullmatch('[- :]+',x or '-') for x in cells):continue
   result.append(cells)
 return result
matrix=table(section('합의 대조')); evidence=table(section('근거와 변경 권한')); plan=table(section('수정 계획'))
def badge(s):
 tone='bad' if '불일치' in s else 'unknown' if any(x in s for x in ['미확인','부분','보완']) else 'ok'
 return '<span class="badge '+tone+'">'+e(s)+'</span>'
def htmltable(data,judgement=False):
 out='<div class=table-scroll><table><thead><tr>'+''.join('<th>'+e(c)+'</th>' for c in data[0])+'</tr></thead><tbody>'
 for row in data[1:]:
  out+='<tr>'+''.join('<td>'+(badge(c) if judgement and i==3 else e(c))+'</td>' for i,c in enumerate(row))+'</tr>'
 return out+'</tbody></table></div>'
codepaths=['settings.gradle.kts','androidApp/settings.gradle.kts','shared/build.gradle.kts','server/build.gradle.kts','server/src/main/kotlin/memo/server/Main.kt','server/src/main/kotlin/memo/server/MemoStore.kt','shared/src/commonMain/kotlin/memo/domain/BodyPolicy.kt','shared/src/commonMain/kotlin/memo/client/SaveMachine.kt','androidApp/src/main/kotlin/memo/android/MainActivity.kt','iosApp/MemoApp.swift','web/src/jsMain/kotlin/memo/web/Main.kt']
codepaths+=['tools/project_workflow.py','tools/verify_settings_alignment.py']
docpaths=['docs/agreement-review.md','docs/product.md','docs/technical-decisions.md','docs/project-settings.json','docs/current-implementation.json','docs/target-architecture.md','docs/settings-alignment.md','docs/settings-alignment-result.md','.harness/v1/settings-correction/history/docs/project-settings.json','docs/feedback.md','docs/retrospective.md','docs/v1-acceptance-status.md','docs/design-conformance.md','.harness/v1/reviews/planning.json']
docpaths+=['.harness/v1/active-baseline.json','.harness/v1/settings-correction/bindings.json']
sources='<ul>'+''.join('<li>'+source(p)+'</li>' for p in docpaths+codepaths)+'</ul>'
old_sha=digest(R/'reports/v1/index.html'); assert old_sha==start['files']['reports/v1/index.html']
archive=R/'reports/memo-v1-review-20261021T045851Z.zip';assert digest(archive)==start['files'][str(archive.relative_to(R))]
changed=[p for p in start['product_files'] if digest(R/p)!=start['files'][p]]
buildpaths=['build.gradle.kts','settings.gradle.kts','server/build.gradle.kts','shared/build.gradle.kts','web/build.gradle.kts','androidApp/build.gradle.kts','androidApp/settings.gradle.kts']
changed += [p for p in buildpaths if digest(R/p)!=start['files'][p]]
assert not changed,changed
work=R/'.harness/v1/settings-correction/work.json'; tracking=json.loads(work.read_text()) if work.exists() else {}
tracking={k:tracking.get(k,'UNKNOWN') for k in ['task_id','agent_run_id','run_id','started_at','baseline']}
intervention_path=R/'.harness/v1/agreement-review/intervention.json'
intervention=json.loads(intervention_path.read_text()) if intervention_path.exists() else {}
meta=dict(generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),product_head=start['product_head'],implementation='WORKING_TREE / dirty',harness=start['harness'],agreement_input='SRC-006/E-01 + SRC-007 corrected target settings; product transition not authorized',old_report_sha256=old_sha,product_or_build_changes=changed,source_hashes=hashes,tracking=tracking,source_message_id='UNKNOWN',source_turn_id='UNKNOWN',intervention_collection='PENDING; no actual collection success inferred',usage='UNKNOWN',cost='UNKNOWN',regenerate='rtk proxy python3 tools/v1-report/agreement.py')
meta.update(source_message_id=intervention.get('source_message_id','UNKNOWN'),source_turn_id=intervention.get('source_turn_id','UNKNOWN'),source_event_id=intervention.get('source_event_id','UNKNOWN'),intervention_collection=intervention.get('collection','PENDING'))
meta['source_reference_scope']='IDs above are preserved SRC-006 approval/intervention evidence; SRC-007 request event/Stop collection is UNKNOWN, not inferred.'
active=json.loads((R/'.harness/v1/active-baseline.json').read_text())
meta['current_target_baseline']={k:active.get(k,'UNKNOWN') for k in ['baseline_id','status','implementation_authorized','planning_review','design_review','target_compliance']}
overview='''<div class="alert"><strong>합의 불일치 · 미해결</strong><span>기능 시험 PASS와 합의 준수는 별개입니다.</span></div>
<div class=grid><article><h2>주요 이탈</h2><ul><li>Android/iOS: 합의는 <b>Compose Multiplatform</b>, 구현은 View·SwiftUI.</li><li>서버: 합의는 <b>Ktor</b>, 구현은 JDK HttpServer.</li><li>구조: 합의한 공통/전용 domain·data·presentation 모듈이 생략됨.</li></ul><p class=muted>대체 구현의 명시적 사용자 승인 근거를 찾지 못했습니다.</p></article>
<article><h2>수정 우선순위</h2><p><b>P0</b> 합의·위임 근거와 문서 정정 — 이번 범위.</p><p><b>P1</b> Ktor·두 앱 UI·모듈 경계 복구 계획 — 구현 미착수.</p><p class=muted>SQLite는 호환 최소안 위임 내 선택으로 분리합니다. 사용 자체를 결함으로 판정하지 않습니다.</p></article>
<article><h2>사용자 결정 1건</h2><p><b>웹도 같은 UI 기술·공유 화면 범위에 포함할지</b> 미확인입니다.</p><p>Android/iOS의 Compose Multiplatform과 Ktor 사용은 이미 합의됐으므로 다시 묻지 않습니다.</p></article>
<article><h2>기능과 남은 인수</h2><p>기존 관측에서 목록·작성·저장·같은 시도 복구가 동작했습니다. 이번에는 제품 시험을 재실행하지 않았습니다.</p><p><b>누락 확인:</b> 미저장 뒤로가기 확인창은 시안에 있었으나9개 상태 비교/캡처에서 제외됐습니다. 세 플랫폼 상태 비교는 <b>NOT_RUN</b>입니다.</p><p><b>전체 v1 BLOCKED</b> · 실제 보조기술, 일부 탐색, 변경 후 웹200% 확대도 남아 있습니다.</p></article></div>'''
legacy_overview=overview
overview='''<div class="alert"><strong>설정·기준 연결 정정</strong><span>제품 전환 구현은 시작하지 않았습니다.</span></div><div class=grid>
<article><h2>승인 목표와 구현 사실 분리</h2><p><b>목표:</b> Compose Multiplatform Android/iOS · Ktor · 공통/전용 domain·data·presentation 경계.</p><p><b>관측:</b> 기존 View·SwiftUI·HttpServer는 별도 current-implementation.json에 보존했습니다.</p><p class=muted>UI 전체 설정은 웹 때문에 UNDECIDED이며, 모바일 결정은 CONFIRMED입니다. SQLite 선택은 유지합니다.</p></article>
<article><h2>앞으로의 실행·검토 기준</h2><p>낡은 동결 설정은 프로젝트 진입 검사에서 거부합니다. 과거 설정·리뷰 PASS는 이력으로 보존하고 정정 목표에 승계하지 않습니다.</p><p><b>현재 baseline BLOCKED · 전환 실행 권한 없음.</b> 정정 입력의 태스크는 TODO로만 구성했고 제품 실행은 0건입니다.</p></article>
<article><h2>남은 사용자 결정 1건</h2><p><b>웹도 같은 UI 기술·공유 화면 범위에 포함할지</b>입니다.</p><p>모바일 UI·Ktor·모듈 경계는 이미 확정됐습니다.</p></article></div>'''
overview+='<details><summary>변경 파일·소비 경로·정합성 검사</summary>'+source('docs/settings-alignment-result.md')+'<br>'+source('docs/project-settings.json')+'<br>'+source('docs/current-implementation.json')+'</details><details><summary>기존 기능과 남은 제품 인수 · 상태 비교 누락 포함</summary>'+legacy_overview+'</details>'
if (R/'.harness/v1/settings-correction/preservation-note.md').exists():
 overview+='<p class="muted">보존 제한: 과거 보고서의 상세 HTTP 목록1개는 경로 충돌로 원문 복원 불가(UNKNOWN)입니다. 불변 리뷰·당시 결과 요약·제품 시험 원본은 보존했습니다. 상세는 변경 파일·정합성 검사 문서에 기록했습니다.</p>'
agreements='<h2>합의한 기준과 실제 구현</h2><p class=muted>SRC-007에서 설정은 정정됐지만 제품 구현 이탈은 아직 남아 있습니다. 아래 E-05의 CONFIRMED는 보존된 과거 설정을 가리킵니다. 정정된 설정의 확인 상태와 제품 준수 PASS를 혼동하지 않습니다.</p>'+htmltable(matrix,True)+'<details><summary>한 번만 읽는 근거표 · 원문·위임·승인 범위</summary>'+htmltable(evidence)+'<p>원문 위치·이벤트·발췌 텍스트 해시는 아래 합의 검토 문서에 있습니다. 원본 세션 로그 전체는 제공하지 않습니다.</p>'+source('docs/agreement-review.md')+'</details>'
planning='<h2>수정 계획 · 이번에는 제품 구현 없음</h2>'+htmltable(plan)+'<details><summary>기존 검토에서 놓친 경위 · 확인된 범위만</summary><ol><li>앞선 명시적 구조 합의와 이후 “미정” 정리의 충돌을 해소하지 못했습니다.</li><li>호환 최소안 위임을 UI/Ktor/모듈 합의 변경 권한으로 확대했습니다.</li><li>기획 검토는 위임 선택을 인정했고, 기능·디자인 시험은 목표 스택/계층 준수 검증을 빠뜨렸습니다.</li><li>직전 설명도 사용자 합의를 KMP 방향으로 축소했습니다. 이번 원문 대조로 정정했습니다.</li></ol><p>모든 과거 검토가 원문을 읽지 않았다고 단정하지 않습니다. 공통 하네스 코드 결함으로 원인을 확정하지도 않습니다. FB-004 / RETRO-009는 사용자 오류 수정 개입으로 기록합니다.</p>'+source('docs/feedback.md')+'<br>'+source('docs/retrospective.md')+'</details>'
architecture='''<h2>실제 구현과 목표 구조</h2><div class=grid><article><h3>현재 구현 · 변경하지 않음</h3><p><b>shared / server / web + 별도 Android 빌드 + SwiftUI 앱</b></p><p>shared: 본문 정책·Unicode·DTO·저장 상태.<br>플랫폼별 UI·HTTP·저장 구현.<br>서버: HttpServer + MemoStore + SQLite.</p><p class=bad>모바일 UI·서버 런타임·전용 계층은 목표와 불일치합니다.</p></article>
<article><h3>합의 목표 · 아직 구현되지 않음</h3><p><b>Ktor + Compose Multiplatform Android/iOS</b></p><p>공통 model / 순수 domain.<br>서버·클라이언트 각각 전용 domain / data / presentation.<br>각 data·presentation → 해당 전용 domain → 공통 domain.<br>전용 domain 간 참조 없음. 진입점에서 DI.</p><p class=muted>웹 UI 적용 범위는 UNKNOWN. 특정 DI 라이브러리는 합의되지 않았습니다.</p></article></div>
<details><summary>현재 구성도 · 실제 코드의 빌드 의존과 런타임 통신</summary><p>아래 그림은 실제 구현이며 목표 구조로 승인됐다는 뜻이 아닙니다. 이미지는 클릭해 확대할 수 있습니다.</p><a target=_blank href="../component.svg"><img src="../component.svg" alt="현재 구현 빌드 의존 구성도"></a><a target=_blank href="../runtime.svg"><img src="../runtime.svg" alt="현재 구현 런타임 통신"></a></details>
<details><summary>상세 기술 스펙·호출 흐름·전체 라이브러리</summary><p>당시 구현을 설명한 기존 상세 보고서입니다. 에이전트 선택을 사용자 승인으로 취급하지 않습니다. 현재와 다른 iOS UserDefaults 기술 메모는 파일 atomic+fsync로 정정했습니다.</p><a target=_blank href="../index.html#spec">기존 상세 기술 스펙</a> · <a target=_blank href="../index.html#architecture">실제 저장/복구 흐름</a></details>'''
history='<h2>기존 결과와 원본 보존</h2><article><p>기존 보고서 HTML과 ZIP은 바꾸지 않았습니다. 과거 기능/디자인 PASS·작업 원장·실행 결과는 해당 당시 입력과 범위로 유지합니다. 합의 적합성에 대한 새 PASS나 제품 완료를 선언하지 않습니다.</p><a target=_blank href="../index.html">기존 상세 보고서 · 당시 구현/검증 이력</a><p>기존 baseline은 당시 입력입니다. SRC-006 문서 정정으로 입력이 달라졌으므로 과거 검토 PASS/ACTIVE를 최신 목표의 검토 통과나 구현 착수 권한으로 승계하지 않습니다.</p></article><details><summary>테스트·캡처·실행 상세 — 필요할 때만</summary><a target=_blank href="../index.html#validation">기존 항목별 검증·비교 캡처</a> · <a target=_blank href="../ui-verification.json">기존 보고서 표시 검증</a><p>DB 관측은 당시 실제8080 서버의 DB 경로·스키마·총6건 확인에 한정됩니다. DB·메모 본문·개인 설정·원본 세션 로그는 새 보고서에 복사하지 않습니다.</p></details><details><summary>이번 조사 원본·코드·사용자 개입 근거</summary>'+sources+'</details><details><summary>코드 기준·입력·해시·실행 ID·수집 한계</summary><pre>'+e(json.dumps(meta,ensure_ascii=False,indent=2))+'</pre></details><p class=muted>수동 재생성: <code>rtk proxy python3 tools/v1-report/agreement.py</code>. 기존 보고서/ZIP을 덮어쓰지 않습니다.</p>'
css='''*{box-sizing:border-box}body{margin:0;background:#f5f7f3;color:#263e34;font:15px/1.65 system-ui,sans-serif}main,body>header,nav{max-width:1200px;padding:20px;margin:auto}body>header{padding-bottom:6px}h1{font-size:29px;line-height:1.35;margin:6px 0}h2{font-size:20px;margin:0 0 12px}h3{margin:0 0 10px}p{margin:8px 0}ul{padding-left:22px;margin:8px 0}.eyebrow{font-size:12px;letter-spacing:.13em;color:#5c6c60}.muted,small{color:#5b6c61}.alert{background:#fff0e7;border:1px solid #e3b6a0;border-left:5px solid #a14c34;border-radius:12px;padding:15px 18px;margin-bottom:16px;display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}article{border:1px solid #d9e2d7;border-radius:14px;background:white;padding:20px;margin-bottom:16px}.grid article{margin:0}nav{display:flex;gap:8px;flex-wrap:wrap;position:sticky;top:0;z-index:2;background:#f5f7f3f7;padding-top:10px;padding-bottom:10px}button{font:inherit;padding:9px 14px;border:1px solid #b3c3b5;border-radius:8px;background:white;color:#294838;cursor:pointer}button[aria-selected=true]{background:#285b46;color:white}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #497da4;outline-offset:3px}a{color:#245f87;overflow-wrap:anywhere}details{border:1px solid #d9e2d7;border-radius:12px;background:white;padding:14px 18px;margin-top:16px}summary{font-weight:600;cursor:pointer}pre{font:12px/1.6 monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4ee;padding:16px;border-radius:8px;max-height:500px;overflow:auto}.table-scroll{overflow:auto;border:1px solid #d8e2d5;border-radius:12px;background:white}table{border-collapse:collapse;width:100%;min-width:940px;font-size:14px}th,td{padding:14px;text-align:left;vertical-align:top;border-bottom:1px solid #e0e6dc}th{background:#eaf0e6}td:first-child{width:19%;font-weight:600}td:nth-child(2){width:22%}td:nth-child(3){width:23%}td:nth-child(4){width:13%}.badge{display:inline-block;padding:4px 7px;border-radius:7px;font-size:12px;line-height:1.5;font-weight:600}.bad{color:#9b3e2b}.badge.bad{background:#ffe6dd}.badge.ok{background:#e4f0e2;color:#2a653b}.badge.unknown{background:#fff0ce;color:#795b21}img{display:block;width:100%;height:auto;margin-top:16px;border:1px solid #dce3d8;border-radius:9px}code{overflow-wrap:anywhere}[hidden]{display:none!important}footer{margin-top:20px;font-size:12px;color:#5b6c61}@media(max-width:700px){main,body>header,nav{padding:14px}.grid{grid-template-columns:1fr}h1{font-size:25px}.alert{display:block}.alert span{display:block;margin-top:5px}article{padding:17px}table{font-size:13px}}'''
pages=[('overview','핵심 요약',overview),('agreements','합의 대조',agreements),('plan','수정 계획',planning),('architecture','실제·목표 구조',architecture),('history','기존 근거',history)]
body='<!doctype html><html lang=ko><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>메모 v1 · 합의 준수 검토</title><style>'+css+'</style><header><div class=eyebrow>MEMO v1 / AGREEMENT REVIEW</div><h1>승인 목표와 실행 기준 정정</h1><small>SRC-007 · 설정·기준 연결 정정 · 2026-10-21 · 조사·문서 범위</small></header><nav role=tablist aria-label="검토 보고서">'+''.join('<button role=tab aria-controls="'+id_+'" aria-selected="'+('true' if i==0 else 'false')+'">'+name+'</button>' for i,(id_,name,_) in enumerate(pages))+'</nav><main>'+''.join('<section role=tabpanel id="'+id_+'"'+(' hidden' if i else '')+'>'+content+'</section>' for i,(id_,_,content) in enumerate(pages))+'<footer>제품 코드·DB·설치 하네스 변경 없음 · 구조 전환 및 전환 후 검증 NOT_RUN · 커밋·푸시·배포 없음</footer></main><script>const tabs=[...document.querySelectorAll("[role=tab]")];function show(t){tabs.forEach(x=>{const selected=x===t;x.setAttribute("aria-selected",selected);document.getElementById(x.getAttribute("aria-controls")).hidden=!selected});history.replaceState(null,"","#"+t.getAttribute("aria-controls"));window.scrollTo(0,0)}tabs.forEach(t=>t.onclick=()=>show(t));const initial=tabs.find(t=>"#"+t.getAttribute("aria-controls")===location.hash);if(initial)show(initial);</script></html>'
(O/'index.html').write_text(body)
class Refs(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):self.refs.extend(v for k,v in attrs if k in ['href','src'] and v)
parser=Refs();parser.feed(body)
for ref in parser.refs:
 p=(O/ref.split('#')[0]).resolve()
 if not p.is_relative_to((R/'reports/v1').resolve()) or not p.is_file():issues.append(ref)
meta['issues']=issues;meta['local_reference_count']=len(parser.refs);meta['report_sha256']=digest(O/'index.html')
(O/'provenance.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print(json.dumps({'report':str(O/'index.html'),'rows':len(matrix)-1,'issues':issues,'old_report_preserved':True,'old_zip_preserved':True,'product_build_unchanged':not changed},ensure_ascii=False,indent=2))
raise SystemExit(1 if issues else 0)
