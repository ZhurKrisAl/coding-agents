"""Typer CLI: coding-agents code | review | serve."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer

from agents.code_agent import run_code_agent
from agents.reviewer_agent.chain import ReviewerAgentChain
from coding_agents.core.github import GitHubClient

app = typer.Typer(help="Coding Agents: Code Agent and Reviewer Agent for GitHub SDLC")


def _get_repo() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise typer.BadParameter("Set GITHUB_REPOSITORY (owner/repo) or use --repo owner/repo")
    return repo


@app.command()
def code(
    issue: int = typer.Option(..., "--issue", "-i", help="Issue number"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Owner/repo (or GITHUB_REPOSITORY)"),
    max_iters: int = typer.Option(5, "--max-iters", help="Max iterations for fix cycle"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Repo path (default: GITHUB_WORKSPACE or .)"),
) -> None:
    """Run Code Agent: read Issue, create branch, apply changes, open PR."""
    repo_name = repo or _get_repo()

    cwd_str = cwd or os.environ.get("GITHUB_WORKSPACE", ".")
    path: Path = Path(cwd_str).resolve()

    if not path.exists():
        typer.echo(f"Path does not exist: {path}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Running Code Agent for issue #{issue} in {repo_name} at {path}")
    result = run_code_agent(path, repo_name, issue, max_iterations=max_iters)

    if result.success:
        typer.echo(f"Success: PR #{result.pr_number} created on branch {result.branch}")
    else:
        typer.echo(f"Failed: {result.message}", err=True)
        raise typer.Exit(1)


@app.command()
def review(
    pr: int = typer.Option(..., "--pr", "-p", help="Pull request number"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Owner/repo (or GITHUB_REPOSITORY)"),
    ci_conclusion: str = typer.Option("success", "--ci-conclusion", help="CI conclusion for context"),
    ci_summary: str = typer.Option("", "--ci-summary", help="CI summary text"),
    no_publish: bool = typer.Option(False, "--no-publish", help="Only output verdict, do not post"),
) -> None:
    """Run Reviewer Agent: analyze PR, post comment + summary + GitHub Review."""
    repo_name = repo or _get_repo()
    typer.echo(f"Running Reviewer Agent for PR #{pr} in {repo_name}")

    gh = GitHubClient()
    pull = gh.get_pull(repo_name, pr)

    issue_title = pull.title or ""
    issue_body = pull.body or ""

    reviewer = ReviewerAgentChain(repo_full_name=repo_name)

    if no_publish:
        out = reviewer.run(pr, issue_title, issue_body, ci_conclusion, ci_summary)
        typer.echo(out.summary)
        return

    out, job_summary = reviewer.run_and_publish(pr, issue_title, issue_body, ci_conclusion, ci_summary)

    typer.echo(job_summary)

    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        with open(step_summary_path, "a", encoding="utf-8") as f:
            f.write("\n" + job_summary)

    typer.echo(f"Verdict: {out.verdict}")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port"),
) -> None:
    """Run FastAPI server for webhook/API (optional)."""
    try:
        from coding_agents.cli.serve import run_serve

        run_serve(host=host, port=port)
    except ImportError:
        typer.echo("FastAPI/uvicorn not available; install with: pip install fastapi uvicorn", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
