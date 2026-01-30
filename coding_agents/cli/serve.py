"""FastAPI server for webhook/API entrypoint."""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.code_agent import run_code_agent
from agents.reviewer_agent.chain import ReviewerAgentChain

app = FastAPI(title="Coding Agents API", version="0.1.0")

class CodeRequest(BaseModel):
    issue: int
    repo: str
    max_iters: int = 5

class ReviewRequest(BaseModel):
    pr: int
    repo: str
    ci_conclusion: str = "success"
    ci_summary: str = ""

@app.post("/code")
def api_code(req: CodeRequest) -> dict:
    """Run Code Agent for an issue."""
    cwd = os.environ.get("GITHUB_WORKSPACE", ".")
    path = Path(cwd).resolve()
    if not path.exists():
        raise HTTPException(status_code=400, detail="GITHUB_WORKSPACE or cwd missing")
    result = run_code_agent(path, req.repo, req.issue, max_iterations=req.max_iters)
    return {
        "success": result.success,
        "branch": result.branch,
        "pr_number": result.pr_number,
        "message": result.message,
    }

@app.post("/review")
def api_review(req: ReviewRequest) -> dict:
    """Run Reviewer Agent for a PR."""
    reviewer = ReviewerAgentChain(repo_full_name=req.repo)
    from coding_agents.core.github import GitHubClient
    gh = GitHubClient()
    pull = gh.get_pull(req.repo, req.pr)
    out, _ = reviewer.run_and_publish(
        req.pr,
        pull.title or "",
        pull.body or "",
        req.ci_conclusion,
        req.ci_summary,
    )
    return {"verdict": out.verdict, "reason": out.reason, "summary": out.summary}

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/items/export/csv")
def export_items_to_csv():
    # Example data, replace with actual data fetching logic
    data = [
        {"id": 1, "name": "Item 1", "description": "Description for Item 1"},
        {"id": 2, "name": "Item 2", "description": "Description for Item 2"},
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=items.csv"
    return response

def run_serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn
    uvicorn.run(app, host=host, port=port)