# kmp_agent_demo_app 진입 지침

이 저장소는 제품·검증 근거를 관리하며 공통 하네스는 /Users/glowdayz/Projects/kmp_agent를 참조한다. 하네스를 복사하지 않는다.

- 하네스 진입: [AGENTS.md](../kmp_agent/AGENTS.md). 거기에 적힌 하네스 저장소 편집 범위를 제품 작업 금지로 전용하지 않는다. 현재 사용자 요청의 작업 범위를 따른다.
- 역할 선택: [역할 목록](../kmp_agent/docs/roles/README.md)에서 현재 역할 문서만 읽는다. 전체 역할을 매번 읽지 않는다.
- 공통 판단·버전: [운영 설계](../kmp_agent/docs/operations.md).
- 실행·환류: [작업 관리](../kmp_agent/docs/task-management.md#demo-feedback).
- 제품 지침: [docs/product.md](docs/product.md), 이후 기능별 requirements.md·design.md와 플랫폼 지침.
- 발견 기록: [docs/feedback.md](docs/feedback.md).

실행 전 하네스 Git 커밋과 제품 기준 커밋, dirty 여부·사용 파일/해시·변경 근거를 고정한다. 커밋 없음은 UNKNOWN이며 미커밋 파일을 커밋된 버전으로 표현하지 않는다.
지침 충돌은 영향 범위와 근거를 기록하고 위 환류·운영 기준을 따른다. 제품 목표·핵심 정책·범위는 임의 변경하지 않는다.
현재는 저장소 연결 문서와 메모 MVP 기획·검토 문서를 작성했다. 제품 기능·시안·독립 자동 호출·PR 연동을 구현했다고 표현하지 않는다.

종료·인계 시 수행 Codex가 [제품 시행착오](docs/retrospective.md)를 [공통 기록 기준](../kmp_agent/docs/task-management.md#retrospective)에 따라 갱신한다. 중단으로 누락하면 재개 후 확인 가능한 근거로 보완하고 사용자 메모를 보존한다. 프로그램 자동 생성은 미구현이다.
