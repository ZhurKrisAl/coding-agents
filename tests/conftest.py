"""Pytest fixtures."""

from __future__ import annotations

import pytest


class MockIssue:
    """Minimal mock for PyGithub Issue."""

    def __init__(
        self,
        number: int,
        title: str,
        body: str,
        labels: list[str],
        state: str = "open",
    ) -> None:
        self.number = number
        self.title = title
        self.body = body
        self.labels = [type("L", (), {"name": lb})() for lb in labels]
        self.state = state


@pytest.fixture
def sample_issue