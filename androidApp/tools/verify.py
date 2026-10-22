"""Run native instrumentation only on the read-only emulator started for this request."""
from pathlib import Path
import os
import subprocess

root=Path(__file__).resolve().parents[2]
adb=str(Path.home()/"Library/Android/sdk/platform-tools/adb")
devices=subprocess.check_output([adb,"devices"],text=True)
active=[line.split()[0] for line in devices.splitlines()[1:] if line.strip() and line.split()[-1]=="device"]
assert active==["emulator-5554"], f"Unexpected connected device set: {active}; no install performed"
subprocess.run([adb,"-s","emulator-5554","reverse","tcp:8080","tcp:8080"],check=True)
env=dict(os.environ,ANDROID_SERIAL="emulator-5554")
result=subprocess.run([str(root/"gradlew"),"-p","androidApp","connectedDebugAndroidTest","--console=plain"],cwd=root,env=env)
raise SystemExit(result.returncode)
