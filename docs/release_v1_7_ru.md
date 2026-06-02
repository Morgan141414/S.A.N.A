# S.A.N.A. v1.7 Release Readiness

Дата: 2026-06-02.

## Статус

Готово как prompt-contract milestone.

## Сделано

- Усилен `build_prompt_policy()` для локального LLM.
- Добавлены protocol-specific правила.
- Добавлены тесты на prompt quality contract.
- Повторно выполнен gated smoke для `llama3.1:8b`.
- Comparison matrix обновлена результатом `accept_for_more_tests`.

## Quality Gates

```text
targeted tests: 16 passed
local gated smoke:
  total: 3
  passed: 3
  candidate_used_count: 3
  fallback_count: 0
  blocked_reasons: none
```

## Риск-вывод

v1.7 улучшает качество candidate response без снижения safety. Это правильный тип прогресса: модель проходит существующие проверки, а не проверки подгоняются под модель.

## Не готово

- Real-user testing.
- Production readiness.
- Clinical validation.
- LLM для minors/high/crisis/emergency.
- Fine-tuning/deep learning.

## Следующая версия

v1.8 должна добавить расширенный local LLM evaluation set и repeated-run stability check.
