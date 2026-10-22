"""Isolated local browser-test fixture. Supervisor records actual server exit separately."""
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request

root = Path(__file__).resolve().parents[2]
folder = root / ".harness/v1/web-fixture"
folder.mkdir(parents=True, exist_ok=True)
pidfile = folder / "server.json"
if sys.argv[1] == "supervise":
    env = dict(os.environ, MEMO_DB=str(folder / "memos.db"), MEMO_WEB_ROOT=str(root / "web/build/dist/js/productionExecutable"), MEMO_PORT="8080")
    with (folder / "server.log").open("ab") as log:
        child = subprocess.Popen([str(root / "server/build/install/server/bin/server")], cwd=root, env=env, stdout=log, stderr=log)
        pidfile.write_text(json.dumps({"pid": child.pid, "port": 8080, "scope": "isolated disposable browser fixture"}))
        result = child.wait()
        (folder / "exit.json").write_text(json.dumps({"returncode": result, "reason": "observed child exit", "at": time.time()}))
elif sys.argv[1] == "start":
    if pidfile.exists() and not (folder / "exit.json").exists():
        try:
            os.kill(json.loads(pidfile.read_text())["pid"], 0)
            raise SystemExit("Fixture already running")
        except ProcessLookupError:
            pass
    (folder / "exit.json").unlink(missing_ok=True)
    subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "supervise"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(100):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8080/api/v1/memos", timeout=1) as response:
                assert response.status == 200
            print("Isolated fixture ready: http://127.0.0.1:8080")
            break
        except Exception:
            time.sleep(0.1)
    else:
        raise SystemExit("Fixture did not become ready")
elif sys.argv[1] == "stop":
    data = json.loads(pidfile.read_text())
    try:
        os.kill(data["pid"], signal.SIGTERM)
    except ProcessLookupError:
        pass
    for _ in range(100):
        if (folder / "exit.json").exists():
            print((folder / "exit.json").read_text())
            break
        time.sleep(0.1)
    else:
        raise SystemExit("Actual child exit UNKNOWN")
