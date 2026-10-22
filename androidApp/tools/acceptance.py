"""Select only new acceptance tests and only our emulator; never install on attached phones."""
from pathlib import Path
import json
import subprocess
import time
import sys
import hashlib

root=Path(__file__).resolve().parents[2]
adb=str(Path.home()/'Library/Android/sdk/platform-tools/adb')
def device(*args): return subprocess.run([adb,'-s','emulator-5554',*args],check=True,capture_output=True,text=True)
assert device('emu','avd','name').stdout.splitlines()[0]=='Small_Phone'
assert device('shell','getprop','sys.boot_completed').stdout.strip()=='1'
live=sys.argv[1:]==['previewLiveServerReadOnly']
device('reverse','tcp:8080','tcp:8080' if live else 'tcp:18080')
device('reverse','tcp:18082','tcp:18082')
subprocess.run([str(root/'gradlew'),'-p','androidApp','assembleDebug','assembleDebugAndroidTest','--console=plain'],cwd=root,check=True)
tested_paths=['androidApp/src/main/kotlin/memo/android/MainActivity.kt','androidApp/src/androidTest/kotlin/memo/android/AcceptanceTest.kt',
              'androidApp/tools/acceptance.py','androidApp/build/outputs/apk/debug/memo-android-debug.apk',
              'androidApp/build/outputs/apk/androidTest/debug/memo-android-debug-androidTest.apk','shared/build/libs/shared-jvm.jar']
tested_files={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in tested_paths}
device('install','-r',str(root/'androidApp/build/outputs/apk/debug/memo-android-debug.apk'))
device('install','-r',str(root/'androidApp/build/outputs/apk/androidTest/debug/memo-android-debug-androidTest.apk'))
folder=root/'.harness/v1'/('android-acceptance-'+time.strftime('%Y%m%d-%H%M%S'))
folder.mkdir()
results=[]
known=['faultsPersistenceAndSaveRefresh','orderInitialFailureBoundariesAndBack','prepareProcessRecovery','finishProcessRecovery','prepareOrdinaryDraft','checkOrdinaryDraftAfterProcessRestart','prepareDuringPostRecovery','finishDuringPostRecovery','largeFontAndThreeLinePreview','failureEditKeepsFocus','designConformance','previewLiveServerReadOnly']
methods=sys.argv[1:] or known
assert all(m in known for m in methods)
for method in methods:
    # Separate invocations create a new target process. Force-stop makes the recovery boundary explicit.
    device('shell','am','force-stop','dev.memo.mvp')
    stopped_at=time.time()
    result=device('shell','am','instrument','-w','-r','-e','acceptance','true','-e','class','memo.android.AcceptanceTest#'+method,
                  'dev.memo.mvp.test/androidx.test.runner.AndroidJUnitRunner')
    (folder/(method+'.txt')).write_text(result.stdout+result.stderr)
    with (folder/(method+'.png')).open('wb') as stream:
        capture=subprocess.run([adb,'-s','emulator-5554','exec-out','run-as','dev.memo.mvp','cat',f'files/acceptance-{method}.png'],stdout=stream,stderr=subprocess.PIPE)
    passed='OK (1 test)' in result.stdout and 'FAILURES!!!' not in result.stdout
    results.append({'method':method,'result':'PASS' if passed else 'FAIL','adb_exit':result.returncode,
                    'screenshot':'COLLECTED' if capture.returncode==0 else 'MISSING','force_stopped_at':stopped_at})
    (folder/'summary.json').write_text(json.dumps({'device':'emulator-5554 / read-only Small_Phone API36 arm64',
        'target_process_force_stopped_between_tests':True,'tested_files':tested_files,'tests':results},indent=2)+'\n')
    print(method, 'PASS' if passed else result.stdout,flush=True)
    if not passed: raise SystemExit(1)
print(folder)
