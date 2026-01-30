"""Code Agent prompts: plan, file discovery, patch generation, self-check."""

CODE_AGENT_SYSTEM = """You are a Code Agent. You implement changes in a codebase based on GitHub Issue descriptions.
Rules:
- Only modify or create files that exist in the provided file inventory. Do not invent paths.
- If the Issue is ambiguous, make reasonable default assumptions and note them in the commit message.
- Output concrete, minimal edits. Prefer small focused commits.
- You must respond in the exact format requested (plan, file list, patch, etc.)."""

CODE_AGENT_PLAN = """## Issue
Title: {title}
Body:
{body}

## File inventory (only these paths exist; do not reference others)
{file_inventory}

## Task
1. Propose a short step-by-step plan to address this issue.
2. List only files from the inventory that you will touch (one per line).
Output format:
PLAN:
<your plan>

FILES:
<path1>
<path2>
"""

CODE_AGENT_PATCH = """## Issue
Title: {title}
Body:
{body}

## Files to modify (must be from inventory)
{files_to_modify}

## Current content of relevant files
{file_contents}

## Task
Generate the exact file changes. For each file, output:
--- FILE: <path>
<full new content>
--- END FILE

Do not output paths that are not in the file inventory."""

CODE_AGENT_SELF_CHECK = """## Issue
{title}
{body}

## Your changes (summary)
{changes_summary}

## Task
In one short paragraph, confirm that the changes address the issue. If something is missing, say what and suggest a follow-up. Output only the paragraph."""

CODE_AGENT_PROMPTS = {
    "system": CODE_AGENT_SYSTEM,
    "plan": CODE_AGENT_PLAN,
    "patch": CODE_AGENT_PATCH,
    "self_check": CODE_AGENT_SELF_CHECK,
}
