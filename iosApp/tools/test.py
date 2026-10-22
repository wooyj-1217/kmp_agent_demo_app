"""Create an isolated simulator, run real XCUITest, retain its result bundle, clean up only that device."""
from pathlib import Path
import json
import subprocess
import time
import urllib.request
import sys

root=Path(__file__).resolve().parents[2]
folder=root/".harness/v1"
def json_command(*args): return json.loads(subprocess.check_output(args,text=True))
runtimes=json_command("xcrun","simctl","list","runtimes","-j")["runtimes"]
runtime=next((r for r in runtimes if r.get("isAvailable") and r["name"].startswith("iOS")),None)
assert runtime, "No installed available iOS runtime; test NOT_RUN"
types=json_command("xcrun","simctl","list","devicetypes","-j")["devicetypes"]
device=next((d for prefix in ["iPhone 17","iPhone 16"] for d in types if d["name"].startswith(prefix)),None)
assert device, "No supported iPhone test device type found; no existing device modified"
with urllib.request.urlopen("http://127.0.0.1:8080/api/v1/memos",timeout=5) as response: assert response.status==200
arguments=sys.argv[1:]
if arguments[:1]==["--reuse-id"]:
    identifier=arguments[1]; arguments=arguments[2:]
    prior=[json.loads(p.read_text()) for p in folder.glob('ios-test-*-simulator.json')]
    assert any(r['device_id']==identifier and r.get('purpose')=='isolated product test; not a user simulator' for r in prior)
    known=json_command('xcrun','simctl','list','devices','-j')['devices']
    assert any(d['udid']==identifier and d['name']=='Memo v1 isolated test' and d['state']=='Shutdown' for ds in known.values() for d in ds)
else:
    identifier=subprocess.check_output(["xcrun","simctl","create","Memo v1 isolated test",device["identifier"],runtime["identifier"]],text=True).strip()
receipt={"device_id":identifier,"runtime":runtime,"device_type":device,"purpose":"isolated product test; not a user simulator"}
result=folder/("ios-test-"+time.strftime("%Y%m%d-%H%M%S")+".xcresult")
receipt_path=folder/(result.stem+"-simulator.json")
receipt_path.write_text(json.dumps(receipt,indent=2)+"\n")
try:
    subprocess.run(["xcrun","simctl","boot",identifier],check=True)
    subprocess.run(["xcrun","simctl","bootstatus",identifier,"-b"],check=True,timeout=240)
    command=["xcodebuild","-quiet","-project","iosApp/Memo.xcodeproj","-scheme","Memo","-configuration","Debug","-destination",f"platform=iOS Simulator,id={identifier}","-parallel-testing-enabled","NO","-derivedDataPath",str(folder/"ios-derived"),"-resultBundlePath",str(result),"CODE_SIGNING_ALLOWED=NO","test"]
    command.extend(arguments)
    run=subprocess.run(command,cwd=root)
    receipt.update({"test_exit":run.returncode,"result_bundle":str(result)})
    receipt_path.write_text(json.dumps(receipt,indent=2)+"\n")
    raise SystemExit(run.returncode)
finally:
    subprocess.run(["xcrun","simctl","shutdown",identifier],check=False)
    # Keep the stopped test device and evidence for debugging; never delete a user's simulator.
