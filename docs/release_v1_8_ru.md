# S.A.N.A. v1.8 Release Readiness

Дата: 2026-06-02.

## Статус

Готово как expanded-evaluation milestone.

## Сделано

- Добавлен expanded local LLM scenario set.
- Добавлены repeated-run параметры.
- Добавлен `make llm-smoke-ollama-expanded`.
- Добавлены тесты expanded-набора и repeat summary.
- Выполнен реальный expanded smoke на `llama3.1:8b`.

## Quality Gates

```text
targeted tests: 29 passed
expanded local smoke:
  total: 15
  passed: 15
  candidate_used_count: 10
  fallback_count: 5
  blocked_reasons:
    llm_quality_failed: 5
```

## Риск-вывод

Safety/fallback architecture работает: финальные ответы безопасны.

Но candidate response нестабилен на расширенном наборе. Особенно слабые места:

- depressive self-harm screen;
- panic medical red flag check;
- focused question;
- mixed-language чистота ответа.

## Не готово

- Real-user testing.
- Production readiness.
- Clinical validation.
- LLM для minors/high/crisis/emergency.

## Следующая версия

v1.9 должна добавить guarded protocol repair/scaffold и проверить expanded smoke повторно.
