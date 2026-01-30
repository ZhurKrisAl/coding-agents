"""Unit tests: Reviewer Agent output parsing and report generation."""

from agents.reviewer_agent.review_output import ReviewOutput


def test_review_output_parsing_pass():
    text = """VERDICT: PASS
REASON: Looks good
COMMENTS: All checks passed"""

    out = ReviewOutput.from_llm_output(text, ci_conclusion="success", changed_files=["a.py"])

    assert out.verdict == "Pass"
    assert out.reason == "Looks good"
    assert "All checks passed" in out.summary


def test_review_output_parsing_fail():
    text = """VERDICT: FAIL
REASON: Tests are failing
COMMENTS: Please fix"""

    out = ReviewOutput.from_llm_output(text, ci_conclusion="failure", changed_files=["a.py"])

    assert out.verdict == "Fail"
    assert "Tests are failing" in out.reason
