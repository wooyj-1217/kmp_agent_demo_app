"""Read disposable localhost QA records after independent Web/Android/iOS executions."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

base = "http://127.0.0.1:8910"
def post(path, data, token=None):
    headers = {"Content-Type":"application/json"}
    if token: headers["Authorization"] = "Bearer " + token
    with urlopen(Request(base+path,json.dumps(data).encode(),headers),timeout=15) as r:
        return json.load(r)

account = post("/v1/login",dict(email="qa@teum.test",password="Teum-local-qa-2026!"))
try:
    snapshot = post("/v1/sync",{"operations":[]},account["token"])
    titles = {n["title"] for n in snapshot["notes"] if not n["purged"] and not n["deleted"]}
    expected = {"오늘의 작은 발견","Android native QA","iOS native QA"}
    result = {"result":"PASS" if expected <= titles else "FAIL", "scope":"actual records written by Web CUA, Android emulator instrumentation and iOS Simulator XCTest in the same new localhost backend",
              "verified_titles":sorted(expected & titles), "missing_titles":sorted(expected - titles), "api":"v1/sync", "contains_credentials":False}
    path = Path(__file__).resolve().parents[2] / "docs/memo-independent/sync-evidence.json"
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["result"] != "PASS": raise SystemExit(1)
finally:
    post("/v1/logout",{},account["token"])
