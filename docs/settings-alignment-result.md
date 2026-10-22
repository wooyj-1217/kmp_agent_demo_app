# SRC-007 설정 정정 결과

이번 결과는 설정·문서·기준 연결 정합성 검증이다. 제품 전환 구현/기술 준수 검증이 아니며 기존 API/DB/앱은 변경하지 않았다.

## 변경점

- `docs/project-settings.json`: 승인 목표는 Android/iOS Compose Multiplatform, 서버 Ktor, 공통/전용 모듈 경계. 웹 UI만 UNDECIDED다. 단일 UI 필드의 전체 상태는 웹 때문에 UNDECIDED이며 모바일 하위 결정은 CONFIRMED다.
- `docs/current-implementation.json`: 기존 Views/SwiftUI/HttpServer·축약 모듈과 코드 해시의 관측만 기록한다. 승인 목표가 아니다. SQLite는 호환 최소안 위임 내 선택으로 유지했다.
- `AGENTS.md`와 `tools/project_workflow.py`: 프로젝트 공식 ready/begin/review/handoff/resume 선검사. 과거 stage snapshot·부모 설정 해시가 낡은 투영·권한 없는 baseline은 거부한다.
- `.harness/v1/active-baseline.json`: 과거 ACTIVE를 보존하고 현재 목표 입력은 BLOCKED/implementation_authorized=false로 연결했다. 과거 planning/design PASS ID는 새 목표에 넣지 않는다.
- `CR-001`(docs registry): 정정 영향의 과거 검토 유효성은 RECHECK_REQUIRED. 리뷰의 원문 결과·실행·산출물·동결 입력은 삭제/변경하지 않았다.
- 기존 비활성 통합 태스크에는 다른 과거 문서 입력도 섞여 있어 설정 하나만 바꾸지 않았다. 구 태스크 전체를 이력으로 유지하고 아래 새 태스크에 현재 입력을 완전히 동결했다. 이전 계획의 “재동결”은 이 별도 태스크 연결로 수행했다. 제품 작업은 아직 시작하지 않았다.
- 프로젝트의 기존 실행/완료/기능 검토 helper8개와 오래된 상세 보고서 생성 경로도 선검사에서 차단한다. runbook/try-v1의 기존 앱 체험 명령은 기존 구현 관측용이며 목표 기술 승인 근거가 아니다.

## 현재 동결 입력

| 새 태스크 | 단계 | 현재 설정 입력 | 상태 |
| --- | --- | --- | --- |
| V1-TARGET-FOUNDATION | server_implementation | docs/project-settings.json | TODO / 실행0 |
| V1-TARGET-SERVER | server_implementation | docs/project-settings.json | TODO / 실행0 |
| V1-TARGET-ANDROID | ui | .harness/v1/settings-correction/projections/targets-android.json | TODO / 실행0 |
| V1-TARGET-IOS | ui | .harness/v1/settings-correction/projections/targets-ios.json | TODO / 실행0 |
| V1-TARGET-WEB | ui | .harness/v1/settings-correction/projections/targets-web.json | TODO / 실행0 |
| V1-TARGET-INTEGRATION | integration_verification | docs/project-settings.json | TODO / 실행0 |

투영 JSON은 부모 설정 SHA와 선택 타깃을 담는 파생 입력이며 독립 상태 원장이 아니다. 향후 설정 변경 시 재동결해야 한다. 새 작업들은 과거 구현 DONE/PASS 대신 정정 작업/정정 구현 태스크끼리 의존하며 모두 실행0이다.

## 실제 정합성 검사

정합성 검사 11건 PASS. 지원 스키마, 모바일 UI 결정 게이트, 웹/전체 UI 거부, 웹 UI와 독립된 Ktor 서버 결정, 모듈 경계, 과거 동결 입력 거부, 위조된 프레임워크/부모 해시 거부, 새 binding 및 실행 차단, 과거 리뷰 원문 보존과 유효성 비승계, 옛 helper 중단, 현재 baseline/보호 파일 해시를 확인했다.

실행 명령: `rtk proxy python3 -B tools/verify_settings_alignment.py`. 근거: `.harness/v1/settings-correction/verification.json`, `bindings.json`, `start.json`. 구 설정/baseline/원장/helper는 같은 폴더 history에 보존한다. 설치 하네스·제품 소스/빌드·이전 ZIP의 보호 해시 변경0이다. 프로젝트 `.harness` helper 자체는 공통 개발 캡처에서 제외되므로 별도 실행 거부 검사와 보존 사본으로 확인했다.

하네스 설치본의 기술 value 의미 검증/타깃별 UI 해석/자동 전파를 구현했다고 말하지 않는다. 프로젝트 공식 경로를 우회하는 직접 설치 API 호출을 전역 보안 강제로 막는 기능도 아니다. 현재 공식 경로·이미 동결된 정정 입력에서는 대체 구현을 승인 목표로 사용하지 않는다.

## 남은 것

- 사용자 결정은 웹의 동일 UI 기술/공유 화면 적용 범위만 남았다.
- 제품 전환 실행 권한 없음. Ktor/CMP/모듈 전환·전환 후 기능/디자인/상태별 검증 NOT_RUN. 미저장 뒤로가기 확인창 비교도 NOT_RUN 유지.
- 설정 검사 PASS를 제품 준수 PASS나 v1 완료로 승계하지 않는다. 전체 v1 BLOCKED.

## 상세 HTTP 기록 보존 제한

SRC-007 보고서 확인 중 검사기의 고정 출력 경로 때문에 .harness/v1/agreement-review/http.json이 현재 결과로 덮였다. 원래의 상세 링크/해시 목록은 복원할 수 없어 UNKNOWN으로 기록했다. 당시24개 링크 PASS 요약과 불변 검토 JSON/검증 문서는 유지되며, 이를 새 목표의 PASS로 승계하지 않는다. 현재 검사 결과는 settings-correction/http.json 및 시각·보고서SHA별 불변 사본으로 분리했다. 이는 제품 시험/리뷰 payload 손실이 아니라 보고서 HTTP 보조 기록의 제한이다.
