# 완료 증거 후속: 잠금 진단과 실제 모델 실행

- 요청: 로컬 공통 커밋 `a5b4a416e41eaecac2cc226b9c36df06bc7dc7ad`의 잠금 대기 원인 확인, 실제 모델을 사용한 격리 구현·독립 QA·재검증·재개.
- 상태: 잠금 진단·최소 수정·격리 native 생명주기 확인. 전체 회귀 원본은 실패이며 관측 원인별 재시험은 통과했다. 최종 단일 전체 PASS는 주장하지 않는다.
- 이전 기록: [완료 증거·병렬 소유권·재개 보강](2026-10-30-pstack-verification-reliability.md).
- 실제 run ID: `b29e3b86-02e1-4a2e-af4a-312d528f2d42`. 부모 native session은 `01a18bc6-1472-70c2-93c0-0a8954b458a1`, 부모 turn ID는 호스트 미제공으로 `UNKNOWN`이다.
- 현재 공통 작업본: `.harness/pstack-followup/source`, 로컬 HEAD `f2f00ca5769788e688fcc4016683a2c54600ed6a`(진단·native 실행 핵심 `c50df5381f61456b4fa474fa8ce97d616c77f128` + 표시 수정 + 시험 fixture/기대 상태 수정). 공통 작업본은 clean이다.
- native 프로젝트: `.harness/pstack-followup/native-project`. 마지막 선택 설치·실제 Python 실행 코드는 `c50df5381f61456b4fa474fa8ce97d616c77f128`이다. 뒤의 표시/시험 수정 커밋 전체에서 모델 실행을 다시 했다고 주장하지 않는다.

## 사용자 범위와 유지 사항

사용자는 계획에 그치지 않는 실행·필요 수정과 검증을 요청했다. 로컬 격리 실행만 수행하며 여백 앱의 제품 기능·선택 설치·기존 미커밋 변경은 보존한다. 푸시·태그·배포·병합은 하지 않는다. 이 작은 host CLI 시험의 성공은 Android/iOS/Web/Server 전체 제품 인수 완료가 아니다.

기존 task·agent_run·artifact·validation_status·모델 사용량 연결을 사용한다. 현재 맥락은 이 기록으로 진입하고, 원시 진단·명령/출력·모델 스트림·receipt는 기존 로컬 경로에 보존한다. raw 파일이나 제품 자료를 공통 코드·Git·외부 보관소에 복제하지 않는다.

## 잠금 원인과 재현 근거

기존 `_mutate`는 원장 잠금을 보유한 채 작업 전후의 `development_tracking.refresh`를 실행했다. 과거 리뷰마다 `capture`가 현재 코드를 다시 읽고, 범위 파일 수 F에 대해 파일별 `git show`를 포함한 F+7개의 동기 Git 프로세스를 실행했다. Git 호출과 잠금 획득에는 유한 시간 제한이 없었다. 완료 리뷰가 늘면 상태 조회에서도 같은 검사가 반복되며 다른 조회·실패/중단 처리도 잠금을 기다렸다.

[진단 요약](../../../.harness/pstack-followup/diagnosis.json)은 다음을 구분한다.

| 실행 | 관측 | 해석 |
| --- | --- | --- |
| 원래 병렬 대표 시험 | 70.60초, Git 1,526회, 최대 단일 Git 0.562초, 최대 원장 잠금 대기 1.545초, 종료 0 | 느린 반복 검사·잠금 경합. 자연 교착은 관측하지 못했다. |
| 수정 후 같은 대표 시험 | 77.11초, Git 1,494회, 최대 단일 Git 0.335초, 최대 잠금 대기 0.771초, 종료 0 | 전체 실행이 빨라졌다고 주장하지 않는다. |
| 수정 전 통제 지연 | 자신이 시작한 4초 subprocess를 Git status 자리에 두면 실제 `Tasks.read` 약 5.25초, `Tasks.fail` 약 5.95초 지연 | 잠금 안 외부 대기가 다른 작업·실패 요청을 막는 구조를 재현했다. 자연 발생 Git 정체의 증거는 아니다. |
| 수정 후 통제 지연 | 30초 subprocess를 5초 Git 제한으로 종료. 실제 read/fail 약 5.1초 후 처리, 소유 프로세스 회수·원장 잠금 해제·기존 PASS 보존·RECHECK_REQUIRED 확인 | 유한 대기와 실패 안전성을 확인했다. 즉시 응답이나 OS 전체 중단을 보장하지 않는다. |
| 코드 식별 대조 | 바이너리·개행 파일명·삭제·untracked·staged·mode 변경이 있는 16개 파일에서 식별 필드 동일, Git 23회→8회 | batch화가 기존 코드 상태 식별 의미를 보존함을 확인했다. |

잠금 획득/해제·capture·Git 시작/종료와 시간은 기존 로컬 진단 로그에 기록했다. 소유한 실행 그룹만 종료했다. 순환 잠금이나 외부의 특정 프로세스를 원인으로 확정할 근거는 없으며, 확인한 원인은 반복 동기 검사에 의한 지연·경합과 무제한 외부 대기 가능성이다.

## 공통 수정과 실패 안전성

- 원장·소유권 검사를 잠금 밖으로 옮기지 않았다. Git 기본 5초, capture 예산 15초, 잠금 획득 10초 제한을 두고 오래 걸린 자신 소유 subprocess를 회수한다. timeout을 PASS나 오래된 조회값으로 바꾸지 않는다. 여러 작업을 검사하는 전체 mutation이 항상 10/15초 이내라는 뜻은 아니다.
- immutable HEAD blob을 batch 조회하고, 한 refresh 안에서는 task별 현재 capture를 재사용한다. mutation 전후 캐시는 공유하지 않으며 RECHECK_REQUIRED 과거 결과를 자동 CURRENT로 되살리지 않는다.
- 실제 독립 QA의 기준별 receipt를 구현 owner 완료로 연결하는 경로를 추가했다. 현재 target·입출력·기준별 명시 mapping·방법/플랫폼·절차/환경·실제 native provenance·source receipt와 관찰의 일치를 원장 잠금 안에서 재확인한다. 거부 시 이번 호출이 생성한 review만 실패 종료한다.
- 첫 실제 QA에서 모델이 상태에 설명을 붙여 exact PASS 게이트가 거부했다. 실패 결과를 수정하지 않고 schema의 상태 필드를 enum으로 제한한 뒤 새 QA 실행을 사용했다.
- 실제 원장을 브라우저에서 확인하다 target과 repair owner가 같은 합법적 연결을 자기 부모로 보는 표시 결함을 발견했다. 자기 owner association만 부모 간선에서 제외했다. 실제 순환 탐지·과거 BLOCKED QA·미검증 기준은 유지한다. 원장 SHA를 바꾸지 않고 잘못된 cycle 표시만 사라짐을 확인했다.
- 전체 시험의 정상 handoff fixture가 이미 검토한 요구사항 파일을 helper로 덮어쓰는 오류를 발견했다. 정상 fixture만 문서를 유지하도록 고치고, 실제 변경 시 인계 차단·과거 PASS/증거 보존 회귀를 별도로 추가했다. production 게이트는 약화하지 않았다.

## 실제 모델 실행으로 확인한 단계

기존 `run_codex`·격리 QA 실행 경로를 사용했다. PATH의 CLI 플랫폼 의존성 누락 후 앱에 설치된 실제 CLI를 선택했으며, 첫 subprocess는 app-server 시작 전 실패했다. 성공 모델 세션은 구현 1회와 독립 QA 3회이며, native thread ID와 task·agent_run은 [실행 기록](../../../.harness/pstack-followup/native-run.json)·[버전 연결](../../../.harness/pstack-followup/native-execution-versions.json)에 정확히 연결했다. 없는 식별자를 만들지 않았다.

작은 제품은 이름을 받아 인사하는 host CLI다. 관찰 기준은 현재 허용된 인사 문자열의 정확한 stdout/종료 코드, 이름 누락 시 종료 2·빈 stdout·stderr usage다. schema의 `server` 표기는 이 host CLI 실행 분류일 뿐 실제 서버나 모바일 UI를 검증했다는 뜻이 아니다.

| 순서 | 실제 관측 |
| --- | --- |
| 작업 시작→구현→제출 | 실제 구현 모델이 `src/greet.py`를 변경했다. 자기 보고는 보존하고 정상 Tasks 제출로 IN_REVIEW가 됐다. “독립 QA 대기” 보고는 제품 기준 면제나 완료로 처리하지 않았다. |
| 독립 QA→DONE | 최초 QA-1은 exact 상태 게이트 실패로 BLOCKED다. 새 QA-1-R2가 실제 `Hello, Ada!`와 잘못된 호출을 실행하고 기준별 관찰·증거를 제출했다. 공통 adapter가 receipt를 생성하고 owner TARGET이 DONE이 됐다. |
| 무변경 재개 | 유효한 완료 작업이 skip됐다. |
| 관찰 가능한 코드 변경 | 허용한 작은 변경으로 인사가 `Welcome, Ada!`가 됐다. 과거 owner 리뷰와 QA-1-R2는 보존되며 RECHECK_REQUIRED가 됐다. |
| 과거 PASS 재사용 거부 | 이전 QA target/출력 불일치로 재완료가 거부됐다. |
| 실제 새 모델 QA | QA-2가 변경된 기대 문자열과 오류 경로를 실제 실행했다. 새 증거·receipt로 TARGET이 다시 DONE, 최신 리뷰는 CURRENT다. LIFECYCLE도 DONE이다. |
| 정리 후 보존 | 모든 agent_run 종료·모델 소유 그룹 소멸·runtime admission 해제를 확인했다. 검증 서버 종료 후 증거 참조 35개/고유 snapshot 18개가 현재 해시 유효다. |

모델 응답이나 receipt를 수작업으로 고쳐 통과시키지 않았다. QA-1의 실패 원본과 과거 인사 PASS는 남아 있다. 표시 집계에서도 QA-1을 DONE/선택 기준으로 바꾸지 않아 TARGET 관련 단계는 과거 차단을 포함하고, LIFECYCLE의 확인 완료와 구분된다.

설치 코드 주요 7개 모듈의 해시가 고정 c50 커밋과 일치한다. 이 Python runtime 관측은 새 프로젝트 세션의 정식 startup/hook 활성화 증명과 별개다.

## 합성 시험과 전체 회귀 상태

합성 시험으로만 확인한 항목은 binary/특수 파일명·작업트리 식별 보존, 지연 subprocess·lock timeout·중단/실패 경로, owner criterion mapping/관찰 변조·경쟁 변경 거부, 표시 순환과 handoff fixture 경계다. 실제 모델 세션 수에 이 fixture 호출을 더하지 않는다.

최종 f2f00ca에서 시간 제한·진단 수집을 적용한 관련 6개 모듈은 **76개 통과**했다(진행 표시 35, 개발 게이트 17, tracking I/O 7, review gate 6, owner 계약 8, platform schema 3). 64.13초, 종료 0, 소유 그룹 회수를 확인했다. 중복 재실행 수는 합산하지 않는다.

| 전체 실행/재시험 | 최종 확인 상태 |
| --- | --- |
| e18380a 전체 시도 | schema 수정 때문에 중단, exit 130. PASS가 아니다. |
| c50df53 전체 재시도 | 1,800초 제한 하에 1,410.12초 만에 종료 1. 626개 실행, failures 4·errors 10·skipped 1. 전체 PASS가 아니다. HTTP class setup 실패 때문에 추가 9개는 실행되지 않았다. |
| HTTP 환경 재시험 | loopback bind PermissionError 관련 초기 4개와 나머지 12개를 권한 있는 격리 경로에서 재실행해 모두 통과했다. |
| multiprocessing 재시험 | 공통 코드가 아니라 이 실행의 외부 진단 wrapper에 main guard가 없어 spawn 자식이 sys.argv 처리 중 실패했다. wrapper 수정 후 관련 모듈 20개 통과, 동일 수정 wrapper로 원래 영향 4개도 통과했다. |
| handoff·누락 증거 기대 수정 | reviewed 요구사항을 덮어쓴 정상 fixture를 수정하고 변경 시 차단 시험을 추가했다. 누락 증거는 RECHECK_REQUIRED라는 현재 동작을 검사하며 raw DONE·과거 PASS 보존도 확인했다. 최종 76개에 포함된다. |
| 최종 설치 smoke | f2f00ca를 별도 fixture에 install/init/명시적 update: 통과. 설치 7개 모듈 해시와 sentinel 보존 확인. 이 fixture에서 실제 모델은 실행하지 않았다. |

전체 원본의 실패 로그는 수정·삭제하지 않았다. 관측 실패 원인은 위 재시험으로 확인했지만 **f2f00ca 단일 전체 재실행은 NOT_RUN**이다. 비공개 실제 기록 corpus가 배포되지 않아 생략한 usage-context 시험 1개도 미검증으로 남는다. [전체 실행 메타데이터](../../../.harness/pstack-followup/full-suite-c50df53.process.json), [최종 관련 재시험](../../../.harness/pstack-followup/final-related-f2f00ca.process.json), [설치 smoke](../../../.harness/pstack-followup/final-install-smoke.json)를 구분한다.

## 비용과 남은 제한

[사용량 요약](../../../.harness/pstack-followup/native-cost-summary.json)은 실제 `gpt-6.1-sol` native 세션 4개, 명시적으로 귀속된 고유 response 21개를 기록한다. 확인 가능한 입력 677,219 + 출력 6,730 = 총 683,949토큰이다. 캐시 입력 534,016은 입력에 포함되므로 다시 더하지 않는다. reasoning 세부도 출력에 중복 합산하지 않는다. 이 수치는 격리 CLI 모델 실행 범위이며 메인/협업 보조 에이전트 사용량 전체가 아니다.

native 세션 시작 전 실패 1회의 사용량은 UNKNOWN이다. ChatGPT 인증 runtime이 청구 금액을 제공하지 않아 통화 비용도 UNKNOWN이다. 실패를 0토큰이나 무료 실행으로 표현하지 않는다.

여백 앱의 선택 설치는 `799a4a529621f393e8566669ed9fecbe60aac018`, startup NOT_RUN/runtime RESTART_REQUIRED를 유지한다. 앱 적용 전에는 로컬 공통 변경과 남은 전체 회귀를 검토하고 명시적으로 커밋/배포를 선택한 뒤 프로젝트 절차·환경·필수 정책을 구성하며 새 세션 startup/hook을 별도로 확인해야 한다. 이번 격리 CLI 시험은 Android/iOS/Web UI·Server API·제품 전체 인수 검증이나 배포 검증을 대신하지 않는다.

실제 환경 파일의 최신성·증거 의미·선언 actor와 실제 신원의 연결·같은 원장 밖 raw shell/외부 프로세스 통제·장기 보관/복구 보장은 여전히 구분한다. 정리 후 현재 로컬 파일 유효성은 저장 장치 손실 복구를 보장하지 않는다.

## 맥락 정리와 메인 수락

실제 맥락 정리 담당이 관련 지침과 위 로컬 근거를 대조해 이 기록과 현재 맥락의 짧은 진입 링크만 갱신했다. 사용자 요청·실제 구현·실패·미검증을 구분하고 원본은 삭제·이동·복제하지 않았다. 메인이 원시 실행 메타데이터·최종 관련 시험·설치 smoke와 내용을 대조하고 위 결과를 갱신해 수락했다. 이 수락은 기록의 정확성에 대한 검토이며 사용자 승인이나 전체 회귀 PASS를 대신하지 않는다.

## Draft PR 제출

사용자의 후속 커밋·Draft PR 지시에 따라 기존 6개 로컬 개선 커밋을 보존하고 최신 main(1a01601)을 별도 제출 clone에 통합했다. 유지보수 문서의 일회성 계측만 원본 로컬 기록으로 분리한 최종 제출은 e2a55fc3f15172028fe239069b019cafecb8e14d이다. [Draft PR #8](https://github.com/wooyj-1217/kmp_agent/pull/8), 브랜치 feat/evidence-gated-verification.

최종 clean checkout에서 설치를 포함한 관련 13개 모듈 188개 시험이 184.875초 만에 통과했다(600초 제한, 소유 프로세스 회수). 원본 대비 30개 변경 경로·해시와 PR 범위 검사 및 diff --check를 확인했다. 최종 단일 전체 회귀는 NOT_RUN으로 유지하며 원래 전체 FAIL과 분리했다. raw 로그·앱 자료는 게시하지 않았다. 기존 앱 선택 버전·미커밋 변경을 보존했고 병합·태그·릴리스·배포는 수행하지 않았다.
