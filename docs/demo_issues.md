# Примеры Issue для демонстрации Coding Agents

Скопируйте текст ниже в новое GitHub Issue (или добавьте label `agent:run` к существующему Issue), чтобы запустить Code Agent.

---

## Пример 1: Добавить функцию и тест

**Title:** Add a greeting function and unit test

**Body:**
```
Add a function `greet(name: str) -> str` that returns a string like "Hello, {name}!".

Requirements:
- Place the function in a new or existing Python module in the repo (e.g. `coding_agents/utils.py` or similar).
- Add a unit test that checks `greet("World") == "Hello, World!"`.
- Use type hints and follow existing code style (ruff, black).
```

---

## Пример 2: Конфигурация и валидация

**Title:** Add config validation with Pydantic

**Body:**
```
Introduce a small configuration model using Pydantic:

- Create a config module (e.g. `coding_agents/config.py`) with a Pydantic model that has optional fields: `github_token`, `openai_api_key`, `max_iterations` (int, default 5).
- Add a function `load_config_from_env() -> Config` that builds the model from environment variables (GITHUB_TOKEN, OPENAI_API_KEY, CODING_AGENTS_MAX_ITERATIONS).
- Add a minimal test that checks default values and that env vars are read when set.
```

---

## Пример 3: Улучшение CLI

**Title:** Add --dry-run to code command

**Body:**
```
Add a `--dry-run` flag to the `coding-agents code` command.

When `--dry-run` is set:
- Do not create a branch, commit, or push.
- Do not open a PR.
- Still run the plan and patch generation steps and print a short summary of what would be done (e.g. "Would create branch agent/issue-1-add-greeting, modify files X, Y, open PR").
```

---

После создания Issue добавьте label **agent:run** (если workflow настроен на label) или дождитесь срабатывания workflow на `issues: opened`. Code Agent создаст ветку, внесёт изменения и откроет PR. Далее запустятся CI и Reviewer Agent.
