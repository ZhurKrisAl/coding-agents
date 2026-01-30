"""Unit tests: parsing Issue context."""

import pytest

from coding_agents.core.github.issues import get_issue_context
from tests.conftest import MockIssue


def test_get_issue_context(sample_issue: MockIssue) -> None:
    ctx = get_issue_context(sample_issue)
    assert ctx.number == 1
    assert ctx.title == "Add greeting function"
    assert "greet" in ctx.body
    assert "enhancement" in ctx.labels
    assert ctx.state == "open"


def test_get_issue_context_empty_body() -> None:
    issue = MockIssue(2, "Title", "", [], "open")
    ctx = get_issue_context(issue)
    assert ctx.number == 2
    assert ctx.body == ""
    assert ctx.labels == []
