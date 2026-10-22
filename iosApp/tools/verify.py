"""Preflight and actual simulator build. Never accepts Apple license agreements."""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[2]
for command in [["xcodebuild","-version"],["xcrun","--sdk","iphonesimulator","--show-sdk-path"],["plutil","-lint",str(root/"iosApp/Memo.xcodeproj/project.pbxproj"),str(root/"iosApp/Info.plist")]]:
    result=subprocess.run(command,cwd=root)
    if result.returncode:
        print("iOS preflight failed; no license agreement or setup acceptance was performed.")
        raise SystemExit(result.returncode)
result=subprocess.run(["xcodebuild","-quiet","-project","iosApp/Memo.xcodeproj","-scheme","Memo","-configuration","Debug","-sdk","iphonesimulator","-destination","generic/platform=iOS Simulator","-derivedDataPath",str(root/".harness/v1/ios-derived"),"CODE_SIGNING_ALLOWED=NO","build"],cwd=root)
raise SystemExit(result.returncode)
