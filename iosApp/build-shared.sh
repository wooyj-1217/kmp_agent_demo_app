#!/bin/sh
set -eu
cd "$SRCROOT/.."
if [ -z "${JAVA_HOME:-}" ]; then JAVA_HOME=$(/usr/libexec/java_home -v 17); export JAVA_HOME; fi
./gradlew :composeApp:embedAndSignAppleFrameworkForXcode --console=plain
