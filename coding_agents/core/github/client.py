"""GitHub API client with retries on rate limit."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Optional, TypeVar, cast
from urllib.parse import urlparse

import github
from github import GithubException

if TYPE_CHECKING:
    from github.Repository import Repository

T = TypeVar("T")


def ensure_http_url(url: Optional[str]) -> str:
    u = (url or "").strip()
    if not u:
        return "https://api.github.com"
    p = urlparse(u)
    if p.scheme not in ("http", "https"):
        raise ValueError(f"Invalid GitHub base_url (missing scheme): {u}")
    return u


def _get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return token


class GitHubClient:
    """Wrapper around PyGithub with retries on rate limit and error handling."""

    def __init__(self, token: str | None = None, base_url: str | None = None) -> None:
        self._token = token or _get_token()
        resolved_base_url = ensure_http_url(base_url)
        self._client = github.Github(self._token, base_url=resolved_base_url)

    def _with_retry(self, fn: Callable[[], T], max_retries: int = 3) -> T:
        for attempt in range(max_retries):
            try:
                return fn()
            except GithubException as e:
                # very basic rate-limit handling
                if e.status == 403 and "rate limit" in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(60)
                        continue
                raise
        raise RuntimeError("Unreachable")

    def get_repo(self, full_name: str) -> Repository:
        """Get repository by owner/name."""
        return self._with_retry(lambda: self._client.get_repo(full_name))

    def get_issue(self, full_name: str, issue_number: int) -> Any:
        """Get issue by repo and number."""
        repo = self.get_repo(full_name)
        return self._with_retry(lambda: repo.get_issue(issue_number))

    def get_pull(self, full_name: str, pr_number: int) -> Any:
        """Get pull request by repo and number."""
        repo = self.get_repo(full_name)
        return self._with_retry(lambda: repo.get_pull(pr_number))

    def create_comment(self, full_name: str, issue_or_pr_number: int, body: str) -> Any:
        """Create comment on issue or PR."""
        repo = self.get_repo(full_name)
        issue = self._with_retry(lambda: repo.get_issue(issue_or_pr_number))
        return self._with_retry(lambda: issue.create_comment(body))

    def list_workflow_runs(self, full_name: str, branch: str | None = None, per_page: int = 10) -> Any:
        """List recent workflow runs for repo (optionally for branch).

        Notes:
        - PyGithub typing stubs are inconsistent for get_workflow_runs parameters.
        - We cast repo to Any to avoid mypy false-positives.
        - Some versions do not accept per_page; we limit results in Python.
        """
        repo = self.get_repo(full_name)
        repo_any = cast(Any, repo)

        def _fetch() -> Any:
            if branch:
                return repo_any.get_workflow_runs(branch=branch)
            return repo_any.get_workflow_runs()

        runs = self._with_retry(_fetch)

        try:
            return list(runs)[:per_page]
        except TypeError:
            return runs
