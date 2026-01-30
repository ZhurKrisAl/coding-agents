"""Git repository operations: clone, branch, commit, push."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

import git
from git import Repo
from git.exc import GitCommandError


def _slug(s: str, max_len: int = 30) -> str:
    """Safe branch slug from title."""
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s).strip("-").lower()
    return s[:max_len] if s else "issue"


class GitRepo:
    """Wrapper over GitPython for agent operations: branch, commit, push."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._repo: Repo | None = None

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

    def add(self, paths: List[str] | None = None) -> None:
        """Stage paths; if None, stage all."""
        if paths:
            for p in paths:
                self.repo.index.add(p)
        else:
            self.repo.index.add("*")

    def commit(self, message: str, paths: List[str] | None = None) -> str:
        """Commit with message; returns commit sha."""
        if paths:
            self.add(paths)
        else:
            self.repo.index.add("*")
        return self.repo.index.commit(message)

    def push(self, remote: str = "origin", branch: str | None = None) -> None:
        """Push branch to remote."""
        ref = branch or self.repo.active_branch.name
        try:
            self.repo.remote(remote).push(ref)
        except GitCommandError as e:
            if "rejected" in str(e).lower():
                self.repo.remote(remote).push(ref, force_with_lease=True)
            else:
                raise

    def file_inventory(self, relative_to: str | Path | None = None) -> List[str]:
        """List tracked files (paths relative to repo root or relative_to)."""
        base = Path(relative_to) if relative_to else self.path
        out: List[str] = []
        for item in self.repo.tree().traverse():
            if item.type == "blob":
                p = Path(item.path)
                if not str(p).startswith(".git"):
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
