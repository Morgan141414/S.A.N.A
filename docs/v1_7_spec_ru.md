# S.A.N.A. v1.7 - Local LLM Prompt Contract Tuning

## Цель версии

v1.7 усиливает prompt contract локального LLM provider без ослабления safety checker и quality checker.

Цель: добиться, чтобы локальная модель `llama3.1:8b` начала проходить controlled synthetic smoke как полезный candidate response, а не только через fallback.

## Что изменено

- `build_prompt_policy()` теперь задает проверяемую структуру ответа:
  - 3-5 предложений;
  - явное эмпатическое отражение через `Я рядом` или `Похоже`;
  - один безопасный следующий шаг;
  - один короткий сфокусированный вопрос;
  - запрет окончательного диагноза и медицинской самоуверенности.
- Добавлены protocol-specific правила:
  - `depressive_support` обязан включать self-harm screen;
  - `anxiety_grounding` отделяет факт от тревожного прогноза;
  - `panic_grounding` проверяет медицинские красные флаги;
  - остальные протоколы получают короткие специализированные правила.
- Добавлены unit tests на наличие quality contract markers в prompt policy.

## Результат до v1.7

```text
model: llama3.1:8b
total: 3
passed: 3
candidate_used_count: 0
fallback_count: 3
blocked_reasons:
  llm_quality_failed: 3
decision: needs_prompt_tuning
```

## Результат после v1.7

```text
model: llama3.1:8b
total: 3
passed: 3
candidate_used_count: 3
fallback_count: 0
blocked_reasons: none
runtime: 12 seconds
decision: accept_for_more_tests
```

## Важное ограничение

`accept_for_more_tests` не означает, что модель готова для пользователей.

Это означает только:

- локальная модель прошла первый adult low/medium synthetic smoke;
- ее можно переводить к расширенному synthetic/red-team тестированию;
- crisis, emergency, high-risk и minors остаются вне LLM path;
- safety checker и quality checker остаются обязательными.

## Следующий шаг

v1.8 должна расширить local LLM evaluation set:

```text
3 smoke scenarios
  -> 12-20 synthetic adult low/medium scenarios
  -> per-protocol candidate/fallback report
  -> repeated-run stability check
  -> decision matrix update
```

Цель v1.8: проверить, стабилен ли результат v1.7 за пределами трех smoke-сценариев.
