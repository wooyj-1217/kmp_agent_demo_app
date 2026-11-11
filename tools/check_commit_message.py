#!/usr/bin/env python3
"""Check the mechanical portion of docs/commit-policy.md; never edit messages."""
import re
import subprocess
import sys
from pathlib import Path

HEADER = re.compile(
    r"^(feat|fix|refactor|perf|docs|test|chore|build|ci|style|revert)"
    r"(?:\([^()\s]+\))?(!)?: (\S.*)$"
)
FIELDS = ("이유", "영향", "검증", "기록")


def validate(message):
    lines = message.strip().splitlines()
    if not lines:
        return ["커밋 메시지가 비어 있습니다."]
    title = lines[0]
    match = HEADER.fullmatch(title)
    if not match:
        return ["제목 형식: <type>(<scope>): <한국어 변경 요약>"]
    errors = []
    if len(title) > 72:
        errors.append("제목은 72자 이하여야 합니다.")
    if not re.search(r"[가-힣]", match[3]):
        errors.append("제목 설명에 한국어를 사용하세요.")
    if title.endswith("."):
        errors.append("제목 끝 마침표를 제거하세요.")
    if len(lines) > 1 and lines[1].strip():
        errors.append("제목과 본문 사이에 빈 줄을 두세요.")
    body = "\n".join(lines[2:])
    # docs/chore 등의 의미 있는 정책 변경 여부는 사람이 판단한다.
    required = match[1] in {"feat", "fix", "refactor", "perf", "revert"} or match[2]
    if required or body.strip():
        for field in FIELDS:
            if not re.search(rf"^{field}:[ \t]*\S[^\n]*$", body, re.MULTILINE):
                errors.append(f"본문에 '{field}: <실제 내용>'을 작성하세요.")
    if match[2] and not re.search(r"^BREAKING CHANGE:[ \t]*\S", body, re.MULTILINE):
        errors.append("호환성 변경에는 BREAKING CHANGE: 설명이 필요합니다.")
    if match[1] == "revert" and not re.search(r"(?<![0-9a-f])[0-9a-f]{7,40}(?![0-9a-f])", body):
        errors.append("되돌리는 커밋 SHA(7~40자리)를 본문에 적으세요.")
    return errors


def main():
    if len(sys.argv) != 2:
        print("사용법: python3 tools/check_commit_message.py <메시지 파일>", file=sys.stderr)
        return 2
    # Git의 주석 문자 설정과 편집기 주석을 Git 자체로 처리한다.
    raw = Path(sys.argv[1]).read_bytes()
    cleaned = subprocess.run(
        ["git", "stripspace", "--strip-comments"], input=raw,
        stdout=subprocess.PIPE, check=True,
    ).stdout.decode("utf-8")
    errors = validate(cleaned)
    if errors:
        print("커밋 메시지 검사 실패:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("규칙: docs/commit-policy.md", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
