"""Execute the isolated Activity relaunch test and preserve fresh Gradle JUnit cases."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
output = root / 'verification/memo-evidence'
output.mkdir(parents=True, exist_ok=True)
command = ['rtk', 'proxy', './gradlew', ':composeApp:cleanConnectedDebugAndroidTest',
           ':composeApp:connectedDebugAndroidTest',
           '-Pandroid.testInstrumentationRunnerArguments.class=dev.yeoback.app.MemoRestartTest', '--console=plain']
environment = os.environ.copy()
if not environment.get('ANDROID_SERIAL'):
    inventory = subprocess.check_output(['rtk', 'proxy', 'adb', 'devices'], text=True)
    devices = [line.split()[0] for line in inventory.splitlines() if line.startswith('emulator-') and line.split()[1] == 'device']
    if len(devices) != 1:
        raise RuntimeError('Set ANDROID_SERIAL or boot exactly one dedicated emulator')
    environment['ANDROID_SERIAL'] = devices[0]
start = time.time_ns()
with (output / 'android-execution.log').open('w') as log:
    result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, env=environment)
reports = []
suites = ET.Element('testsuites')
for path in sorted((root / 'composeApp/build/outputs/androidTest-results/connected').rglob('*.xml')):
    if path.stat().st_mtime_ns < start:
        continue
    data = path.read_bytes()
    reports.append({'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(data).hexdigest()})
    tree = ET.fromstring(data)
    if tree.tag == 'testsuite':
        suites.append(tree)
    else:
        suites.extend(tree.findall('testsuite'))
metadata = {'command': command, 'device': environment.get('ANDROID_SERIAL'),
            'exit_code': result.returncode, 'reports': reports}
(output / 'android-execution.json').write_text(json.dumps(metadata, indent=2))
if not reports:
    sys.exit(result.returncode or 2)
ET.ElementTree(suites).write(output / 'android-result.xml', encoding='utf-8', xml_declaration=True)
sys.exit(result.returncode)
