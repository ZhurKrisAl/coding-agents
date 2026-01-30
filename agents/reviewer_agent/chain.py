"""ReviewerAgentChain: Issue + diff + CI → structured verdict + comments."""

from __future__ import annotations

from typing import Any

from coding_agents.core.github import GitHubClient, get_pr_context, publish_review
from coding_agents.core.github.pr import PRContext
from coding_agents.core.llm import get_llm
from coding_agents.core.observability.langfuse import trace_agent
from coding_agents.core.prompts.reviewer_agent import REVIEWER_AGENT_PROMPTS

from agents.reviewer_agent.review_output import ReviewOutput


class ReviewerAgentChain:
    """Independent Reviewer: Issue + diff + CI → verdict; separate prompts and policy."""

    def __init__(
        self,
        repo_full_name: str,
        github_client: GitHubClient | None = None,
        llm_provider: str | None = None,
        temperature: float = 0.1,
    ) -> None:
        self.repo_full_name = repo_full_name
        self.gh = github_client or GitHubClient()
        self.llm = get_llm(provider=llm_provider, temperature=temperature)

    def run(
        self,
        pr_number: int,
        issue_title: str,
        issue_body: str,
        ci_conclusion: str = "unknown",
        ci_summary: str = "",
    ) -> ReviewOutput:
        """Fetch PR context, run review chain, return structured output (no publish)."""
        metadata = {"pr_number": pr_number, "repo": self.repo_full_name, "agent": "reviewer_agent"}
        with trace_agent("reviewer_agent_run", metadata=metadata) as trace:
            return self._run_impl(
                pr_number, issue_title, issue_body, ci_conclusion, ci_summary, trace
            )

    def _run_impl(
        self,
        pr_number: int,
        issue_title: str,
        issue_body: str,
        ci_conclusion: str,
        ci_summary: str,
        trace: Any,
    ) -> ReviewOutput:
        pull = self.gh.get_pull(self.repo_full_name, pr_number)
        pr_ctx = get_pr_context(pull, ci_conclusion=ci_conclusion, ci_summary=ci_summary)
        diff_excerpt = pr_ctx.diff[:8000] if len(pr_ctx.diff) > 8000 else pr_ctx.diff
        prompt = REVIEWER_AGENT_PROMPTS["verdict"].format(
            issue_title=issue_title,
            issue_body=issue_body,
            pr_title=pr_ctx.title,
            pr_body=pr_ctx.body,
            changed_files="\n".join(pr_ctx.changed_files),
            diff_excerpt=diff_excerpt,
            ci_conclusion=pr_ctx.ci_conclusion or "unknown",
            ci_summary=pr_ctx.ci_summary,
        )
        if trace:
            trace.span(name="verdict", metadata={"model": self.llm.model_name})
        result = self.llm.invoke(prompt)
        return ReviewOutput.from_llm_output(
            result.content,
            ci_conclusion=pr_ctx.ci_conclusion or "unknown",
            changed_files=pr_ctx.changed_files,
        )

    def run_and_publish(
        self,
        pr_number: int,
        issue_title: str,
        issue_body: str,
        ci_conclusion: str = "unknown",
        ci_summary: str = "",
        post_comment: bool = True,
        post_review: bool = True,
    ) -> tuple[ReviewOutput, str]:
        """Run review and publish: PR comment, GitHub Review, return (output, job_summary)."""
        out = self.run(pr_number, issue_title, issue_body, ci_conclusion, ci_summary)
        pull = self.gh.get_pull(self.repo_full_name, pr_number)
        job_summary = f"## Reviewer Agent\n\n**Verdict:** {out.verdict}\n**Reason:** {out.reason}\n**CI:** {ci_conclusion}"
        if post_comment:
            self.gh.create_comment(self.repo_full_name, pr_number, out.summary)
        if post_review:
            comments = [{"path": c["path"], "line": c["line"], "body": c["body"]} for c in out.inline_comments]
            publish_review(pull, out.event, out.summary, comments=comments)
        return out, job_summary
