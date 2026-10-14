"""The pre-commit hook in .githooks/ refuses files under data/private/ (fit-engine-poc 1.3)."""

import shutil
import subprocess
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / ".githooks" / "pre-commit"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def repo_with_hook(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "test")
    hooks = tmp_path / ".githooks"
    hooks.mkdir()
    shutil.copy(HOOK, hooks / "pre-commit")
    git(tmp_path, "config", "core.hooksPath", ".githooks")
    return tmp_path


def test_commit_with_a_private_file_fails_with_an_explanation(tmp_path):
    repo = repo_with_hook(tmp_path)
    (repo / "data" / "private").mkdir(parents=True)
    (repo / "data" / "private" / "study.csv").write_text("P01,180,75\n")
    git(repo, "add", "-f", "data/private/study.csv")
    result = git(repo, "commit", "-m", "oops")
    assert result.returncode != 0
    assert "data/private/study.csv" in result.stderr
    assert "personal" in result.stderr


def test_commit_without_private_files_passes(tmp_path):
    repo = repo_with_hook(tmp_path)
    (repo / "README.md").write_text("hello\n")
    git(repo, "add", "README.md")
    assert git(repo, "commit", "-m", "ok").returncode == 0
