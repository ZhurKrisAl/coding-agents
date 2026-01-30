"""CodeAgentChain: Issue → plan → file discovery → patch generation → self-check."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coding_agents.core.github import GitHubClient, get_issue_context
from coding_agents.core.github.issues import IssueContext
from coding_agents.core.git import GitRepo
from coding_agents.core.llm import get_llm
from coding_agents.core.observability.langfuse import get_langfuse_client, trace_agent
from coding_agents.core.prompts.code_agent import CODE_AGENT_PROMPTS


@dataclass
class CodeAgentResult:
    """Result of Code Agent run."""

    success: bool
    branch: str
    pr_number: int | None
    message: str
    iteration: int


def _parse_plan_output(text: str) -> tuple[str, list[str]]:
    """Extract PLAN and FILES from agent output."""
    plan = ""
    files: list[str] = []
    in_plan = False
    in_files = False
    for line in text.split("\n"):
        if line.strip().upper().startswith("PLAN:"):
            in_plan = True
            in_files = False
            plan += line.replace("PLAN:", "").strip() + "\n"
            continue
        if line.strip().upper().startswith("FILES:"):
            in_files = True
            in_plan = False
            continue
        if in_plan:
            plan += line + "\n"
        if in_files and line.strip():
            files.append(line.strip())
    return plan.strip(), [f for f in files if f and not f.startswith("#")]


def _parse_patches(text: str, allowed_paths: set[str]) -> dict[str, str]:
    """Extract FILE blocks; only allow paths in allowed_paths."""
    out: dict[str, str] = {}
    pattern = re.compile(r"---\s*FILE:\s*(.+?)\s*\n(.*?)(?=---\s*END FILE|---\s*FILE:|\Z)", re.DOTALL)
    for m in pattern.finditer(text):
        path = m.group(1).strip()
        if path in allowed_paths:
            out[path] = m.group(2).strip()
    return out


class CodeAgentChain:
    """Chain: read Issue → plan → file inventory → patch → self-check (no merge)."""

    def __init__(
        self,
        repo_path: str | Path,
        repo_full_name: str,
        github_client: GitHubClient | None = None,
        llm_provider: str | None = None,
        max_iterations: int = 5,
    ) -> None:
        self.repo_path = Path(repo_path)
        self.repo_full_name = repo_full_name
        self.gh = github_client or GitHubClient()
        self.git = GitRepo(self.repo_path)
        self.llm = get_llm(provider=llm_provider, temperature=0.2)
        self.max_iterations = max_iterations

    def run(self, issue_id: int) -> CodeAgentResult:
        """Full flow: fetch issue, plan, file inventory, patch, commit, push, create PR."""
        metadata = {"issue_id": issue_id, "repo": self.repo_full_name, "agent": "code_agent"}
        with trace_agent("code_agent_run", metadata=metadata) as trace:
            return self._run_impl(issue_id, trace)

    def _run_impl(self, issue_id: int, trace: Any) -> CodeAgentResult:
        issue = self.gh.get_issue(self.repo_full_name, issue_id)
        ctx = get_issue_context(issue)
        file_inventory = self.git.list_files()
        if not file_inventory:
            file_inventory = [".gitkeep"]
        inventory_text = "\n".join(file_inventory[:200])
        allowed = set(file_inventory)

        prompt_plan = CODE_AGENT_PROMPTS["plan"].format(
            title=ctx.title,
            body=ctx.body,
            file_inventory=inventory_text,
        )
        if trace:
            trace.span(name="plan", metadata={"model": self.llm.model_name})
        plan_result = self.llm.invoke(prompt_plan)
        plan_str, files_to_touch = _parse_plan_output(plan_result.content)
        files_to_touch = [f for f in files_to_touch if f in allowed][:20]
        if not files_to_touch:
            files_to_touch = [file_inventory[0]] if file_inventory else []

        file_contents = ""
        for f in files_to_touch:
            if self.git.file_exists(f):
                file_contents += f"### {f}\n```\n{self.git.read_file(f)}\n```\n"
        prompt_patch = CODE_AGENT_PROMPTS["patch"].format(
            title=ctx.title,
            body=ctx.body,
            files_to_modify="\n".join(files_to_touch),
            file_contents=file_contents or "(new file)",
        )
        if trace:
            trace.span(name="patch", metadata={"model": self.llm.model_name})
        patch_result = self.llm.invoke(prompt_patch)
        patches = _parse_patches(patch_result.content, allowed)
        if not patches:
            return CodeAgentResult(
                success=False,
                branch="",
                pr_number=None,
                message="No valid patches generated; agent only uses file inventory paths.",
                iteration=0,
            )

        branch_name = self.git.branch_name(issue_id, ctx.title)
        try:
            self.git.create_branch(branch_name)
        except Exception:
            self.git.checkout("main")
            try:
                self.git.repo.delete_head(branch_name, force=True)
            except Exception:
                pass
            self.git.create_branch(branch_name)

        for path, content in patches.items():
            self.git.write_file(path, content)
        self.git.add(list(patches.keys()))
        self.git.commit(f"Implement issue #{issue_id}\n\n{ctx.title}")
        try:
            self.git.push(branch=branch_name)
        except Exception as e:
            return CodeAgentResult(
                success=False,
                branch=branch_name,
                pr_number=None,
                message=f"Push failed: {e}",
                iteration=0,
            )

        pr_body = f"Closes #{issue_id}\n\n{ctx.body}"
        repo = self.gh.get_repo(self.repo_full_name)
        pr = repo.create_pull(
            title=f"[Agent] {ctx.title}",
            body=pr_body,
            head=branch_name,
            base="main",
        )
        return CodeAgentResult(
            success=True,
            branch=branch_name,
            pr_number=pr.number,
            message=f"PR #{pr.number} created",
            iteration=0,
        )


def run_code_agent(
    repo_path: str | Path,
    repo_full_name: str,
    issue_id: int,
    max_iterations: int = 5,
) -> CodeAgentResult:
    """Entrypoint: run Code Agent for one issue."""
    chain = CodeAgentChain(
        repo_path=repo_path,
        repo_full_name=repo_full_name,
        max_iterations=max_iterations,
    )
    return chain.run(issue_id)
