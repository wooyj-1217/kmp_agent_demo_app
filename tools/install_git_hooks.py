#!/usr/bin/env python3
"""Install repository hooks without replacing another hook setup."""
import os
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.run(["git", *args], text=True, capture_output=True, check=True).stdout.strip()


def main():
    root = Path(git("rev-parse", "--show-toplevel"))
    os.chdir(root)
    configured = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"], text=True, capture_output=True,
    )
    if configured.returncode not in (0, 1):
        raise SystemExit(configured.stderr)
    current = configured.stdout.strip()
    if current and current != ".githooks":
        raise SystemExit(f"기존 core.hooksPath={current} 보존: 자동 교체하지 않습니다.")
    if not current:
        hooks = Path(git("rev-parse", "--git-path", "hooks"))
        active = [p.name for p in hooks.iterdir()
                  if p.is_file() and not p.name.endswith(".sample") and os.access(p, os.X_OK)] if hooks.exists() else []
        if active:
            raise SystemExit(f"기존 실행 훅 보존: {', '.join(active)}. 통합 후 설치하세요.")
    hook = root / ".githooks" / "commit-msg"
    if not hook.is_file():
        raise SystemExit(".githooks/commit-msg 파일이 없습니다.")
    hook.chmod(hook.stat().st_mode | 0o111)
    git("config", "--local", "core.hooksPath", ".githooks")
    print("설치 완료: core.hooksPath=.githooks (이 저장소에만 적용)")


if __name__ == "__main__":
    main()
