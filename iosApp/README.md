# iOS 로컬 빌드

전체 Xcode와 iOS 시뮬레이터 런타임이 필요하다. `Memo.xcodeproj`의 Memo scheme을 열어 arm64 iPhone simulator에서 실행한다. 공통 KMP 프레임워크는 Build Shared 단계가 실제 현재 소스에서 빌드한다. Debug/Release와 simulator/device 타깃을 구분한다. 장치 서명 팀은 프로젝트에 임의로 설정하지 않는다.

로컬 서버 127.0.0.1:8080이 먼저 필요하다. 시뮬레이터는 같은 Mac의 loopback 서버를 사용한다. 실제 iPhone의 서버 주소·네트워크·서명은 별도 검증 대상이며 현재 설정으로 동작한다고 주장하지 않는다.

일반 초안은 메모리에만 보관한다. 저장 시도 JSON은 Application Support에 원자 기록·fsync 후 공유 SaveMachine.begin을 호출한다. 디스크 정리가 성공한 뒤 공유 상태의 complete/definitelyNotSaved를 호출한다. Kotlin과 Swift 사이 비예외 콜백이 디스크 실패를 감추지 않도록 메모리 어댑터와 확인된 디스크 작업을 분리한다. 잘못된 복구 기록은 삭제하지 않고 새 저장을 차단한다.
