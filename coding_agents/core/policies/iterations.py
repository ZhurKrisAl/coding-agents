"""Iteration policy: max iterations, stop conditions, no infinite loops."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StopReason(str, Enum):
    """Reason to stop the agent loop."""

    SUCCESS = "success"           # CI green + reviewer approve
    MAX_ITERATIONS = "max_iterations"
    REVIEWER_APPROVE = "reviewer_approve"
    REVIEWER_FAIL = "reviewer_fail"
    CI_FAIL = "ci_fail"
    MANUAL = "manual"


@dataclass
class IterationPolicy:
    """Gatekeeping: max iterations, deterministic stop."""

    max_iterations: int = 5
    require_ci_green: bool = True
    require_reviewer_approve: bool = True

    def should_stop(
        self,
        iteration: int,
        ci_passed: bool,
        reviewer_approved: bool,
    ) -> tuple[bool, StopReason]:
        """Return (should_stop, reason)."""
        if iteration >= self.max_iterations:
            return True, StopReason.MAX_ITERATIONS
        if self.require_ci_green and not ci_passed:
            return False, StopReason.CI_FAIL  # don't stop, retry
        if self.require_reviewer_approve and not reviewer_approved:
            return False, StopReason.REVIEWER_FAIL  # don't stop, retry
        if ci_passed and reviewer_approved:
            return True, StopReason.SUCCESS
        return False, StopReason.REVIEWER_FAIL

    def can_retry(self, iteration: int) -> bool:
        """Whether another iteration is allowed."""
        return iteration < self.max_iterations
