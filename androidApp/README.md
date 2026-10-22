# Android 로컬 빌드

루트에서 `rtk proxy ./gradlew :shared:jvmJar` 후 `rtk proxy ./gradlew -p androidApp assembleDebug`. Android는 루트 KMP 플러그인과 AGP 클래스 로더를 분리한 별도 Gradle 빌드다. 루트의 초기 제안 `-Pandroid :androidApp:assembleDebug`는 현재 지원하지 않으며 실패 기록을 보존한다. `local.properties`에 sdk.dir 또는 ANDROID_HOME을 사용한다. APK는 build/outputs/apk/debug.

서버 127.0.0.1:8080 실행 후 대상 시험 장치에 `adb reverse tcp:8080 tcp:8080`, APK 설치·실행. `tools/verify.py`는 이번 전용 emulator-5554 한 대만 있을 때 계측 검증하며 일반 사용자 장치 설치용이 아니다. 공통 JVM jar를 새로 빌드하지 않으면 이전 jar를 쓸 수 있으므로 위 순서를 지킨다.

2026-10-20: SDK35·AGP8.10.0·Kotlin2.2.10·Gradle8.14.3 APK와 API36 arm64 시험 AVD의 계측 1건 통과. 실제 키보드/스크린리더/회전·불확실 시도 종료복구 전체는 NOT_RUN. 계측 검증은 View callback을 사용하며 하드웨어 터치/스크린샷 검증과 다르다.
