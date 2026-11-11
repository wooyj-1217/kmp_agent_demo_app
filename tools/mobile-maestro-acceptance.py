"""Build/install an isolated app and run real Maestro process-restart acceptance."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = sys.argv[1]
if PLATFORM not in {'android', 'ios'}:
    raise SystemExit('android or ios required')
TOKEN = uuid.uuid4().hex
OUT = ROOT / 'verification/maestro-memo' / (PLATFORM + '-' + TOKEN)
OUT.mkdir(parents=True)
APP_ID = 'dev.yeoback.maestro.acceptance'
TITLE = 'MemoTitle-' + TOKEN
BODY = 'MemoBody-' + TOKEN
CASE = 'MEMO-SAVE-RESTORE Maestro ' + PLATFORM
MAESTRO = os.environ.get('MEMO_MAESTRO_' + PLATFORM.upper() + '_BIN') or shutil.which('maestro') or 'maestro'
metadata = {'tool': 'Maestro', 'criterion_id': 'MEMO-SAVE-RESTORE', 'platform': PLATFORM,
            'token': TOKEN, 'title': TITLE, 'body': BODY, 'app_id': APP_ID,
            'commands': [], 'phase': 'BUILD', 'status': 'NOT_RUN',
            'environment': {key: os.environ.get(key) for key in ('JAVA_HOME', 'ANDROID_HOME', 'ANDROID_SDK_ROOT')}}

def execute(command, timeout=1200):
    entry = {'argv': command, 'started_ns': time.time_ns()}
    metadata['commands'].append(entry)
    path = OUT / ('command-' + str(len(metadata['commands'])) + '.log')
    with path.open('wb') as output:
        result = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
    entry.update(exit_code=result.returncode, finished_ns=time.time_ns(), log=str(path.relative_to(ROOT)))
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command)

def read(command):
    return subprocess.check_output(command, cwd=ROOT, text=True).strip()

def tree_hash(path):
    path = Path(path)
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    entries = {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(path.rglob('*')) if p.is_file()}
    return hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()

code = 2
try:
    metadata['commit'] = read(['rtk', 'proxy', 'git', 'rev-parse', 'HEAD'])
    metadata['git_tree'] = read(['rtk', 'proxy', 'git', 'rev-parse', 'HEAD^{tree}'])
    metadata['tool_bin'] = MAESTRO
    metadata['tool_bin_sha256'] = tree_hash(MAESTRO)
    tool_lib = Path(MAESTRO).resolve().parent.parent / 'lib'
    metadata['tool_library_sha256'] = {name: tree_hash(tool_lib / name) for name in ['dadb-2.0.0.jar', 'maestro-cli-2.10.0.jar'] if (tool_lib / name).is_file()}
    metadata['tool_identity'] = os.environ.get('MEMO_MAESTRO_' + PLATFORM.upper() + '_TOOL_ID', 'Maestro stock')
    metadata['maestro_version'] = read(['rtk', 'proxy', MAESTRO, '--version'])
    if PLATFORM == 'android':
        device = os.environ.get('MEMO_MAESTRO_ANDROID_DEVICE')
        if not device:
            devices = [line.split()[0] for line in read(['rtk', 'proxy', 'adb', 'devices']).splitlines()
                       if line.startswith('emulator-') and line.split()[1] == 'device']
            if len(devices) != 1:
                raise RuntimeError('Set MEMO_MAESTRO_ANDROID_DEVICE or boot exactly one dedicated emulator')
            device = devices[0]
        execute(['rtk', 'proxy', './gradlew', ':composeApp:assembleDebug',
                 '-PmemoAcceptanceAppId=' + APP_ID, '--console=plain'])
        artifact = ROOT / 'composeApp/build/outputs/apk/debug/composeApp-debug.apk'
        metadata.update(device=device, artifact=str(artifact), artifact_sha256=tree_hash(artifact))
        metadata['phase'] = 'INSTALL'
        execute(['rtk', 'proxy', 'adb', '-s', device, 'install', '-r', str(artifact)])
        installed = read(['rtk', 'proxy', 'adb', '-s', device, 'shell', 'pm', 'path', APP_ID]).removeprefix('package:')
        metadata['installed_path'] = installed
        installed_bytes = subprocess.check_output(['rtk', 'proxy', 'adb', '-s', device, 'exec-out', 'cat', installed])
        metadata['installed_sha256'] = hashlib.sha256(installed_bytes).hexdigest()
        preserved = OUT / 'installed-build/base.apk'
        preserved.parent.mkdir()
        preserved.write_bytes(installed_bytes)
        metadata.update(preserved_installed_artifact=str(preserved.relative_to(ROOT)), preserved_installed_sha256=tree_hash(preserved))
        if metadata['installed_sha256'] != metadata['artifact_sha256']:
            raise RuntimeError('Installed APK does not match built artifact')
    else:
        device = os.environ.get('MEMO_MAESTRO_IOS_DEVICE')
        if not device:
            inventory = json.loads(read(['rtk', 'proxy', 'xcrun', 'simctl', 'list', 'devices', 'booted', '--json']))
            devices = [item['udid'] for items in inventory['devices'].values() for item in items if item['state'] == 'Booted']
            if len(devices) != 1:
                raise RuntimeError('Set MEMO_MAESTRO_IOS_DEVICE or boot exactly one dedicated simulator')
            device = devices[0]
        derived = ROOT / 'verification/maestro-memo/ios-derived'
        execute(['rtk', 'proxy', 'xcodebuild', '-project', 'iosApp/Moa.xcodeproj', '-scheme', 'Moa',
                 '-configuration', 'Debug', '-destination', 'platform=iOS Simulator,id=' + device,
                 '-derivedDataPath', str(derived), 'PRODUCT_BUNDLE_IDENTIFIER=' + APP_ID,
                 'CODE_SIGNING_ALLOWED=NO', 'build'])
        artifact = derived / 'Build/Products/Debug-iphonesimulator/Moa.app'
        metadata.update(device=device, artifact=str(artifact), artifact_sha256=tree_hash(artifact))
        metadata['phase'] = 'INSTALL'
        execute(['rtk', 'proxy', 'xcrun', 'simctl', 'install', device, str(artifact)])
        installed = read(['rtk', 'proxy', 'xcrun', 'simctl', 'get_app_container', device, APP_ID, 'app'])
        metadata.update(installed_path=installed, installed_sha256=tree_hash(installed))
        if metadata["installed_sha256"] != metadata["artifact_sha256"]:
            raise RuntimeError("Installed iOS bundle does not match built artifact")
        preserved = OUT / 'installed-build/Moa.app'
        shutil.copytree(installed, preserved, symlinks=True)
        metadata.update(preserved_installed_artifact=str(preserved.relative_to(ROOT)), preserved_installed_sha256=tree_hash(preserved))
        if metadata['preserved_installed_sha256'] != metadata['installed_sha256']:
            raise RuntimeError('Preserved iOS artifact differs from installed artifact')
    metadata['phase'] = 'MAESTRO_SCENARIO'
    report = OUT / 'maestro-junit.xml'
    command = ['rtk', 'proxy', MAESTRO, 'test', '--device', device,
               '--format', 'JUNIT', '--output', str(report), '--debug-output', str(OUT / 'debug'),
               '--test-output-dir', str(OUT / 'artifacts'), '-e', 'APP_ID=' + APP_ID,
               '-e', 'TITLE=' + TITLE, '-e', 'BODY=' + BODY, '-e', 'CASE_NAME=' + CASE,
               '-e', 'EVIDENCE=' + str(OUT), 'maestro-flows/' + PLATFORM + '-memo-process-restart.yaml']
    try:
        execute(command, timeout=300)
        code = 0
    except subprocess.CalledProcessError as exc:
        code = exc.returncode
    if report.exists():
        ET.parse(report)  # Preserve Maestro's actual cases; never synthesize a passing test.
        shutil.copy2(report, ROOT / 'verification/maestro-memo' / (PLATFORM + '-result.xml'))
    metadata['checkpoint_screenshots'] = [str(p.relative_to(ROOT)) for p in OUT.rglob('*.png')]
    metadata['saved_before_stop'] = any(OUT.rglob('saved-before-process-stop.png'))
    metadata['relaunched_list'] = any(OUT.rglob('relaunched-list.png'))
    if code == 0 and not report.exists():
        code = 2
        metadata['reason'] = 'MAESTRO_REPORT_MISSING'
    metadata['status'] = 'OBSERVED_PASS' if code == 0 else 'FAIL'
    metadata['failure_phase'] = None if code == 0 else ('POST_RELAUNCH_SCENARIO' if metadata['saved_before_stop'] and metadata['relaunched_list'] else 'PRECONDITION_OR_LAUNCH')
except Exception as exc:
    metadata.update(status='NOT_RUN', reason=metadata['phase'] + '_UNAVAILABLE', error=str(exc))
finally:
    metadata['finished_ns'] = time.time_ns()
    (OUT / 'execution.json').write_text(json.dumps(metadata, indent=2))
    (ROOT / 'verification/maestro-memo' / (PLATFORM + '-latest.json')).write_text(json.dumps(metadata, indent=2))
    print(json.dumps({'tool': 'Maestro', 'platform': PLATFORM, 'status': metadata['status'],
                      'metadata': str(OUT / 'execution.json')}))
sys.exit(code)
