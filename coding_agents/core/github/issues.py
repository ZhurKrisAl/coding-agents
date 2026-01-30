"""Issue helpers: fetch title, body, labels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class IssueContext:
    """Parsed issue context for agents."""

    number: int
    title: str
    body: str
    labels: list[str]
    state: str


def get_issue_context(issue: Any) -> IssueContext:
    """Extract structured context from PyGithub Issue."""
    return IssueContext(
        number=issue.number,
        title=issue.title or "",
        body=issue.body or "",
        labels=[lb.name for lb in (issue.labels or [])],
        state=issue.state or "open",
    )
