#!/usr/bin/env python3
"""HTTP audit for the derived report only. Does not call the product API."""
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
import re,json,datetime,concurrent.futures,hashlib
ROOT=Path(__file__).resolve().parents[2]/'reports/v1'
content=(ROOT/'index.html').read_text()
refs=sorted(set(re.findall(r'(?:href|src)="([^"]+)"',content)))
paths=['/']+['/'+x for x in refs if not x.startswith(('#','http:','https:'))]
def fetch(path):
 try:
  with urlopen('http://127.0.0.1:8773'+path,timeout=15) as response:
   return dict(path=path,status=response.status,bytes=len(response.read()))
 except HTTPError as error:return dict(path=path,status=error.code)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: results=list(pool.map(fetch,paths))
blocked=[fetch(p) for p in ['/data/memos.db','/.codex/hooks.json','/.harness/logs/events.jsonl','/../data/memos.db','/%2e%2e/data/memos.db','/sources/']]
data=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),report_sha256=hashlib.sha256(content.encode()).hexdigest(),link_count=len(results),failed=[x for x in results if x['status']!=200],assets=results,non_report_routes=blocked,external_resources=re.findall(r'(?:src|href)="https?[^\"]+',content),scope='report HTTP only; no product test or memo API writes')
(ROOT/'http-verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in data.items() if k!='assets'},ensure_ascii=False,indent=2))
raise SystemExit(1 if data['failed'] or any(x['status']!=404 for x in blocked) or data['external_resources'] else 0)
