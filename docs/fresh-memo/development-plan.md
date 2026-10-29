# 여백 신규 개발 계획

## 입력·독립성

사용자 새 개발 요청과 iOS·Android·Web 결정을 `request.md`에 보존한다. `requirements.md`와 독립 요구 검토, `design.md`의 QA 후 선택안을 입력으로 삼는다. 과거 제품 코드·기획·테스트는 읽거나 가져오지 않는다. 기존 Kotlin/Gradle/Android SDK/Xcode는 실행 도구로만 사용한다. 기존 src와 iOS 호스트 구현은 `.harness/fresh-memo/discarded`로 이동하여 활성 빌드에서 제외한다. 소스 폐기는 사용자 원문 요청으로 승인된 범위다. 기존 Git 이력·로깅·하네스는 제품 구현과 분리하여 유지한다.

## 기술·모듈과 소유

- `shared`: 새 순수 Kotlin 모델·정렬/검색/CRUD·트랜잭션 저장 계약·버전 코덱. UI·플랫폼 API 의존 없음. 독립 공통 개발 담당이 새로 작성한다.
- `composeApp`: 새 Compose Multiplatform UI와 Android/iOS/Wasm 진입·플랫폼 저장 어댑터. 메인 개발 담당 소유. 세 타깃에서 같은 UI/로직을 공유하되 작은 화면은 목록↔편집, 넓은 화면은 목록+편집으로 대응한다.
- `iosApp`: SwiftUI가 새 Compose view controller를 호스팅. 기존 Xcode 프로젝트의 도구 설정만 사용하고 Swift 소스/테스트는 새로 작성한다.
- 서버: 없음. 기기 로컬 저장이며 로그인·원격 API·동기화는 제공하지 않는다.
- 기술 버전: 설치되어 있는 Kotlin 2.2.10, Compose 1.9.0, AGP 8.10.0, JDK 17. Android API 24 이상, iOS 15 이상, Wasm GC 지원 최신 Chrome을 우선 검증한다. Safari/Firefox 실제 실행은 별도 결과 없이 지원 검증 완료로 주장하지 않는다.

명시적 생성자 주입으로 UI에 MemoRepository를 전달한다. 저장소 구현은 플랫폼 진입점에서 조립한다. 외부 DI 프레임워크는 필요하지 않다. 하네스의 모듈 예시는 소규모 로컬 앱에 자동 적용하지 않으며 위 경계를 실제 제품 구조로 택한다.

## 저장·오류 계약

`MemoStorage.read(): String?`, `write(String): Unit`에서 실패는 예외. `MemoRepository(storage, now, nextId)`는 로드 실패를 빈 데이터로 바꾸지 않는다. 모든 변경은 새 스냅샷 직렬화→영속 쓰기 성공→메모리 교체 순서다. 실패 시 초안·목록·기존 저장본을 유지하고 UI에서 같은 동작 재시도 가능하다. 처음 로드 실패 시 작성 UI를 열지 않고 재시도만 제공한다. 버전 코덱은 길이를 포함하여 임의 줄바꿈/한글/이모지/구분자를 보존한다. 손상·중복 ID·알 수 없는 버전은 거절한다.

Android는 새 이름의 private SharedPreferences에 동기 commit 성공 확인, iOS는 새 이름의 Documents 파일 원자적 쓰기, Web은 새 키의 localStorage를 사용한다. 과거 앱 데이터 마이그레이션 없음. Web은 자원 캐시를 두어 최초 방문 후 오프라인 재실행을 검증한다. 파일 원자성과 메모리 변경 순서가 중요하며 실패 주입으로 확인한다.

## 의존과 실행 순서

1. 독립 기획 검토: 원문 의미·범위 정책·AC. 실제 결과는 `.harness/fresh-memo/requirements-review.md`.
2. 독립 디자인 QA: 화면·상태·인터랙션·데스크톱/모바일 렌더 검토. 실패 시 시안 보완과 재검토. QA 종료 후 위임받은 디자인 선택을 확정한다.
3. 독립 개발 계획 검토: 모듈 경계·소유 파일·선행 의존·명령·검증 환경. 앞 단계 PASS가 이 단계 PASS를 대신하지 않는다.
4. 공통 모델·저장과 플랫폼 UI 구현. 공통 도메인 구현은 UI와 파일 소유가 겹치지 않는다. 통합 빌드는 shared API 완료 후 수행한다. 실제 플랫폼 저장/입력 확인은 빌드 성공 후다.
5. 독립 구현 QA→결함 담당 보완→영향 범위 재검증. 테스트 성공만으로 미실행 타깃까지 완료시키지 않는다.

공유 자원: Gradle 캐시·에뮬레이터·iOS Simulator·웹 로컬 포트. Gradle/Xcode의 framework 생성은 같은 출력 디렉터리를 사용할 수 있으므로 동시 빌드하지 않는다. 이전 제품의 근거/스크린샷은 새 검증에 사용하지 않는다.

## 검증 명령·범위

프로젝트 루트에서 JDK 17로 실행한다. 아래는 계획이며 실행 결과는 별도 로그에 기록한다.

```sh
rtk proxy env JAVA_HOME=/Users/glowdayz/Library/Java/JavaVirtualMachines/jbr-17.0.12/Contents/Home ./gradlew :shared:jvmTest :composeApp:assembleDebug :composeApp:wasmJsBrowserDistribution --console=plain
rtk proxy env JAVA_HOME=/Users/glowdayz/Library/Java/JavaVirtualMachines/jbr-17.0.12/Contents/Home ./gradlew :composeApp:connectedDebugAndroidTest --console=plain
rtk proxy xcodebuild -project iosApp/Moa.xcodeproj -scheme Moa -configuration Debug -destination 'platform=iOS Simulator,id=6BE99913-C130-4D86-B7C4-95F4DDC8C790' -derivedDataPath .harness/fresh-memo/ios-derived CODE_SIGNING_ALLOWED=NO test
```

실제 기기 ID는 실행 전 연결 목록으로 확인하며 바뀌면 실행 기록에 남긴다. Xcode 프로젝트/스킴 이름은 기존 빌드 도구명이며 제품명은 여백이다. 웹은 새 distribution을 별도 로컬 포트에서 서비스하고 실제 Chrome으로 1440×900·390×844를 검증한다. UI 조작은 cua_repl만 사용한다.

- JVM: 원문 보존·빈 입력·검색·고정 순서·삭제복원·영구삭제·실패 후 재시도·재로드·손상 코덱. AC-001~009.
- Android/iOS: 설치/기동·메모 작성/재열기·재기동 유지·미저장 확인·검색·고정·휴지통/복원, 키보드/안전 영역. UI 테스트와 실제 렌더 캡처를 분리. AC-001~010.
- Web: 같은 CRUD와 새로고침, 브라우저 뒤로·미저장 확인·검색 결과 없음·키보드 탐색/단축키·좁은 화면·오프라인 재실행. 저장 실패는 도메인 실패 주입과 플랫폼 오류 표현으로 구분. AC-001~010.
- 최종 독립 코드 QA: 새 요구/디자인/실제 코드와 테스트 결과 대조, 위험과 미검증 환경 명시.

## 완료와 인계

코드는 미커밋 작업본으로 경로·해시와 실행 근거를 고정한다. 자동 Git commit/tag/push/배포하지 않는다. 최종 인계는 새 소스·실행법·각 플랫폼 결과·독립 QA와 발견 결함 보완 근거를 포함한다. 빌드/제한 시험/실제 플랫폼 실행/제품 전체 완료를 구분하며 NOT_RUN을 PASS로 바꾸지 않는다.
