"""Post-hoc analysis annotations, not original interventions or product approvals."""
# event UUID -> primary category, reason, task context, stage, rework episode
A={}
def a(i,c,why,t='',s='UNKNOWN',r=''):
 A[i]={'category':c,'reason':why,'tasks':t.split() if t else [],'stage_hint':s,'rework_episode':r,'provenance':'POSTHOC_AGENT_REVIEW','user_approved_classification':False}
a('281c7dff-5827-4381-816f-ee367cda687e','신규 요청','서버 연동 메모 제품의 최초 기획·검토 요청','TASK-001 TASK-002','기획')
for i in ['42ccf4a4-287f-4ace-9de2-ba7740cd4c36','a5befdf6-9a7e-40ad-8760-ea9057c3bd1e','69f88794-97f4-4a77-92ca-d03dcdf35ce6']:
 a(i,'정책 결정','질문에 답해 본문·목록·불확실 저장 정책을 선택함','TASK-001 TASK-002','기획')
a('7b1bc03b-0bd5-46cd-9558-117e50276fd9','상태 질문','제품 작업의 실제 로거 시작·근거 확인 요청','TASK-001 TASK-002')
a('f21f3b57-847c-45f5-9e75-9cab000aca55','신규 요청','완료된 제품 기획의 검토·커밋 요청','TASK-001 TASK-002','기획')
a('434176d1-90b3-47ce-bbd2-f8e799e3b12b','신규 요청','기획 버전을 입력으로 목록·작성 디자인 착수 요청','TASK-003 TASK-004','디자인')
a('db7c5830-052f-4579-85cd-f50b1aa21f35','정책 결정','3줄 표시·초과 글자 색상·안내 문구 변경 선택; 기존 위반이라고 단정하지 않음','TASK-003 TASK-004','디자인','DESIGN_CHANGE_REQUEST')
a('14a0c1f5-9235-42b2-a19e-a2e216e884cb','정책 결정','안내 문구 제거의 추가 디자인 선택','TASK-003 TASK-004','디자인','DESIGN_CHANGE_REQUEST')
a('af79796c-a904-449b-8d69-f1fe47d876a8','정책 결정','Ktor·Compose 및 모듈 경계의 기존 합의를 명시; 하네스/제품 혼합 요청이므로 전체 턴 비용을 제품에 귀속하지 않음','V1-BASELINE','기획')
A['af79796c-a904-449b-8d69-f1fe47d876a8']['mixed_scope']=True
a('120f3e5d-67db-4004-9306-906863d7a2ac','정책 결정','데모 웹 지원 범위 추가; 공통 하네스 변경도 포함된 혼합 요청','TASK-005','디자인')
A['120f3e5d-67db-4004-9306-906863d7a2ac']['mixed_scope']=True
a('a5f4bf2b-545d-4c59-809f-306c2715d32f','신규 요청','시안 재생성 요청만으로 오류나 원인 확정 불가','TASK-003 TASK-004 TASK-005','디자인')
a('b9098fc1-c6c8-4dce-89e3-7a2c3444c487','오류 정정','요청된 웹이 시안에서 누락됐다고 지적','TASK-005','수정','DESIGN_OMISSION')
a('e89489f0-cb0f-4abb-b398-4421482493f8','오류 정정','기존 index 대신 새 시안 파일을 만든 전달 방식 문제 지적','TASK-005','수정','DESIGN_DELIVERY')
a('c360d0ad-db17-474d-a51b-2b7f4fda240b','정책 결정','시안 프레임 질문과 반응형 요구 추가; 주 분류는 새로운 디자인 요구','TASK-005','디자인','DESIGN_CHANGE_REQUEST')
a('d9d85caf-63da-4e65-99bf-7354cedc7014','상태 질문','디자인 시스템·토큰 존재 확인','TASK-003 TASK-004','디자인')
a('6db3fc17-fc2e-4c87-84d6-fc37138a07ea','상태 질문','현재 데모 모듈 구조 설명 요청','V1-BASELINE','기획')
a('d299817c-68cf-4e51-9ac0-ec5c2b0302e1','신규 요청','기존 v1 범위·실행·기준 연결 조사 및 설정 반영 요청','V1-BASELINE','기획')
a('58366f5f-7067-4d14-9453-5015b4b3fb5e','신규 요청','미정 사항·기준 연결 재검토 요청; 기능 정책을 새로 선택하지는 않음','V1-BASELINE','기획')
a('60d85378-bdcd-4114-80c6-89f5f9b95461','정책 결정','초안 자동 복원 없음 확정과 후속 구현·검증 허가가 혼합됨','V1-BASELINE V1-DESIGN V1-SHARED V1-SERVER V1-WEB V1-ANDROID V1-IOS V1-INTEGRATION')
a('145d3bd6-002d-4a85-b6d0-217e4717baf4','환경 지원','Xcode 재설치 사실을 알리고 시험 재개 요청','V1-IOS','검증')
a('a1ab0d4f-49c1-446b-a67d-d556ed9c1dee','환경 지원','차단됐던 Apple 라이선스 동의 완료를 사용자가 확인','V1-IOS','검증')
a('99ac0554-60f1-4d55-a646-5d6fd0f4e059','미확인','계속 진행만으로 구체적인 개입 종류·작업을 확정할 수 없음')
a('f9cc148c-28c7-4992-8558-4353bdc43ad9','신규 요청','전체 인수 상태 조사와 누락 검증·결함 수정 수행 요청','V1-INTEGRATION','검증')
a('af471353-9c28-4e98-922d-1bb812d0f14f','환경 지원','Chrome 전경 검증을 위한 사용자 사용 시간 허가','V1-INTEGRATION','검증')
a('0dba9cd9-aefa-4c00-915b-7cbbec841190','환경 지원','직접 사용을 위한 로컬 서버·시험 기기·앱 기동 요청','V1-ANDROID V1-IOS V1-WEB')
a('dd27e2f0-748f-41da-8112-e2f1b9f10dff','오류 정정','명령 안내에서 멈춘 수행 누락을 지적하고 직접 실행 요구','V1-ANDROID V1-IOS V1-WEB','수정','LOCAL_PREVIEW_EXECUTION')
a('905b807f-bca8-4adf-85d1-ea103564e0ac','오류 정정','승인 디자인 대비 플랫폼 불일치를 사용자가 발견; FB-003','V1-DESIGN-CONFORMANCE','수정','DESIGN_CONFORMANCE')
a('e9e25cef-8e0d-46b7-8a20-07ee3dfd6344','미확인','계속 진행이라는 재개 의사만 확인; 오류 정정으로 세지 않음')
a('9060b361-3569-452a-997b-5ced74048dea','상태 질문','실제 서버 SQLite 저장 상태를 읽기 전용으로 확인 요청','V1-SERVER','검증')
a('69abcb34-dfb5-4826-83d0-250a660fe17d','신규 요청','기존 검증·스펙·구조를 HTML 보고서로 구성 요청','','보고서')
a('5f51008b-9fd5-4b85-a9f3-8ae81adbe39b','오류 정정','배포가 아니라 HTML 파일 작성이라는 요청 해석 정정','','보고서','REPORT_SCOPE_CORRECTION')
a('9eec2f97-4bc2-44a2-935d-251979c2d0c9','신규 요청','이동용 HTML 보고서 ZIP 패키징 요청','','보고서')
a('3993fcaf-faa9-48f0-982c-049fc1b24a66','상태 질문','기술 구성에 대한 불만·질문만으로 상세 오류 항목 확정 불가','V1-AGREEMENT-REVIEW','보고서')
a('4c200865-305d-4e37-a730-0954aade730c','오류 정정','사용자가 UI 통일·Ktor 합의 이탈을 명시하고 보고서 정정 요청; FB-004','V1-AGREEMENT-REVIEW','수정','AGREEMENT_DEVIATION')
a('8bd4e697-9adb-4920-9b41-c42b8c77b834','상태 질문','미저장 뒤로가기의 기존 기획·시안 존재를 질문','V1-AGREEMENT-REVIEW','보고서')
a('82a03577-df9b-4f17-9ae2-f703d7518ea4','오류 정정','보고서의 확인창 상태 비교 검증 누락 지적; FB-005','V1-AGREEMENT-REVIEW','수정','STATE_COMPARISON_OMISSION')
a('cdd3491c-0fd7-419e-a039-991f77e060a6','신규 요청','정정 보고서의 ZIP 패키징 요청','','보고서')
a('b9976a31-2da3-42a4-b302-8b1580a28ad7','오류 정정','설정 CONFIRMED와 동결 실행 기준에 남은 대체 구현 정정; FB-006','V1-SETTINGS-ALIGNMENT','수정','TARGET_SETTINGS_CORRECTION')
a('c2151946-ce89-4c48-b1cc-5b52a62c064a','신규 요청','최신 보고서 ZIP 재생성 요청','','보고서')
a('7bccf36d-c864-4d41-9015-af1d3f515f4a','상태 질문','기존 로그 파일 위치 질문','','보고서')
a('d652a75c-cc6d-42e5-b524-129f45ae309f','신규 요청','스터디용 제품 로그 추출·ZIP 요청','','보고서')
a('d12ee1c5-c808-49f7-86e1-605b66b4cd22','상태 질문','로그의 분류·사용량 공백 보강 방법 질문','','보고서')
a('7a5ab9ef-7259-4d4b-b59c-264843aa1530','신규 요청','단계·토큰 구성·추정 비용·재작업 분석 추가 요청','','보고서')
a('cd865c53-e8ae-41c0-a4d8-47a2e68c5559','신규 요청','요청 분류·원본 중복 제거·당시/사후 구분 추가 요청','','보고서')

EXCLUDED={
 '5e0e24af-c0b6-4a9a-8d06-7d8bc51af935':'환경/AGENTS 지침 주입; 독립적인 제품 요청이 아님',
 '4e4e2405-8000-40c6-aad1-80c1a17ef910':'공통 하네스 Goal·워크플로 구조 요청',
 'b7da1db6-2a83-4aac-a87a-aa1d4ef18ef4':'공통 하네스의 기획·디자인 템플릿 동작 점검용 예시 요청',
 '35f73428-0253-4f78-b50a-29508da9c5f3':'작업 관리·로깅을 검증하기 위한 작은 문서 시험 요청',
 '11974948-43fb-47f7-b2c9-ca3bbe4943df':'공통 하네스 개선사항 문서 통합 요청',
 'ea1b51d0-47c2-42de-a587-7d0ddb2a85fe':'저장소 연결 작업의 시행착오 기록 규칙 요청',
 '9b3d6405-37aa-46b7-bcf0-cfa8329e7654':'공통 하네스 파일·문서 구조 점검 요청',
 'b87ef7b0-e88a-43f7-9119-43d989a45922':'공통 하네스 회고 기록 지침 범위 조정 요청',
}
