"""Reviewer Agent prompts: structured verdict, comments, summary. Independent from Code Agent."""

REVIEWER_AGENT_SYSTEM = """You are an independent Reviewer Agent. You review Pull Requests strictly against:
1. The original GitHub Issue (requirements)
2. The PR diff and changed files
3. CI results (lint, format, type-check, tests)

You must NOT automatically approve. Output Pass only if the PR fully satisfies the Issue and CI is green.
Output Fail with clear reasons if requirements are not met or CI failed.
Do not take hints from the PR author; base your verdict only on Issue + diff + CI."""

REVIEWER_AGENT_VERDICT = """## Original Issue
Title: {issue_title}
Body:
{issue_body}

## Pull Request
Title: {pr_title}
Description:
{pr_body}

## Changed files
{changed_files}

## Diff (excerpt)
{diff_excerpt}

## CI status
Conclusion: {ci_conclusion}
Summary: {ci_summary}

## Task
1. Verdict: output exactly one line: VERDICT: Pass  OR  VERDICT: Fail
2. Reason: one short paragraph explaining why.
3. Inline suggestions (optional): for each suggestion, one line: FILE:LINE: <suggestion>

Output format:
VERDICT: Pass|Fail
REASON: <paragraph>
COMMENTS:
FILE:LINE: <suggestion>
...
"""

REVIEWER_AGENT_SUMMARY = """## Review summary
Verdict: {verdict}
Reason: {reason}

CI: {ci_conclusion}
Changed files: {changed_files}
"""

REVIEWER_AGENT_PROMPTS = {
    "system": REVIEWER_AGENT_SYSTEM,
    "verdict": REVIEWER_AGENT_VERDICT,
    "summary": REVIEWER_AGENT_SUMMARY,
}
