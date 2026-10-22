"""Stable project-owned entry point for the pinned tool."""
import base64
import json
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[1]
journal = root / ".harness/install-transaction.json"
if sys.argv[1:2] in (["recover"], ["status"]) and journal.exists():
    previous = json.loads(journal.read_text())["snapshot"].get(".kmp-agent/installation.json")
    manifest = json.loads(base64.b64decode(previous["bytes"])) if previous else json.loads((root / ".kmp-agent/installation.json").read_text())
else:
    manifest = json.loads((root / ".kmp-agent/installation.json").read_text())
code = (root / manifest["code_path"]).resolve()
if manifest["mode"] == "installed" and not code.is_relative_to(root / ".kmp-agent/releases"):
    raise SystemExit("Invalid installation path; restore installation.json")
raise SystemExit(subprocess.call([sys.executable, str(code / "harness/cli.py"),
                                 "--target", str(root), *sys.argv[1:]], cwd=root))
