# v0.2.0 이후 기존 작업 재개 점검 — 2026-10-20

> SRC-007: 현재 승인 목표는 project-settings.json/target-architecture.md, 실행 전 검사는 tools/project_workflow.py 및 settings-alignment.md를 따른다. 아래 명령·PASS·구현 설명은 기존 대체 구현의 관측/이력이며 목표 기술 준수 또는 전환 착수 허가가 아니다. 현재 목표 baseline은 BLOCKED다.

> SRC-006 합의 준수 정정(2026-10-21): 기능/디자인 시험 결과와 별개로 Compose Multiplatform Android/iOS·Ktor·전용 계층 합의와 실제 구현이 불일치한다. [합의 검토](agreement-review.md)가 현재 정정 근거이며 과거 PASS/DONE/ACTIVE는 당시 입력 이력으로 보존한다. 이번 정정 입력을 반영한 새 구현 baseline 승인이나 전환 후 검증은 수행하지 않았다.

근거: `.harness/upgrade-v0.2.0/preparation.md`, `continuation-before.json`, `continuation-audit.json`, `request-hook-check.json`과 기존 작업 원장. 제품 HEAD `0f1851a1b237dd41781fc97bb22d1b364ea66238`, dirty. 설치 하네스 `0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55`, clean. 사용 파일 SHA-256은 continuation-before.json에 고정했다. 현재 파일을 제품 HEAD에 커밋된 버전으로 표현하지 않는다.

## 이미 결정된 범위

[제품 지침](product.md)의 MEMO-MVP-R0.2-WEB(미커밋)을 재사용한다. Android·iOS·웹, KMP 활용, 공통 로컬 서버의 메모 목록·본문 작성·영속 저장·재시작 후 조회가 범위다. 로딩·빈 목록·오류·재시도와 저장 결과 불확실 상태를 포함한다. 로그인·수정·삭제·검색·오프라인 동기화·외부 배포는 제외한다.

D-001~004는 확정: 제목 없이 본문·개행 허용, 앞뒤 공백 제거 후 빈 값 거부·사용자가 보는 2,000자; 서버 생성 시각 최신순·동률 고정 순서; 영속 저장 확인 후 닫고 반환 메모 한 번 반영·목록 재조회 실패 별도 처리; 동일 시도 재시도 최대 한 건·본문 유지·불확실 시 편집 잠금, 독립 새 작성의 같은 본문 허용. 기존 AC 13개를 보존한다.

이 범위가 v1 후보 입력이지만 `feature_version=v1`과 확정 baseline은 UNKNOWN이다. 하네스 v0.2.0과 제품 피처 버전을 혼동하지 않는다. 기존 기획 v0.1 완료와 D0.4/D0.4-WEB 초안은 새 v1 완료가 아니다.

## 실제 모듈과 명령

제품 서버·공유 KMP·Android·iOS·웹 앱 모듈, Gradle/npm 등 빌드 정의와 제품 테스트는 저장소에서 발견되지 않았다. 채택 스택·제품 build/test argv는 UNKNOWN이다. 설치 하네스 코드와 테스트를 제품 모듈/검증으로 등록하지 않는다.

| 실제 산출물 | 추적 모듈 | 용도 |
| --- | --- | --- |
| docs/features/memo-list | memo-list-docs | 기존 목록 요구·명세·HTML 시안 |
| docs/features/memo-create | memo-create-docs | 기존 작성 요구·명세·HTML 시안 |
| docs/design | design-prototype | 공용 CSS/JS·시안 안내·검토 기록 |

사용 가능한 확인 명령은 `rtk proxy node --check docs/design/prototype.js`이며 이번 실행 exit 0. 이름 `prototype-syntax`, 유형 other로 등록했다. JavaScript 문법 검사이며 제품 테스트나 브라우저 검토가 아니다. 기존 문서의 `rtk proxy python3 -m http.server 8765 --bind 127.0.0.1 --directory docs`는 정적 시안 제공용이며 이번에 실행하지 않았다. 제품 서버로 등록하지 않는다. 제품 빌드·테스트 명령은 미등록으로 유지한다.

설정 원본 [sequential-settings.json](sequential-settings.json)을 init으로 `.harness/settings/sequential.json`에 반영했다. 설정 등록은 자동 명령 실행·제품 구현 완료를 뜻하지 않는다.

## 기존 작업과 산출물 연결

| 원장 작업 | 기존 상태 | 연결·한계 |
| --- | --- | --- |
| TASK-001 / FEAT-001 | DONE | 목록 기획 v0.1 이력; 현재 웹/피드백 변경 전체에 대한 PASS 아님 |
| TASK-002 / FEAT-002 | DONE | 작성 기획 v0.1 이력; 동일 한계 |
| TASK-003 / FEAT-001 | BLOCKED | TASK-001 의존; 디자인 명세·시안·검토 기록 보유, 필수 시각 검토 NOT_RUN |
| TASK-004 / FEAT-002 | BLOCKED | TASK-002 의존; 동일 차단 유지 |
| TASK-005 / FEAT-001 | DONE | 두 기능의 웹 범위 변경 문서·검토 연결; 제품 구현 완료 아님 |

실행 14건·검토 7건을 재사용한다. 원장 내 snapshot 참조 315개를 검사해 누락/해시 불일치 0개. 원장 task.outputs와 현재 파일 바이트 일치는 TASK-001 0/3, TASK-002 0/3, TASK-003 0/5, TASK-004 0/5, TASK-005 5/9다. 과거 snapshot은 유효하지만 이후 변경된 현재 산출물을 검증한 것으로 볼 수 없다. TASK-005의 현재 일치 5개는 제품 지침·로드맵·기획 검토·두 requirements다. 최신 디자인/CSS/JS는 재검토·새 실행 시작 시 새 입력 해시 연결이 필요하다. 과거 입력의 git_commit 필드만으로 현재 파일이 커밋돼 있다고 판단하지 않는다.

디자인 문서에는 D0.3-WEB/D0.4-WEB 및 과거 COMPLETE와 현재 IN_PROGRESS가 섞여 있다. 현재 웹 인계 완료는 선언하지 않는다. 원장 BLOCKED·시각 검토 NOT_RUN을 유지한다. 새 작업·실행을 생성하거나 기존 기준·출력·검토를 덮어쓰지 않았다.

피처 v1/baseline 연결은 UNKNOWN, usage_bindings 0건·작업별 model_usage/cost UNKNOWN이다. 새 collection-report는 `.harness/logs/sequential-coverage.json`이며 과거 누락을 소급 보충하지 않는다. 순서만으로 필수 의존·공유 자원을 추가하지 않았다.

## 결정이 필요한 사항

1. 현재 웹 포함 요구와 최신 디자인 중 v1으로 고정할 입력·명세/시안 버전 및 실제 역할 인계용 Git 기준. 현재 문서 간 디자인 버전 불일치를 정리하고 시각 검토할 기준 선택이 필요하다.
2. T-001~002: KMP 로직/UI 공유·담당 소유 범위, 플랫폼 UI·웹 기술·지원 브라우저, 로컬 서버 언어/프레임워크/영속 저장소.
3. T-003~005: API 목록/생성/동일 시도 확인·오류·정렬 동률 키, 글자 분할/공백/개행 정규화와 공통 검증 벡터, 중복 방지 키/보존/재진입 복구·잠금 해제 계약.
4. T-006 잔여: 최신 반응형 시안의 시각 검토·긴 본문 전체 확인 방식, 미저장 본문·불확실 시도의 브라우저 뒤로/앞으로·새로고침·직접 진입 정책.

핵심 업무 정책 재질문은 없다. 기술 제안·계약을 확정한 후 실제 생성된 모듈과 동작 확인된 빌드/테스트 명령을 등록한다. 구현 담당·환경·명령은 그때까지 UNKNOWN이다.

## 실제 자동 훅과 다음 턴 대조

정적 연결 PASS는 init 결과이며 runtime NOT_RUN/AWAITING_REQUEST와 구분한다. 이번 실제 UserPromptSubmit invocation `5db02323-04fa-43a1-a79a-47bc354b7dc1`, session `01a157f9-d976-7451-a32e-abeee71c5010`, turn `01a157f9-df92-7950-87e2-eeef1184fa75`를 확인했다. collector_ready exit 0, hook_exited exit 0, imported_events 2, duplicate_events 0. 이는 수집 자식 종료 관측이며 외부 Codex 실행기 자체 종료 상태는 UNKNOWN이다.

실제 요청 message ID는 `msg_01a157f9-eb44-7851-b47a-06ac17a8d97e`, 원본 rollout의 물리 10행/ordinal 9다. 훅 collection_finished는 06:22:38.835 UTC, 실제 요청 기록은 06:22:38.917 UTC로 뒤늦다. 점검 시 events.jsonl에는 환경 지침 메시지만 있고 실제 요청은 없다. 요청 source_key는 UNKNOWN, 원문 수집은 PENDING이며 자동 수집 전체 PASS로 표시하지 않는다. 점검 시 전체 중복 source_key 0개.

이번 응답 Stop은 PENDING_NEXT_TURN. 다음 턴에는 위 session/turn/message ID의 요청이 정확히 한 번 수집됐는지, 이번 최종 응답의 실제 message ID/source_key와 Stop invocation의 collector_ready/hook_exited/외부 종료 근거를 대조한다. 종료 근거가 없으면 UNKNOWN을 유지한다. 자동 훅을 직접 호출하거나 수동 sync로 성공 근거를 만들지 않았다. 기존 preparation.md·과거 진단·원장·원본 세션을 보존한다.

<a id="decision-review"></a>

## 2026-10-20 후속 대조 — 현재 판단

아래는 앞 절 점검 이후 새 근거이며 이전 시점 기록을 대체 삭제하지 않는다. SRC-004로 **KMP 기반 서버·Android/iOS 앱·웹 방향은 확정**됐다. 웹 KMP 여부 자체는 더 이상 질문이 아니다. KMP가 서버와 모든 UI를 한 코드로 공유한다는 뜻은 아니다. 구체적 타깃·UI·공유 범위·라이브러리는 미정이다. 최소안은 제안(PROPOSED)이며 사용자 답변이나 확정 기술 계약으로 기록하지 않는다.

### 직전 Stop 실제 대조

| 관측 | 결과 |
| --- | --- |
| Stop invocation | 187b0009-3d6e-47fa-add7-7508a03a5d23 |
| 시간(KST, 2026-10-20) | process_entered 15:24:58.113451 → hook_exited 15:24:58.624886 |
| 소요 시간 구분 | 수집 처리 0.078057초; collector_ready 경과 0.591489초; 감독 프로세스 경과 0.738503초. process_entered 이후 시각 차이 0.511435초와 경과 측정의 시작점은 다르므로 혼용하지 않음 |
| 종료 | collection_finished COMPLETED; collector_ready 0; hook_exited 0(자식 프로세스 종료 관측). 외부 Codex 실행기 자체 종료 상태 UNKNOWN |
| 자동 수집 | Stop 신규 59건, 중복 제외 0건; cursor 75848 → 707001 |
| 직전 실제 요청 | msg_01a157f9-eb44-7851-b47a-06ac17a8d97e / source_key 021b7ad747d395a810080939502010774e48a660cfbfb7cb8b2947b11c2f727e / 정확히 1건 |
| 직전 최종 응답 | msg_0ea5f058ca558817016ad709335b64819180314ffbcee282b0 / source_key c025ad2c55994df01b68d0a25df5bdfab875c0260764e234dcb3ebbad4f766c5 / 정확히 1건 |
| 수집 구간 대조 | 원본 요청 끝 byte 77322, 응답 끝 byte 705245는 해당 Stop의 (75848,707001] 구간 안. 원본 역할·메시지 ID·행·레코드 해시와 저장 이벤트를 대조 |
| 중복 | 전체 events.jsonl의 중복 source_key 0건. 다음 UserPromptSubmit도 신규 2건·중복 제외 0건이며 직전 요청/응답을 다시 저장하지 않음 |

즉 직전 요청·응답 자동 수집은 확인됐으며 정적 연결 PASS 이상의 실제 근거가 있다. 모든 훅·외부 실행기까지 포괄한 성공 선언은 하지 않는다. 상세: `.harness/upgrade-v0.2.0/previous-stop-verification.json`. 수동 sync·직접 hook 호출 없음. 이번 응답 Stop은 다시 다음 턴 확인 대상이다.

### 기존 결정으로 해소 가능

| 항목 | 유효 근거·해소 내용 | 구현·검증 차단 판단 |
| --- | --- | --- |
| 플랫폼·KMP 방향(T-001 일부) | SRC-003 세 플랫폼 + SRC-004 KMP 기반 서버·앱·웹 | 플랫폼 포함 여부 질문 해소; 구체 아키텍처/모듈 정의는 아래 기술 판단까지 차단 |
| 길이·빈 값·개행(T-004 일부) | D-001: 본문만, 공백 제거 후 1~2,000 사용자 인지 글자, 내부 개행 유지 | 핵심 정책 질문 해소; 정확한 공백·분할 계약과 AC-002 경계 검증은 미정 |
| 정렬·저장 성공·재시도(T-003/005 일부) | D-002~004: 서버 최신순·동률 고정, 영속 확인 후 닫기, 같은 시도 한 건, 별개 작성 허용, 불확실 편집 잠금 | 성공/불확실 의미 재질문 불필요; API·DB 원자성·재시작 복구 구현/검증은 계약까지 차단 |
| 긴 본문 전체 보기(T-006 일부) | 현재 memo-list/requirements.md와 두 design.md D0.4 사용자 피드백: 목록 3줄·저장 본문 유지·별도 상세/전체 보기 미추가 | readiness의 “전체 확인 방식 결정 필요”는 해소. 상세 화면 추가는 제안하지 않음. 3줄·확대·스크롤 실제 검증은 NOT_RUN |
| 최신 시안 방향(T-006 일부) | D0.4 후속 사용자 요청: 기존 두 index.html, 단일 반응형 UI, 화면/프레임 폭 선택 제거, 초과 현재 수치 빨간색, 두 하단 안내 제거 | 이전 별도 웹 진입점/고정 프레임/선택 UI로 회귀하지 않음. 레이아웃·키보드/포커스 검증은 미완료 |
| 화면 내 작성 취소 | C-DISCARD-CONFIRM·C-BACK: 본문 있으면 계속 작성/버리기 확인 | 내부 이동은 기존 설계로 충분. 새로고침·강제 종료 후 초안 복원은 별도 사용자 선택 |
| 기획/디자인 버전 표기 | 제품 요구는 R0.2-WEB + SRC-004, 기능 명세는 D0.4-WEB 초안, 실제 시안은 최신 D0.4 반응형 파일 | 임의 v1 완료 선언은 불가. 오래된 D0.3/D0.2·COMPLETE 표기는 역사로 한정; 새 baseline은 파일 해시로 식별 가능 |

### 기술적 판단으로 제안 가능

구체 라이브러리/버전 선택과 호환성 검증은 이번 범위에 포함하지 않았다. 아래는 기존 정책을 만족시키는 최소 책임·계약 제안이다. 채택 전 담당의 기술 검토가 필요하며 현재 추적 설정에 가상의 모듈/명령을 추가하지 않는다.

| 항목 | 최소안(PROPOSED) | 막는 구현·검증 / 해제 조건 |
| --- | --- | --- |
| T-001 공유·소유 범위 | 공통 메모 모델·입력 검증 계약/벡터·저장 시도 상태 전이를 우선 공유 후보로 둠. 네트워크/저장 어댑터·플랫폼 탐색은 경계로 분리. UI 전체 공유는 강제하지 않음. 서버는 Kotlin 서버 타깃 후보, 앱·웹은 KMP 타깃 후보로 설계 검토 | 모듈 의존·소유 파일·플랫폼 UI/빌드/통합 계획 차단. 지원 타깃·공유 경계·담당 확정 및 호환성 근거로 해제 |
| T-001 라이브러리·UI 방식 | 업무 규칙은 공통 계약으로 유지하고 UI 기술은 기존 반응형·접근성 요구를 만족하는 최소 구성 비교. 특정 라이브러리·버전 확정은 UNKNOWN | 실제 UI·HTTP 어댑터·환경 구성/컴파일 검증 차단. 타깃별 API/라이브러리 검증 뒤 등록 |
| T-001 웹 지원 환경 | 재현 가능한 데스크톱 브라우저 1종·버전부터 고정해 시안 확인, 320/390/768/1280/1440px 및 600/1,000px 경계·200% 확대·포커스·탐색 확인. 이는 전체 지원 브라우저 보장이 아님 | 브라우저별 최종 호환 검증 차단. 실제 검증 환경 고정으로 해당 환경 검증만 해제; 광범위 지원 확대 필요시 별도 범위 판단 |
| T-002 서버·DB | 로컬 단일 서버·파일 기반 트랜잭션 저장소, 메모와 시도 결과를 같은 원자적 커밋으로 저장. 메모리 전용 DB는 영속성 근거로 쓰지 않음 | 생성·재시작 영속성·동시 재시도 구현, FEAT-002-AC-003/005/006/007 차단. 서버 런타임/DB/트랜잭션 경계 확정으로 해제 |
| T-003 API | 목록 조회·생성·동일 시도 결과 확인의 세 동작만. 생성 응답은 서버 ID·정규화 본문·생성 시각 포함; 오류는 확실한 미저장/결과 불확실 구분. 갱신 실패 재시도는 목록만 호출 | 클라이언트/서버 계약 및 FEAT-001-AC-001~006·FEAT-002-AC-001/003~007 연동 검증 차단. 메서드/경로/스키마/오류 계약으로 해제 |
| T-003 정렬·전체 조회 | 서버 생성 시각 내림차순 + 고정 서버 ID 동률 순서. MVP 전체 조회는 기존 INFERRED 제안 재사용, 페이지·검색 추가하지 않음 | 동률 정렬 및 세 플랫폼 순서 AC-002 차단. ID 비교법·응답 순서 계약 고정으로 해제 |
| T-004 문자열 계약 | 공백 집합·Unicode 분할 기준/버전을 명시하고 확장 자소군 기준을 후보로 삼음. 내부 공백/개행 보존, 임의 NFC 변환·개행 치환은 최소안에서 하지 않음. 서버 최종 판정 + 같은 입력 벡터를 전 타깃에서 확인; JS trim/Intl.Segmenter를 최종 계약으로 승계하지 않음 | 빈/2,000/2,001·조합 한글·이모지·CRLF 등의 FEAT-002-AC-001/002 차단. 정확한 테이블/분할·서버-클라이언트 일치 검증으로 해제 |
| T-005 중복 방지 | 저장 전 독립 시도 키를 생성하고 고정 본문과 함께 복구 정보로 보존. 서버는 키 유일성+본문 일치 검사·원자 저장·기존 결과 반환. MVP 동안 결과 키를 임의 만료하지 않는 안 | 응답 유실·동시 요청·서버 재시작 한 건 및 독립 새 작성 두 건 AC-005~007 차단. 키 범위/원자성/보존/충돌 응답 계약으로 해제 |
| T-005 재진입·잠금 해제 | 저장 중/불확실 시도는 앱 종료·웹 새로고침 뒤 키/본문으로 복구해 같은 시도 확인/재전송. 조회 “아직 없음”이나 타임아웃만으로 새 키 발급·편집 해제하지 않음. 성공 또는 같은 키의 최종 미저장 확정 뒤만 해제 | 탐색·강제 종료·장기 장애 복구, 중복 방지 검증 차단. 재확인 상태·최종 미저장 판정 계약으로 해제. 오프라인 큐/자동 전송/일반 초안 동기화는 추가하지 않음 |
| T-006 레이아웃·접근성 모순 | 두 design.md의 과거 “고정 글줄 수·ellipsis 없음”은 목록 3줄 결정을 덮지 않음. 최소안: 목록은 3줄, 작성은 생략 없이 확대·세로 스크롤. 이전 960px 제안보다 후속 반응형·작성 832px 시안 기준으로 검토 | 최종 UI 인계·시각/확대 검증 차단. 디자인 담당이 모순 구절 적용 범위를 정리하고 실제 렌더링 검토로 해제; 이번엔 원본 시안/명세 재작성 안 함 |
| V-001 실행 인계 | 아래 후보 manifest의 파일 해시·현재 Git HEAD·dirty·역할 상태로 고정하고 승인된 입력을 담은 실제 커밋을 새 실행 전에 연결 | 새 v1 역할 실행/최종 인계 차단. 미래 커밋 해시는 UNKNOWN, commit + feature_version + baseline_id를 시작 전에 고정 |

### 사용자 선택 필요

U-001: **저장을 아직 누르지 않은 일반 초안**을 새로고침·앱 재진입 뒤 자동 복원할지. 기존 문서는 이 분기를 UNKNOWN으로 남겼다. 추천 최소안은 내부 이동 시 기존 버리기 확인을 유지하고, 새로고침/강제 종료 뒤 일반 초안 자동 복원은 제공하지 않는 것이다. 가능한 이탈 경고는 제공하되 OS/브라우저가 경고를 항상 보장한다고 약속하지 않는다. 대안은 기기 내 자동 복원이며 로컬 초안 저장·만료·정리 기준과 추가 검증이 필요하다. 선택 전 이 분기의 제품 동작·관련 탐색/재진입 검증만 보류한다. 저장 중·불확실 시도의 복구 정보 보존은 두 안 공통의 기술 제안으로 별도 취급한다. 답변 전 선택값 UNKNOWN/PENDING.

일반 초안 복원을 안 한다는 선택은 확실한 미저장 실패 후 화면 내 본문 유지나 불확실 동일 시도 복구 정책을 약화하지 않는다. 기술 상세·색상·카드 배치·v1 문서 이름은 재질문하지 않는다.

### v1 baseline 연결안 — 아직 활성 기준 아님

후보 manifest: `.harness/upgrade-v0.2.0/v1-baseline-proposal.json`. 별도 작업 DB나 새 제품 버전을 발급하지 않고 기존 task/execution/artifact 연결에 사용할 파일 묶음을 제시한다. `feature_version` 제안은 `v1`, 활성값/실행 시작 기준은 UNKNOWN이다. 후보 파일 해시를 과거 실행에 소급 삽입하지 않는다.

| 입력 묶음 | 현재 유효한 기준 | 검토 범위·다음 연결 |
| --- | --- | --- |
| 기획 | product.md의 SRC-001~004·D-001~004, 두 requirements.md R0.2-WEB 및 3줄 변경, roadmap.md의 후속 방향 | TASK-001/002 v0.1 PASS는 과거 snapshot만. TASK-005의 웹 범위 문서 검토와 해당 입력 해시는 보존. SRC-004 및 U-001 답변 포함 최종 입력은 새 버전 문서 검토 필요 |
| 디자인 명세 | 두 design.md의 D0.4-WEB IN_PROGRESS와 뒤에 이어진 최신 사용자 반응형/문구 변경 | 오래된 D0.1 COMPLETE·D0.3 표기를 현재 PASS로 삼지 않음. 목록 확대 문구·960px/후속 배치 설명 적용 범위 정리 필요 |
| 시안 | 기존 두 prototype/index.html + docs/design/prototype.css/js 최신 바이트 | D0.4 반응형 초안. 정적 문법 확인 이력만 존재; 시각·상호작용 NOT_RUN |
| 검토 기록 | planning-review.md, docs/design/review.md, 기존 tasks.yaml의 reviews/tested_outputs | 증거/역사 자료이며 최신 디자인 승인 입력이 아님. BROWSER-001은 당시 환경 근거; 현재 브라우저 가용성 재확인·실제 렌더링은 이번 미실행 |

연결 순서 제안: U-001 답변 → 기술 계약·디자인 모순 정리 → 최신 입력 문서/시안의 필요한 검토 → 실제 Git 커밋 고정 → 기존 FEAT-001/002·TASK-003/004를 재개할 새 실행 시작 시 설치 하네스 SHA/dirty와 입력 snapshot 묶음 해시·feature_version=v1·baseline_id 지정. 작업 상태 전환은 기존 실행기의 게이트를 따른다. 개발 작업은 아직 생성하지 않는다. 필수 시각 검토가 준비되기 전 UI 최종 인계를 해제하지 않으며 API/기술 제안의 문서 검토는 독립적으로 진행 가능하다.

현재 baseline의 승인 커밋/검토 실행/시각 근거/구체 라이브러리/제품 명령은 UNKNOWN 또는 NOT_RUN이다. 이번 대조는 기존 결정 식별과 연결안이며 최신 산출물 검증 PASS가 아니다.

## SRC-005 구현 진행 및 Xcode 재설치 후속

v1 baseline ACTIVE: `.harness/v1/active-baseline.json`, 제품 입력 커밋 `43c0b3eb9647161fc21f0c693e8f17ca51446d26`. U-001은 일반 초안 재진입 자동 복원 없음으로 확정됐으며 앞 절의 PENDING은 과거 상태다. 기존 미검증 변경에 과거 PASS를 승계하지 않고 V1-BASELINE/V1-DESIGN-REVIEW에서 최신 입력 변경분을 별도 검토했다. 200% 확대·보조기술·전 타깃 최종 검증은 그 PASS 범위가 아니다.

공통 JVM(공식 Unicode16 벡터·저장 상태), 서버(실제 HTTP·SQLite 경합/재시작/응답 유실), 웹(실제 API·초안 비복원·불확실 시도 재진입/같은 키 복구·독립 같은 본문·조회 실패 복구), Android(APK·API36 arm64 네이티브 계측1건)의 실제 수행 범위는 `.harness/v1/reviews/`와 원장 V1-*의 정확한 출력·코드 상태 해시에 연결됐다. 전 플랫폼 13 AC를 모두 통과했다는 뜻은 아니다.

초기 runbook의 Android `-Pandroid` 명령은 실패했다. 현재 검증한 명령은 `./gradlew :shared:jvmJar` 후 `./gradlew -p androidApp assembleDebug`. AGP/KMP 클래스 로더를 분리한 별도 빌드이며 Android README가 현재 운영 정정이다. 원래 입력 snapshot·실패 명령은 보존한다. iOS 실제 빌드는 `python3 iosApp/tools/verify.py`의 사전 점검과 Xcode 프로젝트를 사용한다.

사용자가 Xcode를 재설치했다고 알려 확인한 결과 Xcode26.6(17F113), 선택 경로는 전체 Xcode로 바뀌었다. 다만 Apple SDK 라이선스 미동의로 xcrun SDK 조회·Swift parser·실제 빌드가 차단됐다. 프로젝트/Info.plist lint만 PASS이며 iOS 컴파일·링크·시뮬레이터·실기기/최종 통합은 NOT_RUN이다. 라이선스는 사용자 직접 검토·동의 대기이며 에이전트는 수락하지 않았다. `.harness/v1/xcode-reinstallation-check.json` 참조. V1-IOS는 같은 작업을 이어갈 수 있도록 IN_PROGRESS로 보존하며 전체 완료로 표시하지 않는다.

### Xcode 후속 실제 검증 — 2026-10-20

위 라이선스 대기는 과거 관측이다. 사용자의 직접 동의 완료 응답 후 SDK 조회에 성공했다. 공식 `xcodebuild -runFirstLaunch`로 누락된 CoreSimulator 구성 요소를 설치하고 `xcodebuild -downloadPlatform iOS`로 iOS26.5(23F77) arm64 런타임을 설치했다. 초기 실패(exit70 구성 요소 누락, exit65 arm64 프레임워크에 x86_64 링크)는 보존한다. 프로젝트를 실제 지원하는 arm64로 명시한 뒤 KMP 프레임워크·앱 컴파일/링크가 exit0으로 통과했다.

별도 생성한 iPhone17 Pro 시뮬레이터에서 실제 XCTest UI/API **2건 PASS, 실패0, 건너뜀0, 명령 exit0**. 확인 범위: 2,001자 저장 차단, 일반 초안 프로세스 재시작 후 비복원, 실제 서버 저장·목록·재진입 유지, 접속 실패 후 불확실 시도 편집 잠금·프로세스 재시작 후 본문/동일 시도 복구·재시도·재진입 한 건. 접속 전 실패 복구 테스트를 서버 커밋 후 응답 유실의 iOS UI 검증으로 확대 해석하지 않는다. 사용한 시뮬레이터는 테스트 종료 후 종료했다.

근거: `.harness/v1/ios-test-summary.json`, `.harness/v1/ios-test-20261020-185357.xcresult`, `.harness/v1/ios-test-attachments/`, `.harness/v1/ios-simulator.json`, 최신 정확한 코드 상태를 담은 `.harness/v1/reviews/ios.json`. 기존 웹·Android 저장 메모가 같은 서버의 iOS 목록에 표시된 캡처도 보존했다. 실기기·서명·device 프레임워크, VoiceOver/Dynamic Type, 전체 키보드/뒤로 탐색, 전 플랫폼 모든 AC는 여전히 NOT_RUN 또는 부분 검증이며 **전체 v1 완료가 아니다**. 현재 응답의 Stop 실행·최종 응답 수집 여부는 다음 턴 대조 대상이며 명령 실행기의 수집 성공으로 대신하지 않는다.

V1-IOS는 위 한정 범위 검토를 통과해 DONE, V1-INTEGRATION은 실행 `8c6b37ed-67b3-43f9-b250-6ae3221ca483`의 IN_PROGRESS다. 통합 점검은 기존 다섯 모듈의 제출 파일 51개가 검토 해시와 일치함을 확인했고, 실제 API의 7개 ID가 유일하며 iOS 테스트 메모 두 개가 각각 한 건임을 확인했다. `.harness/v1/integration-status.json`에 환경상 불가와 아직 실행하지 않은 검증을 구분했다. 공통·서버 회귀 명령은 exit0/UP-TO-DATE로 기존 검증 결과를 재사용했으며 새 테스트 수행으로 세지 않는다. 제품 구현은 여전히 미커밋이며 입력 baseline 커밋에 구현이 들어 있다고 표현하지 않는다. 사용량은 실제 응답 ID 연결분만 집계하며 누락·총비용은 UNKNOWN이다.

현재 확인한 최신 자동 훅은 UserPromptSubmit `8c1704a2-4bce-4e5a-ae12-8820f7ffd24f`: 수집0.146733초, collector_ready0, 감독 관측 종료0/1.085286초다. 중복 후보5건은 재수입 제외 건수이고 저장된 source_key 중복은0건이다. 최근 중단된 개발 구간의 새 Stop 성공은 확인되지 않았으며 마지막 관측 Stop은 06:28:37 UTC다. 정적 연결, 실제 훅 실행, 명령 CLI 수집을 구분한 `.harness/v1/hook-followup.json`을 보존한다. 현재 응답 Stop은 UNKNOWN이다.

## 2026-10-20 전체 인수 대조 후속

현재 조건별 구현·실행·코드 SHA·미검증 이유는 [v1 인수 현황](v1-acceptance-status.md), 직접 실행은 [실행 안내](try-v1.md)로 연결한다. 앞 절의 초기2건 iOS/부분 검증과 차단 이력은 과거 근거로 보존한다. 실제 저장 지연·응답 유실·재시작·중복 방지 시험 및 최신 UI 결함 수정 검증을 추가했지만 전체 인수는 완료하지 않았다. 입력 baseline은 유지하고 제품 dirty 구현을 baseline 커밋의 내용으로 표현하지 않는다. 현재 응답의 Stop 결과는 다음 턴 확인 대상이다.


2026-10-21 사용자 발견 기반 [디자인 적합성 후속](design-conformance.md): 승인 baseline을 유지한 구현 보완 및 상태별 실제 캡처·관련 회귀를 별도 V1-DESIGN-CONFORMANCE에 연결한다. 입력 검토 PASS와 최신 구현 검증, 전체 v1 인수 상태를 구분한다.
