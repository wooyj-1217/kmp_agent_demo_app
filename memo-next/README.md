# 틈 · Teum

생각을 쓰고, 세 기기에서 이어 보는 개인 메모앱. 이번 요청을 바탕으로 `memo-next/`에 새로 작성했다. 이전 앱의 Git 이력·코드·디자인·명세는 입력으로 사용하지 않았다.

## 실행

Python 3.10 이상으로 저장소 루트에서 실행한다. 외부 Python 패키지는 없다.

```sh
python3 memo-next/server/app.py
```

Web: <http://127.0.0.1:8910>. ‘새 메모’ → ‘계정 만들기’로 개인 계정을 만들고 사용한다. 연결했던 브라우저에서는 이후 오프라인으로 열고 편집할 수 있다. 브라우저 저장 데이터를 지우면 서버에 아직 전송하지 않은 변경은 복구할 수 없다.

기본 서버는 localhost에만 바인딩한다. 외부 기기에서 사용할 때는 HTTPS 역방향 프록시와 서버 주소가 필요하다. 앱의 ‘나’ → ‘내 서버 연결’에 해당 HTTPS 주소를 입력한다. 공개 서버·도메인·스토어 배포는 이번 작업에서 실행하지 않았다.

## Android

JDK 17, Android SDK 35, Gradle 8.14.3을 사용한다. 공식 Gradle 도구로 이 프로젝트 전용 래퍼를 새로 생성했으며 이전 앱의 래퍼를 복사하지 않았다. `memo-next/local.properties`에 개발 환경의 `sdk.dir`을 지정하거나 `ANDROID_HOME`을 설정한다.

```sh
cd memo-next
./gradlew :android:assembleDebug
adb -s emulator-5562 install -r android/build/outputs/apk/debug/android-debug.apk
adb -s emulator-5562 shell am start -n app.teum.memo.debug/app.teum.memo.MainActivity
```

에뮬레이터의 기본 서버는 `http://10.0.2.2:8910`이다. 실기기는 같은 개발 PC의 HTTPS 주소를 연결한다. 디버그의 가상 로컬 문서는 HTTP, 릴리스는 HTTPS origin을 사용한다. 혼합 콘텐츠 허용을 켜지 않는다. 파일 접근·임의 외부 페이지 이동도 차단한다.

## iOS

새 Xcode 프로젝트 생성기는 현재 디렉터리의 새 Swift 파일과 공통 Web 리소스만 참조한다. iOS 16 이상을 대상으로 한다.

```sh
python3 memo-next/tools/create_xcode_project.py
cd memo-next
xcodebuild -project ios/Teum.xcodeproj -scheme Teum -sdk iphonesimulator -configuration Debug -derivedDataPath ios/DerivedData CODE_SIGNING_ALLOWED=NO build
```

Xcode에서 `ios/Teum.xcodeproj`를 열어 실행해도 된다. 시뮬레이터 기본 서버는 `http://127.0.0.1:8910`이다. 실기기 서명·배포는 별도 Apple 개발 팀 설정이 필요하다.

## 구현과 데이터

- `web/`: 공통 반응형 화면·기기 저장·동기화 큐·오프라인 Web 셸. 서버 데이터는 서비스 워커 캐시에 저장하지 않는다.
- `android/`, `ios/`: 공통 화면을 로컬에 번들하는 네이티브 앱과 파일 내보내기 브리지. Kotlin Multiplatform 프로젝트나 이전 소스는 재사용하지 않았다.
- `server/app.py`: 계정·세션·개인 메모 API, SQLite 트랜잭션, 정적 Web 제공.
- 기기 캐시는 서버 주소와 사용자 ID로 분리한다. 비밀번호는 서버에 scrypt 해시로 저장하며, 세션 토큰도 서버에는 해시만 저장한다. 세션 유효기간은 30일이다.
- 동기화는 서버 버전 기준이다. 오래된 버전에서 수정하면 원본을 덮지 않고 ‘충돌 사본’을 생성한다. 최신 편집을 대상으로 한 오래된 영구 삭제 요청은 거절한다.
- 삭제는 휴지통으로 이동하며 복원할 수 있다. 영구 삭제는 확인 후 본문을 지우는 tombstone으로 전파한다. 브라우저·OS·서버 백업의 사본까지 암호학적으로 삭제한다고 보장하지 않는다.

서버 계약: [contract.md](../docs/memo-independent/contract.md). 검증: [verification.md](../docs/memo-independent/verification.md).

## 검사

```sh
cd memo-next/server
python3 -B -m unittest -v test_app
cd ../..
node --test memo-next/web/test_client.cjs
```

네이티브 통합 검사는 localhost의 일회용 QA 데이터에만 실행한다. `python3 memo-next/tools/create_qa_account.py`가 테스트 계정을 준비한다. 이 도구에 있는 테스트용 비밀번호는 제품의 기본 계정이나 실사용 인증정보가 아니다. QA 계정 준비 도구와 해당 계정을 운영 서버에 적용하지 않는다.

```sh
cd memo-next
./gradlew :android:assembleDebug :android:assembleDebugAndroidTest
adb -s emulator-5562 install -r android/build/outputs/apk/debug/android-debug.apk
adb -s emulator-5562 install -r android/build/outputs/apk/androidTest/debug/android-debug-androidTest.apk
adb -s emulator-5562 shell am instrument -w -r app.teum.memo.debug.test/android.test.InstrumentationTestRunner
xcodebuild -project ios/Teum.xcodeproj -scheme Teum -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -derivedDataPath ios/DerivedData CODE_SIGNING_ALLOWED=NO test
```

## 현재 운영 범위

개인용 첫 구현이다. 이메일 인증·비밀번호 재설정·계정 삭제·관리 도구·백업 자동화·종단간 암호화는 현재 미구현이며, 각각을 사용자가 명시적으로 제외했다고 해석하지 않는다. 기기 저장소와 세션 토큰은 OS/WebView 저장소에 보관한다. HTTPS 프록시 및 운영 디스크 암호화·접근 권한은 호스팅 환경에서 설정해야 한다. 자동 동기화는 화면이 열려 있을 때 실행되며 OS 백그라운드 작업을 등록하지 않았다.

동일 브라우저의 여러 탭에서 동시 편집하는 동작은 현재 보장하지 않는다. 세 기기의 독립 저장소 간 동시 편집은 서버 revision·충돌 사본으로 처리하도록 구현했다. 현재는 개인 메모 규모를 위한 전체 스냅샷 동기화이며, 대규모 데이터의 커서·페이지 동기화는 미구현이다. 이 항목들은 현재 구현·검증 한계이며 별도의 사용자 제외 승인으로 간주하지 않는다.

네이티브 로컬 콘텐츠 로딩 기준은 [Android 공식 가이드](https://developer.android.com/develop/ui/views/layout/webapps/load-local-content), [Apple WKWebView API](https://developer.apple.com/documentation/webkit/wkwebview/loadfileurl(_:allowingreadaccessto:))를 확인했다.
