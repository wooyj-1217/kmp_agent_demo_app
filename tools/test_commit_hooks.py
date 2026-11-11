import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("checker", ROOT / "tools/check_commit_message.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
VALID = "fix(storage): 저장 실패 시 초안 보존\n\n이유: 재입력 방지\n영향: 실패 시 편집 유지\n검증: 실패 주입 검사 통과\n기록: docs/work-items/2026/example.md\n"


class CommitHooksTest(unittest.TestCase):
    def test_policy_cases(self):
        self.assertEqual(checker.validate(VALID), [])
        self.assertEqual(checker.validate("docs: 오타 수정"), [])
        for bad in ("fix: 초안 보존", "fix: preserve draft", "메시지",
                    VALID.replace("검증: 실패 주입 검사 통과", "검증:"),
                    VALID.replace("\n\n", "\n", 1),
                    VALID.replace("fix(storage):", "fix(storage)!:"),
                    VALID.replace("fix(storage):", "revert:")):
            with self.subTest(message=bad):
                self.assertTrue(checker.validate(bad))
        self.assertEqual(checker.validate(VALID.replace("fix(storage):", "fix(storage)!:") +
                                          "BREAKING CHANGE: 이전 형식 이전 필요\n"), [])
        self.assertEqual(checker.validate(VALID.replace("fix(storage):", "revert:") +
                                          "대상: abc1234\n"), [])

    def test_real_git_hook_and_installation(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
            def run(*args):
                return subprocess.run(args, cwd=repo, env=env, text=True, capture_output=True)
            self.assertEqual(run("git", "init", "-q").returncode, 0)
            (repo / "tools").mkdir()
            (repo / ".githooks").mkdir()
            for name in ("check_commit_message.py", "install_git_hooks.py"):
                shutil.copy2(ROOT / "tools" / name, repo / "tools" / name)
            shutil.copy2(ROOT / ".githooks/commit-msg", repo / ".githooks/commit-msg")
            # 다른 설정/활성 훅을 훼손하지 않아야 한다.
            run("git", "config", "core.hooksPath", "other-hooks")
            self.assertNotEqual(run("python3", "tools/install_git_hooks.py").returncode, 0)
            run("git", "config", "--unset", "core.hooksPath")
            previous = repo / ".git/hooks/pre-commit"
            previous.write_text("#!/bin/sh\nexit 0\n")
            previous.chmod(0o755)
            self.assertNotEqual(run("python3", "tools/install_git_hooks.py").returncode, 0)
            previous.unlink()
            for _ in range(2):
                result = run("python3", "tools/install_git_hooks.py")
                self.assertEqual(result.returncode, 0, result.stderr)
            run("git", "config", "user.name", "Hook Test")
            run("git", "config", "user.email", "hook@example.invalid")
            result = run("git", "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "bad message")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("커밋 메시지 검사 실패", result.stderr)
            result = run("git", "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", VALID)
            self.assertEqual(result.returncode, 0, result.stderr)
            # 설정된 주석 문자와 편집기 주석을 지원한다.
            run("git", "config", "core.commentChar", ";")
            msg = repo / "message.txt"
            msg.write_text(VALID + "; 편집기 주석\n")
            self.assertEqual(run(".githooks/commit-msg", str(msg)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
