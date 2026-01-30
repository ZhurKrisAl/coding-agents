# Отчёт: Coding Agents — SDLC pipeline и качество

## Описание SDLC pipeline

Система реализует замкнутый цикл разработки внутри GitHub:

1. **Триггер:** пользователь создаёт Issue или вешает label `agent:run`.
2. **Code Agent (workflow `issue_to_pr.yml`):**
   - читает Issue (title, body);
   - строит план и получает file inventory репозитория;
   - генерирует патчи только для файлов из inventory (защита от галлюцинаций);
   - создаёт ветку `agent/issue-<id>-<slug>`, коммиты, пушит, открывает PR с «Closes #<id>».
3. **CI (workflow `ci.yml`):** на PR запускаются ruff, black, mypy, pytest.
4. **Reviewer Agent (job `reviewer` в `ci.yml`):**
   - после завершения CI собирает контекст: текст Issue, diff PR, список файлов, результат CI;
   - выносит вердикт **Pass/Fail** и причины строго по Issue + diff + CI (не «всегда approve»);
   - публикует: комментарий в PR, GitHub Review (approve / request changes), при возможности — inline-комментарии;
   - пишет summary в `GITHUB_STEP_SUMMARY`.
5. **Итерации:** при Fail (или провале CI) можно повторно запустить Code Agent по тому же Issue (вручную или по label `agent:retry`), с лимитом итераций (например, `--max-iters 5`). Остановка: успех (CI зелёный + approve) или достижение лимита.

**Safeguards:** лимит итераций, детерминированная остановка, отсутствие авто-мержа, Reviewer не approve по умолчанию.

## Измерение качества через Langfuse

- **Где смотреть:** [Langfuse](https://cloud.langfuse.com) (или self-hosted) после настройки `LANGFUSE_*` в env.
- **Что логируется:**
  - каждый запуск Code Agent / Reviewer Agent = **trace**;
  - этапы (plan, patch, verdict и т.д.) = **spans**;
  - промпты можно версионировать через prompt management;
  - метаданные: `issue_id`, `pr_number`, `repo`, `iteration`, `CI conclusion`, `model name`.
- **Как проверить качество:** откройте Langfuse, найдите трассы по `agent: code_agent` / `reviewer_agent`, посмотрите длительность этапов, использование токенов и метаданные. Ошибки и таймауты видны по статусу span.
- **Без Langfuse:** при отсутствии env vars логирование в Langfuse отключено (graceful degradation); логи остаются в stdout/GitHub Actions.

## Метрики и трассы

| Метрика / объект | Описание |
|-------------------|----------|
| Trace `code_agent_run` | Один запуск Code Agent по Issue |
| Trace `reviewer_agent_run` | Один запуск Reviewer Agent по PR |
| Span `plan` / `patch` | Этапы цепочки Code Agent |
| Span `verdict` | Этап вынесения вердикта Reviewer |
| Metadata `issue_id`, `pr_number`, `repo` | Идентификация контекста |
| Metadata `iteration` | Номер итерации (если поддерживается) |
| Metadata `CI conclusion` | Результат CI для анализа Reviewer |

Использование этих трасс позволяет воспроизводить сценарии и оценивать стабильность и стоимость вызовов LLM.
