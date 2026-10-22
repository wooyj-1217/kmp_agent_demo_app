#!/usr/bin/env python3
"""Package only the report and its transitive local assets; verify extracted ZIP."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import re,json,hashlib,zipfile,tempfile,shutil,datetime,argparse

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reports/v1'
STAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
parser=argparse.ArgumentParser();parser.add_argument('--agreement',action='store_true');args=parser.parse_args()
PACKAGE='memo-v1-agreement-review' if args.agreement else 'memo-v1-review'
ENTRY='agreement-review/index.html' if args.agreement else 'index.html'
DEST=ROOT/'reports'/(PACKAGE+'-'+STAMP+'.zip')

class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if key in ('href','src','poster') and value:self.refs.append(value)
   if key=='srcset' and value:self.refs.extend(x.strip().split()[0] for x in value.split(','))

def references(path):
 if path.suffix not in ('.html','.css','.js','.svg'):return []
 text=path.read_text(); refs=[]
 if path.suffix in ('.html','.svg'):
  parser=Links();parser.feed(text);refs+=parser.refs
 refs+=re.findall(r'url\(\s*[\"\x27]?([^\)\"\x27]+)',text)
 if path.suffix=='.css':refs+=re.findall(r'@import\s+[\"\x27]([^\"\x27]+)',text)
 return refs

def resolve(root,current,reference):
 parts=urlsplit(reference)
 if not parts.path:return None
 if parts.scheme or parts.netloc:
  if parts.scheme=='data':return None
  raise ValueError('External dependency: '+reference)
 if parts.path.startswith('/'):
  raise ValueError('Non-portable absolute asset reference: '+reference)
 target=(current.parent/unquote(parts.path)).resolve()
 if not target.is_relative_to(root.resolve()):raise ValueError('Outside report: '+reference)
 if not target.is_file():raise ValueError('Broken reference: '+str(current)+' -> '+reference)
 return target

selected=set();queue=[SOURCE/ENTRY]
# JSONs are evidence linked by the HTML or its UI verification summary.
queue.extend(SOURCE/p for p in ['provenance.json','ui-verification.json','http-verification.json','task-executions.json'])
if args.agreement:queue.append(SOURCE/'agreement-review/provenance.json')
while queue:
 p=queue.pop()
 if p in selected:continue
 if p.is_symlink() or not p.is_file():raise ValueError('Missing or symlink: '+str(p))
 relative=p.relative_to(SOURCE)
 assert p.suffix in ['.html','.css','.js','.svg','.png','.jpg','.json']
 assert not any(part in ['.codex','.aws','.kmp-agent','logs','sessions'] for part in relative.parts)
 assert not any(part.endswith(('.db','.sqlite','.sqlite3','.jsonl')) for part in relative.parts)
 selected.add(p)
 for reference in references(p):
  target=resolve(SOURCE,p,reference)
  if target:queue.append(target)

temporary=Path(tempfile.mkdtemp(prefix='memo-v1-package-'))
stage=temporary/'stage'/PACKAGE;stage.mkdir(parents=True)
for path in selected:
 target=stage/path.relative_to(SOURCE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
readme='''# 메모 v1 검토 보고서 (이동용 사본)

## 실행 방법

1. ZIP 전체를 압축 해제합니다. 내부 폴더/파일 이름과 상대 경로를 유지하세요.
2. `memo-v1-review/index.html`을 Chrome, Edge, Safari 등 브라우저에서 엽니다.
   CSS·JS는 HTML 내부에 포함되어 있고 도식은 로컬 SVG, 비교 캡처는 captures/에 있습니다.
   외부 CDN·인터넷 연결·제품 서버·DB·설치된 하네스가 필요하지 않습니다.
3. 브라우저의 file:// 제한이 있으면, 압축 해제한 memo-v1-review 폴더에서 아래 명령을 실행합니다.

   python3 -m http.server 8773 --bind 127.0.0.1 --directory .

   http://127.0.0.1:8773/ 를 엽니다. Python 3 표준 라이브러리만 필요합니다.
   이는 선택적인 로컬 열람이며 공개 배포가 아닙니다. 종료는 Ctrl+C입니다.

## 포함 자료와 범위

- index.html, SVG 도식, 승인 시안/플랫폼 비교 캡처, 필요한 근거의 읽기용 HTML 사본
- provenance.json, task-executions.json, ui-verification.json, http-verification.json
- 원본 DB, 개인 설정, 원본 세션 로그, 설치된 하네스는 포함하지 않습니다.
  sources/.harness/는 선별된 기존 검증 결과의 읽기용 HTML 사본이며 설치 하네스/원문 로그가 아닙니다.
- 원본 소스 경로/해시는 추적용 텍스트로 남아 있습니다. 클릭 가능한 링크는 패키지 내부 상대 경로입니다.
- 보고서는 기존 시점의 스냅샷입니다. DB 단일 조회 근거를 전체 영속성/중복 방지 통과로 확대하지 않습니다.
  보고서 표시 검증 PASS는 제품 전체 인수 PASS가 아닙니다. v1 전체 BLOCKED 상태는 유지합니다.

## 재생성과 패키지 검증

원본 프로젝트에서만 수동 재생성합니다 (ZIP 안에는 제품/생성 환경을 포함하지 않습니다).

   rtk proxy python3 tools/v1-report/generate.py
   rtk proxy python3 tools/v1-report/package.py

package-manifest.json에 포함 파일의 SHA-256과 추출 검증 범위를 기록했습니다.
실제 ZIP을 별도 임시 폴더에 풀고 모든 HTML/SVG/CSS 자산 참조 및 파일 해시를 대조합니다.
원본 문서 안의 과거 경로는 HTML 사본의 인용 텍스트이며, 클릭 링크 검사 대상과 구분합니다.
'''
if args.agreement:
 readme=readme.replace('`memo-v1-review/index.html`','`memo-v1-agreement-review/agreement-review/index.html`')
 readme=readme.replace('memo-v1-review 폴더','memo-v1-agreement-review 폴더')
 readme=readme.replace('http://127.0.0.1:8773/ 를','http://127.0.0.1:8773/agreement-review/index.html 를')
 readme=readme.replace('tools/v1-report/generate.py','tools/v1-report/agreement.py').replace('tools/v1-report/package.py','tools/v1-report/package.py --agreement')
 readme+='\n## 개편본과 이전 보고서 구분\n\n첫 화면은 agreement-review/index.html 입니다. 루트 index.html은 개편본에서 연결하는 이전 상세 보고서 이력입니다.\n미저장 뒤로가기 확인창 C-DISCARD-CONFIRM의 세 플랫폼 상태 비교 NOT_RUN 정정도 포함했습니다.\n이전 보고서의 PASS나 표시 검증을 개편본의 새 제품 인수 PASS로 취급하지 않습니다.\n'
(stage/'README.md').write_text(readme)
hashes={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file()}
manifest=dict(generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),entry=ENTRY,report_sha256=hashes[ENTRY],files=hashes,scope='portable derived report only; product verification not rerun',verification='actual ZIP extraction, local HTML/SVG/CSS reference closure and SHA256 checks; excludes manifest self hash')
(stage/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(DEST,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
 for path in sorted(stage.rglob('*')):
  if path.is_file():archive.write(path,str(Path(PACKAGE)/path.relative_to(stage)))
extracted=temporary/'extracted';extracted.mkdir()
with zipfile.ZipFile(DEST) as archive:
 assert archive.testzip() is None
 for item in archive.infolist():
  assert not Path(item.filename).is_absolute() and '..' not in Path(item.filename).parts
 archive.extractall(extracted)
root=extracted/PACKAGE;checked=0
for path in root.rglob('*'):
 if not path.is_file():continue
 relative=str(path.relative_to(root))
 if relative in hashes:assert hashlib.sha256(path.read_bytes()).hexdigest()==hashes[relative],relative
 for reference in references(path):
  if resolve(root,path,reference):checked+=1
result=dict(result='PASS',zip=str(DEST),zip_sha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),zip_bytes=DEST.stat().st_size,extracted_to=str(root),files=len(hashes)+1,checked_relative_references=checked,broken_links=0,missing_assets=0,scope='ZIP integrity + extracted file hashes + local reference closure; no product tests')
audit=DEST.with_suffix('.verification.json');audit.write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
