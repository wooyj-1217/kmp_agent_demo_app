# v1 기술 결정 — SRC-005 위임에 따른 선택

모든 선택은 기존 D-001~004·U-001·세 플랫폼·KMP 방향을 유지하는 가역적 구현 판단이다. 현재 Codex가 서버·공유·웹·Android·iOS를 순차 담당하며 독립 에이전트 실행으로 표현하지 않는다.

| 영역 | 선택·이유 | 소유 경계·검증 |
| --- | --- | --- |
| 빌드 | Kotlin 2.2.10·Gradle 8.14.3·JDK 17, Android AGP 8.10.0 | Kotlin 공식 호환표의 2.2.0~2.2.10/Gradle 8.14/AGP 8.10.0 범위 사용. 패치 호환은 실제 빌드로 확인 |
| 공유 | shared KMP의 순수 domain(검증·글자 분할)·api DTO·client 저장 상태 전이, JVM·JS·iOS 프레임워크. Android는 JVM 산출물 사용 | Domain은 UI/HTTP/DB/DTO 의존 없음. 공통 Unicode 16 테이블·분할 알고리즘으로 클라이언트/서버 길이 일치. 공유 UI는 채택하지 않음 |
| 서버 | Kotlin/JVM + JDK HttpServer, SQLite JDBC 3.50.3.0, kotlinx.serialization JSON 1.9.0 | 작은 로컬 API의 추가 프레임워크/DI 비용을 줄임. Ktor는 이번에 채택하지 않으므로 참조 구조를 강제 복제하지 않음. server 모듈이 HTTP·저장·수동 DI 소유 |
| 영속성 | SQLite 한 트랜잭션 안에 메모·시도 키 저장, UNIQUE 키, prepared statements, 시도 정보 만료 없음 | 동일 요청의 경합·응답 유실·서버 재시작을 실제 테스트. DB 스키마 user_version=1; 호환 불명 버전 시작 거부 |
| 웹 | Kotlin/JS IR + DOM, 기존 디자인 CSS 재사용 | 가상 DOM/Compose 추가 없이 브라우저 기본 레이블·버튼·dialog 사용. API와 같은 로컬 origin. localStorage에는 저장 시도만 보존, 일반 초안 저장 안 함 |
| Android | Kotlin Android + 기본 View UI, HTTP는 플랫폼 API | 공통 검증·상태 모델 사용, SharedPreferences에 저장 시도만 보존. SDK/기기 실행 여부 별도 기록 |
| iOS | SwiftUI + KMP Shared 프레임워크, URLSession | 공통 검증·상태 모델 사용, UserDefaults에 저장 시도만 보존. Xcode 미설치 환경은 빌드/장치 검증 NOT_RUN |
| 통신 | API DTO만 kotlinx.serialization, 플랫폼 HTTP 어댑터를 진입점에서 조립 | HTTP/DB/플랫폼 저장을 순수 업무 로직 밖에 둠. 어댑터 결과는 확실한 미저장/불확실 구분 |
| 범위 | 로컬 loopback 서버·전체 목록, 인증·페이지 분할·검색·수정·삭제 없음 | 기존 MVP 제외 범위 유지. 지원 브라우저 검증 시작점은 실제 연결 Chrome, 버전은 관측 보고서에 고정 |

공식 근거: [KMP 호환표](https://www.jetbrains.com/help/kotlin-multiplatform-dev/multiplatform-compatibility-guide.html), [Kotlin/JS](https://kotlinlang.org/docs/js-overview.html), [Unicode 16 UAX #29](https://www.unicode.org/reports/tr29/tr29-45.html), [SQLite 트랜잭션](https://www.sqlite.org/lang_transaction.html), [JDK HttpServer](https://docs.oracle.com/en/java/javase/17/docs/api/jdk.httpserver/com/sun/net/httpserver/HttpServer.html). 최신 릴리스를 추정 채택하지 않고 위 버전을 고정한다. 실제 빌드 전에는 빌드 성공을 주장하지 않는다.
