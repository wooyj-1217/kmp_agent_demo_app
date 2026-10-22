"""Explicit local acceptance phases. Record control responses as evidence, not browser UI results."""
from pathlib import Path
import json
import sys
import urllib.request

phases = {
    'web-start': {'reset': True, 'rules': [{'method':'GET','path':'/api/v1/memos','delay':5,'remaining':1}]},
    'order': {'reset': True, 'seed_order': True, 'rules': []},
    'initial-fail': {'reset': True, 'rules': [{'method':'GET','path':'/api/v1/memos','status':503}]},
    'clear': {'rules': []},
    'reject': {'rules': [{'method':'POST','path':'/api/v1/memos','status':422,'remaining':1}]},
    'delay-save': {'rules': [{'method':'POST','path':'/api/v1/memos','delay':5,'remaining':1}]},
    'commit-loss': {'rules': [{'method':'POST','path':'/api/v1/memos','drop_after_commit':True}]},
    'restart': {'restart': True, 'rules': []},
    'list-fail': {'rules': [{'method':'GET','path':'/api/v1/memos','status':503}]},
    'snapshot': None,
}
phase = sys.argv[1]
value = phases[phase]
request = urllib.request.Request('http://127.0.0.1:18082/',
    data=json.dumps(value).encode() if value is not None else None,
    headers={'Content-Type':'application/json'})
with urllib.request.urlopen(request,timeout=30) as response:
    data=json.load(response)
folder=Path(__file__).resolve().parents[2]/'.harness/v1/web-acceptance-phases'
folder.mkdir(parents=True,exist_ok=True)
number=len(list(folder.glob('*.json')))+1
(folder/f'{number:03d}-{phase}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'phase':phase,'evidence':str(folder/f'{number:03d}-{phase}.json'),
                  'rows':[{'id':r['id'],'body':r['body'][:80]} for r in data['rows']],
                  'posts':sum(r['method']=='POST' for r in data['requests'])},ensure_ascii=False))
