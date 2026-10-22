# 승인된 목표 구조 — SRC-006 / SRC-007

기술·모듈 목표의 기계 판독 원본은 [project-settings.json](project-settings.json)의 ui_technology / server_technology / code_ownership이다. 현재 구현 사실은 [current-implementation.json](current-implementation.json)이며 승인 목표가 아니다. 사용자 원문·권한 경계는 [합의 검토](agreement-review.md).

- Android/iOS: **Compose Multiplatform** UI 방식. 구체 공통 화면/플랫폼 어댑터 설계는 전환 설계에서 정하되 기존 요구/디자인을 보존한다. 기존 View/SwiftUI를 목표로 확정하지 않는다.
- 서버: **Ktor / Kotlin JVM**. 기존 JDK HttpServer는 관측 구현으로만 보존한다. 이번에는 Ktor 라이브러리 추가/버전 변경/서버 교체를 하지 않는다.
- 공통 `model`은 DTO, `domain`은 순수 업무 정책. Domain은 DTO/UI/HTTP/DB에 의존하지 않는다.
- `data-server`, `presentation-server` → `domain-server` → `domain`.
- `data-client`, `presentation-client` → `domain-client` → `domain`.
- server/client 전용 domain끼리 참조하지 않는다. data 경계에서 model DTO와 domain을 매핑한다. 서버/앱 진입점에서 DI하며 특정 DI 라이브러리가 합의됐다고 가정하지 않는다.
- 웹은 동일 API·업무 정책 및 클라이언트 경계를 따른다. **같은 UI 기술·공유 화면 범위에 포함할지만 미확인**이다. Kotlin/JS DOM의 현 구현을 승인 목표로 소급하지 않는다.
- SQLite는 호환 최소안 위임에 따른 선택으로 유지한다. UI/Ktor/모듈 이탈과 같은 결함으로 판정하지 않는다. 데이터/스키마 변경을 계획에 묶지 않는다.

이 문서/정정 설정은 목표 기준이다. 구현 준수 PASS나 전환 착수 허가가 아니다. 현재 baseline은 BLOCKED이고 이전 입력·검토 PASS는 정정 목표에 승계하지 않는다. [설정·실행 연결](settings-alignment.md)과 프로젝트 검사기를 거쳐야 한다.
