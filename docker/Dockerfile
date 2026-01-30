# coding-agents: Python 3.11+ with CLI and optional API
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY coding_agents coding_agents
COPY agents agents

RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["coding-agents"]
CMD ["--help"]
