# v1 직접 실행

> SRC-007: 현재 승인 목표는 project-settings.json/target-architecture.md, 실행 전 검사는 tools/project_workflow.py 및 settings-alignment.md를 따른다. 아래 명령·PASS·구현 설명은 기존 대체 구현의 관측/이력이며 목표 기술 준수 또는 전환 착수 허가가 아니다. 현재 목표 baseline은 BLOCKED다.

현재 구현은 로컬 시험용이며 전체 인수 완료 상태는 [검증 현황](v1-acceptance-status.md)을 확인한다. 입력 baseline 커밋 이후 구현은 아직 미커밋이다. 아래 명령은 저장소 루트에서 실행한다. JDK17·Android SDK35·전체 Xcode와 arm64 iOS Simulator가 필요하다. 초기 runbook의 Android `-Pandroid` 명령 대신 아래 별도 빌드를 사용한다.

1. 웹·서버·공통 jar 빌드:

   ```sh
   rtk proxy ./gradlew :web:jsBrowserDistribution :server:installDist :shared:jvmJar
   ```

2. 서버 실행(이 터미널을 열어둔다). 웹·Android·iOS Simulator가 같은 서버/DB를 사용한다. 시험 프록시18080과 구분한다.

   ```sh
   rtk proxy env MEMO_DB="$PWD/data/memos.db" MEMO_WEB_ROOT="$PWD/web/build/dist/js/productionExecutable" server/build/install/server/bin/server
   ```

   브라우저에서 **http://127.0.0.1:8080/** 접속. 최초에는 빈 목록이며 본문을 저장하고 새로고침하면 같은 메모를 조회한다. 서버를 Ctrl+C로 종료한 뒤 같은 명령으로 재실행하면 같은 DB를 사용한다. 8080을 다른 프로세스가 사용하면 임의 종료하지 말고 해당 서버를 확인한다.

3. Android: `rtk proxy ./gradlew -p androidApp assembleDebug`. `rtk proxy adb devices`에서 실행 대상 ID를 직접 고르고 아래 `<기기ID>`를 치환한다. 연결된 다른 기기에 자동 설치하지 않는다.

   ```sh
   rtk proxy adb -s <기기ID> reverse tcp:8080 tcp:8080
   rtk proxy adb -s <기기ID> install -r androidApp/build/outputs/apk/debug/memo-android-debug.apk
   rtk proxy adb -s <기기ID> shell am start -n dev.memo.mvp/memo.android.MainActivity
   ```

4. iOS: Xcode에서 `iosApp/Memo.xcodeproj`를 열고 **Memo scheme → arm64 iPhone Simulator → Run**. Build Shared 단계가 현재 KMP 프레임워크를 빌드한다. 서버는 위 8080을 켜둔다. CLI 빌드 점검은 `rtk proxy python3 iosApp/tools/verify.py`. 실기기 iPhone 서명·서버 네트워크 연결은 별도이며 현재 실기기 PASS를 주장하지 않는다.

일반 초안은 앱 종료·새로고침 뒤 복원하지 않는다. 저장 중/결과 불확실 시도는 별도로 보존하며, 같은 결과 다시 확인으로 복구한다. 결과가 불확실할 때 앱 데이터/브라우저 저장소를 지워 새 시도를 만드는 방식으로 복구하지 않는다.

## 자동 검증 재현

이미 유효한 결과는 [현황 문서](v1-acceptance-status.md)의 해시·근거를 재사용한다. 아래는 재현이 필요한 경우의 명령이며 전체 PASS를 대신하지 않는다.

- 공통/서버: `rtk proxy ./gradlew :shared:jvmTest :server:test`.
- 전용 장애 fixture: `rtk proxy python3 server/tools/acceptance_fixture.py`. 18080/18081/18082가 비어 있어야 하며 별도 시험 DB를 만든다. 다른 시험이 진행 중이면 함께 실행하지 않는다. Ctrl+C는 이 fixture가 시작한 서버만 종료한다.
- iOS 추가 장애 시험: fixture와8080 서버 실행 후 `rtk proxy python3 iosApp/tools/test.py -only-testing:MemoUITests/MemoUITests/testAcceptanceFaultsAndPersistence`. 전용 시뮬레이터를 생성하고 종료하며 결과 xcresult를 `.harness/v1/`에 보존한다.
- Android 추가 시험: 읽기 전용 Small_Phone 시험 AVD를 emulator-5554로 실행한 뒤 `rtk proxy python3 androidApp/tools/acceptance.py`. 이 스크립트는 대상 이름·부팅을 확인하고 **그 에뮬레이터에만** 설치한다. 실제 전화는 선택하지 않는다. 각 시험 사이 앱 프로세스를 종료해 일반 초안/불확실 시도 재진입을 구분한다.

새 테스트의 통과·실패는 최신 결과 파일로 판정한다. 문서의 명령 존재를 실제 실행 성공으로 간주하지 않는다.
