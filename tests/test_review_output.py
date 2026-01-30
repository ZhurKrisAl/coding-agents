"""Unit tests: Reviewer Agent output parsing and report generation."""

import pytest

from agents.reviewer_agent.review_output import ReviewOutput


def test_from_llm_output_pass() -> None:
    text = """
VERDICT: Pass
REASON: The PR implements the greeting function and tests as required by the Issue.
COMMENTS:
"""
    out = ReviewOutput.from_llm_output(text, ci_conclusion="success", changed_files=["utils.py"])
    assert out.verdict == "Pass"
    assert out.event == "APPROVE"
    assert len(out.reason) > 0


def test_from_llm_output_fail() -> None:
    text = """
VERDICT: Fail
REASON: The test does not cover the edge case mentioned in the Issue.
COMMENTS:
FILE: utils.py: 10: Consider adding a test for empty string.
"""
    out = ReviewOutput.from_llm_output(text, ci_conclusion="failure", changed_files=["utils.py"])
    assert out.verdict == "Fail"
    assert out.event == "REQUEST_CHANGES"
    assert "edge case" in out.reason or len(out.reason) > 0


def test_summary_contains_verdict_and_ci() -> None:
    text = "VERDICT: Pass\nREASON: All good.\nCOMMENTS:\n"
    out = ReviewOutput.from_llm_output(text, ci_conclusion="success", changed_files=[])
    assert "Pass" in out.summary
    assert "success" in out.summary
