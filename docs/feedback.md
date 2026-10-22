# 데모 피드백

현재 기술·구조 합의 이탈은 [FB-004](#fb-004)에 기록했다. 아래 초기 안내의 “아직 실제 제품 결함 기록은 없다”는 문서는 생성 당시 이력이다.

확인 당시 기존 피드백 위치가 없어 이 단일 Markdown 문서를 초기 기록 위치로 둔다. 실행 상태 원본은 기존 YAML이며 새로운 상태 시스템은 만들지 않는다.
처리 기준은 [하네스 작업 관리](../.kmp-agent/releases/b802d18b068d4a213946a0c7f3b5dee77b6c6621/docs/task-management.md#demo-feedback)를 따른다. 아직 실제 제품 결함 기록은 없다.

## 기록 항목
새 발견마다 고유 피드백 ID와 다음을 기록한다. UNKNOWN·N/A에는 근거를 남긴다.

- 원본 작업 ID·실행 ID·제품 기준 버전:
- 기대 결과 / 실제 결과:
- 재현 조건·증거 위치:
- 영향 단계·담당:
- 사용 하네스 커밋·dirty 여부·파일 해시/변경 근거:
- 분류(제품 전용 / 공통 결함 / 미분류)·근거:
- 관련 데모 작업·하네스 개선 작업·저장소별 PR(없으면 작업 ID):
- 수정된 하네스 버전·제품 버전:
- 영향 단계 재검증 PASS / FAIL / NOT_RUN·증거:
- 발견→분류→개선→재검증→해결 과정·남은 차단:

<a id="fb-001"></a>

## FB-001 — 디자인 시각 검토용 브라우저 미연결
- 원본: 데모 저장소 TASK-003/004, 실행 e47aead8-6431-4856-8dfe-263d74a20489; 제품 입력 0f1851a1b237dd41781fc97bb22d1b364ea66238.
- 기대: 실제 브라우저 렌더링·이동·상태·잘림·겹침·스크롤·버튼 접근 검토. 실제: iab unavailable, 사용 가능 목록 [].
- 재현·증거: [검토 보고 BROWSER-001](design/review.md#browser-001-환경-근거), 기존 로그의 원본 도구 응답 참조. 스크린샷 없음(미실행).
- 영향·담당: 시안 동작 확인·시각 검토·최종 UI 인계 차단 / 디자인·검증 담당.
- 하네스: 0a212803cd240b9ab66a11e0e406767e18e34152, task-management.md·retrospective.md dirty. 사용 해시·diff는 Git 제외 .harness/design/baseline.json 및 인접 파일.
- 분류: 미분류(환경 차단). 브라우저 미연결의 원인이 공통 하네스 결함이라는 근거 없음. 개선 작업 미등록·하네스 수정 없음.
- 수정 버전·PR: N/A, 수정하지 않았고 PR 미생성(요청 제외). 명세/시안 D0.1 미커밋.
- 재검증: NOT_RUN, 브라우저 연결 후 재검토 필요. 발견·잠정 분류 기록, 해결 미선언. 무관한 기획 검토 PASS 유지.

<a id="fb-002"></a>

## FB-002 — 데모 세션 원문 자동 수집 적용 누락
- 원본: 디자인 세션 01a134f9-20d2-79b1-b119-251857516530, 메시지 msg_01a13ee2-443b-79e1-912d-58119d57638b(2026-10-15T09:26:18.427Z). 관련 제품 TASK-003/004는 있으나 이 질문의 task_id·agent_run_id는 UNKNOWN이며 추정 귀속하지 않는다.
- 기대/실제·영향: 로거를 별도 지시하지 않은 질문의 자동 수집을 기대했으나 데모 events.jsonl에 원문이 없고 마지막 수집은 2026-10-13T13:29:02.090544+00:00이었다. 원문·개입 연결 확인이 차단됐다.
- 근거·분류: [하네스 적용 조사](../../kmp_agent/.harness/logs/demo-hook-application.json), 원본 세션 497행. 데모 .codex/hooks.json 부재, 데모 훅 신뢰 항목·호출 진단 부재, 공용 스크립트의 하네스 루트 전용 검사를 확인했다. 공통 수집 경로의 적용·구현 결함이며 제품 정책 문제는 아니다. 기존 세션의 메모리 내 로드 상태는 UNKNOWN.
- 개선 연결: 하네스 FEAT-003 / TASK-009, 실행 eb283cb4-6e0f-4111-b6f6-5a194d1dbc86. 원인·대응은 [RETRO-H006](../../kmp_agent/docs/retrospective.md#retro-h006--하네스-훅-검증이-데모-적용을-보장하지-않음) 참조. 하네스 0a212803cd240b9ab66a11e0e406767e18e34152 + dirty 변경(사용 파일 SHA-256은 적용 조사), 제품 기준 0f1851a1b237dd41781fc97bb22d1b364ea66238 + 기존 dirty 변경 보존. PR·새 커밋 없음.
- 대응·재검증: 데모별 참조 훅 설정·Git 제외·진입 지침과 공용 스크립트의 저장 대상을 수정했다. 내부 합성 테스트 34개 PASS. 신뢰 적용 뒤 기존 디자인 세션의 새 요청은 미호출·미수집 FAIL, 새 CLI 세션 01a13efb-a937-7511-ace2-5d30203ed839에서는 일반 질문이 Stop 훅으로 자동 수집 PASS다. 실제 메시지 msg_01a13efb-f06c-7721-a084-4bc167309cf0 → [데모 로그 1844행](../.harness/logs/events.jsonl#L1844) 이벤트 d9d85caf-63da-4e65-99bf-7354cedc7014가 정확히 1건이며 두 훅 종료 코드 0이다. 근거는 [진단 로그](../.harness/logs/hook-diagnostics.jsonl)와 적용 조사 파일에 연결했다. 수동 sync·로거 호출 없이 검증했다. 새 CLI 실행 경로의 적용 누락은 해결됐고 기존 vscode 세션의 미호출 원인은 UNKNOWN으로 남긴다. 제품 작업·원본 로그·작업 귀속을 소급 수정하지 않았다.


## FB-003 — 실제 플랫폼 화면과 승인 디자인의 차이

2026-10-21 사용자 직접 발견. 기능 시험 PASS와 별개로 Android·iOS·웹의 버튼 배치·입력/카운터·토큰·상태 표현 누락을 확인했다. 요구 변경이 아닌 CORRECTION이며 V1-DESIGN-CONFORMANCE / `a2ab2bff-c8c4-47cf-8437-7f30196e940d`에 연결한다. 실제 원문/source event/개입 event는 `.harness/v1/design-conformance/intervention-resolved.json`, 판정과 실제 캡처·재검증은 [디자인 적합성](design-conformance.md), 시행착오는 [RETRO-007](retrospective.md#retro-007--기능-검증과-디자인-적합성-검증의-누락) 참조. 기존 입력 디자인 검토 PASS를 최신 구현의 시각 PASS로 승계하지 않는다. 설치된 공통 하네스는 수정하지 않는다.

<a id="fb-004"></a>

## FB-004 — UI·서버·모듈 합의 이탈과 승인 근거 혼동

- 발견: 2026-10-21 사용자 직접 개입, **CORRECTION**. 새 UI/Ktor 요구 추가로 집계하지 않는다. 원본 합의·위임·재확인과 코드 대조는 [합의 검토](agreement-review.md).
- 기대/실제: Compose Multiplatform Android/iOS, Ktor, 공통/전용 domain/data/presentation 구조가 목표. 실제 Android View·SwiftUI·JDK HttpServer·축약 모듈. SQLite 선택은 호환 최소안 위임 근거가 있어 별도이며 사용 자체를 결함으로 확정하지 않는다.
- 근거: E-01 사용자 이벤트 `af79796c-a904-449b-8d69-f1fe47d876a8`, SRC-004/005 및 현재 사용자 재확인. 에이전트 technical-decisions/project-settings·planning PASS를 사용자 변경 승인으로 취급할 수 없다.
- 연결: MEMO-MVP / V1-AGREEMENT-REVIEW, 원본 관련 작업 V1-BASELINE·V1-SHARED·V1-SERVER·V1-ANDROID·V1-IOS·V1-WEB·V1-INTEGRATION. 새 실행 ID는 `.harness/v1/agreement-review/work.json`, 시작 코드/입력 해시는 `start.json`에 연결. 네이티브 원문 session/turn/message ID는 `.harness/v1/agreement-review/intervention.json`에 기록. 저장소 원문 이벤트 연결은 수집 전 UNKNOWN/PENDING으로 구분한다.
- 분류/영향: 제품의 합의 추적·계획/개발/검토 누락. 기존 구현 선택 이유와 기능 시험은 있으나 구조 이탈 승인·검출 근거가 부족했다. 설치 하네스 코드 자체의 결함으로 원인을 확정하지 않는다.
- 기준: 제품 HEAD `43c0b3eb9647161fc21f0c693e8f17ca51446d26` + dirty, 하네스 v0.2.0 `0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55`. 제품/DB/설치 하네스 변경 없음, PR/커밋/푸시/배포 없음.
- 대응: SRC-006 및 기술 문서 정정, 기존 보고서를 보존한 간소화 대조 HTML, 후속 수정 계획만 작성. 구조 수정 구현·전환 후 재검증은 **NOT_RUN**. 기능 PASS·과거 디자인 PASS·기존 baseline은 당시 범위로 유지하며 새 합의 적합성에 승계하지 않는다. **미해결**; 웹 UI 적용 범위만 사용자 선택 필요.


<a id="fb-005"></a>

## FB-005 — 미저장 뒤로가기 확인창 상태 비교 누락

2026-10-21 사용자 직접 발견, CORRECTION. 시안의 C-DISCARD-CONFIRM은 존재하지만 최초 상세 보고서의9개 상태 비교와 디자인 manifest의 승인 시안/Android/iOS/웹 캡처 목록에 없다. Android orderInitialFailureBoundariesAndBack의 계속 작성·버리기 기능 PASS는 확인했으나, 그것은 확인창의 세 플랫폼 시각·문구·버튼·포커스 비교 증거가 아니다. 해당 비교는 NOT_RUN/근거 없음으로 정정한다. 기존 시안·시험 결과·첫 HTML/ZIP은 보존하며 제품 구현은 변경하지 않는다. docs/design-conformance.md 범위 정정과 개편 보고서 첫 화면에 누락을 노출한다. 새 정책/사용자 결정이 필요한 것이 아니라 기존 디자인의 검증 누락이다. 현재 사용자 원문 이벤트 연결은 UNKNOWN이며 수집 성공을 추정하지 않는다.


<a id="fb-006"></a>

## FB-006 — 문서 정정 후 승인 설정·동결 실행 기준을 남겨둔 누락

2026-10-21 사용자 직접 발견(CORRECTION / SRC-007). SRC-006 보고서는 기술 이탈을 확인했지만 project-settings.json의 ui/server CONFIRMED 값과 기존 태스크의 stage snapshot은 정정하지 않았다. 설정 파일만 바꾸어도 configure_stage의 불변 입력은 자동 갱신되지 않는 경로를 확인했다. 현재 승인 목표와 관측 구현을 분리하고, 과거 설정/baseline/원장/helper를 settings-correction/history에 보존했다. 현재 baseline은 정정 목표의 BLOCKED/전환 권한 없음으로 연결하고 CR-001로 과거 검토 유효성을 RECHECK_REQUIRED 표시했다. 리뷰 원문/실행/산출물은 유지하며 별도의 현재 입력 태스크6개를 TODO/실행0으로 동결했다. 공식 프로젝트 실행/검토 선검사와 기존 helper의 낡은 입력 차단을 추가했다. 설치 하네스·제품/DB/빌드·과거 ZIP을 변경하지 않았다.

공식 원본/결과: docs/project-settings.json, docs/current-implementation.json, docs/target-architecture.md, docs/settings-alignment.md, docs/settings-alignment-result.md. 검증 근거/실행은 .harness/v1/settings-correction/ 및 V1-SETTINGS-ALIGNMENT에 연결한다. 정합성 PASS는 제품 준수 PASS가 아니며 CMP/Ktor/모듈 전환·필수 상태/기능 검증은 NOT_RUN, 전체v1 BLOCKED다. 이번 사용자 원문 이벤트/Stop 수집·사용량·비용은 확인 전 UNKNOWN이며 일반 기술 위임과 명시 합의를 혼동하지 않는다.
