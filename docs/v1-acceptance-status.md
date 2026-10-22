# v1 인수 검증 현황

> SRC-007: 현재 승인 목표는 project-settings.json/target-architecture.md, 실행 전 검사는 tools/project_workflow.py 및 settings-alignment.md를 따른다. 아래 명령·PASS·구현 설명은 기존 대체 구현의 관측/이력이며 목표 기술 준수 또는 전환 착수 허가가 아니다. 현재 목표 baseline은 BLOCKED다.

> SRC-006 합의 준수 정정(2026-10-21): 기능/디자인 시험 결과와 별개로 Compose Multiplatform Android/iOS·Ktor·전용 계층 합의와 실제 구현이 불일치한다. [합의 검토](agreement-review.md)가 현재 정정 근거이며 과거 PASS/DONE/ACTIVE는 당시 입력 이력으로 보존한다. 이번 정정 입력을 반영한 새 구현 baseline 승인이나 전환 후 검증은 수행하지 않았다.

판정 원본은 `.harness/tasks/tasks.yaml`의 V1-INTEGRATION 및 연결된 실행·근거다. 이 문서는 그 결과를 조건별로 읽기 쉽게 연결한다. **전체 v1 완료 아님.** 구현 파일 존재, 빌드 성공, 실제 시나리오 통과를 구분한다.

입력 baseline: `sha256:4afe5bd1948a1608adfb1e593eaf7e79fe98a3b7010522611d08913a48b9d864`, 입력 커밋 `43c0b3eb9647161fc21f0c693e8f17ca51446d26`. 제품 구현은 WORKING_TREE/dirty이며 해당 커밋만으로 재현된다고 주장하지 않는다. 이번 검증 시작 파일 SHA는 `.harness/v1/acceptance-before.json`, 최종 파일별 SHA·근거 유효성은 후속 인수 근거 manifest로 식별한다. 하네스는 v0.2.0 / `0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55` 고정 설치본이다.

## 구현·근거 연결

| 표기 | 구현 경로 | 실제 기존 검증 / 재사용 범위 |
| --- | --- | --- |
| A | [Android Activity](../androidApp/src/main/kotlin/memo/android/MainActivity.kt), [추가 인수 계측](../androidApp/src/androidTest/kotlin/memo/android/AcceptanceTest.kt) | reviews/android.json: APK·API36 arm64 계측1건. 2,001자 차단·실제 저장/목록·Activity 재생성 일반 초안 비복원. 프로세스 종료/복구와 하드웨어 입력 전체로 확대하지 않음 |
| I | [SwiftUI 모델·화면](../iosApp/MemoApp.swift), [XCTest](../iosApp/MemoUITests.swift) | reviews/ios.json 및 ios-test-summary.json: Xcode26.6 / iOS26.5 arm64 실제 UI 2건. 2,001자 차단·저장/목록·프로세스 재시작 비복원·접속 전 실패 시도 복구. 커밋 후 응답 유실과 다름 |
| W | [Kotlin/JS 제품](../web/src/jsMain/kotlin/memo/web/Main.kt), [제품 CSS](../web/src/jsMain/resources/product.css) | reviews/web.json·web-browser-checks.json: Chrome155 실제 서버 핵심 흐름. 이번 web-acceptance-ui.json: 키보드·커서·문자 계약 경계·반응형 추가 관측 |
| S | [HTTP](../server/src/main/kotlin/memo/server/Main.kt), [SQLite](../server/src/main/kotlin/memo/server/MemoStore.kt), [서버 테스트](../server/src/test/kotlin/memo/server/ServerTest.kt) | reviews/server.json: 실제 HTTP/DB 4건. 별도 연결 24개 동일 키 경합·독립 동일 본문·정렬 동률·재시작·응답 본문 유실 재시도·입력 오류·스키마 보존 |
| C | [공통 본문 정책](../shared/src/commonMain/kotlin/memo/domain/BodyPolicy.kt), [저장 상태](../shared/src/commonMain/kotlin/memo/client/SaveMachine.kt) | reviews/shared.json: JVM 정책3건+공식 Unicode16 분할 벡터1건. 다른 타깃의 실제 컴파일/실행은 플랫폼별 근거로 별도 판정 |

기존 검증을 단순 반복하지 않았다. 공통·서버 회귀 명령의 이전 UP-TO-DATE는 새 테스트 실행 건수가 아니다. 새로운 장애 시험은 [전용 프록시](../server/tools/acceptance_fixture.py)로 실제 JVM 서버/SQLite 앞에 지연·422·503·커밋 후 연결 종료를 주입한다. `:18080` 제품 연결, `:18081` 실제 서버, `:18082` 시험 제어이며 사용자 DB와 분리된다. 모든 reset은 새 시험 DB를 만들고 과거 DB를 보존한다. restart는 같은 DB를 유지한다. `acceptance-fixture/events.jsonl`에는 실제 upstream 상태·요청 키·종료 코드가 남는다.

## 조건별 판정

구현은 아래 모든 조건에 존재한다. PASS는 **명시한 환경·분기**의 실제 실행 결과이며 전 기기·보조기술 보장이 아니다. 아래 근거 별칭은 모두 `.harness/v1/` 기준이다.

- A1: `android-acceptance-20261020-202155/summary.json` 6건 PASS. A2: `android-acceptance-20261020-202449/summary.json` 2건 PASS 및 `during-post-proof.json`.
- A3: `android-acceptance-20261020-203501/summary.json` 큰 글꼴·3줄·시스템 표시 1건 PASS. 각 summary에 실제 APK/소스 SHA가 있다.
- I1: `ios-test-20261020-194148.xcresult` 장애·영속성 1건 PASS. I2: `ios-test-20261020-194536.xcresult` 중 Unicode/전송 중 재시작 1건 PASS(동일 번들 다른 검사의 실패는 보존).
- I3: `ios-test-20261020-195422.xcresult` 정렬·경계·취소 검사 PASS. I4: `ios-test-20261020-210433.xcresult` 최신 편집·앱 접근성 감사·긴 미리보기 3건 PASS. `ios-acceptance-210433/tested-files.json`에 정확한 소스 SHA 보존.
- W: `web-acceptance-product.json` 실제 Chrome 관측, `web-proof.json` DB/요청 대조, `web-acceptance-phases/016-snapshot.json` 원본. 수정 전 실패 관측도 삭제하지 않았다.
- S/C: `reviews/server.json`, `reviews/shared.json` 및 연결된 실제 테스트 XML. 변경 없는 공통/서버 업무 코드는 다시 실행하지 않았다.

| 조건 | 구현 기준 | Android 실제 결과 | iOS 실제 결과 | 웹 실제 결과 | 서버/DB 결과·미검증 이유 |
| --- | --- | --- | --- | --- | --- |
| FEAT-001-AC-001 로딩 표시·종료 | A/I/W loadList, S GET | PASS A1 지연→목록 | PASS I1 | PASS W 지연→빈 목록 | HTTP PASS; 로딩 UI N/A |
| FEAT-001-AC-002 최신순·동률 | A/I/W 정렬, S ORDER BY | PASS A1 고정 날짜/ID 반복 | PASS I3 | PASS W 고정 날짜/ID 반복 | PASS S 고정 Clock·동률 |
| FEAT-001-AC-003 빈 안내·작성 | A/I/W 분기 | PASS A1 | PASS I1 | PASS W | 빈 배열 PASS; UI N/A |
| FEAT-001-AC-004 최초 실패·재시도 | A/I/W 오류 분기 | PASS A1 GET503→회복 | PASS I1 | PASS W GET503→회복 | UI N/A |
| FEAT-001-AC-005 성공 메모 한 번 | A/I/W merge, S 키/ID | PASS A1 | PASS I1 | PASS W | PASS S 같은 키 기존 결과 |
| FEAT-001-AC-006 저장 후 조회 실패 | A/I/W 성공 후 GET | PASS A1 메모 보존·GET만 재시도 | PASS I1 동일 | PASS W 동일·POST 1회 대조 | 영속성 PASS; UI N/A |
| FEAT-002-AC-001 본문·개행·trim | C 정책, A/I/W 입력, S 저장 | PASS A1 실제 다중 줄 저장 | PASS I1 | PASS W 내부 들여쓰기 포함 | PASS S 내부 문자 보존 |
| FEAT-002-AC-002 빈/1/2000/2001·문자 계약 | C 및 A/I/W/S | PASS A1 경계·Unicode 입력 | PASS I3/I2 및 기존2001 검사 | PASS W 계약 벡터·2000 이모지 실제 DB; 기존2001 | PASS S; C 공식 Unicode16 벡터는 JVM 범위 |
| FEAT-002-AC-003 영속 확인 후 닫기 | A/I/W send/success, S COMMIT | PASS A1 지연 중 잠금·작성 유지 | PASS I1 | PASS W 지연 중 잠금 | PASS S COMMIT 후 응답 |
| FEAT-002-AC-004 확실한 미저장·수정/재시도 | A/I/W 422/413 분기 | PASS A1 실제422→수정 저장 | PASS I1 실제422→수정 저장 | PASS W 실제422→수정 저장 | PASS S 422/413 무저장; 클라이언트 장애 주입은422 범위 |
| FEAT-002-AC-005 커밋 후 응답 유실·재시작·한 건 | A/I/W 복구, C 키, S 유일성 | PASS A1 실제 커밋 유실→재확인 | PASS I1 실제 커밋 유실→재진입 | PASS W 실제 커밋 유실→새로고침 | PASS S 실제 HTTP 응답 유실·같은 DB 재시작 |
| FEAT-002-AC-006 연속 저장·독립 같은 본문 | A/I/W 잠금, C 상태, S UNIQUE | PASS A1 연속 누름·독립2건 | PASS I1 동일 | PASS W 연속 누름 당시POST1회·독립2건 기존 근거 | PASS S 별도 연결24개 동일 키 한 건 |
| FEAT-002-AC-007 서버·앱 재시작 | A/I/W 재진입, S 파일DB | PASS A1/A2 | PASS I1/I2 | PASS W 서버 재시작+새로고침 | PASS S 같은 파일·같은 ID |
| V1-NAV-001 일반 초안 자동 비복원 | A/I/W 메모리만 | PASS A1 실제 force-stop 후 빈 작성 | PASS 기존185357 프로세스 재시작 | PASS 기존 실제 새로고침 | N/A 클라이언트 정책 |
| V1-RECOVERY-001 저장 시도 재진입 복구 | A prefs/I 파일/W localStorage, C/S | PASS A2 전송 중 force-stop가 응답보다8.588초 빠름 | PASS I2 지연POST 중 terminate·재진입 | PASS W POST 진행 중 reload·같은 키 | PASS S 유일 키·영속성 |

전체 파일이 변경되면 과거 모듈 검토 PASS를 현재 전체 파일에 승계하지 않는다. 공통/서버 업무 파일의 SHA 불변은 최종 manifest로 대조한다. iOS는 `ios-model-reuse.json`에서 새 `edited()` 메시지 해제 함수 외 모델 영역이 원본과 동일함을 확인했다. Android의 저장/HTTP/재확인 함수는 표시 수정과 분리해 최종 대조한다. 최신 표시/편집 변경에는 별도 집중 시험 결과를 연결한다. 실패한 드라이버 기대값·과거 접근성 실패는 성공 건수에 합산하지 않는다.

## UI·환경 검증과 남은 필수 조건

| 항목 | 실제 결과 | 한계/남은 조건 |
| --- | --- | --- |
| Chrome 키보드·포커스·반응형 | PASS: 320~1440px 및600/1000 경계, 작성/취소/커서, 짧은 높이 문서 스크롤 | 고정 Chrome 환경에 한함 |
| Chrome 실제200% 확대 | PASS: Chrome UI에200%, DPR4; width1024/scrollWidth1016, Tab으로 저장 버튼이 화면 안에 들어옴. `chrome-zoom-proof.json`, `product-captures/chrome-200-create.png` | 100%로 복원 확인; viewport 축소 시험과 구분 |
| 목록 최대3줄·원문 보존 | PASS: A3 native ellipsis, I4 실제 높이/화면, W 실제 clipping+DB 원문2000이모지 | 별도 상세 화면 추가 없음 |
| Android 글꼴200% | PASS A3 실제 font_scale2.0·버튼·3줄; 시험 후1.0 복원 | 실제 TalkBack 읽기/모달은 NOT_RUN |
| iOS Dynamic Type·대비·잘림·타깃/라벨 | PASS I4 앱 소유 요소 감사0건; OS 키보드3건은 원본에 별도 보존 | XCTest 자동 감사이며 실제 VoiceOver 읽기 PASS가 아님 |
| 최신 편집 후 오류 해제·포커스 | 웹·iOS·Android 실제 PASS | Android `android-acceptance-20261020-211355/summary.json`, iOS I4, 웹 W에 최신 결과 연결 |
| 실제 보조기술 읽기·모달 | NOT_RUN: Android TalkBack, iOS VoiceOver, 웹 실제 스크린리더 | 현재 증거는 AX/자동 감사이며 실제 음성·탐색 세션을 수집하지 못함. 접근성 전체 인수는 보류 |
| iOS 스와이프/플랫폼별 탐색 전체 | Android 플랫폼 Back 및 iOS 기본 취소 팝오버 PASS; 모든 제스처 조합은 NOT_RUN | 시뮬레이터/선택 테스트 밖으로 확대하지 않음 |
| iPhone 실기기 | NOT_RUN 서명 팀·연결 기기 미설정 | 선택된 시뮬레이터 검증과 구분하는 추가 타깃; 실기기 통과 주장 없음 |

현재 제품 정책의 추가 사용자 선택은 없다. 실제 보조기술 세션 등 남은 필수 검증이 끝나기 전 **V1-INTEGRATION/v1 전체 완료 아님**. 미실행은 PASS나 자동 사용자 판단 항목으로 치환하지 않는다.

## 실행·작업·사용량·훅

[직접 실행 안내](try-v1.md)에 웹/서버, Android 별도 Gradle 빌드, iOS Simulator 실행 방법을 모았다. 구현은 WORKING_TREE이며 최종 manifest의 파일 SHA가 코드 기준이다. 입력 baseline 커밋만 checkout해서 현재 구현을 얻을 수 있다고 표현하지 않는다.

작업 V1-INTEGRATION / 실행 `8c6b37ed-67b3-43f9-b250-6ae3221ca483`에 실제 명령 시작/종료·코드 스냅샷·검증 원본을 연결한다. `acceptance-usage-bindings.json`의17건은 실제 응답 ID/사용량 레코드에 귀속된 부분 집계이며 전체 사용량·비용 및 이후 미귀속분은 UNKNOWN이다.

직전 Stop `61f4923d-b75c-4ee8-9425-f1009fc645da`: UTC10:15:04, 수집0.184193208초/감독0.897709167초, 내부 종료0. 이전 최종 응답은 실제 Stop 범위에서1회 수집됐고 원문 source_key 중복0건이다. 이전 요청은 CLI가 먼저 회수했으며 Stop에서 최초 수집했다고 하지 않는다. `previous-stop-acceptance-audit.json` 참조. 정적 훅 연결 PASS와 실제 수집 성공은 별도다. **현재 응답 Stop 결과는 UNKNOWN, 다음 턴 대조 대상**이며 외부 실행기 종료도 UNKNOWN이다.

최종 증거: `.harness/v1/acceptance-final-manifest.json`(파일별 SHA/재사용 대조), `android-acceptance-20261020-211355/summary.json`(최신 집중1건 PASS/실제 APK SHA), `ios-test-20261020-210433-summary.json`(최신3건 PASS). 시험용 서버8080·장애 프록시·전용 에뮬레이터/시뮬레이터는 종료했다. [실행 안내](try-v1.md)로 서버를 새로 시작할 수 있다.

최종 원장 판정: V1-INTEGRATION **BLOCKED**, 필수 기준 `V1-INTEGRATION-CHECK` **NOT_RUN**. 별도 검증 실행 `8040bc0d-c0e5-472e-8348-a3b95ff96a30`에서 최신 코드 상태/동일 baseline을 고정했다. `.harness/v1/acceptance-review.json`, `acceptance-integration-links.json`, `acceptance-collection-report.json`이 검토·통합 관측·명령/실행/사용량 연결의 원본이다. 이는 제품 결함이 남았다는 판정과 같지 않으며, 실제 보조기술·남은 탐색 증거가 없어 필수 전체 인수를 통과시키지 않았다는 뜻이다.


## 2026-10-21 디자인 적합성 후속

사용자 발견에 따라 [승인 baseline 대조·수정·최신 검증](design-conformance.md)을 추가했다. 기능 검증 PASS와 디자인 적합성을 분리하며 과거 시안 입력 검토를 최신 제품 PASS로 적용하지 않는다. Android 최신4개 및 실제8080 UI 연결1개, iOS5개와 목록 오류 집중1개, 웹 실제9개 상태/HTTP·SQLite 대조의 정확한 소스·재사용 범위는 해당 문서와 `.harness/v1/design-conformance/manifest.json` 참조. 최신 UI에 대한 실제 VoiceOver·TalkBack·웹 화면 읽기는 NOT_RUN이며 전체 v1 BLOCKED를 보존한다.
