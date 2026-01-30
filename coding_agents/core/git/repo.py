"""Git repository operations: clone, branch, commit, push."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, List, Optional, cast

from git import Repo
from git.exc import GitCommandError

import time
from typing import Optional

def _slug(s: str, max_len: int = 30) -> str:
    """Safe branch slug from title."""
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s).strip("-").lower()
    return s[:max_len] if s else "issue"


class GitRepo:
    """Wrapper over GitPython for agent operations: branch, commit, push."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._repo: Optional[Repo] = None

    @property
    def repo(self) -> Repo:
        if self._repo is None:
            self._repo = Repo(self.path)
        return self._repo

    def branch_name(self, issue_id: int, title: str) -> str:
        """Generate branch name: agent/issue-<id>-<slug>."""
        slug = _slug(title)
        return f"agent/issue-{issue_id}-{slug}"

    def create_branch(self, name: str, start: str = "HEAD") -> None:
        """Create and checkout branch."""
        self.repo.git.checkout("-b", name, start)

    def checkout(self, ref: str) -> None:
        """Checkout ref."""
        self.repo.git.checkout(ref)

    def add(self, paths: Optional[List[str]] = None) -> None:
        """Stage paths; if None, stage all."""
        if paths:
            for p in paths:
                self.repo.index.add([p])
        else:
            # More reliable than "*" and matches "stage everything under repo"
            self.repo.index.add(["."])

    def commit(self, message: str, paths: Optional[List[str]] = None) -> str:
        """Commit with message; returns commit sha."""
        self.add(paths)
        commit_obj = self.repo.index.commit(message)
        return commit_obj.hexsha

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> None:
        """Push branch to remote with retries (more reliable in GitHub Actions)."""
        ref = branch or self.repo.active_branch.name

        token = os.environ.get("GITHUB_TOKEN")
        repo_full = os.environ.get("GITHUB_REPOSITORY")  # owner/repo
        push_url: Optional[str] = None
        if token and repo_full:
            push_url = f"https://x-access-token:{token}@github.com/{repo_full}.git"

        last_err: Optional[Exception] = None
        for attempt in range(3):
            try:
                if push_url:
                    # push explicitly to URL (bypasses potentially odd origin config)
                    self.repo.git.push("--porcelain", push_url, ref)
                else:
                    self.repo.remote(remote).push(ref)
                return
            except GitCommandError as e:
                last_err = e
                msg = str(e).lower()
                if any(x in msg for x in ["rpc failed", "http 500", "hung up", "internal server error"]):
                    time.sleep(5 * (attempt + 1))
                    continue
                if "rejected" in msg:
                    if push_url:
                        self.repo.git.push("--porcelain", "--force-with-lease", push_url, ref)
                    else:
                        self.repo.remote(remote).push(ref, force_with_lease=True)
                    return
                raise

        raise RuntimeError(f"Push failed after retries: {last_err}")


    def file_inventory(self, relative_to: str | Path | None = None) -> List[str]:
        """List tracked files (paths relative to repo root).

        Note: GitPython typing stubs for tree traversal are messy; we cast to Any
        when reading .type and .path.
        """
        out: List[str] = []

        # If relative_to is provided, we still return paths relative to repo root.
        # (You can later post-process if you want relative_to paths.)
        _ = relative_to  # intentionally unused for now

        for item in self.repo.tree().traverse():
            it = cast(Any, item)
            if getattr(it, "type", None) == "blob":
                p = Path(getattr(it, "path", ""))
                if p and not str(p).startswith(".git"):
                    out.append(str(p))

        return sorted(out)

    def list_files(self) -> List[str]:
        """List all files in working tree (non-ignored)."""
        out: List[str] = []
        for root, _dirs, files in os.walk(self.path):
            if ".git" in root:
                continue
            for f in files:
                p = Path(root) / f
                try:
                    r = p.relative_to(self.path)
                    if not any(part.startswith(".") for part in r.parts):
                        out.append(str(r))
                except ValueError:
                    pass
        return sorted(out)

    def write_file(self, path: str, content: str) -> None:
        """Write file under repo root."""
        full = self.path / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")

    def read_file(self, path: str) -> str:
        """Read file from repo root."""
        return (self.path / path).read_text(encoding="utf-8")

    def file_exists(self, path: str) -> bool:
        """Check if path exists in repo."""
        return (self.path / path).exists()
