"""Structured review output: verdict, reason, inline comments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ReviewOutput:
    """Structured output from Reviewer Agent."""

    verdict: str  # Pass | Fail
    reason: str
    summary: str  # Human-readable summary for PR comment
    inline_comments: list[dict[str, Any]]  # [{path, line, body}, ...]
    event: str  # APPROVE | REQUEST_CHANGES

    @classmethod
    def from_llm_output(cls, text: str, ci_conclusion: str, changed_files: list[str]) -> "ReviewOutput":
        """Parse VERDICT/REASON/COMMENTS from agent output."""
        verdict = "Fail"
        reason = ""
        comments: list[dict[str, Any]] = []
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.strip().upper().startswith("VERDICT:"):
                v = line.split(":", 1)[-1].strip().upper()
                if "PASS" in v:
                    verdict = "Pass"
                else:
                    verdict = "Fail"
            if line.strip().upper().startswith("REASON:"):
                reason = line.split(":", 1)[-1].strip()
            if line.strip().upper().startswith("COMMENTS:"):
                for j in range(i + 1, len(lines)):
                    l2 = lines[j]
                    if l2.strip().upper().startswith("FILE:") and ":" in l2:
                        parts = l2.split(":", 2)
                        if len(parts) >= 3:
                            path = parts[1].strip()
                            line_num = parts[2].strip().split()[0] if parts[2].strip() else "1"
                            body = parts[2].strip().split(maxsplit=1)[-1] if len(parts[2].strip().split()) > 1 else "See review."
                            try:
                                line_no = int(line_num)
                            except ValueError:
                                line_no = 1
                            comments.append({"path": path, "line": line_no, "body": body})
                break
        summary = f"**Verdict: {verdict}**\n\nReason: {reason}\n\nCI: {ci_conclusion}"
        event = "APPROVE" if verdict == "Pass" else "REQUEST_CHANGES"
        return cls(
            verdict=verdict,
            reason=reason,
            summary=summary,
            inline_comments=[c for c in comments if c["path"] in changed_files][:10],
            event=event,
        )
