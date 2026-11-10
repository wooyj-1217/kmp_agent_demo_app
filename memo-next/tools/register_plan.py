"""Register this independent request in the existing harness without prior product inputs."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root / ".kmp-agent/releases/4f3ed6bb7ea27d2bd1d0115c0f963339ec465430"))
from harness.tasks import Tasks

t = Tasks(root,"MEMO-INDEPENDENT-20261110")
if t.run_id in t.read().get("execution_plans", {}):
    print("독립 메모앱 전체 계획은 이미 등록되어 있습니다. 기존 이력을 보존합니다.")
    raise SystemExit(0)
steps, previous = [], []
for key,role,title in [("PLAN","planning","기획 범위 확정"),("DESIGN","design","새 디자인과 데이터 계약"),("BUILD","development","독립 소스 구현"),("QA","verification","플랫폼별 동작 검증"),("REPORT","orchestrator","맥락 검토와 결과 전달")]:
    task_id = "MEMO-NEW-"+key
    steps.append(dict(feature_id="MEMO-INDEPENDENT",task_id=task_id,role=role,title=title,scope="docs/memo-independent/requirements.md; 이전 제품 참조 금지",criteria=[dict(id=key+"-AC",description=title+"의 실제 근거 확인",required=True)],inputs=["docs/memo-independent/requirements.md"],dependencies=previous,work_type="PRODUCT"))
    previous = [task_id]
result = t.register_execution_plan(request_type="IMPLEMENT",procedure="delivery_with_qa",goal="이전 버전 참조 없이 독립 메모앱 제작",steps=steps,scope_source="docs/memo-independent/requirements.md")
print("독립 메모앱 전체 계획 등록 완료")
