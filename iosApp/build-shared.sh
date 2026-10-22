#!/bin/sh
set -eu
cd "$SRCROOT/.."
case "$SDK_NAME" in
  iphonesimulator*) target=IosSimulatorArm64 ;;
  iphoneos*) target=IosArm64 ;;
  *) echo "Unsupported iOS SDK: $SDK_NAME"; exit 1 ;;
esac
./gradlew ":shared:link${CONFIGURATION}Framework${target}" --console=plain
