"""Unit tests: iteration policy and stop conditions."""

from coding_agents.core.policies.iterations import IterationPolicy, StopReason


def test_policy_success() -> None:
    policy = IterationPolicy(max_iterations=5)
    stop, reason = policy.should_stop(iteration=0, ci_passed=True, reviewer_approved=True)
    assert stop is True
    assert reason == StopReason.SUCCESS


def test_policy_max_iterations() -> None:
    policy = IterationPolicy(max_iterations=3)
    stop, reason = policy.should_stop(iteration=3, ci_passed=False, reviewer_approved=False)
    assert stop is True
    assert reason == StopReason.MAX_ITERATIONS


def test_policy_retry_on_fail() -> None:
    policy = IterationPolicy(max_iterations=5)
    stop, reason = policy.should_stop(iteration=1, ci_passed=True, reviewer_approved=False)
    assert stop is False
    assert reason == StopReason.REVIEWER_FAIL


def test_can_retry() -> None:
    policy = IterationPolicy(max_iterations=3)
    assert policy.can_retry(0) is True
    assert policy.can_retry(2) is True
    assert policy.can_retry(3) is False
