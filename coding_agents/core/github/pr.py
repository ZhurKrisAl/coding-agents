"""PR helpers: diff, files, CI status, publish review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PRContext:
    """Context for reviewer: issue ref, diff, files, CI info."""

    number: int
    title: str
    body: str
    diff: str
    changed_files: list[str]
    base_ref: str
    head_ref: str
    ci_conclusion: str | None  # success, failure, etc.
    ci_summary: str  # human-readable summary or log links


def get_pr_context(
    pull: Any,
    ci_conclusion: str | None = None,
    ci_summary: str = "",
) -> PRContext:
    """Build PR context from PyGithub PullRequest."""
    diff = pull.diff_url
    try:
        diff_content = pull.get_diff()
    except Exception:
        diff_content = ""
    files = [f.filename for f in pull.get_files()]
    return PRContext(
        number=pull.number,
        title=pull.title or "",
        body=pull.body or "",
        diff=diff_content or f"(see {diff})",
        changed_files=files,
        base_ref=pull.base.ref,
        head_ref=pull.head.ref,
        ci_conclusion=ci_conclusion,
        ci_summary=ci_summary,
    )


def publish_review(
    pull: Any,
    event: str,
    body: str,
    comments: list[dict[str, str]] | None = None,
) -> Any:
    """Submit GitHub Review: APPROVE or REQUEST_CHANGES with optional inline comments.

    comments: list of {path, line (or line as str), body}
    """
    if comments is None:
        comments = []
    # PyGithub: create_review(event, body, commit_id=None, comments=[])
    # comments: list of dict with 'path', 'line', 'body' (and optionally 'side')
    formatted = []
    for c in comments:
        formatted.append({
            "path": c["path"],
            "line": int(c.get("line", 0)) if c.get("line") else None,
            "body": c.get("body", ""),
        })
    return pull.create_review(event=event, body=body, comments=formatted)
