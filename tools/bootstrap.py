"""Fetch only the pinned official Gradle wrapper; no system installation."""
from pathlib import Path
from urllib.request import urlopen
import os

VERSION = "8.14.3"
root = Path(__file__).resolve().parents[1]
for name in ["gradlew", "gradlew.bat", "gradle/wrapper/gradle-wrapper.jar"]:
    url = f"https://raw.githubusercontent.com/gradle/gradle/v{VERSION}/{name}"
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(urlopen(url, timeout=40).read())
checksum = urlopen(f"https://services.gradle.org/distributions/gradle-{VERSION}-bin.zip.sha256", timeout=40).read().decode().strip()
(root / "gradle/wrapper/gradle-wrapper.properties").write_text(
    "distributionBase=GRADLE_USER_HOME\ndistributionPath=wrapper/dists\n"
    f"distributionUrl=https\\://services.gradle.org/distributions/gradle-{VERSION}-bin.zip\n"
    f"distributionSha256Sum={checksum}\nzipStoreBase=GRADLE_USER_HOME\nzipStorePath=wrapper/dists\n"
)
os.chmod(root / "gradlew", 0o755)
print(f"Official Gradle {VERSION} wrapper fetched; distribution SHA256 {checksum}")
