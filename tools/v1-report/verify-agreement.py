#!/usr/bin/env python3
"""Read-only HTTP audit of agreement report; no product API or DB access."""
from pathlib import Path
from urllib.request import urlopen
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit
import json,hashlib,datetime,concurrent.futures
R=Path(__file__).resolve().parents[2];P=R/'reports/v1/agreement-review'
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):self.refs.extend(v for k,v in attrs if k in ['href','src'] and v)
parser=Parser();parser.feed((P/'index.html').read_text());base='http://127.0.0.1:8773/agreement-review/index.html'
urls=sorted(set([base]+[urljoin(base,x).split('#')[0] for x in parser.refs]))
assert all(urlsplit(x).hostname=='127.0.0.1' and urlsplit(x).port==8773 for x in urls)
def fetch(url):
 with urlopen(url,timeout=15) as r:
  data=r.read();return dict(url=url,status=r.status,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,urls))
start=json.loads((R/'.harness/v1/agreement-review/start.json').read_text())
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
guards=start['product_files']+['build.gradle.kts','settings.gradle.kts','server/build.gradle.kts','shared/build.gradle.kts','web/build.gradle.kts','androidApp/build.gradle.kts','androidApp/settings.gradle.kts','reports/v1/index.html','reports/memo-v1-review-20261021T045851Z.zip']
changed=[p for p in guards if sha(p)!=start['files'][p]]
assert not changed,changed
evidence=dict(result='PASS',scope='report HTTP links + preservation only; product functional verification not run',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),report_sha256=sha('reports/v1/agreement-review/index.html'),references=results,failed=[x for x in results if x['status']!=200],product_build_old_report_zip_changed=changed,source_collection='PENDING; do not equate native source inspection with hook collection')
directory=R/'.harness/v1/settings-correction';directory.mkdir(exist_ok=True)
archive=directory/('http-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+evidence['report_sha256'][:12]+'.json')
archive.write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
evidence['immutable_copy']=str(archive.relative_to(R))
(directory/'http.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in evidence.items() if k!='references'}|{'unique_links':len(results)},ensure_ascii=False,indent=2))
