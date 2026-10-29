# kmp_agent_demo_app

Android·iOS 대상 KMP 메모 MVP의 기획 및 검증 근거를 관리한다. 공통 하네스 진입은 [AGENTS.md](AGENTS.md)를 따른다.

`master`는 **제품 구현이 없는 비교 기준 브랜치**다. kmp_agent 버전별 구현은 이 브랜치에서 새 브랜치를 만들어 진행한다. 이전 메모 앱 구현은 [`demo/agent-0.2.0`](https://github.com/wooyj-1217/kmp_agent_demo_app/tree/demo/agent-0.2.0)에 보존했다. 삭제 범위·보존 대상·과거 기록 해석은 [비교 기준 안내](docs/master-baseline.md)를 따른다.

- [제품 기획](docs/product.md) · [목록 요구사항](docs/features/memo-list/requirements.md) · [작성·저장 요구사항](docs/features/memo-create/requirements.md)
- [기획 검토](docs/planning-review.md): 문서 검토 PASS, 실제 앱 검증 NOT_RUN.
- [디자인 시안 열기·검토 안내](docs/design/README.md) · [목록 시안](docs/features/memo-list/prototype/index.html) · [작성 시안](docs/features/memo-create/prototype/index.html): 명세 COMPLETE, 시안 동작 확인 대기, 시각 검토 NOT_RUN.
- [후속 작업과 의존성](docs/roadmap.md): 디자인 → API 계약·개발 준비 → 작업·PR 분해 → 구현·검증.
- [피드백](docs/feedback.md) · [제품 시행착오](docs/retrospective.md): 발견 근거와 개선 결과.

기획 기준 버전은 기획 문서들을 포함하는 Git 커밋이며, 실제 해시는 작업 관리 기록에 연결한다. 현재 승인 기술·모듈 목표는 [project-settings.json](docs/project-settings.json)과 [목표 구조](docs/target-architecture.md)를 따른다. 과거 구현·시험·PASS는 버전별 새 구현의 완료 근거로 승계하지 않는다.

공통 하네스는 `git@github.com-study:wooyj-1217/kmp_agent.git`의 `v0.2.0` 고정 설치를 사용한다. 설치 SHA·프로젝트 ID는 `.kmp-agent/installation.json`에 보존한다. 상태 확인: `rtk proxy python3 .kmp-agent/agent.py status`. 최초 적용 후 `/hooks`에서 두 수집 훅을 신뢰하고 새 Codex 세션의 일반 요청으로 자동 수집을 검증한다.
