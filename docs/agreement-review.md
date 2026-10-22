# v1 합의 준수 검토 — SRC-006 / FB-004

2026-10-21 사용자 재확인에 따른 **CORRECTION**. 제품 변경이나 새 기능 결정이 아니다. 이 문서는 합의·변경 권한·실제 구현의 대조이며 기능 시험 결과를 대체하지 않는다. 현재 제품은 WORKING_TREE/dirty, 기준 HEAD는 `43c0b3eb9647161fc21f0c693e8f17ca51446d26`; 설치 하네스 v0.2.0 `0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55`는 변경하지 않는다.

## 결론

- **불일치:** Android/iOS Compose Multiplatform UI, Ktor 서버, 합의한 서버·클라이언트 전용 모듈과 의존 경계가 현재 구현에 반영되지 않았다. 대체 구현을 승인한 사용자 근거는 찾지 못했다.
- **별도 판단:** SQLite는 원자 저장·재시작 보존을 위한 에이전트 기술 선택이다. 사용자가 DB 종류를 직접 지정했다는 근거는 없으나, 기존 정책과 호환되는 기술 최소안 위임 근거는 있다. SQLite 사용 자체를 결함으로 판정하지 않는다.
- **남은 선택:** 웹을 Android/iOS와 같은 UI 기술·공유 구현 범위에 포함할지. Android/iOS의 Compose Multiplatform과 서버 Ktor는 다시 물을 사항이 아니다.
- **기능과 합의는 별개:** 기존 저장·목록·복구 및 집중 디자인 시험 PASS는 해당 코드/범위의 기능 결과로 보존한다. 합의 준수 PASS는 아니며, 앞으로 교체되는 경로에는 영향에 따른 재검증이 필요하다. 전체 v1은 계속 BLOCKED다.
- **FB-005 추가 발견:** 미저장 본문의 뒤로가기 확인창 `C-DISCARD-CONFIRM`은 시안에 존재했으나 기존9개 상태 비교/캡처에서 빠졌다. Android 일부 행동 시험 PASS와 구분하여 세 플랫폼 확인창 상태 비교를 NOT_RUN으로 명시한다. 새 정책/사용자 선택이 필요한 사항이 아니라 기존 디자인의 검증 누락이다.

## 근거와 변경 권한

원본 세션 로그 전체는 보고서에 복사하지 않는다. 아래는 결정에 필요한 선별 발췌이며, 원본 위치·이벤트·텍스트 SHA로 추적한다. 로그의 기록 순서와 사용자 사건 시각을 혼동하지 않는다.

| 근거 | 원문·의미 | 승인 범위 |
| --- | --- | --- |
| E-01 / 사용자, 2026-10-13T02:41:41.121Z | “Ktor 백엔드 + KMP·Compose Multiplatform Android/iOS 앱”. model/domain, domain-server/data-server/presentation-server/server 및 domain-client/data-client/presentation-client/androidApp/iosApp 명시. 각 data/presentation은 해당 전용 domain, 전용 domain은 공통 domain, 전용 domain끼리 참조 금지. Domain은 DTO/UI/HTTP/DB 독립. 진입점 DI. | 명시적 목표 기술·모듈·의존 경계. DI 라이브러리 이름은 지정하지 않음. 구현 당시에는 PLANNED 유지 요청. |
| E-02 / 사용자 웹 지원 추가, 2026-10-13T13:08:30.061Z | Android·iOS·웹 및 공통 API/업무 정책 확정. “공유 코드·UI·웹 구현 방식은 아직 임의 확정하지 않는다.” | 웹 추가가 웹 Compose 채택이나 모바일 UI 합의 폐기를 자동 승인하는 것은 아님. 공용 하네스 일반 지침과 데모 제품 지시를 구분해야 함. |
| E-03 / SRC-004, 2026-10-20T06:25:28.550Z | KMP 기반 서버·앱·웹 방향, 공유 범위·라이브러리가 이미 결정됐다고 가정하지 말 것, 기존 정책과 충돌하지 않는 최소안 제안. | 기록상 앞선 구체 합의와 미정 표현의 충돌이 존재. 명시적 Ktor/CMP 철회 지시는 확인되지 않음. 당시 대조/질문 또는 기존 합의 보존이 필요했음. |
| E-04 / SRC-005, 2026-10-20T06:30:47.044Z | “기술 판단 항목은 기존 기획·디자인과 호환되는 최소안을 선택하고 선택 이유를 기록”. 요구/UX 변경만 질문. 일반 초안 자동 복원 없음과 저장 시도 복구 계약 별도 유지. | 포괄적 기술 판단·호환되는 세부 선택 및 순차 구현 권한. 이미 명시된 기술·구조를 폐기하는 별도 변경 승인은 아님. |
| E-05 / 에이전트 기술 문서·설정 | technical-decisions의 “최소 의존성”, project-settings의 CONFIRMED 및 planning 검토 PASS. | 구현 선택/검토 기록이며 사용자 승인 근거가 아님. 원본은 보존하고 효력 한계를 정정함. |
| E-06 / 이번 사용자 재확인 | UI 방식 통일과 Ktor 사용이 합의였음을 반영하라는 현재 사용자 요청. | 유효한 사용자 재확인. Android/iOS의 구체 UI 기술은 E-01의 Compose Multiplatform으로 확인. 웹 적용 여부만 UNKNOWN. 네이티브 원문의 session/turn/message ID는 확인해 별도 개입 근거에 기록. 저장소 원문 이벤트 연결은 수집 전 UNKNOWN/PENDING이며, 네이티브 열람을 실제 훅 수집 성공으로 취급하지 않음. |

E-01: `.harness/logs/events.jsonl` 454행, 이벤트 `af79796c-a904-449b-8d69-f1fe47d876a8`, 사용자 텍스트 SHA-256 `2f295305819b2c77d38605d7a83a486bc3383eb31b196306c13ca30ad729cc1f`.

E-02: 같은 로그 1647행, 이벤트 `120f3e5d-67db-4004-9306-906863d7a2ac`. E-03: 2225행, `58366f5f-7067-4d14-9453-5015b4b3fb5e`. E-04: 2271행, `60d85378-bdcd-4114-80c6-89f5f9b95461`, 텍스트 SHA-256 `af014f56eb0eaf9bedd6c963e9f9881850ad9e57e1fcca2ac090b4a2cf132244`.

확인 범위는 이 저장소 수집 원문 중 사용자 발화의 Ktor/Compose/SQLite/UI 방식/공유 범위/기술 위임 관련 항목과 현재 요청이다. 미수집·외부 기록 전체를 확인했다고 주장하지 않는다. 초기 “미정”·이후 “공유 범위 미정” 표현은 실제 기록 충돌로 남기며, 이번 명시적 재확인 없이 에이전트 기술 문서가 이를 해결했다고 보지 않는다.

## 합의 대조

| 합의한 기준 | 실제 구현 | 합의·변경 승인 근거 | 판정 | 필요한 조치 |
| --- | --- | --- | --- | --- |
| Android/iOS는 KMP·Compose Multiplatform으로 UI 방식 통일 | Android 기본 View, iOS SwiftUI. shared는 정책/상태/DTO만 공유, UI 없음 | E-01 + E-06. 플랫폼별 기본 UI로 바꾸라는 명시적 사용자 승인 없음. E-04의 최소안 위임으로 대체 불가 | 불일치 | P0 목표 문서 정정. P1 두 앱을 Compose Multiplatform 기반으로 전환하는 계획. OS 진입점/안전 영역/키보드·접근성 어댑터와 구체 공용 화면 분리는 설계하되 요구/UX 보존 |
| 서버 Ktor | JDK com.sun.net.httpserver.HttpServer, 자체 route/JSON/오류 처리 | E-01 + E-06. 에이전트는 작은 로컬 API/의존성 절감을 이유로 Ktor를 미채택. 별도 변경 승인 없음 | 불일치 | P1 API·오류·원자 저장/복구 계약을 유지한 Ktor 전환 계획. DB 교체와 결합하지 않음 |
| 공통 model/domain 및 server/client 전용 domain/data/presentation 모듈·의존 방향 | 루트 shared/server/web와 별도 Android 빌드. 순수 domain 패키지는 있으나 전용 계층 모듈 없음. HTTP·UI·저장 조립이 각 진입 파일에 집중 | E-01. 모듈 통합/계층 생략 승인 없음. 기술 문서는 해당 구조를 선택 스택의 선택적 참조로 취급 | 불일치 / 일부 원칙 유지 | P1 공통 model/domain과 전용 domain 계약부터 분리. DTO는 model, 순수 규칙은 domain; 서버·클라이언트 경계를 검증. 클래스 개수만 늘리는 변경으로 대체하지 않음 |
| Domain의 DTO/UI/HTTP/DB 독립, 전용 domain끼리 무참조, 진입점 DI | BodyPolicy/Unicode16은 순수. SaveMachine/AttemptStore 공유와 서버 진입점 조립 존재. 전용 domain 자체가 없어 해당 의존 방향 전체를 충족했다고 할 수 없음 | E-01. 특정 DI 라이브러리 채택 합의는 없음 | 부분 일치 | 순수 정책 재사용 가능성 확인. 전용 domain 경계 및 진입점 조립을 목표 모듈에 연결; DI 프레임워크는 필요 시 위임 내 선택 |
| DB 종류는 기존 업무 정책과 호환되는 기술 판단 대상 | SQLite JDBC 3.50.3.0, UNIQUE attempt_id 및 트랜잭션, user_version1 | E-04의 호환 최소안 선택 위임. SQLite를 사용자가 직접 선택/승인했다는 원문 없음. E-01은 DB 종류 미지정. 사용자의 이후 DB 조회 요청은 선정 승인으로 소급 해석하지 않음 | 위임 내 선택 / 위반 근거 없음 | 유지 제안. DB·기존 데이터 보존. Ktor/모듈 전환 때 저장 계약 회귀. 별도 DB 승인 질문을 만들지 않음 |
| 웹 포함·공통 API/정책, 웹 UI 기술/공유 범위는 미확정 | Kotlin/JS DOM + fetch/localStorage, shared 로직 사용 | E-02/03/04. 현재 UI 통일 확인만으로 웹까지 Compose 확정이라 가정하지 않음 | 범위 미확인 | 사용자 선택: 웹도 같은 UI 기술/공유 화면 범위에 포함할지. 선택 전 웹 전환 구현 시작 금지 |
| KMP 활용·버전·세부 라이브러리 선택 | Kotlin2.2.10/Gradle8.14.3/JDK17, serialization1.9.0. Android는 별도 빌드와 shared JVM JAR 파일 연결 | KMP 방향 및 E-04. 위 버전/HTTP 라이브러리를 사용자가 직접 지정한 근거 없음. 별도 Android 빌드는 클래스 로더 충돌 우회 기록 | 위임 내 세부 선택 / 빌드 구조 보완 필요 | 버전 업그레이드 없이 목표 모듈을 Gradle 의존으로 연결하는 방안 검토. Ktor/CMP 전환 호환성은 실제 검증 전 UNKNOWN |
| 일반 초안 비복원·저장 시도 영속 복구·중복 방지·로컬 범위 | 해당 계약 구현 및 범위별 실제 시험 PASS. iOS pending은 UserDefaults가 아닌 파일 atomic+fsync | 기존 D-001~004/SRC-005; 기능 증거는 기존 보고서. iOS 기술 메모는 실제 코드와 불일치 | 정책 기준 유지 / 문서 오류 | 원문 이력을 보존하며 iOS 저장 설명 정정. 기능 PASS와 구조 불일치 분리. 전환 후 영향받는 경로만 재검증 |

실제 구현 근거: `settings.gradle.kts`, `androidApp/settings.gradle.kts`, `shared/build.gradle.kts`, `server/build.gradle.kts`, `server/src/main/kotlin/memo/server/Main.kt`, `server/src/main/kotlin/memo/server/MemoStore.kt`, `shared/src/commonMain/kotlin/memo/domain/BodyPolicy.kt`, `shared/src/commonMain/kotlin/memo/client/SaveMachine.kt`, `androidApp/src/main/kotlin/memo/android/MainActivity.kt`, `iosApp/MemoApp.swift`, `web/src/jsMain/kotlin/memo/web/Main.kt`.

## 기존 검토에서 놓친 경위와 판단 한계

1. product.md/SRC-004의 “세부 기술 미정” 정리와 앞선 명시적 사용자 구조 원문을 완전히 대조하지 못했다. 웹 추가 시 일반 하네스 선택 규칙과 이미 전달된 구체 구조를 구분해야 했다.
2. 에이전트 기술 결정은 “호환 최소안” 위임을 근거로 UI 비공유·Ktor 미사용을 정했다. 이는 선택 이유이지 합의 변경 승인 사유가 아니다. project-settings의 CONFIRMED에도 이 차이가 드러나지 않았다.
3. planning.json PASS는 “KMP direction and technical ownership selected by delegated authority”를 관측으로 남겼다. 기존 구조·UI/Ktor 원문을 각각 인수 기준으로 대조한 증거는 없다. 같은 Codex 역할 전환 검토이며 독립 검토가 아니다.
4. 이후 서버/플랫폼 시험과 디자인 검토는 저장·복구·레이아웃을 확인했다. 목표 기술/모듈 준수 항목이 빠져 기능 PASS가 구조 준수로 오해될 여지가 생겼다. 모든 과거 검토가 원문을 전혀 읽지 않았다고 단정할 수는 없지만, 이탈을 검출/차단하지 못한 사실은 확인된다.
5. 직전 설명도 “사용자 확정은 KMP 방향”으로 축소했다. 이번 원문 대조로 그 설명을 정정한다. 사용자 개입은 새 스택 요구가 아닌 기존 합의 누락의 CORRECTION이다. 공통 하네스 코드 결함으로 원인 확정하지 않는다.

## 수정 계획 — 이번에는 구현하지 않음

| 우선순위 | 작업 | 착수/검증 기준 |
| --- | --- | --- |
| P0 / 이번 문서 범위 | SRC-006 정정, 원문 발췌·위임 경계·불일치 기록, 기존 보고서/검증 보존, 개편 HTML 실제 표시 검토 | 사용자 재확인·원문·코드가 대조표에 연결. 구 보고서의 PASS/ACTIVE를 새 합의 입력 검토로 승계하지 않음 |
| P1 / 후속 구현 계획 | Ktor 서버 전환과 기존 SQLite 저장 구현 경계 분리 | 공개 API/오류/응답 순서/중복 방지/영속성 계약 동일. 임시 DB에서 서버·연동 영향 회귀 필요; 현 DB 변경/마이그레이션 계획 없음 |
| P1 / 후속 구현 계획 | model/domain + server/client 전용 domain/data/presentation 및 진입점 연결 | 의존 방향·순수 domain·전용 domain끼리 무참조·타깃 빌드 검증. 모듈 분리와 동작 보존을 별도 판단 |
| P1 / 후속 구현 계획 | Android/iOS Compose Multiplatform UI 전환, 공통 화면·상태와 플랫폼 어댑터 연결 | 기존 디자인/초안/저장 시도 계약 보존. 두 플랫폼 실제 화면·키보드·취소·접근성 및 저장/복구 영향 재검증. 코드 재사용률 수치 임의 제시 안 함 |
| P2 / 사용자 선택 뒤 계획 | 웹 UI 적용 범위 결정 및 필요 시 웹 전환 | 웹 범위 결정 전 임의 기술 선택·동작 변경 없음. HTML/CSS 시안을 제품 구현 기술 합의로 취급하지 않음 |
| 필수 인수 잔여 | 실제 TalkBack/VoiceOver/웹 스크린리더, 미실행 탐색 조합, 최신 표시 변경 후 웹200% | 기존 NOT_RUN/재검증 필요 유지. 전환 구현의 영향을 반영한 새로운 코드 기준에서 검증해야 하며 기존 결과를 삭제하지 않음 |

현재 사용 가능했던 범위: 로컬 세 클라이언트의 목록·작성·서버 저장·같은 시도 재확인, 범위별 기능/디자인 검증 결과. 이번 요청에서는 앱·서버·DB를 다시 시험/변경하지 않았으며 현재 실행 상태를 새로 보장하지 않는다. DB 조회는 당시 8080 실제 DB의6건/스키마 확인 근거일 뿐 전체 기능 인수 증거가 아니다.

보존: `reports/v1/index.html`과 기존 ZIP·원본 실행 결과는 그대로 두고 `reports/v1/agreement-review/index.html`에서 참조한다. 기존 baseline은 당시 입력으로 보존하며 이번 정정 입력의 합의 적합성 PASS 또는 구현 착수 승인으로 취급하지 않는다. 이번 발견은 [FB-004](feedback.md#fb-004), [RETRO-009](retrospective.md#retro-009) 및 `V1-AGREEMENT-REVIEW`에 연결한다.
