# 완료 증거·병렬 소유권·재개 신뢰성 보강

- 요청: pstack 기준 커밋 4dd1d05818d19792e7cd6e818f1667f95f7e1dbe 조사 후 공통 구현·로컬 검증.
- 상태: 공통 로컬 구현·선별 회귀·독립 검토 완료. 미배포·앱 미적용.
- 실제 task/native turn/원문 ID: UNKNOWN. 사후로 착수 게이트 통과나 수집 완료를 주장하지 않는다.
- 공통 기준: c2b5a52의 메모리 정책 후속 커밋 2ef4b0e29020025a391ebae35145d31183610dfc.
- 최종 로컬 공통 커밋: a5b4a416e41eaecac2cc226b9c36df06bc7dc7ad.
- 보존 작업본: `.harness/pstack-reliability/source`, 브랜치 `improve/verification-reliability`.
- 원본 공통 저장소와 이 앱의 기존 미커밋 변경은 포함·덮어쓰기하지 않았다. 원본 공통 저장소에서 작업 도중 별도 설치/예제 변경이 추가 관측됐으며 이번 커밋 범위 밖이다.

## 범위와 선택

앱 제품 기능·서버 동기화·선택 설치 버전 변경은 범위 밖이다. 공통 task·artifact·agent_run·validation_status·event·QA 경로를 재사용했다. 설치 releases를 수정하지 않고 격리 clone에서 구현했다. 구현 전 요구 대응표와 현재 사용법은 [공통 운영 명세](../../../.harness/pstack-reliability/source/docs/verification-reliability.md)에 있다.

pstack의 프로젝트별 Launch/Doctor/Drive/Evidence/Cleanup/Feature map, 작업별 쓰기 소유권, 재개 시 실제 산출물 대조만 선별했다. 역할·모델 기본값·상태 DB·버전 체계를 추가하지 않았다. 기존 메모리·의사결정·raw log 분리 정책을 유지했다. 기존 보관·복구 도구는 실제 채택돼 있지 않았으므로 있다고 주장하지 않고 로컬 frozen artifact/SHA 검사와 복구 가능 진단을 연결했다. 기존 증거의 삭제·이동·원격 전송은 하지 않았다.

## 변경과 중요 실패 수정

- 실행 전 고정 계약에 목표·입력·의존·쓰기/금지 범위·기준별 검증 방법/플랫폼/증거·통합 책임을 연결한다. 프로젝트 필수 정책은 신규 task에 상속한다.
- 기준/작업/검토 실행·입력·작업트리·환경·명령/조작·기대/관찰·실제 증거를 연결한다. 기준 하나의 receipt를 다른 기준 PASS로 재사용하면 거부한다.
- 독립 검토에서 필수 플랫폼을 요구사항 문서 검토로만 충족하는 우회를 재현했다. 필수 execution criterion 연결을 요구하도록 수정하고 재시험했다.
- 실행 중 자원 선언 변경으로 다른 기기 소유권을 가져가는 우회를 재현했다. 원장 lock 안의 live 변경·begin·resume 검사를 연결해 차단했다.
- code_paths 밖 금지 파일을 수정하고 허용 출력만 제출하는 우회를 재현했다. 기존 전체 로컬 파일 snapshot 시작/제출 대조로 보완했다.
- 일부 실행 조회에서 과거 PASS를 필수 N/N으로 표시하는 문제를 수정하고 회귀를 추가했다.
- 기존 격리 QA에 플랫폼별 실제 관찰의 증거 복사·receipt 생성을 연결했다. generic PASS만으로는 계약 작업이 완료되지 않는다.
- 유효한 완료만 재개 시 skip한다. 코드·기준·환경·증거가 다르면 과거 리뷰는 보존하고 RECHECK_REQUIRED를 표시한다.
- 동일 원인 키의 반복 지적은 한 issue의 history에 보존한다. CONFIRMED/SUSPECTED를 구분한다.

## 검증

총 130개 고유 시험 통과: 핵심 task/재개/dashboard/QA/계약/절차/소유권 94, 일부 조회 표시 추가 회귀 1, 설치·init·update 20, 개발 추적 11, 대표 병렬·통합/소유권 회귀 4. 독립 검토자의 중복 시험 수는 더하지 않았다.

명령은 `rtk proxy python3 -B -m unittest`로 해당 모듈/개별 시험을 실행했다. `harness.test_tasks`, `test_interruptions`, `test_dashboard`, `test_qa`, `test_verification`, `test_verification_procedure`, `test_execution_ownership`, `test_installation`, `test_development_tracking`와 `test_delegation`의 disjoint workers, failed integration, identical path, shared configuration 시험을 포함한다. JS 두 파일 node --check 및 git diff --check도 통과했다.

최종 로컬 커밋을 별도 합성 Git 프로젝트에 설치·init·명시 update하고 설치된 주요 6개 파일 해시를 확인했다. 제품 파일 보존 확인. 실제 앱 선택 설치는 건드리지 않았다.

합성 대표 작업을 시작→제출→별도 검토→DONE→재개 skip까지 수행했다. 브라우저에서 목표·단계·필수 2/2·다음 인계를 관찰했다. 자신이 시작한 대시보드 서버만 종료하고 증거/receipt 4개가 여전히 hash-valid임을 확인했다. 초기 현재 대시보드 8782는 연결 거부 상태였으며 설치 서버를 임의 재시작하지 않았다.

긴 전체/복수 suite 실행은 중단했으므로 전체 회귀 PASS로 계산하지 않는다. 잠금 안 development_tracking.capture/Git 대기를 관측했으나 무한 교착이나 이번 변경의 결함으로 확정하지 않았다. 필요한 대표 delegation 4개는 별도 실행해 모두 통과했다.

모두 합성·임시 Git/명령 시험이다. 실제 앱 Android/iOS/Web/Server 사용자 경로, 확장 QA schema의 실제 신규 모델 실행, 앱 startup/hook 재로드, 전체 harness 회귀는 미검증이다.

로컬 근거: `.harness/pstack-reliability/validation.json`, `source-manifest.json`, `install-smoke-result.json`, `representative/`. 원본 증거는 Git·PR·원격에 업로드하지 않았다.

## 맥락 검토와 적용

실제 맥락 정리 서브에이전트가 공통 명세 두 문서를 갱신했다. 메인이 내용·diff를 검토해 수락하고 QA/작업 관리 진입 링크와 명시적 제한을 보완했다. 별도 독립 검토가 세 우회의 수정과 최종 표시 회귀를 확인했다. 담당 결과를 사용자 승인으로 대체하지 않는다.

앱 선택 설치는 799a4a529621f393e8566669ed9fecbe60aac018, startup NOT_RUN/runtime RESTART_REQUIRED를 유지한다. 이후 공통 커밋/릴리스를 명시 선택해 설치한 뒤 프로젝트가 절차·환경·필수 작업 종류 정책을 구성하고 새 세션에서 확인해야 한다. 기존 task는 소급 인증하지 않는다.

코드는 구조·해시·명시적 주체 분리·같은 원장의 관리 경로를 검사한다. actor_id는 실제 OS/모델 신원 증명이 아니며 환경 파일의 최신성·증거 내용의 의미·raw shell·다른 원장/외부 프로세스·제품별 기대의 타당성은 담당 절차에 의존한다. 장기 보관·자동 복구는 구현하지 않았으며 복구 불가를 명시한다. 이 경계를 실제 제품 완료나 배포 완료로 확대하지 않는다.
