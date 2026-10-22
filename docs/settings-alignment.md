# SRC-007 설정·실행 기준 정정

범위: 승인 목표와 관측 구현의 분리, 설정을 소비하는 실행/검토 경로 및 baseline 연결 정합성. 제품 전환·DB 변경·하네스 설치본 수정·배포는 제외한다. SRC-006의 Compose Multiplatform Android/iOS·Ktor·공통/전용 모듈 경계를 복원하며 웹 UI 범위만 미정으로 둔다.

## 원본과 과거 보존

승인 목표의 단일 설정은 `docs/project-settings.json`이다. 실제 구현은 `docs/current-implementation.json`의 코드/빌드 근거 관측으로 구분하며 승인 상태를 부여하지 않는다. 과거 설정·baseline·원장은 `.harness/v1/settings-correction/history/`와 기존 불변 artifacts에 보존한다. 기존 보고서·ZIP·시험 결과·리뷰 payload는 덮어쓰지 않는다. 기존 PASS는 당시 기능·표시 범위의 이력이지 정정 목표 준수 근거가 아니다.

## 소비 경로 조사 결과

| 경로 | 실제 동작 | 정정 |
| --- | --- | --- |
| 설치 `project_contract.validate` | 최상위 결정 필드 집합·상태 enum 검사. value 내부 구조·타깃별 UI는 해석하지 않음 | 지원 스키마 유지. UI 전체 상태 UNDECIDED(웹만 미정), value 안에 Android/iOS CONFIRMED·웹 UNDECIDED 명시. 서버 Ktor CONFIRMED |
| 설치 `Tasks.configure_stage` | 현재 설정과 API/정책/실행/인수 문서를 불변 artifact로 동결 | 비활성 BLOCKED 통합 작업은 정정 설정으로 재동결. DONE 작업의 기존 stage/settings snapshot은 역사로 보존 |
| 설치 `gate` / `ready` / `begin` / `handoff` / 통합 `review_gate` | 동결 설정을 읽음. 파일만 고쳐도 과거 snapshot은 자동 변경되지 않음. 기술 value 의미 준수 검사를 수행하지 않음 | 프로젝트 `tools/project_workflow.py`에서 현재 설정/타깃 범위·baseline·snapshot 일치·실행 권한을 선검사. 실제 프레임워크 준수는 전환 후 별도 검증 필요 |
| 설치 `development_tracking` | 입력 baseline·코드 상태·의존 검토의 유효성 추적. CR로 기존 검토를 RECHECK_REQUIRED 표시 가능 | 사용자 정정 CR에 대상 작업·검사를 연결. 과거 원문 PASS 삭제 없이 현재 유효성만 재검토 필요로 표시 |
| `active-baseline.json` | 기존 helper가 ACTIVE 여부 확인 없이 ID/inputs를 읽는 관례 존재 | 과거 ACTIVE를 보관하고 현재 포인터는 정정 목표의 BLOCKED 입력으로 교체. 과거 review ID 승계 금지, 전환 실행 권한 false |
| `.harness/v1` 실행/완료/기능 검토 helper | 고정 run/task ID 및 과거 설정으로 실행·판정 가능 | 제품 실행/검토 helper에 프로젝트 선검사 삽입. 낡은 snapshot 또는 비활성 목표 baseline이면 중단 |
| 상세 보고서/manifest 생성 | 기존 기능 결과와 baseline을 조합 | 과거 상세 보고서 재생성은 비활성 baseline에서 차단. 개편 보고서만 현재 목표·설정 변경 요약을 표시 |
| `try-v1.md` / runbook / Gradle·앱 시험 | 현재 대체 구현의 관측/실행 방법. 설정을 읽어 UI/Ktor로 바꾸는 도구가 아님 | 과거 구현 체험/시험과 목표 구현 검토를 구분. 직접 기존 앱 실행 성공을 목표 준수 승인으로 사용 금지 |

설치 하네스에는 기술 목표 의미 비교·타깃별 UI 자동 게이트·동결 설정 자동 전파가 없다. 설치본을 고치지 않고 프로젝트 진입 지침/검사기로 경계를 보완한다. 직접 설치 API를 우회 호출하면 프로젝트 규칙을 우회할 수 있으므로 이를 전역 보안 강제로 설명하지 않는다. 프로젝트의 공식 실행·검토 경로에서는 검사기를 사용한다.

## 타깃별 설정과 권한

공식 경로는 `tools/project_workflow.py`다. 모바일만 보는 UI 검토에는 원본 설정에서 android/ios만 투영한 **파생 입력**을 사용할 수 있다. 승인 목표를 별도로 편집하는 두 번째 설정 원장을 만들지 않는다. 이 입력은 부모 설정 SHA·선택 타깃을 기록하며 부모 변경 시 낡은 입력으로 거부된다. 웹 포함 UI/전체 통합은 웹 UI 미정 때문에 거부된다. 서버 단계는 웹 UI 결정을 요구하지 않지만 이번에는 전환 구현 착수 권한 자체가 없으므로 제품 begin/ready/review/인계를 모두 차단한다. 설정 정합성 검사·읽기 전용 이력 열람은 가능하다.

새로운 제품 실행은 이후 명시적으로 허용된 범위에서 현재 목표·설정·설계 입력을 다시 동결하고 영향받는 작업을 새로 검토한 뒤 수행한다. 이 문서나 정합성 PASS는 그 실행 허가가 아니다.

## 검증 기준

- 지원된 설정 스키마 통과, 목표 값에 View/SwiftUI/HttpServer 없음, 관측 사실에는 기존 구현과 코드 해시 보존.
- 모바일 투영의 Compose 목표는 확인되고 웹 포함 UI는 UNDECIDED로 차단. 서버 기술은 Ktor로 로드되며 웹 미정과 분리.
- 과거 동결 설정을 가진 실행/검토는 거부. 현재 동결 설정이어도 BLOCKED baseline/권한 없음이면 제품 실행 거부.
- 비활성 통합 태스크를 재구성하되 실행하지 않음. 과거 review payload/출력/실행은 보존, CR로 현재 유효성 재검토 필요.
- 설정·문서·현재 baseline의 참조/해시 일치. 개편 HTML은 변경점·남은 웹 결정만 짧게 갱신. 제품 소스/빌드/설치본/기존 ZIP 보호 해시 변경 없음.
- 실제 제품 전환 후 Ktor/CMP/모듈 준수 및 필수 상태/기능 검증은 NOT_RUN. 비용/사용량과 현재 응답 Stop 수집 결과는 UNKNOWN.
