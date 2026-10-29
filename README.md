# 여백 / YEOBACK

떠오른 생각을 가볍게 적고 다시 찾는 개인용 메모앱. iOS·Android·Web에서 같은 메모 흐름을 제공합니다.

이전 제품 기획·소스·테스트를 입력으로 사용하지 않고 새로 기획하고 구현했습니다. 이전 산출물은 활성 빌드에서 제외했습니다. 개발 도구 설정과 오픈소스 Noto 글꼴만 공용 기반으로 유지했습니다.

기능: 일반 텍스트 메모 작성/편집, 명시적 저장, 제목·본문 검색, 고정, 휴지통·복원·확인 후 영구 삭제. 저장 전 이탈 확인과 실패 후 입력 유지·재시도를 지원합니다. 처음 실행하면 빈 메모함으로 시작합니다.

메모는 기기/브라우저에 저장됩니다. 계정·기기 간 동기화·협업은 제공하지 않습니다. 저장 버튼을 누르기 전 강제 종료한 초안은 복구를 보장하지 않습니다.

## 실행

JDK 17, Android SDK 35, Xcode와 iOS Simulator가 필요합니다.

```sh
./gradlew :shared:jvmTest :composeApp:assembleDebug :composeApp:packageOfflineWeb
./gradlew :composeApp:connectedDebugAndroidTest
```

Android APK: `composeApp/build/outputs/apk/debug/composeApp-debug.apk`.

Web은 `composeApp/build/dist/wasmJs/productionExecutable`을 로컬 서버 또는 HTTPS 정적 호스팅으로 서비스합니다. 서비스 워커를 포함하려면 `packageOfflineWeb`으로 빌드합니다. 최초 로딩과 캐시 설치 후 오프라인 재실행할 수 있습니다. Wasm GC를 지원하는 최신 브라우저가 필요하며 실제 검증 환경은 결과 문서를 확인하세요.

```sh
python3 -m http.server 8092 --directory composeApp/build/dist/wasmJs/productionExecutable --bind 127.0.0.1
```

iOS는 `iosApp/Moa.xcodeproj`의 `Moa` 스킴을 실행합니다. 프로젝트/스킴/프레임워크 이름은 빌드 인프라명이며 실제 앱 이름은 여백, 번들 ID는 `dev.yeoback.app`입니다. Xcode가 Gradle 프레임워크 빌드를 수행합니다. UI 테스트는 별도 로컬 파일에만 기록합니다.

## 새 기준과 구조

- [새 기획](docs/fresh-memo/requirements.md) · [디자인](docs/fresh-memo/design.md) · [QA 후 선택](docs/fresh-memo/selection.md) · [개발 계획](docs/fresh-memo/development-plan.md)
- `shared/src`: 순수 모델·저장 계약·검색/정렬·트랜잭션·코덱·공통 테스트
- `composeApp/src`: 공유 UI와 각 플랫폼 로컬 저장/탐색·진입, Android 계측 테스트
- `iosApp`: SwiftUI 호스트와 iOS UI 테스트
- 원문·기획·디자인·코드 QA 및 실제 실행 근거: 프로젝트 로컬 `.harness/fresh-memo/`

로컬 저장을 위한 외부 서버·API 키 설정은 필요하지 않습니다. 기기 앱 제거 또는 브라우저 데이터 삭제 시 저장된 메모가 사라질 수 있습니다.
