# S.A.N.A. v1.6 Release Readiness

Дата: 2026-06-02.

## Статус

Готово для фиксации как runtime/evaluation milestone.

## Сделано

- User-local Ollama runtime установлен и запущен на сервере.
- Модель `llama3.1:8b` скачана в Ollama.
- Preflight подтвердил модель до генерации.
- Gated synthetic smoke выполнен.
- Comparison matrix обновлена фактическим результатом.

## Quality Result

```text
smoke_exit: 0
smoke_seconds: 22
total: 3
passed: 3
failed: 0
candidate_used_count: 0
fallback_count: 3
blocked_reasons:
  llm_quality_failed: 3
```

## Риск-вывод

Safety architecture работает правильно: локальная модель не получает право напрямую отвечать пользователю, если не проходит quality gate.

Главный риск сейчас не infrastructure, а качество candidate response. `llama3.1:8b` требует prompt tuning и повторного smoke.

## Не готово

- Real-user testing.
- Clinical validation.
- Работа с minors/high/crisis/emergency через LLM.
- Fine-tuning или deep learning.

## Следующая версия

v1.7 должна усилить prompt contract и добиться уменьшения `fallback_count` без ослабления safety/quality checker.
