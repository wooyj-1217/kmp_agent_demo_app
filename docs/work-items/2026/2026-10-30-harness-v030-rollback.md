# kmp_agent v0.3.0 복귀

사용자 요청: 현재 kmp_agent를 0.3.0으로 되돌린다. 기존 VERSION 문자열도 0.3.0이므로 정식 태그를 선택해 개발 커밋과 구분했다.

- 이전: 799a4a529621f393e8566669ed9fecbe60aac018
- 선택: v0.3.0 / 275b489fda59d4904031ae8fb445f845485603c6
- 실행: `rtk proxy python3 .kmp-agent/agent.py update --ref v0.3.0` 종료 0.
- 검증: 설치 ref·VERSION·실제 HEAD 일치, 설치 코드 clean, 정적 연결 PASS. status 종료 1은 RESTART_REQUIRED이며 실제 신규 세션 검증 NOT_RUN이다. 원본: `.harness/rollback-v0.3.0-status.json`.
- 제품 코드·기존 로그·이전 정상 릴리스 보존. 커밋·원격 배포 없음.
- 현재 맥락과 운영 문서에 선택 버전 및 과거 적용 설명의 경계를 반영했다. 기능·정책 구현 변경 없는 명시 버전 선택과 기계적 상태 갱신이므로 메인이 직접 맥락 정리했다.
