# v1 로컬 실행·검증 안내

> SRC-007: 현재 승인 목표는 project-settings.json/target-architecture.md, 실행 전 검사는 tools/project_workflow.py 및 settings-alignment.md를 따른다. 아래 명령·PASS·구현 설명은 기존 대체 구현의 관측/이력이며 목표 기술 준수 또는 전환 착수 허가가 아니다. 현재 목표 baseline은 BLOCKED다.

아래 명령은 구현 목표이며 실제 실행 결과는 `.harness/v1/`와 작업 원장에 기록한다. JDK17, Gradle wrapper, Android SDK(앱 빌드), 전체 Xcode(iOS)가 필요하다. 설치된 CommandLineTools만으로 iOS를 검증했다고 표현하지 않는다.

- 루트: `rtk proxy ./gradlew :shared:jvmTest :server:test :web:jsBrowserDistribution`.
- 서버: `MEMO_DB=<로컬 DB 경로> MEMO_WEB_ROOT=<web/build/dist/js/productionExecutable> rtk proxy ./gradlew :server:run`. 서버는 127.0.0.1:8080. 포트 선택은 MEMO_PORT. 기본 DB는 실행 cwd의 data/memos.db. 최초 DB는 자동 준비; 알 수 없는 스키마는 중단.
- 웹: 먼저 web distribution을 빌드하고 위 정적 경로를 서버에 지정, 같은 origin의 http://127.0.0.1:8080 접속. 별도 시안 정적 서버와 다르다.
- Android: `rtk proxy ./gradlew -Pandroid :androidApp:assembleDebug`; 로컬 기기는 `adb reverse tcp:8080 tcp:8080` 후 APK 실행. 에뮬레이터도 reverse를 사용해 API 주소를 통일한다.
- iOS: `rtk proxy ./gradlew :shared:linkDebugFrameworkIosSimulatorArm64`, iosApp의 Xcode 프로젝트/설정 후 실행. Xcode·시뮬레이터 없으면 NOT_RUN.
- 시험 DB/장치 데이터는 제품 데이터와 분리. API 응답 유실·서버 재시작·동시 재시도 테스트는 임시 DB/랜덤 포트로 실행. 실패 시 기존 DB는 보존하고 프로세스 종료/재시작, 같은 시도 재확인. 데이터 삭제로 실패를 숨기지 않는다.

환경변수는 위 이름과 경로/포트만 사용하고 비밀값은 요구하지 않는다. 설치/다운로드·빌드 환경 차단은 명령 종료 근거와 함께 남긴다.
