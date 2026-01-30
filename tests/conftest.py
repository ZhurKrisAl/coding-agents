"""Pytest fixtures."""

import pytest


class MockIssue:
    """Minimal mock for PyGithub Issue."""

    def __init__(self, number: int, title: str, body: str, labels: list[str], state: str = "open"):
        self.number = number
        self.title = title
        self.body = body
        self.labels = [type("L", (), {"name": lb})() for lb in labels]
        self.state = state


@pytest.fixture
def sample_issue() -> MockIssue:
    return MockIssue(
        number=1,
        title="Add greeting function",
        body="Add greet(name) that returns Hello, {name}!",
        labels=["enhancement"],
    )
