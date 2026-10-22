# kmp_agent_demo_app 진입 지침

이 저장소는 제품·검증 근거를 관리하며 공통 하네스는 원격 v0.2.0 고정 설치본 `.kmp-agent/releases/0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55`를 참조한다. 설치 정보는 `.kmp-agent/installation.json`에 보존하며 로컬 개발 원본을 추적하지 않는다.

- 하네스 진입: [AGENTS.md](.kmp-agent/releases/0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55/AGENTS.md). 거기에 적힌 하네스 저장소 편집 범위를 제품 작업 금지로 전용하지 않는다. 현재 사용자 요청의 작업 범위를 따른다.
- 역할 선택: [역할 목록](.kmp-agent/releases/0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55/docs/roles/README.md)에서 현재 역할 문서만 읽는다. 전체 역할을 매번 읽지 않는다.
- 공통 판단·버전: [운영 설계](.kmp-agent/releases/0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55/docs/operations.md).
- 실행·환류: [작업 관리](.kmp-agent/releases/0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55/docs/task-management.md#demo-feedback).
- 원문 자동 수집: [생명주기 수집·저장소별 설정](.kmp-agent/releases/0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55/docs/harness-logging.md#생명주기-수집과-보장-범위). 로컬 .codex/hooks.json이 공용 스크립트를 참조하며 이 저장소의 .harness/logs/에 기록한다. 하네스의 훅 신뢰·테스트 PASS를 데모 적용 PASS로 대신하지 않는다. /hooks에서 데모 정의를 신뢰한 뒤 실제 새 요청으로 확인하며, 수동 로거 호출을 사용자에게 요구하지 않는다.
- 제품 지침: [docs/product.md](docs/product.md), 이후 기능별 requirements.md·design.md와 플랫폼 지침.
- 현재 승인 기술·모듈 목표: [docs/project-settings.json](docs/project-settings.json), [목표 경계](docs/target-architecture.md). `docs/current-implementation.json`과 `.harness/v1/settings-correction/history/`는 관측/과거 이력이며 승인 목표가 아니다. 모바일 Compose Multiplatform·서버 Ktor·전용 모듈 경계는 확정, 웹 UI 범위만 미정이다.
- 제품 실행·검토·인계의 프로젝트 진입: `rtk proxy python3 tools/project_workflow.py check --task <ID> --operation <ready|begin|review|handoff|resume>`. 설치 API/옛 helper 직접 호출로 선검사를 우회하지 않는다. 설정을 바꾼 뒤에도 frozen stage 입력은 자동 갱신되지 않는다. 현재 baseline BLOCKED/전환 실행 권한 없음에서 제품 작업을 시작하거나 과거 PASS를 목표 준수로 승계하지 않는다. 설정 정정·읽기 전용 관측은 제품 전환과 구분한다. 상세: [설정 연결](docs/settings-alignment.md).
- 발견 기록: [docs/feedback.md](docs/feedback.md).

실행 전 하네스 Git 커밋과 제품 기준 커밋, dirty 여부·사용 파일/해시·변경 근거를 고정한다. 커밋 없음은 UNKNOWN이며 미커밋 파일을 커밋된 버전으로 표현하지 않는다.
지침 충돌은 영향 범위와 근거를 기록하고 위 환류·운영 기준을 따른다. 제품 목표·핵심 정책·범위는 임의 변경하지 않는다.
초기 연결 단계에는 문서·기획만 존재했다. 현재 구현 관측은 `docs/current-implementation.json`과 실제 실행 증거로 구분한다. 현재 대체 구현의 존재·부분 기능 PASS를 승인된 목표 구조의 구현 완료로 표현하지 않는다. 독립 자동 호출·PR 연동을 구현했다고도 표현하지 않는다.

종료·인계 시 수행 Codex가 [제품 시행착오](docs/retrospective.md)를 [공통 기록 기준](.kmp-agent/releases/0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55/docs/task-management.md#retrospective)에 따라 갱신한다. 중단으로 누락하면 재개 후 확인 가능한 근거로 보완하고 사용자 메모를 보존한다. 프로그램 자동 생성은 미구현이다.

<!-- kmp-agent:begin -->
공통 하네스 진입: [AGENTS.md](.kmp-agent/releases/0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55/AGENTS.md). 현재 역할에 필요한 지침만 읽는다.
적용 상태: `.harness/integration-status.json`. 원문 수집은 신뢰된 훅이 수행하며 사용자에게 수동 sync를 요구하지 않는다.
<!-- kmp-agent:end -->
