#!/usr/bin/env python3
"""Derived offline report. Reads originals; no DB access, tests or ledger mutation."""
from pathlib import Path
import json, re, html, hashlib, shutil, subprocess, datetime, collections
R=Path(__file__).resolve().parents[2]; O=R/'reports/v1'; O.mkdir(parents=True,exist_ok=True)
def read(p): return (R/p).read_text()
def load(p): return json.loads(read(p))
def h(p): return hashlib.sha256((R/p).read_bytes()).hexdigest() if (R/p).is_file() else None
def e(x): return html.escape(str(x))
issues=[]; sources={}
def link(p):
 if not (R/p).is_file(): issues.append({'path':p,'issue':'MISSING'}); return '<b class=warn>근거 누락 '+e(p)+'</b>'
 assert not any(x in p for x in ['events.jsonl','session','local.properties','.codex/','.aws/','data/memos'])
 dest='sources/'+p+'.html'; f=O/dest; f.parent.mkdir(parents=True,exist_ok=True); sources[p]=h(p)
 f.write_text('<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width"><style>body{font:15px/1.7 system-ui;margin:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><p>원본 읽기용 사본: '+e(p)+'</p><p>SHA256 '+h(p)+'</p><pre>'+e((R/p).read_text(errors='replace'))+'</pre>')
 return '<a target=_blank rel=noopener href="'+e(dest)+'">'+e(p)+'</a>'
def detail(title,value): return '<details><summary>'+e(title)+'</summary><pre>'+e(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2))+'</pre></details>'
def badge(s): return '<span class="badge '+('pass' if s=='PASS' else 'warn' if s in ['FAIL','BLOCKED','NOT_RUN'] else 'unknown')+'">'+e(s)+'</span>'
B=load('.harness/v1/active-baseline.json'); M=load('.harness/v1/design-conformance/manifest.json'); A=load('.harness/v1/acceptance-final-manifest.json'); T=load('.harness/tasks/tasks.yaml')['tasks']; D=load('.harness/v1/html-report-runtime.json')
if B.get('status')!='ACTIVE' or B.get('implementation_authorized') is not True or B.get('baseline_id')!=M.get('active_baseline',{}).get('baseline_id'):
 raise SystemExit('Historical report generator blocked: current approved-target baseline is not authorized/matched. Use tools/v1-report/agreement.py for the correction report; preserve old evidence.')
checks=[]
for group,mapping in [('최신 소스',M['source_files']),('최신 바이너리',M['binaries']),('이전 통합',A['files']),('입력 baseline',{x['path']:x['sha256'] for x in B['inputs']})]:
 for p,digest in mapping.items(): checks.append(dict(group=group,path=p,expected=digest,current=h(p),result='MATCH' if h(p)==digest else 'MISSING' if h(p) is None else 'CHANGED'))
for p,digest in M.get('evidence_sha256',{}).items():
 checks.append(dict(group='최신 결과 무결성',path=p,expected=digest,current=h(p),result='MATCH' if h(p)==digest else 'MISSING' if h(p) is None else 'CHANGED'))
for name in ['server','shared']:
 observations=load('.harness/v1/reviews/'+name+'.json')['observations']
 for p,digest in observations.get('reports',observations.get('report_hashes',{})).items():
  checks.append(dict(group='기존 시험 XML',path=p,expected=digest,current=h(p),result='MATCH' if h(p)==digest else 'MISSING' if h(p) is None else 'CHANGED'))
latest_ok=all(x['result']=='MATCH' for x in checks if x['group'] not in ['이전 통합','기존 시험 XML'])
server_ok=all(h(p)==digest for p,digest in A['files'].items() if p.startswith(('shared/src/','server/src/')) or p in ['server/build.gradle.kts','shared/build.gradle.kts'])
def runs(task): return [{k:x.get(k,'UNKNOWN') for k in ['agent_run_id','run_id','started_at','ended_at','kind','execution_mode']} for x in T.get(task,{}).get('executions',[])]
ledger={k:dict(state=v['state'],criteria=v['criteria'],executions=runs(k)) for k,v in T.items() if k.startswith('V1')}
(O/'task-executions.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2))
expected={}; req={}; design={}
for feature in ['memo-list','memo-create']:
 rp=f'docs/features/{feature}/requirements.md'; dp=f'docs/features/{feature}/design.md'
 for line in read(rp).splitlines():
  c=[s.strip() for s in line.strip().strip('|').split('|')]
  if len(c)==3 and re.fullmatch(r'FEAT-\d+-AC-\d+',c[0]): expected[c[0]]=c[2];req[c[0]]=(rp,c[1])
 for line in read(dp).splitlines():
  c=[s.strip() for s in line.strip().strip('|').split('|')]
  if len(c)>=3 and re.fullmatch(r'FEAT-\d+-AC-\d+',c[0]): design[c[0]]=(dp,c[1])
expected.update({'V1-NAV-001':'일반 미저장 초안은 새로고침·앱 재진입 후 자동 복원 없음. 화면 내 취소 확인 유지.','V1-RECOVERY-001':'전송 전 보존한 같은 시도 키·본문으로 전송 중 종료/응답 유실 후 복구하며 한 건 보장.'})
steps=[
'지연 GET 설정 → 목록 진입 → 응답 전/후 로딩과 본문 관측',
'다른 시각 및 동률 고정 ID 데이터 → 반복 조회 → 세 클라이언트 순서 비교',
'빈 시험 DB → GET → 빈 안내·작성 진입 확인',
'최초 GET503/서버 중단 → 서버 복구 → 재시도',
'저장 성공 ID 기록 → 재조회·반복 응답 → 같은 ID 표시 횟수 비교',
'POST 성공 후 GET만 실패 → GET 재시도 → 성공 메모 유지·POST 횟수 확인',
'앞뒤 공백·내부 들여쓰기·개행 본문 저장 → 반환/목록/DB 대조',
'빈 값·공백·1/2000/2001 자소군·한글/이모지 계약 벡터 → 전송/차단 판정',
'POST 지연 → 잠금/닫힘 관측 → COMMIT 성공 응답 후 목록 반영',
'422 주입 → 본문 유지 → 편집·재저장 (413은 서버 시험 별도)',
'커밋 후 연결 종료 → 같은 DB 재시작/클라이언트 재진입 → 같은 키 복구 → 한 건',
'연속 저장/동일 키 경합 → 한 건; 새 UUID 동일 본문 → 별개 두 건',
'성공 확인 → 같은 DB 서버 재시작 → 앱 재진입/웹 새로고침 → ID·본문 확인',
'일반 초안 입력 → 강제 종료/새로고침 → 재진입 → 자동 비복원 확인',
'지연 POST 중 프로세스 종료/새로고침 → pending 복구 → 같은 키 재확인 → 한 건']
platforms=['Android','iOS','웹','서버/DB']; rows=[]
codes={'Android':'androidApp/src/main/kotlin/memo/android/MainActivity.kt','iOS':'iosApp/MemoApp.swift','웹':'web/src/jsMain/kotlin/memo/web/Main.kt','서버/DB':'server/src/main/kotlin/memo/server/MemoStore.kt','공유':'shared/src/commonMain/kotlin/memo/client/SaveMachine.kt'}
envs={'Android':'emulator-5554 · Small_Phone API36 arm64 · 격리 DB','iOS':'Xcode26.6 · iOS26.5 arm64 Simulator · 격리 DB','웹':'Chrome155 · 실제 브라우저 · 시험 전용18080 프록시/18081 JVM/18082 제어','서버/DB':'JDK17 · JUnit · 실제 HTTP · 임시 SQLite 파일/독립 연결'}
commands={'Android':'rtk proxy python3 androidApp/tools/acceptance.py (기존 실행 재사용)','iOS':'rtk proxy python3 iosApp/tools/test.py / xcodebuild test (기존 xcresult 재사용)','웹':'실제 Chrome UI 조작 + 전용 장애 프록시 HTTP/SQLite 대조','서버/DB':'rtk proxy ./gradlew :server:test --console=plain'}
evs={'Android':['.harness/v1/android-acceptance-20261020-202155/summary.json','.harness/v1/android-acceptance-20261020-202449/summary.json',M['android']['summary']], 'iOS':['docs/v1-acceptance-status.md',M['ios']['five_tests'],M['ios']['latest_list_error_test'],M['ios']['delta']], '웹':['.harness/v1/web-acceptance-product.json','.harness/v1/web-proof.json','.harness/v1/design-conformance/web/result.json'], '서버/DB':['.harness/v1/reviews/server.json','server/build/test-results/test/TEST-memo.server.ServerTest.xml']}
matrix=[]
for line in read('docs/v1-acceptance-status.md').splitlines():
 c=[s.strip() for s in line.strip().strip('|').split('|')]
 if line.startswith('|') and len(c)==6 and re.match(r'(FEAT-|V1-NAV-|V1-RECOVERY-)',c[0]): matrix.append(c)
for n,c in enumerate(matrix):
 cid=c[0].split()[0]
 for i,p in enumerate(platforms):
  actual=c[i+2]
  if actual.startswith('N/A') or (p=='서버/DB' and cid in ['FEAT-001-AC-003','FEAT-001-AC-004','V1-NAV-001']):continue
  status='PASS' if (server_ok if p=='서버/DB' else latest_ok) else '재검증 필요'
  if p=='서버/DB' and not any(x in actual for x in ['PASS','영속성']):status='UNKNOWN'
  rp,rid=req.get(cid,('docs/product.md','SRC-005 / D-004')); dp,did=design.get(cid,('docs/api-contract.md','저장 시도·초안·탐색 계약'))
  rows.append(dict(id=cid+'/'+p,condition=cid,platform=p,required='기존 필수',status=status,expected=expected.get(cid,'UNKNOWN'),actual=actual+' · 과거 통과 범위만 재사용. 최신 업무 영역 불변 대조와 표시 집중 검사를 결합하며 과거 전체 UI PASS를 승계하지 않음.',req=rid,reqpath=rp,design=did,designpath=dp,steps=steps[n],env=envs[p],command=commands[p],method='자동 시험 + 에이전트 변경 영향 검토' if p!='웹' else '에이전트 실제 브라우저 검토 + HTTP/DB 대조',code=codes[p],evidence=evs[p]+(['.harness/v1/design-conformance/business-reuse.json'] if p!='서버/DB' else []),task='V1-INTEGRATION'))
def add(cid,p,required,status,expect,actual,ev,method='에이전트 검토',task='V1-INTEGRATION',step='원본 문서의 해당 체크리스트 참조'):
 rows.append(dict(id=cid,condition=cid,platform=p,required=required,status=status,expected=expect,actual=actual,req='기존 문서 기준' if required=='기존 필수' else '추가 제안/관측이며 신규 필수 아님',reqpath='docs/integration-acceptance.md',design='SCREEN-LIST / SCREEN-CREATE; 탐색·포커스·접근성',designpath='docs/features/memo-create/design.md',steps=step,env=envs.get(p,'기존 플랫폼 환경 및 원장'),command='이번 범위에서 제품 시험 재실행 없음',method=method,code=codes.get(p,'docs/integration-acceptance.md'),evidence=ev,task=task))
for p,tool in [('Android','TalkBack'),('iOS','VoiceOver'),('웹','실제 스크린리더')]:
 add('A11Y-'+p,p,'기존 필수','NOT_RUN',tool+' 읽기 순서·상태 알림·모달 탐색·포커스 복귀 확인','실제 음성/탐색 세션 증거 없음. 자동 AX 감사/글자 확대는 대체하지 못함.',['docs/v1-acceptance-status.md'],step='목록→작성→입력 오류→저장 중/불확실 안내→취소 모달. 음성·포커스 관측을 남김')
add('NAV-REMAINING','전체 연동','기존 필수','NOT_RUN','세 플랫폼의 기존 뒤로/앞으로/스와이프·취소·저장 시도 복구 계약 준수','Android Back·iOS 기본 취소 팝오버 일부 PASS. 남은 제스처 조합의 실행 및 상세 명세/실행 연결 부족.',['docs/v1-acceptance-status.md','docs/api-contract.md'])
add('V1-INTEGRATION-CHECK','전체 연동','기존 필수',T['V1-INTEGRATION']['state'],'모든 필수 기준에 유효한 실제 타깃 검증 근거','원장 BLOCKED · 필수 전체 기준 NOT_RUN · v1 전체 완료 아님.',['docs/v1-acceptance-status.md','.harness/v1/acceptance-review.json'])
for p in platforms[:3]:
 ev={'Android':[M['android']['summary']],'iOS':[M['ios']['five_tests'],M['ios']['latest_list_error_test'],M['ios']['delta']],'웹':['.harness/v1/design-conformance/web/result.json']}[p]
 add('DESIGN-'+p,p,'기존 필수','PASS' if latest_ok else '재검증 필요','현재 디자인의 버튼·본문·글자 수·안내·토큰·카드·9개 상태 준수','집중 회귀 및 실제 화면 비교 PASS. iOS110925 5건은 목록 오류 색상 한 줄 변경 외 분기 한정 재사용; 변경 분기는111454 1건. OS 글꼴·safe area·단위는 기술 검토된 적응이며 과거 사용자 승인 차이로 표현하지 않음.',ev+['docs/design-conformance.md'],task='V1-DESIGN-CONFORMANCE')
add('WEB-ZOOM','웹','기존 필수','재검증 필요','실제 Chrome200%에서 잘림/겹침 없이 저장 접근','기존 실제200% PASS 이후 헤더/표시 변경. 동일 확대의 최신 영향 관측 연결 부족.',['.harness/v1/chrome-zoom-proof.json','docs/design-conformance.md'])
add('ANDROID-FONT','Android','기존 필수','PASS' if latest_ok else '재검증 필요','글꼴200%·3줄 미리보기·버튼 접근','최신 largeFontAndThreeLinePreview PASS; 실제 TalkBack과 별개.',[M['android']['summary']],'자동 계측')
add('IOS-AX-AUDIT','iOS','기존 필수','PASS' if latest_ok else '재검증 필요','Dynamic Type·대비·타깃/라벨·잘림 감사','110925 집중5건에 앱 소유 요소 감사 포함. 실제 VoiceOver 통과 아님.',[M['ios']['five_tests'],'docs/design-conformance.md'],'XCTest 자동 감사 + 에이전트 영향 검토')
add('SHARED-UNICODE','공유','기존 필수','PASS' if server_ok else '재검증 필요','Unicode16 공식 분할 벡터·본문 경계·시도 저장 실패/복구 상태 전이','JVM 공통4건 PASS. 네이티브/JS 공식 전체 벡터 직접 실행은 NOT_RUN; 플랫폼 입력 경계와 구분.',['.harness/v1/reviews/shared.json','shared/build/test-results/jvmTest/TEST-memo.UnicodeConformanceTest.xml','shared/build/test-results/jvmTest/TEST-memo.PolicyTest.xml'],'자동 JVM 시험',task='V1-SHARED')
add('DB-OBSERVED','서버/DB','관측 근거','PASS','8080 런타임 MEMO_DB와 같은 파일을 읽기 전용 조회',f"PID{D['pid']} · {D['at']} · {D['count']}건 · schema v{D['schema_version']}. 단일 시점만 증명; 모든 클라이언트 저장/재시작/중복 방지로 확대하지 않음.",['.harness/v1/html-report-runtime.json'],'에이전트 읽기 전용 관측',step='lsof8080→동일 PID의 ps MEMO_DB/cwd/JAR 대조→SQLite mode=ro/query_only→database_list/schema/COUNT(*)')
add('PROPOSE-COMPATIBILITY','전체 연동','추가 제안','NOT_RUN','최소 지원 OS·추가 브라우저·실기기 대표 흐름 확인','추가 호환성 매트릭스 제안. 승인 전 기존 필수 범위에 자동 편입하지 않음.',['androidApp/build.gradle.kts','iosApp/Memo.xcodeproj/project.pbxproj'])
for p in platforms[:3]:
 add('BUILD-'+p,p,'기존 필수','PASS' if latest_ok else '재검증 필요','대상 실행 산출물 빌드 및 선택된 에뮬레이터/시뮬레이터/브라우저에서 기동','실제 실행 결과와 최신 바이너리 해시가 연결됨. 빌드 성공을 기능 전체 통과로 취급하지 않음.',evs[p]+['.harness/v1/design-conformance/manifest.json'],'자동 빌드 + 실제 기동 관측',task={'Android':'V1-ANDROID','iOS':'V1-IOS','웹':'V1-WEB'}[p])
add('REQ-COVERAGE-L004','전체 연동','관측 근거','UNKNOWN','L-REQ-004: 페이지 분할 없이 MVP 전체 목록 조회·표시','원본은 INFERRED/기획 제안으로 보존됨. 기존 AC 표에 직접 연결 ID가 없어 고유 REQ 집계에서 빠짐. 서버 전체 조회/클라이언트 렌더 구현 존재와 해당 조건의 개별 시험·필수 확정 근거는 별개. 신규 대량 데이터 기준을 만들지 않음.',['docs/features/memo-list/requirements.md','server/src/main/kotlin/memo/server/MemoStore.kt','docs/v1-acceptance-status.md'])
# Auxiliary display checks point to existing design clauses; no newly invented REQ IDs.
for r in rows:
 if r['id'].startswith(('DESIGN-','A11Y-')) or r['id'] in ['WEB-ZOOM','ANDROID-FONT','IOS-AX-AUDIT']:
  r['req']='기능 AC의 표시 검토; 별도 REQ ID 없음 (원본 디자인 키보드·스크롤·접근성 절)'
  r['design']='SCREEN-LIST/L-CARD,L-REFRESH,L-CREATE; SCREEN-CREATE/C-BODY,C-EDIT,C-SAVE,C-INVALID,C-SAVING,C-FAILED,C-UNCERTAIN'
 if r['platform'] in ['Android','iOS','서버/DB']:
  testfile={'Android':'androidApp/src/androidTest/kotlin/memo/android/AcceptanceTest.kt','iOS':'iosApp/MemoUITests.swift','서버/DB':'server/src/test/kotlin/memo/server/ServerTest.kt'}[r['platform']]
  r['evidence']=r['evidence']+[testfile]
spec=[]
def tech(module,declared,resolved,purpose,paths):spec.append(dict(module=module,declared=declared,resolved=resolved,purpose=purpose,paths=paths))
libs=[p.name for p in (R/'server/build/install/server/lib').glob('*.jar')]
tech('공통 빌드','Kotlin plugins2.2.10 / Gradle wrapper8.14.3 / JVM17','배포 kotlin-stdlib2.2.10: '+str(any('kotlin-stdlib-2.2.10' in x for x in libs))+'; 현재 Gradle daemon 버전 UNKNOWN','루트 shared/server/web. Android 별도 settings와 shared-jvm.jar 파일 의존.',['build.gradle.kts','settings.gradle.kts','gradle/wrapper/gradle-wrapper.properties','androidApp/settings.gradle.kts'])
tech('서버','Kotlin/JVM2.2.10 · JDK17 toolchain · JDK HttpServer · JSON1.9.0 · sqlite-jdbc3.50.3.0 · slf4j-nop2.0.17','실제 배포 직접 JAR: '+', '.join(x for x in libs if any(k in x for k in ['serialization-json','sqlite-jdbc','slf4j-nop'])),'application main memo.server.MainKt / installDist. loopback127.0.0.1:8080, JSON UTF-8 REST /api/v1. thread pool4. Ktor 없음.',['server/build.gradle.kts','server/src/main/kotlin/memo/server/Main.kt'])
tech('DB','SQLite / Xerial JDBC3.50.3.0 / user_version1','실행 중 JDBC SQLite 엔진 버전 UNKNOWN (Python 엔진과 구분)','MEMO_DB; WAL; busy_timeout10000; BEGIN IMMEDIATE; UNIQUE attempt_id; prepared statements; COMMIT 후 응답; 미지원 스키마 거부.',['server/src/main/kotlin/memo/server/MemoStore.kt','docs/api-contract.md','.harness/v1/html-report-runtime.json'])
tech('Android','AGP8.10.0 · Kotlin2.2.10 · compile/targetSdk35 · minSdk26 · Java17 · versionCode1/name1.0 · JSON1.9.0','직접 의존 해석 그래프 UNKNOWN; 실제 APK/계측은 API36 (compileSdk35와 구분)','기본 View UI, HttpURLConnection, SharedPreferences.commit 저장 시도, 공유 JVM JAR. 공유 UI/Compose 없음. 시험 runner1.6.2/core1.6.1/ext:junit1.2.1.',['androidApp/build.gradle.kts','androidApp/src/main/AndroidManifest.xml',codes['Android'],M['android']['summary']])
tech('iOS','deployment16.0 · Swift language mode5.0 · arm64 · SwiftUI/Foundation/UIKit · static Shared','설치 Swift6.3.3 / Xcode26.6; 실제 iOS26.5 Simulator. 언어 모드와 컴파일러 버전 구분','URLSession, Swift Codable DTO. 실제 저장은 Application Support/memo-v1/pending.json atomic+fsync. 기술 메모의 UserDefaults 설명은 현 코드와 불일치.',['iosApp/Memo.xcodeproj/project.pbxproj','iosApp/build-shared.sh',codes['iOS']])
tech('웹','Kotlin/JS2.2.10 IR browser executable memo.js · DOM API compat2.2.10 · JSON1.9.0','번들 SHA 대조. 실제 node_modules webpack5.100.2 / webpack-cli6.0.1 / dev-server4.15.2 확인. Node 실행 버전 UNKNOWN. ECMA 명시 타깃 UNKNOWN','직접 DOM, fetch, localStorage 저장 시도, navigator.locks로 탭 간 저장 직렬화, 동일 origin API. 공유 UI/React/Compose 없음. CSS 시안 재사용.',['web/build.gradle.kts',codes['웹'],'web/src/jsMain/resources/product.css'])
tech('공유 KMP','JVM17 / JS IR library / iosArm64·iosX64·iosSimulatorArm64 static Shared','JVM 벡터 실행/실제 플랫폼 빌드 근거는 별도. iosX64 실행 UNKNOWN','BodyPolicy/Unicode16, API DTO, SaveMachine/AttemptStore 공유. UI·HTTP·플랫폼 저장은 개별. Swift는 자체 Codable DTO 사용.',['shared/build.gradle.kts','shared/src/commonMain/kotlin/memo/domain/BodyPolicy.kt','shared/src/commonMain/kotlin/memo/api/Contract.kt','shared/src/commonMain/kotlin/memo/client/SaveMachine.kt'])
tech('검증 도구','Kotlin test/JUnit · Android Instrumentation · XCTest/XCUITest/AX audit · Chrome UI · Python 장애 프록시','각 summary/XML/xcresult 요약과 원본 해시 대조. 사용자 발견은 디자인 검토 개입이며 전체 사용자 인수 PASS 아님.','자동 시험/에이전트 실제 UI 검토/사용자 확인을 구분. 전이 의존성 전체 나열 안 함.',['server/src/test/kotlin/memo/server/ServerTest.kt','androidApp/src/androidTest/kotlin/memo/android/AcceptanceTest.kt','iosApp/MemoUITests.swift','server/tools/acceptance_fixture.py','docs/design-conformance.md'])
def svg(title,nodes,edges,height=470):
 s=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 {height}" role="img" aria-label="{e(title)}"><defs><marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3z" fill="#527466"/></marker></defs><rect width="100%" height="100%" fill="#f4f8f3"/>']
 for x1,y1,x2,y2,label,dashed in edges:s.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#527466" stroke-width="2" fill="none" marker-end="url(#arr)"'+(' stroke-dasharray="7,5"' if dashed else '')+f'/><text x="{(x1+x2)/2}" y="{(y1+y2)/2-10}" font-size="13" text-anchor="middle" fill="#294739">{e(label)}</text>')
 for x,y,w,hh,title_,sub in nodes:s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{hh}" rx="12" fill="white" stroke="#9ab3a2"/><text x="{x+w/2}" y="{y+28}" font-size="17" text-anchor="middle" fill="#243c34">{e(title_)}</text><text x="{x+w/2}" y="{y+53}" font-size="12" text-anchor="middle" fill="#53665c">{e(sub)}</text>')
 return ''.join(s)+'</svg>'
diagrams={
'component':('구성도 · 실선 빌드 의존 / 점선 런타임',svg('구성도',[(20,20,250,75,'Android · View UI','HTTP / SharedPreferences'),(425,20,250,75,'iOS · SwiftUI','URLSession / pending.json'),(830,20,250,75,'웹 · DOM UI','fetch / localStorage'),(360,210,380,75,'KMP shared · UI 공유 없음','BodyPolicy / Unicode16 / DTO / SaveMachine'),(360,370,380,75,'서버 · Kotlin/JVM HttpServer','route / JSON / MemoStore'),(830,370,250,75,'SQLite 파일','memos · attempt_id UNIQUE')],[(145,95,360,220,'JVM JAR',False),(550,95,550,210,'static framework',False),(955,95,740,220,'JS library',False),(550,370,550,285,'JVM module',False),(145,95,360,400,'HTTP JSON',True),(675,55,740,395,'HTTP JSON',True),(955,95,740,430,'HTTP JSON',True),(740,410,830,410,'JDBC',True)])),
'flow':('저장 성공 실행 흐름',svg('저장 성공',[(20,20,290,75,'1 클라이언트 입력 검증','BodyPolicy / UUID / 정규화'),(400,20,290,75,'2 전송 전 시도 영속 보존','플랫폼 저장 → SaveMachine.begin'),(800,20,280,75,'3 POST /api/v1/memos','attemptId + body'),(800,180,280,85,'4 route → MemoStore.save','검증 → BEGIN IMMEDIATE → 키 조회'),(400,180,290,85,'5 기존 결과 또는 INSERT','같은 키/본문 재사용 · 충돌409'),(20,180,290,85,'6 COMMIT 후201/200','서버 ID / body / createdAt'),(20,350,360,80,'7 클라이언트 성공 처리','기록 정리 → ID merge → 작성 닫기'),(700,350,380,80,'8 GET /api/v1/memos','실패: 성공 유지 · 목록 GET만 재시도')],[(310,55,400,55,'유효',False),(690,55,800,55,'보존 성공',False),(940,95,940,180,'HTTP',False),(800,220,690,220,'트랜잭션',False),(400,220,310,220,'COMMIT',False),(165,265,165,350,'성공 응답',False),(380,390,700,390,'목록 재조회',False)])),
'recovery':('저장 결과 불확실 · 복구와 중복 방지',svg('저장 복구',[(20,20,390,80,'응답 유실 / 5xx / 파싱 실패 / 재진입','같은 pending 보존 · UNCERTAIN · 편집 잠금'),(600,20,480,80,'사용자가 같은 결과 다시 확인','SaveMachine.retry → GET /attempts/{UUID}'),(20,190,280,80,'200 기존 결과','성공 처리 · 기록 정리 · 목록 GET'),(410,190,280,80,'404 아직 없음','같은 키·본문 POST 재전송'),(800,190,280,80,'그 외 오류','불확실 유지 · 새 키 없음'),(390,350,350,80,'서버 원자 중복 방지','BEGIN IMMEDIATE + UNIQUE attempt_id')],[(410,60,600,60,'수동 재확인',False),(660,100,160,190,'200',False),(830,100,550,190,'404',False),(1000,100,940,190,'실패',False),(550,270,550,350,'동일 요청',False)]))}
diagrams['component']=('구성도① · 실선은 빌드 의존 방향',svg('모듈 의존 구성도',[(20,20,250,75,'Android · View UI','shared-jvm.jar 파일 의존'),(425,20,250,75,'iOS · SwiftUI','static Shared framework'),(830,20,250,75,'웹 · DOM UI','Kotlin/JS project shared'),(360,210,380,75,'KMP shared · UI 공유 없음','BodyPolicy / Unicode16 / DTO / SaveMachine'),(360,370,380,75,'서버 · Kotlin/JVM','project shared 의존')],[(145,95,360,220,'JVM JAR',False),(550,95,550,210,'static framework',False),(955,95,740,220,'JS library',False),(550,370,550,285,'JVM module',False)]))
diagrams['runtime']=('구성도② · 점선은 런타임 통신',svg('런타임 통신 구성도',[(20,20,250,75,'Android','HttpURLConnection'),(425,20,250,75,'iOS','URLSession'),(830,20,250,75,'웹','fetch / 동일 origin'),(360,210,380,75,'서버 · HttpServer → MemoStore','127.0.0.1:8080 /api/v1 JSON'),(360,370,380,75,'SQLite · memos','DB 파일 / UNIQUE attempt_id')],[(145,95,390,210,'HTTP JSON',True),(550,95,550,210,'HTTP JSON',True),(955,95,710,210,'HTTP JSON',True),(550,285,550,370,'JDBC',True)]))
diagrams={k:diagrams[k] for k in ['component','runtime','flow','recovery']}
for name,(title,content) in diagrams.items():(O/(name+'.svg')).write_text(content)
gallery=[]
for state in ['empty-create','empty-invalid','input','invalid','saving','failed','uncertain','list','empty-list']:
 figs=[]
 for p,label in [('baseline','승인 입력 시안'),('android','Android · API36'),('ios','iOS26.5 Simulator'),('web','웹 · Chrome')]:
  src=f'.harness/v1/design-conformance/{p}/{state}.png'; info=M['captures'].get(src,{})
  if (R/src).is_file():
   dest=f'captures/{p}/{state}.png'; (O/dest).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/src,O/dest)
   valid=h(src)==info.get('sha256') and info.get('use_for_verdict',False)
   figs.append(f'<figure><figcaption>{label} · {state} · {badge("PASS" if valid else "UNKNOWN")}</figcaption><a target=_blank href="{dest}"><img loading=lazy src="{dest}" alt="{label} {state}"></a></figure>')
  else:issues.append(dict(path=src,issue='MISSING'));figs.append('<b class=warn>캡처 누락 '+e(src)+'</b>')
 gallery.append('<details><summary>'+state+' · 시안 / 실제 세 플랫폼</summary><div class=shots>'+''.join(figs)+'</div></details>')
cards=[]
rank={'FAIL':0,'BLOCKED':1,'NOT_RUN':2,'UNKNOWN':3,'재검증 필요':4,'PASS':5}
for r in sorted(rows,key=lambda r:(r['required']!='기존 필수',rank.get(r['status'],9),r['id'])):
 content='<p>원본 REQ: '+e(r['req'])+' · '+link(r['reqpath'])+'<br>디자인: '+e(r['design'])+' · '+link(r['designpath'])+'</p>'
 content+='<div class=versus><section><h4>기대 결과 · 원본 기준</h4><p>'+e(r['expected'])+'</p></section><section><h4>실제 결과 · 범위 한정</h4><p>'+e(r['actual'])+'</p></section></div>'
 content+=detail('사전 조건·환경·입력·절차·판정',r['env']+'\n입력/실행: '+r['steps']+'\n판정: 원본 기대 결과의 해당 분기를 모두 충족. 부분 결과는 해당 범위만 인정.\n명령: '+r['command'])
 content+='<details><summary>코드 기준·입력 baseline·실행 ID·시점·유효성</summary>'+link(r['code'])+'<p>현재 SHA '+str(h(r['code']))+'<br>baseline '+B['baseline_id']+'<br>업무 영역 business-reuse 및 최신 SHA 대조. iOS 목록 오류 색상 한 줄은 집중 재시험. 개별 시각·검사명은 아래 summary/XML 참조; 실행 전체 시각을 개별 시각으로 대신하지 않음.</p>'+detail('원장 실행 기록',runs(r['task']))+'</details>'
 content+='<details><summary>결과·캡처·로그 근거</summary>'+'<br>'.join(link(p) for p in r['evidence'])+'<p>DB·원본 세션 로그·개인 설정은 제공하지 않습니다.</p></details>'
 cards.append('<article class=case data-platform="'+e(r['platform'])+'" data-status="'+e(r['status'])+'" data-required="'+e(r['required'])+'"><header><b>'+e(r['id'])+'</b> '+badge(r['status'])+'<small>'+e(r['platform']+' · '+r['required']+' · '+r['method'])+'</small></header>'+content+'</article>')
techhtml=''
for s in spec:techhtml+='<article><h3>'+e(s['module'])+'</h3><p><b>프로젝트 선언·요구 환경</b> '+e(s['declared'])+'</p><p><b>실제 해석·관측</b> '+e(s['resolved'])+'</p><p>'+e(s['purpose'])+'</p><details><summary>근거 파일</summary>'+'<br>'.join(link(p) for p in s['paths'])+'</details></article>'
for p in ['build/js/packages/memo-mvp-web/package.json','web/build/js/packages/memo-mvp-web/package.json']:
 if (R/p).is_file():techhtml+='<details><summary>기존 웹 package 산출물</summary>'+link(p)+'</details>'
docs=['docs/product.md','docs/features/memo-list/requirements.md','docs/features/memo-create/requirements.md','docs/features/memo-list/design.md','docs/features/memo-create/design.md','docs/api-contract.md','docs/technical-decisions.md','docs/v1-acceptance-status.md','docs/design-conformance.md','docs/v1-readiness.md','docs/try-v1.md','docs/feedback.md','docs/retrospective.md','.harness/v1/design-conformance/manifest.json','.harness/v1/acceptance-final-manifest.json']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(); dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True));now=datetime.datetime.now(datetime.timezone.utc).isoformat()
meta=dict(feature='MEMO-MVP v1',input_baseline=B['baseline_id'],product_head=head,code='WORKING_TREE / dirty='+str(dirty),harness='v0.2.0 / '+M['harness']['commit'],generated_at=now,scope='기존 명세/증거/현 코드 조사. 제품 전체 시험 재실행 없음. 현재 설치 환경은 별도 관측 시각.')
counts=dict(collections.Counter(r['status'] for r in rows if r['required']=='기존 필수'));unique={r['condition'] for r in rows if r['condition'].startswith(('FEAT-','V1-NAV','V1-RECOVERY'))};reqids=set(re.findall(r'[LC]-REQ-\d+',' '.join(r['req'] for r in rows)))
overview='<div class=notice><b>v1 전체 인수: '+e(T['V1-INTEGRATION']['state'])+'</b><br>기능·디자인 범위별 PASS와 전체 필수 인수는 구분합니다. 실제 보조기술·남은 탐색·변경 후 레이아웃 근거가 완결되지 않았습니다.</div><article><h2>현재 남은 일</h2><ul><li>실제 TalkBack·VoiceOver·웹 스크린리더: NOT_RUN</li><li>남은 제스처/탐색의 상세 조합 명세와 실행 근거 연결 부족</li><li>기존 실제 Chrome200% 이후 표시 변경: 최신 영향 재확인 필요</li><li>일부 개별 원본 근거 경로 누락·유효성은 아래 근거 검사에서 공개</li></ul><p>현재 정책의 추가 사용자 선택은 없습니다. 추가 OS/실기기/브라우저 매트릭스는 제안이며 승인 전 필수화하지 않습니다.</p></article>'
overview+=f'<article><h2>집계 범위</h2><p>보고서 항목 {len(rows)}개: 조건×대상 및 별도 UI/관측 항목. 기존 필수 상태 {e(counts)}.</p><p>원본 고유 인수 조건 {len(unique)}개(FEAT AC13 + NAV1 + RECOVERY1), 연결된 고유 REQ {len(reqids)}개. 이는 시험 실행 건수나 완료율이 아닙니다. 추가 제안·DB 단일 관측은 필수 집계에서 제외합니다.</p></article>'
overview+=f'<article><h2>실제8080·SQLite 단일 시점 관측</h2><p>직전 조회2026-10-21T03:02:03Z 및 후속 {e(D["at"])} · PID{D["pid"]} · {D["count"]}건 · schema v{D["schema_version"]}</p><code>{e(D["database"])}</code><p>실행 환경 MEMO_DB / cwd / 배포 JAR와 SQLite database_list 경로 일치. 조회 순간 서버 DB FD는 유지되지 않아 열린 DB 파일 자체는 lsof로 확인하지 못함. 요청별 연결을 닫는 실제 코드와 대조했습니다.</p><p>mode=ro + query_only 단일 읽기 트랜잭션. DB 원본·전체 메모 본문·시도 키는 미포함. 이 관측을 모든 클라이언트 저장/재시작/중복 방지 증명으로 확대하지 않습니다.</p>'+link('.harness/v1/html-report-runtime.json')+'</article>'
overview+='<article><h2>원본과 수동 재생성</h2><p>HTML은 파생 보고서입니다. 상태 원본은 기존 .harness/tasks/tasks.yaml. 별도 상태 원장이나 자동 갱신은 없습니다. DB 관측은 저장된 시점의 근거이며 생성 명령은 DB를 다시 조회하지 않습니다.</p><pre>rtk proxy python3 tools/v1-report/generate.py\nrtk proxy python3 tools/v1-report/serve.py --port 8773</pre><p><a href="task-executions.json">기존 원장 작업·실행 추출</a> · <a href="provenance.json">현재 해시 및 근거/링크 검사</a></p><div class=sources>'+'<br>'.join(link(p) for p in docs)+'</div></article>'
arch='<h2>현재 구현의 구성과 실제 호출 순서</h2><p>실선은 빌드 의존, 점선은 런타임 통신. 플랫폼 UI·HTTP·저장은 별도이며 순수 정책/상태만 공유합니다. 코드에 없는 Repository/UseCase/DI 프레임워크 계층은 추가하지 않았습니다.</p>'
for name,(title,content) in diagrams.items():arch+='<article><h3>'+title+'</h3><button class=zoom>확대 / 원래 크기</button> <a target=_blank href="'+name+'.svg">SVG 원본</a><div class=diagram>'+content+'</div></article>'
arch+='<article><h3>노드 역할과 핵심 설계</h3><p>클라이언트는 입력·전송 전 시도 보존·잠금·성공 후 기록 정리/ID 병합/목록 재조회를 담당합니다. 서버는 최종 검증·시각/ID 생성·정렬·원자 저장을 담당합니다. DB는 시도 키와 본문을 같은 행에 보관합니다.</p><p>422/413은 확실한 미저장으로 본문 유지/잠금 해제. 409·전송/5xx/파싱 실패는 불확실 유지. pending 보존 실패 시 전송 금지, 성공 뒤 정리 실패 시 같은 키 잠금 유지. 재진입은 pending 복원 후 수동 재확인. 일반 초안은 영속 보관하지 않습니다.</p>'+'<br>'.join(link(p) for p in list(codes.values())+['server/src/main/kotlin/memo/server/Main.kt','docs/api-contract.md'])+'</article>'
filters=''
for id_,label,vals in [('platform','플랫폼',sorted({r['platform'] for r in rows})),('status','상태',['PASS','FAIL','NOT_RUN','BLOCKED','UNKNOWN','재검증 필요']),('required','필수 여부',['기존 필수','추가 제안','관측 근거'])]:filters+='<label>'+label+' <select id="'+id_+'"><option value="">전체</option>'+''.join('<option>'+e(v)+'</option>' for v in vals)+'</select></label>'
css='''*{box-sizing:border-box}body{margin:0;background:#f4f6f2;color:#243c34;font:15px/1.65 system-ui}main,body>header,nav{max-width:1320px;margin:auto;padding:22px}h1{font-size:32px;margin:8px 0}h2{margin:10px 0 18px}h3,h4{margin:8px 0}.eyebrow{letter-spacing:.16em;font-size:12px}.meta{font:12px/1.6 monospace;overflow-wrap:anywhere;color:#52665c}nav{position:sticky;top:0;z-index:2;background:#f4f6f2f5;display:flex;gap:8px;flex-wrap:wrap;padding-top:10px;padding-bottom:10px}button,select{font:inherit;border:1px solid #acbeb1;border-radius:9px;padding:10px 18px;background:white;color:#243c34;cursor:pointer}button[aria-selected=true]{background:#285d49;color:white}a{color:#205a8a;overflow-wrap:anywhere}article{background:white;border:1px solid #d9e1d8;border-radius:16px;padding:22px;margin-bottom:18px}.notice{background:#fff5db;border-left:5px solid #966b23;padding:18px;margin-bottom:18px}.badge{display:inline-block;padding:3px 9px;border-radius:6px;background:#ece6f4;font:600 12px/1.6 system-ui}.pass{background:#def0df;color:#175330}.warn{color:#8d3426;background:#fff0d5}.unknown{color:#624683}.versus{display:grid;grid-template-columns:1fr 1fr;gap:14px}.versus section{padding:16px;border-radius:10px;background:#f5f7f3}.versus section+section{background:#edf3f2}small{display:block;color:#5f6e66;margin-top:5px}summary{cursor:pointer;padding:10px 0;font-weight:600}details{border-top:1px solid #e5e9e3;margin-top:10px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.65 monospace;background:#f1f4f0;padding:16px;border-radius:8px;max-height:540px;overflow:auto}.filters,.legend{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px}.shots{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}figure{margin:0;min-width:0}img{width:100%;height:auto;border:1px solid #d8ded6;border-radius:8px}figcaption{font-size:12px;margin-bottom:8px}.diagram{overflow:auto;background:#f4f8f3;border:1px solid #d8e1d5;border-radius:12px}.diagram svg{display:block;width:100%;min-width:850px;height:auto}.diagram.big svg{width:160%;max-width:none}[hidden]{display:none!important}.sources{columns:2}footer{padding:20px;color:#5f6e66}button:focus-visible,select:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #3c79a0;outline-offset:3px}@media(max-width:700px){main,body>header,nav{padding:14px}.versus{grid-template-columns:1fr}.shots{grid-template-columns:repeat(2,minmax(0,1fr))}.sources{columns:1}h1{font-size:26px}article{padding:16px}select{max-width:100%}}'''
tabs=[('overview','개요'),('validation','검증 현황'),('spec','기술 스펙'),('architecture','아키텍처')]
body='<!doctype html><html lang=ko><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>MEMO v1 · 검증과 구조 보고서</title><style>'+css+'</style><header><div class=eyebrow>MEMO MVP / LOCAL REVIEW</div><h1>메모 v1 · 검증과 아키텍처</h1><div class=meta>'+'<br>'.join(e(k)+': '+e(v) for k,v in meta.items())+'</div></header><nav role=tablist aria-label="보고서 탭">'+''.join('<button role=tab aria-selected="'+('true' if i==0 else 'false')+'" aria-controls="'+id_+'">'+name+'</button>' for i,(id_,name) in enumerate(tabs))+'</nav><main><section role=tabpanel id=overview>'+overview+'</section><section role=tabpanel id=validation hidden><h2>검증 명세와 실제 결과</h2><div class=legend>'+''.join(badge(s) for s in ['PASS','FAIL','NOT_RUN','BLOCKED','UNKNOWN','재검증 필요'])+'</div><p>필수 실패·미완료 우선. 추가 제안은 뒤에 분리. A11Y/NAV/DESIGN 표시용 ID는 기존 문서 항목을 연결하며 새 필수 요구를 만들지 않습니다.</p><div class=filters>'+filters+'</div><p id=shown aria-live=polite></p>'+''.join(cards)+'<h2>승인 입력 시안 / 실제 플랫폼 캡처</h2><p>채택 기준은 baseline의 최신 D0.4-WEB 및 실제 공용 CSS/JS. 이전 문서 머리말의 IN_PROGRESS/NOT_RUN은 당시 이력으로 보존하며 최신 검토 원장을 함께 읽습니다. 캡처는 격리 시험의9개 상태이며 사용자 DB 화면은 새로 복사하지 않았습니다. 단위/글꼴 차이가 있어 픽셀 일치를 주장하지 않습니다.</p>'+''.join(gallery)+'</section><section role=tabpanel id=spec hidden><h2>기술 스펙 · 선언과 관측</h2>'+techhtml+detail('현재 설치 환경 · 별도 관측 시점 '+D['at'],D['installed'])+detail('소스·바이너리·입력 유효성 대조',checks)+'</section><section role=tabpanel id=architecture hidden>'+arch+'</section><footer>파생 보고서 · 로컬 전용 · 제품/하네스 변경·전체 회귀·커밋·배포 없음</footer></main><script>const tabs=[...document.querySelectorAll("[role=tab]")];tabs.forEach(t=>t.onclick=()=>{tabs.forEach(x=>{const a=x===t;x.setAttribute("aria-selected",a);document.getElementById(x.getAttribute("aria-controls")).hidden=!a});history.replaceState(null,"","#"+t.getAttribute("aria-controls"))});function filter(){let n=0;document.querySelectorAll(".case").forEach(c=>{c.hidden=["platform","status","required"].some(k=>document.getElementById(k).value&&c.dataset[k]!==document.getElementById(k).value);if(!c.hidden)n++});document.getElementById("shown").textContent=n+"개 표시 / 전체 "+document.querySelectorAll(".case").length+"개"}document.querySelectorAll("select").forEach(s=>s.onchange=filter);filter();document.querySelectorAll(".zoom").forEach(b=>b.onclick=()=>b.parentElement.querySelector(".diagram").classList.toggle("big"));const start=tabs.find(t=>"#"+t.getAttribute("aria-controls")===location.hash);if(start)start.click();</script></html>'
body=body.replace('</style>','code{overflow-wrap:anywhere}</style>')
body=body.replace('<a href="task-executions.json">','<a href="ui-verification.json">보고서 실제 브라우저·HTTP 표시 검증</a> · <a href="task-executions.json">')
(O/'index.html').write_text(body)
refs=re.findall(r'(?:href|src)="([^"]+)"',body)
for ref in refs:
 if ref.startswith(('#','http:','https:')):continue
 f=(O/ref.split('#')[0]).resolve()
 if ref!='provenance.json' and (not f.is_relative_to(O.resolve()) or not f.is_file()):issues.append(dict(path=ref,issue='BROKEN_LINK'))
(O/'provenance.json').write_text(json.dumps(dict(generated_at=now,metadata=meta,source_sha256=sources,code_input_binary_checks=checks,issues=issues,local_link_count=len(refs),manual_regeneration=True,product_test_rerun=False,state_source='.harness/tasks/tasks.yaml'),ensure_ascii=False,indent=2))
# Issues are visible on the first screen; absence is a measured result, not hidden.
msg='<article><h2>근거 누락·링크 검사</h2><p>'+('누락/깨진 링크 '+str(len(issues))+'건' if issues else '생성된 상대 링크 대상 존재 확인: '+str(len(refs))+'개. 누락0건. 실제 브라우저 동작 확인은 별도 기록.')+'</p>'+detail('검사 상세',issues)+'</article>'
(O/'index.html').write_text(body.replace('<section role=tabpanel id=overview>','<section role=tabpanel id=overview>'+msg))
print(json.dumps(dict(report=str(O/'index.html'),items=len(rows),unique_acceptance_ids=len(unique),unique_REQs=len(reqids),required_status=counts,issues=issues,latest_match=latest_ok,server_shared_match=server_ok),ensure_ascii=False,indent=2))
