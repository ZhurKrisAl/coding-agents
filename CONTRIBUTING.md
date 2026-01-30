# Contributing to Coding Agents

## Локальная разработка

- Python 3.11+
- Установка: `pip install -e ".[dev]"`
- Переменные: `GITHUB_TOKEN`, `OPENAI_API_KEY`; опционально `LANGFUSE_*`.

## Качество кода (локально и в CI)

- **Ruff:** `ruff check coding_agents agents tests`
- **Black:** `black coding_agents agents tests` (проверка: `black --check ...`)
- **Mypy:** `mypy coding_agents agents`
- **Pytest:** `pytest tests -v`

Все перечисленные инструменты настроены в `pyproject.toml` и запускаются в CI при открытии PR.

## Структура

- `coding_agents/` — ядро (github, git, llm, prompts, policies, observability) и CLI.
- `agents/` — Code Agent и Reviewer Agent (отдельные промпты и цепочки).
- Тесты в `tests/`; минимальные unit-тесты на парсинг Issue, policy итераций, генерацию отчёта ревью.

## Правила

- Code Agent и Reviewer Agent остаются изолированными (отдельные модули и промпты).
- Reviewer выносит вердикт только по Issue + diff + CI.
- Лимит итераций и стоп-условия задаются в `policies/` и CLI.
