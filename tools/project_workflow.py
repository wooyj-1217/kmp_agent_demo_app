#!/usr/bin/env python3
"""Project-level target/snapshot preflight; never starts a product implementation."""
from pathlib import Path
import argparse,copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
PIN='.kmp-agent/releases/0e2a2468304a610ca6aa4e0b8fa6ff4bf4ebee55'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(root):
 sys.path.insert(0,str(root/PIN))
 from harness.project_contract import validate
 return validate(json.loads((root/'docs/project-settings.json').read_text()))
def project_settings(root,targets=None):
 data=copy.deepcopy(canonical(root)); all_targets=data['implementation_targets']['value']
 targets=list(targets or all_targets)
 if not targets or len(set(targets))!=len(targets) or any(t not in all_targets for t in targets):
  raise ValueError('selected targets must be a nonempty unique subset of canonical implementation_targets')
 data['implementation_targets']['value']=targets
 ui=data['ui_technology'];ui['value']={t:ui['value'][t] for t in targets}
 ui['status']='CONFIRMED' if all(v['status']=='CONFIRMED' for v in ui['value'].values()) else 'UNDECIDED'
 parent=sha(root/'docs/project-settings.json')
 # Extra metadata inside decision fields is supported; no unsupported top-level schema keys.
 for field in ['implementation_targets','ui_technology']:
  data[field]['projection']={'source':'docs/project-settings.json','sha256':parent,'targets':targets}
  data[field]['reason']='Derived target slice; never an independent target decision. '+data[field]['reason']
 return data
def stage_settings(root,stage,targets=None):
 if stage not in ['ui','client_integration','server_implementation','integration_verification']:
  raise ValueError('unsupported stage')
 data=project_settings(root,targets)
 # Use installed gate with an in-memory, explicitly selected target input. No task/begin mutation.
 sys.path.insert(0,str(root/PIN))
 from harness.project_contract import gate
 class Frozen:
  root=None
  def _valid_artifact(self,ref):return ref.get('virtual') is True
 temporary=root/'.harness/v1/settings-correction/projections'
 temporary.mkdir(parents=True,exist_ok=True)
 path=temporary/('targets-'+'-'.join(data['implementation_targets']['value'])+'.json')
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 manager=Frozen();manager.root=root
 ref={'virtual':True,'snapshot':str(path.relative_to(root))}
 gate(manager,{'stage_contract':{'stage':stage,'settings':ref,'documents':[]}})
 return path,data
def snapshot_check(root,task):
 contract=task.get('stage_contract')
 if not contract:raise ValueError('product stage_contract missing; cannot infer an approved target')
 ref=contract['settings']; path=root/ref['snapshot']
 if not path.is_file() or sha(path)!=ref['sha256']:raise ValueError('frozen stage snapshot invalid')
 data=json.loads(path.read_text()); targets=data.get('implementation_targets',{}).get('value')
 current=canonical(root)
 if data!=current and data!=project_settings(root,targets):
  raise ValueError('historical/stale stage settings; refreeze corrected targets, do not use old CONFIRMED implementation')
 for ref in contract['documents']:
  if not (root/ref['path']).is_file() or sha(root/ref['path'])!=ref['sha256']:
   raise ValueError('stage document working copy changed: '+ref['path'])
 return data
def require_current(root,task_id,operation):
 root=Path(root);state=json.loads((root/'.harness/tasks/tasks.yaml').read_text());task=state['tasks'][task_id]
 data=snapshot_check(root,task)
 baseline=json.loads((root/'.harness/v1/active-baseline.json').read_text())
 for ref in baseline.get('inputs',[]):
  if not (root/ref['path']).is_file() or sha(root/ref['path'])!=ref['sha256']:
   raise ValueError('current target baseline input changed: '+ref['path'])
 if baseline.get('status')!='ACTIVE' or baseline.get('implementation_authorized') is not True:
  raise ValueError('corrected target baseline BLOCKED; product transition/execution/review/handoff not authorized')
 if task['state']=='DONE':raise ValueError('historic completed task cannot authorize a new corrected-target execution')
 sys.path.insert(0,str(root/PIN))
 from harness.project_contract import gate
 class Manager:
  def __init__(self):self.root=root
  def _valid_artifact(self,r):return (root/r['snapshot']).is_file() and sha(root/r['snapshot'])==r['sha256']
 gate(Manager(),task)
 return {'task':task_id,'operation':operation,'result':'PASS','targets':data['implementation_targets']['value']}
def main():
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
 check=sub.add_parser('check');check.add_argument('--task',required=True);check.add_argument('--operation',required=True,choices=['ready','begin','review','handoff','resume'])
 inspect=sub.add_parser('inspect');inspect.add_argument('--targets',nargs='+');inspect.add_argument('--stage',choices=['ui','client_integration','server_implementation','integration_verification'])
 args=parser.parse_args()
 try:
  if args.action=='check':result=require_current(ROOT,args.task,args.operation)
  elif args.stage:
   path,data=stage_settings(ROOT,args.stage,args.targets);result={'input_gate':'PASS','scope':'static target slice only; not product execution authorization','projection':str(path.relative_to(ROOT)),'ui_status':data['ui_technology']['status']}
  else:result={'canonical':'docs/project-settings.json','targets':project_settings(ROOT,args.targets),'execution_authorized':False}
  print(json.dumps(result,ensure_ascii=False,indent=2))
 except (ValueError,KeyError) as error:
  print(json.dumps({'result':'BLOCKED','reason':str(error)},ensure_ascii=False));return 2
 return 0
if __name__=='__main__':raise SystemExit(main())
