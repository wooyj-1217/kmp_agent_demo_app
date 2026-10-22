#!/usr/bin/env python3
"""Configuration/control-path tests only. No app build, product API, SDK or DB."""
from pathlib import Path
import copy,json,hashlib,sys,subprocess,unittest,datetime,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.project_workflow import canonical,project_settings,stage_settings,snapshot_check,require_current
FOLDER=ROOT/'.harness/v1/settings-correction'
def load(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Alignment(unittest.TestCase):
 def test_supported_schema_and_goal_fact_separation(self):
  data=canonical(ROOT);ui=data['ui_technology']
  self.assertEqual(ui['status'],'UNDECIDED')
  for target in ['android','ios']:
   self.assertEqual(ui['value'][target],{'status':'CONFIRMED','technology':'Compose Multiplatform'})
  self.assertEqual(ui['value']['web']['status'],'UNDECIDED')
  self.assertEqual(data['server_technology']['value']['framework'],'Ktor')
  self.assertFalse(any(s in json.dumps(ui['value']) for s in ['Views','SwiftUI']))
  observed=load('docs/current-implementation.json');self.assertEqual(observed['approval'],'NOT_AN_APPROVED_TARGET')
  self.assertEqual(observed['server'],'JDK HttpServer')
  for ref in observed['source_files'].values():self.assertEqual(sha(ROOT/ref['path']),ref['sha256'])
 def test_mobile_ui_decision_gate_passes_without_web_decision(self):
  _,data=stage_settings(ROOT,'ui',['android','ios'])
  self.assertEqual(data['ui_technology']['status'],'CONFIRMED')
  self.assertEqual(data['implementation_targets']['value'],['android','ios'])
 def test_web_and_all_target_ui_are_blocked(self):
  for targets in [['web'],None]:
   with self.subTest(targets=targets):
    with self.assertRaisesRegex(ValueError,'ui_technology'):stage_settings(ROOT,'ui',targets)
 def test_server_decision_gate_does_not_depend_on_web_ui(self):
  _,data=stage_settings(ROOT,'server_implementation')
  self.assertEqual(data['server_technology']['value']['framework'],'Ktor')
  self.assertEqual(data['ui_technology']['status'],'UNDECIDED')
 def test_module_boundaries_are_explicit(self):
  modules=canonical(ROOT)['code_ownership']['value']['modules']
  self.assertEqual(modules['domain']['depends_on'],[])
  self.assertEqual(modules['domain-server']['depends_on'],['domain'])
  self.assertEqual(modules['domain-client']['depends_on'],['domain'])
  for name in ['data-server','presentation-server']:self.assertIn('domain-server',modules[name]['depends_on'])
  for name in ['data-client','presentation-client']:self.assertIn('domain-client',modules[name]['depends_on'])
  self.assertNotIn('domain-client',modules['domain-server']['depends_on'])
  self.assertNotIn('domain-server',modules['domain-client']['depends_on'])
 def test_historical_settings_snapshot_rejected(self):
  tasks=load('.harness/tasks/tasks.yaml')['tasks']
  for tid in ['V1-SERVER','V1-ANDROID','V1-IOS','V1-WEB','V1-INTEGRATION']:
   with self.subTest(task=tid):
    with self.assertRaisesRegex(ValueError,'historical/stale'):snapshot_check(ROOT,tasks[tid])
 def test_parent_hash_or_implementation_substitution_rejected(self):
  data=project_settings(ROOT,['android'])
  for change in ['parent','framework']:
   with tempfile.TemporaryDirectory(prefix='negative-',dir=FOLDER) as temp:
    altered=copy.deepcopy(data)
    if change=='parent':altered['ui_technology']['projection']['sha256']='0'*64
    else:altered['server_technology']['value']['framework']='HttpServer'
    path=Path(temp)/'settings.json';path.write_text(json.dumps(altered))
    fake={'stage_contract':{'stage':'ui','settings':{'snapshot':str(path.relative_to(ROOT)),'sha256':sha(path)},'documents':[]}}
    with self.assertRaisesRegex(ValueError,'historical/stale'):snapshot_check(ROOT,fake)
 def test_new_bindings_and_no_product_execution(self):
  state=load('.harness/tasks/tasks.yaml')['tasks'];bindings=load('.harness/v1/settings-correction/bindings.json')
  for tid in bindings['bindings']:
   task=state[tid];self.assertEqual(task['state'],'TODO');self.assertEqual(task['executions'],[])
   data=snapshot_check(ROOT,task)
   self.assertEqual(data['server_technology']['value']['framework'],'Ktor')
   for op in ['ready','begin','review','handoff','resume']:
    with self.assertRaisesRegex(ValueError,'baseline BLOCKED'):require_current(ROOT,tid,op)
  self.assertEqual(state['V1-INTEGRATION']['state'],'BLOCKED')
 def test_legacy_history_unchanged_but_reviews_not_inherited(self):
  old=load('.harness/v1/settings-correction/history/.harness/tasks/tasks.yaml')['tasks'];current=load('.harness/tasks/tasks.yaml')['tasks']
  cr=load('.harness/v1/settings-correction/bindings.json')['change_id']
  for tid,task in old.items():
   if not tid.startswith('V1-'):continue
   for key in ['reviews','executions','outputs','inputs','stage_contract']:
    self.assertEqual(task.get(key),current[tid].get(key),(tid,key))
   for review in task['reviews']:
    status=current[tid]['validation_status'][review['agent_run_id']]
    self.assertEqual(status['state'],'RECHECK_REQUIRED');self.assertEqual(status['change_id'],cr)
 def test_legacy_helpers_stop_before_product_actions(self):
  paths=['.harness/v1/finish-ios.py','.harness/v1/finalize-acceptance.py','.harness/v1/check-integration.py','.harness/v1/control-tracked.py','.harness/v1/design-conformance/setup.py','.harness/v1/design-conformance/finalize.py','.harness/v1/design-conformance/command.py','.harness/v1/design-conformance/manifest.py','tools/v1-report/generate.py']
  for path in paths:
   with self.subTest(path=path):
    result=subprocess.run([sys.executable,'-B',path],cwd=ROOT,capture_output=True,text=True,timeout=25)
    self.assertNotEqual(result.returncode,0,path)
    self.assertTrue(any(s in result.stdout+result.stderr for s in ['historical/stale','stage_contract missing','Historical report generator blocked']),path)
 def test_baseline_inputs_and_protected_files(self):
  baseline=load('.harness/v1/active-baseline.json');self.assertEqual(baseline['status'],'BLOCKED');self.assertIs(baseline['implementation_authorized'],False)
  self.assertEqual(baseline['target_compliance'],'NOT_RUN')
  self.assertEqual(baseline['planning_review'],'UNKNOWN');self.assertEqual(baseline['design_review'],'UNKNOWN')
  for ref in baseline['inputs']:self.assertEqual(sha(ROOT/ref['path']),ref['sha256'])
  for path,digest in load('.harness/v1/settings-correction/start.json')['protected_files'].items():self.assertEqual(sha(ROOT/path),digest,path)

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Alignment)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 evidence={'result':'PASS' if result.wasSuccessful() else 'FAIL','scope':'settings/baseline/runner controls only; not product transition or E2E compliance','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tests_run':result.testsRun,'failures':[(str(t),s) for t,s in result.failures],'errors':[(str(t),s) for t,s in result.errors],'settings_sha256':sha(ROOT/'docs/project-settings.json'),'baseline_sha256':sha(ROOT/'.harness/v1/active-baseline.json'),'tested_sources':{p:sha(ROOT/p) for p in ['tools/project_workflow.py','tools/verify_settings_alignment.py','docs/project-settings.json','docs/current-implementation.json','docs/target-architecture.md']},'product_transition_runs':0,'product_compliance':'NOT_RUN','usage':'UNKNOWN'}
 (FOLDER/'verification.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
 if result.wasSuccessful():
  bindings=load('.harness/v1/settings-correction/bindings.json')
  rows='\n'.join('| '+tid+' | '+entry['stage']+' | '+entry['settings']+' | TODO / 실행0 |' for tid,entry in bindings['bindings'].items())
  document='''# SRC-007 설정 정정 결과

이번 결과는 설정·문서·기준 연결 정합성 검증이다. 제품 전환 구현/기술 준수 검증이 아니며 기존 API/DB/앱은 변경하지 않았다.

## 변경점

- `docs/project-settings.json`: 승인 목표는 Android/iOS Compose Multiplatform, 서버 Ktor, 공통/전용 모듈 경계. 웹 UI만 UNDECIDED다. 단일 UI 필드의 전체 상태는 웹 때문에 UNDECIDED이며 모바일 하위 결정은 CONFIRMED다.
- `docs/current-implementation.json`: 기존 Views/SwiftUI/HttpServer·축약 모듈과 코드 해시의 관측만 기록한다. 승인 목표가 아니다. SQLite는 호환 최소안 위임 내 선택으로 유지했다.
- `AGENTS.md`와 `tools/project_workflow.py`: 프로젝트 공식 ready/begin/review/handoff/resume 선검사. 과거 stage snapshot·부모 설정 해시가 낡은 투영·권한 없는 baseline은 거부한다.
- `.harness/v1/active-baseline.json`: 과거 ACTIVE를 보존하고 현재 목표 입력은 BLOCKED/implementation_authorized=false로 연결했다. 과거 planning/design PASS ID는 새 목표에 넣지 않는다.
- `CR-001`(docs registry): 정정 영향의 과거 검토 유효성은 RECHECK_REQUIRED. 리뷰의 원문 결과·실행·산출물·동결 입력은 삭제/변경하지 않았다.
- 기존 비활성 통합 태스크에는 다른 과거 문서 입력도 섞여 있어 설정 하나만 바꾸지 않았다. 구 태스크 전체를 이력으로 유지하고 아래 새 태스크에 현재 입력을 완전히 동결했다. 이전 계획의 “재동결”은 이 별도 태스크 연결로 수행했다. 제품 작업은 아직 시작하지 않았다.
- 프로젝트의 기존 실행/완료/기능 검토 helper8개와 오래된 상세 보고서 생성 경로도 선검사에서 차단한다. runbook/try-v1의 기존 앱 체험 명령은 기존 구현 관측용이며 목표 기술 승인 근거가 아니다.

## 현재 동결 입력

| 새 태스크 | 단계 | 현재 설정 입력 | 상태 |
| --- | --- | --- | --- |
ROWS

투영 JSON은 부모 설정 SHA와 선택 타깃을 담는 파생 입력이며 독립 상태 원장이 아니다. 향후 설정 변경 시 재동결해야 한다. 새 작업들은 과거 구현 DONE/PASS 대신 정정 작업/정정 구현 태스크끼리 의존하며 모두 실행0이다.

## 실제 정합성 검사

정합성 검사 COUNT건 PASS. 지원 스키마, 모바일 UI 결정 게이트, 웹/전체 UI 거부, 웹 UI와 독립된 Ktor 서버 결정, 모듈 경계, 과거 동결 입력 거부, 위조된 프레임워크/부모 해시 거부, 새 binding 및 실행 차단, 과거 리뷰 원문 보존과 유효성 비승계, 옛 helper 중단, 현재 baseline/보호 파일 해시를 확인했다.

실행 명령: `rtk proxy python3 -B tools/verify_settings_alignment.py`. 근거: `.harness/v1/settings-correction/verification.json`, `bindings.json`, `start.json`. 구 설정/baseline/원장/helper는 같은 폴더 history에 보존한다. 설치 하네스·제품 소스/빌드·이전 ZIP의 보호 해시 변경0이다. 프로젝트 `.harness` helper 자체는 공통 개발 캡처에서 제외되므로 별도 실행 거부 검사와 보존 사본으로 확인했다.

하네스 설치본의 기술 value 의미 검증/타깃별 UI 해석/자동 전파를 구현했다고 말하지 않는다. 프로젝트 공식 경로를 우회하는 직접 설치 API 호출을 전역 보안 강제로 막는 기능도 아니다. 현재 공식 경로·이미 동결된 정정 입력에서는 대체 구현을 승인 목표로 사용하지 않는다.

## 남은 것

- 사용자 결정은 웹의 동일 UI 기술/공유 화면 적용 범위만 남았다.
- 제품 전환 실행 권한 없음. Ktor/CMP/모듈 전환·전환 후 기능/디자인/상태별 검증 NOT_RUN. 미저장 뒤로가기 확인창 비교도 NOT_RUN 유지.
- 설정 검사 PASS를 제품 준수 PASS나 v1 완료로 승계하지 않는다. 전체 v1 BLOCKED.
'''.replace('ROWS',rows).replace('COUNT',str(result.testsRun))
  note=FOLDER/'preservation-note.md'
  if note.exists():document+='\n'+note.read_text()
  (ROOT/'docs/settings-alignment-result.md').write_text(document)
 raise SystemExit(0 if result.wasSuccessful() else 1)
